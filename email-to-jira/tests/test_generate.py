from pathlib import Path

import pytest

from core.audit import actions_for
from core.generate import build_system_prompt, generate_candidate, parse_candidate_json
from core.ingest import ingest_message
from core.models import CandidateStatus, EmailStatus
from core.projects import load_all, load_project, match_project
from tests.fakes import FakeLLM, good_candidate_json

PROJECTS_DIR = Path(__file__).resolve().parent.parent / "projects"


@pytest.fixture
def msa():
    return load_project("MSA", PROJECTS_DIR)


@pytest.fixture
def email(session):
    e, _ = ingest_message(session, "msg-gen", "client@mpr.org", "Login broken", "Safari loops on login.")
    return e


def test_project_configs_load():
    configs = load_all(PROJECTS_DIR)
    assert set(configs) == {"MSA", "PV0", "MS", "OR", "KBS", "OLAW", "NAMA"}
    assert configs["MSA"].enabled
    assert not configs["PV0"].enabled
    assert configs["PV0"].set_sprint_on_subtasks is False  # PV0 board rule
    assert "Lea" in configs["PV0"].glossary


def test_match_project_falls_back_to_default():
    configs = load_all(PROJECTS_DIR)
    assert match_project("anyone@unknown.com", configs, "MSA").key == "MSA"


def test_system_prompt_contains_board_knowledge(msa):
    prompt = build_system_prompt(msa, PROJECTS_DIR.parent / "prompts")
    assert "Board: MSA" in prompt
    assert "ONLY a JSON object" in prompt  # output schema appended
    assert "Respect the board glossary" in prompt  # global rules included


def test_parse_strips_code_fences_and_prose():
    raw = "Here is the ticket:\n```json\n" + good_candidate_json() + "\n```\nDone!"
    assert parse_candidate_json(raw)["summary"].startswith("Fix login")


def test_parse_rejects_missing_fields():
    with pytest.raises(ValueError, match="missing fields"):
        parse_candidate_json('{"summary": "x"}')


def test_generate_persists_candidate_prompt_and_response(session, email, msa):
    llm = FakeLLM(response=good_candidate_json(email.id))
    candidate = generate_candidate(session, email, msa, llm)

    assert candidate is not None
    assert candidate.status == CandidateStatus.PENDING.value
    assert candidate.labels_list == ["auth", "safari"]
    assert candidate.prompt_used  # exact prompt kept for tuning
    assert candidate.raw_response == llm.response
    assert email.status == EmailStatus.DRAFTED.value
    assert [a.action for a in actions_for(session, "candidate", candidate.id)] == ["drafted"]


def test_generate_clamps_disallowed_issue_type_and_priority(session, email, msa):
    llm = FakeLLM(response=good_candidate_json(email.id, issue_type="Epic", priority="ASAP!!"))
    candidate = generate_candidate(session, email, msa, llm)
    assert candidate.issue_type == msa.default_issue_type
    assert candidate.priority == "Medium"


def test_unparseable_output_surfaces_for_manual_review(session, email, msa):
    llm = FakeLLM(response="I cannot produce JSON for this, sorry.")
    candidate = generate_candidate(session, email, msa, llm)

    assert candidate is None
    assert email.status == EmailStatus.NEEDS_REVIEW.value
    log = actions_for(session, "email", email.id)
    assert any(a.action == "generation_failed" for a in log)


def test_llm_error_surfaces_for_manual_review_not_crash(session, email, msa):
    llm = FakeLLM(error="api unavailable")
    candidate = generate_candidate(session, email, msa, llm)
    assert candidate is None
    assert email.status == EmailStatus.NEEDS_REVIEW.value
