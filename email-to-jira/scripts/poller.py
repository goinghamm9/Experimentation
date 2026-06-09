"""Email poller — run as a cron job / on demand, separate from the web app.

Fetches messages under the configured Gmail label, ingests anything new
(idempotent), and drafts a ticket candidate per new source. Drafts only:
nothing here touches Jira — issues are created solely from the dashboard's
Approve button.

Usage:  python -m scripts.poller          (live Gmail + live Claude)
        crontab: */15 * * * * cd .../email-to-jira && .venv/bin/python -m scripts.poller
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import settings  # noqa: E402
from core.db import init_db, session_scope  # noqa: E402
from core.generate import generate_candidate  # noqa: E402
from core.ingest import ingest_message  # noqa: E402
from core.projects import load_all, match_project  # noqa: E402


def poll_once(session, gmail, llm) -> dict:
    """One poll cycle. gmail needs fetch_labeled_messages(); llm needs complete()."""
    configs = load_all()
    stats = {"seen": 0, "ingested": 0, "drafted": 0, "needs_review": 0}
    for msg in gmail.fetch_labeled_messages():
        stats["seen"] += 1
        email, created = ingest_message(
            session,
            gmail_message_id=msg["gmail_message_id"],
            thread_id=msg.get("thread_id", ""),
            sender=msg.get("sender", ""),
            subject=msg.get("subject", ""),
            body=msg.get("body", ""),
            source_type=msg.get("source_type", "email"),
            attachments_meta=msg.get("attachments_meta"),
        )
        if not created:
            continue
        stats["ingested"] += 1
        project = match_project(email.sender, configs, settings.default_project_key)
        candidate = generate_candidate(session, email, project, llm)
        stats["drafted" if candidate else "needs_review"] += 1
    return stats


def main() -> None:
    from core.gmail_client import GmailPoller
    from core.llm import AnthropicClient

    init_db()
    with session_scope() as session:
        stats = poll_once(session, GmailPoller(), AnthropicClient())
    print(f"poll complete: {stats}")


if __name__ == "__main__":
    main()
