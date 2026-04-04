"""
Signal aggregator — combines all signals into a unified trading decision.

Implements the paper's recommended framework:
1. OFI as primary price signal (Cont et al. 2011)
2. Hurst exponent as regime indicator (Qian & Rasheed 2004)
3. VPIN as toxicity filter (Easley et al. 2011)
4. Multifractal width as stability measure (Mandelbrot MMAR)

The aggregator does NOT optimize binary directional accuracy (which is a
category error per Taleb 2020). Instead, it optimizes the expected payoff
distribution by weighting signal strength by the regime context.
"""

from __future__ import annotations

from datetime import datetime

from utils.config import SignalsConfig
from utils.types import OrderBook, Regime, Side, Signal

from .hurst import HurstExponent
from .multifractal import MultifractalAnalyzer
from .ofi import OrderFlowImbalance
from .vpin import VPIN


class SignalAggregator:
    """Aggregates all signal generators into a unified output."""

    def __init__(self, config: SignalsConfig):
        self._config = config

        self._ofi = OrderFlowImbalance(
            lookback=config.ofi.lookback_ticks,
            smoothing_window=config.ofi.smoothing_window,
        ) if config.ofi.enabled else None

        self._hurst = HurstExponent(
            window=config.hurst.window,
            persistence_threshold=config.hurst.regime_threshold_persistence,
            mean_reversion_threshold=config.hurst.regime_threshold_mean_reversion,
        ) if config.hurst.enabled else None

        self._vpin = VPIN(
            bucket_size=config.vpin.bucket_size,
            n_buckets=config.vpin.n_buckets,
            toxicity_threshold=config.vpin.toxicity_threshold,
        ) if config.vpin.enabled else None

        self._multifractal = MultifractalAnalyzer(
            scales=config.multifractal.scales,
        ) if config.multifractal.enabled else None

        self._latest_signals: dict[str, dict[str, Signal]] = {}

    def process_orderbook(self, book: OrderBook) -> dict[str, Signal]:
        """Process an order book update through all relevant signals."""
        symbol = book.symbol
        signals: dict[str, Signal] = {}

        if symbol not in self._latest_signals:
            self._latest_signals[symbol] = {}

        # OFI
        if self._ofi:
            sig = self._ofi.update(book)
            if sig:
                signals["ofi"] = sig
                self._latest_signals[symbol]["ofi"] = sig

        return signals

    def process_trade(
        self,
        symbol: str,
        price: float,
        volume: float,
        timestamp: datetime,
    ) -> dict[str, Signal]:
        """Process a trade through all relevant signals."""
        signals: dict[str, Signal] = {}

        if symbol not in self._latest_signals:
            self._latest_signals[symbol] = {}

        # Hurst exponent
        if self._hurst:
            sig = self._hurst.update(symbol, price, timestamp)
            if sig:
                signals["hurst"] = sig
                self._latest_signals[symbol]["hurst"] = sig

        # VPIN
        if self._vpin:
            sig = self._vpin.update(symbol, price, volume, timestamp)
            if sig:
                signals["vpin"] = sig
                self._latest_signals[symbol]["vpin"] = sig

        # Multifractal
        if self._multifractal:
            sig = self._multifractal.update(symbol, price, timestamp)
            if sig:
                signals["multifractal"] = sig
                self._latest_signals[symbol]["multifractal"] = sig

        return signals

    def get_composite_signal(self, symbol: str) -> Signal | None:
        """Generate a composite trading signal from all available signals.

        Implements the payoff-mapping framework (Taleb 2020):
        - Don't optimize direction accuracy
        - Weight by regime context and expected payoff magnitude
        """
        if symbol not in self._latest_signals:
            return None

        sigs = self._latest_signals[symbol]
        if not sigs:
            return None

        # Check VPIN toxicity first — if toxic, reduce or eliminate signal
        toxicity_discount = 1.0
        if "vpin" in sigs:
            vpin_sig = sigs["vpin"]
            if vpin_sig.metadata.get("is_toxic", False):
                toxicity_discount = 0.2  # Heavily discount in toxic flow

        # Get regime from Hurst
        regime = Regime.RANDOM_WALK
        regime_weight = 0.5  # Base weight for random walk
        if "hurst" in sigs:
            hurst_sig = sigs["hurst"]
            regime = Regime(hurst_sig.metadata.get("regime", "random_walk"))
            if regime == Regime.TRENDING:
                regime_weight = 1.0  # Full weight for trending
            elif regime == Regime.MEAN_REVERTING:
                regime_weight = 0.8  # Good weight for mean reversion

        # Check multifractal stability
        stability_discount = 1.0
        if "multifractal" in sigs:
            mf_sig = sigs["multifractal"]
            stability = mf_sig.metadata.get("stability_score", 1.0)
            if stability < 0.3:
                stability_discount = 0.5  # Market structure breaking down

        # Primary signal: OFI direction and strength
        direction = None
        raw_strength = 0.0
        if "ofi" in sigs:
            ofi_sig = sigs["ofi"]
            direction = ofi_sig.direction
            raw_strength = ofi_sig.strength

            # In mean-reverting regime, flip OFI direction (contrarian)
            if regime == Regime.MEAN_REVERTING and direction:
                direction = Side.SELL if direction == Side.BUY else Side.BUY

        # Composite strength with all modifiers
        composite_strength = raw_strength * regime_weight * toxicity_discount * stability_discount

        now = datetime.utcnow()
        return Signal(
            symbol=symbol,
            timestamp=now,
            name="composite",
            value=composite_strength if direction == Side.BUY else -composite_strength,
            direction=direction,
            strength=composite_strength,
            metadata={
                "regime": regime.value,
                "toxicity_discount": toxicity_discount,
                "stability_discount": stability_discount,
                "regime_weight": regime_weight,
                "raw_ofi_strength": raw_strength,
                "component_signals": list(sigs.keys()),
            },
        )

    def get_regime(self, symbol: str) -> Regime:
        """Get the current detected regime for a symbol."""
        if self._hurst:
            return self._hurst.get_regime(symbol)
        return Regime.RANDOM_WALK

    def is_toxic(self, symbol: str) -> bool:
        """Check if current order flow is toxic."""
        if self._vpin:
            return self._vpin.is_toxic(symbol)
        return False
