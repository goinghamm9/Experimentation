"""Jira Cloud REST API v3 client. Only called from the explicit Approve path."""
import base64
import itertools

import httpx

from core.config import settings
from core.projects import ProjectConfig


class JiraError(Exception):
    pass


_dry_run_counter = itertools.count(1)


class DryRunJiraClient:
    """Testing mode (JIRA_DRY_RUN=true): the approve flow runs end-to-end —
    payload built, candidate marked approved, audit written — but no request
    leaves the machine. Issue keys are minted as DRY-<board>-<n>."""

    def create_issue(self, fields: dict) -> str:
        return f"DRY-{fields['project']['key']}-{next(_dry_run_counter)}"


class JiraClient:
    def __init__(self, base_url: str | None = None, email: str | None = None, api_token: str | None = None):
        self.base_url = (base_url or settings.jira_base_url).rstrip("/")
        email = email or settings.jira_email
        token = api_token or settings.jira_api_token
        auth = base64.b64encode(f"{email}:{token}".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def create_issue(self, fields: dict) -> str:
        """POST /rest/api/3/issue; returns the new issue key (e.g. MSA-101)."""
        try:
            response = httpx.post(
                f"{self.base_url}/rest/api/3/issue",
                json={"fields": fields},
                headers=self._headers,
                timeout=30,
            )
        except httpx.HTTPError as exc:
            raise JiraError(f"Jira request failed: {exc}") from exc
        if response.status_code >= 300:
            raise JiraError(f"Jira returned {response.status_code}: {response.text[:500]}")
        return response.json()["key"]


def build_issue_fields(
    project: ProjectConfig,
    issue_type: str,
    summary: str,
    description_adf: dict,
    priority: str,
    labels: list[str],
    sprint_field_id: str | None = None,
    sprint_id: int | None = None,
) -> dict:
    """Assemble the create-issue payload, honoring per-board sprint rules.

    Boards like PV0 reject a sprint on Sub-tasks (they inherit the parent's);
    set_sprint_on_subtasks=false in the board YAML drops the field there.
    """
    fields: dict = {
        "project": {"key": project.key},
        "issuetype": {"name": issue_type},
        "summary": summary,
        "description": description_adf,
        "priority": {"name": priority},
        "labels": labels,
    }
    if sprint_field_id and sprint_id is not None:
        is_subtask = issue_type.lower() in ("sub-task", "subtask")
        if not (is_subtask and not project.set_sprint_on_subtasks):
            fields[sprint_field_id] = sprint_id
    return fields
