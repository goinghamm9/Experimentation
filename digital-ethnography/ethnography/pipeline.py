"""End-to-end orchestration of an ethnographic study.

Wiring, in order:

    adapters -> pseudonymize -> GOVERNANCE GATE -> open/axial coding
             -> journeys -> personas -> thick descriptions -> field report

The governance gate is the hard boundary: nothing that fails consent,
minimization, retention, or sensitivity checks is visible to any analysis stage.
The pipeline returns a :class:`StudyResult` carrying both the human-facing report
and the machine-readable artifacts (plus the audit log) for further processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .adapters.base import SourceAdapter, to_observations
from .analysis import axial_code, describe, open_code, reconstruct, synthesize
from .ethics import AuditLog, ConsentRegistry, GateReport, GovernanceGate, Pseudonymizer
from .llm.client import LLMClient, build_client
from .report import ReportInputs, render_markdown
from .schema import (
    Code,
    Corpus,
    Journey,
    Persona,
    Study,
    Theme,
    ThickDescription,
)


@dataclass
class StudyResult:
    corpus: Corpus
    gate: GateReport
    codes: list[Code]
    themes: list[Theme]
    journeys: list[Journey]
    personas: list[Persona]
    descriptions: list[ThickDescription]
    audit: AuditLog
    report_markdown: str

    @property
    def review_queue(self) -> list[str]:
        """Human-in-the-loop: everything a model drafted that needs review."""
        items = [f"code: {c.label}" for c in self.codes if c.needs_review]
        items += [f"description: {d.theme_label}" for d in self.descriptions if d.needs_review]
        return items


class EthnographyPipeline:
    def __init__(
        self,
        study: Study,
        consent: ConsentRegistry,
        salt: str,
        codebook: dict[str, list[str]] | None = None,
        llm: LLMClient | None = None,
        audit: AuditLog | None = None,
    ) -> None:
        self.study = study
        self.consent = consent
        self.pseudonymizer = Pseudonymizer(salt)
        self.codebook = codebook
        self.audit = audit or AuditLog()
        self.llm = llm if llm is not None else build_client(study.llm_enrichment)
        self.gate = GovernanceGate(consent, self.audit)

    def run(self, adapters: Iterable[SourceAdapter]) -> StudyResult:
        self.audit.record("study_start", self.study.id, purpose=self.study.purpose)

        # 1. Ingest + pseudonymize.
        raw = []
        for adapter in adapters:
            self.audit.record("ingest", adapter.name)
            raw.extend(adapter.collect())
        observations = to_observations(raw, self.pseudonymizer)

        participants: dict = {}  # gate rebuilds participants from survivors

        # 2. GOVERNANCE GATE (hard boundary).
        corpus, gate_report = self.gate.apply(self.study, observations, participants)

        # 3. Coding.
        codes = open_code(corpus, codebook=self.codebook, llm=self.llm)
        themes = axial_code(codes)

        # 4. Journeys.
        journeys = reconstruct(corpus)

        # 5. Personas.
        personas = synthesize(corpus, codes)

        # 6. Thick descriptions.
        descriptions = describe(corpus, themes, llm=self.llm)

        # 7. Report.
        report_inputs = ReportInputs(
            corpus=corpus,
            gate=gate_report,
            themes=themes,
            journeys=journeys,
            personas=personas,
            descriptions=descriptions,
            audit=self.audit,
        )
        report_md = render_markdown(report_inputs)
        self.audit.record("study_complete", self.study.id, themes=len(themes))

        return StudyResult(
            corpus=corpus,
            gate=gate_report,
            codes=codes,
            themes=themes,
            journeys=journeys,
            personas=personas,
            descriptions=descriptions,
            audit=self.audit,
            report_markdown=report_md,
        )
