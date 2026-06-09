"""Thin seam over the Anthropic Messages API so tests can inject a fake.

The model name comes from config (ANTHROPIC_MODEL) so cheaper models can be
A/B tested without code changes.
"""
from typing import Protocol

from core.config import settings


class LLMClient(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model's text output. Raise LLMError on API failure/refusal."""
        ...


class LLMError(Exception):
    pass


class AnthropicClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.model = model or settings.anthropic_model

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        import anthropic

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as exc:
            raise LLMError(str(exc)) from exc
        # A refusal or empty result must surface for manual review, not crash.
        if response.stop_reason == "refusal" or not response.content:
            raise LLMError(f"model returned no usable content (stop_reason={response.stop_reason})")
        return "".join(block.text for block in response.content if block.type == "text")
