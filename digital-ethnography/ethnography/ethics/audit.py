"""Tamper-evident, append-only audit log.

Ethical research must be *accountable*: at any later point a reviewer (or the
participant themselves) should be able to see exactly what was collected, why it
was permitted, what was redacted, and what a machine inferred from it.

Each entry is hash-chained to the previous one (a tiny blockchain-of-one-file),
so silent after-the-fact edits are detectable via :meth:`AuditLog.verify`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from ..schema import utcnow


@dataclass
class AuditEvent:
    ts: str
    actor: str
    action: str
    target: str
    detail: dict[str, Any]
    prev_hash: str
    hash: str = ""

    def compute_hash(self) -> str:
        body = json.dumps(
            {
                "ts": self.ts,
                "actor": self.actor,
                "action": self.action,
                "target": self.target,
                "detail": self.detail,
                "prev_hash": self.prev_hash,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(body.encode("utf-8")).hexdigest()


class AuditLog:
    """In-memory, hash-chained audit trail.

    The genesis hash anchors the chain; every subsequent event commits to the
    previous event's hash, so any tampering breaks :meth:`verify`.
    """

    GENESIS = "0" * 64

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(
        self,
        action: str,
        target: str,
        actor: str = "system",
        **detail: Any,
    ) -> AuditEvent:
        prev = self._events[-1].hash if self._events else self.GENESIS
        event = AuditEvent(
            ts=utcnow().isoformat(),
            actor=actor,
            action=action,
            target=target,
            detail=detail,
            prev_hash=prev,
        )
        event.hash = event.compute_hash()
        self._events.append(event)
        return event

    def verify(self) -> bool:
        """Return True iff the chain is internally consistent and untampered."""
        prev = self.GENESIS
        for event in self._events:
            if event.prev_hash != prev:
                return False
            if event.compute_hash() != event.hash:
                return False
            prev = event.hash
        return True

    def events(self) -> list[AuditEvent]:
        return list(self._events)

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._events:
            counts[e.action] = counts.get(e.action, 0) + 1
        return counts
