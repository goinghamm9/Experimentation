"""Saturation estimators — species-richness methods applied to code discovery.

Implements corpus §1.2–§1.3. The point is to replace the assertion "no new themes
emerged" with an auditable number:

    "We stopped at f1/n = 0.04 with Chao1 projecting 3 unobserved codes."

The sampling unit is the *participant* (analogous to an interview), and a "species"
is a code. ``f1`` is the number of codes expressed by exactly one participant, ``f2``
by exactly two.

Caveats carried from the corpus, deliberately surfaced in the output rather than
buried: these estimators assume a well-behaved abundance distribution (§11.2 — if
code prevalence is itself fat-tailed, saturation estimates are optimistic), and they
break if coding granularity drifts mid-study, since splitting a code inflates ``f1``
and fakes non-saturation (§1.3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SaturationReport:
    n_units: int
    n_codes_observed: int
    f1: int
    f2: int
    unseen_mass: float          # Good–Turing P0 ≈ f1/n
    chao1: float
    chao1_bias_corrected: float
    projected_unseen: float

    @property
    def is_saturated(self) -> bool:
        """Heuristic only — a low singleton rate is evidence, not proof."""
        return self.unseen_mass < 0.05

    def summary(self) -> str:
        return (
            f"n={self.n_units} units, {self.n_codes_observed} codes observed "
            f"(f1={self.f1}, f2={self.f2}); Good-Turing unseen mass "
            f"{self.unseen_mass:.3f}; Chao1 projects "
            f"{self.projected_unseen:.1f} unobserved code(s)"
        )


def good_turing_unseen(f1: int, n_units: int) -> float:
    """Good–Turing estimate of the probability mass of unseen codes: P0 ≈ f1/n."""
    if n_units <= 0:
        return 0.0
    return f1 / n_units


def chao1(observed: int, f1: int, f2: int) -> float:
    """Chao1 richness: K̂ = D + f1²/(2·f2).

    Falls back to the bias-corrected form when f2 == 0, where the classic
    estimator is undefined (division by zero).
    """
    if f2 == 0:
        return chao1_bias_corrected(observed, f1, f2)
    return observed + (f1 * f1) / (2 * f2)


def chao1_bias_corrected(observed: int, f1: int, f2: int) -> float:
    """Bias-corrected Chao1: K̂ = D + f1(f1−1) / (2(f2+1)).

    Preferred for small samples, and defined even when f2 == 0.
    """
    return observed + (f1 * (f1 - 1)) / (2 * (f2 + 1))


def heaps_beta(discovery_curve: list[int]) -> float | None:
    """Fit the Heaps'-law exponent β in D_n ≈ α·n^β by log-log least squares.

    β < 1 indicates the concave, decelerating discovery expected under saturation.
    Returns None when there is too little data to fit.
    """
    pts = [(i + 1, d) for i, d in enumerate(discovery_curve) if d > 0]
    if len(pts) < 3:
        return None
    xs = [math.log(n) for n, _ in pts]
    ys = [math.log(d) for _, d in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom


def assess(code_to_units: dict[str, set[str]], n_units: int) -> SaturationReport:
    """Build a saturation report from a code → set-of-sampling-units mapping.

    ``code_to_units`` maps each code label to the distinct participants (or other
    sampling units) that expressed it.
    """
    incidences = [len(u) for u in code_to_units.values() if u]
    observed = len(incidences)
    f1 = sum(1 for c in incidences if c == 1)
    f2 = sum(1 for c in incidences if c == 2)

    c1 = chao1(observed, f1, f2)
    c1bc = chao1_bias_corrected(observed, f1, f2)
    return SaturationReport(
        n_units=n_units,
        n_codes_observed=observed,
        f1=f1,
        f2=f2,
        unseen_mass=good_turing_unseen(f1, n_units),
        chao1=c1,
        chao1_bias_corrected=c1bc,
        projected_unseen=max(0.0, c1bc - observed),
    )
