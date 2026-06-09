"""Load per-board YAML configs. Board knowledge lives in projects/*.yaml, not code."""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from core.config import settings


@dataclass
class ProjectConfig:
    key: str
    name: str = ""
    enabled: bool = False
    allowed_issue_types: list[str] = field(default_factory=lambda: ["Task"])
    default_issue_type: str = "Task"
    set_sprint_on_subtasks: bool = True  # PV0 must set this False (Jira rejects it)
    conventions: str = ""
    board_rules: str = ""
    glossary: dict[str, str] = field(default_factory=dict)
    few_shot_examples: list[dict] = field(default_factory=list)
    sender_domains: list[str] = field(default_factory=list)  # match emails to this board

    @classmethod
    def from_yaml(cls, path: Path) -> "ProjectConfig":
        data = yaml.safe_load(path.read_text()) or {}
        key = data.get("project_key", path.stem)
        # Few-shots come from two places: inline in the board YAML (hand-edited)
        # and projects/examples/<KEY>.yaml (written by the dashboard's
        # "Save as example" / paste form). Both feed the prompt identically.
        examples = list(data.get("few_shot_examples") or [])
        examples += _load_example_store(path.parent, key)
        return cls(
            key=key,
            name=data.get("name", ""),
            enabled=bool(data.get("enabled", False)),
            allowed_issue_types=data.get("allowed_issue_types") or ["Task"],
            default_issue_type=data.get("default_issue_type", "Task"),
            set_sprint_on_subtasks=bool(data.get("set_sprint_on_subtasks", True)),
            conventions=data.get("conventions", "") or "",
            board_rules=data.get("board_rules", "") or "",
            glossary=data.get("glossary") or {},
            few_shot_examples=examples,
            sender_domains=data.get("sender_domains") or [],
        )


def _example_store_path(projects_dir: Path, key: str) -> Path:
    return projects_dir / "examples" / f"{key}.yaml"


def _load_example_store(projects_dir: Path, key: str) -> list[dict]:
    path = _example_store_path(projects_dir, key)
    if not path.exists():
        return []
    return yaml.safe_load(path.read_text()) or []


def append_example(key: str, source: str, ticket: dict, projects_dir: Path | None = None) -> int:
    """Append a few-shot example (source text -> ideal ticket) to the board's
    example store. Returns the new example count for the board."""
    directory = projects_dir or settings.projects_dir
    path = _example_store_path(directory, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    examples = _load_example_store(directory, key)
    examples.append({"source": source, "ticket": ticket})
    path.write_text(yaml.safe_dump(examples, allow_unicode=True, sort_keys=False))
    return len(examples)


def load_all(projects_dir: Path | None = None) -> dict[str, ProjectConfig]:
    directory = projects_dir or settings.projects_dir
    configs: dict[str, ProjectConfig] = {}
    for path in sorted(directory.glob("*.yaml")):
        if path.stem.startswith("_"):  # _TEMPLATE.yaml
            continue
        cfg = ProjectConfig.from_yaml(path)
        configs[cfg.key] = cfg
    return configs


def load_project(key: str, projects_dir: Path | None = None) -> ProjectConfig:
    directory = projects_dir or settings.projects_dir
    path = directory / f"{key}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No config for board {key!r} at {path}")
    return ProjectConfig.from_yaml(path)


def match_project(sender: str, configs: dict[str, ProjectConfig], default_key: str) -> ProjectConfig:
    """Pick a board for an email by sender domain; fall back to the default board."""
    domain = sender.rsplit("@", 1)[-1].lower().strip(">").strip()
    for cfg in configs.values():
        if not cfg.enabled:
            continue
        if any(domain == d.lower() or domain.endswith("." + d.lower()) for d in cfg.sender_domains):
            return cfg
    return configs[default_key]
