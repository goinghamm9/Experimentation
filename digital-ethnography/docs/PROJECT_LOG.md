# Project Log — Digital Ethnographic Intelligence

*Everything done, everything decided, everything still open.*

> **Status at a glance.** 13 commits · 49 Python files · **107 tests passing** · 3 docs + 1 published artifact.
>
> **The distinction that matters:** the **governance kernel and rigor layer are built and working**.
> The **platform** (multi-tenant web app → API → MCP) is **designed but not built**.
> Do not mistake the kernel for the product.

**Companion documents**
- `CLAUDE.md` — operational rules for anyone (human or agent) working in this repo. *Read that first for "how to work here."*
- `docs/STRATEGY_AND_ARCHITECTURE.md` — the reasoning. §11 infra, §12 rigor, §13 harness, §14 graphs.
- `docs/formal-models-for-ethnographic-research.md` — the supplied formal corpus the rigor layer implements.
- `docs/architecture-overview.html` — visual overview.
- **This file** — the historical record and the roadmap.

---

## 1. What was done

| Commit | What |
|---|---|
| `02490a0` | **Governance kernel** — ethics gate, consent registry, PII redaction, pseudonymisation, k-anonymity floor, hash-chained audit log. 24 tests. |
| `a214f90` | **Strategy doc** — positioning, Netnography + AoIR/contextual-integrity ethics engine, multi-agent architecture, data pipeline, recruitment, roadmap to API/MCP. |
| `e5cd93e` | **§11 Infrastructure** — after 6 research dives, each adversarially fact-checked (14 agents). Plus the visual artifact. |
| `ab0e395` | **§12 Rigor Layer** — integrates the supplied formal-models corpus; records the 3 places it overturns the earlier design. Corpus vendored into `docs/`. |
| `c978b03` | **CLAUDE.md rewritten** for the platform rather than the CLI. |
| `283542c` | README, artifact and `pyproject.toml` brought in line; root README project index. |
| `8b1fb14` | **§11.0 evidence tiers** — after verification caught errors in claims recorded as settled. |
| `87aa144` | **§13 Harness discipline** (LOOPS.md) — 11 agent roles pruned to 4. |
| `ba30c83` | **§14 The graph layer** — three graphs separated; two rejected. |
| `2ccb8ba` | **Rigor layer in code** — saturation, reliability, consensus, honesty. |
| `31e4491` | **Multi-coder panel** — agent agreement separated from human validity; ρ estimated. |
| `af6dba0` | **Annotation surface** — gold-coding UI, store, `annotate`/`validate` commands. |
| `f6f6074` | **LLM coder** — span verification, refusal accounting, prompt decorrelation, panel runner. |

---

## 2. What exists in code — and the guarantee each part enforces

```
ethnography/
  schema.py            Observation / Corpus / Provenance — the canonical seam
  ethics/              THE HARD GATE: consent · purpose limitation · minimisation ·
                       redaction · retention · k-anonymity · hash-chained audit
  rigor/               ESTIMATORS, NOT VIBES — pure Python, zero dependencies
    saturation.py      Good–Turing f₁/n, Chao1 (+bias-corrected, f₂=0 fallback), Heaps' β
    reliability.py     Krippendorff's α (nominal, missing-data tolerant), Cohen/Fleiss κ,
                       n_eff deflated for correlation AND independently for tails
    consensus.py       Cultural Consensus Theory, competence weighting, Marchenko–Pastur
                       edge; cyclic Jacobi eigensolver (no numpy)
    honesty.py         PPV at base rate, rule of three, detection floor, α_eff,
                       max spurious |r| (clamped), SearchLedger
    panel.py           Multi-coder panel; seeded probability sampling; CQR frequency
                       labels; restart-not-escalate routing
  annotate/            HUMAN GOLD — blind by construction; store, stdlib server, UI
  coders/              base (span verification) · prompts (decorrelation) · llm ·
                       deterministic baseline · panel_runner
  analysis/ report/ adapters/ llm/ pipeline.py config.py cli.py
```

**The invariants, stated as guarantees:**

1. **No analysis stage ever sees pre-gate data.** Everything consumes the post-gate `Corpus`.
2. **Agent↔agent agreement is a disagreement router; agent↔human agreement against gold is the only
   validity claim.** With no gold, the report says *"validity UNKNOWN"* rather than showing a score.
3. **A fabricated evidence span cannot move a number.** Spans are verified against the source
   mechanically; unverified → the label is dropped before it reaches the panel.
4. **An invented code is not a finding.** Labels outside the codebook are refused entry.
5. **A refusal is a refusal, never an absence.** Refusal rate is reported as coverage loss.
6. **ρ is estimated from data, never assumed.** Lineage is recorded; within- vs cross-lineage ρ reported.
7. **The annotator never sees a machine label.** No field exists for one; a test asserts no leakage.
8. **The deterministic core runs with no network and no API key.**

**Commands**
```bash
python -m pytest -q                                      # 107 passing, offline
python -m ethnography verify   config/study.example.yaml # ethics dry-run
python -m ethnography run      config/study.example.yaml # study → field report
python -m ethnography annotate config/study.example.yaml # human gold coding UI
python -m ethnography validate config/study.example.yaml # machine vs human gold
```

---

## 3. Decisions settled — do not relitigate

| Area | Decision |
|---|---|
| Orchestration | **Temporal** (MIT) outside, plain typed Python inside. Workflow = the study; Activity = one bounded, idempotent, cost-attributed call |
| Agent framework | **None as backbone** — `langgraph-api` is Elastic-2.0, prohibiting hosted-service offering |
| Data | **One Postgres**, pgvector in the *same* DB partitioned by `(tenant_id, study_id)` |
| Inference default | **Bedrock EU in-region endpoints** — Anthropic first-party has no EU option; the EU *inference profile* routes to Zurich/London, outside the EEA |
| Self-hosted inference | **vLLM**, not NIM. A sovereign pod is a premium SKU, not a cost saving |
| Open weights | By **tier**, not model ID. Not Hermes for the cascade (see §5) |
| Observability | **Self-hosted Langfuse** (MIT `oss`), OTel-instrumented so it is a swappable sink and never a sub-processor |
| Gateway | **Self-hosted LiteLLM** — per-tenant keys, synchronous hard budget caps |
| Hosting | Render/Railway EU → AWS `eu-central-1`. **Hostinger: marketing site only** (no GPU/K8s/object storage/managed Postgres/KMS/VPC/SOC 2; SLA remedy is a 5% credit) |
| Skip at MVP | Graph DB · search engine · OLAP · agent-memory vendors · **Kubernetes** |

**Two one-way doors:** a model-gateway abstraction from commit #1 (route by capability profile, never
model name), and a tenant→region pin in the data model even with one region. A third specific to this
product: **provenance edges from commit #1**.

**Hard scope boundaries:** no law-enforcement / non-consenting collection · no DIY scraping of ToS-gated
sources · no emotion recognition on workplace data · GDPR Art. 9 needs an explicit lawful basis.

---

## 4. Corrections and reversals

The most valuable section. Each of these was believed, then disproved.

### Architecture

| Was | Now | Why |
|---|---|---|
| N model coders + κ as a reliability claim | **CCT** (rank-one corrected agreement matrix, competence-weighted aggregation) + **Marchenko–Pastur** noise edge + report `n_eff` | Judges sharing lineage are correlated; α measures *shared professional vision*, not truth (Goodwin) |
| Build an unbiased judge | **Accept the judge is biased and correct it statistically** — PPI/DSL against a gold *probability* sample | Tractable engineering vs. a hope |
| Presidio as core PII layer | In-VPC **LLM detector** primary, regex as tripwire | Regex matches surface forms, misses contextual identifiers. ❓ *The oft-quoted "0.07 recall" figure is **unverified** — do not cite it* |
| 11 agent roles, 6 loops, 4 memory layers | **4 agents** (orchestrator, coders, critic, synthesizer); everything else a deterministic tool; **3 files** of state | LOOPS.md: *"short loops, simple state, clean contracts — everything else is decoration"* |
| Human gates throughout analysis | **Humans on contracts, not builds.** Disagreement → restart the pass; persistent disagreement → contract defect | Human attention is the scarcest resource. Ethics gates survive the cut cleanly — they *are* contract-level |
| Graph everywhere / GraphRAG | Three graphs separated. Derivation ✅ · conceptual ✅ · **social ✅ (under-served)** · orchestration ❌ · GraphRAG ❌ | The coding pipeline *already is* a domain GraphRAG |

### Infrastructure

- ❌ **SGLang/RadixAttention retracted.** vLLM has automatic prefix caching **on by default**; an extreme
  prefix ratio *collapses* the gap rather than amplifying it. The real tweak is vLLM **cascade attention**
  (which *is* off by default).
- ⚠️ **Llama licence string corrected** — it requires **"Built with Llama"**, not "Built with Meta Llama 3.1".
- ⚠️ **"Don't build on Hermes" was too broad.** Only 70B/405B are Llama-derived. **Hermes 4 14B (Qwen3 base)
  and 4.3 36B (Seed-OSS, 512K) are Apache-licensed**, and 4.3 earns one seat as a *deliberately decorrelated*
  panel voice — lineage diversity being the scarce resource.
- ⚠️ **RLS does not "structurally eliminate" cross-tenant leakage.** Superusers, `BYPASSRLS` roles and
  **table owners** bypass it unless `FORCE ROW LEVEL SECURITY` is set. Assert it in a test.
- ❓ **NIM pricing unverifiable** — every NVIDIA property was egress-blocked for both researcher and
  fact-checker. The verdict survives on checkable grounds: NIM wraps vLLM and ships prefix caching *disabled*.
- ⚠️ **Break-even used retired pricing.** Frontier Opus is $5/$25, not $15/$75 → self-hosting break-even is
  **2–4× higher**, strengthening "sovereign pod = premium product, not cost saving".
- ⚠️ **Model IDs were stale on arrival** (Qwen3.6 superseded Qwen 3.5). State the cascade by **tier**.

### Bugs my own tests and demos caught

- **Shared-error ρ was non-identifiable for binary codebooks** — if both coders are wrong with two
  categories, they are *necessarily* wrong the same way, so ρ̂ = 1.0 even for independent coders. Now guarded
  (≥3 categories) and normalised against the `1/(C−1)` chance level. Before the fix a realistic panel
  reported ρ̂ = 1.00 and n_eff = 1 while visibly disagreeing.
- **Expected largest spurious |r| exceeded 1.0** — impossible for a correlation. Now clamped, with a
  `search_is_saturated` predicate that says plainly when findings are hypothesis-generating only.
- **α reported as "not computable" when every coder uses one category** — correct (no expected
  disagreement) and surfaced rather than flattered as 1.0.

### In the supplied corpus

- **§8.1 arithmetic slip.** The stated formula `n_eff = k/(1+(k−1)ρ)` gives **1.47** at ρ=0.6, k=5; the text
  illustrates it with "about 1.7", which corresponds to **ρ=0.5**. The formula (standard Kish design effect)
  is correct; the illustration is not. Implemented as the formula; recorded in code and test.

---

## 5. Research completed, and the four reversals not yet in the strategy doc

Three workflows completed: infrastructure (14 agents), connectors/verticals/OSS (11 agents), plus targeted
Hermes-framework research. **The following are recorded here first and still need writing into
`STRATEGY_AND_ARCHITECTURE.md`.**

1. **Regulatory timing collapsed — except pharma.** EU AI Act high-risk → **Dec 2027/Aug 2028**; Colorado AI
   Act **repealed**; ADA Title II → 2027/28; CSDDD → **July 2029**; USAID M&E destroyed. **Only pharma
   tightened** (PFDD Guidance 3 finalised Oct 2025; joint FDA–EMA AI principles Jan 2026). *That asymmetry,
   not market size, should pick the vertical.* And the nearer driver is the **EDPB's April 2026 research
   guidelines, live now**, which make rigor part of the lawful basis itself.
2. **REFI-QDA is table stakes, not the wedge** — it carries no slot for any rigor quantity. The real
   standard-ownership plays are an **open rigor sidecar extending REFI-QDA** and an **open machine-readable
   research-consent manifest**; the ecosystem has named both gaps. Adoption of the free standards
   manufactures demand for the paid attestation.
3. **"The signed artifact is the product" fails on evidence.** Every attestation market where the *verified
   party pays for the verdict* has degraded — Verra suspended four auditors in March 2025 across 57 projects.
   The surviving form: give away the format and free offline verification, **sell the pipeline that earns a
   passing record**, sell custody of the record, add counter-signature last and only with an independent
   co-issuer. Licence: CC0 spec, Apache-2.0 verifier/method library, AGPL+CLA workbench, proprietary hosted
   attestation. **No BSL/SSPL/ELv2/FSL** — *an instrument sold as defensible must be runnable by the adversary.*
   The enforceable asset under a permissive licence is **trademark + conformance suite**.
4. **Vertical: build for COA/PRO but sell to the specialist consultancies, not pharma.** The saturation claim
   is **substantially correct** — the "concept saturation grid" is a *named artefact* in FDA COA Qualification
   Plan templates. Three qualifications: saturation is being retired in favour of **information power**; the
   estimators are already free; and **EMA's PED definition explicitly excludes AI interpretation** — diligence
   it. Avoid market research and management consulting (adverse selection). Academia is a legitimacy channel
   at ~zero revenue. **The strongest unnamed vertical: DSA systemic-risk assessment and trust & safety policy
   research** — mandatory, annual, independently audited, methodologically undefined, genuinely about online
   culture. The right act two. **Law enforcement: decline explicitly** — the platform's own rigor layer would
   prove the product doesn't work, before Article 5 is even reached.

**Other findings worth keeping**

- **OpenClaw confirmed:** `openclaw/openclaw`, **384,136 stars**, most-starred repo in GitHub history, now a
  501(c)(3). Borrow: lean gateway, `SKILL.md` markdown extension format, signed registry, **MCP instead of
  bespoke integrations**. Don't borrow the growth model — ~245k publicly exposed instances by May 2026.
- **Hermes agent framework** (`NousResearch/hermes-agent`, MIT) is real but the wrong tool: single-node SQLite
  Kanban duplicating Temporal, 7-day durability against multi-week studies, no disagreement measurement.
  Steal the root/worker/verifier/synthesizer topology and per-advisor cost attribution only.
- **Connector landscape bifurcated.** High-signal sources (TikTok, Meta, DSA Art. 40) are contractually barred
  to commercial products at any price; Reddit/X/YouTube/LinkedIn priced out of indie reach. What remains:
  **first-party enterprise** (consented by construction) and **open-protocol public** (Bluesky Jetstream,
  Mastodon, HN, Discourse, GDELT, Common Crawl, Wayback, Wikimedia). Open protocols remove the *commercial*
  gatekeeper, not the legal or ethical one — budget for consent engineering, not API fees.
- **Language competence is tiered, and "supports N languages" means tokenizer coverage.** Roughly **12 Tier A,
  ~17 Tier B, ~28 research-grade only**; outside UD's 179 languages, cannot be served. Non-Latin scripts cost
  **3–5× tokens** (Burmese ~11.7×) → **price in analysis units, not tokens**. Code in the original language;
  translation is a derived, attributed view.
- **Rigor layer is ~60% wrappable, 40% greenfield — and the greenfield is the differentiating part.**
  **Zero Python implementations** exist for CCT, generalizability theory, or DSL/PPI variants; the R
  incumbents are abandoned (CCTpack 2017, gtheory 2016). **GPL licence constraints vindicate the clean-room
  Krippendorff** written here (`krippendorff` and `pingouin` are GPL-3): an Apache-2.0 library *requires*
  reimplementation. Use **crepes**, not MAPIE (no covariate-shift support).
- **A unification worth building on:** *"how many effectively independent judges do I have"* and *"is there one
  culture or three"* are **the same eigen-decomposition** of a rater-by-rater agreement matrix.

---

## 6. Evidence status — carry this forward

Research ran under an egress policy that blocked **arXiv, ACL Anthology, OpenReview, Semantic Scholar, every
NVIDIA property, hyperscaler docs, and EU legal sources** for both researchers and fact-checkers. Claims are
tiered in strategy §11.0:

- ✅ **Verified from primary artifacts** (GitHub raw, PyPI JSON, decompiled wheels): `langgraph-api` = Elastic-2.0
  while `langgraph` = MIT · Arize Phoenix = ELv2 · Langfuse `oss` entitlements · Temporal LangGraph plugin is
  experimental · Temporal payload-codec crypto-shredding · pgvector post-filtering · OWASP LLM08:2025 ·
  Postgres RLS bypass semantics · Llama licence string · OpenClaw star count.
- ⚠️ **Direction sound, numbers unusable:** NIM/NVIDIA pricing · inference share of COGS · Hostinger's feature
  gaps · self-hosting break-even · EU region/model availability.
- ❓ **Do not cite:** Presidio recall figures · the LLM-panel correlation quantities (~2 effective votes) ·
  published refusal rates · EDPB endorsement of crypto-shredding · DPF appeal status · COA pricing.

**Every dollar figure in these docs is directional. Re-quote before it enters a financial model.**

---

## 7. Open questions — genuinely unresolved

1. **Horizontal SaaS vs vertical services.** Corpus §18.2 argues a horizontal rigor product fails by adverse
   selection (*"insight markets buy confidence, not calibration"*) and that horizontal-and-fast is the failure
   mode. Strategy §1–§11 assume a horizontal multi-tenant SaaS. **This contradiction is live.** §5 above now
   tilts toward vertical services.
2. **Licence choice.** CC0/Apache/AGPL+CLA proposed but not decided.
3. **Beachhead confirmation.** COA/PRO via consultancies is the recommendation; DSA/T&S is the credible
   alternative. Neither validated with a buyer.
4. **The node-set decision — highest-leverage unresolved item.** *A community is constituted by its
   associations, not its residents.* The entities are plausibly subreddits, servers, moderator teams and their
   overlapping memberships — not an aggregate of posters. **This determines the schema** and should be settled
   before more code is written.

---

## 8. What to do next, in priority order

1. **Write the four reversals (§5) into `STRATEGY_AND_ARCHITECTURE.md`.** Cheapest, highest value, no research
   required. The strategy section should be rewritten *once* against the full evidence.
2. **`core/provenance.py` first** — derivation edges + erasure catalogue, with an API that **structurally
   refuses to run PPI without a registered probability sample**. This also resolves whether the current
   keyed-hash sample qualifies as a probability sample with known inclusion probabilities.
3. **Bootstrap CI for Krippendorff's α** — the GPL implementations lack it; this is a real differentiator.
4. **Unify the two eigen-decompositions** into one primitive (independent-judge count and one-culture test).
5. **Re-run the three killed reviews** when budget allows: code review (4 lenses), corpus review (5 lenses),
   psychology/methodology traditions (5 dives). All were stopped mid-flight; no partial results were kept.
6. **Then:** multi-annotator coordination surface · real gateway client (LiteLLM) · Phase 0 web app
   (monorepo, Stack Exchange connector, Temporal workflow, Next.js UI, CI + eval gate).

---

## 9. Corpus review status

The five-version *Formal Models for Ethnographic Research* corpus was read in full and is vendored at
`docs/formal-models-for-ethnographic-research.md`.

**Arithmetic independently verified.** Every worked numeric example recomputed — §1.1 detection floor (9),
§5.1 spot sampling (245.9 ≈ 246), §11.2 tail deflation (21.5, 4.64), §11.3 uplift (1.587), §12.1 PPV (0.0868),
§12.3 pairs and max|r| (19,900 / 0.199) — **all correct**. The only error found is the §8.1 `n_eff` illustration.

**Two CCT derivations re-derived from scratch and confirmed**, including the aggregation weight
`ln[(1+D)/(1−D)]` that I suspected should be `ln[D/(1−D)]` — **it should not; the corpus is right.**

**Known open items in the corpus** (from partial review before it was stopped): §13.4 says to reach for
measurement invariance first, but §12.7 still presents holonomy as primary — the correction is not propagated.
A section-number collision exists between v4 (§14 Commercial) and v5 (§14 Blockmodeling, Commercial → §18);
cross-references need checking. Psychology is thin — **CQR is absent** despite being built on multiple judges
plus an auditor, which is exactly §10.6's concern; construct validity (Cronbach & Meehl, Messick, Borsboom)
is absent despite §0.4 being about concepts and indicators.

---

*Last updated after commit `f6f6074`. Three research workflows were stopped mid-flight to conserve budget;
their scope is recorded in §8.5 for re-running.*
