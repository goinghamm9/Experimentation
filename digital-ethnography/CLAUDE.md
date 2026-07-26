# digital-ethnography — notes for Claude

**Digital Ethnographic Intelligence** — an AI-native platform that continuously and ethically *observes*
digital behaviour and online culture and returns rigorous, **cited** ethnographic insight. Roadmap: web app →
public API → MCP server, all over one engine.

⚠️ **This directory currently contains only the governance kernel** — a pure, offline Python package that is
the reference implementation of the ethics gate. The platform described in `docs/` is **not built yet**.
Do not mistake the kernel for the product.

## Read before doing anything substantial

| Doc | What it is |
|---|---|
| `docs/STRATEGY_AND_ARCHITECTURE.md` | **Source of truth.** Positioning, method, agent architecture, data pipeline, recruitment, infra (§11), rigor layer (§12) |
| `docs/formal-models-for-ethnographic-research.md` | The founder's formal corpus (§0–§18). The measurement mathematics. **Cite section numbers when applying it** |
| `docs/architecture-overview.html` | Visual overview (published artifact) |

## The three invariants

1. **The governance gate is a hard boundary.** No observation reaches any analysis stage without passing
   consent, purpose limitation, minimisation, retention, and PII redaction. Any new code path that reads
   observations consumes the *post-gate* `Corpus`, never raw adapter output. Never store or propagate a raw
   identifier — pseudonymise at ingest (`adapters/base.to_observations`).
2. **Provenance is the primary key.** Every claim carries evidence spans back to source. The same edge set that
   produces citations makes cascading erasure a bounded graph walk. Provenance is captured **at ingest**, never
   bolted on.
3. **AI augments a human interpreter; it never replaces one.** Anything a model produces is tagged
   `LLM_ASSISTED` and must surface in a review queue. The deterministic core must work with **no network and no
   API key** — this keeps tests hermetic and the tool usable air-gapped.

## Decisions already made — do not relitigate

Researched and adversarially fact-checked. See §11–§12 of the strategy doc for evidence.

| Area | Decision |
|---|---|
| Orchestration | **Temporal** (MIT) outside, plain typed Python inside. Workflow = the study; Activity = one bounded, idempotent, cost-attributed call |
| Agent framework | **None as backbone.** `langgraph-api` is Elastic 2.0 — prohibits hosted-service offering |
| Data | **One Postgres.** pgvector in the *same* DB, partitioned by `(tenant_id, study_id)` so isolation is inherited from RLS |
| Inference default | **Bedrock EU in-region endpoints.** Anthropic first-party has no EU option. The Bedrock *EU inference profile* routes to Zurich/London — outside the EEA. Use in-region endpoints only |
| Self-hosted inference | **vLLM** (not NIM — it wraps vLLM and ships prefix caching *disabled*). Sovereign pod is a premium SKU, not a cost saving |
| Open weights | Qwen 3.5 / Gemma 4 / Mistral Large 3. **Not Hermes** — Llama-3.1 derivative whose licence forces "Built with Meta Llama 3.1" onto a governance-branded UI |
| Observability | **Self-hosted Langfuse** (MIT `oss`), OTel-instrumented so it stays a swappable sink and never becomes a sub-processor |
| Gateway | **Self-hosted LiteLLM** — per-tenant keys, synchronous hard budget caps |
| Hosting | Render/Railway EU → AWS `eu-central-1`. **Hostinger is not viable** as primary (no GPU/K8s/object storage/managed Postgres/KMS/VPC/SOC 2) — marketing site only, outside the compliance boundary |
| Skip at MVP | Graph DB, search engine, OLAP, agent-memory vendors, **Kubernetes** |

**Two one-way doors:** a model-gateway abstraction from commit #1 (never call a provider SDK from app code;
route by capability profile, not model name), and a tenant→region pin in the data model even with one region.

## Corrections already applied — do not reintroduce

These were mistakes in earlier drafts. They are fixed; re-introducing them is a regression.

- ❌ **Do not use inter-model κ as a reliability or validity claim.** LLM judges from one family are correlated
  (~1 effective judge); α measures *shared professional vision*, not truth (corpus §15.6). Use **Cultural
  Consensus Theory** (rank-one corrected agreement matrix, competence-weighted aggregation) with
  **Marchenko–Pastur** for the signal/noise threshold, report `n_eff`, and use κ *against a human gold
  codebook* only. κ between models is a **disagreement router** for human attention, nothing more.
- ❌ **Do not try to build an unbiased judge.** Accept the judge is biased and correct it statistically —
  **PPI/DSL** against a gold **probability** sample (corpus §13.8).
- ❌ **Do not recommend Presidio as the PII layer.** 0.07 recall on high-sensitivity PII vs 0.74–0.77 for LLM
  detectors. Use an in-VPC LLM detector as primary, regex/NER as tripwire only.
- ❌ **Do not spawn agents dynamically without logging `m`.** `max|r| ≈ √(2 ln m / n)` — a system that doesn't
  account for its own search space cannot state what its findings mean. Hard cap + `α_eff` reporting.
- ❌ **Do not code on machine translation.** It destroys the indexical/pragmatic signal (register, honorifics,
  code-switching) that the linguistic layer exists to capture. Translate for the reading view only.
- ❌ **Do not market "reliable/objective automated coding."** Reflexive TA rejects IRR as a category error;
  support both epistemologies and never conflate them.

## The rigor layer is the differentiator

The insight category is crowded; **the rigor layer is not productised anywhere**. When implementing analysis,
reach for the estimator, not a vibe. Map in strategy §12.4. Minimum set:

- **Stopping** → Good–Turing `f₁/n`, Chao1. Saturation is an auditable number, never "no new themes emerged."
- **Reliability** → Krippendorff's α + G-theory variance components (tells you coders-vs-informants).
- **Corpus-scale annotation** → PPI/DSL.
- **Uncertainty** → conformal intervals, not point estimates.
- **Drift** → CUSUM/BOCPD on `f₁/n`.
- **Comparability** → measurement invariance (configural→metric→scalar, ΔCFI<0.01). Required across languages
  *and* across time. **Pin the coder model for a study's life**; frontier deprecation otherwise confounds model
  drift with the cultural signal.
- **Output honesty** → ranked queue, never a finding. State PPV at the real base rate; report `n_eff` deflated
  for both correlation and tails.

Six controls must be **architectural, not procedural**: search-space accounting, base-rate honesty, `n_eff` on
both axes, holonomy/invariance check on every schema migration, survivorship correction (sample the graveyard —
churned users, dead communities, refusals), conformal intervals.

## Hard scope boundaries

- 🚫 **No law-enforcement / non-consenting collection.** It is *a different system, not a different setting*
  (corpus §12.10): removes re-contact (killing every disconfirming test), inherits wiretap/GDPR/FTC exposure,
  and at realistic base rates is wrong >9 times in 10 — unacceptable when false positives are assertions about
  identifiable people. Plus EU AI Act prohibitions.
- 🚫 **No DIY scraping of ToS-gated or logged-in sources.** Breach-of-contract is the real risk, not CFAA.
  Official APIs → licensed brokers with DPAs → never scrape. Enforce in the connector contract.
- 🚫 **No emotion recognition on workplace/employee-adjacent data** — likely a *prohibited* practice under the
  EU AI Act, not merely regulated.
- ⚠️ **GDPR Art. 9**: special-category data appears routinely in transcripts and community discourse. Needs an
  explicit lawful basis, not consent-by-default.

## Current code state

Pure offline Python package, 24 tests passing, no network or API key required.

```
ethnography/
  schema.py     Observation/Corpus/Provenance model — the canonical seam
  ethics/       governance.py (the gate) · consent.py · redaction.py · audit.py (hash-chained)
  adapters/     base.py contract · events.py · qualitative.py
  analysis/     coding.py · journeys.py · personas.py (k-anon floor) · thick_description.py
  llm/          optional enrichment, OfflineLLM fallback
  report/       Markdown field report
  pipeline.py   orchestration · config.py · cli.py
```

```bash
python -m pytest -q                                     # offline, must stay green
python -m ethnography verify config/study.example.yaml  # ethics dry-run
python -m ethnography run    config/study.example.yaml  # full report
```

**When productionising:** reuse `schema.py` (extend with provenance envelope + `tenant_id` + evidence spans),
all of `ethics/` (persist audit + consent to Postgres, keep the hash chain), `analysis/coding.py` as the
deterministic baseline, `personas.py`'s k-anon floor generalised to *all* output. Rewrite `llm/client.py`
(→ gateway client, keep `OfflineLLM`) and `pipeline.py` (→ durable workflow, same ordered stages).

## Open questions — genuinely unresolved

Do not paper over these; they need evidence, not assertion.

1. **Horizontal SaaS vs vertical services.** Corpus §18.2 argues a horizontal rigor product fails by adverse
   selection — *"insight markets buy confidence, not calibration"* — and that horizontal-and-fast is the failure
   mode. §1–§11 of the strategy doc assume a horizontal multi-tenant SaaS. **This contradiction is live.**
2. **Open-source vs monetise.** Proposed: open-source the method library (become *the format*), monetise the
   attestation (provenance, audit trail, regulatory-grade reports, sign-off). Licence choice unresolved.
3. **Beachhead vertical.** Candidate: regulated instrument development (COA/PRO), where saturation
   documentation is reportedly a mandated deliverable with no specified method.
4. **Node set.** A community is constituted by its *associations*, not its residents (corpus §14.4). What the
   entities actually are — subreddits, servers, moderator teams — is a support decision, not a detail.

## Conventions

- Timezone-aware datetimes only; get "now" from `schema.utcnow()` (patchable).
- New data source → add a `SourceAdapter`; nothing downstream changes.
- New analysis → read `Corpus`, return schema dataclasses, set `provenance`.
- Every dollar figure in the docs is **directional** — vendor egress was blocked during research. Re-quote
  before it enters a financial model, especially NVIDIA licensing (never read from a primary source).
- Keep the report's ethics section and limitations honest and up front. *"A Chao1 estimate computed over a
  badly specified code list is a confident number about nothing."*
