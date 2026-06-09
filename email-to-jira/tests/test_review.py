from pathlib import Path

import pytest

from core.adf import candidate_description_adf, text_to_adf
from core.audit import actions_for
from core.generate import generate_candidates
from core.ingest import ingest_message
from core.jira_client import DryRunJiraClient, JiraError, build_issue_fields
from core.models import CandidateStatus
from core.projects import load_project
from core.review import approve, reject, save_edits
from tests.fakes import FakeJira, FakeLLM, good_candidate_json

PROJECTS_DIR = Path(__file__).resolve().parent.parent / "projects"


@pytest.fixture
def msa():
    return load_project("MSA", PROJECTS_DIR)


@pytest.fixture
def candidate(session, msa):
    email, _ = ingest_message(session, "msg-rev", "client@mpr.org", "Login broken", "Safari loops.")
    return generate_candidates(session, email, msa, FakeLLM(response=good_candidate_json(email.id)))[0]


def test_text_to_adf_paragraphs_headings_bullets():
    doc = text_to_adf("# Context\nClient reported a bug.\n\n- step one\n- step two")
    assert doc["type"] == "doc" and doc["version"] == 1
    types = [node["type"] for node in doc["content"]]
    assert types == ["heading", "paragraph", "bulletList"]
    assert len(doc["content"][2]["content"]) == 2


def test_description_adf_appends_acceptance_criteria():
    doc = candidate_description_adf("Body text.", ["it works", "no regressions"])
    assert doc["content"][-2]["type"] == "heading"
    assert doc["content"][-1]["type"] == "bulletList"


def test_approve_creates_issue_and_audits(session, candidate, msa):
    jira = FakeJira(issue_key="MSA-42")
    approve(session, candidate, msa, jira)

    assert candidate.status == CandidateStatus.APPROVED.value
    assert candidate.jira_issue_key == "MSA-42"
    fields = jira.created[0]
    assert fields["project"]["key"] == "MSA"
    assert fields["description"]["type"] == "doc"  # ADF, not raw markdown
    log = [a.action for a in actions_for(session, "candidate", candidate.id)]
    assert log == ["drafted", "approved"]


def test_approve_twice_is_blocked(session, candidate, msa):
    jira = FakeJira()
    approve(session, candidate, msa, jira)
    with pytest.raises(ValueError, match="already approved"):
        approve(session, candidate, msa, jira)
    assert len(jira.created) == 1


def test_jira_failure_leaves_candidate_retriable(session, candidate, msa):
    jira = FakeJira(error=JiraError("400 priority invalid"))
    with pytest.raises(JiraError):
        approve(session, candidate, msa, jira)
    assert candidate.status != CandidateStatus.APPROVED.value
    assert candidate.jira_issue_key is None


def test_reject_records_reason(session, candidate, msa):
    reject(session, candidate, "Wrong board — belongs on PV0")
    assert candidate.status == CandidateStatus.REJECTED.value
    assert "PV0" in candidate.reject_reason
    log = actions_for(session, "candidate", candidate.id)
    assert log[-1].action == "rejected"


def test_save_edits_marks_edited_and_audits(session, candidate):
    save_edits(session, candidate, {"summary": "Fix Safari login loop", "labels": ["auth"]})
    assert candidate.status == CandidateStatus.EDITED.value
    assert candidate.summary == "Fix Safari login loop"
    assert candidate.labels_list == ["auth"]
    log = actions_for(session, "candidate", candidate.id)
    assert log[-1].action == "edited"


def test_dry_run_client_mints_dry_keys_and_approve_flow_works(session, candidate, msa):
    jira = DryRunJiraClient()
    approve(session, candidate, msa, jira)
    assert candidate.status == CandidateStatus.APPROVED.value
    assert candidate.jira_issue_key.startswith("DRY-MSA-")
    log = [a.action for a in actions_for(session, "candidate", candidate.id)]
    assert log == ["drafted", "approved"]


def test_get_jira_honors_dry_run_setting(monkeypatch):
    from app.deps import get_jira
    from core.config import settings
    from core.jira_client import JiraClient

    monkeypatch.setattr(settings, "jira_dry_run", True)
    assert isinstance(get_jira(), DryRunJiraClient)
    monkeypatch.setattr(settings, "jira_dry_run", False)
    assert isinstance(get_jira(), JiraClient)


def test_pv0_subtask_sprint_rule():
    pv0 = load_project("PV0", PROJECTS_DIR)
    adf = text_to_adf("body")
    with_sprint = dict(project=pv0, summary="s", description_adf=adf,
                       priority="Medium", labels=[], sprint_field_id="customfield_10020", sprint_id=7)

    subtask = build_issue_fields(issue_type="Sub-task", **with_sprint)
    assert "customfield_10020" not in subtask  # PV0: sub-tasks inherit sprint

    task = build_issue_fields(issue_type="Task", **with_sprint)
    assert task["customfield_10020"] == 7  # normal issues still get it
