"""
Multifractal analysis for market structure detection.

Based on:
- Mandelbrot's Multifractal Model of Asset Returns (MMAR)
- Jeon (2021): Overview of the Multifractal Model of Asset Returns
- Bank of England (2013): Fractal Market Hypothesis

The multifractal spectrum captures how the scaling behavior of price
changes varies across different moment orders. A wider spectrum indicates
richer microstructure — multiple agent types interacting across timescales.

When the fractal structure "breaks down" (spectrum narrows), markets become
unstable — short-term and long-term investors correlate rather than offset.
This is a leading indicator of flash crashes and liquidity crises.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from utils.types import Signal


class MultifractalAnalyzer:
    """Multifractal Detrended Fluctuation Analysis (MF-DFA).

    Computes the generalized Hurst exponent h(q) for multiple moment
    orders q, revealing the multifractal spectrum of price dynamics.
    """

    def __init__(
        self,
        scales: list[int] | None = None,
        q_values: list[float] | None = None,
        min_window: int = 256,
    ):
        self._scales = scales or [16, 32, 64, 128, 256]
        self._q_values = q_values or [-3, -2, -1, 0.5, 1, 2, 3, 4, 5]
        self._min_window = min_window
        self._price_history: dict[str, deque] = {}

    def update(self, symbol: str, price: float, timestamp: datetime) -> Signal | None:
        """Update with new price and compute multifractal spectrum."""
        if symbol not in self._price_history:
            self._price_history[symbol] = deque(maxlen=max(self._scales) * 4)
        self._price_history[symbol].append(price)

        if len(self._price_history[symbol]) < self._min_window:
            return None

        prices = np.array(self._price_history[symbol], dtype=np.float64)
        returns = np.diff(np.log(prices))

        spectrum = self._compute_mf_spectrum(returns)
        if spectrum is None:
            return None

        h_q = spectrum["h_q"]
        spectrum_width = spectrum["width"]

        # Wider spectrum = more complex multifractal structure = healthy market
        # Narrowing spectrum = structure breaking down = instability risk
        # Typical width for equities: 0.3-0.6
        stability_score = min(spectrum_width / 0.5, 1.0)

        return Signal(
            symbol=symbol,
            timestamp=timestamp,
            name="multifractal",
            value=spectrum_width,
            strength=1.0 - stability_score,  # High strength = instability
            metadata={
                "h_q": {str(q): h for q, h in zip(self._q_values, h_q)},
                "spectrum_width": spectrum_width,
                "h2": spectrum["h2"],  # Standard Hurst from q=2
                "stability_score": stability_score,
            },
        )

    def _compute_mf_spectrum(
        self,
        returns: NDArray[np.float64],
    ) -> dict | None:
        """Compute the multifractal spectrum using MF-DFA."""
        n = len(returns)
        profile = np.cumsum(returns - np.mean(returns))

        # For each scale, compute fluctuation function
        h_q_values = []

        for q in self._q_values:
            log_scales = []
            log_fluct = []

            for scale in self._scales:
                if scale > n // 2:
                    continue

                n_segments = n // scale
                if n_segments < 2:
                    continue

                fluctuations = []
                for i in range(n_segments):
                    segment = profile[i * scale : (i + 1) * scale]
                    # Detrend with linear fit
                    x = np.arange(len(segment), dtype=np.float64)
                    coeffs = np.polyfit(x, segment, 1)
                    trend = np.polyval(coeffs, x)
                    residual = segment - trend
                    rms = np.sqrt(np.mean(residual**2))
                    if rms > 0:
                        fluctuations.append(rms)

                if not fluctuations:
                    continue

                fluct_array = np.array(fluctuations, dtype=np.float64)

                # Generalized fluctuation function F_q(s)
                if q == 0:
                    # Use geometric mean for q=0
                    fq = np.exp(np.mean(np.log(fluct_array)))
                else:
                    fq = np.mean(fluct_array**q) ** (1.0 / q)

                log_scales.append(np.log(scale))
                log_fluct.append(np.log(fq))

            if len(log_scales) < 2:
                h_q_values.append(0.5)  # Default
                continue

            # Fit log(F_q) vs log(s) to get h(q)
            coeffs = np.polyfit(log_scales, log_fluct, 1)
            h_q_values.append(float(coeffs[0]))

        if not h_q_values:
            return None

        h_q = np.array(h_q_values, dtype=np.float64)

        # Spectrum width = h(q_min) - h(q_max)
        width = float(np.max(h_q) - np.min(h_q))

        # h(2) is the standard Hurst exponent
        h2_idx = self._q_values.index(2) if 2 in self._q_values else -1
        h2 = float(h_q[h2_idx]) if h2_idx >= 0 else 0.5

        return {
            "h_q": h_q.tolist(),
            "width": width,
            "h2": h2,
        }
