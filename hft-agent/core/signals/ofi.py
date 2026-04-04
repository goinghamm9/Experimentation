"""
Order Flow Imbalance (OFI) signal.

Based on:
- Cont, Kukanov, Stoikov (2011): The Price Impact of Order Book Events
  "Linear relation between OFI and price changes, R² ~65%"

OFI measures the net pressure from the order book:
  OFI = (bid_size_change * bid_price_improved) - (ask_size_change * ask_price_improved)

This is the PRIMARY short-term price predictor for HFT, as it captures
the endogenous order-flow dynamics that drive price formation.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from utils.types import OrderBook, Side, Signal


class OrderFlowImbalance:
    """Computes Order Flow Imbalance from order book updates.

    OFI captures the net buying/selling pressure at the best bid/ask.
    It is the most important microstructure signal for short-term
    price prediction (R² ~65% per Cont et al. 2011).
    """

    def __init__(self, lookback: int = 50, smoothing_window: int = 10):
        self._lookback = lookback
        self._smoothing_window = smoothing_window
        self._prev_book: dict[str, OrderBook] = {}
        self._ofi_history: dict[str, deque] = {}

    def update(self, book: OrderBook) -> Signal | None:
        """Compute OFI from a new order book snapshot.

        Returns a Signal if enough history is available.
        """
        symbol = book.symbol
        prev = self._prev_book.get(symbol)

        if prev is None or not book.bids or not book.asks:
            self._prev_book[symbol] = book
            return None

        if not prev.bids or not prev.asks:
            self._prev_book[symbol] = book
            return None

        # Compute OFI components
        # Bid side: if bid price improved, count new size; if same, count delta
        bid_ofi = 0.0
        if book.bids[0].price > prev.bids[0].price:
            bid_ofi = book.bids[0].size
        elif book.bids[0].price == prev.bids[0].price:
            bid_ofi = book.bids[0].size - prev.bids[0].size
        else:
            bid_ofi = -prev.bids[0].size

        # Ask side: if ask price improved (lower), count negatively
        ask_ofi = 0.0
        if book.asks[0].price < prev.asks[0].price:
            ask_ofi = -book.asks[0].size
        elif book.asks[0].price == prev.asks[0].price:
            ask_ofi = -(book.asks[0].size - prev.asks[0].size)
        else:
            ask_ofi = prev.asks[0].size

        ofi_value = bid_ofi + ask_ofi

        # Store history
        if symbol not in self._ofi_history:
            self._ofi_history[symbol] = deque(maxlen=self._lookback)
        self._ofi_history[symbol].append(ofi_value)

        self._prev_book[symbol] = book

        if len(self._ofi_history[symbol]) < self._smoothing_window:
            return None

        # Smoothed OFI (exponential moving average)
        history = np.array(self._ofi_history[symbol], dtype=np.float64)
        weights = np.exp(np.linspace(-1, 0, len(history)))
        weights /= weights.sum()
        smoothed_ofi = float(np.dot(weights, history))

        # Normalize to [-1, 1] using recent range
        ofi_std = np.std(history)
        if ofi_std > 0:
            normalized = np.clip(smoothed_ofi / (3 * ofi_std), -1, 1)
        else:
            normalized = 0.0

        # Direction
        direction = None
        if normalized > 0.1:
            direction = Side.BUY
        elif normalized < -0.1:
            direction = Side.SELL

        return Signal(
            symbol=symbol,
            timestamp=book.timestamp,
            name="ofi",
            value=smoothed_ofi,
            direction=direction,
            strength=abs(float(normalized)),
            metadata={
                "raw_ofi": ofi_value,
                "smoothed": smoothed_ofi,
                "normalized": float(normalized),
                "bid_ofi": bid_ofi,
                "ask_ofi": ask_ofi,
            },
        )

    def get_cumulative_ofi(self, symbol: str, window: int | None = None) -> float:
        """Get cumulative OFI over recent window."""
        if symbol not in self._ofi_history:
            return 0.0
        history = list(self._ofi_history[symbol])
        if window:
            history = history[-window:]
        return float(np.sum(history))
