"""Ingest sources (emails / meeting transcripts) into SQLite.

ingest_message is the single entry point used by the Gmail poller, the test
harness, and the manual transcript-paste form — so idempotency lives in one
place: a gmail_message_id is never ingested twice.
"""
import json
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from core.audit import record_action
from core.models import Email, EmailStatus, SourceType, utcnow


def ingest_message(
    session: Session,
    gmail_message_id: str,
    sender: str,
    subject: str,
    body: str,
    thread_id: str = "",
    source_type: str = SourceType.EMAIL.value,
    attachments_meta: Optional[list[dict]] = None,
    received_at: Optional[datetime] = None,
) -> tuple[Email, bool]:
    """Store a message. Returns (email, created). Never double-ingests an id."""
    existing = session.exec(
        select(Email).where(Email.gmail_message_id == gmail_message_id)
    ).first()
    if existing:
        return existing, False

    email = Email(
        gmail_message_id=gmail_message_id,
        thread_id=thread_id,
        sender=sender,
        subject=subject,
        body=body,
        source_type=source_type,
        attachments_meta=json.dumps(attachments_meta or []),
        received_at=received_at or utcnow(),
        status=EmailStatus.INGESTED.value,
    )
    session.add(email)
    session.flush()  # assign id for the audit entry
    record_action(session, "email", email.id, "ingested", f"source_type={source_type} from={sender}")
    return email, True
