#!/usr/bin/env python3
"""Merge per-agent source files (sources_A.md, sources_B.md, ...) into sources.md.

Usage: python3 merge_sources.py OUTPUT_DIR [--labels "A=Practice and market intel,B=Keywords and demand,..."]

Parallel agents must never write one shared file, so each writes sources_<LETTER>.md
with one entry per line in either of these forms (a leading "- " is optional):
    Source: A1 | publisher | URL | date accessed | what it measures | geography | year | verification depth
    Assumption: A20 | statement | reasoning | what would change it
This script rebuilds sources.md from scratch every time it runs (idempotent), keeping a
fixed header, so run it after every phase.
"""
import argparse
import re
from pathlib import Path

HEADER = """# Sources and assumptions (merged by the orchestrator)

ID convention: agent letter plus number (A1, B1, C1, ...). Sources list publisher, URL, date accessed,
what is measured, geography, year, and verification depth (page read, search snippet, or search summary).
Assumptions list the statement, the reasoning, and what would change it. Orchestrator decisions live in decisions.md.

"""
ENTRY_RE = re.compile(r"^(- )?(Source|Assumption):", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--labels", default="", help='e.g. "A=Practice and market intel,B=Keywords and demand"')
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    labels = dict(kv.split("=", 1) for kv in args.labels.split(",") if "=" in kv)
    parts = [HEADER]
    total = 0
    for f in sorted(out_dir.glob("sources_*.md")):
        letter = f.stem.split("_", 1)[1]
        entries = [l.rstrip() for l in f.read_text(encoding="utf-8").splitlines() if ENTRY_RE.match(l)]
        entries = [l if l.startswith("- ") else "- " + l for l in entries]
        parts.append(f"## Agent {letter}: {labels.get(letter, '')}".rstrip(": ") + "\n\n" + "\n".join(entries) + "\n\n")
        total += len(entries)
        print(f"{f.name}: {len(entries)} entries")
    (out_dir / "sources.md").write_text("".join(parts), encoding="utf-8")
    print(f"sources.md written with {total} entries")


if __name__ == "__main__":
    main()
