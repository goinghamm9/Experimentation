"""Dashboard routes: list, review side-by-side, edit, approve, reject,
paste-a-transcript, regenerate, audit trail. HTMX posts return redirects or
partials; nothing reaches Jira except POST /candidates/{id}/approve."""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.auth import require_operator
from app.deps import get_jira, get_llm, get_session
from core.audit import actions_for, record_action
from core.config import settings
from core.generate import generate_candidates
from core.ingest import ingest_message
from core.jira_client import JiraError
from core.models import Action, Candidate, CandidateStatus, Email, EmailStatus, SourceType
from core.projects import append_example, load_all, load_project
from core.review import approve, reject, save_edits

router = APIRouter(dependencies=[Depends(require_operator)])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _candidate_or_404(session: Session, candidate_id: int) -> Candidate:
    candidate = session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404)
    return candidate


@router.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    pending = session.exec(
        select(Candidate)
        .where(Candidate.status.in_([CandidateStatus.PENDING.value, CandidateStatus.EDITED.value]))
        .order_by(Candidate.created_at)
    ).all()
    needs_review = session.exec(
        select(Email).where(Email.status == EmailStatus.NEEDS_REVIEW.value)
    ).all()
    processed = session.exec(
        select(Candidate)
        .where(Candidate.status.in_([CandidateStatus.APPROVED.value, CandidateStatus.REJECTED.value]))
        .where(Candidate.project_key != "")
        .order_by(Candidate.updated_at.desc())
        .limit(20)
    ).all()
    return templates.TemplateResponse(request, "index.html", {
        "pending": pending,
        "needs_review": needs_review,
        "processed": processed,
        "projects": load_all(),
        "jira_dry_run": settings.jira_dry_run,
    })


@router.get("/candidates/{candidate_id}")
def review_view(candidate_id: int, request: Request, session: Session = Depends(get_session)):
    candidate = _candidate_or_404(session, candidate_id)
    email = session.get(Email, candidate.email_id)
    if not email:
        raise HTTPException(404, f"source email {candidate.email_id} missing")
    projects = load_all()
    return templates.TemplateResponse(request, "review.html", {
        "c": candidate,
        "email": email,
        "project": projects.get(candidate.project_key),
        "projects": projects,
        "audit": actions_for(session, "candidate", candidate.id),
        "jira_dry_run": settings.jira_dry_run,
    })


@router.post("/candidates/{candidate_id}/edit")
def edit_candidate(
    candidate_id: int,
    session: Session = Depends(get_session),
    project_key: str = Form(...),
    issue_type: str = Form(...),
    summary: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    labels: str = Form(""),
    acceptance_criteria: str = Form(""),
):
    candidate = _candidate_or_404(session, candidate_id)
    if project_key not in load_all():
        raise HTTPException(400, f"unknown board {project_key!r}")
    save_edits(session, candidate, {
        "project_key": project_key,
        "issue_type": issue_type,
        "summary": summary,
        "description": description,
        "priority": priority,
        "labels": [l.strip() for l in labels.split(",") if l.strip()],
        "acceptance_criteria": _split_lines(acceptance_criteria),
    })
    return RedirectResponse(f"/candidates/{candidate_id}", status_code=303)


@router.post("/candidates/{candidate_id}/approve")
def approve_candidate(
    candidate_id: int,
    session: Session = Depends(get_session),
    jira=Depends(get_jira),
):
    """The explicit human approval step — the only path that touches Jira."""
    candidate = _candidate_or_404(session, candidate_id)
    try:
        project = load_project(candidate.project_key)
    except FileNotFoundError:
        raise HTTPException(400, f"unknown board {candidate.project_key!r}")
    try:
        approve(session, candidate, project, jira)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    except JiraError as exc:
        raise HTTPException(502, f"Jira rejected the issue: {exc}")
    return RedirectResponse(f"/candidates/{candidate_id}", status_code=303)


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate(
    candidate_id: int,
    reason: str = Form(...),
    session: Session = Depends(get_session),
):
    candidate = _candidate_or_404(session, candidate_id)
    try:
        reject(session, candidate, reason)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return RedirectResponse("/", status_code=303)


@router.post("/emails/{email_id}/generate")
def regenerate(
    email_id: int,
    project_key: str = Form(""),
    session: Session = Depends(get_session),
    llm=Depends(get_llm),
):
    """Draft (or re-draft) candidates — e.g. after a parse failure."""
    email = session.get(Email, email_id)
    if not email:
        raise HTTPException(404)
    key = project_key or settings.default_project_key
    try:
        project = load_project(key)
    except FileNotFoundError:
        raise HTTPException(400, f"unknown board {key!r}")
    candidates = generate_candidates(session, email, project, llm)
    if not candidates:
        return RedirectResponse("/", status_code=303)
    if len(candidates) == 1:
        return RedirectResponse(f"/candidates/{candidates[0].id}", status_code=303)
    return RedirectResponse("/", status_code=303)


@router.post("/transcripts")
def add_transcript(
    title: str = Form(...),
    text: str = Form(...),
    sender: str = Form("manual-paste"),
    session: Session = Depends(get_session),
):
    """Manual paste of a Google Meet / Drive transcript (v1 path for meetings
    that don't arrive by email). Automated Drive fetch is a future phase."""
    ingest_message(
        session,
        gmail_message_id=f"manual-{uuid.uuid4().hex[:12]}",
        sender=sender,
        subject=title,
        body=text,
        source_type=SourceType.TRANSCRIPT.value,
    )
    return RedirectResponse("/", status_code=303)


@router.post("/candidates/{candidate_id}/save-example")
def save_candidate_as_example(
    candidate_id: int,
    session: Session = Depends(get_session),
):
    """Capture this candidate (as last edited/approved) plus its source as a
    few-shot example for its board — the cheapest way to grow example data."""
    candidate = _candidate_or_404(session, candidate_id)
    if not candidate.project_key or candidate.project_key not in load_all():
        raise HTTPException(400, f"candidate has no valid board ({candidate.project_key!r})")
    email = session.get(Email, candidate.email_id)
    if not email:
        raise HTTPException(404, f"source email {candidate.email_id} missing")
    count = append_example(
        candidate.project_key,
        source=f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}",
        ticket={
            "summary": candidate.summary,
            "description": candidate.description,
            "issue_type": candidate.issue_type,
            "priority": candidate.priority,
            "labels": candidate.labels_list,
            "acceptance_criteria": candidate.acceptance_criteria_list,
        },
    )
    record_action(session, "candidate", candidate.id, "example_saved",
                  f"board={candidate.project_key} examples={count}")
    return RedirectResponse(f"/candidates/{candidate_id}", status_code=303)


@router.get("/examples")
def examples_page(request: Request):
    """Per-board few-shot examples: paste source + ideal ticket pairs here
    (e.g. exported from past Claude/ChatGPT drafting sessions)."""
    return templates.TemplateResponse(request, "examples.html", {
        "projects": load_all(),
    })


@router.post("/examples")
def add_example(
    project_key: str = Form(...),
    source: str = Form(...),
    summary: str = Form(...),
    description: str = Form(""),
    issue_type: str = Form("Task"),
    priority: str = Form("Medium"),
    labels: str = Form(""),
    acceptance_criteria: str = Form(""),
):
    if project_key not in load_all():
        raise HTTPException(400, f"unknown board {project_key!r}")
    append_example(
        project_key,
        source=source,
        ticket={
            "summary": summary,
            "description": description,
            "issue_type": issue_type,
            "priority": priority,
            "labels": [l.strip() for l in labels.split(",") if l.strip()],
            "acceptance_criteria": _split_lines(acceptance_criteria),
        },
    )
    return RedirectResponse("/examples", status_code=303)


@router.get("/audit")
def audit_log(request: Request, session: Session = Depends(get_session)):
    entries = session.exec(select(Action).order_by(Action.created_at.desc()).limit(200)).all()
    return templates.TemplateResponse(request, "audit.html", {"entries": entries})
