"""Coder reliability — and the effective sample size that qualifies it.

Implements corpus §3, §8.1 and §11.2.

Two warnings are load-bearing and are surfaced in the report rather than left to
the reader:

1. **Agreement is not truth.** Krippendorff's α measures shared professional
   vision (Goodwin, §15.6) — two coders trained together agree, and that is
   evidence about the training. High α on a scheme with no external validation is
   not reassurance.
2. **Correlated coders are not independent coders.** Judges sharing a base model
   or prompt lineage are correlated sources (§10.6). Always report ``n_eff``
   beside any agreement statistic; nominal coder count overstates the evidence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass
class ReliabilityReport:
    n_units: int
    n_coders: int
    alpha: float | None            # Krippendorff's α (nominal)
    observed_agreement: float | None
    n_eff: float                   # effective coders after correlation deflation
    rho: float                     # assumed/estimated inter-coder correlation
    note: str = ""

    def interpretation(self) -> str:
        if self.alpha is None:
            return "not computable"
        a = self.alpha
        if a < 0.40:
            return "poor"
        if a < 0.60:
            return "moderate"
        if a < 0.80:
            return "substantial"
        return "excellent"


# --------------------------------------------------------------------------
# Agreement statistics
# --------------------------------------------------------------------------

def krippendorff_alpha(units: list[list[str | None]]) -> float | None:
    """Krippendorff's α for *nominal* data, tolerating missing values.

    ``units`` is one list per unit, holding each coder's label (``None`` = missing).
    Units with fewer than two present ratings contribute nothing, per the standard
    treatment.

        α = 1 − D_o/D_e
          = 1 − [ (n−1)·Σ_{c≠k} o_ck ] / [ Σ_{c≠k} n_c·n_k ]      (nominal δ²)

    Returns None when α is undefined (no pairable ratings, or zero expected
    disagreement — e.g. every rating is the same category).
    """
    coincidence: Counter[tuple[str, str]] = Counter()
    for ratings in units:
        present = [r for r in ratings if r is not None]
        m = len(present)
        if m < 2:
            continue
        w = 1.0 / (m - 1)
        for i, a in enumerate(present):
            for j, b in enumerate(present):
                if i != j:
                    coincidence[(a, b)] += w

    if not coincidence:
        return None

    marginals: Counter[str] = Counter()
    for (a, _b), v in coincidence.items():
        marginals[a] += v
    n = sum(marginals.values())
    if n <= 1:
        return None

    observed_disagreement = sum(v for (a, b), v in coincidence.items() if a != b)
    expected_disagreement = sum(
        marginals[a] * marginals[b]
        for a in marginals
        for b in marginals
        if a != b
    )
    if expected_disagreement == 0:
        return None
    return 1.0 - ((n - 1) * observed_disagreement) / expected_disagreement


def cohens_kappa(a: list[str], b: list[str]) -> float | None:
    """Cohen's κ for two coders over the same units."""
    if len(a) != len(b) or not a:
        return None
    n = len(a)
    p_o = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    p_e = sum((ca[k] / n) * (cb[k] / n) for k in set(ca) | set(cb))
    if p_e == 1:
        return None
    return (p_o - p_e) / (1 - p_e)


def fleiss_kappa(units: list[list[str]]) -> float | None:
    """Fleiss' κ for a fixed number of coders per unit."""
    units = [u for u in units if u]
    if not units:
        return None
    m = len(units[0])
    if m < 2 or any(len(u) != m for u in units):
        return None
    categories = sorted({c for u in units for c in u})
    N = len(units)

    p_i = []
    for u in units:
        counts = Counter(u)
        p_i.append((sum(v * v for v in counts.values()) - m) / (m * (m - 1)))
    p_bar = sum(p_i) / N

    p_j = [sum(Counter(u)[c] for u in units) / (N * m) for c in categories]
    p_e = sum(p * p for p in p_j)
    if p_e == 1:
        return None
    return (p_bar - p_e) / (1 - p_e)


def observed_agreement(units: list[list[str | None]]) -> float | None:
    """Mean pairwise proportion of agreeing coder pairs across units."""
    total = agree = 0
    for ratings in units:
        present = [r for r in ratings if r is not None]
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                total += 1
                if present[i] == present[j]:
                    agree += 1
    return agree / total if total else None


# --------------------------------------------------------------------------
# Effective sample size — the qualifier that must travel with every estimate
# --------------------------------------------------------------------------

def n_eff_correlation(k: int, rho: float) -> float:
    """Effective count of *correlated* sources: n_eff = k / (1 + (k−1)·ρ)   (§8.1).

    At ρ = 0.6, five sources are worth ~1.47 independent observations; at ρ = 0.5,
    ~1.67. This is the formal statement of why three coders from one model family
    are not three coders.

    Source note: corpus §8.1 illustrates this formula with "at ρ = 0.6 … about 1.7",
    which does not follow from the formula it states (5/3.4 = 1.47); 1.67
    corresponds to ρ = 0.5. The formula is the standard Kish design effect and is
    implemented as written, not as illustrated.
    """
    if k <= 0:
        return 0.0
    rho = min(max(rho, 0.0), 1.0)
    return k / (1 + (k - 1) * rho)


def n_eff_tail(n: int, alpha: float) -> float:
    """Tail-deflated effective sample size: n_eff = n^(2(α−1)/α) for 1 < α ≤ 2 (§11.2).

    Deflates *independently* of the correlation deflation above — a sample can be
    hit by both. As α → 1 no achievable n helps and reporting a sample mean is an
    error rather than an approximation.
    """
    if n <= 0:
        return 0.0
    if alpha <= 1:
        return 1.0
    if alpha > 2:
        return float(n)
    return n ** (2 * (alpha - 1) / alpha)


def assess(
    units: list[list[str | None]],
    n_coders: int,
    rho: float = 0.0,
) -> ReliabilityReport:
    """Build a reliability report, refusing to invent numbers for one coder."""
    if n_coders < 2:
        return ReliabilityReport(
            n_units=len(units),
            n_coders=n_coders,
            alpha=None,
            observed_agreement=None,
            n_eff=float(n_coders),
            rho=rho,
            note=(
                "Single coder: agreement is not computable and reliability is "
                "UNKNOWN. This is a stated limitation, not a passing grade."
            ),
        )
    return ReliabilityReport(
        n_units=len(units),
        n_coders=n_coders,
        alpha=krippendorff_alpha(units),
        observed_agreement=observed_agreement(units),
        n_eff=n_eff_correlation(n_coders, rho),
        rho=rho,
        note=(
            "α measures shared professional vision, not correspondence to truth. "
            "Only α against a human gold codebook supports a validity claim."
        ),
    )
