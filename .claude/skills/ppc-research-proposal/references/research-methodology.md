# Research methodology: local paid-search data first

The budget recommendation rests on what people in the target geography actually search and what those clicks cost there. Everything else is context.

## Evidence hierarchy (use the highest available; label every number with its level)
1. **Observed platform data for the geography**: Google Ads Keyword Planner historical metrics (12-month average monthly searches, top-of-page bid low and high, competition) with locations set to the prospect's geography; an existing Google Ads account's search terms, CPC, impression share, and conversion data.
2. **Platform forecasts for the geography**: Keyword Planner "Get search volume and forecasts" (clicks, impressions, cost, CPC at a given bid or budget).
3. **Other first-party platform data** where appropriate (Microsoft Advertising Keyword Planner, Meta for demand context).
4. **Credible third-party paid-search platforms** (Semrush, Ahrefs, SpyFu, Similarweb) as supplemental evidence: volume and CPC at the national or metro level, competitor ad presence.
5. **Current industry benchmarks** (WordStream by LocalIQ, LocalIQ vertical reports, and similar) for context only: what a category's CPC, CTR, and cost per lead look like nationally. Never present these as local auction data.
6. **Model assumptions**, only when clearly marked provisional, with the ratio or share stated.

Population-scaling a national volume to a metro is a level-6 model, not research. It may fill a gap to size an order of magnitude while the export is requested; it never drives the recommendation once platform data exists, and it never appears in the client proposal as a finding.

## How to obtain the platform data
- Ask for it first: the sender (or the prospect, if they have an account) runs Keyword Planner in about 15 minutes. Give exact instructions (below) rather than a vague request.
- A browser session that is already logged into a Google Ads account may run Keyword Planner live. Never create an account, accept terms, or add billing; if anything prompts for that, stop and fall back to the request.
- An existing account beats Keyword Planner: pull the last 90 to 365 days of search terms, CPC, impression share (and its split between lost-to-budget and lost-to-rank), and conversions by campaign.

### Keyword Planner instructions to hand the sender
Tools and settings > Keyword Planner > Get search volume and forecasts. Paste the keyword list (the seed searches plus the representative keywords per cluster from the snapshot). Location: one run per geography level the prospect named (priority cities; the metro or DMA; the state or country if a service line draws from farther). Network: Google. Language: as appropriate. Date range: last 12 months. Download the Historical metrics view (average monthly searches, three-month change, year-over-year change, competition, top-of-page bid low and high) and the Forecast view if shown. Send the CSVs. Put each run's values in the snapshot with evidence_type "observed" (historical) or "forecast".

## When local platform data is missing
Say so, in the internal note and in the proposal's limitations line. Then do exactly one of:
1. Request the export with the instructions above and pause the budget recommendation, or
2. Produce a clearly labeled PROVISIONAL assessment using levels 3 to 6, with every provisional number marked, a sentence saying what would replace it, and the recommendation phrased as an order of magnitude ("likely $2,000 to $4,000 a month; confirm with Keyword Planner before treating this as a researched figure").
Never present a modeled or scaled figure as observed. `scripts/entry_budget.py` labels the result PROVISIONAL automatically when any priority cluster lacks observed or forecast data.

## Research snapshot (internal evidence table)
One row per representative keyword (or per cluster where the platform gives cluster totals), columns as in `assets/research_snapshot_template.csv`: cluster, geography, keyword, searches low and high, CPC low and high, competition, evidence_type (observed, forecast, third_party, benchmark, modeled), source, date, confidence, priority, notes. Keep it in OUTPUT_DIR as `research_snapshot.csv`; every number in the proposal traces back to a row.

## Clustering
Group by the prospect's services or categories and by intent: provider-seeking terms ("near me", "surgeon", "attorney", "company"), service or product terms, and research or condition terms. The first two carry the entry budget; research terms are context or a later test. Include every seed keyword the prospect supplied. Note which clusters are thin (too little demand in the geography to justify their own campaign) and which are broad (generic terms that would draw unrelated intent).

## Market observations (short, factual)
Who advertises on these terms (from third-party tools, Ads Transparency Center, or a plain search), how the prospect's own pages compare as destinations, seasonality if the platform shows it, and anything about the prospect's parent organization that affects whether a campaign can run (brand approval, an existing agency). Facts about the prospect or competitors are either verified with a source or marked unverified; unverified items become kickoff questions, not assertions.

## Reading platform metrics correctly
- Impression share, lost impression share due to budget, and lost impression share due to rank are three different signals. Lost-to-budget means more demand than the budget buys. Lost-to-rank means bids or quality are too low to win auctions that exist. High lost-to-rank is not evidence that a campaign is demand-bound.
- CPC, available search demand, and conversion or lead quality are analyzed separately; a cheap click on a broad term is not the same opportunity as an expensive click on a provider-seeking term.
- Distinguish platform requirement (what Google enforces), platform recommendation (what Google's help pages suggest), agency operating rule (what the sender prefers), and model assumption. Google does not "require" a conversion count before Target CPA; a minimum conversion volume is a recommendation and an agency evaluation rule.

## Source discipline
For every important number keep source, geography, date or period, evidence level, and confidence. Prefer current, primary sources. Never fabricate a citation or a platform figure. If tools cannot reach a page, record the depth actually achieved (search snippet, search summary) and say so.
