"""Consent registry and gating.

The foundational rule of this system: **no observation is ever processed for a
participant who has not given valid, unexpired, purpose-matching consent for the
relevant data category.** Consent is not a checkbox appended at the end; it is a
gate that data must pass through before analysis can see it.

A :class:`ConsentRecord` binds a *pseudonymous* participant to a study, a set of
permitted data categories, and a set of permitted purposes, with an expiry.
Withdrawal is first-class: a withdrawn record permits nothing, which lets the
pipeline honor a right-to-erasure request by cascading deletion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..schema import DataCategory, Study, utcnow


@dataclass
class ConsentRecord:
    pid: str
    study_id: str
    purposes: set[str]
    categories: set[DataCategory]
    granted_at: datetime
    expires_at: datetime | None = None
    withdrawn: bool = False

    def is_active(self, at: datetime | None = None) -> bool:
        at = at or utcnow()
        if self.withdrawn:
            return False
        if self.expires_at is not None and at >= self.expires_at:
            return False
        return at >= self.granted_at


class ConsentRegistry:
    """Holds consent records and answers the only question that matters:
    *may this data category be processed for this participant, for this study
    and purpose, right now?*
    """

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], ConsentRecord] = {}

    def grant(self, record: ConsentRecord) -> None:
        self._records[(record.pid, record.study_id)] = record

    def withdraw(self, pid: str, study_id: str) -> bool:
        """Record a withdrawal. Returns True if a record existed to withdraw."""
        rec = self._records.get((pid, study_id))
        if rec is None:
            return False
        rec.withdrawn = True
        return True

    def get(self, pid: str, study_id: str) -> ConsentRecord | None:
        return self._records.get((pid, study_id))

    def permits(
        self,
        pid: str,
        study: Study,
        category: DataCategory,
        at: datetime | None = None,
    ) -> bool:
        rec = self._records.get((pid, study.id))
        if rec is None or not rec.is_active(at):
            return False
        if study.purpose not in rec.purposes:
            return False
        return category in rec.categories

    def consented_pids(self, study_id: str, at: datetime | None = None) -> set[str]:
        return {
            pid
            for (pid, sid), rec in self._records.items()
            if sid == study_id and rec.is_active(at)
        }
