"""Prompt templates for the optional LLM enrichment layer.

Prompts are written to keep the model in an *interpretive assistant* role, not
an autonomous decider. They always ask for grounded, hedged output because the
result is a draft a researcher will review.
"""

from __future__ import annotations

SYSTEM = (
    "You are a research assistant supporting a digital ethnography study. "
    "You interpret already-anonymized user data. Never invent identities or "
    "facts not present in the material. Be concise, hedge appropriately, and "
    "frame outputs as drafts for a human researcher to verify."
)


def thick_description_prompt(theme_label: str, snippets: list[str]) -> str:
    joined = "\n".join(f"- {s}" for s in snippets[:15])
    return (
        f"Theme: {theme_label}\n\n"
        f"Representative anonymized excerpts:\n{joined}\n\n"
        "Write a short (3-5 sentence) 'thick description': situate the behavior "
        "in the users' apparent context and motivations. Stay grounded in the "
        "excerpts. Do not speculate about individual identities."
    )


def emergent_codes_prompt(snippets: list[str]) -> str:
    joined = "\n".join(f"- {s}" for s in snippets[:20])
    return (
        "From these anonymized user excerpts, propose up to 5 short interpretive "
        "codes (2-4 words each) capturing recurring concerns not obvious from "
        "keywords. Return one code per line, no numbering.\n\n"
        f"Excerpts:\n{joined}"
    )
