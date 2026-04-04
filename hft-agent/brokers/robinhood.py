"""
Robinhood broker integration via robin_stocks.

Robinhood API characteristics:
- No official API; robin_stocks is the best unofficial wrapper
- Rate limited (~1 req/sec for market data)
- Supports stocks, options, crypto
- No direct websocket feed (poll-based)
- Commission-free trades
- Limited order types vs. IBKR

Limitations for HFT:
- Rate limiting makes true HFT impossible; suitable for medium-frequency
- No direct market data websocket (use Alpaca/Polygon for data, Robinhood for execution)
- Best used as execution-only broker with external data feed
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

# Mapping from Robinhood order states to our OrderStatus
_RH_STATUS_MAP = {
    "queued": OrderStatus.PENDING,
    "unconfirmed": OrderStatus.PENDING,
    "confirmed": OrderStatus.SUBMITTED,
    "partially_filled": OrderStatus.PARTIALLY_FILLED,
    "filled": OrderStatus.FILLED,
    "cancelled": OrderStatus.CANCELLED,
    "rejected": OrderStatus.REJECTED,
    "failed": OrderStatus.REJECTED,
}


class RobinhoodBroker(Broker):
    """Robinhood broker using robin_stocks library."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        mfa_code: str | None = None,
    ):
        self._username = username or os.environ.get("ROBINHOOD_USERNAME", "")
        self._password = password or os.environ.get("ROBINHOOD_PASSWORD", "")
        self._mfa_code = mfa_code or os.environ.get("ROBINHOOD_MFA_CODE")
        self._connected = False
        self._rs = None  # robin_stocks module

    @property
    def name(self) -> str:
        return "robinhood"

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Login to Robinhood."""
        try:
            import robin_stocks.robinhood as rs

            self._rs = rs
            login_kwargs = {
                "username": self._username,
                "password": self._password,
            }
            if self._mfa_code:
                login_kwargs["mfa_code"] = self._mfa_code

            rs.login(**login_kwargs)
            self._connected = True
            logger.info("robinhood_connected")
        except Exception as e:
            logger.error("robinhood_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Logout from Robinhood."""
        if self._rs and self._connected:
            self._rs.logout()
            self._connected = False
            logger.info("robinhood_disconnected")

    async def get_account(self) -> PortfolioState:
        """Get Robinhood account info."""
        if not self._rs:
            raise RuntimeError("Not connected to Robinhood")

        profile = self._rs.profiles.load_portfolio_profile()
        positions = await self.get_positions()

        equity = float(profile.get("equity", 0))
        cash = float(profile.get("withdrawable_amount", 0))

        return PortfolioState(
            cash=cash,
            positions=positions,
            total_equity=equity,
            peak_equity=equity,
        )

    async def get_positions(self) -> dict[str, Position]:
        """Get all open Robinhood positions."""
        if not self._rs:
            raise RuntimeError("Not connected to Robinhood")

        rh_positions = self._rs.account.get_open_stock_positions()
        positions: dict[str, Position] = {}

        for pos in rh_positions:
            qty = float(pos.get("quantity", 0))
            if qty == 0:
                continue

            # Get the instrument info for the symbol
            instrument_url = pos.get("instrument", "")
            instrument_data = self._rs.stocks.get_instrument_by_url(instrument_url)
            symbol = instrument_data.get("symbol", "UNKNOWN") if instrument_data else "UNKNOWN"

            avg_price = float(pos.get("average_buy_price", 0))

            # Get current price
            quote = self._rs.stocks.get_latest_price(symbol)
            current_price = float(quote[0]) if quote else avg_price

            positions[symbol] = Position(
                symbol=symbol,
                qty=qty,
                avg_entry_price=avg_price,
                current_price=current_price,
                unrealized_pnl=(current_price - avg_price) * qty,
            )

        return positions

    async def submit_order(self, order: Order) -> Order:
        """Submit an order to Robinhood."""
        if not self._rs:
            raise RuntimeError("Not connected to Robinhood")

        try:
            if order.order_type == OrderType.MARKET:
                if order.side == Side.BUY:
                    result = self._rs.orders.order_buy_market(
                        order.symbol, order.qty,
                    )
                else:
                    result = self._rs.orders.order_sell_market(
                        order.symbol, order.qty,
                    )
            elif order.order_type == OrderType.LIMIT:
                if order.limit_price is None:
                    raise ValueError("Limit price required for limit orders")
                if order.side == Side.BUY:
                    result = self._rs.orders.order_buy_limit(
                        order.symbol, order.qty, order.limit_price,
                    )
                else:
                    result = self._rs.orders.order_sell_limit(
                        order.symbol, order.qty, order.limit_price,
                    )

            if result and "id" in result:
                order.order_id = result["id"]
                order.status = _RH_STATUS_MAP.get(
                    result.get("state", ""), OrderStatus.PENDING
                )
                order.timestamp = datetime.now(timezone.utc)
                logger.info(
                    "robinhood_order_submitted",
                    symbol=order.symbol,
                    side=order.side.value,
                    qty=order.qty,
                    order_id=order.order_id,
                )
            else:
                order.status = OrderStatus.REJECTED
                logger.warning("robinhood_order_rejected", result=str(result)[:200])

        except Exception as e:
            order.status = OrderStatus.REJECTED
            logger.error("robinhood_order_failed", error=str(e))

        return order

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order on Robinhood."""
        if not self._rs:
            return False
        try:
            result = self._rs.orders.cancel_stock_order(order_id)
            return result is not None
        except Exception as e:
            logger.error("robinhood_cancel_failed", order_id=order_id, error=str(e))
            return False

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Check order status on Robinhood."""
        if not self._rs:
            return OrderStatus.REJECTED
        try:
            info = self._rs.orders.get_stock_order_info(order_id)
            state = info.get("state", "failed") if info else "failed"
            return _RH_STATUS_MAP.get(state, OrderStatus.REJECTED)
        except Exception:
            return OrderStatus.REJECTED

    async def cancel_all_orders(self) -> int:
        """Cancel all open orders."""
        if not self._rs:
            return 0
        try:
            result = self._rs.orders.cancel_all_stock_orders()
            count = len(result) if result else 0
            logger.info("robinhood_all_orders_cancelled", count=count)
            return count
        except Exception as e:
            logger.error("robinhood_cancel_all_failed", error=str(e))
            return 0
