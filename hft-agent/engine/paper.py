"""Paper account: runs the live plan against a simulated ledger with the backtest's cost model."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone

from .config import STATE_DIR, EngineConfig
from .data import MarketData
from .plan import make_plan, recent_data

LEDGER = STATE_DIR / "paper.json"


def load() -> dict | None:
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else None


def save(ledger: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(ledger, indent=2))


def init(capital: float) -> dict:
    ledger = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "starting_capital": capital,
        "cash": capital,
        "holdings": {},
        "peak_equity": capital,
        "history": [],
        "fills": [],
        "last_trade_date": None,
    }
    save(ledger)
    return ledger


def step(cfg: EngineConfig, md: MarketData | None = None) -> dict:
    ledger = load()
    if ledger is None:
        raise RuntimeError("No paper account. Run: python -m engine paper init --capital 10000")
    md = md or recent_data(cfg)
    last = md.close.ffill().iloc[-1]
    data_date = str(md.close.index[-1].date())

    plan = make_plan(cfg, ledger["holdings"], ledger["cash"], md=md, peak_equity=ledger["peak_equity"])
    traded = False
    if ledger["last_trade_date"] != data_date and not plan["blocked"]:
        for o in plan["orders"]:
            sym = o["symbol"]
            price = float(last[sym])
            cost = o["notional_usd"] * cfg.costs.half_spread_bps / 1e4
            qty = o["notional_usd"] / price
            if o["side"] == "sell":
                qty = min(qty, ledger["holdings"].get(sym, 0.0))
                if o["sell_all"]:
                    qty = ledger["holdings"].get(sym, 0.0)
                ledger["holdings"][sym] = ledger["holdings"].get(sym, 0.0) - qty
                ledger["cash"] += qty * price - cost
            else:
                spend = min(o["notional_usd"], ledger["cash"] - cost)
                if spend <= 0:
                    continue
                qty = spend / price
                ledger["holdings"][sym] = ledger["holdings"].get(sym, 0.0) + qty
                ledger["cash"] -= spend + cost
            ledger["fills"].append({
                "date": data_date, "symbol": sym, "side": o["side"], "shares": round(qty, 6),
                "price": round(price, 4), "cost": round(cost, 4), "reason": o["reason"],
            })
            traded = True
        ledger["holdings"] = {s: q for s, q in ledger["holdings"].items() if q > 1e-9}
        ledger["last_trade_date"] = data_date

    equity = ledger["cash"] + sum(q * float(last[s]) for s, q in ledger["holdings"].items() if s in last.index and math.isfinite(last[s]))
    ledger["peak_equity"] = max(ledger["peak_equity"], equity)
    hist = [h for h in ledger["history"] if h["date"] != data_date]
    hist.append({"date": data_date, "equity": round(equity, 2)})
    ledger["history"] = hist
    save(ledger)
    return {"ledger": ledger, "plan": plan, "traded": traded, "equity": equity}
