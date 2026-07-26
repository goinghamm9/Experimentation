"""Command-line interface.

    python -m ethnography run    config/study.example.yaml [-o report.md]
    python -m ethnography verify config/study.example.yaml   # ethics dry-run

``run`` executes the full study and writes the field report. ``verify`` runs the
governance gate only and prints what *would* be kept / dropped / redacted —
useful for confirming the ethical posture before doing any interpretation.
"""

from __future__ import annotations

import argparse
import sys

from .config import load_study
from .ethics import AuditLog, GovernanceGate
from .adapters.base import to_observations
from .ethics.redaction import Pseudonymizer
from .pipeline import EthnographyPipeline


def _cmd_run(args: argparse.Namespace) -> int:
    loaded = load_study(args.config)
    pipeline = EthnographyPipeline(
        study=loaded.study,
        consent=loaded.consent,
        salt=loaded.salt,
        codebook=loaded.codebook,
    )
    result = pipeline.run(loaded.adapters)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(result.report_markdown)
        print(f"Report written to {args.output}")
    else:
        print(result.report_markdown)

    if result.review_queue:
        print("\n--- HUMAN REVIEW REQUIRED ---", file=sys.stderr)
        for item in result.review_queue:
            print(f"  [ ] {item}", file=sys.stderr)
    if not result.audit.verify():
        print("WARNING: audit chain failed verification", file=sys.stderr)
        return 2
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    loaded = load_study(args.config)
    audit = AuditLog()
    gate = GovernanceGate(loaded.consent, audit)
    pseudo = Pseudonymizer(loaded.salt)
    raw = [r for a in loaded.adapters for r in a.collect()]
    observations = to_observations(raw, pseudo)
    _, report = gate.apply(loaded.study, observations, {})
    print("Ethics dry-run (no analysis performed):")
    print(f"  seen:                 {report.total_seen}")
    print(f"  kept:                 {report.kept}")
    print(f"  dropped no-consent:   {report.dropped_no_consent}")
    print(f"  dropped minimization: {report.dropped_minimization}")
    print(f"  dropped retention:    {report.dropped_retention}")
    print(f"  dropped sensitive:    {report.dropped_sensitive}")
    print(f"  PII redacted:         {report.redacted}")
    print(f"  audit verified:       {audit.verify()}")
    return 0


def _load_corpus(config_path: str):
    """Ingest + gate, returning the post-gate corpus. No analysis stage sees raw data."""
    loaded = load_study(config_path)
    audit = AuditLog()
    gate = GovernanceGate(loaded.consent, audit)
    pseudo = Pseudonymizer(loaded.salt)
    raw = [r for a in loaded.adapters for r in a.collect()]
    corpus, report = gate.apply(loaded.study, to_observations(raw, pseudo), {})
    return loaded, corpus, report


def _cmd_annotate(args: argparse.Namespace) -> int:
    from .annotate import build_session, serve

    loaded, corpus, report = _load_corpus(args.config)
    if not corpus.observations:
        print("No observations survived the governance gate — nothing to code.", file=sys.stderr)
        return 1
    if not loaded.codebook:
        print("This study has no codebook. Gold coding needs the rubric it codes against.",
              file=sys.stderr)
        return 1

    print(f"Gate kept {report.kept}/{report.total_seen} observations.")
    session = build_session(
        corpus=corpus,
        codebook=loaded.codebook,
        gold_path=args.output,
        annotator=args.annotator,
        sample_size=args.sample,
        seed=args.seed,
    )
    serve(session, host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    """Compare machine coding against the human gold standard."""
    from .analysis.coding import open_code
    from .annotate import GoldStore
    from .rigor import Coder, CoderKind, assess_panel

    loaded, corpus, _ = _load_corpus(args.config)
    store = GoldStore(args.gold)
    if len(store) == 0:
        print(f"No annotations in {args.gold}. Run `ethnography annotate` first.", file=sys.stderr)
        return 1

    unit_ids = sorted({a.unit_id for a in store.annotations()})
    gold = store.gold_vector(unit_ids)

    # Machine coding restricted to the same units, as a per-unit label vector.
    codes = open_code(corpus, codebook=loaded.codebook)
    machine: dict[str, str] = {}
    for c in codes:
        for oid in c.observation_ids:
            machine.setdefault(oid, c.label)
    machine_vector = [machine.get(u) for u in unit_ids]

    coders = [
        Coder("deterministic", CoderKind.DETERMINISTIC, lineage="rules"),
        *[Coder(a, CoderKind.HUMAN, lineage="human") for a in store.annotators()],
    ]
    panel = assess_panel(
        {"deterministic": machine_vector},
        coders,
        unit_ids=unit_ids,
        gold=gold,
    )

    coded = sum(1 for g in gold if g is not None)
    print(f"Gold units: {coded} coded of {len(unit_ids)} sampled "
          f"({len(unit_ids) - coded} uncertain or outstanding)")
    print(f"Annotators: {', '.join(store.annotators()) or '(none)'}")
    print()
    if panel.validity_vs_gold:
        for cid, k in sorted(panel.validity_vs_gold.items()):
            print(f"  VALIDITY  {cid} vs human gold: κ = {k:.3f}")
    else:
        print("  VALIDITY  not computable — no overlapping coded units")
    print()
    for flag in store.quality_flags():
        print(f"  ⚠ {flag}")
    for note in panel.notes:
        print(f"  · {note}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ethnography", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_ann = sub.add_parser("annotate", help="Human gold coding UI over a probability sample")
    p_ann.add_argument("config", help="Path to the study YAML config")
    p_ann.add_argument("-o", "--output", default="gold.jsonl", help="Annotation store (JSONL)")
    p_ann.add_argument("-a", "--annotator", default="researcher", help="Annotator id")
    p_ann.add_argument("-n", "--sample", type=int, default=30, help="Units to sample")
    p_ann.add_argument("--seed", default="gold", help="Sampling seed (keep stable per study)")
    p_ann.add_argument("--host", default="127.0.0.1")
    p_ann.add_argument("--port", type=int, default=8765)
    p_ann.add_argument("--no-browser", action="store_true")
    p_ann.set_defaults(func=_cmd_annotate)

    p_val = sub.add_parser("validate", help="Score machine coding against the human gold standard")
    p_val.add_argument("config", help="Path to the study YAML config")
    p_val.add_argument("-g", "--gold", default="gold.jsonl", help="Annotation store (JSONL)")
    p_val.set_defaults(func=_cmd_validate)

    p_run = sub.add_parser("run", help="Run the full study and emit a field report")
    p_run.add_argument("config", help="Path to the study YAML config")
    p_run.add_argument("-o", "--output", help="Write report to this file instead of stdout")
    p_run.set_defaults(func=_cmd_run)

    p_verify = sub.add_parser("verify", help="Ethics dry-run: gate only, no analysis")
    p_verify.add_argument("config", help="Path to the study YAML config")
    p_verify.set_defaults(func=_cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
