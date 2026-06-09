from pathlib import Path

import pytest

import shutil

from core.audit import actions_for
from core.generate import build_system_prompt, generate_candidates, parse_candidates_json
from core.ingest import ingest_message
from core.models import CandidateStatus, EmailStatus, SourceType
from core.projects import append_example, load_all, load_project, match_project
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
    assert "Respond with ONLY JSON" in prompt  # output schema appended
    assert "Respect the board glossary" in prompt  # global rules included


def test_parse_strips_code_fences_and_prose():
    raw = "Here is the ticket:\n```json\n" + good_candidate_json() + "\n```\nDone!"
    items = parse_candidates_json(raw)
    assert len(items) == 1
    assert items[0]["summary"].startswith("Fix login")


def test_parse_accepts_array_and_tickets_wrapper():
    two = f"[{good_candidate_json()}, {good_candidate_json(summary='Second item')}]"
    assert len(parse_candidates_json(two)) == 2
    wrapped = f'{{"tickets": [{good_candidate_json()}]}}'
    assert len(parse_candidates_json(wrapped)) == 1
    with_prose = f"Two tickets:\n[{good_candidate_json()}, {good_candidate_json()}]\nDone."
    assert len(parse_candidates_json(with_prose)) == 2


def test_parse_rejects_missing_fields_and_runaway_lists():
    with pytest.raises(ValueError, match="missing fields"):
        parse_candidates_json('{"summary": "x"}')
    with pytest.raises(ValueError, match="empty ticket list"):
        parse_candidates_json("[]")
    runaway = "[" + ",".join(good_candidate_json() for _ in range(11)) + "]"
    with pytest.raises(ValueError, match="max 10"):
        parse_candidates_json(runaway)


def test_generate_persists_candidate_prompt_and_response(session, email, msa):
    llm = FakeLLM(response=good_candidate_json(email.id))
    candidates = generate_candidates(session, email, msa, llm)

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.status == CandidateStatus.PENDING.value
    assert candidate.labels_list == ["auth", "safari"]
    assert candidate.prompt_used  # exact prompt kept for tuning
    assert candidate.raw_response == llm.response
    assert email.status == EmailStatus.DRAFTED.value
    assert [a.action for a in actions_for(session, "candidate", candidate.id)] == ["drafted"]


def test_transcript_yields_multiple_candidates(session, msa):
    transcript, _ = ingest_message(
        session, "msg-meeting", "meet-recordings-noreply@google.com",
        "Transcript: weekly sync", "Dana: we agreed on X.\nJames: and Y.",
        source_type=SourceType.TRANSCRIPT.value,
    )
    response = (f"[{good_candidate_json(transcript.id, summary='Add opt-out toggle')},"
                f" {good_candidate_json(transcript.id, summary='Update toggle copy')}]")
    candidates = generate_candidates(session, transcript, msa, FakeLLM(response=response))

    assert [c.summary for c in candidates] == ["Add opt-out toggle", "Update toggle copy"]
    assert all(c.status == CandidateStatus.PENDING.value for c in candidates)
    assert all(c.raw_response == response for c in candidates)  # shared provenance
    assert transcript.status == EmailStatus.DRAFTED.value
    assert len({c.id for c in candidates}) == 2


def test_user_prompt_instruction_varies_by_source_type(session):
    from core.generate import build_user_prompt

    email, _ = ingest_message(session, "msg-up-1", "a@b.c", "subj", "body")
    transcript, _ = ingest_message(session, "msg-up-2", "a@b.c", "subj", "body",
                                   source_type=SourceType.TRANSCRIPT.value)
    assert "client email" in build_user_prompt(email)
    assert "one per distinct commitment" in build_user_prompt(transcript)


def test_generate_clamps_disallowed_issue_type_and_priority(session, email, msa):
    llm = FakeLLM(response=good_candidate_json(email.id, issue_type="Epic", priority="ASAP!!"))
    candidate = generate_candidates(session, email, msa, llm)[0]
    assert candidate.issue_type == msa.default_issue_type
    assert candidate.priority == "Medium"


def test_generate_tolerates_sloppy_field_types(session, email, msa):
    llm = FakeLLM(response=good_candidate_json(
        email.id, confidence="high", labels="auth", acceptance_criteria="it works"))
    candidates = generate_candidates(session, email, msa, llm)
    assert candidates  # never crash on malformed-but-parseable output
    assert candidates[0].confidence == 0.0
    assert candidates[0].labels_list == ["auth"]  # bare string wrapped, not split into chars
    assert candidates[0].acceptance_criteria_list == ["it works"]


def test_unparseable_output_surfaces_for_manual_review(session, email, msa):
    llm = FakeLLM(response="I cannot produce JSON for this, sorry.")
    candidates = generate_candidates(session, email, msa, llm)

    assert candidates == []
    assert email.status == EmailStatus.NEEDS_REVIEW.value
    log = actions_for(session, "email", email.id)
    assert any(a.action == "generation_failed" for a in log)


def test_llm_error_surfaces_for_manual_review_not_crash(session, email, msa):
    llm = FakeLLM(error="api unavailable")
    candidates = generate_candidates(session, email, msa, llm)
    assert candidates == []
    assert email.status == EmailStatus.NEEDS_REVIEW.value


def test_example_store_merges_into_config_and_prompt(tmp_path):
    projects_tmp = tmp_path / "projects"
    projects_tmp.mkdir()
    shutil.copy(PROJECTS_DIR / "MSA.yaml", projects_tmp / "MSA.yaml")

    count = append_example(
        "MSA",
        source="From: x@mpr.org\nSubject: slow dashboard\n\nIt takes 30s to load.",
        ticket={"summary": "Investigate dashboard load time regression",
                "issue_type": "Bug", "priority": "High"},
        projects_dir=projects_tmp,
    )
    assert count == 1
    assert (projects_tmp / "examples" / "MSA.yaml").exists()

    cfg = load_project("MSA", projects_tmp)
    assert len(cfg.few_shot_examples) == 1  # store merged with (empty) inline list

    prompt = build_system_prompt(cfg, PROJECTS_DIR.parent / "prompts")
    assert "Investigate dashboard load time regression" in prompt
    # examples/ store files must not be mistaken for board configs
    assert set(load_all(projects_tmp)) == {"MSA"}
