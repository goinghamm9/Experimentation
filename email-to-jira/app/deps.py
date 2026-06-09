"""Dependency providers; tests override these via app.dependency_overrides."""
from typing import Iterator

from sqlmodel import Session

from core.db import get_engine
from core.jira_client import JiraClient
from core.llm import AnthropicClient


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
        session.commit()


def get_jira():
    return JiraClient()


def get_llm():
    return AnthropicClient()
