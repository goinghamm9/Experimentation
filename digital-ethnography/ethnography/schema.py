"""Internal normalized data model for digital ethnographic research.

Every source of data about a digital system is reduced to a small, uniform
vocabulary so that the ethics gate and the analysis stages never have to know
where an observation came from. The vocabulary is deliberately close to how
field researchers actually think:

    Study        -> the research project, its questions, its ethical basis
    Participant  -> a *pseudonymous* subject (raw identity is never stored)
    Observation  -> a single situated trace: an event, an utterance, an artifact
    Code / Theme -> interpretive labels produced during analysis
    Journey      -> one participant's ordered path through the system
    Persona      -> a synthesized, aggregate portrait (never a real person)

All analysis artifacts carry *provenance* so a human reviewer can always tell
what a machine inferred versus what was directly observed.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    """Timezone-aware 'now'. Centralised so tests can monkeypatch it."""
    return datetime.now(timezone.utc)


class DataCategory(str, enum.Enum):
    """Coarse categories of data, used for consent scoping and minimization.

    Consent is granted *per category*, and the governance policy drops any
    observation whose category the participant did not agree to share.
    """

    BEHAVIORAL = "behavioral"          # clicks, screens, navigation, timing
    CONTENT = "content"                # text the participant authored
    DERIVED = "derived"                # sentiment, inferred intent, etc.
    TECHNICAL = "technical"            # device, os, app version
    SENSITIVE = "sensitive"            # anything special-category; handled strictly


class ObservationKind(str, enum.Enum):
    EVENT = "event"            # a behavioral trace (a tap, a page view)
    UTTERANCE = "utterance"    # something the participant said/wrote
    ARTIFACT = "artifact"      # a produced object (a review, a screenshot ref)


class Provenance(str, enum.Enum):
    """How an interpretive artifact came to exist."""

    OBSERVED = "observed"              # directly present in source data
    DETERMINISTIC = "deterministic"   # produced by explicit, reproducible rules
    LLM_ASSISTED = "llm_assisted"     # drafted by a language model, needs review


@dataclass
class Study:
    """The research project and, crucially, its ethical charter."""

    id: str
    title: str
    purpose: str                       # the single declared purpose (purpose limitation)
    research_questions: list[str] = field(default_factory=list)
    allowed_categories: set[DataCategory] = field(
        default_factory=lambda: {DataCategory.BEHAVIORAL, DataCategory.CONTENT}
    )
    retention_days: int = 90           # observations older than this are dropped
    llm_enrichment: bool = False       # opt-in; deterministic core works without it


@dataclass
class Participant:
    """A pseudonymous subject.

    ``pid`` is a salted hash of whatever raw identifier the source used. The raw
    identifier is never stored anywhere in the system.
    """

    pid: str
    first_seen: datetime = field(default_factory=utcnow)
    attributes: dict[str, Any] = field(default_factory=dict)  # minimized, non-identifying


@dataclass
class Observation:
    """A single situated trace about a participant using the system."""

    id: str
    pid: str
    source: str
    kind: ObservationKind
    timestamp: datetime
    category: DataCategory
    payload: dict[str, Any] = field(default_factory=dict)
    text: str | None = None            # free text (already redaction-eligible)
    retention_until: datetime | None = None
    redacted: bool = False


@dataclass
class Code:
    """An interpretive label applied to one or more observations (open coding)."""

    label: str
    definition: str
    observation_ids: list[str] = field(default_factory=list)
    provenance: Provenance = Provenance.DETERMINISTIC
    confidence: float = 1.0

    @property
    def needs_review(self) -> bool:
        return self.provenance == Provenance.LLM_ASSISTED


@dataclass
class Theme:
    """A cluster of codes into a higher-order pattern (axial coding)."""

    label: str
    description: str
    code_labels: list[str] = field(default_factory=list)
    observation_ids: list[str] = field(default_factory=list)
    provenance: Provenance = Provenance.DETERMINISTIC

    @property
    def prevalence(self) -> int:
        return len(set(self.observation_ids))


@dataclass
class FrictionPoint:
    observation_id: str
    reason: str
    severity: float  # 0..1


@dataclass
class Journey:
    """One participant's ordered path through the digital system."""

    pid: str
    step_ids: list[str] = field(default_factory=list)
    friction: list[FrictionPoint] = field(default_factory=list)


@dataclass
class Persona:
    """A synthesized aggregate portrait. Never a real individual."""

    label: str
    description: str
    member_pids: list[str] = field(default_factory=list)
    signature_codes: list[str] = field(default_factory=list)
    provenance: Provenance = Provenance.DETERMINISTIC

    @property
    def size(self) -> int:
        return len(set(self.member_pids))


@dataclass
class ThickDescription:
    """Narrative interpretation of a theme in its situated context."""

    theme_label: str
    narrative: str
    provenance: Provenance = Provenance.DETERMINISTIC

    @property
    def needs_review(self) -> bool:
        return self.provenance == Provenance.LLM_ASSISTED


@dataclass
class Corpus:
    """The working set carried through the pipeline after the ethics gate."""

    study: Study
    participants: dict[str, Participant] = field(default_factory=dict)
    observations: list[Observation] = field(default_factory=list)

    def by_participant(self, pid: str) -> list[Observation]:
        return [o for o in self.observations if o.pid == pid]
