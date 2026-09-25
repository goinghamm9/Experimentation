"""Independent risk agent with hard veto power over all trades."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import numpy as np

from core.risk.fragility import FragilityState
from core.risk.manager import RiskManager
from utils.config import RiskConfig
from utils.types import PortfolioState, Signal

from .base import BaseAgent, Message, MessageType, Priority


class RiskAgent(BaseAgent):
    """Enforces risk limits and has unconditional veto power.

    The coordinator cannot override a RISK_REJECTED decision.
    This agent also monitors portfolio-level exposure continuously
    and can issue HALT_TRADING as a circuit breaker.
    """

    def __init__(
        self,
        config: RiskConfig,
        initial_equity: float,
        fragility_check_interval: float = 60.0,
        exposure_check_interval: float = 5.0,
    ):
        super().__init__("risk")
        self._manager = RiskManager(config, initial_equity)
        self._config = config
        self._fragility_interval = fragility_check_interval
        self._exposure_interval = exposure_check_interval
        self._last_fragility_check = 0.0
        self._last_exposure_check = 0.0
        self._checks_performed = 0
        self._rejections = 0
        self._approvals = 0
        self._position_correlations: dict[tuple[str, str], float] = {}

    async def on_start(self) -> None:
        self._last_fragility_check = time.time()
        self._last_exposure_check = time.time()

    async def on_idle(self) -> None:
        now = time.time()
        if now - self._fragility_interval >= self._last_fragility_check:
            await self._run_fragility_check()
            self._last_fragility_check = now
        if now - self._exposure_interval >= self._last_exposure_check:
            await self._check_portfolio_exposure()
            self._last_exposure_check = now

    async def handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.RISK_CHECK_REQUEST:
            await self._evaluate_trade(msg)
        elif msg.msg_type == MessageType.FILL_REPORT:
            self._record_fill(msg.payload)
        elif msg.msg_type == MessageType.RESUME_TRADING:
            self._manager.reset_daily(msg.payload.get("equity", 0.0))
            self.logger.info("trading_resumed")
        elif msg.msg_type == MessageType.STATUS_REQUEST:
            await self._report_status(msg.sender)

    async def _evaluate_trade(self, msg: Message) -> None:
        self._checks_performed += 1
        signal: Signal | None = msg.payload.get("signal")
        portfolio: PortfolioState | None = msg.payload.get("portfolio")
        current_price: float = msg.payload.get("current_price", 0.0)
        returns_history = msg.payload.get("returns_history")

        if signal is None or portfolio is None:
            await self._reject(msg, "missing signal or portfolio data")
            return

        np_returns = None
        if returns_history is not None:
            np_returns = np.array(returns_history, dtype=np.float64)

        check = self._manager.check_trade(signal, portfolio, current_price, np_returns)

        if check.approved:
            self._approvals += 1
            await self.send_message(
                msg.sender,
                MessageType.RISK_APPROVED,
                {
                    "original_signal": signal,
                    "adjusted_qty": check.adjusted_qty,
                    "cvar": check.cvar,
                    "kelly_size": check.kelly_size,
                    "exposure_pct": check.exposure_pct,
                    "request_id": msg.msg_id,
                },
                Priority.HIGH,
            )
            self.logger.info(
                "trade_approved",
                symbol=signal.symbol,
                qty=check.adjusted_qty,
                reason=check.reason,
            )
        else:
            await self._reject(msg, check.reason, signal=signal)

    async def _reject(
        self, msg: Message, reason: str, signal: Signal | None = None
    ) -> None:
        self._rejections += 1
        await self.send_message(
            msg.sender,
            MessageType.RISK_REJECTED,
            {
                "reason": reason,
                "original_signal": signal,
                "request_id": msg.msg_id,
            },
            Priority.HIGH,
        )
        symbol = signal.symbol if signal else "unknown"
        self.logger.warning("trade_rejected", symbol=symbol, reason=reason)

    async def _run_fragility_check(self) -> None:
        report = self._manager.assess_fragility()
        if report is None:
            return

        self.logger.info(
            "fragility_check",
            state=report.state.value,
            vega=round(report.vega, 4),
            vol_sensitivity=round(report.vol_sensitivity, 4),
        )

        if report.state == FragilityState.FRAGILE:
            self.logger.warning("fragile_strategy_detected", recommendation=report.recommendation)
            await self.send_message(
                "coordinator",
                MessageType.HALT_TRADING,
                {
                    "reason": f"Fragility detected: {report.recommendation}",
                    "source": "risk",
                    "fragility_report": {
                        "state": report.state.value,
                        "vega": report.vega,
                        "vol_sensitivity": report.vol_sensitivity,
                    },
                },
                Priority.CRITICAL,
            )

    async def _check_portfolio_exposure(self) -> None:
        portfolio: PortfolioState | None = self._shared_state.get("portfolio")
        if portfolio is None:
            return

        if portfolio.exposure_pct > self._config.max_total_exposure_pct:
            self.logger.warning(
                "exposure_breach",
                exposure_pct=round(portfolio.exposure_pct, 4),
                limit=self._config.max_total_exposure_pct,
            )
            await self.send_message(
                "coordinator",
                MessageType.HALT_TRADING,
                {
                    "reason": f"Exposure breach: {portfolio.exposure_pct:.2%} > {self._config.max_total_exposure_pct:.2%}",
                    "source": "risk",
                },
                Priority.CRITICAL,
            )

        self._update_correlations(portfolio)

    def _update_correlations(self, portfolio: PortfolioState) -> None:
        """Track pairwise position concentration risk."""
        symbols = list(portfolio.positions.keys())
        if len(symbols) < 2:
            self._position_correlations.clear()
            return

        for i, s1 in enumerate(symbols):
            for s2 in symbols[i + 1:]:
                p1 = portfolio.positions[s1]
                p2 = portfolio.positions[s2]
                total = portfolio.total_exposure
                if total > 0:
                    concentration = (abs(p1.market_value) + abs(p2.market_value)) / total
                    self._position_correlations[(s1, s2)] = concentration

    def _record_fill(self, payload: dict[str, Any]) -> None:
        pnl = payload.get("pnl", 0.0)
        market_return = payload.get("market_return", 0.0)
        self._manager.update_pnl(pnl, market_return)

    async def _report_status(self, requester: str) -> None:
        await self.send_message(
            requester,
            MessageType.STATUS_RESPONSE,
            {
                "agent": self.name,
                "checks_performed": self._checks_performed,
                "approvals": self._approvals,
                "rejections": self._rejections,
                "is_halted": self._manager.is_halted,
                "daily_pnl": self._manager.daily_pnl,
                "top_concentrations": dict(
                    sorted(
                        self._position_correlations.items(),
                        key=lambda x: x[1],
                        reverse=True,
                    )[:5]
                ),
            },
        )

    @property
    def rejection_rate(self) -> float:
        if self._checks_performed == 0:
            return 0.0
        return self._rejections / self._checks_performed
