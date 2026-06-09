"""Review actions: edit, approve, reject.

approve() is the ONLY code path in the app that creates a Jira issue — the v1
invariant. It is only ever reached from the dashboard's Approve button.
"""
from sqlmodel import Session

from core.adf import candidate_description_adf
from core.audit import record_action
from core.jira_client import build_issue_fields
from core.models import Candidate, CandidateStatus, utcnow
from core.projects import ProjectConfig

EDITABLE_FIELDS = ("project_key", "issue_type", "summary", "description", "priority")


def save_edits(session: Session, candidate: Candidate, fields: dict) -> Candidate:
    changed = []
    for name in EDITABLE_FIELDS:
        if name in fields and fields[name] is not None and getattr(candidate, name) != fields[name]:
            setattr(candidate, name, fields[name])
            changed.append(name)
    if "labels" in fields and fields["labels"] is not None:
        candidate.labels_list = fields["labels"]
        changed.append("labels")
    if "acceptance_criteria" in fields and fields["acceptance_criteria"] is not None:
        candidate.acceptance_criteria_list = fields["acceptance_criteria"]
        changed.append("acceptance_criteria")

    if changed:
        candidate.status = CandidateStatus.EDITED.value
        candidate.updated_at = utcnow()
        session.add(candidate)
        record_action(session, "candidate", candidate.id, "edited", f"fields={','.join(changed)}")
    return candidate


def approve(session: Session, candidate: Candidate, project: ProjectConfig, jira) -> Candidate:
    """Create the Jira issue and mark the candidate processed. Raises JiraError
    on API failure, leaving the candidate untouched for a retry."""
    if candidate.status in (CandidateStatus.APPROVED.value, CandidateStatus.REJECTED.value):
        raise ValueError(f"candidate {candidate.id} already {candidate.status}")

    fields = build_issue_fields(
        project=project,
        issue_type=candidate.issue_type,
        summary=candidate.summary,
        description_adf=candidate_description_adf(
            candidate.description, candidate.acceptance_criteria_list
        ),
        priority=candidate.priority,
        labels=candidate.labels_list,
    )
    issue_key = jira.create_issue(fields)

    candidate.jira_issue_key = issue_key
    candidate.status = CandidateStatus.APPROVED.value
    candidate.updated_at = utcnow()
    session.add(candidate)
    record_action(session, "candidate", candidate.id, "approved", f"jira_issue_key={issue_key}")
    return candidate


def reject(session: Session, candidate: Candidate, reason: str) -> Candidate:
    """Reject with a free-text reason — kept as future training signal."""
    if candidate.status == CandidateStatus.APPROVED.value:
        raise ValueError(f"candidate {candidate.id} already approved")
    candidate.status = CandidateStatus.REJECTED.value
    candidate.reject_reason = reason
    candidate.updated_at = utcnow()
    session.add(candidate)
    record_action(session, "candidate", candidate.id, "rejected", f"reason={reason}")
    return candidate
