# Outputs: research snapshot, internal recommendation, client proposal

Three layers, in OUTPUT_DIR. The client proposal is intentionally lighter than the research behind it.

## A. Research snapshot (internal): `research_snapshot.csv` plus `research_notes.md`
The evidence table (columns in `assets/research_snapshot_template.csv`) and a short notes file: clusters and what each contains, seed keywords covered, market observations with sources, landing-page observations, what could not be verified, and the exact Keyword Planner request if platform data is missing. Every proposal number traces to a row here.

## B. Internal recommendation: `internal_recommendation.md` (about one page)
- Recommended starting services or clusters and why
- Recommended entry budget with range, coverage it buys, evidence level (evidence-backed or provisional), and the coverage math summary from `scripts/entry_budget.py`
- Uncertainties and what would change the recommendation
- Missing inputs (essential versus nonessential)
- Human review checklist: fees, terms, conflict, exclusivity, guarantees, and any provisional figure the reviewer must accept before sending (see human-review.md)
- Suggested next-stage work if the prospect advances (see stage2-implementation.md)
- A draft reply to the prospect and two or three questions for the first call

## C. Client-facing proposal: `proposal.docx` and `proposal.md`
Two to four pages unless the user asks for more. Build it with `scripts/docx_builder.py` from a content module so the docx and md match; placeholders in brackets are highlighted automatically. Sender line is the agency's; no hidden party in text or metadata.

Structure:
1. **Opportunity and our understanding** (a short paragraph): the prospect's goal, the services, the geography, the business outcome that matters.
2. **Paid-search findings** (half a page): the meaningful clusters, monthly search demand in the geography as ranges, CPC and competition, two or three market observations, and one limitations line (what the data is, what it is not, and what is provisional). A compact table of clusters is fine; no keyword dumps.
3. **Recommended starting approach** (a short paragraph plus a few bullets): which clusters to prioritize, the geographic approach, the high-level strategy (search campaigns on provider-seeking and service terms, presence-only geography, staffed-hours schedule, no sensitive-category audiences), and why this is the right starting point. No campaign-by-campaign structure, match types, negative lists, bidding transitions, or optimization gates.
4. **Recommended entry budget**: the figure and range, what it covers, the rationale in two or three sentences, and what would cause it to scale up or down. Alternatives only if the research supports meaningfully different coverage.
5. **Measurement**: tie the campaign to the prospect's business objective (qualified inquiries and consultations, demos, appointments, purchases). Clicks and traffic are diagnostic. Say what is counted from day one (calls and forms with the prospect's qualification) and that conversion rates are measured in the first campaign rather than forecast, unless history exists. For regulated verticals, one or two sentences on the privacy-safe tracking posture; details later.
6. **Landing page and conversion considerations** (a few sentences): whether existing pages appear usable, whether dedicated pages are recommended, and the basic tracking requirement (call tracking, form event, ad-platform conversion). No page outlines or ad copy.
7. **Fees and terms**: only agency-supplied content; otherwise highlighted placeholders. Never invent fees, setup fees, term, cancellation, exclusivity, conflict answers, or guarantees.
8. **Next step**: one easy action, usually a 30-minute call or approval to develop the campaign plan, and what the agency needs to start.

Optional appendix (one page at most): the cluster table with sources and dates, and the assumptions behind the coverage math. Detailed keyword lists stay in the snapshot.

Voice: plain, specific, confident, warm; first person plural; ranges with a one-line basis; competitors factual and brief; no hype, no promised results, no em-dashes; budgets in dollars.

Length control: measure on a fresh PDF with `scripts/check_package.py --max-body-pages 4` (set `--appendix-heading` if an appendix exists). Cut prose before tables; cut tables before answers.

## What the first proposal leaves out on purpose
Campaign and ad-group maps, match-type and negative-keyword lists, bidding ladders, dayparting, 30/60/90 gates, ad copy, landing-page section outlines, vendor comparisons, BAA and call-routing architecture, statutory discussion, offline-conversion design, funnel projections beyond what history supports. These belong to Stage 2 after the prospect advances, or in the proposal only when the prospect explicitly asked for them, and then briefly.
