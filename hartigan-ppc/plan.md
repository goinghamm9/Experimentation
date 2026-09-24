# Run plan: Google Ads research to proposal (Dr. David Hartigan, for Humanus Marketing)

Run date: Thursday, September 24, 2026. Orchestrator: Claude (for James Hamm, Samprand COO). Output directory: ./hartigan-ppc/

## Environment findings that shape the run
- No browser session is logged into Google Ads, and KEYWORD_PLANNER_EXPORT is blank. Live Keyword Planner (source priority b) is unavailable. Demand and cost data fall to priority (c) published benchmarks, (d) third-party keyword tool data reachable without login, and (e) modeled estimates, each labeled.
- Web search works. Direct page fetches (WebFetch, curl) are blocked by the network egress policy for nearly every domain tested (tcomn.com, davidhartiganmd.com, hhs.gov, support.google.com, wordstream.com, revisor.mn.gov, adstransparency.google.com). Agents verify through search results, snippets, and search-engine page summaries, and label the verification depth. The PageSpeed Insights API endpoint answered (HTTP 429), so Agent E retries it.
- Subagents are available (Agent tool). Each phase runs as parallel subagents with self-contained briefs.
- Skills available for the final deliverables: python-docx and openpyxl installed; LibreOffice installed for recalculation and render checks.

## Phases, agents, files, dependencies

| Phase | Agent | Role | Output files | Depends on |
|---|---|---|---|---|
| 0 | Orchestrator | Plan, brief, decisions log, sources skeleton | plan.md, 00_brief.md, decisions.md, sources.md | none |
| 1 | A | Practice and market intelligence | 01_market_intel.md, sources_A.md | 00_brief.md |
| 1 | B | Keywords and demand | 02_keywords.csv, 02_keyword_summary.md, sources_B.md | 00_brief.md |
| 1 | C | Measurement, tracking, compliance | 03_measurement_compliance.md, sources_C.md | 00_brief.md |
| 1.5 | Orchestrator | Merge sources, reconcile A vs B (demand ceilings vs market picture), pick launch-cluster guidance for D and E | sources.md, decisions.md | A, B, C |
| 2 | D | Strategy and budget model | 04_budget_model.xlsx, 04_strategy.md, sources_D.md | A, B, C |
| 2 | E | Landing pages and ad creative | 05_landing_creative.md, sources_E.md | A, B, C, launch clusters from orchestrator |
| 2.5 | Orchestrator | Reconcile D clusters with E pages, merge sources | sources.md, decisions.md | D, E |
| 3 | F | Proposal writer | 06_proposal.md, 06_proposal.docx | A to E |
| 4 | G | Red team | 07_qa_report.md | all |
| 4.5 | Orchestrator | Fix blockers and majors; G rechecks changed sections once | changed files, 07_qa_report.md addendum | G |
| 5 | Orchestrator | Note to Kristina; render and formula checks; em-dash sweep; commit and push | 08_note_to_kristina.md | all |

## Source ID convention
Each agent prefixes IDs with its letter (A1, B1, C1, D1, E1). Agents write their entries to sources_X.md. The orchestrator concatenates them into sources.md after each phase so parallel agents never write the same file. Entry formats:
- Source: ID | publisher | URL | date accessed | what it measures | geography | year | verification depth (page read, search snippet, search summary)
- Assumption: ID | statement | reasoning | what would change it

## Status at close (2026-09-24)
All phases complete. Phase 4 fixes applied and rechecked once by Agent G. Files delivered: 06_proposal.docx and .md, 04_budget_model.xlsx, 08_note_to_kristina.md, 01 to 05, 07_qa_report.md, sources.md, decisions.md.

## Protection order if time runs short
1. 06_proposal (docx and md)
2. 04_budget_model.xlsx
3. 08_note_to_kristina.md
4. Everything else
