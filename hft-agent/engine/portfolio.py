"""Barbell portfolio construction (Taleb): a large ultra-safe sleeve plus a capped risky sleeve.

Risky sleeve weight for asset i (N eligible assets):
    w_i = (budget / N) * strength_i * hurst_mult_i * (1/ES_i) / mean_j(1/ES_j)
where strength_i = clip(trend_i / 0.5, 0, 1). The sleeve is fully used only when every
asset trends, and each asset's size is set by its fat-tailed expected shortfall
rather than its variance.
Then three vetoes apply in order: fractional-Kelly cap on time-average growth
(Peters 2019), portfolio ES cap, and a drawdown brake. Long-only, no leverage,
matching a cash-only Robinhood agentic account.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .config import RiskLimits, StrategyParams
from .signals import dfa_hurst, effective_tail_exponent, tail_es, trend_score

FULL_POSITION_SCORE = 0.5


@dataclass
class AssetView:
    symbol: str
    trend: float
    hurst: float
    hurst_mult: float
    tail_exponent: float
    es99: float
    weight: float
    reason: str


@dataclass
class TargetPortfolio:
    weights: dict[str, float]
    safe_weight: float
    assets: list[AssetView] = field(default_factory=list)
    portfolio_es99: float = 0.0
    kelly_cap: float | None = None
    vetoes: list[str] = field(default_factory=list)

    @property
    def risky_exposure(self) -> float:
        return float(sum(self.weights.values()))


def build_target(
    symbols: list[str],
    log_prices: np.ndarray,
    params: StrategyParams,
    risk: RiskLimits,
    drawdown: float = 0.0,
) -> TargetPortfolio:
    """log_prices: array (T, N) of log prices up to and including today, NaN before listing."""
    lookback = risk.lookback_days
    need = max(lookback, max(params.horizons)) + 1
    views: list[AssetView] = []
    raw: dict[str, float] = {}
    inv_es: dict[str, float] = {}
    window_returns: dict[str, np.ndarray] = {}

    for j, sym in enumerate(symbols):
        col = log_prices[-need:, j]
        if len(col) < need or np.isnan(col).any():
            continue
        lr = np.diff(col)
        window_returns[sym] = lr[-lookback:]
        score = trend_score(col, params.horizons)
        hurst = dfa_hurst(lr[-252:]) if params.use_hurst else 0.5
        mult = float(np.clip(1 + 2 * (hurst - 0.5), 0.5, 1.25)) if params.use_hurst else 1.0
        alpha = effective_tail_exponent(lr, risk.tail_exponent_floor, risk.metaprobability_discount)
        es = tail_es(lr[-lookback:], alpha)
        inv_es[sym] = 1.0 / max(es, 1e-6)
        raw[sym] = min(max(score, 0.0) / FULL_POSITION_SCORE, 1.0) * mult
        views.append(AssetView(sym, score, hurst, mult, alpha, es, 0.0, ""))

    target = TargetPortfolio(weights={}, safe_weight=1.0, assets=views)
    if not views:
        target.vetoes.append("not enough price history for any asset")
        return target

    mean_inv_es = sum(inv_es.values()) / len(inv_es)
    per_asset = params.risky_budget / len(raw)
    weights = {s: per_asset * raw[s] * inv_es[s] / mean_inv_es for s in raw}
    weights = {s: min(w, risk.max_weight_per_asset) for s, w in weights.items() if w > 1e-4}

    exposure = sum(weights.values())
    if exposure > 0:
        hist = np.column_stack([window_returns[s] for s in weights])
        w_vec = np.array(list(weights.values()))
        sleeve = (np.expm1(hist) @ (w_vec / exposure))

        fracs = np.linspace(0.0, 3.0, 301)
        growth = [np.mean(np.log1p(np.clip(f * sleeve, -0.99, None))) for f in fracs]
        kelly_full = float(fracs[int(np.argmax(growth))])
        cap = params.kelly_fraction * kelly_full
        target.kelly_cap = cap
        if exposure > cap:
            scale = cap / exposure if exposure > 0 else 0.0
            weights = {s: w * scale for s, w in weights.items()}
            target.vetoes.append(
                f"Kelly: {params.kelly_fraction:.2f}x Kelly allows {cap:.1%} risky exposure, cut from {exposure:.1%}"
            )

        w_vec = np.array([weights[s] for s in weights])
        port_hist = np.expm1(hist) @ w_vec
        port_alpha = effective_tail_exponent(port_hist, risk.tail_exponent_floor, risk.metaprobability_discount)
        port_es = tail_es(port_hist, port_alpha)
        if port_es > risk.max_cvar_99_daily and port_es > 0:
            scale = risk.max_cvar_99_daily / port_es
            weights = {s: w * scale for s, w in weights.items()}
            target.vetoes.append(
                f"Tail risk: portfolio ES99 {port_es:.2%}/day exceeds {risk.max_cvar_99_daily:.2%}, scaled by {scale:.2f}"
            )
            port_es = risk.max_cvar_99_daily
        target.portfolio_es99 = float(port_es)

    if drawdown > risk.max_drawdown_brake:
        weights = {s: w * 0.5 for s, w in weights.items()}
        target.vetoes.append(f"Drawdown brake: down {drawdown:.1%} from peak, risky sleeve halved")

    weights = {s: w for s, w in weights.items() if w > 1e-4}
    for v in views:
        v.weight = weights.get(v.symbol, 0.0)
        v.reason = _explain(v, params)
    target.weights = weights
    target.safe_weight = 1.0 - sum(weights.values())
    return target


def _explain(v: AssetView, params: StrategyParams) -> str:
    if v.trend <= 0:
        return f"No position: trend score {v.trend:+.2f} is not positive (long-only)."
    parts = [f"Trend score {v.trend:+.2f} across {len(params.horizons)} horizons"]
    if params.use_hurst:
        parts.append(f"DFA Hurst {v.hurst:.2f} -> size x{v.hurst_mult:.2f}")
    parts.append(f"tail exponent {v.tail_exponent:.2f}, 1-day ES99 {v.es99:.2%} sets risk size")
    return "; ".join(parts) + f". Weight {v.weight:.2%}."
