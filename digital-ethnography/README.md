# digital-ethnography

**Digital Ethnographic Intelligence** — an AI-native system for research that continuously and ethically
*observes* digital behaviour and online culture, and returns rigorous, **cited** ethnographic insight.

Two things live here, and it matters which is which:

| | Status |
|---|---|
| **The governance kernel** — a pure, offline Python package enforcing ethics as a hard gate | ✅ **built**, 24 tests passing |
| **The platform** — multi-tenant web app → public API → MCP server, multi-agent analysis, rigor layer | 📐 **designed, not built** — see `docs/` |

> Don't mistake the kernel for the product. What runs today is the ethics boundary the platform is built around.

---

## The thesis

Every incumbent — Dovetail, Marvin, Condens, Notably, dscout, UserTesting, Sprig, Maze — runs the same loop:
*collect a session a researcher deliberately ran → transcribe → AI-tag → synthesise → report.* The unit of
analysis is always a session you commissioned. Two gaps follow:

1. **Observation vs. elicitation.** Nobody productises observation of *naturally-occurring* digital behaviour —
   communities, forums, reviews, support logs, in-the-wild usage — as the primary substrate with research-grade
   provenance.
2. **Meaning vs. sentiment.** Incumbents surface themes and polarity. Ethnography's value is *meaning* — norms,
   identity, rituals, discourse, how a culture shifts over time.

And a third, which is sharper: **the rigor layer is not productised anywhere.** Krippendorff's α, Cultural
Consensus Theory, Chao1/Good–Turing saturation, prediction-powered inference, conformal prediction, measurement
invariance — these exist as R packages, free calculators and arXiv papers, with nothing joining them to a
working research pipeline.

---

## What's built: the governance kernel

**Ethics is a hard gate, not a checklist.** No observation reaches any analysis stage unless it passes consent,
purpose limitation, data minimisation, retention, and PII redaction. Every decision is written to a
tamper-evident audit log.

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

| Principle | How it is enforced (in code) |
| --- | --- |
| **Informed consent** | `ethics/consent.py` — default-deny registry. No valid, unexpired, purpose-matched record → dropped at the gate. |
| **Purpose limitation** | The study declares one `purpose`; consent must name it or the data is refused. |
| **Data minimization** | The study declares `allowed_categories`; anything outside them is dropped *even if consent exists*. |
| **Anonymity** | `ethics/redaction.py` — raw identifiers salted-hashed to pseudonyms at ingest and discarded; free-text PII redacted before retention. |
| **k-anonymity** | Personas require minimum membership (`k_min`, default 3); no portrait describes a single person. |
| **Right to erasure** | `GovernanceGate.erase_participant` cascades deletion; withdrawal revokes future access. |
| **Retention limits** | Observations past `retention_days` from their timestamp are dropped. |
| **Accountability** | `ethics/audit.py` — SHA-256 hash-chained log with `verify()` tamper detection. |
| **Human-in-the-loop** | AI is *optional enrichment only*. Model output is tagged `LLM_ASSISTED` and surfaced in a `review_queue`. |
| **Interpretive honesty** | The report foregrounds limitations and provenance flags (⚠️) on machine-drafted sections. |

### Quick start

```bash
cd digital-ethnography
pip install -r requirements.txt

python -m ethnography verify config/study.example.yaml   # ethics dry-run: kept/dropped/redacted, no analysis
python -m ethnography run    config/study.example.yaml   # full study → Markdown field report
```

Or `make verify` · `make run` · `make test`.

Runs **fully offline** — no API key required. The example study demonstrates the gate dropping non-consenting
participants and redacting PII.

### Designing a study

A study is one YAML file (`config/study.example.yaml`) declaring the purpose, the data categories it may touch,
retention, the sources, an optional a-priori codebook, and the consent records — written against raw
identifiers, which are pseudonymised on load so the running system never holds them.

### Supporting a new source

Implement one adapter; everything downstream is reused.

```python
from ethnography.adapters.base import RawRecord
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

Built in: `EventLogAdapter` (behavioural JSONL) and `QualitativeAdapter` (text JSONL — reviews, interviews,
forum and support posts).

### Optional LLM enrichment

Set `llm_enrichment: true` and export `ANTHROPIC_API_KEY` to let a model propose emergent codes and richer
thick descriptions. Output is always tagged `LLM_ASSISTED`, flagged `needs_review`, and listed in
`StudyResult.review_queue`. Without a key the pipeline degrades gracefully to the deterministic core.

### Layout

```
ethnography/
  schema.py          # Observation / Corpus / Provenance — the canonical seam
  ethics/            # governance.py (the gate) · consent.py · redaction.py · audit.py
  adapters/          # base.py contract · events.py · qualitative.py
  analysis/          # coding · journeys+friction · personas · thick description
  llm/               # optional enrichment (offline fallback)
  report/            # Markdown field report
  pipeline.py        # orchestration (the gate is the hard boundary)
  config.py, cli.py  # study loading + `run` / `verify`
config/ examples/ tests/ docs/
```

---

## What's designed: the platform

**`docs/STRATEGY_AND_ARCHITECTURE.md`** is the source of truth.

- **§1–§10** — positioning, methodology (Netnography as core method; AoIR IRE 3.0 + Nissenbaum's contextual
  integrity as the ethics engine), the multi-agent architecture, data pipeline and connector law, the
  recruitment model, and the roadmap to API/MCP.
- **§11 Infrastructure** — researched and adversarially fact-checked. Temporal outside / typed Python inside ·
  one Postgres with pgvector partitioned by `(tenant_id, study_id)` · Bedrock EU **in-region endpoints** ·
  vLLM not NIM · Qwen/Gemma/Mistral not Hermes · self-hosted Langfuse + LiteLLM. Includes the plain verdict on
  Hostinger, the LangGraph licensing problem, and the EU-residency traps.
- **§12 The Rigor Layer** — the measurement mathematics, and the three places it **overturns** the earlier design.

**`docs/formal-models-for-ethnographic-research.md`** — the formal corpus (§0–§18) the rigor layer is built on:
Stinchcombe's causal-structure triage, saturation as species richness, Cultural Consensus Theory,
generalizability theory, fsQCA, Bayesian process tracing, tail regimes and fragility, prediction-powered
inference, linguistic anthropology, and the commercial argument.

**`docs/architecture-overview.html`** — a self-contained visual overview.

### The rigor layer in one table

| Question | Estimator |
|---|---|
| When do I stop? | Good–Turing `f₁/n`, Chao1 — saturation as an auditable number, not "no new themes emerged" |
| Can I trust the coding? | Krippendorff's α + generalizability-theory variance components |
| Do my coders share one rubric? | Cultural Consensus Theory + Marchenko–Pastur noise edge |
| Can I label a whole corpus validly? | **PPI / DSL** against a gold *probability* sample |
| How uncertain is this? | Conformal intervals, not point estimates |
| Has the codebook gone stale? | CUSUM / BOCPD on `f₁/n` |
| Comparable across languages and time? | Measurement invariance (configural→scalar, ΔCFI < 0.01) |
| Is this finding real? | PPV at the *real* base rate — output is a **ranked queue, never a finding** |

---

## Scope boundaries

- 🚫 **No law-enforcement / non-consenting collection.** It is *a different system, not a different setting* —
  it removes re-contact (killing every disconfirming test), inherits wiretap/GDPR/FTC exposure, and at realistic
  base rates is wrong more than nine times in ten.
- 🚫 **No DIY scraping of ToS-gated or logged-in sources.** Breach-of-contract is the real risk, not CFAA.
  Official APIs → licensed brokers with DPAs → never scrape.
- 🚫 **No emotion recognition on workplace or employee-adjacent data** — likely *prohibited* under the EU AI Act,
  not merely regulated.

## Honest limitations

A research **scaffold**, not a compliance product. Consent collection, lawful basis, and jurisdiction-specific
obligations (GDPR, CCPA, IRB) remain the researcher's responsibility. Findings are interpretive, not
statistical. The kernel's regex PII redactor is a conservative floor — the platform design replaces it with an
in-VPC LLM detector, because regex/NER alone measures roughly 0.07 recall on high-sensitivity PII.

And the limit that matters most, from the corpus: nothing here generates a theory. Every estimator takes the
coding scheme, item set and candidate mechanisms *as given* — those are the ethnographer's contribution.

> *"A Chao1 estimate computed over a badly specified code list is a confident number about nothing."*
