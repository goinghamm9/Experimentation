# Lessons from live runs (read before planning; add to it after every run)

Contents: environment; orchestration; research; modeling; proposal; QA loop.

## Environment
- Cloud containers may ship LibreOffice core without Writer and Calc: every conversion fails with "source file could not be loaded" and recalc.py times out. Run scripts/env_check.sh first; apt-get install libreoffice-writer libreoffice-calc fixed it in one run even though PPAs were blocked.
- Direct page fetches are often blocked by the network policy (403 from the proxy) while web search still works. Decide at Phase 0 that agents verify at search depth, cap direct fetch attempts at two per domain, and label depth on every source. Tell the user how to widen network access for a rerun.
- PageSpeed Insights: the public API can be out of daily quota (HTTP 429) and the web UI blocked; do not guess a score. Mark "not measured" and hand the sender the two-minute browser check.
- Live Keyword Planner needs an already logged-in browser session; it is almost never available in a cloud session. Never create accounts or accept setup prompts. Fall through the source priority and log it.
- A stop hook may require commits after every turn: commit the output directory after each phase with a short message; it also gives the reviewer a phase-by-phase history.

## Orchestration
- Write plan.md, 00_brief.md, decisions.md, and a sources.md skeleton before launching anyone. Subagents never see the run prompt, so briefs must be self-contained: case facts, standards, tasks, exact output paths, done criteria, and the environment notes.
- Parallel agents write sources_<LETTER>.md; the orchestrator merges with scripts/merge_sources.py. Two agents appending to one file will clobber each other.
- Launch Phase 2 as soon as its hard dependencies exist; a late Phase 1 file (compliance) can be reconciled at the checkpoint. Log the choice as a decision.
- Between phases, reconcile explicitly and log each decision with reasoning: geography (wider ring versus statewide), unverified capabilities (technology terms run only after confirmation), launch clusters (thin clusters combine), and gates (a knee cluster kept at launch but gated on one kickoff question). Agents D and E need those IDs.
- Deferred questions go in the final report as open decisions; the run does not stop for them unless the core deliverable becomes impossible.

## Research
- Verify the run prompt's own facts: one prompt said four years at a prior institution (the bio says three) and cited the wrong statute chapter for a state privacy law. Correct the brief and log it.
- Facts a search summary asserts without a supporting page (for example "specializes in robotic surgery") are unverified; say so and turn them into kickoff confirmations.
- "Verified" for a location means a page names the person at that site; an address on a personal site is weaker than a group listing; a surgery center's own page describing the center does not prove a surgeon operates there. The red team will catch these; better to label them in Phase 1.
- Competitor sentences overreach easily ("offer the same procedures"): state only what 01 verified per competitor.
- Benchmarks: keep each figure attributed to its report and year (a physicians-and-surgeons cost per lead from one report and a healthcare-wide figure from another are not one range).

## Modeling
- Cap clicks at demand: min(budget / CPC, searches x query expansion x impression share x CTR). At an entry budget the cap binds in low and base cases; say that demand, not budget, is the first constraint, and that the day 30 impression share report resolves it.
- A low case that combines low demand with low CPC yields tiny deployed spend and high cost per outcome; present it as demand-bound, not as a spend line.
- Keep every threshold in one place (the Pilot Plan tab) and quote rounded versions; unify the same signal's threshold across files (one run had 20% lost-to-budget at day 30 and 10% at day 60 until QA caught it).
- Show arithmetic with unrounded intermediates (3.78, not 3.8) so a reader with a calculator reproduces it.
- Set workbook creator and lastModifiedBy to the sender; openpyxl leaves "openpyxl".

## Proposal
- Build from content-as-data with scripts/docx_builder.py; a QA fix is then a one-line edit and a rebuild. Save the content module to the scratchpad and name it in the final report so the sender can rebuild.
- Measure page count on a fresh PDF; a stale PDF reported six pages when the body had grown to seven after fixes.
- Metadata: python-docx leaves creator "python-docx", a 2013 created date, and "Microsoft Macintosh Word" in app.xml; the builder sets author, dates, title, and exactly one Company element (a duplicate Company element risks Word's "unreadable content" prompt).
- A section that is only bracketed options (exclusivity) reads as indecision; add one highlighted sentence with a suggested position and keep the option bullets.
- Add a cost per contact row when the RFP says "cost per lead"; readers look for that word.
- A rubric that names clinic cities must include every city the ads name.

## QA loop
- Red team, then fix every blocker and major plus the cheap minors, then send the same agent a recheck message (SendMessage keeps its context) listing what changed by file and issue ID. Expect it to find one or two new items from the fixes (a duplicate metadata element, a page overflow); fix and re-measure.
- Run scripts/check_package.py before the red team and again before handoff; it catches dashes in spreadsheet cells and metadata that a text grep misses.
- The note to the sender should end near one page; trim phrasing, not items.
