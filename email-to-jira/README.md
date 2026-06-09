# Email → Jira Ticket Pipeline (v1 — human-in-the-loop)

Ingests client emails and Google Meet transcripts, has Claude draft Jira
**ticket candidates**, and lets a single operator review, edit, and approve
them in a dashboard. **Nothing reaches Jira without an explicit Approve
click** — that is the v1 invariant.

## Quick start (no keys needed)

```bash
make setup      # venv + dependencies
make harness    # feed fixture emails through the pipeline (offline stub model)
make dev        # dashboard at http://localhost:8000  (login: operator / change-me)
make test       # run the test suite
```

`make harness` is the test harness: it runs the fixture emails in
`tests/fixtures/emails/` through ingest → candidate generation with a
deterministic offline stub, so you can exercise the whole review flow —
including a Meet transcript, which drafts multiple candidates — before adding
any credentials. Add your own fixtures as JSON files in that directory to
build test cases.

**Jira dry-run is ON by default** (`JIRA_DRY_RUN=true`): the Approve button
runs the entire flow — payload built, candidate approved, audit written — but
mints a `DRY-MSA-1`-style key instead of creating a real issue. The dashboard
shows a banner while dry-run is active. That means you can test everything
today with a single credential: an Anthropic API key.

## Testing mode, today

1. `cp .env.example .env`, set `ANTHROPIC_API_KEY` (console.anthropic.com).
2. `make harness-live` — real Claude drafts from the fixtures.
3. `make dev` — review, edit, approve (dry-run), reject in the dashboard.
4. Paste a real client email or a Meet transcript via the dashboard forms and
   see what it drafts. Transcripts produce one candidate per commitment.
5. Add 2-3 few-shot examples (see below) and re-paste the same source — this
   is the fastest way to watch quality respond to examples.

## Going live

1. Fill in the rest of `.env`:
   - `JIRA_EMAIL` + `JIRA_API_TOKEN` — an [API token](https://id.atlassian.com/manage-profile/security/api-tokens)
     for `samprand.atlassian.net` — and set `JIRA_DRY_RUN=false`.
   - `DASHBOARD_USER` / `DASHBOARD_PASS` — change these.
2. `make harness-live` — same fixtures, real Claude. Sanity-check draft quality.
3. Gmail (label on your existing inbox):
   - In Google Cloud: enable the Gmail API, create an OAuth *Desktop* client,
     download it as `credentials.json` into this directory.
   - In Gmail: create the `jira-intake` label (or change `GMAIL_LABEL`) and a
     filter that applies it to client mail. Meet/Gemini transcript emails under
     the same label are auto-detected and ingested as transcripts.
   - `make poll` — first run opens the OAuth consent screen and stores
     `token.json` locally (read-only scope; the inbox is never modified).
4. Schedule the poller while your machine is awake (review is manual anyway):
   ```
   */15 * * * * cd /path/to/email-to-jira && .venv/bin/python -m scripts.poller >> poller.log 2>&1
   ```
5. Approve a few candidates end-to-end on MSA before enabling more boards.

## How it flows

```
Gmail label ──poller──▶ emails table ──Claude──▶ candidates (pending)
paste transcript ──┘        │ (idempotent)            │  1 per work item;
                            ▼                         ▼  meetings yield several
                      needs-review queue   dashboard: edit / reject(reason)
                      (on parse failure)              │
                                              [Approve click]  ◀── the only
                                                      ▼            Jira path
                                            Jira issue (ADF) + audit entry
                                            (or DRY-* key in dry-run mode)
```

Every state change (ingested, drafted, edited, approved → issue key,
rejected → reason) lands in the append-only `actions` table (`/audit`).

## Per-board configuration

Board knowledge lives in `projects/<KEY>.yaml`, not code: allowed issue
types, conventions, board rules, glossary, and few-shot examples. **MSA is
wired**; PV0/MS/OR/KBS/OLAW/NAMA are templates with TODOs — fill one in and
set `enabled: true` when ready. Two real rules ship as examples:

- `PV0.yaml` sets `set_sprint_on_subtasks: false` — Jira rejects sprints on
  PV0 sub-tasks (they inherit the parent's sprint).
- `PV0.yaml`'s glossary pins the Pearme coaching agent's name to **"Lea"**.

### Few-shot examples — the main quality lever

How tickets get written per board is learned from examples, not code. Each
board's examples live in two merged places: inline in `projects/<KEY>.yaml`
and in `projects/examples/<KEY>.yaml` (written by the dashboard). Three ways
to grow them:

1. **Dashboard → Examples page**: paste a source email/transcript + the ideal
   ticket. This is where your past Claude/ChatGPT drafting chats go — open an
   old chat, copy the client email you pasted in as the *source*, and the
   final ticket you settled on as the *ticket* fields. 2-3 good pairs per
   board move quality more than any prompt tweak.
2. **"Save as few-shot example"** button on any candidate: after you edit and
   approve a draft, one click stores the source → final-ticket pair. Reviewing
   tickets grows the example base as a side effect.
3. Edit the YAML files directly (`projects/examples/README.md` has the format).

Prompt fragments live in `prompts/` and are assembled at runtime
(global rules + board YAML + merged few-shots + output schema), so tuning
needs no code changes. Each candidate stores the exact prompt and raw model
response, and rejection reasons are captured — so you can see exactly why a
draft came out wrong and which example would fix it.

## Deferred features (interfaces only, not implemented)

- `core/router.py` — `TaskRouter`: route task types to Claude vs. OpenAI.
- `core/docgen.py` — `DocGenerator`: sprint wrap-ups → Google Drive.
- `core/viz.py` — `Visualizer`: JQL → Mermaid diagrams.
- `core/transcripts.py` — `TranscriptSource`: auto-fetch Meet transcripts from
  Drive. (v1: transcript emails arrive via the label; Drive-only transcripts
  are pasted into the dashboard's "Add transcript" form.)
- Silent auto-creation and multi-user roles: intentionally absent.

## Deployment notes

Runs anywhere Python 3.11 does. For Railway: deploy the web app
(`uvicorn app.main:app --host 0.0.0.0 --port $PORT`) and, if you later want
always-on polling, add a second service/cron running `python -m scripts.poller`.
SQLite needs a persistent volume. Current setup assumes local-first (poller
via cron on your machine), which costs nothing.

## Security

- All secrets in `.env` (gitignored); `.env.example` documents the shape.
- Gmail OAuth token stored locally, read-only scope.
- Email bodies / PII never appear in URLs or logs; IDs only.
- Dashboard: single-operator HTTP basic auth.
