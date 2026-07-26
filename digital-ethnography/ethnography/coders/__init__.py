"""Coders — deterministic, model-backed, and the panel runner that scores them.

Every coder produces the same shape, so the rigor layer never needs to know what
produced a label. Two invariants live in :mod:`.base`: cited evidence is verified
against the source before a label may count, and refusals are recorded rather than
silently becoming absences.
"""

from .base import Coder, CodedUnit, CodingResult, verify_span
from .deterministic import DeterministicCoder
from .llm import CompletionClient, LLMCoder, ModelSpec, extract_json, looks_like_refusal
from .panel_runner import PanelRun, run_panel
from .prompts import (
    DEDUCTIVE,
    DEFAULT_VARIANTS,
    ELIMINATIVE,
    INDUCTIVE,
    PromptVariant,
    coding_prompt,
)

__all__ = [
    "Coder", "CodedUnit", "CodingResult", "verify_span",
    "DeterministicCoder",
    "LLMCoder", "ModelSpec", "CompletionClient", "extract_json", "looks_like_refusal",
    "run_panel", "PanelRun",
    "PromptVariant", "coding_prompt",
    "DEDUCTIVE", "INDUCTIVE", "ELIMINATIVE", "DEFAULT_VARIANTS",
]
