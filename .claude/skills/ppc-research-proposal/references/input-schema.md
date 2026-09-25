# Input schema

Normalize the prospect request into this structure before any research. Infer what is safe to infer (industry from the website, geography from the cities named); flag what is essential and missing rather than inventing it. Nonessential gaps get a transparent assumption logged in the internal note.

## Prospect
- Company or professional name, website, industry (picks the regulated-industry module, if any)
- Target geography as the prospect stated it (cities, metro, region, national), and how far customers travel for this service
- Primary business objective in the prospect's words (qualified inquiries, consultations, demos, appointments, purchases, opportunities)
- The contact, how they reached out, date, and the deadline if any

## Services or products
- Priority services, procedures, products, or categories, in the prospect's order
- Revenue or margin priorities if stated (otherwise say "not provided"; do not assume case values)

## Search inputs
- Seed keywords and phrases the prospect supplied (every one must appear in the research snapshot)
- Competitor names if relevant

## Paid-search research inputs (the ones that make the budget defensible)
- Google Ads Keyword Planner export for the target geography (historical metrics and, if available, forecasts)
- Existing Google Ads account data (search terms, CPC, impression share, conversions) when the prospect already advertises
- Other first-party platform data (Microsoft Advertising, Meta) where appropriate
- Third-party research platform data (Semrush, Ahrefs, SpyFu, similar) as supplemental evidence

Essential: at least one of the first three for the actual geography. Without it the assessment is provisional, and the deliverable must say so (see research-methodology.md, "When local platform data is missing").

## Historical business data, if the prospect or agency has it
- CPC, CTR, landing-page conversion rate, cost per lead
- Qualification rate, appointment or demo rate, close rate, revenue or lifetime value
- Period and source for each figure

Any funnel or outcome forecast requires these. Without them, outcomes are measured in the first campaign, not forecast.

## Commercial inputs (human decisions; never inferred)
- Management fee, setup fee, pricing structure
- Contract term, cancellation policy, proposal validity
- Conflict-of-interest answer, market exclusivity position
- Guarantees or commitments the agency is willing to make (usually none)

## Sender and reviewer
- Agency name as it goes on the proposal, sender name and title, contracting entity (to confirm)
- Any party behind the work that must not appear in client-facing files
- Who reviews before anything is sent

## Output locations
- OUTPUT_DIR (default ./<prospect-slug>-ppc/), run date
