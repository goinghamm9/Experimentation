"""Execution agent -- smart order routing, TWAP, and fill tracking."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

from brokers.base import Broker
from execution.engine import ExecutionEngine
from utils.config import ExecutionConfig
from utils.types import Order, OrderStatus, OrderType, Side

from .base import BaseAgent, Message, MessageType, Priority


@dataclass
class FillRecord:
    symbol: str
    side: str
    qty: float
    expected_price: float
    filled_price: float
    slippage: float
    ts: float


class ExecutionAgent(BaseAgent):
    """Routes and executes orders across brokers."""

    def __init__(
        self,
        brokers: list[Broker],
        config: ExecutionConfig,
        twap_slice_count: int = 10,
        twap_interval_s: float = 1.0,
        fill_history_size: int = 2000,
    ):
        super().__init__("execution")
        self._brokers = {b.name: b for b in brokers}
        self._engines: dict[str, ExecutionEngine] = {}
        for b in brokers:
            self._engines[b.name] = ExecutionEngine(b, config)
        self._primary_broker = brokers[0].name if brokers else ""
        self._config = config
        self._twap_slices = twap_slice_count
        self._twap_interval = twap_interval_s
        self._fill_history: deque[FillRecord] = deque(maxlen=fill_history_size)
        self._pending_twap_tasks: dict[str, asyncio.Task] = {}
        self._total_orders = 0
        self._total_fills = 0
        self._total_slippage = 0.0

    async def on_start(self) -> None:
        for name, broker in self._brokers.items():
            if not broker.is_connected:
                try:
                    await broker.connect()
                    self.logger.info("broker_connected", broker=name)
                except Exception:
                    self.logger.exception("broker_connect_failed", broker=name)

    async def on_stop(self) -> None:
        for task in self._pending_twap_tasks.values():
            task.cancel()
        self._pending_twap_tasks.clear()

        for name, engine in self._engines.items():
            try:
                cancelled = await engine.cancel_all()
                self.logger.info("orders_cancelled_on_stop", broker=name, count=cancelled)
            except Exception:
                self.logger.exception("cancel_all_failed", broker=name)

    async def handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.EXECUTE_ORDER:
            await self._execute_order(msg.payload)
        elif msg.msg_type == MessageType.HALT_TRADING:
            await self._cancel_everything()
        elif msg.msg_type == MessageType.STATUS_REQUEST:
            await self._report_status(msg.sender)

    async def _execute_order(self, payload: dict[str, Any]) -> None:
        order: Order | None = payload.get("order")
        use_twap: bool = payload.get("use_twap", False)
        broker_name: str = payload.get("broker", self._primary_broker)

        if order is None:
            self.logger.warning("execute_order_missing_order")
            return

        broker_name = self._select_broker(order, broker_name)
        engine = self._engines.get(broker_name)
        if engine is None:
            self.logger.error("no_engine_for_broker", broker=broker_name)
            return

        self._total_orders += 1

        if use_twap and order.qty > 100:
            task = asyncio.create_task(
                self._execute_twap(engine, order, broker_name),
                name=f"twap-{order.symbol}-{time.time():.0f}",
            )
            task_key = f"{order.symbol}_{time.time()}"
            self._pending_twap_tasks[task_key] = task
            task.add_done_callback(lambda t, k=task_key: self._pending_twap_tasks.pop(k, None))
        else:
            await self._execute_single(engine, order, broker_name)

    def _select_broker(self, order: Order, preferred: str) -> str:
        """Route to connected broker, preferring the requested one."""
        if preferred in self._brokers and self._brokers[preferred].is_connected:
            return preferred
        for name, broker in self._brokers.items():
            if broker.is_connected:
                return name
        return preferred

    async def _execute_single(
        self, engine: ExecutionEngine, order: Order, broker_name: str
    ) -> None:
        expected_price = order.limit_price or 0.0
        result = await engine.execute(order)

        if result.status in (OrderStatus.FILLED, OrderStatus.SUBMITTED, OrderStatus.PENDING):
            filled_price = result.filled_price or expected_price
            slippage = abs(filled_price - expected_price) if expected_price > 0 else 0.0
            self._total_fills += 1
            self._total_slippage += slippage

            record = FillRecord(
                symbol=result.symbol,
                side=result.side.value,
                qty=result.filled_qty or result.qty,
                expected_price=expected_price,
                filled_price=filled_price,
                slippage=slippage,
                ts=time.time(),
            )
            self._fill_history.append(record)

            await self.send_message(
                "coordinator",
                MessageType.FILL_REPORT,
                {
                    "order": result,
                    "symbol": result.symbol,
                    "side": result.side.value,
                    "qty": result.filled_qty or result.qty,
                    "filled_price": filled_price,
                    "slippage": slippage,
                    "broker": broker_name,
                },
                Priority.HIGH,
            )
            self.logger.info(
                "order_filled",
                symbol=result.symbol,
                side=result.side.value,
                qty=result.qty,
                slippage=round(slippage, 6),
                broker=broker_name,
            )
        else:
            self.logger.warning(
                "order_not_filled",
                symbol=result.symbol,
                status=result.status.value,
                broker=broker_name,
            )

    async def _execute_twap(
        self, engine: ExecutionEngine, order: Order, broker_name: str
    ) -> None:
        """Split a large order into time-weighted slices."""
        total_qty = order.qty
        slice_qty = max(1.0, total_qty / self._twap_slices)
        remaining = total_qty

        self.logger.info(
            "twap_started",
            symbol=order.symbol,
            total_qty=total_qty,
            slices=self._twap_slices,
        )

        for i in range(self._twap_slices):
            if remaining <= 0:
                break

            qty = min(slice_qty, remaining)
            child = Order(
                symbol=order.symbol,
                side=order.side,
                qty=qty,
                order_type=order.order_type,
                limit_price=order.limit_price,
            )

            await self._execute_single(engine, child, broker_name)
            remaining -= qty

            if i < self._twap_slices - 1 and remaining > 0:
                await asyncio.sleep(self._twap_interval)

        self.logger.info("twap_completed", symbol=order.symbol, filled=total_qty - remaining)

    async def _cancel_everything(self) -> None:
        for task in self._pending_twap_tasks.values():
            task.cancel()
        self._pending_twap_tasks.clear()

        for name, engine in self._engines.items():
            try:
                await engine.cancel_all()
            except Exception:
                self.logger.exception("cancel_all_failed", broker=name)
        self.logger.info("all_orders_cancelled")

    async def _report_status(self, requester: str) -> None:
        avg_slippage = self._total_slippage / self._total_fills if self._total_fills > 0 else 0.0
        await self.send_message(
            requester,
            MessageType.STATUS_RESPONSE,
            {
                "agent": self.name,
                "total_orders": self._total_orders,
                "total_fills": self._total_fills,
                "avg_slippage": round(avg_slippage, 8),
                "pending_twap": len(self._pending_twap_tasks),
                "connected_brokers": [
                    n for n, b in self._brokers.items() if b.is_connected
                ],
            },
        )

    @property
    def avg_slippage(self) -> float:
        if self._total_fills == 0:
            return 0.0
        return self._total_slippage / self._total_fills
