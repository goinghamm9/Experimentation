"""Prompt construction — and deliberate decorrelation.

Model panels share errors heavily, so **lineage diversity is the scarce resource**
and adding another coder from the same family buys almost nothing. The research is
equally clear that family diversity alone is insufficient: decorrelation must also
vary *prompt frame, codebook framing, and elicitation order*.

This module makes those three levers explicit and seeded, so a panel's diversity
is a recorded property of the run rather than a hope.

The prompt keeps the model in an assistant role and demands grounding: a label is
only admissible with a verbatim span, and "uncertain" is an available answer. That
last point matters — forcing a choice manufactures agreement, and a high uncertain
rate is a signal about the codebook rather than about the coder.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

SYSTEM = (
    "You are one of several independent coders applying a fixed codebook to "
    "anonymised research material. You are not the analyst and you do not draw "
    "conclusions. Apply the codebook as written. If the material is not covered "
    "by the codebook, say so — a forced label is worse than an honest 'uncertain'. "
    "Never invent a quotation."
)


@dataclass(frozen=True)
class PromptVariant:
    """One decorrelation setting. Vary these across coders, not just the model."""

    name: str
    framing: str            # "deductive" | "inductive" | "eliminative"
    shuffle_codes: bool = True
    ask_rationale: bool = False

    def code_order(self, labels: list[str], coder_id: str) -> list[str]:
        """Deterministically permute the option list per coder.

        Option order is a known anchor. Fixing it identically across coders is a
        shared bias; randomising it per coder without a seed is unreproducible.
        Seeded permutation gives decorrelation *and* auditability.
        """
        if not self.shuffle_codes:
            return list(labels)
        return sorted(
            labels,
            key=lambda l: hashlib.sha256(f"{coder_id}:{self.name}:{l}".encode()).hexdigest(),
        )


# Three genuinely different ways to ask the same question.
DEDUCTIVE = PromptVariant("deductive", "deductive")
INDUCTIVE = PromptVariant("inductive", "inductive", ask_rationale=True)
ELIMINATIVE = PromptVariant("eliminative", "eliminative")

DEFAULT_VARIANTS = (DEDUCTIVE, INDUCTIVE, ELIMINATIVE)

_FRAMES = {
    "deductive": (
        "Decide which single codebook entry best describes this unit. "
        "Match the definitions as written."
    ),
    "inductive": (
        "First read the unit on its own terms and note what it is about. "
        "Then decide which single codebook entry, if any, captures that."
    ),
    "eliminative": (
        "Rule out the codebook entries that clearly do not apply. "
        "Choose from whatever remains, or answer UNCERTAIN if nothing survives."
    ),
}


def codebook_block(codebook: dict[str, list[str]], order: list[str]) -> str:
    lines = []
    for label in order:
        triggers = codebook.get(label, [])
        gloss = f" — e.g. {', '.join(triggers[:5])}" if triggers else ""
        lines.append(f"- {label}{gloss}")
    return "\n".join(lines)


def coding_prompt(
    unit_text: str,
    unit_context: str,
    codebook: dict[str, list[str]],
    variant: PromptVariant,
    coder_id: str,
) -> str:
    order = variant.code_order(sorted(codebook), coder_id)
    rationale = (
        '\n  "rationale": "<one short sentence>",' if variant.ask_rationale else ""
    )
    return f"""{_FRAMES[variant.framing]}

CODEBOOK
{codebook_block(codebook, order)}
- UNCERTAIN — the codebook does not fit this unit

UNIT ({unit_context})
\"\"\"
{unit_text}
\"\"\"

Reply with JSON only:
{{
  "label": "<one codebook entry, or UNCERTAIN>",
  "evidence": "<a VERBATIM span copied exactly from the unit above, or null>",{rationale}
  "confidence": <0.0-1.0>
}}

The evidence must be copied character-for-character from the unit. Do not
paraphrase, summarise, or compose it. If you cannot quote it, use null."""
