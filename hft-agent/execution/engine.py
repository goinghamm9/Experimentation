"""
Order execution engine with slippage modeling.

Handles:
- Order submission via broker API
- Order lifecycle management
- Slippage estimation (power-law model per Bouchaud et al. 2008)
- Rate limiting
- Retry logic
"""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any

import numpy as np

from brokers.base import Broker
from data.storage.redis_cache import RedisCache
from utils.config import ExecutionConfig
from utils.logging import get_logger
from utils.types import Order, OrderStatus, OrderType, Side

logger = get_logger(__name__)


class SlippageModel:
    """Power-law slippage model.

    Based on Bouchaud, Farmer, Lillo (2008):
    Price impact follows a power law: impact ~ volume^0.5
    (the "square root law" of market impact).

    This is critical for realistic execution modeling — linear
    impact models underestimate the cost of large orders.
    """

    def __init__(self, model_type: str = "power_law"):
        self._model_type = model_type

    def estimate_slippage(
        self,
        order_qty: float,
        avg_daily_volume: float,
        spread: float,
        price: float,
    ) -> float:
        """Estimate expected slippage for an order.

        Args:
            order_qty: Order quantity in shares.
            avg_daily_volume: Average daily volume for the symbol.
            spread: Current bid-ask spread.
            price: Current mid price.

        Returns:
            Estimated slippage in price terms.
        """
        if self._model_type == "none":
            return 0.0

        if avg_daily_volume <= 0 or price <= 0:
            return spread / 2  # Default to half spread

        participation_rate = order_qty / avg_daily_volume

        if self._model_type == "power_law":
            # Square root law: impact = sigma * sqrt(Q/V)
            # Simplified: slippage = spread/2 + k * sqrt(participation_rate)
            k = spread * 2  # Calibration constant
            impact = k * np.sqrt(participation_rate)
            return float(spread / 2 + impact)

        elif self._model_type == "linear":
            return float(spread / 2 + spread * participation_rate * 10)

        return float(spread / 2)


class ExecutionEngine:
    """Manages order execution lifecycle."""

    def __init__(
        self,
        broker: Broker,
        config: ExecutionConfig,
        redis_cache: RedisCache | None = None,
        max_orders_per_second: int = 5,
    ):
        self._broker = broker
        self._config = config
        self._cache = redis_cache
        self._max_ops = max_orders_per_second
        self._slippage = SlippageModel(config.slippage_model)

        # Order tracking
        self._pending_orders: dict[str, Order] = {}
        self._filled_orders: deque[Order] = deque(maxlen=10000)
        self._order_timestamps: deque[datetime] = deque(maxlen=100)

    async def execute(self, order: Order) -> Order:
        """Execute an order through the broker.

        Handles rate limiting, retries, and status tracking.
        """
        # Rate limiting
        if self._cache:
            allowed = await self._cache.check_rate_limit(
                f"orders:{order.symbol}", self._max_ops,
            )
            if not allowed:
                logger.warning("rate_limited", symbol=order.symbol)
                order.status = OrderStatus.REJECTED
                return order

        # Submit with retries
        last_error = None
        for attempt in range(self._config.max_retries):
            try:
                order = await self._broker.submit_order(order)

                if order.status in (OrderStatus.SUBMITTED, OrderStatus.PENDING, OrderStatus.FILLED):
                    if order.order_id:
                        self._pending_orders[order.order_id] = order
                    logger.info(
                        "order_executed",
                        symbol=order.symbol,
                        side=order.side.value,
                        qty=order.qty,
                        status=order.status.value,
                        attempt=attempt + 1,
                    )
                    return order

                if order.status == OrderStatus.REJECTED:
                    logger.warning(
                        "order_rejected",
                        symbol=order.symbol,
                        attempt=attempt + 1,
                    )
                    return order

            except Exception as e:
                last_error = e
                logger.warning(
                    "order_attempt_failed",
                    symbol=order.symbol,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < self._config.max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))

        order.status = OrderStatus.REJECTED
        logger.error(
            "order_failed_all_retries",
            symbol=order.symbol,
            error=str(last_error),
        )
        return order

    async def cancel(self, order_id: str) -> bool:
        """Cancel a pending order."""
        success = await self._broker.cancel_order(order_id)
        if success and order_id in self._pending_orders:
            self._pending_orders[order_id].status = OrderStatus.CANCELLED
            del self._pending_orders[order_id]
        return success

    async def cancel_all(self) -> int:
        """Cancel all pending orders."""
        count = await self._broker.cancel_all_orders()
        self._pending_orders.clear()
        return count

    async def check_fills(self) -> list[Order]:
        """Check for filled orders and update tracking."""
        filled = []
        to_remove = []

        for order_id, order in self._pending_orders.items():
            status = await self._broker.get_order_status(order_id)
            order.status = status

            if status == OrderStatus.FILLED:
                self._filled_orders.append(order)
                to_remove.append(order_id)
                filled.append(order)
                logger.info(
                    "order_filled",
                    symbol=order.symbol,
                    side=order.side.value,
                    qty=order.qty,
                    order_id=order_id,
                )
            elif status in (OrderStatus.CANCELLED, OrderStatus.REJECTED):
                to_remove.append(order_id)

        for order_id in to_remove:
            del self._pending_orders[order_id]

        return filled

    def estimate_slippage(
        self,
        order: Order,
        avg_daily_volume: float,
        spread: float,
    ) -> float:
        """Estimate slippage for a proposed order."""
        price = order.limit_price or 0
        return self._slippage.estimate_slippage(
            order.qty, avg_daily_volume, spread, price,
        )

    @property
    def pending_count(self) -> int:
        return len(self._pending_orders)

    @property
    def total_filled(self) -> int:
        return len(self._filled_orders)
