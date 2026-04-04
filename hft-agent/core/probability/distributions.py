"""
Fat-tailed distribution modeling for HFT.

Based on:
- Taleb (2020): Statistical Consequences of Fat Tails
- Gabaix (2009): Power Laws in Economics (cubic law, exponent ~3)
- Taleb (2012): How We Tend to Overestimate Power-Law Tail Exponents
- Bouchaud & Potters (1999): Theory of Financial Risk

Key principle: Under fat tails, the empirical distribution is NOT the true
distribution. Sample means are biased. Use MAD instead of standard deviation.
The tail is always fatter than measured (metaprobability correction).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy import stats
from scipy.optimize import minimize_scalar


class FatTailDistribution:
    """Asymmetric Student-t / power-law distribution for returns.

    Models returns as a Student-t distribution with:
    - Tail exponent (degrees of freedom) ~3 (cubic law)
    - Asymmetric tails (left fatter than right)
    - Metaprobability correction (Taleb 2012)
    """

    def __init__(
        self,
        tail_exponent: float = 3.0,
        tail_exponent_min: float = 2.0,
        asymmetry_factor: float = 1.15,
        loc: float = 0.0,
        scale: float = 1.0,
    ):
        self.tail_exponent = tail_exponent
        self.tail_exponent_min = tail_exponent_min
        self.asymmetry_factor = asymmetry_factor
        self.loc = loc
        self.scale = scale

        # Effective tail exponent after metaprobability correction (Taleb 2012):
        # When uncertainty exists about the exponent, the effective exponent
        # corresponds to the minimum possible value.
        self.effective_exponent = max(tail_exponent_min, tail_exponent * 0.85)

    def fit(self, returns: NDArray[np.float64]) -> None:
        """Fit distribution to observed returns using MLE with metaprobability correction."""
        # Fit Student-t via MLE
        df, loc, scale = stats.t.fit(returns)

        self.tail_exponent = max(self.tail_exponent_min, df)
        self.loc = loc
        self.scale = scale

        # Apply metaprobability correction: effective exponent is biased lower
        # (Taleb 2012 - we systematically overestimate the exponent)
        self.effective_exponent = max(
            self.tail_exponent_min,
            self.tail_exponent * 0.85,
        )

        # Estimate asymmetry from data
        negative_returns = returns[returns < 0]
        positive_returns = returns[returns > 0]
        if len(negative_returns) > 10 and len(positive_returns) > 10:
            left_tail = np.percentile(np.abs(negative_returns), 99)
            right_tail = np.percentile(positive_returns, 99)
            if right_tail > 0:
                self.asymmetry_factor = left_tail / right_tail

    def pdf(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """Probability density with asymmetric tails."""
        result = np.empty_like(x, dtype=np.float64)

        left_mask = x < self.loc
        right_mask = ~left_mask

        # Left tail: fatter (use effective exponent / asymmetry)
        left_scale = self.scale * self.asymmetry_factor
        result[left_mask] = stats.t.pdf(
            x[left_mask], df=self.effective_exponent, loc=self.loc, scale=left_scale
        )

        # Right tail: standard
        result[right_mask] = stats.t.pdf(
            x[right_mask], df=self.effective_exponent, loc=self.loc, scale=self.scale
        )

        # Renormalize
        total = np.sum(result)
        if total > 0:
            result /= total
            result *= len(result)  # Scale back to density

        return result

    def cdf(self, x: float) -> float:
        """CDF at point x, accounting for asymmetry on the left tail."""
        if x < self.loc:
            return stats.t.cdf(
                x, df=self.effective_exponent,
                loc=self.loc, scale=self.scale * self.asymmetry_factor,
            )
        return stats.t.cdf(x, df=self.effective_exponent, loc=self.loc, scale=self.scale)

    def tail_probability(self, threshold: float) -> float:
        """P(X < threshold) for left tail, P(X > threshold) for right tail.

        Uses the power-law approximation for extreme quantiles where
        Student-t converges to a Pareto tail.
        """
        if threshold < self.loc:
            return self.cdf(threshold)
        return 1.0 - self.cdf(threshold)

    def var(self, confidence: float = 0.99) -> float:
        """Value at Risk (negative return at given confidence).

        Uses the fat-tailed distribution, NOT Gaussian.
        """
        alpha = 1.0 - confidence
        return stats.t.ppf(alpha, df=self.effective_exponent, loc=self.loc, scale=self.scale)

    def cvar(self, confidence: float = 0.99, n_samples: int = 100_000) -> float:
        """Conditional Value at Risk (Expected Shortfall).

        Monte Carlo estimation using the fat-tailed distribution because
        analytical CVaR for asymmetric Student-t is not tractable.
        """
        samples = self.sample(n_samples)
        var_threshold = self.var(confidence)
        tail_samples = samples[samples <= var_threshold]
        if len(tail_samples) == 0:
            return var_threshold
        return float(np.mean(tail_samples))

    def sample(self, n: int) -> NDArray[np.float64]:
        """Generate samples from the asymmetric fat-tailed distribution."""
        # Generate from Student-t
        samples = stats.t.rvs(df=self.effective_exponent, loc=self.loc, scale=self.scale, size=n)

        # Apply asymmetry: stretch the left tail
        left_mask = samples < self.loc
        samples[left_mask] = (
            self.loc + (samples[left_mask] - self.loc) * self.asymmetry_factor
        )

        return samples


def estimate_tail_exponent(returns: NDArray[np.float64], method: str = "hill") -> float:
    """Estimate the power-law tail exponent using Hill estimator.

    The Hill estimator is the standard method for estimating the tail index
    of a heavy-tailed distribution. Per Taleb (2012), the result should be
    treated as an upper bound - the true tail is fatter.

    Args:
        returns: Array of return observations.
        method: Estimation method ('hill' or 'moment').

    Returns:
        Estimated tail exponent (alpha). Lower = fatter tails.
    """
    abs_returns = np.abs(returns)
    abs_returns = abs_returns[abs_returns > 0]
    abs_returns = np.sort(abs_returns)[::-1]  # Descending

    if method == "hill":
        # Use top 10% of observations for Hill estimator
        k = max(10, len(abs_returns) // 10)
        top_k = abs_returns[:k]
        threshold = abs_returns[k]

        if threshold <= 0:
            return 3.0  # Default to cubic law

        log_ratios = np.log(top_k / threshold)
        hill_estimate = 1.0 / np.mean(log_ratios)

        return float(hill_estimate)

    elif method == "moment":
        # Moment estimator (more robust but less efficient)
        k = max(10, len(abs_returns) // 10)
        top_k = abs_returns[:k]
        log_vals = np.log(top_k)
        m1 = np.mean(log_vals) - np.log(abs_returns[k]) if abs_returns[k] > 0 else 1.0
        m2 = np.mean(log_vals**2) - np.log(abs_returns[k]) ** 2 if abs_returns[k] > 0 else 1.0

        if m1 <= 0:
            return 3.0

        return float(1.0 / m1)

    return 3.0


def mean_absolute_deviation(returns: NDArray[np.float64]) -> float:
    """Mean Absolute Deviation - robust dispersion metric under fat tails.

    Per Taleb (2020), MAD is more reliable than standard deviation
    when the distribution has infinite or unstable variance (alpha < 4).
    """
    return float(np.mean(np.abs(returns - np.median(returns))))


def interquartile_range(returns: NDArray[np.float64]) -> float:
    """IQR - another robust dispersion metric for fat-tailed data."""
    return float(np.percentile(returns, 75) - np.percentile(returns, 25))
