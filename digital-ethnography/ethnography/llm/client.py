"""LLM client with a deterministic offline fallback.

The whole system is designed to produce a complete, defensible ethnographic
report *without any model calls*. The LLM is strictly an enrichment layer that
proposes additional interpretation — always tagged ``LLM_ASSISTED`` and flagged
``needs_review`` so a human stays in the loop.

If the ``anthropic`` package is installed and ``ANTHROPIC_API_KEY`` is set and
the study opted into enrichment, real calls are made. Otherwise an
:class:`OfflineLLM` returns empty enrichments, and the deterministic core stands
alone. This keeps tests hermetic and keeps the tool usable in an air-gapped
research environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class LLMClient(Protocol):
    available: bool

    def complete(self, system: str, prompt: str) -> str:
        ...


@dataclass
class OfflineLLM:
    """No-op client. Returns empty string; enrichment steps treat this as
    'nothing to add' and fall back to deterministic output only."""

    available: bool = False

    def complete(self, system: str, prompt: str) -> str:
        return ""


class AnthropicLLM:
    """Thin wrapper over the Anthropic Messages API, used only when explicitly
    enabled. Import is lazy so the dependency is optional."""

    def __init__(self, model: str = "claude-sonnet-5", max_tokens: int = 1024) -> None:
        from anthropic import Anthropic  # imported lazily; optional dependency

        self._client = Anthropic()
        self._model = model
        self._max_tokens = max_tokens
        self.available = True

    def complete(self, system: str, prompt: str) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if block.type == "text")


def build_client(enabled: bool) -> LLMClient:
    """Return a real client if enrichment is enabled and possible, else offline."""
    if not enabled:
        return OfflineLLM()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return OfflineLLM()
    try:
        return AnthropicLLM()
    except Exception:
        # Missing package or client init failure -> degrade gracefully.
        return OfflineLLM()
