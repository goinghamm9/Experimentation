"""Cultural Consensus Theory and the noise threshold that qualifies it.

Implements corpus §2.1 (General Condorcet Model) and §12.2 (Marchenko–Pastur).

CCT recovers the "right answers" with no answer key by exploiting the fact that
competent informants agree with each other more. With guessing bias g = 1/2 the
guessing-corrected agreement matrix is **rank one**:

    M*_ij = 2·M_ij − 1 = D_i · D_j

so eigendecomposing M* yields competences as first-eigenvector loadings, and the
ratio λ1/λ2 tests whether one shared domain is in play. A large λ2 means
subcultures — or, applied to model coders, **two different rubrics**, which is a
finding about rubric ambiguity rather than noise to average away.

§12.2 supplies the discipline that turns the λ1/λ2 ≥ 3 rule of thumb into a
theorem: eigenvalues inside the Marchenko–Pastur bulk are sampling noise however
suggestive they look.

Pure Python — symmetric eigendecomposition by the cyclic Jacobi method, so the
package keeps its zero-dependency, fully-offline property.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class ConsensusReport:
    n_coders: int
    eigenvalues: list[float]
    competences: dict[str, float] = field(default_factory=dict)
    eigenvalue_ratio: float | None = None
    mp_upper_edge: float | None = None
    n_signal_dimensions: int = 0
    note: str = ""

    @property
    def single_domain(self) -> bool:
        """True when one shared rubric/culture is supported (λ1/λ2 ≥ 3)."""
        return self.eigenvalue_ratio is not None and self.eigenvalue_ratio >= 3.0


# --------------------------------------------------------------------------
# Linear algebra (kept dependency-free on purpose)
# --------------------------------------------------------------------------

def jacobi_eigen(
    matrix: list[list[float]],
    max_sweeps: int = 100,
    tol: float = 1e-10,
) -> tuple[list[float], list[list[float]]]:
    """Cyclic Jacobi eigendecomposition of a real symmetric matrix.

    Returns (eigenvalues, eigenvectors) sorted by descending eigenvalue, with
    ``eigenvectors[k]`` the k-th eigenvector.
    """
    n = len(matrix)
    a = [row[:] for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for _ in range(max_sweeps):
        off = math.sqrt(sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j))
        if off < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < tol:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = (1 if theta >= 0 else -1) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p] = c * vkp - s * vkq
                    v[k][q] = s * vkp + c * vkq

    eigenvalues = [a[i][i] for i in range(n)]
    vectors = [[v[i][k] for i in range(n)] for k in range(n)]
    order = sorted(range(n), key=lambda k: -eigenvalues[k])
    return [eigenvalues[k] for k in order], [vectors[k] for k in order]


# --------------------------------------------------------------------------
# CCT
# --------------------------------------------------------------------------

def agreement_matrix(
    coder_answers: dict[str, list[str | None]],
) -> tuple[list[str], list[list[float]]]:
    """Pairwise proportion-of-match matrix over coders sharing the same items."""
    names = sorted(coder_answers)
    n = len(names)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        m[i][i] = 1.0
        for j in range(i + 1, n):
            a, b = coder_answers[names[i]], coder_answers[names[j]]
            pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
            score = (sum(1 for x, y in pairs if x == y) / len(pairs)) if pairs else 0.0
            m[i][j] = m[j][i] = score
    return names, m


def corrected_agreement_matrix(m: list[list[float]]) -> list[list[float]]:
    """Guessing-corrected matrix M* = 2M − 1, which should be rank one under CCT.

    The diagonal is excluded from the rank-one claim (self-agreement is trivially
    1), so it is set to the mean off-diagonal value of its row — the standard
    treatment for estimating a communality-style diagonal.
    """
    n = len(m)
    star = [[2 * m[i][j] - 1 for j in range(n)] for i in range(n)]
    for i in range(n):
        others = [star[i][j] for j in range(n) if j != i]
        star[i][i] = sum(others) / len(others) if others else 1.0
    return star


def marchenko_pastur_edge(n_variables: int, n_observations: int, sigma_sq: float = 1.0) -> float:
    """Upper edge of the noise bulk: λ+ = σ²·(1 + √q)², q = p/n   (§12.2).

    Eigenvalues at or below this are indistinguishable from sampling noise.
    """
    if n_observations <= 0:
        return float("inf")
    q = n_variables / n_observations
    return sigma_sq * (1 + math.sqrt(q)) ** 2


def assess(
    coder_answers: dict[str, list[str | None]],
    n_items: int | None = None,
) -> ConsensusReport:
    """Run CCT over coders and gate the result on the Marchenko–Pastur edge."""
    names, m = agreement_matrix(coder_answers)
    n = len(names)
    if n < 3:
        return ConsensusReport(
            n_coders=n,
            eigenvalues=[],
            note="CCT needs at least 3 coders to separate competence from agreement.",
        )

    star = corrected_agreement_matrix(m)
    eigenvalues, vectors = jacobi_eigen(star)

    first = vectors[0]
    # Sign-normalise, then read competences as first-eigenvector loadings.
    if sum(first) < 0:
        first = [-x for x in first]
    scale = math.sqrt(max(eigenvalues[0], 0.0)) if eigenvalues[0] > 0 else 0.0
    competences = {
        name: max(0.0, min(1.0, first[i] * scale)) for i, name in enumerate(names)
    }

    ratio = None
    if len(eigenvalues) > 1 and abs(eigenvalues[1]) > 1e-12:
        ratio = eigenvalues[0] / abs(eigenvalues[1])

    items = n_items if n_items is not None else max(
        (len(v) for v in coder_answers.values()), default=0
    )
    edge = marchenko_pastur_edge(n, items) if items else None
    n_signal = sum(1 for e in eigenvalues if edge is not None and e > edge)

    if ratio is None:
        note = "Second eigenvalue ~0; ratio undefined."
    elif ratio >= 3.0:
        note = "Single shared rubric supported (λ1/λ2 ≥ 3)."
    else:
        note = (
            "λ1/λ2 < 3 — coders are applying MORE THAN ONE rubric. This is a "
            "finding about rubric ambiguity, not noise to average away."
        )
    if edge is not None and n_signal == 0:
        note += " WARNING: no eigenvalue exceeds the Marchenko–Pastur edge — no structure to find."

    return ConsensusReport(
        n_coders=n,
        eigenvalues=eigenvalues,
        competences=competences,
        eigenvalue_ratio=ratio,
        mp_upper_edge=edge,
        n_signal_dimensions=n_signal,
        note=note,
    )


def competence_weighted_answer(
    coder_answers: dict[str, list[str | None]],
    competences: dict[str, float],
    item_index: int,
) -> str | None:
    """Aggregate one item by competence-weighted voting rather than majority.

    Weight ln((1+D)/(1−D)) is the exact Bayesian aggregation of §2.1 — the formal
    warrant for the ethnographer's key-informant instinct: five informants at
    D ≈ 0.8 beat fifty at D ≈ 0.2.
    """
    scores: dict[str, float] = {}
    for name, answers in coder_answers.items():
        if item_index >= len(answers):
            continue
        value = answers[item_index]
        if value is None:
            continue
        d = min(max(competences.get(name, 0.0), 0.0), 0.999)
        weight = math.log((1 + d) / (1 - d)) if d > 0 else 0.0
        scores[value] = scores.get(value, 0.0) + weight
    if not scores:
        return None
    return max(scores.items(), key=lambda kv: kv[1])[0]
