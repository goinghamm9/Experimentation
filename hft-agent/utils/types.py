"""Common type definitions for the HFT agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Side(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Regime(Enum):
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"
    RANDOM_WALK = "random_walk"
    TOXIC = "toxic"  # High VPIN - informed trading detected


@dataclass
class Tick:
    symbol: str
    timestamp: datetime
    price: float
    size: float
    side: Side | None = None


@dataclass
class Bar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float | None = None


@dataclass
class OrderBookLevel:
    price: float
    size: float


@dataclass
class OrderBook:
    symbol: str
    timestamp: datetime
    bids: list[OrderBookLevel] = field(default_factory=list)
    asks: list[OrderBookLevel] = field(default_factory=list)

    @property
    def mid_price(self) -> float | None:
        if self.bids and self.asks:
            return (self.bids[0].price + self.asks[0].price) / 2
        return None

    @property
    def spread(self) -> float | None:
        if self.bids and self.asks:
            return self.asks[0].price - self.bids[0].price
        return None

    @property
    def spread_bps(self) -> float | None:
        mid = self.mid_price
        spread = self.spread
        if mid and spread and mid > 0:
            return (spread / mid) * 10_000
        return None


@dataclass
class Order:
    symbol: str
    side: Side
    qty: float
    order_type: OrderType
    limit_price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    order_id: str | None = None
    filled_price: float | None = None
    filled_qty: float = 0.0
    timestamp: datetime | None = None


@dataclass
class Position:
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    @property
    def market_value(self) -> float:
        return self.qty * self.current_price

    @property
    def side(self) -> Side | None:
        if self.qty > 0:
            return Side.BUY
        elif self.qty < 0:
            return Side.SELL
        return None


@dataclass
class Signal:
    symbol: str
    timestamp: datetime
    name: str
    value: float
    direction: Side | None = None
    strength: float = 0.0  # 0-1 normalized
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioState:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    total_equity: float = 0.0
    daily_pnl: float = 0.0
    daily_return: float = 0.0
    max_drawdown: float = 0.0
    peak_equity: float = 0.0

    @property
    def total_exposure(self) -> float:
        return sum(abs(p.market_value) for p in self.positions.values())

    @property
    def exposure_pct(self) -> float:
        if self.total_equity > 0:
            return self.total_exposure / self.total_equity
        return 0.0
