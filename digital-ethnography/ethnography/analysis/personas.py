"""Persona synthesis.

Personas are *aggregate portraits*, never real individuals. We cluster
participants by their behavioral signature — the set of codes that apply to
their observations — and describe each cluster. Because participants are already
pseudonymous and a persona requires a minimum membership, no persona can be
traced back to one person (a k-anonymity floor).

The clustering is deterministic: participants sharing their dominant code land
in the same persona. Small clusters below ``k_min`` are folded into a residual
"long-tail" persona so we never publish a portrait describing a single user.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from ..schema import Code, Corpus, Persona, Provenance


def synthesize(
    corpus: Corpus,
    codes: list[Code],
    k_min: int = 3,
) -> list[Persona]:
    # Map each observation to the codes applied to it.
    obs_to_codes: dict[str, list[str]] = defaultdict(list)
    for code in codes:
        for oid in code.observation_ids:
            obs_to_codes[oid].append(code.label)

    # Each participant's dominant code = most frequent code across their obs.
    pid_signature: dict[str, list[str]] = {}
    pid_dominant: dict[str, str] = {}
    for pid in corpus.participants:
        counter: Counter[str] = Counter()
        for o in corpus.by_participant(pid):
            counter.update(obs_to_codes.get(o.id, []))
        if counter:
            pid_signature[pid] = [c for c, _ in counter.most_common(3)]
            pid_dominant[pid] = counter.most_common(1)[0][0]
        else:
            pid_dominant[pid] = "_uncoded"
            pid_signature[pid] = []

    clusters: dict[str, list[str]] = defaultdict(list)
    for pid, dom in pid_dominant.items():
        clusters[dom].append(pid)

    personas: list[Persona] = []
    residual: list[str] = []
    for dominant, pids in clusters.items():
        if len(pids) < k_min or dominant == "_uncoded":
            residual.extend(pids)
            continue
        sig = Counter()
        for pid in pids:
            sig.update(pid_signature[pid])
        personas.append(
            Persona(
                label=_persona_label(dominant),
                description=(
                    f"Participants whose behavior centers on '{dominant}'. "
                    f"Shared signals: {', '.join(c for c, _ in sig.most_common(3))}."
                ),
                member_pids=sorted(pids),
                signature_codes=[c for c, _ in sig.most_common(5)],
            )
        )

    if len(residual) >= k_min:
        personas.append(
            Persona(
                label="The Long Tail",
                description=(
                    "Participants with diffuse or uncoded behavior; individually "
                    "varied, grouped to preserve anonymity."
                ),
                member_pids=sorted(residual),
            )
        )

    return sorted(personas, key=lambda p: -p.size)


def _persona_label(dominant_code: str) -> str:
    pretty = dominant_code.replace("emergent:", "").replace("_", " ").replace(":", " ").title()
    return f"The {pretty} User"
