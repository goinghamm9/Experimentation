"""Adapter for qualitative text: reviews, interviews, forum/support posts.

Qualitative traces are where "thick description" comes from — the situated,
first-person account of what using the system *felt* like. Accepts JSONL where
each line carries free text::

    {"author": "reviewer_9", "text": "The onboarding was confusing...",
     "ts": "2026-01-03T12:00:00Z", "rating": 2, "channel": "app_store"}

The text is emitted as-is; the governance gate redacts PII before retention.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..schema import DataCategory, ObservationKind
from .base import RawRecord
from .events import _parse_ts  # reuse the tolerant timestamp parser


@dataclass
class QualitativeAdapter:
    path: str | Path
    source: str = "qualitative"
    id_field: str = "author"
    text_field: str = "text"
    ts_field: str = "ts"
    kind: ObservationKind = ObservationKind.UTTERANCE
    category: DataCategory = DataCategory.CONTENT

    @property
    def name(self) -> str:
        return self.source

    def collect(self) -> Iterable[RawRecord]:
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                raw_id = str(row.get(self.id_field, "")).strip()
                text = (row.get(self.text_field) or "").strip()
                if not raw_id or not text:
                    continue
                payload = {
                    k: v
                    for k, v in row.items()
                    if k not in {self.id_field, self.text_field}
                }
                yield RawRecord(
                    raw_identifier=raw_id,
                    kind=self.kind,
                    category=self.category,
                    timestamp=_parse_ts(row.get(self.ts_field)),
                    source=self.source,
                    payload=payload,
                    text=text,
                )
