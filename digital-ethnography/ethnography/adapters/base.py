"""Adapter contract for ingesting from *any* digital system.

A source adapter's only job is to turn some external shape (an analytics export,
a reviews dump, an interview folder) into a stream of :class:`RawRecord`s. It
does **not** decide what is ethical to keep — that is the governance gate's job.
The adapter must, however, (a) declare the data category of what it emits and
(b) provide the raw identifier so the pseudonymizer can hash it.

To support a new system, implement :class:`SourceAdapter.collect`. Everything
downstream — ethics, coding, journeys, personas, reporting — is reused as-is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Protocol, runtime_checkable

from ..schema import (
    DataCategory,
    Observation,
    ObservationKind,
    utcnow,
)
from ..ethics.redaction import Pseudonymizer


@dataclass
class RawRecord:
    """A pre-pseudonymization record straight from a source."""

    raw_identifier: str
    kind: ObservationKind
    category: DataCategory
    timestamp: datetime
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    text: str | None = None


@runtime_checkable
class SourceAdapter(Protocol):
    name: str

    def collect(self) -> Iterable[RawRecord]:
        ...


def to_observations(
    records: Iterable[RawRecord],
    pseudonymizer: Pseudonymizer,
) -> list[Observation]:
    """Pseudonymize raw records into internal observations.

    The raw identifier is consumed here and never propagated. The observation id
    is derived from the pseudonymous id + a monotonic counter, so it is stable
    within a run but carries no external identity.
    """
    observations: list[Observation] = []
    counter: dict[str, int] = {}
    for rec in records:
        pid = pseudonymizer.pid(rec.raw_identifier)
        n = counter.get(pid, 0)
        counter[pid] = n + 1
        observations.append(
            Observation(
                id=f"{pid}:{rec.source}:{n}",
                pid=pid,
                source=rec.source,
                kind=rec.kind,
                timestamp=rec.timestamp,
                category=rec.category,
                payload=dict(rec.payload),
                text=rec.text,
            )
        )
    return observations
