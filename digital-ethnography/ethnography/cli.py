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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ethnography", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

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
