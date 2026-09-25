"""Portfolio agent -- cross-asset allocation, correlation tracking, rebalancing."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

from utils.types import Order, OrderType, PortfolioState, Position, Side

from .base import BaseAgent, Message, MessageType, Priority


class PortfolioAgent(BaseAgent):
    """Manages cross-asset allocation and enforces exposure limits."""

    def __init__(
        self,
        target_weights: dict[str, float] | None = None,
        max_sector_exposure: float = 0.30,
        rebalance_threshold: float = 0.05,
        rebalance_interval: float = 60.0,
        correlation_window: int = 100,
    ):
        super().__init__("portfolio")
        self._target_weights = target_weights or {}
        self._max_sector_exposure = max_sector_exposure
        self._rebalance_threshold = rebalance_threshold
        self._rebalance_interval = rebalance_interval
        self._last_rebalance_check = 0.0

        self._price_history: dict[str, deque[float]] = {}
        self._correlation_window = correlation_window
        self._correlations: dict[tuple[str, str], float] = {}
        self._sector_map: dict[str, str] = {}

    async def on_idle(self) -> None:
        now = time.time()
        if now - self._last_rebalance_check >= self._rebalance_interval:
            await self._check_rebalance()
            self._last_rebalance_check = now

    async def handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.TICK_DATA:
            self._update_prices(msg.payload)
        elif msg.msg_type == MessageType.FILL_REPORT:
            self._on_fill(msg.payload)
        elif msg.msg_type == MessageType.STATUS_REQUEST:
            await self._report_status(msg.sender)

    def set_targets(self, weights: dict[str, float]) -> None:
        self._target_weights = weights

    def set_sector_map(self, mapping: dict[str, str]) -> None:
        self._sector_map = mapping

    def _update_prices(self, payload: dict[str, Any]) -> None:
        tick = payload.get("tick")
        if tick is None:
            return
        symbol = tick.symbol
        if symbol not in self._price_history:
            self._price_history[symbol] = deque(maxlen=self._correlation_window)
        self._price_history[symbol].append(tick.price)
        self._update_correlations()

    def _update_correlations(self) -> None:
        symbols = [s for s, h in self._price_history.items() if len(h) >= 20]
        for i, s1 in enumerate(symbols):
            for s2 in symbols[i + 1:]:
                p1 = list(self._price_history[s1])
                p2 = list(self._price_history[s2])
                n = min(len(p1), len(p2))
                if n < 20:
                    continue
                p1 = p1[-n:]
                p2 = p2[-n:]

                r1 = [p1[j] / p1[j - 1] - 1 for j in range(1, n)]
                r2 = [p2[j] / p2[j - 1] - 1 for j in range(1, n)]
                corr = self._pearson(r1, r2)
                self._correlations[(s1, s2)] = corr

    @staticmethod
    def _pearson(x: list[float], y: list[float]) -> float:
        n = len(x)
        if n < 2:
            return 0.0
        mx = sum(x) / n
        my = sum(y) / n
        cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
        sx = sum((xi - mx) ** 2 for xi in x) ** 0.5
        sy = sum((yi - my) ** 2 for yi in y) ** 0.5
        if sx * sy == 0:
            return 0.0
        return cov / (sx * sy)

    def _on_fill(self, payload: dict[str, Any]) -> None:
        pass

    async def _check_rebalance(self) -> None:
        if not self._target_weights:
            return

        portfolio: PortfolioState | None = self._shared_state.get("portfolio")
        if portfolio is None or portfolio.total_equity <= 0:
            return

        await self._enforce_sector_limits(portfolio)

        current_weights = {}
        for symbol, pos in portfolio.positions.items():
            current_weights[symbol] = abs(pos.market_value) / portfolio.total_equity

        for symbol, target in self._target_weights.items():
            current = current_weights.get(symbol, 0.0)
            drift = current - target

            if abs(drift) < self._rebalance_threshold:
                continue

            # Need to buy more if underweight, sell if overweight
            target_value = target * portfolio.total_equity
            current_value = current * portfolio.total_equity
            delta_value = target_value - current_value

            price = self._get_latest_price(symbol)
            if price <= 0:
                continue

            qty = abs(delta_value / price)
            if qty < 1:
                continue

            side = Side.BUY if delta_value > 0 else Side.SELL
            order = Order(
                symbol=symbol,
                side=side,
                qty=round(qty),
                order_type=OrderType.MARKET,
            )

            self.logger.info(
                "rebalance_order",
                symbol=symbol,
                side=side.value,
                qty=round(qty),
                drift=round(drift, 4),
                target=target,
                current=round(current, 4),
            )

            await self.send_message(
                "coordinator",
                MessageType.REBALANCE_ORDER,
                {
                    "order": order,
                    "reason": f"drift {drift:+.2%} from target {target:.2%}",
                    "current_weight": current,
                    "target_weight": target,
                },
                Priority.NORMAL,
            )

    async def _enforce_sector_limits(self, portfolio: PortfolioState) -> None:
        if not self._sector_map:
            return

        sector_exposure: dict[str, float] = {}
        for symbol, pos in portfolio.positions.items():
            sector = self._sector_map.get(symbol, "other")
            sector_exposure[sector] = sector_exposure.get(sector, 0.0) + abs(pos.market_value)

        for sector, exposure in sector_exposure.items():
            pct = exposure / portfolio.total_equity if portfolio.total_equity > 0 else 0.0
            if pct > self._max_sector_exposure:
                self.logger.warning(
                    "sector_limit_breach",
                    sector=sector,
                    exposure_pct=round(pct, 4),
                    limit=self._max_sector_exposure,
                )

    def _get_latest_price(self, symbol: str) -> float:
        prices = self._price_history.get(symbol)
        if prices:
            return prices[-1]
        portfolio: PortfolioState | None = self._shared_state.get("portfolio")
        if portfolio and symbol in portfolio.positions:
            return portfolio.positions[symbol].current_price
        return 0.0

    async def _report_status(self, requester: str) -> None:
        portfolio: PortfolioState | None = self._shared_state.get("portfolio")
        current_weights = {}
        if portfolio and portfolio.total_equity > 0:
            for symbol, pos in portfolio.positions.items():
                current_weights[symbol] = round(
                    abs(pos.market_value) / portfolio.total_equity, 4
                )

        top_corr = sorted(
            self._correlations.items(), key=lambda x: abs(x[1]), reverse=True
        )[:10]

        await self.send_message(
            requester,
            MessageType.STATUS_RESPONSE,
            {
                "agent": self.name,
                "target_weights": self._target_weights,
                "current_weights": current_weights,
                "correlations": {f"{s1}/{s2}": round(c, 4) for (s1, s2), c in top_corr},
            },
        )

    @property
    def position_correlations(self) -> dict[tuple[str, str], float]:
        return dict(self._correlations)
