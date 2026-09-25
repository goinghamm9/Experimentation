"""
Adaptive Microstructure Strategy.

This is the main trading strategy implementing the research framework:

1. REGIME DETECTION (Hurst + Multifractal):
   - Trending: Follow OFI direction (momentum)
   - Mean-reverting: Fade OFI direction (contrarian)
   - Random walk: Spread capture only (market making)
   - Toxic: Step aside (VPIN filter)

2. SIGNAL (Order Flow Imbalance):
   - Primary alpha signal: OFI from order book
   - Captures endogenous order-flow dynamics
   - R² ~65% for short-term price changes (Cont et al. 2011)

3. POSITION SIZING (Fractional Kelly):
   - Log-wealth maximization (ergodically correct)
   - Fat-tail adjusted dispersion (MAD, not std)
   - 0.25x Kelly to protect against parameter uncertainty

4. RISK MANAGEMENT:
   - CVaR limits (fat-tailed, not Gaussian)
   - Daily loss limits, max drawdown stops
   - Fragility monitoring (detect if strategy becomes short-gamma)

5. EXECUTION:
   - Prefer limit orders for spread capture
   - Power-law slippage model
   - Rate limiting to avoid broker throttling
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from core.risk.manager import RiskCheck, RiskManager
from core.signals.aggregator import SignalAggregator
from utils.config import StrategyConfig
from utils.logging import get_logger
from utils.types import (
    Order,
    OrderBook,
    OrderType,
    PortfolioState,
    Regime,
    Side,
    Signal,
    Tick,
)

logger = get_logger(__name__)


@dataclass
class TradeDecision:
    """Output of the strategy's decision process."""
    should_trade: bool
    order: Order | None = None
    signal: Signal | None = None
    risk_check: RiskCheck | None = None
    reason: str = ""


class AdaptiveMicrostructureStrategy:
    """Regime-adaptive HFT strategy based on microstructure signals.

    Switches between momentum, mean-reversion, and market-making
    depending on the detected regime (Hurst exponent) and order
    flow toxicity (VPIN).
    """

    def __init__(
        self,
        config: StrategyConfig,
        signal_aggregator: SignalAggregator,
        risk_manager: RiskManager,
    ):
        self._config = config
        self._signals = signal_aggregator
        self._risk = risk_manager
        self._returns_cache: dict[str, list[float]] = {}
        self._last_prices: dict[str, float] = {}

    def on_tick(self, tick: Tick, portfolio: PortfolioState) -> TradeDecision:
        """Process a tick and decide whether to trade.

        This is the main tick-level decision function called on every
        market data update.
        """
        symbol = tick.symbol
        price = tick.price

        # Track returns for risk calculations
        if symbol in self._last_prices:
            ret = np.log(price / self._last_prices[symbol])
            if symbol not in self._returns_cache:
                self._returns_cache[symbol] = []
            self._returns_cache[symbol].append(ret)
            # Keep last 5000 returns
            if len(self._returns_cache[symbol]) > 5000:
                self._returns_cache[symbol] = self._returns_cache[symbol][-5000:]
        self._last_prices[symbol] = price

        # Process trade through signal generators
        signals = self._signals.process_trade(symbol, price, tick.size, tick.timestamp)

        # Get composite signal
        composite = self._signals.get_composite_signal(symbol)
        if composite is None:
            return TradeDecision(should_trade=False, reason="No composite signal")

        # Check signal strength
        if composite.strength < self._config.min_signal_strength:
            return TradeDecision(
                should_trade=False,
                signal=composite,
                reason=f"Signal too weak: {composite.strength:.3f} < {self._config.min_signal_strength}",
            )

        # Check toxicity
        if self._signals.is_toxic(symbol):
            return TradeDecision(
                should_trade=False,
                signal=composite,
                reason="Order flow is toxic (high VPIN) - stepping aside",
            )

        # Direction
        if composite.direction is None:
            return TradeDecision(
                should_trade=False,
                signal=composite,
                reason="No clear direction",
            )

        # Risk check
        returns_arr = None
        if symbol in self._returns_cache and len(self._returns_cache[symbol]) > 20:
            returns_arr = np.array(self._returns_cache[symbol])

        risk_check = self._risk.check_trade(
            signal=composite,
            portfolio=portfolio,
            current_price=price,
            returns_history=returns_arr,
        )

        if not risk_check.approved:
            return TradeDecision(
                should_trade=False,
                signal=composite,
                risk_check=risk_check,
                reason=f"Risk rejected: {risk_check.reason}",
            )

        # Build order
        order_type = OrderType.LIMIT if self._config.prefer_limit_orders else OrderType.MARKET
        limit_price = None

        if order_type == OrderType.LIMIT:
            # For limit orders, place at a favorable price
            # BUY: bid at mid - half spread; SELL: ask at mid + half spread
            tick_size = 0.01  # Standard equity tick
            if composite.direction == Side.BUY:
                limit_price = round(price - tick_size, 2)
            else:
                limit_price = round(price + tick_size, 2)

        order = Order(
            symbol=symbol,
            side=composite.direction,
            qty=risk_check.adjusted_qty,
            order_type=order_type,
            limit_price=limit_price,
        )

        regime = self._signals.get_regime(symbol)
        logger.info(
            "trade_decision",
            symbol=symbol,
            side=composite.direction.value,
            qty=risk_check.adjusted_qty,
            regime=regime.value,
            signal_strength=composite.strength,
            kelly_size=risk_check.kelly_size,
        )

        return TradeDecision(
            should_trade=True,
            order=order,
            signal=composite,
            risk_check=risk_check,
            reason=f"Signal: {composite.strength:.3f}, Regime: {regime.value}",
        )

    def on_orderbook(self, book: OrderBook, portfolio: PortfolioState) -> TradeDecision:
        """Process an order book update.

        Order book updates feed the OFI signal, which is the primary
        alpha driver.
        """
        # Update OFI signal
        signals = self._signals.process_orderbook(book)

        # Only trade on OFI updates if we have enough signal strength
        composite = self._signals.get_composite_signal(book.symbol)
        if composite is None or composite.strength < self._config.min_signal_strength:
            return TradeDecision(should_trade=False, reason="Insufficient OFI signal")

        # Check spread is wide enough for profit
        if book.spread_bps is not None and book.spread_bps < self._config.min_spread_bps:
            return TradeDecision(
                should_trade=False,
                signal=composite,
                reason=f"Spread too tight: {book.spread_bps:.1f} bps",
            )

        mid = book.mid_price
        if mid is None:
            return TradeDecision(should_trade=False, reason="No mid price")

        # Delegate to tick handler with mid price as reference
        tick = Tick(
            symbol=book.symbol,
            timestamp=book.timestamp,
            price=mid,
            size=0,
        )
        return self.on_tick(tick, portfolio)
