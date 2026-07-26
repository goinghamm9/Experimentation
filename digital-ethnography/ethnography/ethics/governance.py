"""The data governance gate.

This is the single choke point every observation must pass before analysis.
It composes the other ethics primitives into one enforced policy:

1. **Consent** — the participant permitted this category for this study/purpose.
2. **Purpose limitation** — implicit in the consent check (purpose must match).
3. **Data minimization** — the study declares which categories it may use;
   anything outside that set is dropped even if consent existed.
4. **Retention** — observations past their retention horizon are dropped.
5. **Redaction** — free text is scrubbed of PII before it is ever retained.
6. **Special-category care** — SENSITIVE data is refused unless the study
   explicitly allows it, and always logged.

Every decision — kept, dropped, redacted — is written to the audit log with a
reason, so the corpus that reaches analysis is fully accountable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from ..schema import Corpus, DataCategory, Observation, Participant, Study, utcnow
from .audit import AuditLog
from .consent import ConsentRegistry
from .redaction import redact_text


@dataclass
class GateReport:
    kept: int = 0
    dropped_no_consent: int = 0
    dropped_minimization: int = 0
    dropped_retention: int = 0
    dropped_sensitive: int = 0
    redacted: int = 0

    @property
    def total_seen(self) -> int:
        return (
            self.kept
            + self.dropped_no_consent
            + self.dropped_minimization
            + self.dropped_retention
            + self.dropped_sensitive
        )


class GovernanceGate:
    def __init__(self, consent: ConsentRegistry, audit: AuditLog) -> None:
        self._consent = consent
        self._audit = audit

    def apply(
        self,
        study: Study,
        observations: list[Observation],
        participants: dict[str, Participant],
    ) -> tuple[Corpus, GateReport]:
        report = GateReport()
        now = utcnow()
        kept: list[Observation] = []

        for obs in observations:
            # 4. Retention horizon.
            horizon = obs.timestamp + timedelta(days=study.retention_days)
            if now >= horizon:
                report.dropped_retention += 1
                self._audit.record("drop", obs.id, reason="retention_expired")
                continue

            # 3. Data minimization — study must allow the category.
            if obs.category not in study.allowed_categories:
                report.dropped_minimization += 1
                self._audit.record(
                    "drop", obs.id, reason="minimization", category=obs.category.value
                )
                continue

            # 6. Special-category data requires explicit study allowance.
            if obs.category == DataCategory.SENSITIVE and (
                DataCategory.SENSITIVE not in study.allowed_categories
            ):
                report.dropped_sensitive += 1
                self._audit.record("drop", obs.id, reason="sensitive_not_allowed")
                continue

            # 1 & 2. Consent + purpose limitation.
            if not self._consent.permits(obs.pid, study, obs.category, at=now):
                report.dropped_no_consent += 1
                self._audit.record("drop", obs.id, reason="no_consent")
                continue

            # 5. Redact free text before retaining anything.
            if obs.text:
                result = redact_text(obs.text)
                if result.anything_redacted:
                    obs.text = result.text
                    obs.redacted = True
                    report.redacted += 1
                    self._audit.record(
                        "redact", obs.id, categories=list(result.counts.keys())
                    )

            obs.retention_until = horizon
            kept.append(obs)
            report.kept += 1
            self._audit.record("keep", obs.id, category=obs.category.value)

        # Only participants with at least one kept observation survive.
        kept_pids = {o.pid for o in kept}
        surviving = {pid: participants[pid] for pid in kept_pids if pid in participants}
        for pid in kept_pids:
            surviving.setdefault(pid, Participant(pid=pid))

        corpus = Corpus(study=study, participants=surviving, observations=kept)
        self._audit.record(
            "gate_complete",
            study.id,
            kept=report.kept,
            dropped=report.total_seen - report.kept,
            redacted=report.redacted,
        )
        return corpus, report

    def erase_participant(self, corpus: Corpus, pid: str) -> int:
        """Right-to-erasure: remove all trace of a participant from the corpus.

        Returns the number of observations removed. The audit log retains a
        record that an erasure happened (but not the erased content).
        """
        before = len(corpus.observations)
        corpus.observations = [o for o in corpus.observations if o.pid != pid]
        corpus.participants.pop(pid, None)
        removed = before - len(corpus.observations)
        self._audit.record("erase", pid, observations_removed=removed)
        return removed
