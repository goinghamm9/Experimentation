from core.audit import actions_for
from core.ingest import ingest_message
from core.models import EmailStatus, SourceType


def test_ingest_stores_email_and_audit_entry(session):
    email, created = ingest_message(
        session,
        gmail_message_id="msg-001",
        sender="client@example.com",
        subject="Bug: login broken",
        body="The login page errors out.",
        thread_id="thread-1",
        attachments_meta=[{"filename": "screenshot.png", "mime_type": "image/png", "size": 1024}],
    )
    assert created
    assert email.id is not None
    assert email.status == EmailStatus.INGESTED.value
    assert "screenshot.png" in email.attachments_meta

    log = actions_for(session, "email", email.id)
    assert [a.action for a in log] == ["ingested"]


def test_ingest_is_idempotent(session):
    first, created1 = ingest_message(session, "msg-dup", "a@b.c", "subj", "body")
    second, created2 = ingest_message(session, "msg-dup", "a@b.c", "subj", "body")
    assert created1 and not created2
    assert first.id == second.id
    # no duplicate audit entries either
    assert len(actions_for(session, "email", first.id)) == 1


def test_ingest_transcript_source_type(session):
    email, created = ingest_message(
        session,
        gmail_message_id="meet-001",
        sender="meet-transcripts@google.com",
        subject="Transcript: Weekly sync with MPR",
        body="Operator: ...\nClient: we need the export button fixed...",
        source_type=SourceType.TRANSCRIPT.value,
    )
    assert created
    assert email.source_type == "transcript"
