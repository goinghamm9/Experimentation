"""Today's order plan: current holdings in, explained orders out. Never places orders itself."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

from .backtest import trade_threshold
from .config import STATE_DIR, EngineConfig, StrategyParams
from .data import MarketData, load_prices
from .portfolio import build_target

CASH_BUFFER = 0.005
MAX_STALENESS_DAYS = 5


def live_params(cfg: EngineConfig) -> tuple[StrategyParams, str]:
    path = STATE_DIR / "model.json"
    if path.exists():
        data = json.loads(path.read_text())
        return StrategyParams(**data["params"]), f"walk-forward selection from {data['chosen_at'][:10]}"
    return cfg.params, "config defaults (run a backtest to select parameters)"


def recent_data(cfg: EngineConfig) -> MarketData:
    days = int((cfg.risk.lookback_days + max(cfg.params.horizons) + 60) * 1.5)
    start = (date.today() - timedelta(days=days)).isoformat()
    symbols = [*cfg.universe, cfg.safe_asset, *cfg.safe_asset_fallbacks]
    return load_prices(symbols, start, source=cfg.data_source, csv_path=cfg.csv_path, use_cache=False)


def make_plan(
    cfg: EngineConfig,
    holdings: dict[str, float],
    cash: float,
    md: MarketData | None = None,
    peak_equity: float | None = None,
) -> dict:
    md = md or recent_data(cfg)
    params, params_source = live_params(cfg)
    safe = next((s for s in [cfg.safe_asset, *cfg.safe_asset_fallbacks] if s in md.close.columns), None)
    risky = [s for s in cfg.universe if s in md.close.columns and s != safe]
    last = md.close.ffill().iloc[-1]
    last_date = md.close.index[-1]
    holdings = {k.upper(): float(v) for k, v in holdings.items() if float(v) != 0}

    checks: list[dict] = []
    unknown = [s for s in holdings if s not in last.index or not np.isfinite(last[s])]
    if unknown:
        checks.append(_check(False, f"No price for held symbols {unknown}; they are left untouched and excluded from equity."))
    held_value = sum(q * float(last[s]) for s, q in holdings.items() if s not in unknown)
    equity = cash + held_value
    peak = max(peak_equity or equity, equity)
    drawdown = 1 - equity / peak if peak > 0 else 0.0

    stale = (pd.Timestamp(date.today()) - last_date).days
    checks.append(_check(stale <= MAX_STALENESS_DAYS, f"Latest price data is from {last_date.date()} ({stale} days old)."))
    checks.append(_check(equity > 0, f"Account equity ${equity:,.2f}."))
    short = [s for s, q in holdings.items() if q < 0]
    checks.append(_check(not short, "No short positions (cash account)." if not short else f"Short positions found: {short}"))

    target = build_target(risky, np.log(md.close[risky].ffill().to_numpy(dtype=np.float64)), params, cfg.risk, drawdown)

    desired = {s: w * equity for s, w in target.weights.items()}
    if safe:
        desired[safe] = max(target.safe_weight - CASH_BUFFER, 0.0) * equity

    orders = []
    for sym in sorted(set(desired) | {s for s in holdings if s not in unknown}):
        if sym not in last.index:
            continue
        price = float(last[sym])
        cur = holdings.get(sym, 0.0) * price
        want = desired.get(sym, 0.0)
        d = want - cur
        exiting = want == 0 and cur > 0
        managed = sym in risky or sym == safe
        if not managed:
            continue
        if abs(d) < trade_threshold(cfg, want, cur, equity) and not exiting:
            continue
        view = next((a for a in target.assets if a.symbol == sym), None)
        reason = view.reason if view else (
            f"Safe sleeve: T-bill ETF holds {target.safe_weight:.1%} of equity." if sym == safe else "Not in the model universe."
        )
        orders.append({
            "symbol": sym,
            "side": "buy" if d > 0 else "sell",
            "notional_usd": round(abs(d), 2),
            "est_shares": round(abs(d) / price, 6),
            "ref_price": round(price, 4),
            "sell_all": bool(exiting),
            "reason": reason,
        })
    orders.sort(key=lambda o: (o["side"] != "sell", -o["notional_usd"]))

    buys = sum(o["notional_usd"] for o in orders if o["side"] == "buy")
    sells = sum(o["notional_usd"] for o in orders if o["side"] == "sell")
    checks.append(_check(buys <= cash + sells + 1e-6, f"Buys ${buys:,.2f} funded by cash ${cash:,.2f} + sells ${sells:,.2f} (no margin)."))
    risky_after = sum(target.weights.values())
    checks.append(_check(risky_after <= params.risky_budget + 1e-9, f"Risky sleeve {risky_after:.1%} within budget {params.risky_budget:.0%}."))

    plan = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "data_last_date": str(last_date.date()),
        "data_source": md.source,
        "equity": round(equity, 2),
        "cash": round(cash, 2),
        "drawdown": drawdown,
        "params": params.model_dump(),
        "params_source": params_source,
        "safe_asset": safe,
        "target": {
            "weights": target.weights,
            "safe_weight": target.safe_weight,
            "portfolio_es99": target.portfolio_es99,
            "kelly_cap": target.kelly_cap,
            "vetoes": target.vetoes,
            "assets": [asdict(a) for a in target.assets],
        },
        "orders": orders,
        "checks": checks,
        "blocked": not all(c["ok"] for c in checks),
        "summary": _summary(target, orders, safe),
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "plan.json").write_text(json.dumps(plan, indent=2, default=float))
    return plan


def _check(ok: bool, message: str) -> dict:
    return {"ok": bool(ok), "message": message}


def _summary(target, orders: list[dict], safe: str | None) -> str:
    held = ", ".join(f"{s} {w:.1%}" for s, w in sorted(target.weights.items(), key=lambda kv: -kv[1])) or "nothing"
    text = (
        f"Barbell target: {target.safe_weight:.1%} in the safe sleeve ({safe or 'cash'}), "
        f"{sum(target.weights.values()):.1%} risky ({held}). "
    )
    if target.vetoes:
        text += "Risk limits applied: " + "; ".join(target.vetoes) + ". "
    text += f"{len(orders)} order(s) needed." if orders else "No trades needed; positions are within their bands."
    return text
