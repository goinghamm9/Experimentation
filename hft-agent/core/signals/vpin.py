"""
Volume-Synchronized Probability of Informed Trading (VPIN).

Based on:
- Easley, Lopez de Prado, O'Hara (2011): Flow Toxicity and Liquidity in a
  High Frequency World

VPIN measures order flow toxicity in real-time using volume-synchronized
sampling (the "volume clock"). High VPIN indicates informed trading is
occurring — market makers withdraw liquidity, spreads widen, and flash
crash probability increases.

VPIN produced a warning signal >1 hour before the May 6, 2010 Flash Crash.

For an HFT agent, VPIN serves as a dynamic regime indicator:
- Low VPIN: Normal market making / spread capture is safe
- High VPIN: Reduce exposure, widen quotes, or step aside entirely
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from math import erfc, sqrt

import numpy as np
from numpy.typing import NDArray

from utils.types import Regime, Signal


class VPIN:
    """Volume-Synchronized Probability of Informed Trading.

    Instead of sampling by time (which distorts the probability space),
    VPIN samples by volume, creating "volume buckets" of equal size.
    The buy/sell classification uses the Bulk Volume Classification (BVC)
    method from the original paper.
    """

    def __init__(
        self,
        bucket_size: float = 50_000,
        n_buckets: int = 50,
        toxicity_threshold: float = 0.7,
    ):
        """
        Args:
            bucket_size: Volume per bucket (shares).
            n_buckets: Number of buckets in the rolling window.
            toxicity_threshold: VPIN level above which flow is considered toxic.
        """
        self._bucket_size = bucket_size
        self._n_buckets = n_buckets
        self._toxicity_threshold = toxicity_threshold

        # Current bucket accumulation
        self._current_bucket_volume: dict[str, float] = {}
        self._current_bucket_buy_volume: dict[str, float] = {}
        self._prev_price: dict[str, float] = {}

        # Completed buckets
        self._buy_volumes: dict[str, deque] = {}
        self._sell_volumes: dict[str, deque] = {}

    def update(
        self,
        symbol: str,
        price: float,
        volume: float,
        timestamp: datetime,
    ) -> Signal | None:
        """Process a trade and compute VPIN if a bucket is completed.

        Uses Bulk Volume Classification (BVC):
        The fraction of volume classified as buys is:
            V_buy = V * CDF(dP / sigma_dP)
        where dP is the price change and sigma_dP is the standard
        deviation of price changes.
        """
        # Initialize state for new symbols
        if symbol not in self._current_bucket_volume:
            self._current_bucket_volume[symbol] = 0.0
            self._current_bucket_buy_volume[symbol] = 0.0
            self._buy_volumes[symbol] = deque(maxlen=self._n_buckets)
            self._sell_volumes[symbol] = deque(maxlen=self._n_buckets)

        # BVC classification
        prev_price = self._prev_price.get(symbol)
        self._prev_price[symbol] = price

        if prev_price is not None and prev_price > 0:
            dp = price - prev_price
            # Simple BVC: fraction of volume classified as buy
            # Uses the sign and magnitude of price change
            sigma = abs(dp) + 1e-10  # Avoid division by zero
            z = dp / sigma
            # CDF of standard normal approximation
            buy_fraction = 0.5 * erfc(-z / sqrt(2))
        else:
            buy_fraction = 0.5  # No directional info

        buy_volume = volume * buy_fraction
        sell_volume = volume * (1 - buy_fraction)

        self._current_bucket_volume[symbol] += volume
        self._current_bucket_buy_volume[symbol] += buy_volume

        # Check if bucket is complete
        if self._current_bucket_volume[symbol] < self._bucket_size:
            return None

        # Complete the bucket
        bucket_buy = self._current_bucket_buy_volume[symbol]
        bucket_sell = self._current_bucket_volume[symbol] - bucket_buy

        self._buy_volumes[symbol].append(bucket_buy)
        self._sell_volumes[symbol].append(bucket_sell)

        # Reset bucket
        overflow = self._current_bucket_volume[symbol] - self._bucket_size
        self._current_bucket_volume[symbol] = overflow
        self._current_bucket_buy_volume[symbol] = overflow * buy_fraction

        # Need at least n_buckets to compute VPIN
        if len(self._buy_volumes[symbol]) < self._n_buckets:
            return None

        # Compute VPIN
        buys = np.array(self._buy_volumes[symbol], dtype=np.float64)
        sells = np.array(self._sell_volumes[symbol], dtype=np.float64)
        total_per_bucket = buys + sells

        # VPIN = mean(|V_buy - V_sell|) / mean(V_total)
        imbalances = np.abs(buys - sells)
        vpin_value = float(np.sum(imbalances) / np.sum(total_per_bucket))

        # Determine regime
        is_toxic = vpin_value > self._toxicity_threshold

        return Signal(
            symbol=symbol,
            timestamp=timestamp,
            name="vpin",
            value=vpin_value,
            strength=min(vpin_value, 1.0),
            metadata={
                "is_toxic": is_toxic,
                "threshold": self._toxicity_threshold,
                "n_buckets": len(self._buy_volumes[symbol]),
                "avg_buy_pct": float(np.mean(buys / (total_per_bucket + 1e-10))),
            },
        )

    def is_toxic(self, symbol: str) -> bool:
        """Quick check if order flow is currently toxic."""
        if symbol not in self._buy_volumes:
            return False
        if len(self._buy_volumes[symbol]) < self._n_buckets:
            return False

        buys = np.array(self._buy_volumes[symbol], dtype=np.float64)
        sells = np.array(self._sell_volumes[symbol], dtype=np.float64)
        total = buys + sells
        imbalances = np.abs(buys - sells)
        vpin = float(np.sum(imbalances) / np.sum(total)) if np.sum(total) > 0 else 0
        return vpin > self._toxicity_threshold
