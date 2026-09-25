from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from backtest.engine import BacktestEngine
from core.risk.manager import RiskManager
from core.signals.aggregator import SignalAggregator
from strategies.adaptive_microstructure import AdaptiveMicrostructureStrategy, TradeDecision
from utils.config import Settings, load_settings
from utils.logging import get_logger
from utils.types import Bar, PortfolioState, Regime, Signal, Tick

from .data_loader import generate_synthetic_ticks, load_historical_bars

logger = get_logger(__name__)


@dataclass
class StateSnapshot:
    step: int
    timestamp: datetime
    tick: Tick
    signals: dict[str, dict[str, Any]] = field(default_factory=dict)
    composite_signal: Signal | None = None
    regime: Regime = Regime.RANDOM_WALK
    regime_name: str = "random_walk"
    is_toxic: bool = False
    decision: TradeDecision | None = None
    decision_reason: str = ""
    portfolio: PortfolioState | None = None
    equity: float = 0.0
    daily_pnl: float = 0.0
    risk_halted: bool = False
    risk_cvar: float | None = None
    risk_kelly_size: float | None = None
    risk_exposure_pct: float = 0.0
    trade_executed: bool = False


class EventReplay:
    """Step-by-step replay of historical data through the strategy.

    Supports pause, step forward, and step backward by capturing full
    state snapshots at each tick.
    """

    def __init__(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 100_000,
        interval: str = "1d",
        ticks_per_bar: int = 20,
        settings: Settings | None = None,
    ):
        self._symbols = symbols
        self._initial_capital = initial_capital
        self._settings = settings or load_settings()

        bars_by_symbol = load_historical_bars(symbols, start_date, end_date, interval)
        all_ticks: list[Tick] = []
        for bars in bars_by_symbol.values():
            all_ticks.extend(generate_synthetic_ticks(bars, ticks_per_bar))
        all_ticks.sort(key=lambda t: t.timestamp)
        self._ticks = all_ticks

        self._snapshots: list[StateSnapshot] = []
        self._current_step = -1
        self._is_built = False

    @property
    def total_steps(self) -> int:
        return len(self._ticks)

    @property
    def current_step(self) -> int:
        return self._current_step

    @property
    def is_paused(self) -> bool:
        return True

    def build(self) -> None:
        """Pre-compute all snapshots by running the full simulation."""
        if self._is_built:
            return

        if not self._ticks:
            self._is_built = True
            return

        backtest = BacktestEngine(
            initial_capital=self._initial_capital,
            slippage_model=self._settings.execution.slippage_model,
        )
        aggregator = SignalAggregator(self._settings.signals)
        risk_mgr = RiskManager(self._settings.risk, self._initial_capital)
        strategy = AdaptiveMicrostructureStrategy(
            config=self._settings.strategy,
            signal_aggregator=aggregator,
            risk_manager=risk_mgr,
        )

        self._snapshots = []
        for i, tick in enumerate(self._ticks):
            portfolio = backtest.get_portfolio_state()
            decision = strategy.on_tick(tick, portfolio)

            trade_executed = False
            if decision.should_trade and decision.order is not None:
                trade_executed = backtest.execute_order(decision.order, tick.price, tick.timestamp)

            backtest.update_prices({tick.symbol: tick.price})
            updated_portfolio = backtest.get_portfolio_state()

            composite = aggregator.get_composite_signal(tick.symbol)
            regime = aggregator.get_regime(tick.symbol)
            is_toxic = aggregator.is_toxic(tick.symbol)

            raw_signals: dict[str, dict[str, Any]] = {}
            if hasattr(aggregator, "_latest_signals") and tick.symbol in aggregator._latest_signals:
                for name, sig in aggregator._latest_signals[tick.symbol].items():
                    raw_signals[name] = {
                        "value": sig.value,
                        "strength": sig.strength,
                        "direction": sig.direction.value if sig.direction else None,
                        "metadata": sig.metadata,
                    }

            snap = StateSnapshot(
                step=i,
                timestamp=tick.timestamp,
                tick=tick,
                signals=raw_signals,
                composite_signal=composite,
                regime=regime,
                regime_name=regime.value,
                is_toxic=is_toxic,
                decision=decision,
                decision_reason=decision.reason,
                portfolio=updated_portfolio,
                equity=updated_portfolio.total_equity,
                daily_pnl=risk_mgr.daily_pnl,
                risk_halted=risk_mgr.is_halted,
                risk_cvar=decision.risk_check.cvar if decision.risk_check else None,
                risk_kelly_size=decision.risk_check.kelly_size if decision.risk_check else None,
                risk_exposure_pct=updated_portfolio.exposure_pct,
                trade_executed=trade_executed,
            )
            self._snapshots.append(snap)

        self._is_built = True
        logger.info("replay_built", total_steps=len(self._snapshots))

    def step_forward(self) -> StateSnapshot | None:
        """Advance one step and return the snapshot."""
        if not self._is_built:
            self.build()
        if self._current_step >= len(self._snapshots) - 1:
            return None
        self._current_step += 1
        return self._snapshots[self._current_step]

    def step_backward(self) -> StateSnapshot | None:
        """Go back one step and return the snapshot."""
        if self._current_step <= 0:
            return None
        self._current_step -= 1
        return self._snapshots[self._current_step]

    def jump_to(self, step: int) -> StateSnapshot | None:
        """Jump to a specific step."""
        if not self._is_built:
            self.build()
        if step < 0 or step >= len(self._snapshots):
            return None
        self._current_step = step
        return self._snapshots[self._current_step]

    def get_current(self) -> StateSnapshot | None:
        """Get the current snapshot without advancing."""
        if not self._is_built:
            self.build()
        if 0 <= self._current_step < len(self._snapshots):
            return self._snapshots[self._current_step]
        return None

    def get_range(self, start: int, end: int) -> list[StateSnapshot]:
        """Get a range of snapshots."""
        if not self._is_built:
            self.build()
        start = max(0, start)
        end = min(len(self._snapshots), end)
        return self._snapshots[start:end]

    def reset(self) -> None:
        """Reset to the beginning."""
        self._current_step = -1

    def find_trades(self) -> list[StateSnapshot]:
        """Return only snapshots where a trade was executed."""
        if not self._is_built:
            self.build()
        return [s for s in self._snapshots if s.trade_executed]

    def find_risk_events(self) -> list[StateSnapshot]:
        """Return snapshots where a risk check rejected a trade."""
        if not self._is_built:
            self.build()
        return [
            s for s in self._snapshots
            if s.decision is not None
            and s.decision.risk_check is not None
            and not s.decision.risk_check.approved
        ]

    def find_regime_changes(self) -> list[StateSnapshot]:
        """Return snapshots where the regime changed."""
        if not self._is_built:
            self.build()
        changes: list[StateSnapshot] = []
        prev_regime = None
        for snap in self._snapshots:
            if snap.regime != prev_regime:
                changes.append(snap)
                prev_regime = snap.regime
        return changes
