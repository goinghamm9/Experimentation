# Budget methodology: one evidence-backed entry budget

The business question is: what is a credible starting media budget for this prospect, given the services and geography they named? Answer it with one primary figure (or a tight range), the rationale, what it covers, and what would move it.

## Coverage math (the default)
For each priority cluster, with platform data for the geography:
- clicks available per month = monthly searches x target impression share x expected CTR
- media to buy them = clicks x CPC (use the platform's top-of-page bid range or observed CPC)
Sum across priority clusters at low and high inputs; the entry budget is the rounded midpoint, shown with its range. `scripts/entry_budget.py` does this from the research snapshot and writes a small live-formula workbook (Inputs and Coverage tabs) the sender can adjust on a call.

State the planning assumptions plainly: target impression share (a starting campaign rarely holds more than 40% to 65% of eligible impressions) and CTR (use the account's own CTR when history exists; otherwise a labeled planning range). These are assumptions, not findings.

If Keyword Planner forecasts are available, compare the coverage math with the platform's own forecast of clicks and cost at the recommended budget, and report both.

## What the entry budget is for
Say what it covers (which clusters, at roughly what share of eligible searches, in which geography) and what it does not (clusters deferred, geographies excluded). Say what it is designed to learn in the first 60 to 90 days: real CPC, impression share and where it is lost, search-term quality, contact volume, and the prospect's own conversion rates. Say what would justify raising it (lost-to-budget impression share on qualified terms with acceptable cost per contact) or lowering it (thin demand, poor search-term quality, budget not deploying).

## Priorities
Rank clusters for the entry budget by: demand in the geography, fit with what the prospect verifiably offers and emphasizes, CPC relative to likely value (qualitative unless the prospect supplied figures), and competition. Concentrate: an entry budget spread across every service rarely learns anything. Name what phases in later and on what evidence.

## Tiers
Do not manufacture round-number tiers. Offer alternatives only when the research supports meaningfully different coverage (for example, priority cities only versus the full metro; the top two clusters versus all clusters) or when the user asks for options. Each alternative must state the coverage difference, not just the dollar difference.

## No false precision
- Show ranges and rounded figures; never decimals of leads or consultations.
- Contacts, qualified leads, appointments, consultations, sales, or revenue are forecast only from the client's own historical rates (CPC, CTR, conversion rate, cost per lead, qualification rate, appointment rate, close rate) supplied through the history input, with period and source stated. Without those, write that these outcomes are measured during the first campaign.
- Benchmarks may give a directional cost-per-lead context sentence ("national physicians-and-surgeons cost per lead ran about $40 to $57 in 2025 to 2026 reports; surgical terms usually run higher"), labeled as context.
- Every figure carries its evidence level; a budget built on third-party, benchmark, or modeled inputs is labeled provisional in the internal note and the proposal.

## Existing account
When the prospect already advertises, the account is the primary source: real CPC, CTR, conversion rate, cost per lead, impression share and its lost-to-budget and lost-to-rank split, and search-term quality. Use those ahead of Keyword Planner and benchmarks, state the period, and base the entry budget on what the account shows it can deploy at acceptable cost per contact.
