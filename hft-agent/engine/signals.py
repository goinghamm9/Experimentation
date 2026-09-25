"""Daily-bar signals and fat-tail estimators.

- Time-series momentum (Moskowitz, Ooi, Pedersen 2012): trend following produces
  convex, crisis-positive payoffs — the stocks-only way to own convexity.
- DFA Hurst exponent (Peng et al. 1994): long-memory regime estimate, more robust
  than rescaled-range on short, fat-tailed samples.
- Hill tail exponent with a metaprobability haircut (Taleb 2012): the measured
  tail is an upper bound on how thin the true tail is.
- Student-t expected shortfall scaled from mean absolute deviation (Taleb 2020).
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray
from scipy import special, stats

GAUSS_MAD_TO_SIGMA = math.sqrt(math.pi / 2)


def mad(x: NDArray[np.float64]) -> float:
    return float(np.mean(np.abs(x - np.median(x)))) if len(x) else 0.0


def robust_vol(log_returns: NDArray[np.float64]) -> float:
    """Gaussian-consistent volatility estimated from MAD (no squaring of outliers)."""
    return mad(log_returns) * GAUSS_MAD_TO_SIGMA


def trend_score(log_prices: NDArray[np.float64], horizons: list[int]) -> float:
    """Average clipped momentum z-score across horizons, in [-1, 1]."""
    lr = np.diff(log_prices[-(max(horizons) + 1):])
    if len(lr) < max(horizons):
        return 0.0
    vol = robust_vol(lr[-252:])
    if vol <= 0:
        return 0.0
    zs = []
    for h in horizons:
        z = (log_prices[-1] - log_prices[-1 - h]) / (vol * math.sqrt(h))
        zs.append(float(np.clip(z, -2.0, 2.0)) / 2.0)
    return float(np.mean(zs))


def dfa_hurst(returns: NDArray[np.float64], min_scale: int = 8, n_scales: int = 8) -> float:
    """Detrended fluctuation analysis (order 1). ~0.5 = no memory, >0.5 persistent."""
    x = np.asarray(returns, dtype=np.float64)
    n = len(x)
    if n < 4 * min_scale * 2:
        return 0.5
    profile = np.cumsum(x - x.mean())
    scales = np.unique(np.logspace(np.log10(min_scale), np.log10(n // 4), n_scales).astype(int))
    fluct = []
    for s in scales:
        m = n // s
        segs = profile[: m * s].reshape(m, s)
        t = np.arange(s, dtype=np.float64)
        t_c = t - t.mean()
        slope = (segs - segs.mean(axis=1, keepdims=True)) @ t_c / (t_c @ t_c)
        fit = segs.mean(axis=1, keepdims=True) + slope[:, None] * t_c[None, :]
        fluct.append(math.sqrt(float(np.mean((segs - fit) ** 2))))
    fluct_arr = np.array(fluct)
    ok = fluct_arr > 0
    if ok.sum() < 3:
        return 0.5
    return float(np.polyfit(np.log(scales[ok]), np.log(fluct_arr[ok]), 1)[0])


def hill_tail_exponent(returns: NDArray[np.float64], tail_fraction: float = 0.05) -> float:
    a = np.sort(np.abs(returns[np.isfinite(returns)]))[::-1]
    a = a[a > 0]
    k = max(10, int(len(a) * tail_fraction))
    if len(a) <= k + 1:
        return 3.0
    return float(1.0 / np.mean(np.log(a[:k] / a[k])))


def effective_tail_exponent(returns: NDArray[np.float64], floor: float, discount: float) -> float:
    """Metaprobability-corrected exponent: assume the tail is fatter than it looks."""
    return max(floor, hill_tail_exponent(returns) * discount)


def student_t_es(returns: NDArray[np.float64], nu: float, alpha: float = 0.01) -> float:
    """Expected shortfall (positive loss) of a Student-t whose scale is matched to the sample MAD."""
    nu = max(nu, 1.5)
    abs_moment = 2 * math.sqrt(nu) * math.exp(special.gammaln((nu + 1) / 2) - special.gammaln(nu / 2)) / (
        math.sqrt(math.pi) * (nu - 1)
    )
    scale = mad(returns) / abs_moment
    q = stats.t.ppf(alpha, nu)
    es_std = -(stats.t.pdf(q, nu) / alpha) * (nu + q * q) / (nu - 1)
    return float(-(np.median(returns) + scale * es_std))


def historical_es(returns: NDArray[np.float64], alpha: float = 0.01) -> float:
    if len(returns) == 0:
        return 0.0
    cutoff = np.quantile(returns, alpha)
    tail = returns[returns <= cutoff]
    return float(-tail.mean()) if len(tail) else float(-cutoff)


def tail_es(returns: NDArray[np.float64], nu: float, alpha: float = 0.01) -> float:
    """Conservative ES: the worse of the empirical and the fat-tailed model estimate."""
    return max(historical_es(returns, alpha), student_t_es(returns, nu, alpha))
