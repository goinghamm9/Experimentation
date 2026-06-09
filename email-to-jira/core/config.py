"""App settings, loaded from environment / .env. All secrets live here, never in code."""
import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Tiny .env loader so we don't need python-dotenv. Existing env vars win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(BASE_DIR / ".env")


@dataclass
class Settings:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"))

    jira_base_url: str = field(default_factory=lambda: os.getenv("JIRA_BASE_URL", "https://samprand.atlassian.net"))
    jira_email: str = field(default_factory=lambda: os.getenv("JIRA_EMAIL", ""))
    jira_api_token: str = field(default_factory=lambda: os.getenv("JIRA_API_TOKEN", ""))

    gmail_label: str = field(default_factory=lambda: os.getenv("GMAIL_LABEL", "jira-intake"))
    gmail_credentials_path: str = field(default_factory=lambda: os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"))
    gmail_token_path: str = field(default_factory=lambda: os.getenv("GMAIL_TOKEN_PATH", "token.json"))

    dashboard_user: str = field(default_factory=lambda: os.getenv("DASHBOARD_USER", "operator"))
    dashboard_pass: str = field(default_factory=lambda: os.getenv("DASHBOARD_PASS", "change-me"))

    database_path: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", str(BASE_DIR / "email_to_jira.db")))
    default_project_key: str = field(default_factory=lambda: os.getenv("DEFAULT_PROJECT_KEY", "MSA"))

    prompts_dir: Path = BASE_DIR / "prompts"
    projects_dir: Path = BASE_DIR / "projects"


settings = Settings()
