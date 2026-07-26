# Digital Ethnographic Intelligence — Product Strategy & Technical Architecture

*A public-facing, AI-native platform for ethical digital ethnographic user research — with a
roadmap from web app → API → MCP suite ("ethnographic intelligence as a service").*

> Status: strategy & architecture v1. Synthesizes five research streams (ethnographic
> methodology & ethics; AI model selection & agentic engineering; data sources & pipeline;
> participant recruitment & panel operations; product/platform & competitive landscape).
> The existing `ethnography/` Python package in this repo is the **reference implementation of
> the governance gate** described in §4 — the ethics kernel that the platform is built around.

---

## 0. TL;DR

- **The wedge.** Every incumbent (Dovetail, Marvin, dscout, UserTesting, Sprig…) runs the same loop:
  *collect a session a researcher deliberately ran → transcribe → AI-tag → synthesize → report.*
  Nobody owns **continuous observation of naturally-occurring digital behavior and culture** as a
  first-class product, with research-grade rigor, provenance, and ethics. That is the white space:
  **the AI ethnographer that watches the field, not just the interviews you recorded.**
- **The moat is three compounding assets, in order:** (1) an **ethics/governance kernel** that lets
  enterprises connect sensitive first-party data without legal fear; (2) a **sophisticated multi-agent
  AI brain** whose rigor (grounding + measured inter-coder agreement + adversarial verification +
  human-in-the-loop) is defensible to expert buyers; (3) an **owned, consent-governed longitudinal
  panel** that produces a compounding, AI-monetizable data stream.
- **The non-negotiable principle** running through every layer: **AI augments a human interpreter;
  it does not replace one.** This is both an ethical stance and the single most important design
  constraint, because the peer-reviewed evidence shows LLM qualitative coding introduces *systematic,
  non-random bias* that does not wash out with scale.
- **The answer to "what recruitment & utilization model should we grow"** (both readings of the
  question) is in §6–§7: a **hybrid centered on an owned longitudinal panel**, fed by marketplace +
  in-product intercept, with public data as *licensed auxiliary signal only*; and an **AI-model
  utilization model that starts single-frontier-model and grows into a routed multi-model fleet**
  priced per-study, not per-seat.

---

## 1. Positioning & the competitive white space

### 1.1 The market has three clusters — and one gap

| Cluster | Examples | What they do | Structural limit |
|---|---|---|---|
| **Research repositories / analysis** | Dovetail (3.0: AI Agents, Ask Dovetail, AI Docs/Dashboards, Canvas), Marvin, Condens, Notably, Looppanel, Aurelius/EnjoyHQ, User Evaluation | Bring-your-own interviews/surveys → transcribe → AI-tag → synthesize → cited reports | Unit of analysis is *a session you ran*. They analyze what you bring; they don't observe the field. |
| **Testing / behavioral** | UserTesting, dscout, Sprig, Maze, Great Question | Moderated/unmoderated tests, in-product feedback, mobile diary studies | Elicited/recruited data. dscout is the closest to "ethnographic" but still relies on recruited participants filming themselves. |
| **Social listening** | Brandwatch, Meltwater | Have the in-the-wild data | Frame it as marketing/PR *sentiment*, not rigorous, cited, culture-level ethnographic insight. |

**The gap (two structural axes):**

1. **Observation vs. elicitation.** No one productizes *observation of naturally-occurring digital
   behavior* — communities, forums, reviews, support logs, in-the-wild usage — as the primary
   substrate, with researcher-grade provenance.
2. **Culture & meaning vs. themes & sentiment.** Incumbents surface *themes* and *polarity*.
   Ethnography's value is **meaning** — norms, identity, rituals, discourse, community dynamics over
   time. We model communities and evolving culture, not just tagged quotes.

### 1.2 Our one-line positioning

> **The AI ethnographer that continuously and ethically observes digital behavior and online culture —
> producing rigorous, cited, longitudinal cultural insight — and exposes that engine to humans (web
> app), systems (API), and other AI agents (MCP).**

The wedge against Dovetail/Marvin: *they analyze what you bring; we watch the field.* The wedge
against dscout: attack its ~$15K–$60K per-study price floor and weak B2B panel, and add the online-
culture observation layer it lacks.

---

## 2. Methodological foundation (what makes it *ethnography*, not analytics)

The platform is organized around a **core methodology** with a **hard ethics backbone**, and a set of
supporting methods. This is what earns credibility with senior UX and academic buyers — and what keeps
us out of legal and reputational trouble.

### 2.1 Core methodology: **Netnography** (Kozinets)

Netnography is purpose-built for online communities and social media, is already *procedural* (so it
maps to software), and ships with a ready-made ethics protocol. Its stages — **initiation →
investigation → immersion → data collection (archival / elicited / produced) → interpretation →
integration** — become the spine of a "study" object in the product. Critically, we implement its
**ethics steps**, not just its data steps: consent thresholds, **anonymization / "cloaking"**, and
**quote fabrication/paraphrase** so verbatim excerpts from small or vulnerable communities can't be
reverse-searched back to a real person.

### 2.2 The ethics engine: **AoIR IRE 3.0 + Contextual Integrity**

This is non-negotiable and architectural (see §4 and §5).

- **AoIR Internet Research Ethics 3.0** (Franzke, Bechmann, Zimmer, Ess) — case-based, lifecycle-wide,
  and vulnerability-scaled: *the greater the vulnerability of the community, the greater the obligation,
  regardless of data accessibility.* "Public ≠ consented."
- **Contextual Integrity** (Nissenbaum) — the most *operationally useful* ethics theory we have:
  privacy = appropriate information **flow** relative to the norms of the original context. Repurposing
  a support-forum post into a research dataset is a **context transgression** even if nothing is
  "leaked." We test every data use against *the norms of the context it came from*, not just a consent
  checkbox. This becomes a concrete gate: `is_appropriate_flow(actor, info_type, transmission_principle)`.
- **Belmont** (respect for persons / beneficence / justice) and **GDPR/CCPA** (lawful basis, data
  minimization, purpose limitation, special-category protection, erasure) are the compliance floor.
  GDPR Recital 26: *pseudonymized data is still personal* — only true anonymization escapes.

### 2.3 Supporting methods we operationalize

| Method | Role in product | AI verdict |
|---|---|---|
| **Grounded Theory** (Glaser & Strauss; Charmaz) — constant comparison, open→axial→selective coding, saturation | The coding pipeline's methodological grounding | Strong fit for AI-*assisted* first-pass coding + retrieval; theory-building stays human |
| **Triangulation** (Denzin) — corroborate across sources/methods | Our defensible differentiator: cross-reference interviews + diaries + traces + community data | Strong fit; frame multi-source synthesis explicitly as triangulation for methodological legitimacy |
| **Trace Ethnography** (Geiger & Ribes) — reconstruct activity from digital exhaust (logs, histories) | Product-analytics-adjacent studies; journey reconstruction | Strong AI fit — but traces are only legible against ethnographic knowledge of what they *mean*; keep human grounding |
| **Diary studies + ESM** (Larson & Csikszentmihalyi) | The *ethically cleanest* data (consented, elicited, longitudinal); early flagship | Strong, low-risk fit; natural software workflow (prompt, transcribe, longitudinal theming) |
| **Reflexive Thematic Analysis** (Braun & Clarke) — *with built-in reflexivity/positionality tooling* | Credibility signal to expert users; forces us to design against AI's flattening | Ship with **honest framing** — see the landmine below |
| **Saturation tracking** (Guest et al.; Hennink et al.) | An AI-operationalizable rigor feature (signal when new codes stop emerging) | Present as a heuristic signal, not proof; ~12–15+ interviews/segment generative, ~5–8 evaluative |

### 2.4 The paradigm landmine (get this wrong and you alienate experts)

Braun & Clarke's **reflexive TA explicitly rejects inter-rater reliability and Cohen's κ** as category
errors — two researchers are *expected* to code differently. But **codebook/positivist TA teams
*want* κ.** So the product must **support both epistemologies and never conflate them**: offer κ-based
agreement as an *optional* codebook-TA feature, and for reflexive work, position multiple AI "coders"
as *interpretive lenses that provoke researcher reflexivity*, not as a march toward "reliable" coding.
**Never market "reliable/objective automated coding."**

### 2.5 The documented risks of LLM qualitative coding (design against these)

Grounded in recent empirical work (Ashwin, Chhabra & Rao 2025; Tai et al. 2024):

- **Thin-for-thick substitution** — LLMs produce fluent surface description and systematically
  over-claim on interpretation (the Geertzian "wink vs. twitch"). *Mitigation:* keep interpretation
  human; treat AI output as candidate observations.
- **Systematic (non-random) bias** — the load-bearing warning: LLM coding errors *correlate with
  subject characteristics*, so they **bias conclusions in a consistent direction** and do **not** wash
  out with sample size. This silently distorts exactly the underrepresented voices research exists to
  surface. *Mitigation:* multi-model coding + bias auditing (§4.5).
- **Hallucination / fabricated quotes & support.** *Mitigation:* strict source-grounding, span-level
  quote verification, RAGAS-style faithfulness gate.
- **Automation bias / false confidence.** *Mitigation:* surface *disagreement and uncertainty*, not
  smoothed answers; make the human adjudicate, not rubber-stamp.
- **Confidentiality leakage** — sending participant data to third-party APIs can itself breach consent,
  GDPR, and contextual integrity. *Mitigation:* PII redaction *before* any model call; self-hostable
  inference path for regulated tenants.

---

## 3. The AI brain — a sophisticated multi-agent architecture

> This is the product. The differentiator is not the model (models are a swappable commodity behind a
> router) — it is **pipeline discipline**: grounding, measured agreement, adversarial verification,
> learning memory, and human gates. Designed to the "go more sophisticated" mandate.

### 3.1 Design stance

Ground the design in **Anthropic's workflow patterns** (prompt chaining, routing, parallelization,
orchestrator-worker, evaluator-optimizer) + reflection, and prefer **deterministic, observable
workflows over free-roaming agents** wherever the pipeline is known — the qualitative pipeline is
largely known. Reserve open-ended agency for genuinely open sub-tasks (fieldsite discovery, adaptive
follow-up interviewing). Mirrors emerging research systems: **LOGOS** (LLM grounded-theory + schema
induction with iterative codebook refinement), **Neo-Grounded Theory** (vector clustering +
multi-agent), **Thematic-LM** (multi-agent TA at scale), **Agent-as-Peer-Debriefer** (perspective-based
multi-agent refinement mirroring qualitative peer debriefing).

### 3.2 The agent "research team"

Each agent is a distinct role with its own model tier, toolset, and memory scope. Every agent is
**retrieval-grounded**: every claim it emits must cite a verifiable source span, or the critic rejects it.

```mermaid
flowchart TD
    PI["🧭 Principal Investigator<br/>(orchestrator · planner · saturation control)"]
    subgraph Fieldwork
      FW["🛰 Fieldwork agents<br/>(per connector · normalize · provenance)"]
      GATE["⚖️ Governance Gate<br/>(consent · CI flow-check · PII · minimization)"]
    end
    subgraph Coding["Coding (parallel, independent)"]
      C1["🏷 Coder 1"]
      C2["🏷 Coder 2"]
      C3["🏷 Coder N (dynamically spawned)"]
      EMB["🧬 Embedding/BERTopic worker<br/>(bottom-up theme candidates · saturation)"]
    end
    REL["📏 Reliability engine<br/>(Cohen's/Fleiss' κ + semantic agreement)"]
    DEB["🗣 Peer-debrief / debate<br/>(adjudicate disagreements)"]
    AX["🧩 Axial/Selective synthesizer"]
    INT["📖 Interpreter (thick description)"]
    BEH["🧭 Behavioral analyst (journeys + friction)"]
    PER["👥 Persona synthesizer (k-anonymous)"]
    SKP["🥷 Skeptic / adversarial critic<br/>(refute · faithfulness gate · contradiction)"]
    REF["🪞 Reflexivity agent<br/>(positionality · bias surfacing)"]
    HITL["🧑‍🔬 Human-in-the-loop gates"]
    MEM[("🧠 Memory: working · episodic · semantic codebook · procedural")]
    INS["💬 Insight agent (RAG chat: 'Ask your research')"]

    PI --> FW --> GATE --> Coding
    EMB --> AX
    Coding --> REL --> DEB --> AX --> INT --> SKP
    BEH --> SKP
    PER --> SKP
    REF -. audits .-> AX
    REF -. audits .-> INT
    SKP --> HITL
    HITL --> MEM
    MEM -. bootstraps .-> Coding
    HITL --> INS
```

| Agent | Job | Model tier | Notable tools |
|---|---|---|---|
| **Principal Investigator (orchestrator)** | Research question → study plan; decompose; route; **decide when to stop** (saturation); **dynamically spawn more coders** when disagreement/volume is high | Frontier | planner, saturation calculator |
| **Fieldwork agents** (per connector) | Pull + normalize to the canonical Observation model; capture provenance + legal basis at ingest | Small | connector SDK |
| **Governance Gate** | Consent, **Contextual-Integrity flow check**, PII redaction, minimization, sensitivity triage — *hard boundary* | Deterministic + small | Presidio, CI policy engine, audit log |
| **Coder agents ×N (independent, blind)** | Open-code the same units in parallel; emit confidence | Small→mid (cascade) | codebook, structured output, retrieval |
| **Embedding / BERTopic worker** | Bottom-up theme candidates (embed → UMAP → HDBSCAN → label), dedup, saturation novelty signal | Embeddings | vector index, clustering |
| **Reliability engine** | Compute **Cohen's/Fleiss' κ** *and* semantic-similarity agreement across coders; route low-agreement units onward | Deterministic | κ + cosine metrics |
| **Peer-debrief / debate moderator** | Disagreeing coders enter a **structured debate**; adjudicator resolves or escalates to human | Frontier | debate protocol |
| **Axial/Selective synthesizer** | Relate codes → themes → core category (evaluator-optimizer loop) | Frontier | retrieval, codebook memory |
| **Interpreter** | Thick description — situated narrative per theme | Frontier | retrieval |
| **Behavioral analyst** | Journey reconstruction + friction detection from traces/replay | Mid + vision | event-stream + vision fusion |
| **Persona synthesizer** | k-anonymous aggregate portraits *from coded evidence with provenance* | Mid | cohort thresholds |
| **Skeptic / adversarial critic** | Try to **refute** each theme; enforce grounding; **contradiction (NLI) detection**; RAGAS faithfulness gate | Frontier (different family than authors) | NLI, faithfulness scorer, quote-span verifier |
| **Reflexivity agent** | Maintain positionality/assumption memos; surface where model priors may bias interpretation; prompt the human | Frontier | positionality memory |
| **Insight agent** | RAG chat over the analyzed, cited corpus — "Ask your research" | Frontier | retrieval, tools |

### 3.3 The loops that make it *rigorous* (not just fast)

1. **Saturation loop** — track the rate of *new* codes (embedding novelty vs. existing code space);
   stop coding new material for a theme when new-code rate falls below threshold across batches.
   Principled "we've analyzed enough" signal *and* a cost governor.
2. **Reliability loop (signature feature)** — N independent coders (different models and/or
   prompts/temperatures) → **dual metric**: Cohen's/Fleiss' κ *plus* semantic-similarity (catches
   "same meaning, different label"). κ<0.4 poor · 0.4–0.6 moderate · 0.6–0.8 substantial · >0.8
   excellent. **Low agreement auto-escalates** to the debate moderator or a human. Agreement is both a
   quality gate and a headline trust metric shown to customers — *with the epistemology caveat of §2.4*.
3. **Reflection loop** — each coder self-critiques against source + codebook before submitting.
4. **Evaluator-optimizer loop** — theme narratives and codebook definitions are generated → critiqued
   against explicit criteria (grounded? distinct? non-overlapping? ≥N supporting quotes?) → refined.
5. **Adversarial verification loop** — the skeptic must produce a *refuting* quote for each theme;
   survivors are consensus-grounded, the rest flagged. Primary hallucination defense alongside grounding.
6. **Human-in-the-loop gates** — hard checkpoints: (a) **codebook approval** before mass coding,
   (b) **low-agreement / low-confidence review**, (c) **final theme/narrative sign-off**. The human sees
   *evidence + disagreement + confidence*, never a smoothed answer. Every override is logged as eval data.

### 3.4 The sophistication layer: memory, learning, and dynamic scaling

This is what pushes the design beyond a static pipeline into a *learning research organization*:

- **Layered memory.**
  - *Working* — per-study state (current codebook, open questions).
  - *Episodic* — past studies (what was learned, what humans overrode).
  - *Semantic* — a **living codebook / ontology** of codes, themes, and community profiles that
    accumulates across studies. New studies **bootstrap** from relevant prior codebooks — *with explicit
    human opt-in*, because uncritical reuse would import prior bias (a deliberate reflexivity gate).
  - *Procedural* — versioned, tested prompt/skill assets ("prompts are code": versioned, eval-gated).
- **Self-improving codebook.** The evaluator-optimizer loop refines code *definitions* based on
  inter-coder disagreement and human overrides; changes are proposed, human-approved, and versioned.
- **Tool-use per agent.** Agents call real tools — retrieval, κ calculators, BERTopic clustering,
  quote-span verifiers, NLI contradiction checkers, connectors — rather than "reasoning" numbers they
  should compute.
- **Dynamic agent spawning.** The PI scales the coder pool to *difficulty*: more independent coders when
  disagreement is high or the corpus is large; fewer when agreement is trivially high. The "research
  team" right-sizes itself.
- **Structured debate / peer-debrief.** Disagreements aren't averaged away — they're *argued out* by a
  moderated debate agent (Agent-as-Peer-Debriefer), mirroring real qualitative peer debriefing, with the
  human as final adjudicator on persistent splits.

### 3.5 Model selection & routing (the "utilization" that grows)

Advertised context ≠ effective context: multi-fact retrieval degrades badly past ~200K tokens, so
"find every mention across the corpus" is a **RAG job, not a stuff-the-window job.** Task→tier map:

| Task | Tier | Rationale |
|---|---|---|
| Clustering, dedup, retrieval, saturation novelty | **Embeddings** | Cheapest, highest volume; one index serves retrieval + clustering + saturation |
| PII, sentiment (aspect-based), quote extraction, first-pass open coding | **Small model** (Haiku/Flash class) | The bulk of token spend; use structured outputs + fixed codebook |
| Journey analysis, mid-complexity coding | **Mid model** (Sonnet class) | Balance |
| Axial/selective synthesis, thick description, adversarial critique, debate adjudication, cross-study reasoning | **Frontier** (Opus/Gemini-Pro class) | Low volume, high reasoning value; pick on *faithfulness + governance*, not leaderboard deltas (frontier tier is ~interchangeable at κ≥0.84 vs humans when well-prompted) |
| Screenshots / session-replay frames / UI grounding | **Vision model** | Prefer DOM/accessibility text where available; vision as enricher/fallback |
| Non-English segments | **Language-routed** | Keep original-language quotes with provenance; flag low-resource-language findings as lower-confidence; never code off machine translation for anything load-bearing |

**Routing = a tiered cascade** (proven ~85% cost reduction at ~95% of frontier quality): a semantic
router or trained classifier sends each unit to the cheapest capable tier; the small tier codes the bulk
and emits confidence; **only low-confidence / high-disagreement units escalate** to frontier. Route by
*capability profile*, not hardcoded model names, so the fleet is hot-swappable (the frontier turns over
roughly quarterly).

### 3.6 Evaluation & quality (how we keep humans credibly in the loop)

- **Gold-standard human codebooks + κ-vs-human** per study type; report the fleet's agreement with
  humans (frontier reaches κ≈0.71–0.91 *when prompt-engineered*).
- **Faithfulness / groundedness** (RAGAS-style): decompose each output into atomic claims, score the
  fraction supported by retrieved context; a dedicated hallucination detector (entailment model or LLM
  judge) flags unsupported claims. **Faithfulness ≈ 1.0 is a release gate.**
- **LLM-as-judge, carefully** — pairwise not scalar; randomize/swap order and average; **judge model
  from a different family than the generator**; audit judges against human labels. Never let one model
  author, code, *and* solely judge its own work.
- **Observability everywhere** (Langfuse + OTel): every call, cost, confidence, citation, and human
  override logged — both the antidote to agent antipatterns and the substrate for evals.

### 3.7 Cost & scaling (co-designed with the business model)

Diary/ethnographic work is inference-heavy (every entry transcribed → coded → summarized), and cost
scales with *entries × participants × study length*, **not seats** — which is why pricing must be
usage/study-based (dscout-like), not pure per-seat. Levers, stacked:

- **Batch API** (~50% off) — default all non-interactive coding to async batch.
- **Prompt caching** (~90% off cached reads) — cache codebook + system prompt + shared context; batch +
  caching stack to ~95% savings.
- **Cascade routing** — keep ~85% of units on the small tier.
- **Embeddings for dedup/saturation** — stop paying to code redundant/saturated material.
- **Incremental synthesis** — re-analysis doesn't re-run everything; **cost attribution per study**.

**Utilization growth path:** v1 = single frontier model doing everything (fastest to a working
product). Then split out the **cheap coding tier** (biggest win) → add the **embedding/clustering tier**
→ add the **cascade router** → a **multi-model fleet** (different families for coding vs. adjudication
vs. judging — which *also* improves quality and de-risks any single provider). End state: per-unit model
choice is a runtime decision and adding a model is a config change, not a rebuild.

---

## 4. Data pipeline & connectors

**Strategic core: first-party, consented customer data is the product; public social data is thin,
high-risk, *licensed* garnish.** The legal reality below makes DIY scraping a business-model time bomb.

### 4.1 Public sources — access & legal reality (2025–26)

The doctrine that matters: **CFAA is mostly *not* the risk** after *hiQ v. LinkedIn* and *Meta v. Bright
Data* (scraping public, logged-out data). **Breach-of-ToS is** — if you must log in / accept ToS to see
data, scraping it is contractually actionable (hiQ ultimately settled with a permanent injunction, $500K,
and data destruction). **GDPR gives no "publicly available" exemption** (CNIL fined KASPR €240K for
scraping LinkedIn data). Practical tiering:

| Tier | Sources | Posture |
|---|---|---|
| **Official APIs** | Stack Exchange (best-in-class, CC BY-SA), YouTube Data API (10k units/day), **own-app** store reviews (Apple/Google), G2 (paid), Discourse, GDELT/news RSS | Preferred |
| **Licensed brokers** (push legal risk to a vendor with a DPA) | Bright Data, Apify, Data365; **Reddit's commercial license** (~$0.24/1k calls, ~$12k/mo floor) | Use when needed |
| **Never DIY-scrape** | Anything logged-in or ToS-gated: X/Twitter (now pay-per-use, expensive), TikTok (research API bars commercial), Discord (self-bots banned), Amazon reviews (no API text), Glassdoor | Prohibited in architecture |

Build **one abstraction ("external mentions")** over these tiers so downstream code is agnostic to how a
mention was obtained. **Do not let public scraping become a core dependency.**

### 4.2 First-party connectors — the real product

Weighted toward qualitative "voice":

- **Conversation layer (crown jewels):** support desks (**Zendesk / Intercom / Front** — densest
  ethnographic text: real problems in customers' words), interview transcripts (**Gong** best-supported;
  **Recall.ai** as the meeting-bot aggregator normalizing Zoom/Meet/Teams; Grain/Fireflies/tl;dv;
  note **Otter has no official API**), community (**Discourse** clean API; **Slack**).
- **Voice-of-customer:** surveys/NPS open-text (**Typeform / Qualtrics / SurveyMonkey / Delighted**).
- **Behavior:** product analytics (**Amplitude / Mixpanel / PostHog**), and **Segment/RudderStack (the
  CDP) as the single highest-leverage connector** — connect once, fan out everything.
- **Struggle:** session replay (**FullStory / Hotjar / LogRocket**) — heavy PII (screen contents),
  redaction critical.
- **Skeleton:** CRM (**Salesforce / HubSpot**) for firmographic segmentation of all other signal.

**Highest signal-to-effort first: connect at the CDP (Segment) + the conversation layer (Gong/Recall +
Zendesk).**

### 4.3 Pipeline architecture

```mermaid
flowchart LR
    SRC["Sources<br/>(licensed public + first-party OAuth/DPA)"]
    ING["Ingestion: self-hosted Airbyte OSS + custom CDK connectors<br/>(Gong · Recall · Discourse · replay)<br/>+ provenance & legal-basis at ingest"]
    LAKE["Raw lake (S3/GCS, immutable, region-pinned)"]
    PII["PII stage: Presidio detect/redact → token vault"]
    CANON["dbt: raw → staging → CANONICAL 'Observation'"]
    STORE["Postgres + pgvector (→ Qdrant at scale)"]
    ANALYSIS["AI brain (§3): clustering · coding · κ · synthesis · cited insights"]
    KANON["k-anonymity / min-cohort suppression at OUTPUT"]
    SURF["Web app · REST/GraphQL API · MCP server"]
    SRC --> ING --> LAKE --> PII --> CANON --> STORE --> ANALYSIS --> KANON --> SURF
```

- **Ingestion:** **self-hosted Airbyte (OSS)** for the ~30 commodity connectors (residency + margin +
  maintained catalog), extended with **custom CDK connectors** for the differentiated qualitative
  sources. **Batch by default**; a **streaming lane** (Kafka/CDC) only for support/live-chat "emerging
  issue" detection. Reserve Fivetran only if an enterprise buyer demands it.
- **Provenance envelope at ingest (first-class columns, non-negotiable):** `source_system`,
  `source_record_id`, `connector_version`, `ingested_at`, `original_created_at`, `legal_basis`,
  `consent_ref`, `data_subject_id` (pseudonymized), `tenant_id`, `retention_class`, `residency_region`,
  `pii_flags`. This is what makes erasure and audit *possible at all*.
- **PII:** **Microsoft Presidio** (OSS, in-VPC, no egress) + transformer NER; reversible token vault
  behind a strict access boundary. Redact **before** any model call.
- **Canonical `Observation` model** is the stable seam — every source maps to it, so the AI brain, the
  API, and the MCP server all fall out of one schema (this is exactly the `Observation` dataclass already
  in this repo's `ethnography/schema.py`, scaled up).
- **Storage:** Postgres (structured + provenance) · **pgvector until it hurts** → Qdrant self-hosted at
  scale · S3/GCS raw lake.

### 4.4 Governance & compliance (architectural, not a feature)

- **You wear two hats:** *processor* for customer data, *controller* for anything scraped. Offer DPAs +
  SCCs; document legitimate-interest assessments for any public data.
- **Data residency:** self-hosting Airbyte/Presidio/Qdrant + region-pinned storage → EU-resident
  deployments (an enterprise sales unlock). Multi-region from day one (tenant → region pin).
- **SOC 2 Type II** controls (access, change mgmt, audit logging) started at architecture time, not
  retrofitted.
- **Cascading right-to-erasure:** `data_subject_id` as a join key everywhere → a deletion-orchestration
  job that purges source records, vector entries, token-vault entries, and flags derived aggregates for
  recompute → tombstones + audit proof. Never let raw PII into fine-tuning where it can't be deleted.
- **k-anonymity at output:** suppress any theme/quote attributable to fewer than *k* subjects; prefer
  paraphrased/aggregated insight over verbatim when a quote could re-identify — protecting end-users
  *and* customers' employees (e.g., internal Slack VoC). (This is the persona k-floor already in the
  repo's `analysis/personas.py`, generalized to all outputs.)

### 4.5 Bias auditing (ties back to §2.5)

Audit **sample bias** (whose voices dominate the corpus) *and* **model bias** (does a given model
systematically over/under-code certain groups or languages). Running coding across ≥2 model families and
comparing divergence is both a quality signal and a bias-surfacing mechanism — the direct countermeasure
to the "systematic non-random bias" finding.

---

## 5. Platform architecture & admin

### 5.1 Recommended stack (opinionated)

| Layer | Choice | Why |
|---|---|---|
| Frontend | **Next.js (App Router) + React + TS**, Tailwind + shadcn/ui, TanStack Query; streaming UI for agent output | Default for AI SaaS; Vercel preview envs; edge/streaming |
| App/API tier | **TypeScript** (NestJS or tRPC/Next API) | Web-app velocity |
| AI/agent tier | **Python (FastAPI)** service | Where the LLM/data-eng ecosystem lives; talks to app tier over internal API + queue |
| Auth & tenancy | **Clerk or WorkOS** (orgs, SSO/SAML, RBAC) + **Postgres RLS**, `org_id` on every row *and* every embedding | Enterprise-ready fast; **cross-tenant leakage is the #1 failure mode** — enforce isolation at 3 layers: RLS, vector metadata filters, tenant-scoped gateway keys |
| Data + vector | **Postgres + pgvector** → Qdrant/Pinecone at scale; S3/R2 media | One system for MVP; ACID tenant isolation |
| Orchestration | **Temporal** for durable long-running ingestion/agent workflows + **Redis/BullMQ** for fast async | Continuous observation + multi-day studies need durability, retries, HITL, resumability |
| LLM gateway | **LiteLLM** (self-hosted): OpenAI-compatible over 100+ providers, **per-tenant virtual keys + budgets + spend tracking + PII masking**, Langfuse hooks | Model-agnostic routing + per-tenant cost control + one governance choke point |
| Observability | **Langfuse + OpenTelemetry** (+ Grafana/Sentry) | Trace every agent run for cost/latency/quality evals |
| CI/CD | **GitHub Actions** (lint/typecheck/test/build) + **Vercel preview deploys** + **Neon branch DBs** for ephemeral backends; **Terraform/Pulumi** IaC; **LLM output evals (Langfuse/Promptfoo) as a first-class CI gate** | Preview envs + eval-gated deploys |

### 5.2 Admin / governance console (a differentiator, not overhead)

Because we touch consent, PII, and community data: **tenant management** (orgs, seats, entitlements,
feature flags) · **usage/billing/quotas** (per-tenant token spend, Stripe metering, budgets enforced at
the gateway) · **model & cost controls** (per-tenant model allow-lists, routing policy, max-cost-per-job,
prompt/version management) · **data-source connectors** (authorize, rate-limit, ToS/compliance flags,
connector health) · **consent & audit review** (immutable audit log of every data access + AI action;
GDPR/DSAR retention & deletion tooling) · **content moderation & safety** (PII/sensitive-content review
queue, output guardrails) · **RBAC** (owner/admin/researcher/viewer + super-admin, SSO/SCIM,
impersonation with audit) · **eval console** (review outputs, flag hallucinations, manage eval sets,
prompt A/B).

---

## 6. Recruitment & panel model (answering "what model should we grow")

**Reading 1 — participant recruitment.** For an *ethnographic* product, the recruitment model is the
moat, not a procurement detail. One-off interview tools can rent a marketplace; **longitudinal
ethnography lives or dies on a retained, consenting, richly-profiled panel that stays engaged over
weeks/months.** That is expensive to build and very hard to copy — which is exactly why it's where to
invest. Grow a **hybrid centered on an owned longitudinal panel:**

| Channel | Role |
|---|---|
| **Owned longitudinal panel** (dscout's "Scout" model) | The durable asset & AI-data flywheel. Center of gravity. |
| **Marketplace** (User Interviews; Respondent for hard B2B; Prolific for representative consumer) | Feeder for net-new strangers, quotas, spikes — especially early. |
| **In-product intercept** (our own Ethnio/Sprig-style widget) | Feeder for real-context BYO-users of a customer's live product. High ecological validity (but only existing users). |
| **Public-data observation** | **Auxiliary discovery/trend signal only** — walled off from consented primary research. Never a substitute. |

**Staged:**

- **Stage 1 (early):** don't build a panel. Integrate marketplace APIs + BYO-user intercept. **Win on
  the AI ethnography workflow** (mobile capture → auto-transcribe → grounded AI coding/synthesis), and
  ship **consent-lifecycle tooling** from day one as a differentiator.
- **Stage 2 (growth):** add a **research-hub/CRM layer** so each customer builds & re-contacts *their
  own* longitudinal panel inside the product (Great Question's play). Build fatigue/frequency/rotation +
  re-consent machinery. Longitudinal diary studies become a repeatable product; retention compounds.
- **Stage 3 (scale):** stand up a **proprietary, verified, profiled panel** as premium managed
  recruitment — invest specifically in **B2B/specialist depth where dscout is weak**. Public-data trace
  observation as auxiliary signal.

**Panel operations that matter:** rich persistent profiles (to re-target the same people
longitudinally) · gaming-resistant screeners + verification + **ML detection of AI-generated "cheater"
responses** (the newest critical control) · **incentives** ($60–$100/hr field standard; never <~$50 for
60 min; pay partial on withdrawal; per-entry + completion bonus for diaries without becoming coercive) ·
**fatigue controls** (contact caps, cool-downs, rotation — fatigue is now treated as an *ethical* harm,
not just a data problem) · representativeness/quota management (owned panels drift toward engaged
super-users).

**Consent as a lifecycle object (the hard part of ongoing observation):** continuous/diary ethnography
needs **continuous consent, not point-in-time** — explicit **re-consent checkpoints**, per-entry
"share/don't-share" control, frictionless withdrawal, guidance/tooling for **secondary subjects** (home/
work video captures non-consenting third parties), and heightened safeguards for vulnerable populations.
Making consent-lifecycle management a **first-class, auditable product feature** is both an ethical
necessity and a commercial differentiator enterprise buyers will pay for.

---

## 7. Direct answer: "best total model of recruitment & utilization to grow"

Because the phrase spans both readings, here is the crisp two-part answer:

**Participant recruitment → grow a hybrid with an owned longitudinal panel at the center.** Marketplace +
in-product intercept are *acquisition channels into* the owned panel; public data is *exhaust, not
evidence.* The owned, consent-governed, richly-profiled panel is simultaneously the **moat**, the **AI-
data flywheel**, and the **enterprise-trust differentiator**. Benchmark and beat **dscout** (attack its
price floor and weak B2B panel). Sequence it Stage 1→3 as above — don't build the panel before you've won
on the workflow.

**AI-model utilization → grow from a single frontier model into a routed multi-model fleet.** Start
simple; peel off a cheap coding tier (biggest cost win), then embeddings/clustering, then a cascade
router, then a multi-family fleet where per-unit model choice is a runtime decision. Price **per-study /
usage-based** (not per-seat) so marginal inference is covered, because a longitudinal panel makes cost
scale with *entries × participants × length.* **The two models must be co-designed:** the panel is what
generates the compounding data stream the AI monetizes, and the AI's rigor is what makes the panel's data
worth paying for.

---

## 8. Productizing as a suite (web app → API → MCP)

**One core "ethnographic intelligence engine," three surfaces over the same governed API + gateway** —
the `codex-plugin-cc` lesson: *wrap the engine, don't rebuild the runtime.*

- **(a) Web app** — the researcher UI: connect sources, run observation studies, browse communities/
  discourse, agent-generated cited reports, canvas/dashboard views. Competes on *cultural depth*, not
  tagging.
- **(b) Public REST + GraphQL API** — **REST** for actions/jobs (ingest, run analysis, fetch insights),
  **GraphQL** for the relational insight graph (communities → discourse → themes → evidence). Every
  endpoint returns provenance/citations. Long jobs use the **async submit → job_id → poll status →
  retrieve result** contract borrowed from `codex-plugin-cc`'s `--background/--wait/--resume` +
  `status/result/cancel` ergonomics.
- **(c) MCP server** — so any AI agent (Claude, IDEs, agent frameworks) can call our tools, with the same
  provenance + k-anonymity enforced **server-side**. MCP is a *second transport, not a second system.*

**Patterns to borrow from `openai/codex-plugin-cc`** (it's a Claude Code plugin wrapping OpenAI Codex —
"cc" = Claude Code): thin client over one engine · **async-first job model** · config inheritance with a
**trust boundary** (only load trusted-project/tenant config) · **hook-based gates** (an "insight gate"
that blocks a report until evidence/consent checks pass) · one-command onboarding · ship CI + tests with
the integration.

**Proposed MCP tools/resources** (all tenant-scoped, provenance-returning, k-anon-enforced):

```
Tools:
  search_insights(query, community?, timeframe?)      -> cited insights (RAG Q&A)
  analyze_community(community_id | source)            -> culture/norms/discourse profile
  detect_themes(dataset_id, method?)                  -> themes + evidence quotes
  track_behavior_trend(topic, timeframe)              -> longitudinal discourse/behavior shift
  run_observation_study(sources[], objective)         -> async job_id
  get_job_status(job_id) / get_job_result(job_id)     -> async pattern
  list_quotes(theme, min_cohort=k)                    -> quotes above k-anonymity floor
  generate_report(scope, format)                      -> cited VoC/culture report
Resources:
  ethno://communities/{id}   ethno://insights/{id}
  ethno://studies/{id}/report   ethno://sources
```

Publish to the **MCP Registry**. This makes the platform the *"ethnographic intelligence" capability
other agents depend on* — a durable moat in the agent ecosystem, and the literal realization of your
"API, MCP, and more as a suite" note.

---

## 9. Phased roadmap

| Phase | Theme | Ships |
|---|---|---|
| **0 — Engine + MVP web app** | Prove the wedge | Core engine: ingest 1–2 connectors → embed in pgvector → grounded multi-agent theme/culture analysis → cited insights. Next.js UI, Clerk + RLS, LiteLLM gateway, Langfuse, Temporal. **The governance kernel from this repo, productionized.** Ship the async job model + consent-lifecycle tooling day one. Killer demo: *continuous observation of one digital community with cited, longitudinal cultural insight.* |
| **1 — Depth + governance** | Trust & rigor | More connectors (support/interview/survey/community/replay + licensed public), community & discourse modeling, dashboards/canvas, full PII/provenance/audit + cascading erasure + k-anon, admin console, multi-tenant hardening, **evals in CI**, the reliability engine + adversarial verification. |
| **2 — Public API** | Programmable | REST (jobs) + GraphQL (insight graph) over the same engine, tenant-scoped keys, gateway budgets/rate limits, docs + SDKs. |
| **3 — MCP suite + plugins** | Agent-ecosystem moat | MCP server (stdio + streamable HTTP) → MCP Registry; a Claude Code / IDE plugin wrapping the same engine (`codex-plugin-cc` pattern). |
| **Parallel track** | Recruitment | Stage 1 marketplace + intercept → Stage 2 customer research-hub/panel → Stage 3 owned proprietary panel. |

---

## 10. Top risks & how the architecture answers them

| Risk | Mitigation (where) |
|---|---|
| **LLM systematic bias distorts findings** (peer-reviewed, doesn't wash out with scale) | Multi-model coding + bias auditing (§4.5); human-in-the-loop gates; surface disagreement (§3.3) |
| **Hallucinated quotes/claims** | Retrieval grounding + span-level quote verification + RAGAS faithfulness release gate + adversarial critic (§3.3, §3.6) |
| **Alienating expert users on epistemology** | Support both reflexive-TA and codebook-TA; never sell "reliable automated coding" (§2.4) |
| **Legal exposure from public data** | First-party-first; licensed brokers with DPAs; never DIY-scrape ToS-gated sources (§4.1) |
| **Cross-tenant data leakage** (#1 SaaS failure mode) | RLS + vector metadata filters + tenant-scoped gateway keys (§5.1) |
| **Right-to-erasure across derived data** | `data_subject_id` join key + cascading deletion orchestration + tombstones (§4.4) |
| **Re-identification of individuals/employees** | Output k-anonymity + quote cloaking/paraphrase (§2.1, §4.4) |
| **Consent for continuous observation & bystanders** | Consent-as-lifecycle, re-consent checkpoints, per-entry sharing control, secondary-subject tooling (§6) |
| **Runaway inference cost** | Cascade routing + batch + caching + saturation stop + per-study cost attribution (§3.7) |
| **Model churn (frontier turns over quarterly)** | Model-agnostic router; route by capability profile; adding a model is config (§3.5) |

---

## Appendix — key sources by stream

**Methodology & ethics:** Geertz, *The Interpretation of Cultures* (thick description); Glaser & Strauss;
Charmaz, *Constructing Grounded Theory*; Braun & Clarke, reflexive TA (tandfonline.com/doi/abs/10.1191/
1478088706qp063oa); Kozinets, *Netnography* (2020); Hine, *Virtual Ethnography*; Geiger & Ribes, "Trace
Ethnography" (stuartgeiger.com/trace-ethnography-hicss-geiger-ribes.pdf); Guest/Bunce/Johnson, "How Many
Interviews Are Enough?"; **AoIR IRE 3.0** (aoir.org/reports/ethics3.pdf); Belmont Report
(hhs.gov/ohrp/…/belmont-report); **Nissenbaum, "Privacy as Contextual Integrity"**; Ashwin/Chhabra/Rao,
"Using LLMs for Qualitative Analysis Can Introduce Serious Bias" (2025, doi.org/10.1177/00491241251338246);
Tai et al. (2024).

**AI brain:** Anthropic, "Building Effective Agents" (anthropic.com/engineering/building-effective-agents);
Multi-LLM Thematic Analysis w/ dual reliability (arxiv.org/abs/2512.20352); LOGOS (arxiv.org/pdf/
2509.24294); Neo-Grounded Theory (arxiv.org/pdf/2509.25244); Agent-as-Peer-Debriefer (arxiv.org/pdf/
2605.24600); BERTopic (emergentmind.com/topics/bertopic); RouteLLM (arxiv.org/pdf/2410.10347); RAG
faithfulness (arxiv.org/pdf/2505.04847); LLM-as-judge position bias (arxiv.org/abs/2406.07791); prompt
caching economics (leanlm.ai/blog/prompt-caching).

**Data pipeline:** hiQ v. LinkedIn; Meta v. Bright Data (fbm.com/publications/…meta-platforms-v-bright-
data); EDPB/CNIL web-scraping guidance; Reddit API pricing (socialcrawl.dev/blog/reddit-data-api-2026);
Airbyte vs Fivetran vs Meltano (portable.io/learn/fivetran-vs-airbyte-comparison); Microsoft Presidio
(github.com/microsoft/presidio); Recall.ai / Gong integration.

**Recruitment & panel:** dscout pricing & methods (cleverx.com/blog/dscout-pricing-plans-and-costs-
explained-2026; dscout.com/platform/methods/diary-studies); Respondent/Prolific/User Interviews
comparisons; Klykken (2022) "continuous consent" (journals.sagepub.com/doi/10.1177/14687941211014366);
research incentives & fatigue guides (Great Question, User Interviews).

**Product/platform:** Dovetail Fall 2025 launch (dovetail.com/blog/2025-fall-launch); Marvin Deep
Research; multi-tenant AI SaaS patterns; LiteLLM vs OpenRouter; Langfuse + LiteLLM OSS LLMOps stack; MCP
design guidelines (AWS Labs github.com/awslabs/mcp/blob/main/DESIGN_GUIDELINES.md;
modelcontextprotocol.io); `openai/codex-plugin-cc`.

*Note: model version numbers and API prices (esp. Reddit/X) reflect mid-2026 sources and move fast —
treat tiering logic as durable and exact figures/model IDs as config to re-verify at build time.*
