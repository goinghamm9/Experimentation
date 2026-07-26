"""A deterministic keyword coder, wrapped in the panel contract.

Two jobs. It keeps the package usable with no network and no API key, and it acts
as a **baseline**: a model coder that cannot beat keyword matching against human
gold is not earning its cost. The corpus's warning applies to the whole product —
a multi-agent pipeline should be cost-matched against a simple baseline before any
claim is made for it.

Its evidence spans are exact substrings by construction, so it verifies trivially.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..schema import Observation
from .base import CodedUnit, CodingResult


@dataclass
class DeterministicCoder:
    codebook: dict[str, list[str]]
    id: str = "deterministic"
    lineage: str = "rules"
    notes: list[str] = field(default_factory=list)

    def code_one(self, obs: Observation) -> CodedUnit:
        haystack = " ".join(
            filter(None, [obs.text or "", str(obs.payload.get("event", "")) if obs.payload else ""])
        )
        low = haystack.lower()
        best: tuple[str, str] | None = None
        for label in sorted(self.codebook):
            for trigger in self.codebook[label]:
                idx = low.find(trigger.lower())
                if idx >= 0:
                    span = haystack[idx: idx + len(trigger)]
                    # Prefer the longest trigger match: more specific evidence.
                    if best is None or len(span) > len(best[1]):
                        best = (label, span)
        if best is None:
            return CodedUnit(obs.id, None, rationale="no trigger matched")

        label, span = best
        # Only claim a verified span when the evidence came from the free text.
        from_text = bool(obs.text) and span.lower() in (obs.text or "").lower()
        return CodedUnit(
            unit_id=obs.id,
            label=label,
            evidence=span if from_text else None,
            confidence=1.0,
            span_verified=from_text,
            rationale=f"matched trigger {span!r}",
        )

    def code(self, observations: list[Observation]) -> CodingResult:
        units = [self.code_one(o) for o in observations]
        result = CodingResult(
            coder_id=self.id,
            lineage=self.lineage,
            units=units,
            hypotheses_considered=len(observations) * (len(self.codebook) + 1),
            notes=list(self.notes),
        )
        result.notes.extend(result.quality_flags())
        return result
