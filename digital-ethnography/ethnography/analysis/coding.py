"""Thematic coding: open coding then axial clustering into themes.

Method mirrors grounded-theory practice:

* **Open coding** — attach short interpretive labels to observations. Two
  deterministic sources: (a) a *codebook* the researcher supplies (keyword ->
  code, the a-priori frame) and (b) *emergent* codes from salient repeated terms
  the codebook missed. An optional LLM pass proposes further emergent codes,
  clearly marked ``LLM_ASSISTED``.
* **Axial coding** — group co-occurring codes into higher-order themes.

Everything is reproducible from the corpus alone; the LLM only ever *adds*
candidate codes for a human to accept or reject.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from ..llm.client import LLMClient
from ..llm.prompts import SYSTEM, emergent_codes_prompt
from ..schema import Code, Corpus, Observation, Provenance, Theme

# Words too common to be interesting emergent codes.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "for", "is",
    "it", "this", "that", "was", "with", "i", "my", "me", "we", "you", "they",
    "at", "be", "as", "so", "if", "not", "no", "have", "has", "had", "just",
    "app", "very", "really", "would", "could", "when", "then", "there", "get",
}

_WORD = re.compile(r"[a-z][a-z']+")


def _tokens(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if w not in _STOPWORDS and len(w) > 3]


def open_code(
    corpus: Corpus,
    codebook: dict[str, list[str]] | None = None,
    llm: LLMClient | None = None,
    min_emergent_freq: int = 3,
) -> list[Code]:
    """Return open codes over the corpus.

    ``codebook`` maps a code label to trigger keywords/phrases. Emergent codes
    are frequent salient terms not already covered by the codebook.
    """
    codebook = codebook or _DEFAULT_CODEBOOK
    codes: dict[str, Code] = {}

    # (a) Codebook-driven coding across event names and free text.
    for obs in corpus.observations:
        haystack = _observation_text(obs).lower()
        for label, triggers in codebook.items():
            if any(t.lower() in haystack for t in triggers):
                code = codes.setdefault(
                    label,
                    Code(label=label, definition=f"Mentions/relates to: {label}"),
                )
                code.observation_ids.append(obs.id)

    covered_terms = {t.lower() for terms in codebook.values() for t in terms}

    # (b) Emergent codes from repeated salient terms in free text.
    term_to_obs: dict[str, list[str]] = defaultdict(list)
    for obs in corpus.observations:
        if not obs.text:
            continue
        for tok in set(_tokens(obs.text)):
            if tok not in covered_terms:
                term_to_obs[tok].append(obs.id)
    freq = Counter({t: len(ids) for t, ids in term_to_obs.items()})
    for term, count in freq.items():
        if count >= min_emergent_freq:
            label = f"emergent:{term}"
            codes[label] = Code(
                label=label,
                definition=f"Emergent term '{term}' recurred {count}x",
                observation_ids=list(term_to_obs[term]),
            )

    # (c) Optional LLM-proposed emergent codes (drafts only).
    if llm is not None and getattr(llm, "available", False):
        snippets = [o.text for o in corpus.observations if o.text][:20]
        if snippets:
            raw = llm.complete(SYSTEM, emergent_codes_prompt(snippets))
            for line in (raw or "").splitlines():
                label = line.strip("-* \t").strip()
                if label:
                    key = f"llm:{label.lower()}"
                    codes.setdefault(
                        key,
                        Code(
                            label=label,
                            definition="LLM-proposed emergent code (review required)",
                            provenance=Provenance.LLM_ASSISTED,
                            confidence=0.5,
                        ),
                    )

    return sorted(codes.values(), key=lambda c: (-len(c.observation_ids), c.label))


def axial_code(codes: list[Code], min_theme_size: int = 2) -> list[Theme]:
    """Cluster codes into themes by shared observations (co-occurrence).

    A theme collects codes that frequently apply to the same observations,
    approximating the analyst's move from fragmented codes to organizing
    categories. Uses a simple connected-components grouping on co-occurrence.
    """
    coded = [c for c in codes if c.observation_ids]
    parent: dict[str, str] = {c.label: c.label for c in coded}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        parent[find(a)] = find(b)

    # Link two codes if they share observations.
    for i, a in enumerate(coded):
        set_a = set(a.observation_ids)
        for b in coded[i + 1 :]:
            if set_a & set(b.observation_ids):
                union(a.label, b.label)

    groups: dict[str, list[Code]] = defaultdict(list)
    for c in coded:
        groups[find(c.label)].append(c)

    themes: list[Theme] = []
    for members in groups.values():
        if len(members) < min_theme_size:
            continue
        obs_ids: list[str] = []
        for c in members:
            obs_ids.extend(c.observation_ids)
        label = " + ".join(sorted(m.label for m in members)[:3])
        has_llm = any(m.provenance == Provenance.LLM_ASSISTED for m in members)
        themes.append(
            Theme(
                label=label,
                description="Codes that recur together across observations.",
                code_labels=[m.label for m in members],
                observation_ids=sorted(set(obs_ids)),
                provenance=Provenance.LLM_ASSISTED if has_llm else Provenance.DETERMINISTIC,
            )
        )
    return sorted(themes, key=lambda t: -t.prevalence)


def _observation_text(obs: Observation) -> str:
    parts = [obs.text or ""]
    ev = obs.payload.get("event")
    if ev:
        parts.append(str(ev))
    return " ".join(parts)


# A small default codebook so the tool produces something useful out of the box.
_DEFAULT_CODEBOOK: dict[str, list[str]] = {
    "onboarding_friction": ["onboard", "sign up", "signup", "confusing", "setup", "get started"],
    "checkout_flow": ["checkout", "cart", "payment", "pay", "purchase", "buy"],
    "error_or_bug": ["error", "crash", "bug", "broken", "fail", "stuck"],
    "trust_and_privacy": ["privacy", "trust", "data", "permission", "secure", "scam"],
    "value_and_delight": ["love", "great", "helpful", "easy", "amazing", "delight"],
    "abandonment": ["gave up", "quit", "uninstall", "left", "abandon", "cancel"],
}
