"""Multi-coder panels: agreement among agents, and validity against humans.

This module exists because agreement statistics are routinely misread, and the
misreading is the whole risk of an AI coding system. Two quantities look alike and
mean opposite things:

    agent ↔ agent   agreement  →  a DISAGREEMENT ROUTER.  Not evidence of truth.
    agent ↔ human   agreement  →  the VALIDITY claim, and the only one available.

Judges sharing a base model or prompt lineage are correlated sources (corpus
§10.6); ensembling them "produces confidence rather than evidence". Goodwin's
point (§15.6) is sharper still — α measures *shared professional vision*, so two
coders trained alike agree for reasons that have nothing to do with being right.

Three design consequences are enforced here rather than left to discipline:

1. **Lineage is recorded per coder.** Correlation is not assumed away.
2. **ρ is estimated from the data**, not passed in as a hopeful default. The
   ``n_eff`` reported by this module is computed from an *observed* ρ.
3. **Validity is computed only against a gold standard**, and refuses to report
   anything when no human gold is present.
"""

from __future__ import annotations

import enum
import hashlib
from dataclasses import dataclass, field

from .consensus import ConsensusReport
from .consensus import assess as assess_consensus
from .reliability import cohens_kappa, krippendorff_alpha, n_eff_correlation


class CoderKind(str, enum.Enum):
    DETERMINISTIC = "deterministic"   # rule-based; perfectly reproducible
    MODEL = "model"                   # an LLM coder
    HUMAN = "human"                   # a person; the only source of gold


@dataclass
class Coder:
    """A coder and — critically — its lineage.

    ``lineage`` groups coders whose errors are expected to correlate: a base model
    family, a shared prompt template, or a shared training cohort for humans.
    Coders in the same lineage are *not* independent evidence.
    """

    id: str
    kind: CoderKind
    lineage: str | None = None

    @property
    def is_gold_source(self) -> bool:
        return self.kind is CoderKind.HUMAN


class RoutingAction(str, enum.Enum):
    ACCEPT = "accept"            # coders agree
    RESTART = "restart"          # disagreement → re-code, do not spend a human
    ESCALATE = "escalate"        # persistent disagreement → the CONTRACT is wrong


@dataclass
class Disagreement:
    unit_id: str
    labels: dict[str, str]        # coder id → label
    restart_count: int
    action: RoutingAction
    reason: str


@dataclass
class PanelReport:
    n_units: int
    coders: list[Coder]

    # Agent-side: a router, not a validity claim.
    agent_alpha: float | None
    mean_pairwise_kappa: float | None

    # Correlation, estimated rather than assumed.
    rho_estimated: float
    rho_within_lineage: float | None
    rho_cross_lineage: float | None
    n_eff: float

    # Human-side: the only validity claim available.
    validity_vs_gold: dict[str, float] = field(default_factory=dict)
    gold_units: int = 0

    consensus: ConsensusReport | None = None
    frequency_labels: dict[str, str] = field(default_factory=dict)
    routing: list[Disagreement] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def has_validity_evidence(self) -> bool:
        return bool(self.validity_vs_gold) and self.gold_units > 0

    @property
    def n_nominal(self) -> int:
        return len(self.coders)

    def summary(self) -> str:
        parts = [f"{self.n_nominal} coders → n_eff {self.n_eff:.2f} (ρ̂={self.rho_estimated:.2f})"]
        if self.agent_alpha is not None:
            parts.append(f"agent α={self.agent_alpha:.3f} [router, not validity]")
        if self.has_validity_evidence:
            best = max(self.validity_vs_gold.values())
            parts.append(f"vs human gold: κ up to {best:.3f} on {self.gold_units} units")
        else:
            parts.append("NO human gold — validity UNKNOWN")
        return "; ".join(parts)


# ---------------------------------------------------------------------------
# Gold-standard sampling
# ---------------------------------------------------------------------------

def probability_sample(unit_ids: list[str], k: int, seed: str = "gold") -> list[str]:
    """Draw a reproducible *probability* sample of units for human gold coding.

    A probability sample — not a convenience sample — is a hard requirement for
    two downstream uses: it is the validity benchmark, and it is the rectifier set
    for prediction-powered inference. Selection is by keyed hash so the draw is
    deterministic, auditable, and independent of unit ordering.
    """
    if k <= 0 or not unit_ids:
        return []
    ranked = sorted(
        unit_ids,
        key=lambda u: hashlib.sha256(f"{seed}:{u}".encode()).hexdigest(),
    )
    return sorted(ranked[: min(k, len(ranked))])


# ---------------------------------------------------------------------------
# Correlation, estimated from observed behaviour
# ---------------------------------------------------------------------------

def estimate_rho_from_agreement(
    answers: dict[str, list[str | None]],
    coders: dict[str, Coder],
) -> tuple[float, float | None, float | None]:
    """Estimate inter-coder correlation ρ from chance-corrected agreement.

    Returns ``(overall, within_lineage, cross_lineage)``.

    **Assumption, stated because it matters:** mean pairwise Cohen's κ is used as a
    *proxy* for ρ. It measures agreement beyond chance, which conflates
    agreeing-because-correct with agreeing-because-identically-wrong. Without a
    gold standard those cannot be separated, so this is a **lower bound on shared
    error** and therefore an *optimistic* ρ. Prefer
    :func:`estimate_rho_from_shared_error` whenever gold labels exist.
    """
    ids = sorted(answers)
    within: list[float] = []
    cross: list[float] = []

    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            pairs = [
                (x, y)
                for x, y in zip(answers[a], answers[b])
                if x is not None and y is not None
            ]
            if not pairs:
                continue
            k = cohens_kappa([x for x, _ in pairs], [y for _, y in pairs])
            if k is None:
                continue
            k = max(0.0, k)
            la, lb = coders[a].lineage, coders[b].lineage
            if la is not None and la == lb:
                within.append(k)
            else:
                cross.append(k)

    allv = within + cross
    overall = sum(allv) / len(allv) if allv else 0.0
    return (
        overall,
        sum(within) / len(within) if within else None,
        sum(cross) / len(cross) if cross else None,
    )


def estimate_rho_from_shared_error(
    answers: dict[str, list[str | None]],
    gold: list[str | None],
    min_joint_errors: int = 5,
) -> float | None:
    """Estimate ρ properly: do coders make the *same* mistake more than chance?

    Restricted to units where both coders are wrong, this measures genuine error
    correlation rather than shared correctness — the quantity that actually
    deflates effective sample size.

    **Identifiability guard (this is not optional).** With a binary codebook the
    statistic is degenerate: if gold is one of two categories and both coders are
    wrong, they are *necessarily* wrong in the same way, so the raw shared-error
    rate is 1.0 for any pair — including perfectly independent coders. The measure
    is only identifiable with **three or more categories**, and the chance level is
    ``1/(C−1)`` rather than 0, so the rate is normalised against it.

    Returns None when ρ is not identifiable or when there is too little evidence.
    """
    categories = {g for g in gold if g is not None}
    categories |= {v for vals in answers.values() for v in vals if v is not None}
    n_cat = len(categories)
    if n_cat < 3:
        # Degenerate: "both wrong" implies "same wrong". Not identifiable.
        return None

    chance = 1.0 / (n_cat - 1)   # P(same wrong | both wrong) under independence
    ids = sorted(answers)
    scores: list[float] = []

    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            both_wrong = same_wrong = 0
            for x, y, g in zip(answers[a], answers[b], gold):
                if x is None or y is None or g is None:
                    continue
                if x != g and y != g:
                    both_wrong += 1
                    if x == y:
                        same_wrong += 1
            if both_wrong >= min_joint_errors:
                raw = same_wrong / both_wrong
                # Normalise against chance, floored at 0.
                scores.append(max(0.0, (raw - chance) / (1.0 - chance)))

    return sum(scores) / len(scores) if scores else None


# ---------------------------------------------------------------------------
# CQR-style frequency labels
# ---------------------------------------------------------------------------

def frequency_label(n_with: int, n_total: int) -> str:
    """Label a finding's prevalence rather than implying a population estimate.

    Conventional thresholds from Consensual Qualitative Research (Hill et al.):
    *general* = all or all-but-one case; *typical* = more than half; *variant* =
    at least two but not more than half; *rare* = one.

    These are descriptive labels for the sample in hand. They are **not**
    prevalence estimates — see the rule of three for what non-observation licenses.
    """
    if n_total <= 0 or n_with <= 0:
        return "absent"
    if n_with >= n_total - 1:
        return "general"
    if n_with > n_total / 2:
        return "typical"
    if n_with >= 2:
        return "variant"
    return "rare"


# ---------------------------------------------------------------------------
# Disagreement routing (LOOPS.md: restart beats repair)
# ---------------------------------------------------------------------------

def route_disagreements(
    answers: dict[str, list[str | None]],
    unit_ids: list[str],
    restart_counts: dict[str, int] | None = None,
    max_restarts: int = 2,
) -> list[Disagreement]:
    """Route disagreeing units — restart the pass; escalate only on persistence.

    Human attention is the scarcest resource in the system, so a disagreement is
    *not* a reason to summon a person. Re-running the coding pass is cheap.
    Disagreement that survives ``max_restarts`` is evidence the **codebook** is
    defective — a contract error — and that *is* a human's job.
    """
    restart_counts = restart_counts or {}
    out: list[Disagreement] = []

    for idx, unit in enumerate(unit_ids):
        labels = {
            cid: vals[idx]
            for cid, vals in answers.items()
            if idx < len(vals) and vals[idx] is not None
        }
        if len(labels) < 2 or len(set(labels.values())) <= 1:
            continue

        n = restart_counts.get(unit, 0)
        if n >= max_restarts:
            action, reason = (
                RoutingAction.ESCALATE,
                f"disagreement persisted through {n} restarts — codebook defect (contract error)",
            )
        else:
            action, reason = (
                RoutingAction.RESTART,
                "coders disagree — re-code rather than spend human attention",
            )
        out.append(Disagreement(unit, labels, n, action, reason))

    return out


# ---------------------------------------------------------------------------
# The panel assessment
# ---------------------------------------------------------------------------

def assess_panel(
    answers: dict[str, list[str | None]],
    coders: list[Coder],
    unit_ids: list[str] | None = None,
    gold: list[str | None] | None = None,
    restart_counts: dict[str, int] | None = None,
) -> PanelReport:
    """Assess a coding panel, keeping agent agreement and human validity separate."""
    by_id = {c.id: c for c in coders}
    n_units = max((len(v) for v in answers.values()), default=0)
    unit_ids = unit_ids or [f"u{i}" for i in range(n_units)]
    notes: list[str] = []

    agent_ids = [c.id for c in coders if not c.is_gold_source and c.id in answers]
    agent_answers = {cid: answers[cid] for cid in agent_ids}

    # --- Agent-side agreement: a router, explicitly not validity. ---
    agent_alpha = None
    mean_kappa = None
    if len(agent_ids) >= 2:
        units_matrix = [
            [agent_answers[cid][i] if i < len(agent_answers[cid]) else None for cid in agent_ids]
            for i in range(n_units)
        ]
        agent_alpha = krippendorff_alpha(units_matrix)
        ks = []
        for i, a in enumerate(agent_ids):
            for b in agent_ids[i + 1:]:
                pairs = [
                    (x, y)
                    for x, y in zip(agent_answers[a], agent_answers[b])
                    if x is not None and y is not None
                ]
                if pairs:
                    k = cohens_kappa([x for x, _ in pairs], [y for _, y in pairs])
                    if k is not None:
                        ks.append(k)
        mean_kappa = sum(ks) / len(ks) if ks else None
        notes.append(
            "Agent-agent agreement is a disagreement router. It is NOT evidence of "
            "validity: correlated coders agree on their shared errors."
        )
        if agent_alpha is None:
            distinct = {v for vals in agent_answers.values() for v in vals if v is not None}
            if len(distinct) <= 1:
                notes.append(
                    "α not computable: every coder used a single category, so expected "
                    "disagreement is zero. This is a degenerate codebook, not agreement."
                )

    # --- Correlation, estimated rather than assumed. ---
    rho, rho_within, rho_cross = estimate_rho_from_agreement(agent_answers, by_id)
    if gold is not None:
        shared = estimate_rho_from_shared_error(agent_answers, gold)
        if shared is not None:
            rho = max(rho, shared)
            notes.append(
                f"ρ refined to {rho:.2f} using shared-error rate against gold "
                "(the honest estimator; agreement-based ρ is optimistic)."
            )
    if rho_within is not None and rho_cross is not None and rho_within > rho_cross:
        notes.append(
            f"Same-lineage coders agree more (ρ̂={rho_within:.2f}) than cross-lineage "
            f"(ρ̂={rho_cross:.2f}) — lineage diversity is the scarce resource, not coder count."
        )

    n_eff = n_eff_correlation(len(agent_ids), rho) if agent_ids else 0.0

    # --- Human-side: the only validity claim on offer. ---
    validity: dict[str, float] = {}
    gold_units = 0
    if gold is not None:
        gold_units = sum(1 for g in gold if g is not None)
        for cid in agent_ids:
            pairs = [
                (p, g)
                for p, g in zip(agent_answers[cid], gold)
                if p is not None and g is not None
            ]
            if pairs:
                k = cohens_kappa([p for p, _ in pairs], [g for _, g in pairs])
                if k is not None:
                    validity[cid] = k
        if not validity:
            notes.append("Gold supplied but no overlapping units — validity not computable.")
    else:
        notes.append(
            "NO human gold standard: validity is UNKNOWN. Agreement among agents "
            "cannot substitute. Draw a probability sample and have a human code it."
        )

    # --- Consensus structure over coders. ---
    consensus = assess_consensus(agent_answers) if len(agent_ids) >= 3 else None

    # --- CQR-style frequency labels over the consensus labelling. ---
    freq: dict[str, str] = {}
    if agent_ids:
        primary = gold if gold is not None else agent_answers[agent_ids[0]]
        counts: dict[str, int] = {}
        for v in primary:
            if v is not None:
                counts[v] = counts.get(v, 0) + 1
        total = sum(1 for v in primary if v is not None)
        freq = {label: frequency_label(c, total) for label, c in counts.items()}

    routing = route_disagreements(agent_answers, unit_ids, restart_counts)

    return PanelReport(
        n_units=n_units,
        coders=coders,
        agent_alpha=agent_alpha,
        mean_pairwise_kappa=mean_kappa,
        rho_estimated=rho,
        rho_within_lineage=rho_within,
        rho_cross_lineage=rho_cross,
        n_eff=n_eff,
        validity_vs_gold=validity,
        gold_units=gold_units,
        consensus=consensus,
        frequency_labels=freq,
        routing=routing,
        notes=notes,
    )
