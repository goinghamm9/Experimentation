"""Base class for market data feeds."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterator, Callable

from utils.types import Bar, OrderBook, Tick


class DataFeed(ABC):
    """Abstract base class for real-time market data feeds."""

    def __init__(self, symbols: list[str]):
        self.symbols = symbols
        self._tick_callbacks: list[Callable] = []
        self._bar_callbacks: list[Callable] = []
        self._orderbook_callbacks: list[Callable] = []
        self._running = False

    def on_tick(self, callback: Callable) -> None:
        """Register a callback for tick data."""
        self._tick_callbacks.append(callback)

    def on_bar(self, callback: Callable) -> None:
        """Register a callback for bar data."""
        self._bar_callbacks.append(callback)

    def on_orderbook(self, callback: Callable) -> None:
        """Register a callback for order book updates."""
        self._orderbook_callbacks.append(callback)

    async def _emit_tick(self, tick: Tick) -> None:
        for cb in self._tick_callbacks:
            if asyncio.iscoroutinefunction(cb):
                await cb(tick)
            else:
                cb(tick)

    async def _emit_bar(self, bar: Bar) -> None:
        for cb in self._bar_callbacks:
            if asyncio.iscoroutinefunction(cb):
                await cb(bar)
            else:
                cb(bar)

    async def _emit_orderbook(self, ob: OrderBook) -> None:
        for cb in self._orderbook_callbacks:
            if asyncio.iscoroutinefunction(cb):
                await cb(ob)
            else:
                cb(ob)

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the data source."""
        ...

    @abstractmethod
    async def subscribe(self) -> None:
        """Subscribe to market data for configured symbols."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start receiving data. Blocks until stopped."""
        ...

    async def stop(self) -> None:
        """Stop receiving data."""
        self._running = False

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the data source."""
        ...
