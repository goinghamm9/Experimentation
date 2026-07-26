"""The LLM coder.

Talks to a gateway-shaped client, never a provider SDK, so the model is a runtime
configuration rather than a build-time dependency. Route by *capability profile*;
model identifiers go stale in weeks and must never be structural.

Everything the coder emits is treated as a claim to be checked:

* the response must parse as the requested JSON, or the unit is uncertain;
* the label must be in the codebook, or the unit is uncertain (no invented codes);
* the cited span must be verifiable in the source, or the label is dropped.

A refusal is recorded as a refusal, not as an absence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from ..schema import Observation
from .base import CodedUnit, CodingResult, verify_span
from .prompts import SYSTEM, DEDUCTIVE, PromptVariant, coding_prompt

# Phrases that indicate the model declined rather than answered.
_REFUSAL = re.compile(
    r"\b(i (?:can(?:no|')t|won'?t|am unable to)|i'm sorry|i apologize|"
    r"as an ai|cannot assist|not able to help|against my guidelines)\b",
    re.IGNORECASE,
)


class CompletionClient:
    """Minimal gateway contract. Anything with these two members works."""

    available: bool = False

    def complete(self, system: str, prompt: str) -> str:  # pragma: no cover - protocol
        raise NotImplementedError


@dataclass
class ModelSpec:
    """A coder's configuration. `lineage` is the decorrelation axis, not `model`."""

    id: str
    lineage: str                       # base-model family: coders sharing this correlate
    model: str = "config:mid"          # capability profile, resolved by the gateway
    temperature: float = 0.0
    variant: PromptVariant = DEDUCTIVE
    cost_per_1k_in: float = 0.0
    cost_per_1k_out: float = 0.0


def extract_json(raw: str) -> dict | None:
    """Pull the first JSON object out of a response, tolerating chatty wrappers."""
    if not raw:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = raw.find("{")
        if start < 0:
            return None
        depth, end = 0, None
        for i, ch in enumerate(raw[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is None:
            return None
        candidate = raw[start:end]
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def looks_like_refusal(raw: str) -> bool:
    return bool(raw) and bool(_REFUSAL.search(raw[:400]))


@dataclass
class LLMCoder:
    """One model-backed coder in a panel."""

    spec: ModelSpec
    codebook: dict[str, list[str]]
    client: CompletionClient
    max_units: int | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.spec.id

    @property
    def lineage(self) -> str:
        return self.spec.lineage

    def _context(self, obs: Observation) -> str:
        event = obs.payload.get("event") if obs.payload else None
        bits = [obs.source, obs.kind.value]
        if event:
            bits.append(str(event))
        return " · ".join(bits)

    def _unit_text(self, obs: Observation) -> str:
        if obs.text:
            return obs.text
        # Behavioural trace: render the payload rather than sending an empty unit.
        return json.dumps(obs.payload, sort_keys=True) if obs.payload else ""

    def code_one(self, obs: Observation) -> CodedUnit:
        text = self._unit_text(obs)
        if not text.strip():
            return CodedUnit(obs.id, None, rationale="empty unit")

        prompt = coding_prompt(
            unit_text=text,
            unit_context=self._context(obs),
            codebook=self.codebook,
            variant=self.spec.variant,
            coder_id=self.spec.id,
        )
        raw = self.client.complete(SYSTEM, prompt) or ""

        if looks_like_refusal(raw):
            return CodedUnit(obs.id, None, refused=True, rationale="model declined")

        parsed = extract_json(raw)
        if parsed is None:
            return CodedUnit(obs.id, None, rationale="unparseable response")

        label = parsed.get("label")
        if isinstance(label, str):
            label = label.strip()
        if not label or label.upper() == "UNCERTAIN":
            return CodedUnit(obs.id, None, rationale="coder answered uncertain")
        if label not in self.codebook:
            # An invented code is not a finding; it is out-of-contract output.
            return CodedUnit(obs.id, None, rationale=f"label not in codebook: {label!r}")

        evidence = parsed.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            evidence = None
        verified = verify_span(evidence, obs.text) if evidence else False

        try:
            confidence = float(parsed.get("confidence", 1.0))
        except (TypeError, ValueError):
            confidence = 1.0

        return CodedUnit(
            unit_id=obs.id,
            label=label,
            evidence=evidence,
            confidence=max(0.0, min(1.0, confidence)),
            span_verified=verified,
            rationale=str(parsed.get("rationale", ""))[:300],
        )

    def code(self, observations: list[Observation]) -> CodingResult:
        if not getattr(self.client, "available", False):
            return CodingResult(
                coder_id=self.spec.id,
                lineage=self.spec.lineage,
                notes=[
                    f"{self.spec.id}: no model client available — coder produced nothing. "
                    "This is an absent coder, not an agreeing one."
                ],
            )

        subset = observations[: self.max_units] if self.max_units else observations
        units = [self.code_one(o) for o in subset]

        # Each unit puts the whole codebook plus UNCERTAIN on the table.
        m = len(subset) * (len(self.codebook) + 1)

        result = CodingResult(
            coder_id=self.spec.id,
            lineage=self.spec.lineage,
            units=units,
            hypotheses_considered=m,
            notes=list(self.notes),
        )
        result.notes.extend(result.quality_flags())
        return result
