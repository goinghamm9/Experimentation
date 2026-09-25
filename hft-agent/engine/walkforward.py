"""Walk-forward validation: choose parameters on the past, trade the next year blind.

Every parameter combination is backtested once over the full period (signals only
ever see past data). For each test year the combination with the best time-average
log growth over the previous `train_years` is selected, and only its test-year
returns are kept. The stitched out-of-sample record is what we report.
"""

from __future__ import annotations

import itertools
import json
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from .backtest import BacktestRun, run_backtest
from .config import STATE_DIR, EngineConfig, StrategyParams
from .data import MarketData, safe_asset_returns
from .gauge import attribute
from .metrics import convexity_report, drawdown_series, summarize


def param_combos(cfg: EngineConfig) -> list[StrategyParams]:
    grid = cfg.param_grid
    keys = list(grid)
    base = cfg.params.model_dump()
    return [StrategyParams(**{**base, **dict(zip(keys, vals))}) for vals in itertools.product(*grid.values())]


def _run(args: tuple) -> BacktestRun:
    md, cfg, params, capital = args
    return run_backtest(md, cfg, params, capital=capital)


def walk_forward(
    md: MarketData,
    cfg: EngineConfig,
    train_years: int = 3,
    capital: float = 100_000.0,
    progress=None,
    workers: int | None = None,
) -> dict:
    combos = param_combos(cfg)
    workers = workers or min(len(combos), os.cpu_count() or 1)
    runs: list[BacktestRun] = []
    jobs = [(md, cfg, p, capital) for p in combos]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for i, run in enumerate(ex.map(_run, jobs)):
                runs.append(run)
                if progress:
                    progress(i + 1, len(combos))
    else:
        for i, job in enumerate(jobs):
            runs.append(_run(job))
            if progress:
                progress(i + 1, len(combos))

    rets = pd.DataFrame({i: r.returns for i, r in enumerate(runs)})
    years = sorted(set(rets.index.year))
    test_years = [y for y in years[train_years:] if (rets.index.year == y).sum() > 20]
    if not test_years:
        raise ValueError(f"Need more than {train_years} years of post-warm-up data for walk-forward")

    folds, oos_parts, chosen_rows = [], [], []
    for y in test_years:
        train = rets[(rets.index.year >= y - train_years) & (rets.index.year < y)]
        score = np.log1p(train).mean() * 252
        best = int(score.idxmax())
        test = rets.loc[rets.index.year == y, best]
        oos_parts.append(test)
        folds.append({
            "test_year": y,
            "chosen": _params_label(combos[best]),
            "train_log_growth": float(score[best]),
            "test_log_growth": float(np.log1p(test).mean() * 252),
        })
        chosen_rows.append((y, best))

    oos = pd.concat(oos_parts)
    safe_col = runs[0].columns.index("SAFE")
    exposure = pd.concat([
        pd.Series(1 - runs[b].weights[runs[b].dates[1:].year == y, safe_col], index=runs[b].dates[1:][runs[b].dates[1:].year == y])
        for y, b in chosen_rows
    ])
    benches = _benchmarks(md, cfg, oos.index, combos, chosen_rows, exposure)

    run_rows_w, run_rows_r, trades, costs = [], [], [], 0.0
    for y, best in chosen_rows:
        run = runs[best]
        mask = run.dates[1:].year == y
        run_rows_w.append(run.weights[mask])
        run_rows_r.append(run.period_returns[mask])
        trades += [o for o in run.orders if o["date"][:4] == str(y)]
        costs += float(run.costs[1:][mask].sum())
    gauge = attribute(np.vstack(run_rows_w), np.vstack(run_rows_r))

    safe_r = safe_asset_returns(md, [cfg.safe_asset, *cfg.safe_asset_fallbacks], cfg.costs.cash_rate_annual)
    gauge_tbill = attribute(
        np.vstack(run_rows_w),
        _to_numeraire(np.vstack(run_rows_r), safe_r.reindex(oos.index).fillna(0).to_numpy()),
    )

    latest_score = rets[rets.index.year >= years[-1] - train_years + 1]
    live_best = int((np.log1p(latest_score).mean() * 252).idxmax())
    live_params = combos[live_best]
    last_run = runs[live_best]

    equity = (1 + oos).cumprod() * capital
    bench_eq = {k: (1 + v).cumprod() * capital for k, v in benches.items()}
    market = benches.get("Benchmark buy & hold", benches["Equal-weight universe"])
    trips = [t for (y, b) in chosen_rows for t in runs[b].round_trips if t.exit_date[:4] == str(y)]

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": md.source,
        "period": [str(oos.index[0].date()), str(oos.index[-1].date())],
        "n_param_sets_tried": len(combos),
        "train_years": train_years,
        "folds": folds,
        "metrics": {"Strategy (out-of-sample)": summarize(oos), **{k: summarize(v) for k, v in benches.items()}},
        "convexity": convexity_report(oos, market),
        "bootstrap": {
            k: _bootstrap_prob_better(oos, v) for k, v in benches.items()
        },
        "gauge": {
            "usd": gauge.totals(),
            "tbill_numeraire": gauge_tbill.totals(),
            "cumulative": {
                "dates": [d.date().isoformat() for d in oos.index],
                "exposure": np.cumsum(gauge.exposure).round(6).tolist(),
                "timing": np.cumsum(gauge.timing).round(6).tolist(),
                "convexity": np.cumsum(gauge.convexity).round(6).tolist(),
            },
        },
        "costs_paid": costs,
        "round_trips": {
            "count": len(trips),
            "win_rate": float(np.mean([t.pnl > 0 for t in trips])) if trips else None,
            "avg_return": float(np.mean([t.ret for t in trips])) if trips else None,
        },
        "equity": {
            "dates": [d.date().isoformat() for d in equity.index],
            "Strategy (out-of-sample)": equity.round(2).tolist(),
            **{k: v.reindex(equity.index).ffill().round(2).tolist() for k, v in bench_eq.items()},
        },
        "drawdown": drawdown_series(equity).round(5).tolist(),
        "daily_returns": oos.round(6).tolist(),
        "trades": trades[-300:],
        "live_params": live_params.model_dump(),
        "latest_target": _target_json(last_run),
        "hedge_note": runs[0].hedge_note,
        "warnings": _warnings(md, cfg, len(combos), test_years) + _edge_warnings(cfg, combos, chosen_rows),
    }
    result = clean_json(result)
    _save_model(live_params, result)
    return result


def clean_json(obj):
    """Replace NaN/inf with None and numpy scalars with Python types so browsers can parse it."""
    if isinstance(obj, dict):
        return {str(k): clean_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean_json(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return f if np.isfinite(f) else None
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def _params_label(p: StrategyParams) -> str:
    return f"budget {p.risky_budget:.0%}, horizons {p.horizons}, hurst {'on' if p.use_hurst else 'off'}"


def _to_numeraire(r: np.ndarray, num: np.ndarray) -> np.ndarray:
    return (1 + r) / (1 + num[:, None]) - 1


def _benchmarks(md: MarketData, cfg: EngineConfig, idx: pd.DatetimeIndex, combos, chosen_rows, exposure: pd.Series) -> dict[str, pd.Series]:
    safe = [cfg.safe_asset, *cfg.safe_asset_fallbacks]
    risky = [s for s in cfg.universe if s in md.close.columns and s not in safe]
    r = md.close[risky].pct_change()
    ew = r.mean(axis=1, skipna=True).reindex(idx).fillna(0)
    safe_r = safe_asset_returns(md, safe, cfg.costs.cash_rate_annual).reindex(idx).fillna(0)
    budget = pd.Series(index=idx, dtype=float)
    for y, best in chosen_rows:
        budget[idx.year == y] = combos[best].risky_budget
    avg_exp = exposure.groupby(exposure.index.year).mean()
    matched = pd.Series(idx.year.map(avg_exp).to_numpy(dtype=float), index=idx).fillna(0)
    out = {
        "Naive barbell (matched avg exposure)": matched * ew + (1 - matched) * safe_r,
        "Naive barbell (same budget, no signals)": budget * ew + (1 - budget) * safe_r,
        "Equal-weight universe": ew,
    }
    if cfg.benchmark in md.close.columns:
        out["Benchmark buy & hold"] = md.close[cfg.benchmark].pct_change().reindex(idx).fillna(0)
    return out


def _bootstrap_prob_better(a: pd.Series, b: pd.Series, n: int = 2000, block: int = 21, seed: int = 7) -> float:
    """Stationary block bootstrap of P(strategy log growth > comparison log growth)."""
    d = (np.log1p(a) - np.log1p(b.reindex(a.index).fillna(0))).to_numpy()
    rng = np.random.default_rng(seed)
    m = len(d)
    wins = 0
    for _ in range(n):
        idx = np.empty(m, dtype=int)
        i = 0
        while i < m:
            start = rng.integers(0, m)
            length = min(rng.geometric(1 / block), m - i)
            idx[i:i + length] = (start + np.arange(length)) % m
            i += length
        wins += d[idx].mean() > 0
    return wins / n


def _target_json(run: BacktestRun) -> dict | None:
    t = run.last_target
    if t is None:
        return None
    return {
        "weights": t.weights,
        "safe_weight": t.safe_weight,
        "portfolio_es99": t.portfolio_es99,
        "kelly_cap": t.kelly_cap,
        "vetoes": t.vetoes,
        "assets": [asdict(a) for a in t.assets],
    }


def _warnings(md: MarketData, cfg: EngineConfig, n_trials: int, test_years: list[int]) -> list[str]:
    w = [
        f"{n_trials} parameter sets were tried; out-of-sample results are still one historical path.",
        "Past trend-following performance does not guarantee future results.",
    ]
    safe = [cfg.safe_asset, *cfg.safe_asset_fallbacks]
    if not any(s in md.close.columns for s in safe):
        w.append(f"No T-bill ETF in the data; safe sleeve earns the configured cash rate ({cfg.costs.cash_rate_annual:.1%}).")
    if len(test_years) < 5:
        w.append(f"Only {len(test_years)} out-of-sample years; treat results as weak evidence.")
    return w


def _edge_warnings(cfg: EngineConfig, combos, chosen_rows) -> list[str]:
    out = []
    for key, values in cfg.param_grid.items():
        if len(values) < 3 or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            continue
        picked = [getattr(combos[b], key) for _, b in chosen_rows]
        edge = sum(p in (min(values), max(values)) for p in picked)
        if edge > len(picked) / 2:
            out.append(f"'{key}' was chosen at the edge of its grid in {edge}/{len(picked)} years; the grid may be too narrow.")
    return out


def _save_model(params: StrategyParams, result: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_DIR / "model.json", "w") as f:
        json.dump({"params": params.model_dump(), "chosen_at": result["generated_at"], "period": result["period"]}, f, indent=2)
    with open(STATE_DIR / "last_backtest.json", "w") as f:
        json.dump(result, f)
