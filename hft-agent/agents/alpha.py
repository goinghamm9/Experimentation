"""Alpha agent -- wraps SignalAggregator, generates composite trading signals."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

from core.signals.aggregator import SignalAggregator
from utils.config import SignalsConfig
from utils.types import OrderBook, Signal, Tick

from .base import BaseAgent, Message, MessageType, Priority


class AlphaAgent(BaseAgent):
    """Processes market data and emits trade signals."""

    def __init__(
        self,
        config: SignalsConfig,
        min_signal_strength: float = 0.6,
        signal_history_size: int = 500,
    ):
        super().__init__("alpha")
        self._aggregator = SignalAggregator(config)
        self._min_strength = min_signal_strength
        self._signal_history: deque[dict[str, Any]] = deque(maxlen=signal_history_size)
        self._signals_emitted = 0
        self._correct_predictions = 0

    async def handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.TICK_DATA:
            await self._process_tick(msg.payload)
        elif msg.msg_type == MessageType.ORDERBOOK_DATA:
            await self._process_orderbook(msg.payload)
        elif msg.msg_type == MessageType.FILL_REPORT:
            self._record_fill(msg.payload)
        elif msg.msg_type == MessageType.STATUS_REQUEST:
            await self._report_status(msg.sender)

    async def _process_tick(self, payload: dict[str, Any]) -> None:
        tick: Tick | None = payload.get("tick")
        if tick is None:
            return

        self._aggregator.process_trade(
            symbol=tick.symbol,
            price=tick.price,
            volume=tick.size,
            timestamp=tick.timestamp,
        )
        await self._try_emit_signal(tick.symbol)

    async def _process_orderbook(self, payload: dict[str, Any]) -> None:
        book: OrderBook | None = payload.get("book")
        if book is None:
            return

        self._aggregator.process_orderbook(book)
        await self._try_emit_signal(book.symbol)

    async def _try_emit_signal(self, symbol: str) -> None:
        signal = self._aggregator.get_composite_signal(symbol)
        if signal is None or signal.strength < self._min_strength:
            return

        regime = self._aggregator.get_regime(symbol)
        is_toxic = self._aggregator.is_toxic(symbol)
        if is_toxic:
            self.logger.debug("toxic_flow_skip", symbol=symbol)
            return

        self._signals_emitted += 1
        self._signal_history.append({
            "symbol": symbol,
            "direction": signal.direction.value if signal.direction else None,
            "strength": signal.strength,
            "regime": regime.value,
            "ts": time.time(),
            "outcome": None,
        })

        await self.send_message(
            "coordinator",
            MessageType.TRADE_SIGNAL,
            {
                "signal": signal,
                "regime": regime.value,
                "is_toxic": is_toxic,
            },
            Priority.HIGH,
        )
        self.logger.info(
            "signal_emitted",
            symbol=symbol,
            direction=signal.direction.value if signal.direction else None,
            strength=round(signal.strength, 4),
            regime=regime.value,
        )

    def _record_fill(self, payload: dict[str, Any]) -> None:
        """Track fill outcomes to measure signal accuracy."""
        symbol = payload.get("symbol")
        fill_side = payload.get("side")
        if not symbol or not fill_side:
            return

        for entry in reversed(self._signal_history):
            if entry["symbol"] == symbol and entry["outcome"] is None:
                entry["outcome"] = fill_side
                if entry["direction"] == fill_side:
                    self._correct_predictions += 1
                break

    async def _report_status(self, requester: str) -> None:
        accuracy = (
            self._correct_predictions / self._signals_emitted
            if self._signals_emitted > 0
            else 0.0
        )
        await self.send_message(
            requester,
            MessageType.STATUS_RESPONSE,
            {
                "agent": self.name,
                "signals_emitted": self._signals_emitted,
                "accuracy": round(accuracy, 4),
                "history_size": len(self._signal_history),
            },
        )

    @property
    def signal_accuracy(self) -> float:
        if self._signals_emitted == 0:
            return 0.0
        return self._correct_predictions / self._signals_emitted
