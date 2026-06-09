"""Test harness — feed fixture emails through ingest → generate without Gmail.

Default is fully offline (StubLLM): no keys needed, candidates land in the
review queue so the operator can exercise the dashboard end-to-end. With
--live it calls the real Anthropic API (still never touches Jira — only the
dashboard's Approve button does that).

Usage:
    python -m scripts.harness                 # all fixtures, offline stub
    python -m scripts.harness --live          # all fixtures, real Claude
    python -m scripts.harness tests/fixtures/emails/bug_report.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import settings  # noqa: E402
from core.db import init_db, session_scope  # noqa: E402
from core.generate import generate_candidate  # noqa: E402
from core.ingest import ingest_message  # noqa: E402
from core.llm import AnthropicClient, StubLLM  # noqa: E402
from core.projects import load_all, match_project  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "emails"


def run_fixture(session, path: Path, llm) -> str:
    data = json.loads(path.read_text())
    email, created = ingest_message(
        session,
        gmail_message_id=data["gmail_message_id"],
        thread_id=data.get("thread_id", ""),
        sender=data.get("sender", ""),
        subject=data.get("subject", ""),
        body=data.get("body", ""),
        source_type=data.get("source_type", "email"),
    )
    if not created:
        return f"{path.name}: already ingested, skipped"
    project = match_project(email.sender, load_all(), settings.default_project_key)
    candidate = generate_candidate(session, email, project, llm)
    if candidate is None:
        return f"{path.name}: generation failed — surfaced in dashboard as needs-review"
    return (f"{path.name}: candidate #{candidate.id} [{candidate.project_key}/{candidate.issue_type}] "
            f"\"{candidate.summary}\" (confidence {candidate.confidence:.2f})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", nargs="*", type=Path, help="fixture JSON files (default: all)")
    parser.add_argument("--live", action="store_true", help="use the real Anthropic API instead of the stub")
    args = parser.parse_args()

    fixtures = args.fixtures or sorted(FIXTURES_DIR.glob("*.json"))
    llm = AnthropicClient() if args.live else StubLLM()

    init_db()
    with session_scope() as session:
        for path in fixtures:
            print(run_fixture(session, path, llm))
    print(f"\nDone — review the queue at http://localhost:8000 (model: "
          f"{'live ' + settings.anthropic_model if args.live else 'offline stub'})")


if __name__ == "__main__":
    main()
