"""
Interactive Brokers integration via ib_insync.

IBKR advantages for HFT:
- Lowest commissions for high volume ($0.0035/share, capped)
- Direct market access (DMA)
- Deep order book data (Level II)
- Sophisticated order types (iceberg, TWAP, VWAP, adaptive)
- FIX protocol support for ultra-low latency
- Robust paper trading environment
- Global market access (stocks, futures, options, forex)

Best choice for serious HFT due to:
- Lowest latency execution
- Best market data quality
- Most order type flexibility
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from utils.logging import get_logger
from utils.types import (
    Order,
    OrderStatus,
    OrderType,
    Position,
    PortfolioState,
    Side,
)

from .base import Broker

logger = get_logger(__name__)

_IB_STATUS_MAP = {
    "PendingSubmit": OrderStatus.PENDING,
    "PendingCancel": OrderStatus.PENDING,
    "PreSubmitted": OrderStatus.SUBMITTED,
    "Submitted": OrderStatus.SUBMITTED,
    "Cancelled": OrderStatus.CANCELLED,
    "Filled": OrderStatus.FILLED,
    "Inactive": OrderStatus.REJECTED,
}


class IBKRBroker(Broker):
    """Interactive Brokers via ib_insync."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
    ):
        self._host = host
        self._port = port
        self._client_id = client_id
        self._ib = None
        self._connected = False

    @property
    def name(self) -> str:
        return "ibkr"

    @property
    def is_connected(self) -> bool:
        return self._connected and self._ib is not None and self._ib.isConnected()

    async def connect(self) -> None:
        """Connect to TWS/Gateway."""
        try:
            from ib_insync import IB

            self._ib = IB()
            await self._ib.connectAsync(
                host=self._host,
                port=self._port,
                clientId=self._client_id,
            )
            self._connected = True

            account_values = self._ib.accountSummary()
            logger.info("ibkr_connected", host=self._host, port=self._port)
        except Exception as e:
            logger.error("ibkr_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from TWS/Gateway."""
        if self._ib:
            self._ib.disconnect()
            self._connected = False
            logger.info("ibkr_disconnected")

    async def get_account(self) -> PortfolioState:
        """Get IBKR account state."""
        if not self._ib:
            raise RuntimeError("Not connected to IBKR")

        account_values = self._ib.accountSummary()
        equity = 0.0
        cash = 0.0

        for av in account_values:
            if av.tag == "NetLiquidation":
                equity = float(av.value)
            elif av.tag == "AvailableFunds":
                cash = float(av.value)

        positions = await self.get_positions()

        return PortfolioState(
            cash=cash,
            positions=positions,
            total_equity=equity,
            peak_equity=equity,
        )

    async def get_positions(self) -> dict[str, Position]:
        """Get all open IBKR positions."""
        if not self._ib:
            raise RuntimeError("Not connected to IBKR")

        ib_positions = self._ib.positions()
        positions: dict[str, Position] = {}

        for pos in ib_positions:
            symbol = pos.contract.symbol
            qty = float(pos.position)
            avg_cost = float(pos.avgCost)

            positions[symbol] = Position(
                symbol=symbol,
                qty=qty,
                avg_entry_price=avg_cost,
                current_price=avg_cost,  # Will be updated by market data
            )

        return positions

    async def submit_order(self, order: Order) -> Order:
        """Submit an order to IBKR."""
        if not self._ib:
            raise RuntimeError("Not connected to IBKR")

        try:
            from ib_insync import LimitOrder, MarketOrder, Stock

            contract = Stock(order.symbol, "SMART", "USD")

            action = "BUY" if order.side == Side.BUY else "SELL"

            if order.order_type == OrderType.MARKET:
                ib_order = MarketOrder(action, order.qty)
            elif order.order_type == OrderType.LIMIT:
                if order.limit_price is None:
                    raise ValueError("Limit price required")
                ib_order = LimitOrder(action, order.qty, order.limit_price)
            else:
                raise ValueError(f"Unsupported order type: {order.order_type}")

            trade = self._ib.placeOrder(contract, ib_order)

            order.order_id = str(trade.order.orderId)
            order.status = OrderStatus.SUBMITTED
            order.timestamp = datetime.now(timezone.utc)

            logger.info(
                "ibkr_order_submitted",
                symbol=order.symbol,
                side=order.side.value,
                qty=order.qty,
                order_id=order.order_id,
            )
        except Exception as e:
            order.status = OrderStatus.REJECTED
            logger.error("ibkr_order_failed", error=str(e))

        return order

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an IBKR order."""
        if not self._ib:
            return False
        try:
            for trade in self._ib.openTrades():
                if str(trade.order.orderId) == order_id:
                    self._ib.cancelOrder(trade.order)
                    return True
            return False
        except Exception as e:
            logger.error("ibkr_cancel_failed", order_id=order_id, error=str(e))
            return False

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Check IBKR order status."""
        if not self._ib:
            return OrderStatus.REJECTED
        for trade in self._ib.trades():
            if str(trade.order.orderId) == order_id:
                return _IB_STATUS_MAP.get(trade.orderStatus.status, OrderStatus.REJECTED)
        return OrderStatus.REJECTED

    async def cancel_all_orders(self) -> int:
        """Cancel all open IBKR orders."""
        if not self._ib:
            return 0
        try:
            self._ib.reqGlobalCancel()
            count = len(self._ib.openTrades())
            logger.info("ibkr_all_orders_cancelled", count=count)
            return count
        except Exception as e:
            logger.error("ibkr_cancel_all_failed", error=str(e))
            return 0
