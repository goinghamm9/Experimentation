"""
Hurst Exponent for regime detection.

Based on:
- Qian & Rasheed (2004): Hurst Exponent and Financial Market Predictability
- Mandelbrot's Fractal Market Hypothesis

H = 0.5: Random walk (no predictability)
H > 0.5: Persistent/trending (momentum strategies work)
H < 0.5: Anti-persistent/mean-reverting (mean-reversion strategies work)

The Hurst exponent tells the agent WHICH strategy regime is active,
preventing the catastrophic error of applying momentum logic in a
mean-reverting market or vice versa.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from utils.types import Regime, Side, Signal


class HurstExponent:
    """Rolling Hurst exponent computation for regime detection.

    Uses Rescaled Range (R/S) analysis, which is more robust than
    DFA for short time series typical in HFT.
    """

    def __init__(
        self,
        window: int = 500,
        persistence_threshold: float = 0.55,
        mean_reversion_threshold: float = 0.45,
    ):
        self._window = window
        self._persistence_threshold = persistence_threshold
        self._mean_reversion_threshold = mean_reversion_threshold
        self._price_history: dict[str, deque] = {}

    def update(self, symbol: str, price: float, timestamp: datetime) -> Signal | None:
        """Update with new price and compute Hurst if enough data.

        Returns Signal with regime classification.
        """
        if symbol not in self._price_history:
            self._price_history[symbol] = deque(maxlen=self._window)
        self._price_history[symbol].append(price)

        if len(self._price_history[symbol]) < self._window:
            return None

        prices = np.array(self._price_history[symbol], dtype=np.float64)
        returns = np.diff(np.log(prices))

        h = self._compute_hurst_rs(returns)

        # Classify regime
        regime = Regime.RANDOM_WALK
        if h > self._persistence_threshold:
            regime = Regime.TRENDING
        elif h < self._mean_reversion_threshold:
            regime = Regime.MEAN_REVERTING

        # Strength: how far from 0.5 (random walk)
        strength = min(abs(h - 0.5) * 4, 1.0)  # Scale to [0, 1]

        return Signal(
            symbol=symbol,
            timestamp=timestamp,
            name="hurst",
            value=h,
            strength=strength,
            metadata={
                "regime": regime.value,
                "persistence_threshold": self._persistence_threshold,
                "mean_reversion_threshold": self._mean_reversion_threshold,
            },
        )

    def get_regime(self, symbol: str) -> Regime:
        """Get the current regime for a symbol based on last Hurst calculation."""
        if symbol not in self._price_history:
            return Regime.RANDOM_WALK

        if len(self._price_history[symbol]) < self._window:
            return Regime.RANDOM_WALK

        prices = np.array(self._price_history[symbol], dtype=np.float64)
        returns = np.diff(np.log(prices))
        h = self._compute_hurst_rs(returns)

        if h > self._persistence_threshold:
            return Regime.TRENDING
        elif h < self._mean_reversion_threshold:
            return Regime.MEAN_REVERTING
        return Regime.RANDOM_WALK

    @staticmethod
    def _compute_hurst_rs(returns: NDArray[np.float64]) -> float:
        """Compute Hurst exponent using Rescaled Range (R/S) analysis.

        For each sub-series length n, compute:
        1. Mean-adjusted cumulative deviations
        2. Range R = max(cumdev) - min(cumdev)
        3. Standard deviation S
        4. R/S ratio

        Then fit log(R/S) vs log(n) to get the Hurst exponent.
        """
        n = len(returns)
        if n < 20:
            return 0.5

        # Use multiple sub-series lengths
        min_len = 10
        max_len = n // 2
        lengths = []
        rs_values = []

        length = min_len
        while length <= max_len:
            n_subseries = n // length
            if n_subseries < 1:
                break

            rs_list = []
            for i in range(n_subseries):
                subseries = returns[i * length : (i + 1) * length]
                mean = np.mean(subseries)
                deviations = subseries - mean
                cumdev = np.cumsum(deviations)

                r = np.max(cumdev) - np.min(cumdev)
                s = np.std(subseries, ddof=1)

                if s > 0:
                    rs_list.append(r / s)

            if rs_list:
                lengths.append(length)
                rs_values.append(np.mean(rs_list))

            length = int(length * 1.5)  # Logarithmic spacing

        if len(lengths) < 3:
            return 0.5

        # Linear regression in log-log space: log(R/S) = H * log(n) + c
        log_n = np.log(np.array(lengths, dtype=np.float64))
        log_rs = np.log(np.array(rs_values, dtype=np.float64))

        # Least squares fit
        A = np.vstack([log_n, np.ones(len(log_n))]).T
        result = np.linalg.lstsq(A, log_rs, rcond=None)
        hurst = float(result[0][0])

        # Clamp to valid range
        return max(0.0, min(1.0, hurst))
