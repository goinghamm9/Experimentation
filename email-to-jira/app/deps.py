"""Dependency providers; tests override these via app.dependency_overrides."""
from typing import Iterator

from sqlmodel import Session

from core.config import settings
from core.db import get_engine
from core.jira_client import DryRunJiraClient, JiraClient
from core.llm import AnthropicClient


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
        session.commit()


def get_jira():
    if settings.jira_dry_run:
        return DryRunJiraClient()
    return JiraClient()


def get_llm():
    return AnthropicClient()
