"""Run a panel of coders and hand the result to the rigor layer.

This is the seam between *producing* labels and *judging* them. The runner does
no interpretation: it collects each coder's vector, records what was spent and
what was searched, and passes everything to :func:`assess_panel`, which owns the
distinction between agent agreement (a router) and validity against human gold
(the only claim available).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..rigor import Coder as PanelCoder
from ..rigor import CoderKind, PanelReport, SearchLedger, assess_panel
from ..schema import Observation
from .base import CodingResult


@dataclass
class PanelRun:
    unit_ids: list[str]
    results: list[CodingResult]
    report: PanelReport
    ledger: SearchLedger
    gold_units: int = 0
    quality_flags: list[str] = field(default_factory=list)

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.results)

    @property
    def lineages(self) -> set[str]:
        return {r.lineage for r in self.results}

    def summary(self) -> str:
        lines = [
            f"{len(self.results)} coders across {len(self.lineages)} lineage(s) "
            f"over {len(self.unit_ids)} units",
            f"  {self.report.summary()}",
            f"  {self.ledger.summary(len(self.unit_ids))}",
        ]
        if len(self.lineages) < 2 and len(self.results) > 1:
            lines.append(
                "  ⚠ all coders share one lineage — additional coders add confidence, "
                "not evidence"
            )
        for f in self.quality_flags:
            lines.append(f"  ⚠ {f}")
        return "\n".join(lines)


def run_panel(
    coders: list,
    observations: list[Observation],
    gold: list[str | None] | None = None,
    unit_ids: list[str] | None = None,
    require_evidence: bool = True,
    restart_counts: dict[str, int] | None = None,
) -> PanelRun:
    """Code ``observations`` with every coder, then assess the panel.

    ``gold`` aligns to ``unit_ids`` and comes from the human annotation store. Its
    absence is not neutral: without it the run yields no validity evidence, and
    :func:`assess_panel` says so explicitly rather than reporting agreement as a
    score.
    """
    ids = unit_ids or [o.id for o in observations]
    results = [c.code(observations) for c in coders]

    answers = {r.coder_id: r.label_vector(ids, require_evidence) for r in results}

    kind_for = {"rules": CoderKind.DETERMINISTIC, "human": CoderKind.HUMAN}
    panel_coders = [
        PanelCoder(
            id=r.coder_id,
            kind=kind_for.get(r.lineage, CoderKind.MODEL),
            lineage=r.lineage,
        )
        for r in results
    ]

    ledger = SearchLedger()
    for r in results:
        ledger.record(f"coding:{r.coder_id}", r.hypotheses_considered)

    report = assess_panel(
        answers,
        panel_coders,
        unit_ids=ids,
        gold=gold,
        restart_counts=restart_counts,
    )

    flags: list[str] = []
    for r in results:
        flags.extend(r.quality_flags())

    return PanelRun(
        unit_ids=ids,
        results=results,
        report=report,
        ledger=ledger,
        gold_units=sum(1 for g in (gold or []) if g is not None),
        quality_flags=flags,
    )
