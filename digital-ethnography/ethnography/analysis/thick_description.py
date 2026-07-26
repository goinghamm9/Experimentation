"""Thick description: situated narrative interpretation of each theme.

Named after Geertz: not just *what* happened but the layered meaning of it in
context. The deterministic version assembles a grounded narrative from the
theme's prevalence and representative excerpts. If LLM enrichment is enabled, it
drafts a richer narrative — tagged ``LLM_ASSISTED`` and requiring review.
"""

from __future__ import annotations

from ..llm.client import LLMClient
from ..llm.prompts import SYSTEM, thick_description_prompt
from ..schema import Corpus, Provenance, Theme, ThickDescription


def describe(
    corpus: Corpus,
    themes: list[Theme],
    llm: LLMClient | None = None,
    max_themes: int = 8,
) -> list[ThickDescription]:
    obs_by_id = {o.id: o for o in corpus.observations}
    out: list[ThickDescription] = []

    for theme in themes[:max_themes]:
        excerpts = _excerpts(theme, obs_by_id)
        narrative = _deterministic_narrative(corpus, theme, excerpts)
        provenance = Provenance.DETERMINISTIC

        if llm is not None and getattr(llm, "available", False) and excerpts:
            drafted = llm.complete(SYSTEM, thick_description_prompt(theme.label, excerpts))
            if drafted.strip():
                narrative = drafted.strip()
                provenance = Provenance.LLM_ASSISTED

        out.append(
            ThickDescription(
                theme_label=theme.label,
                narrative=narrative,
                provenance=provenance,
            )
        )
    return out


def _excerpts(theme: Theme, obs_by_id: dict) -> list[str]:
    seen: list[str] = []
    for oid in theme.observation_ids:
        obs = obs_by_id.get(oid)
        if obs and obs.text:
            snippet = obs.text.strip()
            if snippet and snippet not in seen:
                seen.append(snippet[:200])
        if len(seen) >= 8:
            break
    return seen


def _deterministic_narrative(corpus: Corpus, theme: Theme, excerpts: list[str]) -> str:
    n_participants = len({o.pid for o in corpus.observations if o.id in set(theme.observation_ids)})
    lead = (
        f"The theme '{theme.label}' surfaced across {theme.prevalence} observations "
        f"from {n_participants} participant(s). It is organised by the codes "
        f"{', '.join(theme.code_labels[:5])}."
    )
    if excerpts:
        voice = f' Representative account: "{excerpts[0]}"'
        return lead + voice
    return lead + " It is grounded in behavioral traces rather than direct utterances."
