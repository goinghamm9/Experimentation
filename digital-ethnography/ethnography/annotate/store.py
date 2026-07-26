"""Persistence for human gold coding.

Gold annotations are the only source of validity evidence in the system, so the
store enforces the properties that make them worth anything:

* **Blind by construction.** The store never holds a machine label alongside the
  unit being coded. An annotator who can see the model's answer is anchored by it,
  and the resulting "gold" measures agreement with the model rather than truth.
* **Probability sample, not convenience sample.** Units come from
  :func:`ethnography.rigor.probability_sample`, seeded and reproducible, so the
  same set can serve as both validity benchmark and PPI rectifier.
* **Append-only on disk.** One JSONL file, resumable after a crash — the
  ``findings.jsonl`` discipline applied to annotation.

Time-on-task is recorded because implausibly fast annotation is the standard
quality signal, and because it makes the cost of gold visible rather than assumed.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..schema import utcnow


@dataclass
class Annotation:
    unit_id: str
    label: str | None            # None = explicitly uncertain (not a skip)
    annotator: str
    codebook_version: str
    seconds_on_task: float
    note: str = ""
    recorded_at: str = field(default_factory=lambda: utcnow().isoformat())

    @property
    def is_uncertain(self) -> bool:
        return self.label is None


class GoldStore:
    """Append-only JSONL store of human annotations, keyed by (annotator, unit)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._records: list[Annotation] = []
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    self._records.append(Annotation(**json.loads(line)))

    def add(self, annotation: Annotation) -> None:
        """Append an annotation. Re-coding a unit supersedes the earlier record."""
        self._records.append(annotation)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(annotation), default=str) + "\n")

    def annotations(self, annotator: str | None = None) -> list[Annotation]:
        if annotator is None:
            return list(self._records)
        return [a for a in self._records if a.annotator == annotator]

    def latest_by_unit(self, annotator: str) -> dict[str, Annotation]:
        """Most recent annotation per unit for one annotator (later supersedes)."""
        out: dict[str, Annotation] = {}
        for a in self._records:
            if a.annotator == annotator:
                out[a.unit_id] = a
        return out

    def completed_units(self, annotator: str) -> set[str]:
        return set(self.latest_by_unit(annotator))

    def annotators(self) -> list[str]:
        return sorted({a.annotator for a in self._records})

    def gold_vector(self, unit_ids: list[str], annotator: str | None = None) -> list[str | None]:
        """Align annotations to ``unit_ids`` for :func:`assess_panel`.

        Uncertain annotations and un-coded units both become ``None``, which the
        agreement estimators correctly treat as missing rather than as a category.
        """
        if annotator is None:
            merged: dict[str, Annotation] = {}
            for a in self._records:
                merged[a.unit_id] = a
            by_unit = merged
        else:
            by_unit = self.latest_by_unit(annotator)
        return [by_unit[u].label if u in by_unit else None for u in unit_ids]

    def quality_flags(self, min_seconds: float = 2.0) -> list[str]:
        """Surface quality concerns rather than silently averaging them in."""
        flags: list[str] = []
        for annotator in self.annotators():
            anns = self.latest_by_unit(annotator).values()
            if not anns:
                continue
            fast = [a for a in anns if a.seconds_on_task < min_seconds]
            if fast:
                flags.append(
                    f"{annotator}: {len(fast)}/{len(anns)} units coded in under "
                    f"{min_seconds:.0f}s — implausibly fast, review before trusting"
                )
            uncertain = [a for a in anns if a.is_uncertain]
            if len(uncertain) > len(anns) * 0.3:
                flags.append(
                    f"{annotator}: {len(uncertain)}/{len(anns)} marked uncertain — "
                    "the codebook may not fit the material (a contract defect)"
                )
        return flags

    def __len__(self) -> int:
        return len(self._records)
