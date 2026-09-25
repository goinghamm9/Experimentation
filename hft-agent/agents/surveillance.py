"""Surveillance agent -- monitors market conditions and system health."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

from utils.types import Regime, Tick

from .base import BaseAgent, Message, MessageType, Priority


class SurveillanceAgent(BaseAgent):
    """Continuously monitors market-wide conditions and agent system health.

    Can independently halt trading on detecting anomalies or regime shifts.
    """

    def __init__(
        self,
        volume_spike_threshold: float = 3.0,
        price_crash_threshold_pct: float = 0.05,
        latency_threshold_ms: float = 500.0,
        error_rate_threshold: float = 0.1,
        check_interval: float = 2.0,
        history_window: int = 1000,
    ):
        super().__init__("surveillance")
        self._vol_spike_thresh = volume_spike_threshold
        self._crash_thresh = price_crash_threshold_pct
        self._latency_thresh_ms = latency_threshold_ms
        self._error_rate_thresh = error_rate_threshold
        self._check_interval = check_interval

        self._tick_history: dict[str, deque[Tick]] = {}
        self._volume_history: dict[str, deque[float]] = {}
        self._message_latencies: deque[float] = deque(maxlen=history_window)
        self._error_counts: dict[str, int] = {}
        self._message_counts: dict[str, int] = {}
        self._fill_slippages: deque[float] = deque(maxlen=history_window)
        self._current_regime: dict[str, Regime] = {}
        self._last_system_check = 0.0
        self._halted = False

    async def handle_message(self, msg: Message) -> None:
        delivery_latency_ms = (time.time() - msg.timestamp) * 1000
        self._message_latencies.append(delivery_latency_ms)
        self._message_counts[msg.sender] = self._message_counts.get(msg.sender, 0) + 1

        if msg.msg_type == MessageType.TICK_DATA:
            await self._process_tick(msg.payload)
        elif msg.msg_type == MessageType.FILL_REPORT:
            self._record_fill_quality(msg.payload)
        elif msg.msg_type == MessageType.HEARTBEAT:
            self._check_agent_health(msg.payload)
        elif msg.msg_type == MessageType.STATUS_REQUEST:
            await self._report_status(msg.sender)

    async def on_idle(self) -> None:
        now = time.time()
        if now - self._last_system_check >= self._check_interval:
            await self._run_system_checks()
            self._last_system_check = now

    async def _process_tick(self, payload: dict[str, Any]) -> None:
        tick: Tick | None = payload.get("tick")
        if tick is None:
            return

        symbol = tick.symbol
        if symbol not in self._tick_history:
            self._tick_history[symbol] = deque(maxlen=500)
            self._volume_history[symbol] = deque(maxlen=200)

        self._tick_history[symbol].append(tick)
        self._volume_history[symbol].append(tick.size)

        await self._check_flash_crash(symbol)
        await self._check_volume_anomaly(symbol)

    async def _check_flash_crash(self, symbol: str) -> None:
        history = self._tick_history[symbol]
        if len(history) < 20:
            return

        recent_prices = [t.price for t in list(history)[-20:]]
        high = max(recent_prices)
        low = min(recent_prices)
        if high <= 0:
            return

        drop_pct = (high - low) / high
        if drop_pct >= self._crash_thresh:
            self.logger.warning(
                "flash_crash_detected",
                symbol=symbol,
                drop_pct=round(drop_pct, 4),
                high=high,
                low=low,
            )
            if not self._halted:
                self._halted = True
                await self.send_message(
                    "coordinator",
                    MessageType.HALT_TRADING,
                    {
                        "reason": f"Flash crash detected in {symbol}: {drop_pct:.2%} drop",
                        "source": "surveillance",
                        "symbol": symbol,
                    },
                    Priority.CRITICAL,
                )

    async def _check_volume_anomaly(self, symbol: str) -> None:
        volumes = self._volume_history[symbol]
        if len(volumes) < 50:
            return

        vol_list = list(volumes)
        baseline = vol_list[:-10]
        recent = vol_list[-10:]

        avg_baseline = sum(baseline) / len(baseline) if baseline else 1.0
        avg_recent = sum(recent) / len(recent) if recent else 0.0

        if avg_baseline > 0 and avg_recent / avg_baseline >= self._vol_spike_thresh:
            self.logger.warning(
                "volume_spike",
                symbol=symbol,
                ratio=round(avg_recent / avg_baseline, 2),
            )

            old_regime = self._current_regime.get(symbol, Regime.RANDOM_WALK)
            new_regime = Regime.TOXIC
            if old_regime != new_regime:
                self._current_regime[symbol] = new_regime
                await self.send_message(
                    "coordinator",
                    MessageType.REGIME_CHANGE,
                    {
                        "symbol": symbol,
                        "old_regime": old_regime.value,
                        "new_regime": new_regime.value,
                        "reason": "volume_spike",
                    },
                    Priority.HIGH,
                )

    def _record_fill_quality(self, payload: dict[str, Any]) -> None:
        slippage = payload.get("slippage", 0.0)
        self._fill_slippages.append(slippage)

    def _check_agent_health(self, payload: dict[str, Any]) -> None:
        agent_name = payload.get("agent", "unknown")
        state = payload.get("state", "unknown")
        if state == "error":
            self._error_counts[agent_name] = self._error_counts.get(agent_name, 0) + 1
            self.logger.warning("agent_in_error_state", agent=agent_name)

    async def _run_system_checks(self) -> None:
        if self._message_latencies:
            avg_latency = sum(self._message_latencies) / len(self._message_latencies)
            if avg_latency > self._latency_thresh_ms:
                self.logger.warning("high_system_latency", avg_latency_ms=round(avg_latency, 2))

        total_messages = sum(self._message_counts.values())
        total_errors = sum(self._error_counts.values())
        if total_messages > 0 and total_errors / max(total_messages, 1) > self._error_rate_thresh:
            self.logger.warning(
                "high_error_rate",
                error_rate=round(total_errors / total_messages, 4),
            )
            if not self._halted:
                self._halted = True
                await self.send_message(
                    "coordinator",
                    MessageType.HALT_TRADING,
                    {
                        "reason": "System error rate exceeded threshold",
                        "source": "surveillance",
                    },
                    Priority.CRITICAL,
                )

    async def _report_status(self, requester: str) -> None:
        avg_latency = (
            sum(self._message_latencies) / len(self._message_latencies)
            if self._message_latencies
            else 0.0
        )
        avg_slippage = (
            sum(self._fill_slippages) / len(self._fill_slippages)
            if self._fill_slippages
            else 0.0
        )
        await self.send_message(
            requester,
            MessageType.STATUS_RESPONSE,
            {
                "agent": self.name,
                "avg_latency_ms": round(avg_latency, 2),
                "avg_fill_slippage": round(avg_slippage, 8),
                "error_counts": dict(self._error_counts),
                "regimes": {s: r.value for s, r in self._current_regime.items()},
                "halted": self._halted,
            },
        )

    def reset_halt(self) -> None:
        self._halted = False
