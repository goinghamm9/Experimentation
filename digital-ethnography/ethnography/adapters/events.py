"""Adapter for behavioral event / session logs.

Accepts JSONL where each line is one interaction event. This is the canonical
"digital trace" of ethnography: what a person actually did, in sequence, in the
system's own environment. Expected (flexible) fields per line::

    {"user": "u_42", "event": "checkout_start", "ts": "2026-01-02T10:04:00Z",
     "screen": "cart", "device": "ios", "props": {...}}

Field names are configurable so the adapter fits arbitrary analytics exports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..schema import DataCategory, ObservationKind
from .base import RawRecord


@dataclass
class EventLogAdapter:
    path: str | Path
    source: str = "events"
    id_field: str = "user"
    event_field: str = "event"
    ts_field: str = "ts"
    category: DataCategory = DataCategory.BEHAVIORAL

    @property
    def name(self) -> str:
        return self.source

    def collect(self) -> Iterable[RawRecord]:
        for line in _read_jsonl(self.path):
            raw_id = str(line.get(self.id_field, "")).strip()
            if not raw_id:
                continue  # cannot pseudonymize without an identifier; skip safely
            ts = _parse_ts(line.get(self.ts_field))
            event_name = line.get(self.event_field, "unknown")
            payload = {k: v for k, v in line.items() if k != self.id_field}
            yield RawRecord(
                raw_identifier=raw_id,
                kind=ObservationKind.EVENT,
                category=self.category,
                timestamp=ts,
                source=self.source,
                payload={"event": event_name, **payload},
            )


def _read_jsonl(path: str | Path) -> Iterable[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _parse_ts(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        v = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(v)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    # Fall back to epoch-agnostic "now-unknown": use a fixed anchor so retention
    # logic still applies deterministically rather than silently passing.
    return datetime(1970, 1, 1, tzinfo=timezone.utc)
