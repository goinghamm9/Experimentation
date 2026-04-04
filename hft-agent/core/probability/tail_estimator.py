"""
Tail risk estimation using Extreme Value Theory (EVT).

Based on:
- LeBaron & Samanta (2004): Extreme Value Theory and Fat Tails in Equity Markets
- Cirillo & Taleb (2016): dual-distribution technique for bounded variables
- Taleb (2012): metaprobability correction for tail exponents

Uses Generalized Pareto Distribution (GPD) for peaks-over-threshold modeling.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats
from scipy.optimize import minimize


@dataclass
class TailEstimate:
    """Result of tail estimation."""
    shape: float       # xi parameter (positive = heavy tail)
    scale: float       # sigma parameter
    threshold: float   # u - threshold used
    n_exceedances: int
    tail_exponent: float  # alpha = 1/xi
    corrected_exponent: float  # After metaprobability correction


class EVTTailEstimator:
    """Extreme Value Theory tail estimator using GPD.

    For equity returns, we fit GPD to the peaks over a high threshold
    to model the tail behavior separately from the body of the distribution.
    """

    def __init__(self, metaprobability_discount: float = 0.85):
        """
        Args:
            metaprobability_discount: Multiplier for tail exponent to account
                for estimation uncertainty (Taleb 2012). Lower = more conservative.
        """
        self.metaprobability_discount = metaprobability_discount
        self._left_tail: TailEstimate | None = None
        self._right_tail: TailEstimate | None = None

    def fit(
        self,
        returns: NDArray[np.float64],
        threshold_quantile: float = 0.95,
    ) -> None:
        """Fit GPD to both tails of the return distribution.

        Args:
            returns: Array of returns.
            threshold_quantile: Quantile to use as threshold (e.g., 0.95 = top 5%).
        """
        # Left tail (losses)
        losses = -returns[returns < 0]
        if len(losses) > 20:
            self._left_tail = self._fit_tail(losses, threshold_quantile)

        # Right tail (gains)
        gains = returns[returns > 0]
        if len(gains) > 20:
            self._right_tail = self._fit_tail(gains, threshold_quantile)

    def _fit_tail(
        self,
        data: NDArray[np.float64],
        threshold_quantile: float,
    ) -> TailEstimate:
        """Fit GPD to one tail."""
        threshold = float(np.quantile(data, threshold_quantile))
        exceedances = data[data > threshold] - threshold

        if len(exceedances) < 5:
            # Not enough data; use default cubic law
            return TailEstimate(
                shape=1 / 3.0,
                scale=float(np.std(exceedances)) if len(exceedances) > 0 else 0.01,
                threshold=threshold,
                n_exceedances=len(exceedances),
                tail_exponent=3.0,
                corrected_exponent=3.0 * self.metaprobability_discount,
            )

        # Fit GPD using MLE
        shape, loc, scale = stats.genpareto.fit(exceedances, floc=0)

        tail_exponent = 1.0 / shape if shape > 0 else float("inf")
        corrected_exponent = tail_exponent * self.metaprobability_discount

        return TailEstimate(
            shape=shape,
            scale=scale,
            threshold=threshold,
            n_exceedances=len(exceedances),
            tail_exponent=tail_exponent,
            corrected_exponent=corrected_exponent,
        )

    @property
    def left_tail(self) -> TailEstimate | None:
        return self._left_tail

    @property
    def right_tail(self) -> TailEstimate | None:
        return self._right_tail

    @property
    def tail_asymmetry(self) -> float | None:
        """Ratio of left to right tail exponents. > 1 means left tail is fatter."""
        if self._left_tail and self._right_tail:
            if self._right_tail.corrected_exponent > 0:
                return self._left_tail.corrected_exponent / self._right_tail.corrected_exponent
        return None

    def exceedance_probability(self, loss: float, side: str = "left") -> float:
        """P(X > loss) using the fitted GPD tail.

        This gives a much more accurate estimate of extreme event probability
        than assuming a Gaussian distribution.
        """
        tail = self._left_tail if side == "left" else self._right_tail
        if tail is None:
            return 0.0

        excess = abs(loss) - tail.threshold
        if excess <= 0:
            return 1.0  # Below threshold, handled by body of distribution

        prob = stats.genpareto.sf(excess, tail.shape, scale=tail.scale)
        # Scale by the fraction of data above threshold
        return float(prob * (tail.n_exceedances / 1000))  # Approximate

    def expected_shortfall_evt(
        self,
        confidence: float = 0.99,
        side: str = "left",
    ) -> float | None:
        """Expected Shortfall using EVT (more accurate than empirical for extreme quantiles).

        ES_p = VaR_p / (1 - xi) + (sigma - xi * u) / (1 - xi)
        where xi = shape, sigma = scale, u = threshold.
        """
        tail = self._left_tail if side == "left" else self._right_tail
        if tail is None or tail.shape >= 1.0:
            return None

        alpha = 1.0 - confidence
        var = self.var_evt(confidence, side)
        if var is None:
            return None

        es = var / (1.0 - tail.shape) + (tail.scale - tail.shape * tail.threshold) / (
            1.0 - tail.shape
        )
        return float(es)

    def var_evt(self, confidence: float = 0.99, side: str = "left") -> float | None:
        """Value at Risk using EVT tail model."""
        tail = self._left_tail if side == "left" else self._right_tail
        if tail is None:
            return None

        alpha = 1.0 - confidence
        var = tail.threshold + (tail.scale / tail.shape) * (
            (alpha * 1000 / tail.n_exceedances) ** (-tail.shape) - 1
        )
        return float(var)
