"""Candidate generation: assemble prompt -> call Claude -> parse strict JSON.

On any failure (API error, refusal, unparseable output) the email is marked
needs_review and the raw response is kept — never crash, never silently drop.
The exact prompt and raw response are persisted on the candidate for tuning.
"""
import json
import re
from pathlib import Path
from typing import Optional

from sqlmodel import Session

from core.audit import record_action
from core.config import settings
from core.llm import LLMClient, LLMError
from core.models import Candidate, CandidateStatus, Email, EmailStatus
from core.projects import ProjectConfig

REQUIRED_FIELDS = ("summary", "description", "issue_type", "project_key")
VALID_PRIORITIES = {"Highest", "High", "Medium", "Low", "Lowest"}


def _read_prompt(name: str, prompts_dir: Optional[Path] = None) -> str:
    return ((prompts_dir or settings.prompts_dir) / name).read_text()


def build_system_prompt(project: ProjectConfig, prompts_dir: Optional[Path] = None) -> str:
    """Global rules + board config + board few-shots + output schema."""
    parts = [_read_prompt("global_rules.md", prompts_dir)]

    board = [f"# Board: {project.key} ({project.name})",
             f"Allowed issue types: {', '.join(project.allowed_issue_types)}",
             f"Default issue type: {project.default_issue_type}"]
    if project.conventions.strip():
        board.append(f"## Ticket conventions\n{project.conventions.strip()}")
    if project.board_rules.strip():
        board.append(f"## Board rules\n{project.board_rules.strip()}")
    if project.glossary:
        terms = "\n".join(f"- {term}: {meaning}" for term, meaning in project.glossary.items())
        board.append(f"## Glossary (use these names verbatim)\n{terms}")
    parts.append("\n\n".join(board))

    if project.few_shot_examples:
        shots = []
        for i, ex in enumerate(project.few_shot_examples, 1):
            shots.append(
                f"## Example {i}\nSource:\n{ex.get('source', '').strip()}\n\n"
                f"Ideal ticket:\n{json.dumps(ex.get('ticket', {}), indent=2)}"
            )
        parts.append("# Examples of ideal tickets for this board\n\n" + "\n\n".join(shots))

    parts.append(_read_prompt("output_schema.md", prompts_dir))
    return "\n\n---\n\n".join(parts)


def build_user_prompt(email: Email) -> str:
    if email.source_type == "transcript":
        instruction = (
            "Extract Jira ticket candidates from this meeting transcript — one per "
            "distinct commitment or decision (typically 1-5). Ignore discussion that "
            "did not land on a commitment."
        )
    else:
        instruction = (
            "Draft Jira ticket candidate(s) from this client email. Usually ONE "
            "ticket; only split if it contains clearly separate actionable requests."
        )
    return (
        f"{instruction}\n"
        f"source_email_id: {email.id}\n"
        f"From: {email.sender}\n"
        f"Subject: {email.subject}\n\n"
        f"{email.body}"
    )


MAX_TICKETS_PER_SOURCE = 10


def _extract_json_payload(raw: str) -> str:
    """Strip code fences / surrounding prose around a JSON object or array."""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    if text.startswith(("{", "[")):
        return text
    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        raise ValueError("no JSON found in model output")
    start = min(starts)
    end = text.rfind("}" if text[start] == "{" else "]")
    if end <= start:
        raise ValueError("no JSON found in model output")
    return text[start : end + 1]


def parse_candidates_json(raw: str) -> list[dict]:
    """Parse one ticket object, an array of them, or {"tickets": [...]} —
    transcripts routinely yield several work items per meeting."""
    data = json.loads(_extract_json_payload(raw))
    if isinstance(data, dict) and isinstance(data.get("tickets"), list):
        data = data["tickets"]
    items = data if isinstance(data, list) else [data]
    if not items:
        raise ValueError("model returned an empty ticket list")
    if len(items) > MAX_TICKETS_PER_SOURCE:
        raise ValueError(f"model returned {len(items)} tickets (max {MAX_TICKETS_PER_SOURCE})")
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"ticket {i} is not a JSON object")
        missing = [f for f in REQUIRED_FIELDS if not item.get(f)]
        if missing:
            raise ValueError(f"ticket {i} missing fields: {missing}")
    return items


def generate_candidates(
    session: Session,
    email: Email,
    project: ProjectConfig,
    llm: LLMClient,
    prompts_dir: Optional[Path] = None,
) -> list[Candidate]:
    """Returns the pending Candidates (a transcript often yields several), or
    an empty list if the email was routed to manual review."""
    system_prompt = build_system_prompt(project, prompts_dir)
    user_prompt = build_user_prompt(email)
    prompt_used = f"[system]\n{system_prompt}\n\n[user]\n{user_prompt}"

    try:
        raw = llm.complete(system_prompt, user_prompt)
    except LLMError as exc:
        _mark_needs_review(session, email, prompt_used, raw="", reason=f"llm_error: {exc}")
        return []

    try:
        items = parse_candidates_json(raw)
        return [
            _build_candidate(session, email, project, item, prompt_used, raw)
            for item in items
        ]
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        _mark_needs_review(session, email, prompt_used, raw=raw, reason=f"parse_error: {exc}")
        return []


def _as_str_list(value) -> list[str]:
    """Model fields that should be lists sometimes arrive as a bare string."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(item) for item in value]


def _as_confidence(value) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _build_candidate(
    session: Session,
    email: Email,
    project: ProjectConfig,
    data: dict,
    prompt_used: str,
    raw: str,
) -> Candidate:
    issue_type = data.get("issue_type", project.default_issue_type)
    if issue_type not in project.allowed_issue_types:
        issue_type = project.default_issue_type
    priority = data.get("priority", "Medium")
    if priority not in VALID_PRIORITIES:
        priority = "Medium"

    candidate = Candidate(
        email_id=email.id,
        project_key=project.key,
        issue_type=issue_type,
        summary=str(data.get("summary", ""))[:255],
        description=str(data.get("description", "")),
        priority=priority,
        confidence=_as_confidence(data.get("confidence")),
        rationale=str(data.get("rationale", "")),
        prompt_used=prompt_used,
        raw_response=raw,
        status=CandidateStatus.PENDING.value,
    )
    candidate.labels_list = _as_str_list(data.get("labels"))
    candidate.acceptance_criteria_list = _as_str_list(data.get("acceptance_criteria"))
    session.add(candidate)

    email.status = EmailStatus.DRAFTED.value
    session.add(email)
    session.flush()
    record_action(session, "candidate", candidate.id, "drafted",
                  f"email_id={email.id} project={project.key} confidence={candidate.confidence}")
    return candidate


def _mark_needs_review(session: Session, email: Email, prompt_used: str, raw: str, reason: str) -> None:
    """Persist the failed attempt so the operator can handle the email manually."""
    failed = Candidate(
        email_id=email.id,
        project_key="",
        summary="",
        prompt_used=prompt_used,
        raw_response=raw,
        status=CandidateStatus.REJECTED.value,
        reject_reason=reason,
    )
    session.add(failed)
    email.status = EmailStatus.NEEDS_REVIEW.value
    session.add(email)
    session.flush()
    record_action(session, "email", email.id, "generation_failed", reason)
