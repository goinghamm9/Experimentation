# CLAUDE.md — Email-to-Jira Ticket Pipeline

This file is always loaded. Read it before doing anything. Keep it accurate as the project evolves.

## What this project is
An internal web app for a software agency. It ingests client emails, has an AI draft **Jira ticket candidates**, lets a human review/edit/approve them, and only then creates real Jira issues.

## Current phase: v1 — human-in-the-loop ONLY
- IN scope now: email ingestion, AI candidate generation, review/edit/approve dashboard, Jira issue creation on approve, reject-with-reason, audit log, and a test harness that runs fixture emails through the whole pipeline.
- OUT of scope now (leave clean interfaces / stubs, do NOT implement): silent auto-creation, client-doc generation + Google Drive export, OpenAI/GPT task routing, Mermaid/workflow visualization, multi-user roles.
- **Invariant:** nothing irreversible (Jira create, any send, any save) happens without an explicit human approval click. Do not add background auto-actions in v1.

## Tech stack (use exactly this; flag a concrete reason before deviating)
- Python 3.11+, FastAPI
- SQLite via SQLModel (SQLAlchemy)
- Server-rendered UI: Jinja2 + HTMX + minimal CSS — no SPA, no build step
- Anthropic Messages API for parsing/drafting; **model name lives in config** (the app's runtime model should be a cheap Sonnet/Haiku-class model — this is the recurring cost, keep it low)
- Jira Cloud REST API v3 — issue descriptions use Atlassian Document Format (ADF); do NOT send raw markdown to the description field
- Gmail API (OAuth) — poll a dedicated label on a schedule (polling, not Pub/Sub)
- Secrets in `.env` (provide `.env.example`); per-project rules in editable YAML

## Repo layout (target)
```
app/            FastAPI app, routes, templates
  templates/    Jinja2 + HTMX views
core/           pipeline: ingest, generate, create
  router.py     TaskRouter interface (Claude only in v1; stub for GPT)
  docgen.py     DocGenerator interface (stub)
  viz.py        Visualizer interface (stub)
prompts/        prompt fragments assembled at runtime
projects/       one YAML per Jira board (templates with TODO placeholders)
tests/          pytest + fixture emails
.env.example
README.md
```

## Per-project configuration (this is where board knowledge lives, NOT in code)
Each Jira board gets a YAML in `projects/`: project key, allowed issue types, ticket conventions, board-specific rules, a terminology glossary, and few-shot examples (email → ideal ticket). Ship templates with TODO placeholders; the operator fills real data later.

Real rules that MUST be expressible per-board:
- **PV0:** sub-tasks inherit their sprint from the parent. Do NOT set the sprint field when creating a Sub-task on PV0 — Jira rejects it ("subtasks cannot be associated to a sprint"). Sprint-setting must be a per-board toggle, not hardcoded.
- **Glossary:** project-specific naming is verbatim — e.g. the Pearme coaching agent is always "Lea," never "Leia."

Boards to support (enable incrementally, wire ONE first): MSA, PV0, MS, OR, KBS, OLAW, NAMA.

## Candidate generation contract
- Assemble the system prompt from: global rules + the matched board's YAML + that board's few-shot examples.
- Output strict JSON: `summary, description, issue_type, project_key, priority, labels[], acceptance_criteria[], confidence (0–1), rationale, source_email_id`.
- Strip code fences, parse defensively. On parse failure or an API refusal, store the raw response and surface the email for manual handling — never crash, never silently drop.

## How to run / verify
- One-command dev run (add a `make dev` or documented command).
- A test harness that feeds fixture emails through ingest → generate → review without a live Gmail connection. Build fixtures early; the operator uses them to create test cases before any live keys are added.

## Working style for this repo
- Plan before building: propose the file tree and confirm open questions, then implement in small runnable checkpoints.
- After each meaningful change, run the tests and self-review (use /code-review).
- Prefer the cheapest correct approach (free tiers, SQLite, server-rendered, polling). Don't add dependencies without reason.
- Narrate intent as you work on autonomous stretches so a human can oversee.

## Open questions to confirm before coding
1. Gmail source: dedicated forwarding account, or a label on an existing inbox?
2. Jira Cloud base URL + which single board to wire first.
3. Dashboard auth: is single-user basic auth fine for v1?
4. Poller hosting: Railway always-on, or local cron when the machine is awake?
