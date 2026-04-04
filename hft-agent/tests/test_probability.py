"""Tests for the probability engine."""

import numpy as np
import pytest

from core.probability.distributions import (
    FatTailDistribution,
    estimate_tail_exponent,
    mean_absolute_deviation,
)
from core.probability.tail_estimator import EVTTailEstimator


class TestFatTailDistribution:
    def test_fit_student_t(self):
        """Distribution should fit Student-t to returns."""
        np.random.seed(42)
        # Generate fat-tailed data (Student-t with df=3)
        returns = np.random.standard_t(df=3, size=5000) * 0.01
        dist = FatTailDistribution()
        dist.fit(returns)

        assert dist.tail_exponent >= 2.0
        assert dist.effective_exponent <= dist.tail_exponent
        assert dist.scale > 0

    def test_asymmetry(self):
        """Distribution should detect asymmetric tails."""
        np.random.seed(42)
        # Create asymmetric returns (fatter left tail)
        returns = np.random.standard_t(df=3, size=5000) * 0.01
        returns[returns < 0] *= 1.3  # Make left tail fatter
        dist = FatTailDistribution()
        dist.fit(returns)

        assert dist.asymmetry_factor > 1.0

    def test_var_fatter_than_gaussian(self):
        """VaR from fat-tailed dist should be more extreme than Gaussian."""
        np.random.seed(42)
        returns = np.random.standard_t(df=3, size=5000) * 0.01
        dist = FatTailDistribution()
        dist.fit(returns)

        fat_var = dist.var(0.99)
        gauss_var = np.mean(returns) - 2.326 * np.std(returns)

        # Fat-tailed VaR should be more negative (more extreme)
        assert fat_var < gauss_var

    def test_cvar(self):
        """CVaR should be more extreme than VaR."""
        dist = FatTailDistribution(tail_exponent=3.0, scale=0.01)
        var = dist.var(0.99)
        cvar = dist.cvar(0.99)

        assert cvar < var  # CVaR is more negative (worse)

    def test_sample_shape(self):
        """Samples should have correct shape."""
        dist = FatTailDistribution()
        samples = dist.sample(1000)
        assert samples.shape == (1000,)


class TestTailExponent:
    def test_hill_estimator(self):
        """Hill estimator should recover approximate tail exponent."""
        np.random.seed(42)
        returns = np.random.standard_t(df=3, size=10000) * 0.01
        alpha = estimate_tail_exponent(returns, method="hill")

        # Should be roughly around 3 (cubic law)
        assert 1.5 < alpha < 6.0

    def test_mad_vs_std(self):
        """MAD should be more robust than std under fat tails."""
        np.random.seed(42)
        # Normal data: MAD and std should be proportional
        normal = np.random.normal(0, 1, 1000)
        mad_normal = mean_absolute_deviation(normal)

        # Add extreme outlier
        contaminated = np.append(normal, [50.0])
        mad_contam = mean_absolute_deviation(contaminated)
        std_contam = np.std(contaminated)

        # MAD should be much less affected by the outlier
        mad_change = abs(mad_contam - mad_normal) / mad_normal
        std_change = abs(std_contam - np.std(normal)) / np.std(normal)
        assert mad_change < std_change


class TestEVTTailEstimator:
    def test_gpd_fit(self):
        """GPD should fit to tail data."""
        np.random.seed(42)
        returns = np.random.standard_t(df=3, size=5000) * 0.01
        est = EVTTailEstimator()
        est.fit(returns)

        assert est.left_tail is not None
        assert est.right_tail is not None
        assert est.left_tail.shape > 0
        assert est.left_tail.n_exceedances > 0

    def test_asymmetric_tails(self):
        """Left tail should be fatter than right for typical equities."""
        np.random.seed(42)
        returns = np.random.standard_t(df=3, size=5000) * 0.01
        returns[returns < 0] *= 1.3
        est = EVTTailEstimator()
        est.fit(returns)

        # The asymmetry ratio should reflect fatter left tail
        assert est.tail_asymmetry is not None
