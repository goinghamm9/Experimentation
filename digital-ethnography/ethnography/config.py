"""Load a study from a YAML config into runtime objects.

The config is the researcher's declared design: the study's purpose (which is
enforced as purpose limitation), the data categories it may touch, retention,
the data sources, the codebook, and — critically — the consent records. Consent
is expressed against *raw* identifiers in the file and pseudonymized on load, so
the running system never holds a raw identifier and the config author never has
to compute hashes by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .adapters.base import SourceAdapter
from .adapters.events import EventLogAdapter
from .adapters.qualitative import QualitativeAdapter
from .ethics.consent import ConsentRecord, ConsentRegistry
from .ethics.redaction import Pseudonymizer
from .schema import DataCategory, Study


@dataclass
class LoadedStudy:
    study: Study
    consent: ConsentRegistry
    adapters: list[SourceAdapter]
    salt: str
    codebook: dict[str, list[str]] | None


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def load_study(config_path: str | Path) -> LoadedStudy:
    config_path = Path(config_path)
    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    base = config_path.parent
    scfg = cfg["study"]
    salt = str(cfg["salt"])

    study = Study(
        id=scfg["id"],
        title=scfg["title"],
        purpose=scfg["purpose"],
        research_questions=scfg.get("research_questions", []),
        allowed_categories={DataCategory(c) for c in scfg.get("allowed_categories", ["behavioral", "content"])},
        retention_days=int(scfg.get("retention_days", 90)),
        llm_enrichment=bool(scfg.get("llm_enrichment", False)),
    )

    # Consent records, pseudonymized on load.
    pseudonymizer = Pseudonymizer(salt)
    registry = ConsentRegistry()
    for c in cfg.get("consent", []):
        pid = pseudonymizer.pid(str(c["identifier"]))
        registry.grant(
            ConsentRecord(
                pid=pid,
                study_id=study.id,
                purposes=set(c.get("purposes", [study.purpose])),
                categories={DataCategory(x) for x in c.get("categories", ["behavioral", "content"])},
                granted_at=_parse_dt(c.get("granted_at")) or datetime(1970, 1, 1, tzinfo=timezone.utc),
                expires_at=_parse_dt(c.get("expires_at")),
                withdrawn=bool(c.get("withdrawn", False)),
            )
        )

    # Adapters.
    adapters: list[SourceAdapter] = []
    for src in cfg.get("sources", []):
        kind = src["type"]
        path = (base / src["path"]).as_posix() if not Path(src["path"]).is_absolute() else src["path"]
        if kind == "events":
            adapters.append(
                EventLogAdapter(
                    path=path,
                    source=src.get("name", "events"),
                    id_field=src.get("id_field", "user"),
                    event_field=src.get("event_field", "event"),
                    ts_field=src.get("ts_field", "ts"),
                )
            )
        elif kind == "qualitative":
            adapters.append(
                QualitativeAdapter(
                    path=path,
                    source=src.get("name", "qualitative"),
                    id_field=src.get("id_field", "author"),
                    text_field=src.get("text_field", "text"),
                    ts_field=src.get("ts_field", "ts"),
                )
            )
        else:
            raise ValueError(f"Unknown source type: {kind}")

    codebook = cfg.get("codebook")
    return LoadedStudy(
        study=study,
        consent=registry,
        adapters=adapters,
        salt=salt,
        codebook=codebook,
    )
