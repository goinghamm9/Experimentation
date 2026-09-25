from __future__ import annotations

import copy
import itertools
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from backtest.engine import BacktestEngine, BacktestResult
from core.risk.manager import RiskCheck, RiskManager
from core.signals.aggregator import SignalAggregator
from strategies.adaptive_microstructure import AdaptiveMicrostructureStrategy, TradeDecision
from utils.config import RiskConfig, Settings, SignalsConfig, StrategyConfig, load_settings
from utils.logging import get_logger
from utils.types import Bar, PortfolioState, Signal, Tick

from .data_loader import generate_synthetic_ticks, load_historical_bars

logger = get_logger(__name__)


@dataclass
class TradeRecord:
    timestamp: datetime
    symbol: str
    side: str
    qty: float
    price: float
    entry_price: float | None = None
    exit_price: float | None = None
    pnl: float = 0.0
    signal_strength: float = 0.0
    regime: str = ""
    reason: str = ""


@dataclass
class SignalRecord:
    timestamp: datetime
    symbol: str
    name: str
    value: float
    strength: float
    direction: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionRecord:
    timestamp: datetime
    symbol: str
    should_trade: bool
    reason: str
    signal_strength: float = 0.0
    risk_approved: bool | None = None
    kelly_size: float | None = None
    regime: str = ""


@dataclass
class RiskEvent:
    timestamp: datetime
    event_type: str
    approved: bool
    reason: str
    cvar: float | None = None
    exposure_pct: float | None = None
    daily_pnl: float = 0.0
    kelly_size: float | None = None


@dataclass
class SimulationResult:
    equity_curve: list[float] = field(default_factory=list)
    trades: list[TradeRecord] = field(default_factory=list)
    signals: list[SignalRecord] = field(default_factory=list)
    decisions: list[DecisionRecord] = field(default_factory=list)
    risk_events: list[RiskEvent] = field(default_factory=list)
    backtest_report: BacktestResult | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    symbols: list[str] = field(default_factory=list)
    ticks_processed: int = 0
    wall_clock_seconds: float = 0.0

    @property
    def total_return(self) -> float:
        if len(self.equity_curve) < 2 or self.equity_curve[0] <= 0:
            return 0.0
        return (self.equity_curve[-1] - self.equity_curve[0]) / self.equity_curve[0]

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        winning = [t for t in self.trades if t.pnl > 0]
        return len(winning) / len(self.trades) if self.trades else 0.0


class SimulatorEngine:
    def __init__(
        self,
        initial_capital: float = 100_000,
        settings: Settings | None = None,
        ticks_per_bar: int = 20,
    ):
        self._initial_capital = initial_capital
        self._settings = settings or load_settings()
        self._ticks_per_bar = ticks_per_bar

    def run(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        speed: float = 0.0,
        interval: str = "1d",
    ) -> SimulationResult:
        """Run a full simulation over historical data.

        Args:
            symbols: List of ticker symbols.
            start_date: "YYYY-MM-DD" start date.
            end_date: "YYYY-MM-DD" end date.
            speed: Replay speed multiplier. 0 = max speed (no delay).
                   1 = real-time, 10 = 10x, 100 = 100x.
            interval: Bar interval for data download.
        """
        wall_start = time.monotonic()

        bars_by_symbol = load_historical_bars(symbols, start_date, end_date, interval)
        all_ticks = self._build_tick_stream(bars_by_symbol)

        if not all_ticks:
            logger.warning("no_ticks_generated", symbols=symbols)
            return SimulationResult(symbols=symbols)

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

        result = SimulationResult(
            symbols=symbols,
            start_time=all_ticks[0].timestamp,
            end_time=all_ticks[-1].timestamp,
            parameters={
                "initial_capital": self._initial_capital,
                "interval": interval,
                "speed": speed,
                "ticks_per_bar": self._ticks_per_bar,
                "strategy": self._settings.strategy.model_dump(),
                "risk": self._settings.risk.model_dump(),
            },
        )

        prev_timestamp = all_ticks[0].timestamp
        for tick in all_ticks:
            if speed > 0:
                dt = (tick.timestamp - prev_timestamp).total_seconds()
                if dt > 0:
                    time.sleep(dt / speed)
            prev_timestamp = tick.timestamp

            portfolio = backtest.get_portfolio_state()
            decision = strategy.on_tick(tick, portfolio)

            self._record_signals(result, tick, aggregator)
            self._record_decision(result, tick, decision, aggregator)
            self._record_risk_event(result, tick, decision, risk_mgr, portfolio)

            if decision.should_trade and decision.order is not None:
                filled = backtest.execute_order(decision.order, tick.price, tick.timestamp)
                if filled:
                    self._record_trade(result, tick, decision, aggregator)

            backtest.update_prices({tick.symbol: tick.price})
            result.equity_curve.append(backtest.get_portfolio_state().total_equity)
            result.ticks_processed += 1

        result.backtest_report = backtest.generate_report()
        result.wall_clock_seconds = time.monotonic() - wall_start

        logger.info(
            "simulation_complete",
            ticks=result.ticks_processed,
            trades=result.total_trades,
            total_return=f"{result.total_return:.4%}",
            wall_clock=f"{result.wall_clock_seconds:.1f}s",
        )

        return result

    def run_parameter_sweep(
        self,
        param_grid: dict[str, list[Any]],
        symbols: list[str],
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> list[SimulationResult]:
        """Run simulations across a parameter grid.

        param_grid keys can be:
          - "kelly_fraction": list of kelly fractions
          - "min_signal_strength": list of thresholds
          - "daily_loss_limit_pct": list of daily loss limits
          - "initial_capital": list of starting capitals
          - Any key matching a StrategyConfig or RiskConfig field.
        """
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combos = list(itertools.product(*values))

        logger.info("parameter_sweep", total_combinations=len(combos))
        results: list[SimulationResult] = []

        for combo in combos:
            params = dict(zip(keys, combo))
            settings = copy.deepcopy(self._settings)
            capital = self._initial_capital

            for k, v in params.items():
                if k == "initial_capital":
                    capital = v
                elif hasattr(settings.strategy, k):
                    setattr(settings.strategy, k, v)
                elif hasattr(settings.risk, k):
                    setattr(settings.risk, k, v)

            engine = SimulatorEngine(
                initial_capital=capital,
                settings=settings,
                ticks_per_bar=self._ticks_per_bar,
            )
            result = engine.run(symbols, start_date, end_date, speed=0.0, interval=interval)
            result.parameters.update(params)
            results.append(result)

            logger.info(
                "sweep_iteration",
                params=params,
                total_return=f"{result.total_return:.4%}",
                trades=result.total_trades,
            )

        return results

    def _build_tick_stream(self, bars_by_symbol: dict[str, list[Bar]]) -> list[Tick]:
        all_ticks: list[Tick] = []
        for symbol, bars in bars_by_symbol.items():
            ticks = generate_synthetic_ticks(bars, self._ticks_per_bar)
            all_ticks.extend(ticks)
        all_ticks.sort(key=lambda t: t.timestamp)
        return all_ticks

    def _record_signals(
        self, result: SimulationResult, tick: Tick, aggregator: SignalAggregator,
    ) -> None:
        composite = aggregator.get_composite_signal(tick.symbol)
        if composite is None:
            return
        result.signals.append(SignalRecord(
            timestamp=tick.timestamp,
            symbol=tick.symbol,
            name=composite.name,
            value=composite.value,
            strength=composite.strength,
            direction=composite.direction.value if composite.direction else None,
            metadata=composite.metadata,
        ))

    def _record_decision(
        self,
        result: SimulationResult,
        tick: Tick,
        decision: TradeDecision,
        aggregator: SignalAggregator,
    ) -> None:
        regime = aggregator.get_regime(tick.symbol)
        result.decisions.append(DecisionRecord(
            timestamp=tick.timestamp,
            symbol=tick.symbol,
            should_trade=decision.should_trade,
            reason=decision.reason,
            signal_strength=decision.signal.strength if decision.signal else 0.0,
            risk_approved=decision.risk_check.approved if decision.risk_check else None,
            kelly_size=decision.risk_check.kelly_size if decision.risk_check else None,
            regime=regime.value,
        ))

    def _record_risk_event(
        self,
        result: SimulationResult,
        tick: Tick,
        decision: TradeDecision,
        risk_mgr: RiskManager,
        portfolio: PortfolioState,
    ) -> None:
        if decision.risk_check is None:
            return
        rc = decision.risk_check
        result.risk_events.append(RiskEvent(
            timestamp=tick.timestamp,
            event_type="trade_check",
            approved=rc.approved,
            reason=rc.reason,
            cvar=rc.cvar,
            exposure_pct=rc.exposure_pct,
            daily_pnl=risk_mgr.daily_pnl,
            kelly_size=rc.kelly_size,
        ))

    def _record_trade(
        self,
        result: SimulationResult,
        tick: Tick,
        decision: TradeDecision,
        aggregator: SignalAggregator,
    ) -> None:
        order = decision.order
        if order is None:
            return
        regime = aggregator.get_regime(tick.symbol)
        result.trades.append(TradeRecord(
            timestamp=tick.timestamp,
            symbol=tick.symbol,
            side=order.side.value,
            qty=order.qty,
            price=tick.price,
            signal_strength=decision.signal.strength if decision.signal else 0.0,
            regime=regime.value,
            reason=decision.reason,
        ))
