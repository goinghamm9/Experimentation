"""SQLModel tables: emails (sources), candidates, projects, actions (audit log).

`emails` also holds Google Meet transcripts (source_type="transcript") — many
tickets originate in client meetings, and transcript emails arrive through the
same Gmail label. JSON-ish fields (labels, acceptance_criteria) are stored as
JSON strings; use the helpers on Candidate to read/write them.
"""
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SourceType(str, Enum):
    EMAIL = "email"
    TRANSCRIPT = "transcript"


class EmailStatus(str, Enum):
    INGESTED = "ingested"      # stored, no candidate yet
    DRAFTED = "drafted"        # candidate generated
    NEEDS_REVIEW = "needs_review"  # generation failed; surface for manual handling


class CandidateStatus(str, Enum):
    PENDING = "pending"
    EDITED = "edited"
    APPROVED = "approved"
    REJECTED = "rejected"


class Email(SQLModel, table=True):
    __tablename__ = "emails"

    id: Optional[int] = Field(default=None, primary_key=True)
    gmail_message_id: str = Field(unique=True, index=True)
    thread_id: str = ""
    sender: str = ""
    subject: str = ""
    body: str = ""
    source_type: str = SourceType.EMAIL.value
    attachments_meta: str = "[]"  # JSON list of {filename, mime_type, size}
    received_at: datetime = Field(default_factory=utcnow)
    status: str = EmailStatus.INGESTED.value


class Candidate(SQLModel, table=True):
    __tablename__ = "candidates"

    id: Optional[int] = Field(default=None, primary_key=True)
    email_id: int = Field(foreign_key="emails.id", index=True)
    project_key: str = ""
    issue_type: str = "Task"
    summary: str = ""
    description: str = ""
    priority: str = "Medium"
    labels: str = "[]"               # JSON list[str]
    acceptance_criteria: str = "[]"  # JSON list[str]
    confidence: float = 0.0
    rationale: str = ""
    prompt_used: str = ""            # exact assembled prompt, kept for tuning
    raw_response: str = ""           # exact model output, kept for tuning
    status: str = CandidateStatus.PENDING.value
    jira_issue_key: Optional[str] = None
    reject_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @property
    def labels_list(self) -> list[str]:
        return json.loads(self.labels or "[]")

    @labels_list.setter
    def labels_list(self, value: list[str]) -> None:
        self.labels = json.dumps(value)

    @property
    def acceptance_criteria_list(self) -> list[str]:
        return json.loads(self.acceptance_criteria or "[]")

    @acceptance_criteria_list.setter
    def acceptance_criteria_list(self, value: list[str]) -> None:
        self.acceptance_criteria = json.dumps(value)


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    key: str = Field(primary_key=True)
    name: str = ""
    config_path: str = ""
    enabled: bool = False  # boards are wired incrementally; only MSA at first


class Action(SQLModel, table=True):
    """Append-only audit log. Never update or delete rows."""
    __tablename__ = "actions"

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str  # "email" | "candidate"
    entity_id: int
    action: str       # ingested | drafted | edited | approved | rejected | ...
    detail: str = ""
    created_at: datetime = Field(default_factory=utcnow)
