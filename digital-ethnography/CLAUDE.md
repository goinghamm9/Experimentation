# digital-ethnography — notes for Claude

Ethics-first pipeline for digital ethnographic user research over any digital
system. Ingests behavioral event logs + qualitative text, enforces an ethics
gate, and produces a Markdown field report.

## The one invariant

**The governance gate (`ethnography/ethics/governance.py`) is a hard boundary.**
No observation may reach any analysis stage without passing consent, purpose
limitation, minimization, retention, and PII redaction. If you add a code path
that reads observations, it must consume the *post-gate* `Corpus`, never raw
adapter output. Never store or propagate a raw identifier — pseudonymize at
ingest (`adapters/base.to_observations`).

## Architecture (data flow)

`adapters → to_observations (pseudonymize) → GovernanceGate.apply → analysis
(coding → axial → journeys → personas → thick descriptions) → report`.
Orchestrated in `pipeline.py`. Config/consent loaded in `config.py`.

## Conventions

- Deterministic core must work with **no network and no API key**; the LLM
  (`llm/client.py`) is optional enrichment with an `OfflineLLM` fallback.
- Anything a model produces is tagged `Provenance.LLM_ASSISTED` and must surface
  in `StudyResult.review_queue` (human-in-the-loop).
- Personas must respect the `k_min` anonymity floor — never publish a portrait
  describing fewer than `k_min` participants.
- Timezone-aware datetimes only; get "now" from `schema.utcnow()` (patchable).

## Commands

```bash
python -m pytest -q                                   # tests (offline)
python -m ethnography verify config/study.example.yaml # ethics dry-run
python -m ethnography run    config/study.example.yaml  # full report
```

## When extending

- New data source → add a `SourceAdapter` in `adapters/`; nothing else changes.
- New analysis → read `Corpus`, return schema dataclasses, set `provenance`.
- Keep the report's ethics section and limitations honest and up front.
