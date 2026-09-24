# Decisions and assumptions log (orchestrator)

| ID | Date | Decision or assumption | Reasoning |
|---|---|---|---|
| O1 | 2026-09-24 | Live Keyword Planner is skipped. Data falls to source priority (c), (d), and (e). | No browser session is logged into a Google Ads account, KEYWORD_PLANNER_EXPORT is blank, and the standards forbid creating accounts. |
| O2 | 2026-09-24 | Agents verify through web search results and search-engine page summaries; direct fetches are attempted at most twice per domain. | The network egress policy blocked every direct fetch tested (tcomn.com, davidhartiganmd.com, hhs.gov, support.google.com, wordstream.com, revisor.mn.gov, adstransparency.google.com). Search still surfaces page content. Each source is labeled with verification depth. |
| O3 | 2026-09-24 | Each agent writes sources_X.md; the orchestrator merges into sources.md between phases. | Parallel agents writing one file would clobber each other. |
| O4 | 2026-09-24 | TCO is treated as Twin Cities Orthopedics pending Agent A's verification. | The first search returned a TCO physician profile for David E. Hartigan. |
| O5 | 2026-09-24 | Stephanie's last name, role, and email are not in the forwarded email; the proposal addresses her as "Stephanie" with a placeholder for her title. | Kristina holds the direct contact details. |
| O6 | 2026-09-24 | Proposal format: a clean, plain Humanus-branded document built from scratch. | HUMANUS_TEMPLATE is blank. |
| O7 | 2026-09-24 | The docx and xlsx are built with python-docx and openpyxl, then recalculated and render-checked in LibreOffice. | Both libraries installed; LibreOffice present. |
| O8 | 2026-09-24 | Questions for James are deferred to the final report rather than asked mid-run. | The run prompt says not to stop for questions; James asked for questions "as needed", which the open-decisions list satisfies. |
| O9 | 2026-09-24 | Installed the LibreOffice Writer and Calc packages in the session container (only the core package was present) so the xlsx can be recalculated and the docx rendered for checks. | The run prompt requires formula recalculation and a render check. The install is local to this session and touches no deliverable. |
| O10 | 2026-09-24 | PageSpeed Insights is unavailable for this run: the public API answered HTTP 429 (daily quota exhausted) on three attempts, and the web UI is blocked by the network policy. Agent E audits pages from search results and labels mobile speed as unmeasured. | Two retries five seconds apart returned the same quota error. Kristina can run PageSpeed Insights in a browser in two minutes; the note to her says so. |
