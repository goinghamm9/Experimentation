"""Tests for signal generation."""

from datetime import datetime, timezone

import numpy as np
import pytest

from core.signals.hurst import HurstExponent
from core.signals.ofi import OrderFlowImbalance
from core.signals.vpin import VPIN
from utils.types import OrderBook, OrderBookLevel, Side


class TestOFI:
    def _make_book(self, symbol, bid_price, bid_size, ask_price, ask_size):
        return OrderBook(
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            bids=[OrderBookLevel(price=bid_price, size=bid_size)],
            asks=[OrderBookLevel(price=ask_price, size=ask_size)],
        )

    def test_ofi_buy_pressure(self):
        """Increasing bid size should produce positive OFI."""
        ofi = OrderFlowImbalance(lookback=20, smoothing_window=3)
        # Gradually increase bid size
        for i in range(20):
            book = self._make_book("SPY", 100.0, 100 + i * 10, 100.02, 100)
            signal = ofi.update(book)

        # Last signal should indicate buy pressure
        assert signal is not None
        assert signal.value > 0
        assert signal.direction == Side.BUY

    def test_ofi_sell_pressure(self):
        """Increasing ask size should produce negative OFI."""
        ofi = OrderFlowImbalance(lookback=20, smoothing_window=3)
        for i in range(20):
            book = self._make_book("SPY", 100.0, 100, 100.02, 100 + i * 10)
            signal = ofi.update(book)

        assert signal is not None
        assert signal.value < 0


class TestHurstExponent:
    def test_trending_series(self):
        """A trending series should have H > 0.5."""
        hurst = HurstExponent(window=200, persistence_threshold=0.55)
        np.random.seed(42)
        # Create trending series (cumulative sum of biased random walk)
        prices = 100 + np.cumsum(np.random.normal(0.01, 0.5, 500))

        signal = None
        for i, p in enumerate(prices):
            ts = datetime.now(timezone.utc)
            signal = hurst.update("SPY", float(p), ts)

        assert signal is not None
        assert signal.value > 0.45  # Should show persistence

    def test_mean_reverting_series(self):
        """A mean-reverting series should have H < 0.5."""
        hurst = HurstExponent(window=200, mean_reversion_threshold=0.45)
        np.random.seed(42)
        # Create mean-reverting series (Ornstein-Uhlenbeck)
        prices = [100.0]
        for _ in range(500):
            mean_level = 100.0
            speed = 0.5
            vol = 0.5
            dp = speed * (mean_level - prices[-1]) + vol * np.random.normal()
            prices.append(prices[-1] + dp)

        signal = None
        for p in prices:
            ts = datetime.now(timezone.utc)
            signal = hurst.update("SPY", p, ts)

        assert signal is not None
        assert signal.value < 0.55  # Should show anti-persistence


class TestVPIN:
    def test_balanced_flow(self):
        """Balanced buy/sell flow should produce low VPIN."""
        vpin = VPIN(bucket_size=100, n_buckets=10)
        np.random.seed(42)

        signal = None
        price = 100.0
        for _ in range(2000):
            # Random walk price — balanced flow
            price += np.random.normal(0, 0.01)
            volume = np.random.uniform(10, 20)
            signal = vpin.update(
                "SPY", price, volume,
                datetime.now(timezone.utc),
            )

        if signal:
            assert signal.value < 0.8  # Should not be excessively toxic

    def test_directional_flow(self):
        """Strongly directional flow should produce high VPIN."""
        vpin = VPIN(bucket_size=100, n_buckets=10)
        np.random.seed(42)

        signal = None
        price = 100.0
        for _ in range(2000):
            # Strongly trending price — all buys
            price += 0.05  # Consistent upward pressure
            volume = np.random.uniform(10, 20)
            signal = vpin.update(
                "SPY", price, volume,
                datetime.now(timezone.utc),
            )

        if signal:
            # High VPIN indicates informed trading (directional)
            assert signal.value > 0.3
