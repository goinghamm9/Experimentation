"""
Alpaca broker integration.

Alpaca advantages for HFT:
- Commission-free stock and ETF trading
- Real-time websocket data feed (IEX free, SIP paid)
- REST + streaming API
- Paper trading environment for testing
- Fractional shares support
- Better rate limits than Robinhood (~200 req/min)
- Native support for bracket and OCO orders
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

_ALPACA_STATUS_MAP = {
    "new": OrderStatus.SUBMITTED,
    "partially_filled": OrderStatus.PARTIALLY_FILLED,
    "filled": OrderStatus.FILLED,
    "done_for_day": OrderStatus.FILLED,
    "canceled": OrderStatus.CANCELLED,
    "expired": OrderStatus.CANCELLED,
    "replaced": OrderStatus.SUBMITTED,
    "pending_new": OrderStatus.PENDING,
    "accepted": OrderStatus.SUBMITTED,
    "rejected": OrderStatus.REJECTED,
}


class AlpacaBroker(Broker):
    """Alpaca Markets broker integration."""

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        base_url: str = "https://paper-api.alpaca.markets",
    ):
        self._api_key = api_key or os.environ.get("ALPACA_API_KEY", "")
        self._secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY", "")
        self._base_url = base_url
        self._api = None
        self._connected = False

    @property
    def name(self) -> str:
        return "alpaca"

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Connect to Alpaca API."""
        try:
            import alpaca_trade_api as tradeapi

            self._api = tradeapi.REST(
                self._api_key,
                self._secret_key,
                self._base_url,
            )
            # Verify connection
            account = self._api.get_account()
            self._connected = True
            logger.info(
                "alpaca_connected",
                status=account.status,
                equity=account.equity,
                buying_power=account.buying_power,
            )
        except Exception as e:
            logger.error("alpaca_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from Alpaca."""
        self._connected = False
        self._api = None
        logger.info("alpaca_disconnected")

    async def get_account(self) -> PortfolioState:
        """Get Alpaca account state."""
        if not self._api:
            raise RuntimeError("Not connected to Alpaca")

        account = self._api.get_account()
        positions = await self.get_positions()

        equity = float(account.equity)
        cash = float(account.cash)

        return PortfolioState(
            cash=cash,
            positions=positions,
            total_equity=equity,
            peak_equity=equity,
        )

    async def get_positions(self) -> dict[str, Position]:
        """Get all open Alpaca positions."""
        if not self._api:
            raise RuntimeError("Not connected to Alpaca")

        alpaca_positions = self._api.list_positions()
        positions: dict[str, Position] = {}

        for pos in alpaca_positions:
            positions[pos.symbol] = Position(
                symbol=pos.symbol,
                qty=float(pos.qty),
                avg_entry_price=float(pos.avg_entry_price),
                current_price=float(pos.current_price),
                unrealized_pnl=float(pos.unrealized_pl),
            )

        return positions

    async def submit_order(self, order: Order) -> Order:
        """Submit an order to Alpaca."""
        if not self._api:
            raise RuntimeError("Not connected to Alpaca")

        try:
            alpaca_order = self._api.submit_order(
                symbol=order.symbol,
                qty=order.qty,
                side=order.side.value,
                type=order.order_type.value,
                time_in_force="day",
                limit_price=str(order.limit_price) if order.limit_price else None,
            )

            order.order_id = alpaca_order.id
            order.status = _ALPACA_STATUS_MAP.get(
                alpaca_order.status, OrderStatus.PENDING
            )
            order.timestamp = datetime.now(timezone.utc)

            logger.info(
                "alpaca_order_submitted",
                symbol=order.symbol,
                side=order.side.value,
                qty=order.qty,
                order_id=order.order_id,
            )
        except Exception as e:
            order.status = OrderStatus.REJECTED
            logger.error("alpaca_order_failed", error=str(e))

        return order

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an Alpaca order."""
        if not self._api:
            return False
        try:
            self._api.cancel_order(order_id)
            return True
        except Exception as e:
            logger.error("alpaca_cancel_failed", order_id=order_id, error=str(e))
            return False

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Check Alpaca order status."""
        if not self._api:
            return OrderStatus.REJECTED
        try:
            alpaca_order = self._api.get_order(order_id)
            return _ALPACA_STATUS_MAP.get(alpaca_order.status, OrderStatus.REJECTED)
        except Exception:
            return OrderStatus.REJECTED

    async def cancel_all_orders(self) -> int:
        """Cancel all open Alpaca orders."""
        if not self._api:
            return 0
        try:
            cancelled = self._api.cancel_all_orders()
            count = len(cancelled) if cancelled else 0
            logger.info("alpaca_all_orders_cancelled", count=count)
            return count
        except Exception as e:
            logger.error("alpaca_cancel_all_failed", error=str(e))
            return 0
