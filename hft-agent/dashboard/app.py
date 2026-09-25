"""Dashboard backend. Serves real engine output only: backtests, today's plan, paper account.

Bind to localhost (the default). There is no login, so do not expose it to the internet.
"""

from __future__ import annotations

import asyncio
import json
import threading
import traceback
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from engine import paper
from engine.config import STATE_DIR, load_config
from engine.explain import CONCEPTS

TEMPLATE = Path(__file__).resolve().parent / "templates" / "index.html"

app = FastAPI(title="Barbell Engine Dashboard")

_job: dict[str, Any] = {"state": "idle", "id": None, "done": 0, "total": 0, "message": "", "error": None}
_lock = threading.Lock()


class BacktestRequest(BaseModel):
    start: str = "2007-06-01"
    end: str | None = None
    capital: float = 100_000
    train_years: int = 3
    symbols: list[str] | None = None
    hedge: bool = False
    csv_path: str | None = None


class PlanRequest(BaseModel):
    cash: float = 0.0
    positions: dict[str, float] = {}
    use_paper: bool = False


class PaperInit(BaseModel):
    capital: float = 10_000


def _read_state(name: str) -> dict | list | None:
    p = STATE_DIR / name
    return json.loads(p.read_text()) if p.exists() else None


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(TEMPLATE.read_text())


@app.get("/api/config")
async def get_config() -> dict:
    return load_config().model_dump()


@app.get("/api/concepts")
async def concepts() -> dict:
    return CONCEPTS


@app.post("/api/backtest")
async def start_backtest(req: BacktestRequest) -> dict:
    with _lock:
        if _job["state"] == "running":
            raise HTTPException(409, "A backtest is already running")
        _job.update(state="running", id=uuid.uuid4().hex[:8], done=0, total=0, message="Loading prices", error=None)
    threading.Thread(target=_run_backtest, args=(req,), daemon=True).start()
    return {"job_id": _job["id"]}


def _run_backtest(req: BacktestRequest) -> None:
    from engine.data import load_prices
    from engine.walkforward import walk_forward

    try:
        cfg = load_config()
        if req.symbols:
            cfg.universe = [s.strip().upper() for s in req.symbols if s.strip()]
        cfg.hedge.enabled = req.hedge
        symbols = [*cfg.universe, cfg.safe_asset, *cfg.safe_asset_fallbacks, cfg.benchmark]
        source = "csv" if req.csv_path else cfg.data_source
        md = load_prices(symbols, req.start, req.end, source=source, csv_path=req.csv_path or cfg.csv_path)
        _job["message"] = f"Loaded {md.close.shape[0]} days from {md.source}; running parameter sets"

        def progress(i: int, n: int) -> None:
            _job.update(done=i, total=n)

        walk_forward(md, cfg, train_years=req.train_years, capital=req.capital, progress=progress)
        _job.update(state="done", message="Complete")
    except Exception as exc:
        traceback.print_exc()
        _job.update(state="error", error=str(exc), message="Failed")


@app.get("/api/backtest/status")
async def backtest_status() -> dict:
    return dict(_job)


@app.get("/api/backtest/latest")
async def backtest_latest() -> dict:
    data = _read_state("last_backtest.json")
    return {"available": data is not None, "result": data}


@app.get("/api/plan")
async def plan_latest() -> dict:
    data = _read_state("plan.json")
    return {"available": data is not None, "plan": data}


@app.post("/api/plan")
async def plan_create(req: PlanRequest) -> dict:
    from engine.plan import make_plan

    cfg = load_config()
    if req.use_paper:
        ledger = paper.load()
        if ledger is None:
            raise HTTPException(400, "No paper account yet")
        holdings, cash, peak = ledger["holdings"], ledger["cash"], ledger["peak_equity"]
    else:
        holdings, cash, peak = req.positions, req.cash, None
    try:
        plan = await asyncio.to_thread(make_plan, cfg, holdings, cash, None, peak)
    except Exception as exc:
        raise HTTPException(500, f"Could not build plan: {exc}") from exc
    return {"available": True, "plan": plan}


@app.get("/api/paper")
async def paper_state() -> dict:
    ledger = paper.load()
    return {"available": ledger is not None, "ledger": ledger}


@app.post("/api/paper/init")
async def paper_init(req: PaperInit) -> dict:
    if req.capital <= 0:
        raise HTTPException(400, "Capital must be positive")
    return {"available": True, "ledger": paper.init(req.capital)}


@app.post("/api/paper/step")
async def paper_step() -> dict:
    if paper.load() is None:
        raise HTTPException(400, "No paper account yet")
    try:
        out = await asyncio.to_thread(paper.step, load_config())
    except Exception as exc:
        raise HTTPException(500, f"Paper step failed: {exc}") from exc
    return {"available": True, "ledger": out["ledger"], "plan": out["plan"], "traded": out["traded"]}


@app.get("/api/robinhood/tools")
async def robinhood_tools() -> dict:
    data = _read_state("robinhood_tools.json")
    return {"available": data is not None, "tools": data}
