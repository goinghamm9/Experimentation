"""Probability engine: fat-tailed distributions and tail estimation."""

from .distributions import (
    FatTailDistribution,
    estimate_tail_exponent,
    interquartile_range,
    mean_absolute_deviation,
)
from .tail_estimator import EVTTailEstimator, TailEstimate

__all__ = [
    "FatTailDistribution",
    "EVTTailEstimator",
    "TailEstimate",
    "estimate_tail_exponent",
    "mean_absolute_deviation",
    "interquartile_range",
]
