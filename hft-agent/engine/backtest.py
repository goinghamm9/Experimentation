"""Daily backtest of the barbell engine.

Rules that keep it honest:
- Decisions use data up to the close of day t; orders fill at the close of day t+1.
- Long-only, no margin, fractional shares (matches a Robinhood agentic account).
- Costs: half-spread plus square-root market impact on dollar volume.
- Trade statistics come from FIFO lots (real round trips), not from bar returns.
- The optional put hedge is priced with Black-Scholes at a marked-up implied vol.
  It is a model, not historical option prices.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from .config import EngineConfig, StrategyParams
from .data import MarketData, safe_asset_returns
from .portfolio import TargetPortfolio, build_target
from .signals import robust_vol


@dataclass
class Lot:
    shares: float
    price: float
    date: pd.Timestamp


@dataclass
class RoundTrip:
    symbol: str
    entry_date: str
    exit_date: str
    shares: float
    entry_price: float
    exit_price: float
    pnl: float
    ret: float


@dataclass
class BacktestRun:
    dates: pd.DatetimeIndex
    equity: np.ndarray
    columns: list[str]
    weights: np.ndarray            # (T, K) start-of-period value shares, incl. safe (and hedge)
    period_returns: np.ndarray     # (T, K) simple returns of each column over the period
    costs: np.ndarray              # dollars paid per day
    turnover: np.ndarray           # traded dollars / equity per day
    orders: list[dict] = field(default_factory=list)
    round_trips: list[RoundTrip] = field(default_factory=list)
    last_target: TargetPortfolio | None = None
    hedge_note: str = ""

    @property
    def returns(self) -> pd.Series:
        eq = pd.Series(self.equity, index=self.dates)
        return eq.pct_change().dropna()


def _bs_put(s: float, k: float, t: float, vol: float) -> float:
    if t <= 0 or vol <= 0:
        return max(k - s, 0.0)
    d1 = (math.log(s / k) + 0.5 * vol * vol * t) / (vol * math.sqrt(t))
    d2 = d1 - vol * math.sqrt(t)
    return float(k * stats.norm.cdf(-d2) - s * stats.norm.cdf(-d1))


def run_backtest(
    md: MarketData,
    cfg: EngineConfig,
    params: StrategyParams | None = None,
    start: str | None = None,
    capital: float = 100_000.0,
) -> BacktestRun:
    params = params or cfg.params
    safe_candidates = [cfg.safe_asset, *cfg.safe_asset_fallbacks]
    symbols = [s for s in cfg.universe if s in md.close.columns and s not in safe_candidates]
    if not symbols:
        raise ValueError("None of the universe symbols are in the price data")

    close = md.close[symbols].ffill()
    dates = close.index
    logp = np.log(close.to_numpy(dtype=np.float64))
    px = np.nan_to_num(close.to_numpy(dtype=np.float64))
    safe_r = safe_asset_returns(md, safe_candidates, cfg.costs.cash_rate_annual).reindex(dates).fillna(0.0).to_numpy()
    if md.volume is not None and not md.volume.empty:
        vol_df = md.volume.reindex(index=dates, columns=symbols)
        adv = (vol_df * close).rolling(20, min_periods=5).mean().to_numpy(dtype=np.float64)
    else:
        adv = np.full_like(px, np.nan)

    need = max(cfg.risk.lookback_days, max(params.horizons)) + 1
    first_ok = next((t for t in range(len(dates)) if np.isfinite(logp[max(0, t - need + 1):t + 1]).all(axis=0).any() and t >= need - 1), None)
    if first_ok is None:
        raise ValueError(f"Need at least {need} days of history for one asset")
    t0 = first_ok
    if start:
        t0 = max(t0, int(np.searchsorted(dates, pd.Timestamp(start))))

    hedge = cfg.hedge
    hedge_idx = None
    hedge_note = ""
    if hedge.enabled:
        if hedge.underlying in md.close.columns:
            hedge_px = md.close[hedge.underlying].reindex(dates).ffill().to_numpy(dtype=np.float64)
            hedge_idx = True
            hedge_note = "Put hedge is model-priced (Black-Scholes, marked-up vol); real fills will differ."
        else:
            hedge_note = f"Hedge disabled: {hedge.underlying} not in price data."

    n = len(symbols)
    shares = np.zeros(n)
    lots: list[deque[Lot]] = [deque() for _ in range(n)]
    safe_val = capital
    put: dict | None = None
    peak = capital
    pending: TargetPortfolio | None = None
    last_target: TargetPortfolio | None = None

    out_dates, out_eq, out_w, out_r, out_cost, out_turn = [], [], [], [], [], []
    orders: list[dict] = []
    trips: list[RoundTrip] = []
    cols = symbols + ["SAFE"] + (["HEDGE"] if hedge_idx else [])

    prev_vals: np.ndarray | None = None
    for t in range(t0, len(dates)):
        day_safe = safe_r[t] if t > t0 else 0.0

        risky_vals_before = shares * px[t]
        safe_val *= 1 + day_safe
        hedge_val = 0.0
        if put is not None:
            put["days_left"] -= 1
            s = hedge_px[t]
            if put["days_left"] <= 0:
                safe_val += put["units"] * max(put["strike"] - s, 0.0)
                put = None
            else:
                rv = robust_vol(np.diff(np.log(hedge_px[max(0, t - 21):t + 1]))) * math.sqrt(252)
                iv = max(rv, 0.10) * hedge.vol_markup * (1 + 2 * (1 - hedge.moneyness))
                hedge_val = put["units"] * _bs_put(s, put["strike"], put["days_left"] / 252, iv)

        vals_now = np.concatenate([risky_vals_before, [safe_val], [hedge_val] if hedge_idx else []])
        if prev_vals is not None:
            with np.errstate(divide="ignore", invalid="ignore"):
                period_r = np.where(prev_vals > 0, vals_now / prev_vals - 1, 0.0)
            prev_w = prev_vals / prev_vals.sum()
            out_w.append(prev_w)
            out_r.append(period_r)

        equity = float(vals_now.sum())
        peak = max(peak, equity)
        drawdown = 1 - equity / peak if peak > 0 else 0.0

        cost_today = 0.0
        traded = 0.0
        if pending is not None:
            desired = np.array([pending.weights.get(s, 0.0) for s in symbols]) * equity
            current = shares * px[t]
            delta = desired - current
            for j in np.argsort(delta):
                d = delta[j]
                exiting = desired[j] == 0 and current[j] > 0
                if abs(d) < trade_threshold(cfg, desired[j], current[j], equity) and not exiting:
                    continue
                if d > 0:
                    d = min(d, safe_val * 0.995)
                    if d <= cfg.min_order_usd:
                        continue
                sigma = robust_vol(np.diff(logp[max(0, t - 63):t + 1, j]))
                part = abs(d) / adv[t, j] if np.isfinite(adv[t, j]) and adv[t, j] > 0 else 0.0
                c = abs(d) * (cfg.costs.half_spread_bps / 1e4 + cfg.costs.impact_coef * sigma * math.sqrt(part))
                q = d / px[t, j]
                if q > 0:
                    lots[j].append(Lot(q, px[t, j], dates[t]))
                    safe_val -= d + c
                else:
                    trips += _close_lots(lots[j], -q, px[t, j], dates[t], symbols[j])
                    safe_val += -d - c
                shares[j] += q
                cost_today += c
                traded += abs(d)
                orders.append({
                    "date": dates[t].date().isoformat(), "symbol": symbols[j],
                    "side": "buy" if q > 0 else "sell", "shares": round(abs(q), 6),
                    "price": round(px[t, j], 4), "notional": round(abs(d), 2), "cost": round(c, 2),
                })
            pending = None

        if hedge_idx and put is None and (t - t0) % hedge.tenor_days == 0:
            budget = hedge.annual_budget * hedge.tenor_days / 252 * equity
            s = hedge_px[t]
            rv = robust_vol(np.diff(np.log(hedge_px[max(0, t - 21):t + 1]))) * math.sqrt(252)
            iv = max(rv, 0.10) * hedge.vol_markup * (1 + 2 * (1 - hedge.moneyness))
            strike = hedge.moneyness * s
            prem = _bs_put(s, strike, hedge.tenor_days / 252, iv)
            if prem > 0 and budget < safe_val:
                put = {"units": budget / prem, "strike": strike, "days_left": hedge.tenor_days}
                safe_val -= budget
                hedge_val = budget

        if (t - t0) % cfg.rebalance_every_days == 0 and t < len(dates) - 1:
            pending = build_target(symbols, logp[: t + 1], params, cfg.risk, drawdown)
            last_target = pending

        post_vals = np.concatenate([shares * px[t], [safe_val], [hedge_val] if hedge_idx else []])
        prev_vals = post_vals
        out_dates.append(dates[t])
        out_eq.append(float(post_vals.sum()))
        out_cost.append(cost_today)
        out_turn.append(traded / equity if equity > 0 else 0.0)

    k = len(cols)
    w_arr = np.array(out_w) if out_w else np.zeros((0, k))
    r_arr = np.array(out_r) if out_r else np.zeros((0, k))
    return BacktestRun(
        dates=pd.DatetimeIndex(out_dates),
        equity=np.array(out_eq),
        columns=cols,
        weights=w_arr,
        period_returns=r_arr,
        costs=np.array(out_cost),
        turnover=np.array(out_turn),
        orders=orders,
        round_trips=trips,
        last_target=last_target,
        hedge_note=hedge_note,
    )


def trade_threshold(cfg: EngineConfig, desired: float, current: float, equity: float) -> float:
    """Skip small rebalances: a position must drift no_trade_band (relative) from target."""
    return max(cfg.no_trade_band * max(desired, current), 0.0025 * equity, cfg.min_order_usd)


def _close_lots(lots: deque[Lot], qty: float, price: float, date: pd.Timestamp, symbol: str) -> list[RoundTrip]:
    out = []
    while qty > 1e-12 and lots:
        lot = lots[0]
        take = min(lot.shares, qty)
        pnl = take * (price - lot.price)
        out.append(RoundTrip(
            symbol, lot.date.date().isoformat(), date.date().isoformat(), take,
            lot.price, price, pnl, price / lot.price - 1,
        ))
        lot.shares -= take
        qty -= take
        if lot.shares <= 1e-12:
            lots.popleft()
    return out
