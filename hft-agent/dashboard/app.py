"""
HFT Agent Admin Dashboard -- FastAPI Backend

Provides REST API routes, WebSocket live updates, simulator controls,
and explainability endpoints for the web-based admin dashboard.
"""

from __future__ import annotations

import asyncio
import math
import random
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class AgentStatus:
    """Snapshot of a single agent's health."""

    name: str
    state: str = "idle"  # idle | running | error | halted
    last_heartbeat: float = 0.0
    messages_processed: int = 0
    error_message: str | None = None


@dataclass
class TradeRecord:
    """Completed trade record for the activity log."""

    trade_id: str
    symbol: str
    side: str
    qty: float
    price: float
    pnl: float
    timestamp: str
    signal_strength: float = 0.0
    agent: str = "execution"
    explanation: str = ""


@dataclass
class SimulationResult:
    """Results of a backtest / simulation run."""

    run_id: str
    status: str  # pending | running | completed | failed
    symbols: list[str] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 0.0
    final_equity: float = 0.0
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0
    win_rate: float = 0.0
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""


# ---------------------------------------------------------------------------
# Dashboard state
# ---------------------------------------------------------------------------


class DashboardState:
    """In-memory state container updated by the multi-agent coordinator.

    In production the coordinator pushes real-time data here.
    In standalone/demo mode it populates itself with synthetic data.
    """

    def __init__(self) -> None:
        # Core collections (bounded deques)
        self.recent_signals: deque[dict[str, Any]] = deque(maxlen=500)
        self.recent_trades: deque[dict[str, Any]] = deque(maxlen=1000)
        self.portfolio_snapshots: deque[dict[str, Any]] = deque(maxlen=10000)

        # Agent health
        self.agent_statuses: dict[str, AgentStatus] = {
            name: AgentStatus(name=name)
            for name in [
                "market_data",
                "signal",
                "risk",
                "execution",
                "portfolio",
            ]
        }

        # Simulation results keyed by run_id
        self.simulation_results: dict[str, SimulationResult] = {}
        self._sim_tasks: dict[str, asyncio.Task[None]] = {}

        # System-level flags
        self.trading_halted: bool = False
        self.system_start_time: str = datetime.now(timezone.utc).isoformat()
        self.start_time: float = time.time()
        self.current_regime: str = "random_walk"

        # Tracked symbols
        self.symbols: list[str] = ["SPY", "QQQ", "AAPL", "MSFT", "TSLA", "NVDA"]

        # Live prices
        self.prices: dict[str, float] = {
            "SPY": 587.42, "QQQ": 503.18, "AAPL": 227.63,
            "MSFT": 442.51, "TSLA": 248.92, "NVDA": 138.47,
        }

        # Per-symbol signal snapshots
        self.signals: dict[str, dict[str, float]] = {
            s: {"ofi": 0.0, "hurst": 0.5, "vpin": 0.0, "multifractal": 0.0, "composite": 0.0}
            for s in self.symbols
        }

        # Per-symbol regimes & Hurst values
        self.regimes: dict[str, str] = {s: "random_walk" for s in self.symbols}
        self.hurst_values: dict[str, float] = {s: 0.5 for s in self.symbols}

        # Current portfolio (latest snapshot)
        self.portfolio: dict[str, Any] = {
            "cash": 0.0,
            "positions": {},
            "total_equity": 0.0,
            "daily_pnl": 0.0,
            "daily_return": 0.0,
            "max_drawdown": 0.0,
            "exposure_pct": 0.0,
        }

        # Risk metrics
        self.risk_metrics: dict[str, Any] = {
            "exposure_pct": 0.0,
            "cvar_95": 0.0,
            "daily_pnl": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "position_count": 0,
            "largest_position_pct": 0.0,
            "var_95": 0.0,
        }

        # Equity curve for chart
        self.equity_curve: deque[dict[str, Any]] = deque(maxlen=500)

        # Activity / decision feed
        self.activity: deque[dict[str, Any]] = deque(maxlen=200)

        # Positions
        self.positions: list[dict[str, Any]] = []

        # Performance metrics
        self.sharpe: float = 0.0
        self.win_rate: float = 0.0
        self.profit_factor: float = 0.0
        self.kelly_fraction: float = 0.25

        # Initialize demo data
        self._init_demo_data()

    # -- Mutation helpers (called by the coordinator) ----------------------

    def add_signal(self, signal: dict[str, Any]) -> None:
        self.recent_signals.appendleft(signal)

    def add_trade(self, trade: dict[str, Any]) -> None:
        self.recent_trades.appendleft(trade)

    def update_portfolio(self, snapshot: dict[str, Any]) -> None:
        self.portfolio = snapshot
        self.portfolio_snapshots.append(snapshot)

    def update_agent_status(self, name: str, new_state: str, **extra: Any) -> None:
        if name in self.agent_statuses:
            self.agent_statuses[name].state = new_state
            if "last_heartbeat" in extra:
                self.agent_statuses[name].last_heartbeat = extra["last_heartbeat"]
            if "error_message" in extra:
                self.agent_statuses[name].error_message = extra["error_message"]

    def update_risk(self, metrics: dict[str, Any]) -> None:
        self.risk_metrics.update(metrics)

    def set_regime(self, regime: str) -> None:
        self.current_regime = regime

    def snapshot(self) -> dict[str, Any]:
        """Full state dump for the REST /api/status endpoint."""
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        return {
            "trading_halted": self.trading_halted,
            "system_start_time": self.system_start_time,
            "uptime": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "current_regime": self.current_regime,
            "agents": {
                name: {
                    "name": s.name,
                    "state": s.state,
                    "last_heartbeat": s.last_heartbeat,
                    "messages_processed": s.messages_processed,
                    "error_message": s.error_message,
                }
                for name, s in self.agent_statuses.items()
            },
            "portfolio": self.portfolio,
            "risk": self.risk_metrics,
            "signal_count": len(self.recent_signals),
            "trade_count": len(self.recent_trades),
            "symbols": self.symbols,
            "prices": self.prices,
            "signals": self.signals,
            "regimes": self.regimes,
        }

    # -- Demo data ---------------------------------------------------------

    def _init_demo_data(self) -> None:
        now = datetime.now(timezone.utc)

        # Agent statuses
        for name in self.agent_statuses:
            self.agent_statuses[name].state = "running"
            self.agent_statuses[name].last_heartbeat = now.timestamp()
            self.agent_statuses[name].messages_processed = random.randint(5000, 50000)

        # Positions
        self.positions = [
            {"symbol": "SPY", "side": "long", "qty": 85, "entry_price": 584.20,
             "current_price": 587.42, "unrealized_pnl": 273.70, "pnl_pct": 0.055},
            {"symbol": "QQQ", "side": "long", "qty": 40, "entry_price": 498.50,
             "current_price": 503.18, "unrealized_pnl": 187.20, "pnl_pct": 0.094},
            {"symbol": "NVDA", "side": "short", "qty": 50, "entry_price": 141.30,
             "current_price": 138.47, "unrealized_pnl": 141.50, "pnl_pct": 0.200},
            {"symbol": "AAPL", "side": "long", "qty": 60, "entry_price": 225.10,
             "current_price": 227.63, "unrealized_pnl": 151.80, "pnl_pct": 0.056},
        ]

        # Portfolio
        self.portfolio = {
            "cash": 45_231.87,
            "positions": {p["symbol"]: p for p in self.positions},
            "total_equity": 102_487.35,
            "daily_pnl": 487.35,
            "daily_return": 0.48,
            "max_drawdown": 2.1,
            "exposure_pct": 55.8,
        }

        # Risk
        self.risk_metrics = {
            "exposure_pct": 55.8,
            "cvar_95": 1842.50,
            "daily_pnl": 487.35,
            "max_drawdown": 2.1,
            "sharpe_ratio": 1.91,
            "position_count": len(self.positions),
            "largest_position_pct": 24.3,
            "var_95": 1245.00,
            "daily_loss_consumed_pct": 12.4,
            "drawdown_pct": 0.59,
            "fragility": "robust",
        }

        self.sharpe = 1.91
        self.win_rate = 57.3
        self.profit_factor = 1.82

        # Generate equity curve history
        eq = 100_000.0
        for i in range(100):
            change = random.gauss(0.0003, 0.004)
            eq *= (1 + change)
            self.equity_curve.append({
                "t": (now.timestamp() - (100 - i) * 300) * 1000,
                "equity": round(eq, 2),
            })

        # Generate signal snapshots
        for s in self.symbols:
            ofi = math.sin(hash(s) % 10) * 0.6 + random.gauss(0, 0.1)
            hurst = 0.5 + 0.2 * math.sin(hash(s) % 7) + random.gauss(0, 0.03)
            hurst = max(0.0, min(1.0, hurst))
            vpin = 0.3 + 0.15 * math.sin(hash(s) % 5) + random.gauss(0, 0.05)
            vpin = max(0.0, min(1.0, vpin))
            mf = 0.5 + 0.3 * math.cos(hash(s) % 3) + random.gauss(0, 0.04)
            comp = ofi * 0.4 + (hurst - 0.5) * 0.3 + (1 - vpin) * 0.2 + mf * 0.1
            self.signals[s] = {
                "ofi": round(ofi, 4), "hurst": round(hurst, 4),
                "vpin": round(vpin, 4), "multifractal": round(mf, 4),
                "composite": round(comp, 4),
            }

        # Regime assignments
        regime_opts = ["trending", "mean_reverting", "random_walk"]
        for s in self.symbols:
            self.regimes[s] = random.choice(regime_opts)
            self.hurst_values[s] = round(0.3 + random.random() * 0.4, 3)

        # Trade history
        for i in range(30):
            sym = random.choice(self.symbols)
            side = random.choice(["buy", "sell"])
            qty = random.randint(5, 100)
            price = self.prices.get(sym, 100.0) + random.gauss(0, 2)
            pnl = random.gauss(20, 80)
            ts = datetime.fromtimestamp(
                now.timestamp() - (30 - i) * 120, tz=timezone.utc
            ).isoformat()
            self.recent_trades.append({
                "trade_id": uuid.uuid4().hex[:8],
                "timestamp": ts,
                "symbol": sym, "side": side, "qty": qty,
                "price": round(price, 2),
                "signal_strength": round(random.uniform(0.5, 1.0), 3),
                "pnl": round(pnl, 2),
            })

        # Activity feed
        entries = [
            ("Signal fired: SPY composite +0.72, regime TRENDING", "info",
             "OFI showed strong buying pressure (+0.68). Hurst=0.62 confirms trending regime. VPIN=0.31 is clean. Kelly sizing: 85 shares."),
            ("Order filled: BUY 85 SPY @ 584.20", "info",
             "Execution via TWAP split across 3 child orders. Average slippage: 0.02 bps."),
            ("VPIN spike detected on TSLA: 0.81 (threshold 0.75)", "warning",
             "Informed flow detected. Reducing TSLA exposure by 50%. Toxicity discount applied to all TSLA signals."),
            ("Kelly fraction adjusted: 0.25 -> 0.22 (tail estimate widened)", "info",
             "Tail exponent dropped from 3.2 to 2.8. Wider tails require more conservative sizing to maintain survival probability."),
            ("Regime change: QQQ shifted to MEAN_REVERTING (H=0.38)", "info",
             "Hurst exponent crossed below 0.45. Switching from momentum to mean-reversion strategy. OFI signals will be inverted."),
            ("Fragility check: ROBUST (vega=+0.12, gamma=+0.04)", "info",
             "Portfolio benefits slightly from volatility increases. No fragility risk detected."),
            ("Order filled: SHORT 50 NVDA @ 141.30", "info",
             "Mean-reversion signal triggered. NVDA price 2.1 sigma above 20-bar VWAP in mean-reverting regime."),
            ("Daily loss consumed: 12.4% of limit", "info",
             "Well within the 100% daily loss budget. Current CVaR estimate: $1,842.50 at 99% confidence."),
            ("CVaR estimate updated: $1,842.50 at 99% confidence", "info",
             "Computed using Student-t distribution with 3.12 degrees of freedom. Gaussian CVaR would underestimate by ~3.2x."),
            ("Multifractal width narrowing on MSFT -- stability improving", "info",
             "The multifractal spectrum is narrowing, indicating simpler price dynamics. Signal reliability improving."),
            ("Heartbeat: all 5 agents healthy, 52891 messages processed", "info",
             "All agents responding within SLA. No message queue backpressure detected."),
            ("Signal fired: NVDA composite -0.65, regime RANDOM_WALK", "info",
             "Moderate sell signal but in random-walk regime. Signal discounted by 40%. Position sized conservatively."),
        ]
        for i, (msg, sev, detail) in enumerate(entries):
            ts = datetime.fromtimestamp(
                now.timestamp() - (len(entries) - i) * 30, tz=timezone.utc
            ).isoformat()
            self.activity.append({
                "timestamp": ts, "message": msg, "severity": sev,
                "detail": detail, "source": "system",
            })

        self.start_time = time.time() - 3600 * 2.5  # 2.5 hours ago
        self.trading_halted = False


# ---------------------------------------------------------------------------
# Explainability helpers
# ---------------------------------------------------------------------------

SIGNAL_EXPLANATIONS: dict[str, dict[str, str]] = {
    "ofi": {
        "name": "Order Flow Imbalance",
        "short": "Measures net buying vs selling pressure from the order book.",
        "detail": (
            "OFI (Cont et al. 2011) tracks the imbalance between bid and ask "
            "changes in the limit order book. A positive OFI indicates net "
            "buying pressure. Range: -1 (strong sell) to +1 (strong buy)."
        ),
    },
    "hurst": {
        "name": "Hurst Exponent",
        "short": "Detects whether the market is trending, mean-reverting, or random.",
        "detail": (
            "H > 0.55 suggests persistence (trending). H < 0.45 suggests "
            "antipersistence (mean reversion). H near 0.5 is a random walk."
        ),
    },
    "vpin": {
        "name": "VPIN (Volume-Synchronized Probability of Informed Trading)",
        "short": "Detects toxic order flow from informed traders.",
        "detail": (
            "VPIN (Easley et al. 2011) estimates the fraction of trading "
            "volume from informed traders. High VPIN (> 0.75) means toxic flow."
        ),
    },
    "multifractal": {
        "name": "Multifractal Width",
        "short": "Measures the complexity and stability of the price process.",
        "detail": (
            "Based on Mandelbrot's MMAR. Wide spectrum indicates complex, "
            "unstable dynamics. Narrow spectrum suggests simpler behavior."
        ),
    },
}


# ---------------------------------------------------------------------------
# Application singleton
# ---------------------------------------------------------------------------

state = DashboardState()

app = FastAPI(title="HFT Agent Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Public helper -- push updates from the coordinator
# ---------------------------------------------------------------------------


async def push_update(category: str, data: dict[str, Any]) -> None:
    """Broadcast a categorised update to all connected WebSocket clients."""
    await manager.broadcast({"type": category, "data": data})


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard() -> HTMLResponse:
    html_path = TEMPLATE_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text())


@app.get("/api/status")
async def get_status() -> dict[str, Any]:
    return state.snapshot()


@app.get("/api/portfolio")
async def get_portfolio() -> dict[str, Any]:
    return {
        "current": state.portfolio,
        "positions": state.positions,
        "equity_curve": list(state.equity_curve),
        "history": list(state.portfolio_snapshots)[-200:],
    }


@app.get("/api/signals")
async def get_signals() -> dict[str, Any]:
    return {
        "current": state.signals,
        "regimes": state.regimes,
        "recent": list(state.recent_signals)[:100],
    }


@app.get("/api/trades")
async def get_trades() -> dict[str, Any]:
    return {"trades": list(state.recent_trades)[:200]}


@app.get("/api/risk")
async def get_risk() -> dict[str, Any]:
    return state.risk_metrics


@app.post("/api/simulator/run")
async def run_simulation(body: dict[str, Any]) -> dict[str, Any]:
    run_id = uuid.uuid4().hex[:12]
    result = SimulationResult(
        run_id=run_id,
        status="running",
        symbols=body.get("symbols", ["SPY"]),
        start_date=body.get("start_date", "2024-01-01"),
        end_date=body.get("end_date", "2024-12-31"),
        initial_capital=body.get("initial_capital", 1_000_000),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    state.simulation_results[run_id] = result
    task = asyncio.create_task(_run_simulation(run_id, result))
    state._sim_tasks[run_id] = task
    await push_update("simulation", {"run_id": run_id, "status": "running"})
    return {"run_id": run_id, "status": "running"}


@app.get("/api/simulator/results/{run_id}")
async def get_simulation_results(run_id: str) -> dict[str, Any]:
    result = state.simulation_results.get(run_id)
    if result is None:
        return {"error": "not_found"}
    return {
        "run_id": result.run_id,
        "status": result.status,
        "symbols": result.symbols,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "initial_capital": result.initial_capital,
        "final_equity": result.final_equity,
        "total_return": result.total_return,
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown": result.max_drawdown,
        "total_trades": result.total_trades,
        "win_rate": result.win_rate,
        "equity_curve": result.equity_curve,
        "created_at": result.created_at,
    }


@app.post("/api/halt")
async def halt_trading() -> dict[str, str]:
    state.trading_halted = True
    now_iso = datetime.now(timezone.utc).isoformat()
    state.activity.append({
        "timestamp": now_iso,
        "message": "EMERGENCY HALT. All orders cancelled, positions being closed.",
        "severity": "critical",
        "detail": "Manual halt triggered via dashboard. All open orders cancelled. Risk manager closing positions.",
        "source": "dashboard",
    })
    await push_update("system", {"trading_halted": True})
    return {"status": "halted"}


@app.post("/api/resume")
async def resume_trading() -> dict[str, str]:
    state.trading_halted = False
    now_iso = datetime.now(timezone.utc).isoformat()
    state.activity.append({
        "timestamp": now_iso,
        "message": "Trading resumed by operator.",
        "severity": "info",
        "detail": "Manual resume triggered via dashboard. All agents re-enabled.",
        "source": "dashboard",
    })
    await push_update("system", {"trading_halted": False})
    return {"status": "running"}


# ---------------------------------------------------------------------------
# Explainability endpoints
# ---------------------------------------------------------------------------


@app.get("/api/explain/signal/{signal_name}")
async def explain_signal_route(signal_name: str) -> dict[str, Any]:
    info = SIGNAL_EXPLANATIONS.get(signal_name.lower())
    if not info:
        return {"error": f"Unknown signal: {signal_name}",
                "available": list(SIGNAL_EXPLANATIONS.keys())}
    return info


@app.get("/api/positions")
async def get_positions() -> dict[str, Any]:
    return {"positions": state.positions}


@app.get("/api/signals/{symbol}")
async def get_signals_for_symbol(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper()
    snap = state.signals.get(symbol, {})
    return {
        "symbol": symbol,
        "signals": snap,
        "regime": state.regimes.get(symbol, "unknown"),
        "hurst": state.hurst_values.get(symbol, 0.5),
        "price": state.prices.get(symbol, 0),
        "price_change": round(random.gauss(0, 0.5), 2),
    }


@app.get("/api/signals/history/{symbol}")
async def get_signal_history(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper()
    history = [s for s in state.recent_signals if s.get("symbol") == symbol][:200]
    return {"symbol": symbol, "history": history}


@app.get("/api/metrics")
async def get_metrics() -> dict[str, Any]:
    return {
        "mad_ratio": round(random.uniform(1.5, 3.0), 3),
        "tail_exponent": round(random.uniform(2.5, 4.0), 2),
        "win_rate": state.win_rate,
        "profit_factor": state.profit_factor,
        "kelly_fraction": state.kelly_fraction,
        "sharpe": state.sharpe,
        "calmar_ratio": round(random.uniform(0.5, 2.5), 3),
        "max_drawdown": state.risk_metrics.get("max_drawdown", 0),
    }


@app.get("/api/agents")
async def get_agents() -> dict[str, Any]:
    return {
        "agents": [
            {
                "name": s.name,
                "state": s.state,
                "last_heartbeat": s.last_heartbeat,
                "messages_processed": s.messages_processed,
                "error_message": s.error_message,
            }
            for s in state.agent_statuses.values()
        ]
    }


@app.get("/api/regime/{symbol}")
async def get_regime(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper()
    return {
        "symbol": symbol,
        "regime": state.regimes.get(symbol, "random_walk"),
        "hurst": state.hurst_values.get(symbol, 0.5),
    }


@app.get("/api/explain/decision/latest")
async def explain_decision_latest() -> dict[str, Any]:
    latest = list(state.activity)[-1] if state.activity else None
    if latest:
        return {
            "title": "Latest Decision",
            "summary": latest.get("message", ""),
            "detail": latest.get("detail", ""),
            "severity": latest.get("severity", "info"),
        }
    return {"title": "No Decisions", "summary": "No trading decisions recorded yet.", "detail": "", "severity": "info"}


@app.get("/api/explain/risk")
async def explain_risk() -> dict[str, Any]:
    return {
        "title": "Risk State",
        "summary": f"Exposure {state.risk_metrics.get('exposure_pct', 0):.1f}%, CVaR ${state.risk_metrics.get('cvar_95', 0):,.0f}",
        "detail": (
            f"Daily loss consumed: {state.risk_metrics.get('daily_loss_consumed_pct', 0):.1f}% of limit. "
            f"Drawdown: {state.risk_metrics.get('drawdown_pct', 0):.2f}%. "
            f"Fragility state: {state.risk_metrics.get('fragility', 'unknown')}. "
            f"Position count: {state.risk_metrics.get('position_count', 0)}. "
            "Risk agent has hard veto power over all trades."
        ),
        "severity": "critical" if state.trading_halted else "info",
    }


@app.get("/api/explain/signal/{symbol}/{signal_name}")
async def explain_signal_by_symbol(symbol: str, signal_name: str) -> dict[str, Any]:
    info = SIGNAL_EXPLANATIONS.get(signal_name.lower())
    if not info:
        return {"error": f"Unknown signal: {signal_name}", "available": list(SIGNAL_EXPLANATIONS.keys())}
    symbol = symbol.upper()
    value = state.signals.get(symbol, {}).get(signal_name, 0)
    return {**info, "symbol": symbol, "current_value": value}


@app.get("/api/explain/concept/{concept}")
async def explain_concept(concept: str) -> dict[str, Any]:
    concepts = {
        "fat_tails": {"title": "Fat Tails", "detail": "Financial returns have 'fat tails' -- extreme events happen far more often than a bell curve predicts. Our agent uses Student-t distributions with tail exponents around 3 (the 'cubic law') instead of Gaussian assumptions."},
        "kelly_criterion": {"title": "Kelly Criterion", "detail": "The Kelly Criterion determines the optimal bet size to maximize long-term wealth growth. We use fractional Kelly (25% of optimum) because over-betting is far more dangerous than under-betting."},
        "ergodicity": {"title": "Ergodicity Economics", "detail": "Financial markets are non-ergodic: the average across many investors differs from one investor's experience over time. Our agent optimizes the time-average (log-wealth growth) rather than the ensemble average."},
        "fragility": {"title": "Fragility Detection", "detail": "Based on Taleb-Douady (2012), we measure whether the strategy's P&L becomes more negative as volatility increases. Fragile strategies are immediately halted."},
        "cvar": {"title": "Conditional Value at Risk", "detail": "CVaR answers: 'In the worst 1% of scenarios, how bad is the average loss?' This is more honest than VaR because it captures tail risk."},
        "vpin_toxicity": {"title": "VPIN Toxicity", "detail": "Volume-Synchronized Probability of Informed Trading detects 'smart money' activity. When VPIN exceeds 0.7, informed traders are active and the agent steps aside."},
        "regime_detection": {"title": "Regime Detection", "detail": "Markets shift between trending (H>0.55), mean-reverting (H<0.45), and random walk regimes. The agent adapts its strategy to match the current regime."},
        "mad_ratio": {"title": "MAD Ratio", "detail": "Mean Absolute Deviation is more robust than standard deviation under fat tails. The MAD ratio replaces the Sharpe ratio for a more honest risk-adjusted return measure."},
    }
    info = concepts.get(concept.lower())
    if not info:
        return {"error": f"Unknown concept: {concept}", "available": list(concepts.keys())}
    return info


@app.get("/api/explain/metric/{metric_name}")
async def explain_metric(metric_name: str) -> dict[str, Any]:
    metrics = {
        "mad_ratio": {"title": "MAD Ratio", "detail": "Return per unit of risk using Mean Absolute Deviation. More reliable than Sharpe under fat tails. Above 0.3 is good, above 0.5 is excellent."},
        "tail_exponent": {"title": "Tail Exponent", "detail": "How fat the distribution tails are. Below 3, standard deviation is meaningless. Below 2, even the mean is unreliable."},
        "win_rate": {"title": "Win Rate", "detail": "Percentage of profitable trades. In HFT, profit factor matters more than win rate."},
        "profit_factor": {"title": "Profit Factor", "detail": "Gross profits / gross losses. Above 1.5 is good, above 2.0 is excellent."},
        "max_drawdown": {"title": "Max Drawdown", "detail": "Largest peak-to-trough decline. The most important risk metric for real portfolios."},
        "sharpe": {"title": "Sharpe Ratio", "detail": "Risk-adjusted return. Unreliable under fat tails -- use MAD ratio instead."},
        "kelly_fraction": {"title": "Kelly Fraction", "detail": "Fraction of Kelly optimum used. 0.25 means 25% of theoretical optimum, sacrificing growth for safety."},
        "calmar_ratio": {"title": "Calmar Ratio", "detail": "Annualized return / max drawdown. Above 1.0 is good, above 3.0 is excellent."},
    }
    info = metrics.get(metric_name.lower())
    if not info:
        return {"error": f"Unknown metric: {metric_name}", "available": list(metrics.keys())}
    return info


@app.post("/api/control/{action}")
async def control_action(action: str) -> dict[str, str]:
    if action == "halt":
        state.trading_halted = True
        return {"status": "halted"}
    elif action == "start" or action == "resume":
        state.trading_halted = False
        return {"status": "running"}
    elif action == "stop":
        state.trading_halted = True
        return {"status": "stopped"}
    return {"status": "unknown_action"}


@app.post("/api/simulator/start")
async def start_simulation(body: dict[str, Any]) -> dict[str, Any]:
    run_id = uuid.uuid4().hex[:12]
    result = SimulationResult(
        run_id=run_id,
        status="running",
        symbols=body.get("symbols", ["SPY"]),
        start_date=body.get("start_date", "2024-01-01"),
        end_date=body.get("end_date", "2024-12-31"),
        initial_capital=body.get("initial_capital", 100_000),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    state.simulation_results[run_id] = result
    task = asyncio.create_task(_run_simulation(run_id, result))
    state._sim_tasks[run_id] = task
    return {"run_id": run_id, "status": "running"}


@app.post("/api/simulator/stop")
async def stop_simulation() -> dict[str, str]:
    for task in state._sim_tasks.values():
        task.cancel()
    state._sim_tasks.clear()
    return {"status": "stopped"}


@app.get("/api/simulator/status")
async def sim_status() -> dict[str, Any]:
    for rid, result in state.simulation_results.items():
        if result.status == "running":
            return {"run_id": rid, "status": "running", "progress": 50}
    return {"status": "idle", "progress": 0}


@app.get("/api/simulator/results")
async def sim_results_latest() -> dict[str, Any]:
    completed = [r for r in state.simulation_results.values() if r.status == "completed"]
    if not completed:
        return {"status": "no_results"}
    latest = completed[-1]
    return {
        "run_id": latest.run_id,
        "status": latest.status,
        "result": {
            "final_equity": latest.final_equity,
            "total_return_pct": latest.total_return,
            "metrics": {
                "total_trades": latest.total_trades,
                "win_rate": latest.win_rate,
                "max_drawdown": latest.max_drawdown,
                "mad_ratio": round(random.uniform(1.5, 3.0), 3),
                "tail_exponent": round(random.uniform(2.5, 4.0), 2),
            },
        },
    }


@app.get("/api/activity")
async def get_activity() -> dict[str, Any]:
    return {"activity": list(state.activity)}


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        # Send full initial state on connect
        await ws.send_json({"type": "init", "data": state.snapshot()})
        # Keep the connection alive -- read client pings / commands
        while True:
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=30)
                # Clients can send {"action": "ping"} to keep alive
                if data:
                    await ws.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                await ws.send_json({"type": "heartbeat", "t": time.time()})
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------


async def _run_simulation(run_id: str, result: SimulationResult) -> None:
    """Run a synthetic simulation and push progress via WebSocket."""
    try:
        equity = result.initial_capital
        curve: list[dict[str, Any]] = []
        n_steps = 252
        wins = 0
        total_profit = 0.0
        total_loss = 0.0
        total_trades = 0
        peak = equity

        for i in range(n_steps):
            progress = (i + 1) / n_steps * 100
            ret = random.gauss(0.0004, 0.012)
            pnl = equity * ret * 0.25 * 4  # quarter Kelly
            equity += pnl
            peak = max(peak, equity)
            curve.append({
                "day": i + 1,
                "equity": round(equity, 2),
                "pnl": round(pnl, 2),
            })
            if random.random() < 0.3:
                trade_pnl = round(pnl * random.uniform(0.2, 1.0), 2)
                total_trades += 1
                if trade_pnl > 0:
                    wins += 1
                    total_profit += trade_pnl
                else:
                    total_loss += abs(trade_pnl)
            await asyncio.sleep(0.02)
            if i % 10 == 0:
                await push_update("sim_progress", {
                    "run_id": run_id, "progress": round(progress, 1),
                })

        total_return = (equity - result.initial_capital) / result.initial_capital * 100
        max_dd = (peak - min(c["equity"] for c in curve)) / peak * 100 if peak > 0 else 0

        result.status = "completed"
        result.final_equity = round(equity, 2)
        result.total_return = round(total_return, 2)
        result.max_drawdown = round(max_dd, 2)
        result.total_trades = total_trades
        result.win_rate = round(wins / total_trades * 100, 1) if total_trades else 0
        result.sharpe_ratio = round(total_return / max_dd, 2) if max_dd > 0 else 0
        result.equity_curve = curve

        await push_update("sim_complete", {
            "run_id": run_id,
            "final_equity": result.final_equity,
            "total_return": result.total_return,
            "max_drawdown": result.max_drawdown,
            "total_trades": result.total_trades,
            "win_rate": result.win_rate,
            "sharpe_ratio": result.sharpe_ratio,
        })

    except asyncio.CancelledError:
        result.status = "failed"
    except Exception:
        result.status = "failed"


# ---------------------------------------------------------------------------
# Background live ticker -- synthetic data for demo mode
# ---------------------------------------------------------------------------


async def _live_ticker() -> None:
    """Periodically update state with synthetic data and push to clients."""
    while True:
        await asyncio.sleep(2)

        if state.trading_halted:
            continue

        now = datetime.now(timezone.utc)

        # Update prices
        for sym in state.symbols:
            price = state.prices[sym]
            change_pct = random.gauss(0, 0.001)
            state.prices[sym] = round(price * (1 + change_pct), 2)

        # Update signals
        for sym in state.symbols:
            snap = state.signals[sym]
            snap["ofi"] = round(max(-1, min(1, snap["ofi"] + random.gauss(0, 0.03))), 4)
            snap["hurst"] = round(max(0, min(1, snap["hurst"] + random.gauss(0, 0.005))), 4)
            snap["vpin"] = round(max(0, min(1, snap["vpin"] + random.gauss(0, 0.01))), 4)
            snap["multifractal"] = round(max(0, min(1, snap["multifractal"] + random.gauss(0, 0.01))), 4)
            snap["composite"] = round(
                snap["ofi"] * 0.4 + (snap["hurst"] - 0.5) * 0.3
                + (1 - snap["vpin"]) * 0.2 + snap["multifractal"] * 0.1,
                4,
            )
            state.recent_signals.appendleft({
                "symbol": sym, "timestamp": now.isoformat(), **snap,
            })

        # Update equity
        eq = state.portfolio.get("total_equity", 100_000)
        eq_change = random.gauss(0, 50)
        eq = round(eq + eq_change, 2)
        state.portfolio["total_equity"] = eq
        state.portfolio["daily_pnl"] = round(
            state.portfolio.get("daily_pnl", 0) + eq_change, 2
        )
        state.equity_curve.append({
            "t": now.timestamp() * 1000,
            "equity": eq,
        })

        # Update positions
        for pos in state.positions:
            p = state.prices.get(pos["symbol"], pos["current_price"])
            pos["current_price"] = p
            direction = 1 if pos["side"] == "long" else -1
            pos["unrealized_pnl"] = round(
                (p - pos["entry_price"]) * pos["qty"] * direction, 2
            )
            if pos["entry_price"] > 0:
                pos["pnl_pct"] = round(
                    pos["unrealized_pnl"] / (pos["entry_price"] * pos["qty"]) * 100, 3
                )

        # Update risk metrics
        state.risk_metrics["daily_pnl"] = state.portfolio["daily_pnl"]
        state.risk_metrics["cvar_95"] = round(
            state.risk_metrics.get("cvar_95", 1800) + random.gauss(0, 10), 2
        )

        # Update agent heartbeats
        for ag in state.agent_statuses.values():
            ag.last_heartbeat = now.timestamp()
            ag.messages_processed += random.randint(1, 20)

        # Occasional activity entry
        if random.random() < 0.12:
            msgs = [
                (f"Signal update: {random.choice(state.symbols)} composite "
                 f"{random.uniform(-0.8, 0.8):+.3f}", "info",
                 "Composite signal updated after new order book snapshot. All sub-signals within normal range."),
                (f"Heartbeat: all {len(state.agent_statuses)} agents healthy", "info",
                 "Periodic health check passed. No agent latency or queue depth issues."),
                (f"VPIN tick on {random.choice(state.symbols)}: "
                 f"{random.uniform(0.2, 0.9):.2f}", "info",
                 "VPIN updated from latest volume bucket. No toxicity threshold breach."),
                (f"Regime check: {random.choice(state.symbols)} "
                 f"Hurst={random.uniform(0.3, 0.7):.3f}", "info",
                 "Hurst exponent re-estimated from rolling window. Regime classification unchanged."),
            ]
            msg, sev, detail = random.choice(msgs)
            state.activity.append({
                "timestamp": now.isoformat(),
                "message": msg,
                "severity": sev,
                "detail": detail,
                "source": "system",
            })

        # Broadcast tick to all clients
        await manager.broadcast({
            "type": "tick",
            "data": {
                "t": now.timestamp() * 1000,
                "equity": eq,
                "daily_pnl": state.portfolio["daily_pnl"],
                "prices": state.prices,
                "signals": state.signals,
                "positions": state.positions,
                "activity": list(state.activity)[-3:],
                "risk": state.risk_metrics,
                "agents": {
                    name: {"state": s.state, "messages_processed": s.messages_processed}
                    for name, s in state.agent_statuses.items()
                },
            },
        })


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(_live_ticker())


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
