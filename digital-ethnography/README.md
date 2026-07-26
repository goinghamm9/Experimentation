# digital-ethnography

An ethics-first pipeline for **digital ethnographic user research** over *any*
digital system. It ingests the traces a system already produces — behavioral
event logs and qualitative text (reviews, interviews, support, forums) — and
turns them into a reviewable ethnographic field report: themes, thick
descriptions, user journeys with friction points, and anonymized personas.

The defining property is that **ethics is a hard gate, not a checklist**. No
observation reaches any analysis stage unless it passes consent, purpose
limitation, data minimization, retention, and PII redaction. Every decision is
written to a tamper-evident audit log.

```
adapters ─▶ pseudonymize ─▶ ┃ GOVERNANCE GATE ┃ ─▶ coding ─▶ themes
 (any source)               ┃ consent          ┃      │
                            ┃ purpose limit    ┃      ├─▶ journeys + friction
                            ┃ minimization     ┃      ├─▶ personas (k-anonymous)
                            ┃ retention        ┃      └─▶ thick descriptions
                            ┃ PII redaction    ┃              │
                            ┗━━━━━━━━━━━━━━━━━━━┛      ─▶ field report (Markdown)
                                    │
                                 audit log (hash-chained)
```

## Why this is "ethical by design"

| Principle | How it is enforced (in code) |
| --- | --- |
| **Informed consent** | `ethics/consent.py` — a default-deny registry. Data for a participant without a valid, unexpired, purpose-matched consent record is dropped at the gate. |
| **Purpose limitation** | The study declares one `purpose`; consent must name that purpose or the data is refused. |
| **Data minimization** | The study declares `allowed_categories`; anything outside them is dropped even if consent exists. |
| **Anonymity** | `ethics/redaction.py` — raw identifiers are salted-hashed to pseudonyms at ingest and discarded. Free-text PII (emails, phones, SSNs, cards, IPs, handles) is redacted before retention. |
| **k-anonymity** | Personas require a minimum membership (`k_min`, default 3); no portrait can describe a single person. |
| **Right to erasure** | `GovernanceGate.erase_participant` cascades deletion of all of a participant's observations; withdrawal in the consent registry revokes future access. |
| **Retention limits** | Observations past `retention_days` from their timestamp are dropped. |
| **Accountability** | `ethics/audit.py` — every keep/drop/redact/erase is recorded in a SHA-256 hash-chained log with `verify()` tamper detection. |
| **Human-in-the-loop** | AI is *optional enrichment only*. Anything a model drafts is tagged `LLM_ASSISTED` and surfaced in a `review_queue`; the deterministic core produces a complete report with no model calls. |
| **Interpretive honesty** | The report foregrounds a limitations section and provenance flags (⚠️) on machine-drafted sections. |

## Quick start

```bash
cd digital-ethnography
pip install -r requirements.txt

# 1. Ethics dry-run: see what WOULD be kept / dropped / redacted, no analysis.
python -m ethnography verify config/study.example.yaml

# 2. Full study: emits the Markdown field report.
python -m ethnography run config/study.example.yaml -o report.md

# Or via make:
make verify
make run
make test
```

Runs **fully offline** — no API key required. The example study ships with
sample event and review data and demonstrates the gate dropping non-consenting
users and redacting PII.

## Designing a study

A study is one YAML file (`config/study.example.yaml`). It declares the purpose,
the data categories the study may touch, retention, the data sources, an
optional a-priori codebook, and the consent records (against raw identifiers,
which are pseudonymized on load — the running system never holds them).

## Supporting a new digital system

Implement one adapter — everything downstream is reused. An adapter turns a
source into a stream of `RawRecord`s, declaring the data category and the raw
identifier to pseudonymize:

```python
from ethnography.adapters.base import RawRecord, SourceAdapter
from ethnography.schema import DataCategory, ObservationKind

class MyAdapter:
    name = "my_system"
    def collect(self):
        for row in my_export():
            yield RawRecord(
                raw_identifier=row["user_id"],
                kind=ObservationKind.EVENT,
                category=DataCategory.BEHAVIORAL,
                timestamp=row["ts"],
                source=self.name,
                payload={"event": row["action"]},
            )
```

Built-in adapters: `EventLogAdapter` (behavioral JSONL) and `QualitativeAdapter`
(text JSONL: reviews, interviews, forum/support posts).

## Optional LLM enrichment

Set `llm_enrichment: true` in the study config and export `ANTHROPIC_API_KEY` to
let a model propose additional emergent codes and richer thick descriptions.
These outputs are always tagged `LLM_ASSISTED`, flagged `needs_review`, and
listed in `StudyResult.review_queue`. Without a key (or the `anthropic` package)
the pipeline degrades gracefully to the deterministic core.

## Layout

```
ethnography/
  schema.py          # normalized data model + provenance
  ethics/            # consent, redaction, governance gate, audit log
  adapters/          # ingest for any digital system (events, qualitative)
  analysis/          # coding, journeys+friction, personas, thick description
  llm/               # optional enrichment (offline fallback)
  report/            # Markdown field report
  pipeline.py        # orchestration (gate is the hard boundary)
  config.py, cli.py  # study loading + `run` / `verify` commands
config/              # example study
examples/            # sample event + review data
tests/               # ethics, analysis, and end-to-end tests
```

## Scope & honest limitations

This is a research *scaffold*, not a compliance product. It gives you a defensible
default posture and a place to encode your own IRB/ethics-board requirements —
but consent collection, lawful basis, and jurisdiction-specific obligations
(GDPR, CCPA, etc.) remain the researcher's responsibility. Findings are
interpretive, not statistical. The PII redactor is a conservative regex floor;
layer an NER model for higher recall on names and addresses.
