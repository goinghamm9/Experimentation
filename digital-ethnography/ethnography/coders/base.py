"""Coder contract, evidence verification, and refusal accounting.

Every coder — deterministic, model-backed, or human — produces the same shape, so
the panel arithmetic never has to know what produced a label.

Two properties are enforced here rather than trusted:

* **Evidence spans are verified mechanically.** A model that cites a quote which
  does not appear in the source has fabricated it. This is checkable without an
  oracle, which makes it the one hallucination gate that actually closes, and it
  is applied before a label is allowed to count.
* **Refusals are counted, not swallowed.** Silent refusal on stigmatised material
  is coverage loss that looks like a finding — the corpus is emphatic that absence
  of a code must never be read as absence of the phenomenon.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..schema import Observation

UNCERTAIN = None  # a label of None means "the codebook does not fit this unit"


def _normalise(text: str) -> str:
    """Fold whitespace, case, and unicode so span checks survive cosmetic drift."""
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def verify_span(evidence: str | None, source_text: str | None) -> bool:
    """True iff ``evidence`` genuinely occurs in ``source_text``.

    Deliberately strict about content and lenient about formatting: a coder may
    normalise whitespace or case, but may not invent, paraphrase, or splice.
    """
    if not evidence or not source_text:
        return False
    return _normalise(evidence) in _normalise(source_text)


@dataclass
class CodedUnit:
    unit_id: str
    label: str | None                 # None = uncertain / not covered by the codebook
    evidence: str | None = None       # verbatim span from the source
    confidence: float = 1.0
    refused: bool = False
    span_verified: bool = False
    rationale: str = ""

    @property
    def is_usable(self) -> bool:
        """A label counts only if it is present, not refused, and grounded.

        Behavioural units carry no free text, so a label with no evidence is
        admissible there; the caller signals that by leaving ``evidence`` None
        while ``span_verified`` stays False. :meth:`CodingResult.usable_labels`
        applies the text-dependent rule.
        """
        return self.label is not None and not self.refused


@dataclass
class CodingResult:
    coder_id: str
    lineage: str
    units: list[CodedUnit] = field(default_factory=list)
    hypotheses_considered: int = 0     # feeds the search ledger
    cost_usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    notes: list[str] = field(default_factory=list)

    def label_vector(self, unit_ids: list[str], require_evidence: bool = True) -> list[str | None]:
        """Align to ``unit_ids`` for the panel, dropping ungrounded labels.

        An unverified span means the quote was not found in the source, so the
        label is treated as missing rather than as evidence. That is the point of
        the gate: a fabricated citation must not be able to move a validity number.
        """
        by_id = {u.unit_id: u for u in self.units}
        out: list[str | None] = []
        for uid in unit_ids:
            u = by_id.get(uid)
            if u is None or not u.is_usable:
                out.append(None)
            elif require_evidence and u.evidence is not None and not u.span_verified:
                out.append(None)
            else:
                out.append(u.label)
        return out

    @property
    def refusal_rate(self) -> float:
        return (sum(1 for u in self.units if u.refused) / len(self.units)) if self.units else 0.0

    @property
    def fabrication_rate(self) -> float:
        """Share of cited spans that could not be found in the source."""
        cited = [u for u in self.units if u.evidence]
        if not cited:
            return 0.0
        return sum(1 for u in cited if not u.span_verified) / len(cited)

    @property
    def uncertain_rate(self) -> float:
        return (
            sum(1 for u in self.units if u.label is None and not u.refused) / len(self.units)
        ) if self.units else 0.0

    def quality_flags(self) -> list[str]:
        flags: list[str] = []
        if self.refusal_rate > 0.02:
            flags.append(
                f"{self.coder_id}: refused {self.refusal_rate:.1%} of units — "
                "coverage loss that will look like absence of the phenomenon"
            )
        if self.fabrication_rate > 0.0:
            flags.append(
                f"{self.coder_id}: {self.fabrication_rate:.1%} of cited spans were NOT "
                "found in the source — fabricated evidence; those labels were dropped"
            )
        if self.uncertain_rate > 0.30:
            flags.append(
                f"{self.coder_id}: {self.uncertain_rate:.1%} uncertain — the codebook "
                "may not fit the material (a contract defect, not a coder defect)"
            )
        return flags


@runtime_checkable
class Coder(Protocol):
    """Anything that can assign codebook labels to observations."""

    id: str
    lineage: str

    def code(self, observations: list[Observation]) -> CodingResult:
        ...
