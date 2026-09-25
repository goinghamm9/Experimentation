# Lessons from live runs (read at Step 1; append after every run)

## The big one
The first live run (Hartigan, September 2026) jumped from the prospect's email to a seven-agent implementation manual: population-scaled "local" demand, a $3,000/$6,000/$9,000 ladder, 9.37 qualified inquiries a month, a 16-section proposal, HIPAA data-flow tables, and 90-day gates, all before anyone asked for Keyword Planner data. The rebuilt workflow puts the data request first, recommends one entry budget from coverage math, keeps the proposal to a few pages, and moves implementation to Stage 2. If you feel the run drifting toward campaign maps and funnel decimals, stop and check which stage you are in.

## Research
- Population share times a national volume is a model, not local data. Use it only to size an order of magnitude while the export is requested, label it provisional, and keep it out of the client findings.
- Verify the prompt's own facts (a prior-institution tenure, a statute chapter) against primary sources before they reach a deliverable.
- A search summary asserting a capability ("specializes in robotic surgery") without a supporting page is unverified; make it a kickoff confirmation.
- "Verified" for a location means a page names the person at that site; a surgery center's own page does not prove a surgeon operates there; competitor sentences overreach ("offer the same procedures") unless each competitor was checked.
- Keep benchmark figures attributed to their report and year; do not blend two reports into one range.
- Cloud sessions often block direct page fetches while web search works; cap fetch attempts, verify at search depth, and label it. PageSpeed Insights may be out of quota; never guess a score.

## Budget
- Coverage math (searches x impression share x CTR x CPC) is transparent and reproducible; a click-cap-by-demand model layered on funnel rates is not, and it produces false precision.
- Read impression share correctly: lost-to-budget and lost-to-rank are different signals, and a high lost-to-rank number does not mean the market is demand-bound.
- A conversion count before Target CPA is a Google recommendation and an agency rule, not a requirement.

## Proposal
- Build from content-as-data with scripts/docx_builder.py; a fix is a one-line edit and a rebuild.
- Measure page count on a fresh PDF; a stale PDF once hid a page overflow.
- python-docx leaves creator "python-docx", a 2013 created date, and a Mac Word app tag; the builder sets author, dates, title, and exactly one Company element (a duplicate element risks Word's unreadable-content prompt).
- A section that is only bracketed options reads as indecision to the prospect; give the agency a suggested position as a highlighted sentence they can strike, and keep the options.
- If the prospect said "cost per lead", show cost per contact; readers look for that word.

## Process
- Parallel agents write their own sources files; merge with scripts/merge_sources.py.
- A red-team pass, fixes, and one recheck by the same agent catches most embarrassments; run scripts/check_package.py before and after.
- Commit the output directory after each step when working in a repository.
