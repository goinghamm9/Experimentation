"""Coordinator agent -- orchestrates the trading pipeline and agent lifecycle."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from utils.logging import get_logger
from utils.types import (
    Order,
    OrderType,
    PortfolioState,
    Signal,
    Side,
)

from .base import (
    AgentState,
    BaseAgent,
    Message,
    MessageType,
    Priority,
    make_message,
)

logger = get_logger("coordinator")

# Agents that can independently halt trading -- coordinator respects these unconditionally
_VETO_AGENTS = frozenset({"risk", "surveillance"})

_HEARTBEAT_TIMEOUT = 15.0
_MAX_RESTARTS = 3


class Coordinator:
    """Orchestrates all child agents and the trading pipeline.

    Trading flow: Data -> Alpha -> Risk (veto gate) -> Execution
    Risk agent has HARD VETO -- this is enforced architecturally:
    the coordinator never routes to execution without risk approval.
    """

    def __init__(self, agents: list[BaseAgent]):
        self._agents: dict[str, BaseAgent] = {a.name: a for a in agents}
        self._central_queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=10_000)
        self._shared_state: dict[str, Any] = {}
        self._running = False
        self._halted = False
        self._halt_reason = ""
        self._router_task: asyncio.Task | None = None

        self._last_heartbeat: dict[str, float] = {}
        self._restart_counts: dict[str, int] = {}
        self._pending_risk_checks: dict[str, Message] = {}
        self._market_open = False

        for agent in self._agents.values():
            agent.bind_outbox(self._central_queue)
            agent.set_shared_state(self._shared_state)

    # -- Lifecycle --

    async def start(self) -> None:
        self._running = True
        self._halted = False

        for agent in self._agents.values():
            await agent.start()
            self._last_heartbeat[agent.name] = time.time()

        self._router_task = asyncio.create_task(
            self._message_loop(), name="coordinator-router"
        )
        self._health_task = asyncio.create_task(
            self._health_monitor_loop(), name="coordinator-health"
        )
        logger.info("coordinator_started", agents=list(self._agents.keys()))

    async def stop(self) -> None:
        self._running = False
        for agent in self._agents.values():
            await agent.stop()

        if self._router_task and not self._router_task.done():
            self._router_task.cancel()
            try:
                await self._router_task
            except asyncio.CancelledError:
                pass

        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        logger.info("coordinator_stopped")

    # -- Market transitions --

    async def on_market_open(self, portfolio: PortfolioState) -> None:
        self._market_open = True
        self._halted = False
        self._halt_reason = ""
        self._shared_state["portfolio"] = portfolio

        for agent in self._agents.values():
            await agent.receive_message(
                make_message(
                    "coordinator", agent.name, MessageType.RESUME_TRADING,
                    {"equity": portfolio.total_equity},
                    Priority.HIGH,
                )
            )
        logger.info("market_open", equity=portfolio.total_equity)

    async def on_market_close(self) -> None:
        self._market_open = False
        logger.info("market_close")

    # -- Inject external data --

    async def inject(self, msg: Message) -> None:
        """Inject an external message (tick, orderbook) into the system."""
        await self._central_queue.put(msg)

    def update_portfolio(self, portfolio: PortfolioState) -> None:
        self._shared_state["portfolio"] = portfolio

    @property
    def shared_state(self) -> dict[str, Any]:
        return self._shared_state

    @property
    def is_halted(self) -> bool:
        return self._halted

    # -- Core message loop --

    async def _message_loop(self) -> None:
        try:
            while self._running:
                try:
                    msg = await asyncio.wait_for(self._central_queue.get(), timeout=0.05)
                except asyncio.TimeoutError:
                    continue

                await self._route_message(msg)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("message_loop_crash")

    async def _route_message(self, msg: Message) -> None:
        mt = msg.msg_type

        if mt == MessageType.HEARTBEAT:
            self._last_heartbeat[msg.sender] = time.time()
            if "surveillance" in self._agents:
                await self._agents["surveillance"].receive_message(msg)
            return

        if mt == MessageType.HALT_TRADING:
            await self._handle_halt(msg)
            return

        if mt == MessageType.RESUME_TRADING:
            await self._handle_resume(msg)
            return

        if mt == MessageType.TRADE_SIGNAL:
            await self._handle_trade_signal(msg)
            return

        if mt == MessageType.RISK_APPROVED:
            await self._handle_risk_approved(msg)
            return

        if mt == MessageType.RISK_REJECTED:
            await self._handle_risk_rejected(msg)
            return

        if mt == MessageType.FILL_REPORT:
            await self._broadcast(msg, exclude={msg.sender})
            return

        if mt == MessageType.REGIME_CHANGE:
            await self._broadcast(msg)
            return

        if mt == MessageType.REBALANCE_ORDER:
            await self._handle_rebalance(msg)
            return

        # Direct routing for addressed messages
        if msg.recipient and msg.recipient in self._agents:
            await self._agents[msg.recipient].receive_message(msg)
            return

        # Broadcast tick and orderbook data to interested agents
        if mt in (MessageType.TICK_DATA, MessageType.ORDERBOOK_DATA):
            targets = {"alpha", "surveillance", "portfolio"}
            for name in targets:
                if name in self._agents:
                    await self._agents[name].receive_message(msg)
            return

        # Default: route to recipient or drop
        if msg.recipient and msg.recipient in self._agents:
            await self._agents[msg.recipient].receive_message(msg)

    # -- Trading pipeline --

    async def _handle_trade_signal(self, msg: Message) -> None:
        if self._halted:
            logger.debug("signal_dropped_halted", signal=msg.payload.get("signal"))
            return

        if not self._market_open:
            logger.debug("signal_dropped_market_closed")
            return

        signal: Signal | None = msg.payload.get("signal")
        if signal is None:
            return

        portfolio: PortfolioState | None = self._shared_state.get("portfolio")
        if portfolio is None:
            logger.warning("no_portfolio_state")
            return

        current_price = 0.0
        if signal.symbol in portfolio.positions:
            current_price = portfolio.positions[signal.symbol].current_price

        # Route through risk -- this is mandatory, never bypass
        risk_req = make_message(
            "coordinator",
            "risk",
            MessageType.RISK_CHECK_REQUEST,
            {
                "signal": signal,
                "portfolio": portfolio,
                "current_price": current_price,
                "returns_history": self._shared_state.get(f"returns:{signal.symbol}"),
            },
            Priority.HIGH,
        )
        self._pending_risk_checks[risk_req.msg_id] = msg

        if "risk" in self._agents:
            await self._agents["risk"].receive_message(risk_req)
        else:
            logger.error("no_risk_agent_registered")

    async def _handle_risk_approved(self, msg: Message) -> None:
        """Risk approved -- proceed to execution."""
        request_id = msg.payload.get("request_id")
        original = self._pending_risk_checks.pop(request_id, None)

        signal: Signal | None = msg.payload.get("original_signal")
        adjusted_qty = msg.payload.get("adjusted_qty", 0)

        if signal is None or adjusted_qty <= 0:
            return

        order = Order(
            symbol=signal.symbol,
            side=signal.direction or Side.BUY,
            qty=adjusted_qty,
            order_type=OrderType.LIMIT,
            limit_price=self._shared_state.get(f"price:{signal.symbol}"),
        )

        use_twap = adjusted_qty > 500

        exec_msg = make_message(
            "coordinator",
            "execution",
            MessageType.EXECUTE_ORDER,
            {"order": order, "use_twap": use_twap},
            Priority.HIGH,
        )

        if "execution" in self._agents:
            await self._agents["execution"].receive_message(exec_msg)

        logger.info(
            "trade_routed_to_execution",
            symbol=signal.symbol,
            qty=adjusted_qty,
            twap=use_twap,
        )

    async def _handle_risk_rejected(self, msg: Message) -> None:
        """Risk rejected -- trade does NOT proceed. No override possible."""
        request_id = msg.payload.get("request_id")
        self._pending_risk_checks.pop(request_id, None)
        reason = msg.payload.get("reason", "unknown")
        signal = msg.payload.get("original_signal")
        symbol = signal.symbol if signal else "unknown"
        logger.info("trade_vetoed_by_risk", symbol=symbol, reason=reason)

    async def _handle_rebalance(self, msg: Message) -> None:
        """Rebalance orders also go through risk gate."""
        order: Order | None = msg.payload.get("order")
        if order is None:
            return

        if self._halted:
            logger.debug("rebalance_dropped_halted")
            return

        signal = Signal(
            symbol=order.symbol,
            timestamp=datetime.now(timezone.utc),
            name="rebalance",
            value=0.0,
            direction=order.side,
            strength=0.5,
        )

        portfolio: PortfolioState | None = self._shared_state.get("portfolio")
        current_price = self._shared_state.get(f"price:{order.symbol}", 0.0)

        risk_req = make_message(
            "coordinator",
            "risk",
            MessageType.RISK_CHECK_REQUEST,
            {
                "signal": signal,
                "portfolio": portfolio,
                "current_price": current_price,
            },
            Priority.NORMAL,
        )
        self._pending_risk_checks[risk_req.msg_id] = msg

        if "risk" in self._agents:
            await self._agents["risk"].receive_message(risk_req)

    # -- Halt / Resume --

    async def _handle_halt(self, msg: Message) -> None:
        source = msg.payload.get("source", msg.sender)
        reason = msg.payload.get("reason", "unknown")

        # VETO agents (risk, surveillance) can halt unconditionally
        if source in _VETO_AGENTS or msg.sender in _VETO_AGENTS:
            self._halted = True
            self._halt_reason = reason
            logger.warning("trading_halted", source=source, reason=reason)
            await self._broadcast(msg)
        else:
            logger.info("halt_request_from_non_veto_agent", source=source, reason=reason)

    async def _handle_resume(self, msg: Message) -> None:
        self._halted = False
        self._halt_reason = ""
        logger.info("trading_resumed", source=msg.sender)

    # -- Health monitoring --

    async def _health_monitor_loop(self) -> None:
        try:
            while self._running:
                await asyncio.sleep(5.0)
                now = time.time()
                for name, last in self._last_heartbeat.items():
                    if now - last > _HEARTBEAT_TIMEOUT:
                        agent = self._agents.get(name)
                        if agent and agent.state != AgentState.IDLE:
                            logger.warning("agent_heartbeat_timeout", agent=name)
                            await self._restart_agent(name)
        except asyncio.CancelledError:
            raise

    async def _restart_agent(self, name: str) -> None:
        count = self._restart_counts.get(name, 0)
        if count >= _MAX_RESTARTS:
            logger.error("agent_max_restarts_exceeded", agent=name)
            return

        agent = self._agents.get(name)
        if agent is None:
            return

        logger.info("restarting_agent", agent=name, attempt=count + 1)
        try:
            await agent.stop()
        except Exception:
            logger.exception("agent_stop_failed_during_restart", agent=name)

        try:
            await agent.start()
            self._last_heartbeat[name] = time.time()
            self._restart_counts[name] = count + 1
            logger.info("agent_restarted", agent=name)
        except Exception:
            logger.exception("agent_restart_failed", agent=name)

    # -- Utilities --

    async def _broadcast(
        self, msg: Message, exclude: set[str] | None = None
    ) -> None:
        exclude = exclude or set()
        for name, agent in self._agents.items():
            if name not in exclude:
                await agent.receive_message(msg)
