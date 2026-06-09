import base64
import shutil
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.deps import get_jira, get_llm
from app.main import create_app
from core.config import settings
from core.generate import generate_candidates
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
    candidate = generate_candidates(session, email, msa, FakeLLM(response=good_candidate_json(email.id)))[0]
    session.commit()
    return candidate.id


@pytest.fixture
def tmp_projects(monkeypatch, tmp_path):
    """Point the app at a throwaway projects dir so example writes don't touch the repo."""
    projects_tmp = tmp_path / "projects"
    projects_tmp.mkdir()
    shutil.copy(PROJECTS_DIR / "MSA.yaml", projects_tmp / "MSA.yaml")
    monkeypatch.setattr(settings, "projects_dir", projects_tmp)
    return projects_tmp


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


def test_save_candidate_as_example_writes_store(client, candidate_id, tmp_projects):
    response = client.post(f"/candidates/{candidate_id}/save-example",
                           headers=AUTH, follow_redirects=False)
    assert response.status_code == 303

    store = tmp_projects / "examples" / "MSA.yaml"
    examples = yaml.safe_load(store.read_text())
    assert len(examples) == 1
    assert "Safari loops." in examples[0]["source"]
    assert examples[0]["ticket"]["summary"].startswith("Fix login redirect loop")


def test_examples_page_and_manual_add(client, tmp_projects):
    page = client.get("/examples", headers=AUTH)
    assert page.status_code == 200
    assert "Add an example" in page.text

    response = client.post("/examples", headers=AUTH, data={
        "project_key": "MSA",
        "source": "From: client@mpr.org\n\nPasted from an old Claude drafting chat.",
        "summary": "Add CSV export to admin reports",
        "description": "Finance needs CSV export of the monthly usage report.",
        "issue_type": "Story", "priority": "Medium",
        "labels": "reports, export", "acceptance_criteria": "CSV downloads\ncolumns match table",
    }, follow_redirects=False)
    assert response.status_code == 303

    examples = yaml.safe_load((tmp_projects / "examples" / "MSA.yaml").read_text())
    assert examples[0]["ticket"]["labels"] == ["reports", "export"]
    assert examples[0]["ticket"]["acceptance_criteria"] == ["CSV downloads", "columns match table"]

    # the new example is now part of the board's prompt material
    coverage = client.get("/examples", headers=AUTH)
    assert ">1<" in coverage.text.replace(" ", "")


def test_add_example_rejects_unknown_board(client, tmp_projects):
    response = client.post("/examples", headers=AUTH, data={
        "project_key": "NOSUCH", "source": "x", "summary": "y",
    }, follow_redirects=False)
    assert response.status_code == 400
