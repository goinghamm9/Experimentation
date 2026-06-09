from pathlib import Path

from sqlmodel import select

from core.gmail_client import classify_source
from core.llm import StubLLM
from core.models import Candidate, CandidateStatus, Email
from scripts.harness import FIXTURES_DIR, run_fixture
from scripts.poller import poll_once


class FakeGmail:
    def __init__(self, messages):
        self.messages = messages

    def fetch_labeled_messages(self):
        return self.messages


MESSAGES = [
    {"gmail_message_id": "live-1", "thread_id": "t1", "sender": "ops@mpr.org",
     "subject": "Search is down", "body": "Search returns 500s since 9am.", "source_type": "email"},
    {"gmail_message_id": "live-2", "thread_id": "t2", "sender": "meet-recordings-noreply@google.com",
     "subject": "Transcript: sync", "body": "Client: we agreed to add SSO.", "source_type": "transcript"},
]


def test_poll_once_ingests_and_drafts(session):
    stats = poll_once(session, FakeGmail(MESSAGES), StubLLM())
    # the email drafts 1 candidate; the transcript drafts 2 (one per work item)
    assert stats == {"seen": 2, "ingested": 2, "drafted": 3, "needs_review": 0}
    candidates = session.exec(select(Candidate)).all()
    assert len(candidates) == 3
    assert all(c.status == CandidateStatus.PENDING.value for c in candidates)
    assert all(c.project_key == "MSA" for c in candidates)  # default board


def test_poll_twice_is_idempotent(session):
    poll_once(session, FakeGmail(MESSAGES), StubLLM())
    stats = poll_once(session, FakeGmail(MESSAGES), StubLLM())
    assert stats["ingested"] == 0 and stats["drafted"] == 0
    assert len(session.exec(select(Email)).all()) == 2
    assert len(session.exec(select(Candidate)).all()) == 3


def test_classify_source_detects_meet_transcripts():
    assert classify_source("meet-recordings-noreply@google.com", "anything") == "transcript"
    assert classify_source("dana@mpr.org", "Transcript: weekly sync") == "transcript"
    assert classify_source("dana@mpr.org", "Login broken") == "email"


def test_all_fixtures_run_through_pipeline_offline(session):
    import json

    fixtures = sorted(FIXTURES_DIR.glob("*.json"))
    assert len(fixtures) >= 4
    for path in fixtures:
        result = run_fixture(session, path, StubLLM())
        assert "candidate #" in result, result

    emails = session.exec(select(Email)).all()
    assert {e.source_type for e in emails} == {"email", "transcript"}
    pending = session.exec(
        select(Candidate).where(Candidate.status == CandidateStatus.PENDING.value)
    ).all()
    # transcripts draft two stub candidates each; emails draft one
    expected = sum(
        2 if json.loads(p.read_text()).get("source_type") == "transcript" else 1
        for p in fixtures
    )
    assert len(pending) == expected
    # the exact prompt is persisted for tuning on every candidate
    assert all(c.prompt_used and c.raw_response for c in pending)


def test_stub_llm_output_passes_strict_parsing():
    from core.generate import parse_candidates_json

    email_prompt = ("Draft Jira ticket candidate(s) from this client email.\n"
                    "Subject: Fix search\nsource_email_id: 3\n\nbody")
    items = parse_candidates_json(StubLLM().complete("# Board: MSA (x)", email_prompt))
    assert len(items) == 1
    assert items[0]["summary"] == "Fix search"
    assert items[0]["project_key"] == "MSA"
    assert items[0]["source_email_id"] == 3

    transcript_prompt = ("Extract Jira ticket candidates from this meeting transcript — one per "
                         "distinct commitment.\nSubject: Weekly sync\nsource_email_id: 4\n\nbody")
    items = parse_candidates_json(StubLLM().complete("# Board: MSA (x)", transcript_prompt))
    assert len(items) == 2
    assert all(i["source_email_id"] == 4 for i in items)
