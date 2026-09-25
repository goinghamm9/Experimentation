"""Base agent with async lifecycle, message bus, and state management."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from utils.logging import get_logger


class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    HALTED = "halted"


class Priority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class MessageType(Enum):
    TICK_DATA = "tick_data"
    ORDERBOOK_DATA = "orderbook_data"
    TRADE_SIGNAL = "trade_signal"
    RISK_CHECK_REQUEST = "risk_check_request"
    RISK_APPROVED = "risk_approved"
    RISK_REJECTED = "risk_rejected"
    EXECUTE_ORDER = "execute_order"
    FILL_REPORT = "fill_report"
    HALT_TRADING = "halt_trading"
    RESUME_TRADING = "resume_trading"
    REGIME_CHANGE = "regime_change"
    REBALANCE_ORDER = "rebalance_order"
    HEARTBEAT = "heartbeat"
    STATUS_REQUEST = "status_request"
    STATUS_RESPONSE = "status_response"


@dataclass(order=True)
class Message:
    """Structured message for inter-agent communication.

    Ordered by priority (lower value = higher priority) then timestamp
    so asyncio.PriorityQueue dequeues critical messages first.
    """
    priority: int = field(compare=True)
    timestamp: float = field(compare=True)
    sender: str = field(compare=False)
    recipient: str = field(compare=False)
    msg_type: MessageType = field(compare=False)
    payload: dict[str, Any] = field(compare=False, default_factory=dict)
    msg_id: str = field(compare=False, default_factory=lambda: uuid.uuid4().hex[:12])


def make_message(
    sender: str,
    recipient: str,
    msg_type: MessageType,
    payload: dict[str, Any] | None = None,
    priority: Priority = Priority.NORMAL,
) -> Message:
    return Message(
        priority=priority.value,
        timestamp=time.time(),
        sender=sender,
        recipient=recipient,
        msg_type=msg_type,
        payload=payload or {},
    )


class BaseAgent:
    """Base class for all agents in the multi-agent system."""

    def __init__(self, name: str, inbox_size: int = 1000):
        self.name = name
        self.state = AgentState.IDLE
        self._inbox: asyncio.PriorityQueue[Message] = asyncio.PriorityQueue(maxsize=inbox_size)
        self._outbox: asyncio.Queue[Message] | None = None
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_heartbeat = 0.0
        self._heartbeat_interval = 5.0
        self._shared_state: dict[str, Any] = {}
        self.logger = get_logger(f"agent.{name}")

    def bind_outbox(self, outbox: asyncio.Queue[Message]) -> None:
        """Bind to the coordinator's central message queue."""
        self._outbox = outbox

    def set_shared_state(self, state: dict[str, Any]) -> None:
        """Reference to the coordinator's shared state store."""
        self._shared_state = state

    async def receive_message(self, msg: Message) -> None:
        """Enqueue a message into this agent's inbox."""
        try:
            self._inbox.put_nowait(msg)
        except asyncio.QueueFull:
            self.logger.warning("inbox_full", dropped_msg_type=msg.msg_type.value)

    async def send_message(
        self,
        recipient: str,
        msg_type: MessageType,
        payload: dict[str, Any] | None = None,
        priority: Priority = Priority.NORMAL,
    ) -> None:
        """Send a message via the coordinator's central queue."""
        if self._outbox is None:
            self.logger.error("outbox_not_bound")
            return
        msg = make_message(self.name, recipient, msg_type, payload, priority)
        await self._outbox.put(msg)

    async def start(self) -> None:
        """Start this agent's processing loop as an asyncio task."""
        if self._running:
            return
        self._running = True
        self.state = AgentState.RUNNING
        self._task = asyncio.create_task(self._run_loop(), name=f"agent-{self.name}")
        self.logger.info("agent_started")

    async def stop(self) -> None:
        """Gracefully stop the agent."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.state = AgentState.IDLE
        self.logger.info("agent_stopped")

    async def _run_loop(self) -> None:
        try:
            await self.on_start()
            while self._running:
                now = time.time()
                if now - self._last_heartbeat >= self._heartbeat_interval:
                    await self._emit_heartbeat()
                    self._last_heartbeat = now

                try:
                    msg = await asyncio.wait_for(self._inbox.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    await self.on_idle()
                    continue

                try:
                    await self.handle_message(msg)
                except Exception:
                    self.logger.exception("message_handler_error", msg_type=msg.msg_type.value)
                    self.state = AgentState.ERROR
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger.exception("agent_loop_crash")
            self.state = AgentState.ERROR
        finally:
            await self.on_stop()

    async def _emit_heartbeat(self) -> None:
        await self.send_message(
            "coordinator",
            MessageType.HEARTBEAT,
            {"agent": self.name, "state": self.state.value, "ts": time.time()},
            Priority.LOW,
        )

    # -- Override points --

    async def on_start(self) -> None:
        """Called once when the agent starts."""

    async def on_stop(self) -> None:
        """Called once when the agent stops."""

    async def on_idle(self) -> None:
        """Called when no message is available."""

    async def handle_message(self, msg: Message) -> None:
        """Process a single message. Subclasses must implement."""
        raise NotImplementedError
