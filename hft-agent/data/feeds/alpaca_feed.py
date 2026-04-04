"""
Alpaca real-time data feed via websocket.

Alpaca provides:
- Real-time trades and quotes via websocket
- Free IEX data feed (15-min delayed quotes for non-subscribers)
- SIP feed for full market data (paid)
- Bar aggregation at 1-min intervals
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from utils.logging import get_logger
from utils.types import Bar, OrderBook, OrderBookLevel, Side, Tick

from .base import DataFeed

logger = get_logger(__name__)


class AlpacaDataFeed(DataFeed):
    """Real-time data feed from Alpaca Markets."""

    def __init__(
        self,
        symbols: list[str],
        api_key: str,
        secret_key: str,
        feed: str = "iex",
    ):
        super().__init__(symbols)
        self._api_key = api_key
        self._secret_key = secret_key
        self._feed = feed
        self._stream = None

    async def connect(self) -> None:
        """Connect to Alpaca streaming API."""
        try:
            from alpaca_trade_api.stream import Stream

            self._stream = Stream(
                self._api_key,
                self._secret_key,
                data_feed=self._feed,
            )
            logger.info("alpaca_feed_connected", feed=self._feed)
        except ImportError:
            logger.error("alpaca_trade_api not installed")
            raise

    async def subscribe(self) -> None:
        """Subscribe to trades, quotes, and bars."""
        if not self._stream:
            raise RuntimeError("Not connected")

        # Subscribe to trades
        for symbol in self.symbols:
            self._stream.subscribe_trades(self._handle_trade, symbol)
            self._stream.subscribe_quotes(self._handle_quote, symbol)
            self._stream.subscribe_bars(self._handle_bar, symbol)

        logger.info("alpaca_subscribed", symbols=self.symbols)

    async def _handle_trade(self, trade: object) -> None:
        """Convert Alpaca trade to internal Tick format."""
        tick = Tick(
            symbol=trade.symbol,  # type: ignore
            timestamp=trade.timestamp,  # type: ignore
            price=float(trade.price),  # type: ignore
            size=float(trade.size),  # type: ignore
        )
        await self._emit_tick(tick)

    async def _handle_quote(self, quote: object) -> None:
        """Convert Alpaca quote to internal OrderBook format."""
        ob = OrderBook(
            symbol=quote.symbol,  # type: ignore
            timestamp=quote.timestamp,  # type: ignore
            bids=[OrderBookLevel(price=float(quote.bid_price), size=float(quote.bid_size))],  # type: ignore
            asks=[OrderBookLevel(price=float(quote.ask_price), size=float(quote.ask_size))],  # type: ignore
        )
        await self._emit_orderbook(ob)

    async def _handle_bar(self, bar: object) -> None:
        """Convert Alpaca bar to internal Bar format."""
        b = Bar(
            symbol=bar.symbol,  # type: ignore
            timestamp=bar.timestamp,  # type: ignore
            open=float(bar.open),  # type: ignore
            high=float(bar.high),  # type: ignore
            low=float(bar.low),  # type: ignore
            close=float(bar.close),  # type: ignore
            volume=float(bar.volume),  # type: ignore
            vwap=float(bar.vwap) if hasattr(bar, "vwap") else None,  # type: ignore
        )
        await self._emit_bar(b)

    async def start(self) -> None:
        """Start the Alpaca data stream."""
        if not self._stream:
            raise RuntimeError("Not connected")
        self._running = True
        logger.info("alpaca_feed_started")
        # The Alpaca stream runs its own event loop
        await asyncio.get_event_loop().run_in_executor(None, self._stream.run)

    async def stop(self) -> None:
        """Stop the stream."""
        self._running = False
        if self._stream:
            self._stream.stop()

    async def disconnect(self) -> None:
        """Disconnect from Alpaca."""
        await self.stop()
        self._stream = None
        logger.info("alpaca_feed_disconnected")
