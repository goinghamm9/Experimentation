import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.deps import get_jira, get_llm
from app.main import create_app
from core.config import settings
from core.generate import generate_candidate
from core.ingest import ingest_message
from core.models import Candidate, CandidateStatus
from core.projects import load_project
from tests.fakes import FakeJira, FakeLLM, good_candidate_json

PROJECTS_DIR = Path(__file__).resolve().parent.parent / "projects"
AUTH = {"Authorization": "Basic " + base64.b64encode(
    f"{settings.dashboard_user}:{settings.dashboard_pass}".encode()).decode()}


@pytest.fixture
def jira():
    return FakeJira(issue_key="MSA-7")


@pytest.fixture
def client(engine, jira):
    app = create_app()
    app.dependency_overrides[get_jira] = lambda: jira
    app.dependency_overrides[get_llm] = lambda: FakeLLM(response=good_candidate_json())
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def candidate_id(session):
    email, _ = ingest_message(session, "msg-ui", "client@mpr.org", "Login broken", "Safari loops.")
    msa = load_project("MSA", PROJECTS_DIR)
    candidate = generate_candidate(session, email, msa, FakeLLM(response=good_candidate_json(email.id)))
    session.commit()
    return candidate.id


def test_dashboard_requires_auth(client):
    assert client.get("/").status_code == 401
    assert client.get("/", headers={"Authorization": "Basic " + base64.b64encode(b"x:y").decode()}).status_code == 401


def test_queue_lists_pending_candidate(client, candidate_id):
    page = client.get("/", headers=AUTH)
    assert page.status_code == 200
    assert "Fix login redirect loop" in page.text


def test_review_page_shows_source_side_by_side(client, candidate_id):
    page = client.get(f"/candidates/{candidate_id}", headers=AUTH)
    assert page.status_code == 200
    assert "Safari loops." in page.text          # source email
    assert "Fix login redirect loop" in page.text  # candidate
    assert "Approve" in page.text


def test_edit_then_approve_flow(client, jira, candidate_id, session):
    edit = client.post(f"/candidates/{candidate_id}/edit", headers=AUTH, data={
        "project_key": "MSA", "issue_type": "Bug",
        "summary": "Fix Safari login loop (edited)",
        "description": "Edited description.", "priority": "High",
        "labels": "auth, safari", "acceptance_criteria": "login works\nno regressions",
    }, follow_redirects=False)
    assert edit.status_code == 303

    approve = client.post(f"/candidates/{candidate_id}/approve", headers=AUTH, follow_redirects=False)
    assert approve.status_code == 303
    assert jira.created[0]["summary"] == "Fix Safari login loop (edited)"

    session.expire_all()
    candidate = session.get(Candidate, candidate_id)
    assert candidate.status == CandidateStatus.APPROVED.value
    assert candidate.jira_issue_key == "MSA-7"


def test_nothing_reaches_jira_without_approve(client, jira, candidate_id):
    client.get("/", headers=AUTH)
    client.get(f"/candidates/{candidate_id}", headers=AUTH)
    client.post(f"/candidates/{candidate_id}/edit", headers=AUTH, data={
        "project_key": "MSA", "issue_type": "Bug", "summary": "s",
        "description": "d", "priority": "Medium",
        "labels": "", "acceptance_criteria": "",
    }, follow_redirects=False)
    assert jira.created == []  # v1 invariant


def test_edit_rejects_unknown_board(client, candidate_id):
    response = client.post(f"/candidates/{candidate_id}/edit", headers=AUTH, data={
        "project_key": "NOSUCHBOARD", "issue_type": "Bug", "summary": "s",
        "description": "d", "priority": "Medium",
        "labels": "", "acceptance_criteria": "",
    }, follow_redirects=False)
    assert response.status_code == 400


def test_reject_with_reason(client, candidate_id, session):
    response = client.post(f"/candidates/{candidate_id}/reject", headers=AUTH,
                           data={"reason": "duplicate of MSA-3"}, follow_redirects=False)
    assert response.status_code == 303
    session.expire_all()
    assert session.get(Candidate, candidate_id).reject_reason == "duplicate of MSA-3"


def test_paste_transcript_joins_queue(client):
    response = client.post("/transcripts", headers=AUTH, data={
        "title": "Weekly sync with MPR",
        "text": "Client: please add CSV export to the admin panel.",
    }, follow_redirects=False)
    assert response.status_code == 303
