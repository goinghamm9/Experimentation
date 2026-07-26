"""Base-rate honesty and search-space accounting.

Implements corpus §11.3, §12.1 and §12.3 — the controls that must be
*architectural rather than procedural*, because at machine speed nobody enforces
them by hand.

Two results drive the design:

* **Base rates dominate.** At prevalence 0.001 with sensitivity 0.95 and
  specificity 0.99, precision is 8.7% — more than nine flags in ten are wrong,
  from an excellent-sounding classifier. Hence: *the output is a ranked queue,
  never a finding*, and you raise prevalence by pre-stratification rather than
  chasing specificity.
* **Apophenia scales with the search.** Under the null the largest of ``m``
  sampled correlations is ≈ √(2·ln m / n). An agent enumerating hypotheses drives
  ``m`` up by orders of magnitude, so α_eff → 1. **A system that does not log
  ``m`` cannot state what any of its findings mean.**
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


def ppv(sensitivity: float, specificity: float, prevalence: float) -> float:
    """Positive predictive value at a stated base rate (§12.1)."""
    tp = sensitivity * prevalence
    fp = (1 - specificity) * (1 - prevalence)
    denom = tp + fp
    return tp / denom if denom > 0 else 0.0


def rule_of_three(n: int) -> float:
    """95% upper bound on prevalence given ZERO observations in n trials: p ≤ 3/n.

    The correct reply to "we never saw it" (§11.3). Thirty interviews with no
    report of a practice leaves its prevalence plausibly as high as 10%.
    """
    return 3.0 / n if n > 0 else 1.0


def detection_floor(prevalence: float, confidence: float = 0.95) -> int:
    """Interviews needed to detect a theme held by ``prevalence`` (§1.1).

        n ≥ ln(1−confidence) / ln(1−p)

    Thin-tailed formula: assumes exchangeable informants and stationary p. For
    rare, consequential or regime-dependent events use :func:`rule_of_three`.
    """
    if not 0 < prevalence < 1:
        return 0
    return math.ceil(math.log(1 - confidence) / math.log(1 - prevalence))


def alpha_eff(alpha: float, m_hypotheses: int) -> float:
    """Family-wise error after m implicit analytic paths: α_eff = 1 − (1−α)^m."""
    if m_hypotheses <= 0:
        return 0.0
    return 1 - (1 - alpha) ** m_hypotheses


def max_spurious_correlation(m_hypotheses: int, n_observations: int) -> float:
    """Expected largest |r| under the null across m comparisons: √(2·ln m / n).

    **Approximation limit.** This is an asymptotic result valid when ``n`` is large
    relative to ``ln m``. When ``m`` is large and ``n`` small the raw expression
    exceeds 1, which is impossible for a correlation; the value is clamped and
    :func:`search_is_saturated` reports that the bound has gone uninformative.

    A clamped 1.0 is not a reassuring number — it means the search space is so
    large relative to the sample that chance alone can produce *any* apparent
    relationship, and no correlation from this run carries information.
    """
    if m_hypotheses <= 1 or n_observations <= 0:
        return 0.0
    return min(1.0, math.sqrt(2 * math.log(m_hypotheses) / n_observations))


def search_is_saturated(m_hypotheses: int, n_observations: int) -> bool:
    """True when the search space has outgrown the sample entirely.

    At that point the expected largest chance correlation reaches 1.0: the data
    cannot discriminate signal from noise at all, and findings must be reported as
    hypothesis-generating only.
    """
    if m_hypotheses <= 1 or n_observations <= 0:
        return False
    return 2 * math.log(m_hypotheses) / n_observations >= 1.0


@dataclass
class SearchLedger:
    """Counts hypotheses considered so a run can state what its findings mean.

    Every candidate code, theme, or comparison the system *entertained* — not only
    those it reported — must be counted here.
    """

    hypotheses_considered: int = 0
    by_stage: dict[str, int] = field(default_factory=dict)

    def record(self, stage: str, count: int = 1) -> None:
        self.hypotheses_considered += count
        self.by_stage[stage] = self.by_stage.get(stage, 0) + count

    def report(self, n_observations: int, alpha: float = 0.05) -> dict[str, float]:
        m = self.hypotheses_considered
        return {
            "m_hypotheses": float(m),
            "alpha_nominal": alpha,
            "alpha_effective": alpha_eff(alpha, m),
            "expected_max_spurious_r": max_spurious_correlation(m, n_observations),
        }

    def summary(self, n_observations: int, alpha: float = 0.05) -> str:
        r = self.report(n_observations, alpha)
        line = (
            f"m={int(r['m_hypotheses'])} hypotheses considered; "
            f"nominal α={alpha:.2f} → effective α={r['alpha_effective']:.3f}; "
            f"expected largest spurious |r|={r['expected_max_spurious_r']:.3f}"
        )
        if search_is_saturated(self.hypotheses_considered, n_observations):
            line += (
                " — SATURATED: the search space has outgrown the sample, so chance "
                "alone can produce any apparent relationship. Hypothesis-generating only."
            )
        return line
