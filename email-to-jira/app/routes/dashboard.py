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
from core.audit import actions_for
from core.config import settings
from core.generate import generate_candidate
from core.ingest import ingest_message
from core.jira_client import JiraError
from core.models import Action, Candidate, CandidateStatus, Email, EmailStatus, SourceType
from core.projects import load_all, load_project
from core.review import approve, reject, save_edits

router = APIRouter(dependencies=[Depends(require_operator)])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


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
    })


@router.get("/candidates/{candidate_id}")
def review_view(candidate_id: int, request: Request, session: Session = Depends(get_session)):
    candidate = session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404)
    email = session.get(Email, candidate.email_id)
    project = load_all().get(candidate.project_key)
    return templates.TemplateResponse(request, "review.html", {
        "c": candidate,
        "email": email,
        "project": project,
        "projects": load_all(),
        "audit": actions_for(session, "candidate", candidate.id),
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
    candidate = session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404)
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
    candidate = session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404)
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
    candidate = session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404)
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
    """Draft (or re-draft) a candidate — e.g. after a parse failure."""
    email = session.get(Email, email_id)
    if not email:
        raise HTTPException(404)
    key = project_key or settings.default_project_key
    try:
        project = load_project(key)
    except FileNotFoundError:
        raise HTTPException(400, f"unknown board {key!r}")
    candidate = generate_candidate(session, email, project, llm)
    if candidate is None:
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(f"/candidates/{candidate.id}", status_code=303)


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


@router.get("/audit")
def audit_log(request: Request, session: Session = Depends(get_session)):
    entries = session.exec(select(Action).order_by(Action.created_at.desc()).limit(200)).all()
    return templates.TemplateResponse(request, "audit.html", {"entries": entries})
