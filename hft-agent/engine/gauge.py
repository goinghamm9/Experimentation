"""Gauge-theoretic return attribution after Malaney & Weinstein ("The Economic Index Problem").

Malaney-Weinstein treat a price index as parallel transport under the connection
    A = sum_i w_i d(ln p_i)
with w the expenditure (here: portfolio value) shares. When shares are a fixed
function of prices the connection is flat and the index is path-independent; when
preferences (here: portfolio weights) respond to the path, the curvature dw ^ d(ln p)
is non-zero and the index acquires holonomy.

For a self-financing portfolio this gives an exact, per-period identity:

    ln(1 + w_t . r_t) = wbar . dl_t              exposure  (flat, path-independent)
                      + (w_t - wbar) . dl_t      timing    (curvature / holonomy)
                      + [ln(w_t . e^{dl_t}) - w_t . dl_t]   convexity (Jensen gap, >= 0 long-only)

where dl = ln(1 + r). Around any closed loop in log-price space the exposure term
vanishes, so realised timing + convexity *is* the holonomy of the strategy.

Changing numeraire (dollars -> T-bills -> gold) is a gauge transformation dl -> dl - c.
Because weights sum to one, only the exposure term moves; timing and convexity are
gauge-invariant. That invariance is what makes them honest measures of skill.

This is a measurement layer. It says whether returns came from simply holding assets
or from the path-dependent act of trading them. It does not generate signals.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class GaugeAttribution:
    exposure: np.ndarray
    timing: np.ndarray
    convexity: np.ndarray
    total: np.ndarray

    def totals(self) -> dict[str, float]:
        return {
            "exposure": float(self.exposure.sum()),
            "timing_holonomy": float(self.timing.sum()),
            "convexity": float(self.convexity.sum()),
            "total_log_growth": float(self.total.sum()),
        }


def attribute(weights: np.ndarray, simple_returns: np.ndarray, reference_weights: np.ndarray | None = None) -> GaugeAttribution:
    """weights: (T, N) start-of-period value shares summing to 1 (include the safe asset).
    simple_returns: (T, N) returns over each period. Rows with NaN returns are treated as 0.
    """
    w = np.asarray(weights, dtype=np.float64)
    r = np.nan_to_num(np.asarray(simple_returns, dtype=np.float64))
    # ln(0) is undefined for positions that expire worthless (options); floor at -99%.
    # `total` uses exact returns, so the flooring difference lands in `convexity`.
    dl = np.log1p(np.maximum(r, -0.99))
    wbar = w.mean(axis=0) if reference_weights is None else np.asarray(reference_weights, dtype=np.float64)

    total = np.log1p(np.sum(w * r, axis=1))
    connection = np.sum(w * dl, axis=1)
    exposure = dl @ wbar
    timing = connection - exposure
    convexity = total - connection
    return GaugeAttribution(exposure, timing, convexity, total)


def change_numeraire(simple_returns: np.ndarray, numeraire_returns: np.ndarray) -> np.ndarray:
    """Re-express asset returns in units of a numeraire asset (a gauge transformation)."""
    r = np.asarray(simple_returns, dtype=np.float64)
    n = np.asarray(numeraire_returns, dtype=np.float64)[:, None]
    return (1 + r) / (1 + n) - 1
