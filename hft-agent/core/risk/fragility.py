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

from core.probability.distributions import mean_absolute_deviation


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

    Measures the sensitivity of realized P&L to realized volatility
    changes — the practical implementation of Taleb & Douady's
    mathematical fragility framework.
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
        """Assess strategy fragility from P&L and return series.

        Method:
        1. Compute rolling realized volatility
        2. Compute rolling P&L
        3. Measure correlation between vol changes and P&L changes
        4. Measure convexity (gamma) of the P&L-to-vol relationship

        Args:
            pnl_series: Daily or per-trade P&L values.
            return_series: Corresponding market returns.
            window: Rolling window for volatility computation.
        """
        n = min(len(pnl_series), len(return_series))
        if n < window + 10:
            return FragilityReport(
                state=FragilityState.ROBUST,
                vega=0.0,
                gamma=0.0,
                vol_sensitivity=0.0,
                recommendation="Insufficient data for fragility assessment",
            )

        pnl = pnl_series[:n]
        returns = return_series[:n]

        # Rolling realized volatility (MAD-based for fat-tail robustness)
        vol_series = np.array([
            mean_absolute_deviation(returns[max(0, i - window):i])
            for i in range(window, n)
        ])

        # Corresponding P&L for each vol observation
        pnl_windowed = pnl[window:]

        # Trim to same length
        min_len = min(len(vol_series), len(pnl_windowed))
        vol_series = vol_series[:min_len]
        pnl_windowed = pnl_windowed[:min_len]

        if len(vol_series) < 10:
            return FragilityReport(
                state=FragilityState.ROBUST,
                vega=0.0,
                gamma=0.0,
                vol_sensitivity=0.0,
                recommendation="Insufficient data",
            )

        # Vega: dPnL/dVol (first derivative)
        # Use changes to avoid level effects
        dvol = np.diff(vol_series)
        dpnl = np.diff(pnl_windowed)

        # Avoid division by zero
        mask = np.abs(dvol) > 1e-10
        if np.sum(mask) < 5:
            return FragilityReport(
                state=FragilityState.ROBUST,
                vega=0.0,
                gamma=0.0,
                vol_sensitivity=0.0,
                recommendation="Insufficient volatility variation",
            )

        # Linear regression: dPnL = vega * dVol + epsilon
        vega = float(np.sum(dpnl[mask] * dvol[mask]) / np.sum(dvol[mask] ** 2))

        # Gamma: d²PnL/dVol² (convexity)
        # Fit quadratic: PnL = a * vol^2 + b * vol + c
        if len(vol_series) > 20:
            coeffs = np.polyfit(vol_series, pnl_windowed, 2)
            gamma = float(2 * coeffs[0])  # Second derivative of quadratic
        else:
            gamma = 0.0

        # Normalize vega to [-1, 1]
        pnl_std = np.std(dpnl)
        vol_std = np.std(dvol)
        if pnl_std > 0 and vol_std > 0:
            vol_sensitivity = float(np.corrcoef(dpnl[mask], dvol[mask])[0, 1])
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
