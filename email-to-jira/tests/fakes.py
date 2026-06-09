"""Fakes for the two external services: the LLM and Jira."""
import json

from core.llm import LLMError


class FakeLLM:
    """Returns a canned response (or raises) and records what it was asked."""

    def __init__(self, response: str | None = None, error: str | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append({"system": system_prompt, "user": user_prompt})
        if self.error:
            raise LLMError(self.error)
        return self.response or ""


def good_candidate_json(source_email_id: int = 1, **overrides) -> str:
    data = {
        "summary": "Fix login redirect loop on Safari",
        "description": "Client reports Safari users loop back to /login.\n\nContext: reported by email.",
        "issue_type": "Bug",
        "project_key": "MSA",
        "priority": "High",
        "labels": ["auth", "safari"],
        "acceptance_criteria": ["Safari login lands on the dashboard", "No regression on Chrome"],
        "confidence": 0.85,
        "rationale": "Clear bug report with browser specifics.",
        "source_email_id": source_email_id,
    }
    data.update(overrides)
    return json.dumps(data)


class FakeJira:
    """Stands in for JiraClient; records create_issue payloads."""

    def __init__(self, issue_key: str = "MSA-101", error: Exception | None = None):
        self.issue_key = issue_key
        self.error = error
        self.created: list[dict] = []

    def create_issue(self, fields: dict) -> str:
        if self.error:
            raise self.error
        self.created.append(fields)
        return self.issue_key
