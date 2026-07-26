"""Optional LLM enrichment layer (deterministic core works without it)."""

from .client import AnthropicLLM, LLMClient, OfflineLLM, build_client

__all__ = ["AnthropicLLM", "LLMClient", "OfflineLLM", "build_client"]
