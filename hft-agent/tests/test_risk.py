"""Tests for risk management."""

import numpy as np
import pytest

from core.risk.fragility import FragilityDetector, FragilityState
from core.risk.kelly import FractionalKelly


class TestFractionalKelly:
    def test_positive_edge(self):
        """Positive expected return should produce positive position size."""
        kelly = FractionalKelly(kelly_fraction=0.25, max_position_pct=0.05)
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 1000)

        size = kelly.optimal_position_size(
            expected_return=0.001,
            returns_history=returns,
            portfolio_value=100_000,
            price=100.0,
        )
        assert size > 0

    def test_negative_edge(self):
        """Negative expected return should produce negative position size."""
        kelly = FractionalKelly(kelly_fraction=0.25, max_position_pct=0.05)
        returns = np.random.normal(-0.001, 0.02, 1000)

        size = kelly.optimal_position_size(
            expected_return=-0.001,
            returns_history=returns,
            portfolio_value=100_000,
            price=100.0,
        )
        assert size < 0

    def test_position_cap(self):
        """Position size should not exceed max_position_pct."""
        kelly = FractionalKelly(kelly_fraction=1.0, max_position_pct=0.05)
        returns = np.random.normal(0.01, 0.01, 1000)  # High edge

        size = kelly.optimal_position_size(
            expected_return=0.01,
            returns_history=returns,
            portfolio_value=100_000,
            price=100.0,
        )
        max_shares = 100_000 * 0.05 / 100.0  # 50 shares
        assert abs(size) <= max_shares + 1  # Allow rounding

    def test_fractional_reduces_size(self):
        """Lower Kelly fraction should produce smaller positions."""
        returns = np.random.normal(0.001, 0.02, 1000)

        kelly_full = FractionalKelly(kelly_fraction=1.0, max_position_pct=1.0)
        kelly_quarter = FractionalKelly(kelly_fraction=0.25, max_position_pct=1.0)

        size_full = kelly_full.optimal_position_size(0.001, returns, 100_000, 100.0)
        size_quarter = kelly_quarter.optimal_position_size(0.001, returns, 100_000, 100.0)

        assert abs(size_quarter) < abs(size_full)

    def test_log_growth_rate(self):
        """Kelly growth rate should be concave in fraction."""
        kelly = FractionalKelly()
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 10000)

        g_small = kelly.kelly_growth_rate(0.1, returns)
        g_optimal, _ = kelly.find_optimal_fraction(returns)
        g_at_optimal = kelly.kelly_growth_rate(g_optimal, returns)
        g_overleveraged = kelly.kelly_growth_rate(5.0, returns)

        # Growth at optimal should be highest
        assert g_at_optimal >= g_small
        # Over-leveraged should have lower growth (possibly negative)
        assert g_at_optimal >= g_overleveraged


class TestFragilityDetector:
    def test_fragile_strategy(self):
        """Strategy that loses money when vol increases should be fragile."""
        np.random.seed(42)
        n = 500
        # Market returns with increasing vol
        returns = np.random.normal(0, 0.02, n)
        # P&L that is negatively correlated with vol
        vol = np.abs(returns)
        pnl = -vol * 100 + np.random.normal(0.01, 0.1, n)  # Loses when vol spikes

        detector = FragilityDetector(vol_sensitivity_threshold=-0.3)
        report = detector.assess(pnl, returns, window=50)

        # Should detect fragility
        assert report.vol_sensitivity < 0

    def test_antifragile_strategy(self):
        """Strategy that profits from vol increases should be antifragile."""
        np.random.seed(42)
        n = 500
        returns = np.random.normal(0, 0.02, n)
        vol = np.abs(returns)
        pnl = vol * 100 + np.random.normal(0, 0.1, n)  # Profits when vol spikes

        detector = FragilityDetector(vol_sensitivity_threshold=-0.3)
        report = detector.assess(pnl, returns, window=50)

        assert report.vol_sensitivity > 0
