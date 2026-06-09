"""TaskRouter seam — FUTURE: route certain task types to Claude vs. OpenAI.

v1 uses Claude for everything; nothing here is wired into the pipeline yet.
"""
from typing import Protocol


class TaskRouter(Protocol):
    def route(self, task_type: str) -> str:
        """Return the provider/model identifier to use for a task type."""
        ...


class ClaudeOnlyRouter:
    """v1 default: everything goes to the configured Anthropic model."""

    def __init__(self, model: str):
        self.model = model

    def route(self, task_type: str) -> str:
        return self.model
