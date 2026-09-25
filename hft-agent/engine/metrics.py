"""Performance metrics that stay meaningful under fat tails."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .signals import GAUSS_MAD_TO_SIGMA, hill_tail_exponent, historical_es, mad

TRADING_DAYS = 252


def summarize(returns: pd.Series) -> dict[str, float]:
    r = returns.dropna().to_numpy(dtype=np.float64)
    if len(r) < 2:
        return {}
    years = len(r) / TRADING_DAYS
    wealth = np.cumprod(1 + r)
    peaks = np.maximum.accumulate(np.concatenate([[1.0], wealth]))[1:]
    dd = 1 - wealth / peaks
    log_growth = float(np.mean(np.log1p(r)) * TRADING_DAYS)
    cagr = float(wealth[-1] ** (1 / years) - 1) if years > 0 else 0.0
    ann_mad = mad(r) * math.sqrt(TRADING_DAYS)
    ann_std = float(np.std(r, ddof=1) * math.sqrt(TRADING_DAYS))
    max_dd = float(dd.max())
    return {
        "cagr": cagr,
        "log_growth": log_growth,
        "total_return": float(wealth[-1] - 1),
        "robust_vol": ann_mad * GAUSS_MAD_TO_SIGMA,
        "std_vol": ann_std,
        "mad_ratio": float(np.mean(r) * TRADING_DAYS / ann_mad) if ann_mad > 0 else 0.0,
        "sharpe_for_reference": float(np.mean(r) * TRADING_DAYS / ann_std) if ann_std > 0 else 0.0,
        "es99_daily": historical_es(r, 0.01),
        "worst_day": float(r.min()),
        "best_day": float(r.max()),
        "max_drawdown": max_dd,
        "calmar": cagr / max_dd if max_dd > 0 else 0.0,
        "tail_exponent": hill_tail_exponent(r) if len(r) > 200 else float("nan"),
        "years": years,
    }


def convexity_report(strategy: pd.Series, market: pd.Series) -> dict[str, float | str]:
    """Taleb-Douady style fragility test on monthly returns.

    Fits r_s = a + b r_m + g r_m^2 (Treynor-Mazuy). g > 0 means the strategy gains
    convexly from large market moves in either direction (antifragile); g < 0 means it
    is short volatility (fragile). Also reports the strategy's average month when the
    market had its worst decile of months.
    """
    df = pd.concat([strategy, market], axis=1, join="inner").dropna()
    if len(df) < 60:
        return {"state": "insufficient data"}
    m = (1 + df).resample("ME").prod() - 1
    rs, rm = m.iloc[:, 0].to_numpy(), m.iloc[:, 1].to_numpy()
    if len(rs) < 12:
        return {"state": "insufficient data"}
    x = np.column_stack([np.ones_like(rm), rm, rm ** 2])
    coef, *_ = np.linalg.lstsq(x, rs, rcond=None)
    resid = rs - x @ coef
    dof = max(len(rs) - 3, 1)
    cov = np.linalg.pinv(x.T @ x) * (resid @ resid / dof)
    g, g_se = float(coef[2]), float(math.sqrt(max(cov[2, 2], 0.0)))
    worst = rm <= np.quantile(rm, 0.1)
    crisis = float(rs[worst].mean())
    t = g / g_se if g_se > 0 else 0.0
    state = "antifragile" if t > 2 else "fragile" if t < -2 else "robust (no significant convexity)"
    return {
        "state": state,
        "beta": float(coef[1]),
        "convexity_gamma": g,
        "convexity_t": t,
        "strategy_in_worst_market_months": crisis,
        "market_worst_decile_avg": float(rm[worst].mean()),
    }


def drawdown_series(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1
