"""
Fragility detection based on Taleb & Douady (2012).

Mathematical Definition of (Anti)Fragility:
- Fragility = negative sensitivity to dispersion (negative vega)
- Antifragility = positive sensitivity to dispersion (positive vega)
- The equivalence: gamma (convexity) <=> vega (vol sensitivity)

A strategy that is "short gamma" is FRAGILE: it profits in calm markets
but suffers disproportionately from volatility spikes. Many HFT market-making
strategies are inadvertently fragile — they collect small spreads repeatedly
but blow up on a single large move.

This module detects whether the agent's strategy is fragile, robust, or
antifragile by measuring the sensitivity of P&L to changes in realized
volatility.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray


class FragilityState(Enum):
    FRAGILE = "fragile"          # Negative vega — exposed to vol spikes
    ROBUST = "robust"            # Neutral — limited vol sensitivity
    ANTIFRAGILE = "antifragile"  # Positive vega — benefits from vol


@dataclass
class FragilityReport:
    """Fragility assessment of the trading strategy."""
    state: FragilityState
    vega: float             # Sensitivity of PnL to volatility
    gamma: float            # Second-order sensitivity (convexity)
    vol_sensitivity: float  # Normalized [-1, 1]
    recommendation: str


class FragilityDetector:
    """Detects fragility/antifragility of the agent's strategy.

    Taleb & Douady (2013): a payoff is fragile when it responds concavely to
    stress, so large moves hurt more than small moves help.
    """

    def __init__(self, vol_sensitivity_threshold: float = -0.5):
        """
        Args:
            vol_sensitivity_threshold: Below this, strategy is considered fragile.
        """
        self._threshold = vol_sensitivity_threshold

    def assess(
        self,
        pnl_series: NDArray[np.float64],
        return_series: NDArray[np.float64],
        window: int = 50,
    ) -> FragilityReport:
        """Assess fragility as the curvature of P&L against same-period market moves.

        vol_sensitivity is the correlation of P&L with the size of the move: negative
        means the strategy loses when moves are large (fragile). `window` is unused and
        kept for call compatibility.
        """
        n = min(len(pnl_series), len(return_series))
        if n < 30:
            return FragilityReport(
                state=FragilityState.ROBUST,
                vega=0.0,
                gamma=0.0,
                vol_sensitivity=0.0,
                recommendation="Insufficient data for fragility assessment",
            )

        pnl = np.asarray(pnl_series[:n], dtype=np.float64)
        returns = np.asarray(return_series[:n], dtype=np.float64)

        # Taleb-Douady: fragility is a concave response to the size of a move.
        # Fit pnl = a + b*r + g*r^2; g is the convexity (gamma), and the response to
        # the move's magnitude |r| (dispersion) plays the role of vega.
        x = np.column_stack([np.ones(n), returns, returns ** 2])
        coeffs, *_ = np.linalg.lstsq(x, pnl, rcond=None)
        gamma = float(2 * coeffs[2])

        size = np.abs(returns - np.median(returns))
        size_c = size - size.mean()
        vega = float(size_c @ (pnl - pnl.mean()) / (size_c @ size_c)) if size_c @ size_c > 0 else 0.0

        if np.std(pnl) > 0 and np.std(size) > 0:
            vol_sensitivity = float(np.corrcoef(pnl, size)[0, 1])
        else:
            vol_sensitivity = 0.0

        # Classify
        if vol_sensitivity < self._threshold:
            state = FragilityState.FRAGILE
            recommendation = (
                "FRAGILE: Strategy is short gamma/vega. "
                "Reduce position sizes, add tail hedges, or switch to convex strategies. "
                "Current strategy will suffer disproportionately from volatility spikes."
            )
        elif vol_sensitivity > abs(self._threshold):
            state = FragilityState.ANTIFRAGILE
            recommendation = (
                "ANTIFRAGILE: Strategy benefits from volatility. "
                "This is the desired payoff profile. Maintain current approach."
            )
        else:
            state = FragilityState.ROBUST
            recommendation = (
                "ROBUST: Strategy has limited volatility sensitivity. "
                "Acceptable risk profile."
            )

        return FragilityReport(
            state=state,
            vega=vega,
            gamma=gamma,
            vol_sensitivity=vol_sensitivity,
            recommendation=recommendation,
        )
