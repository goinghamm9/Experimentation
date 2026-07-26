"""Field report assembly.

Produces a Markdown research report that a human researcher can read, verify,
and hand to stakeholders. The report deliberately foregrounds:

* an **ethics statement** and the governance gate's numbers, so readers know
  what was collected, dropped, and redacted, and on what basis;
* **provenance flags** on every machine-drafted section (⚠ = needs review);
* explicit **limitations**, because ethnography is interpretive, not a
  measurement.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ethics.audit import AuditLog
from ..ethics.governance import GateReport
from ..schema import (
    Corpus,
    Journey,
    Persona,
    Provenance,
    Theme,
    ThickDescription,
)
from ..analysis.journeys import friction_index


@dataclass
class ReportInputs:
    corpus: Corpus
    gate: GateReport
    themes: list[Theme]
    journeys: list[Journey]
    personas: list[Persona]
    descriptions: list[ThickDescription]
    audit: AuditLog
    saturation: object | None = None
    reliability: object | None = None
    search: object | None = None


def render_markdown(data: ReportInputs) -> str:
    s = data.corpus.study
    lines: list[str] = []
    add = lines.append

    add(f"# Digital Ethnography Field Report: {s.title}")
    add("")
    add(f"**Study purpose:** {s.purpose}")
    if s.research_questions:
        add("")
        add("**Research questions:**")
        for q in s.research_questions:
            add(f"- {q}")
    add("")

    # --- Ethics & provenance up front, not buried. ---
    add("## Ethics & Data Governance")
    add("")
    add(
        "This study processed only data for which participants gave valid, "
        "purpose-matched consent. Identities were pseudonymized at ingest; free "
        "text was scrubbed of personal information before retention."
    )
    add("")
    g = data.gate
    add("| Governance outcome | Count |")
    add("| --- | --- |")
    add(f"| Observations seen | {g.total_seen} |")
    add(f"| Kept (consented, minimized, in-retention) | {g.kept} |")
    add(f"| Dropped — no/expired consent | {g.dropped_no_consent} |")
    add(f"| Dropped — data minimization | {g.dropped_minimization} |")
    add(f"| Dropped — retention expired | {g.dropped_retention} |")
    add(f"| Dropped — sensitive not permitted | {g.dropped_sensitive} |")
    add(f"| Observations with PII redacted | {g.redacted} |")
    add("")
    add(f"- **Participants (pseudonymous):** {len(data.corpus.participants)}")
    add(f"- **Retention horizon:** {s.retention_days} days from observation")
    add(f"- **Audit chain integrity:** {'VERIFIED ✅' if data.audit.verify() else 'BROKEN ❌'}")
    add(f"- **Audit events recorded:** {len(data.audit.events())}")
    add("")

    # --- Rigor: the numbers that qualify every claim below. ---
    add("## Methodological Rigor")
    add("")
    sat = data.saturation
    if sat is not None:
        add("### Saturation")
        add("")
        add(f"- **Sampling units (participants):** {sat.n_units}")
        add(f"- **Codes observed:** {sat.n_codes_observed} "
            f"(seen once: {sat.f1}, seen twice: {sat.f2})")
        add(f"- **Good–Turing unseen mass (`f₁/n`):** {sat.unseen_mass:.3f}")
        add(f"- **Chao1 projected richness:** {sat.chao1_bias_corrected:.1f} "
            f"→ ~{sat.projected_unseen:.1f} code(s) not yet observed")
        add("")
        if sat.is_saturated:
            add("_Singleton rate below 0.05 — consistent with approaching saturation. "
                "This is evidence, not proof; saturation is asymptotic and never reached._")
        else:
            add("⚠️ _Singleton rate at or above 0.05 — **not saturated**. New codes were "
                "still emerging when collection stopped, so absent themes cannot be "
                "interpreted as absent from the population._")
        add("")

    rel = data.reliability
    if rel is not None:
        add("### Coder reliability")
        add("")
        if rel.alpha is None:
            add(f"- **Krippendorff's α:** not computable ({rel.n_coders} coder)")
            add(f"- ⚠️ {rel.note}")
        else:
            add(f"- **Krippendorff's α:** {rel.alpha:.3f} ({rel.interpretation()})")
            add(f"- **Coders:** {rel.n_coders} nominal → "
                f"**{rel.n_eff:.2f} effective** (ρ={rel.rho:.2f})")
            add(f"- _{rel.note}_")
        add("")

    if data.search is not None:
        r = data.search.report(len(data.corpus.observations))
        add("### Search-space accounting")
        add("")
        add(f"- **Hypotheses considered (`m`):** {int(r['m_hypotheses'])}")
        add(f"- **Nominal α:** {r['alpha_nominal']:.2f} → "
            f"**effective α: {r['alpha_effective']:.3f}**")
        add(f"- **Expected largest spurious \\|r\\| under the null:** "
            f"{r['expected_max_spurious_r']:.3f}")
        add("")
        add("_A system that does not log `m` cannot state what its findings mean._")
        add("")

    add("> **These findings are a ranked queue, not a set of conclusions.** They are "
        "interpretive claims qualified by the numbers above, and every estimator here "
        "takes the coding scheme as given.")
    add("")

    # --- Findings. ---
    add("## Findings")
    add("")
    add(f"- **Friction index (mean friction points / journey):** {friction_index(data.journeys):.2f}")
    add(f"- **Themes identified:** {len(data.themes)}")
    add("")

    add("### Themes & Thick Descriptions")
    add("")
    desc_by_theme = {d.theme_label: d for d in data.descriptions}
    if not data.themes:
        add("_No themes met the minimum support threshold._")
    for theme in data.themes:
        flag = " ⚠️ _needs review_" if theme.provenance == Provenance.LLM_ASSISTED else ""
        add(f"#### {theme.label} — {theme.prevalence} observations{flag}")
        d = desc_by_theme.get(theme.label)
        if d:
            rflag = " ⚠️ _LLM draft, review required_" if d.needs_review else ""
            add("")
            add(d.narrative + rflag)
        add("")

    # --- Personas. ---
    add("### Personas")
    add("")
    add("_Aggregate portraits with a minimum membership; not real individuals._")
    add("")
    if not data.personas:
        add("_Not enough participants to form anonymized personas._")
    for p in data.personas:
        add(f"- **{p.label}** (n={p.size}) — {p.description}")
    add("")

    # --- Journeys summary. ---
    add("### Journeys & Friction")
    add("")
    high_friction = sorted(data.journeys, key=lambda j: -len(j.friction))[:5]
    if not any(j.friction for j in data.journeys):
        add("_No friction points detected in reconstructed journeys._")
    for j in high_friction:
        if not j.friction:
            continue
        reasons = ", ".join(sorted({f.reason for f in j.friction}))
        add(f"- `{j.pid}` — {len(j.step_ids)} steps, {len(j.friction)} friction point(s): {reasons}")
    add("")

    # --- Limitations. ---
    add("## Limitations")
    add("")
    add(
        "- Findings are interpretive, not statistical; codes and themes reflect "
        "analyst and (where used) model judgment.\n"
        "- Only consented, minimized data was analyzed, so behavior of "
        "non-consenting users is absent by design.\n"
        "- Sections flagged ⚠️ were drafted with model assistance and require "
        "researcher verification before external use."
    )
    add("")
    add("---")
    add("_Generated by the digital-ethnography pipeline. Review flagged sections before distribution._")
    return "\n".join(lines)
