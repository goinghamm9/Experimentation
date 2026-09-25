# Stage 2: implementation planning (after the prospect advances)

Run this stage only when the prospect has agreed to proceed, or when the user explicitly asks for implementation detail. It reuses the research snapshot and the entry budget; it does not restart research.

## Inputs to confirm at kickoff
Ad account access (or creation in the prospect's name), the prospect's confirmation of every capability or location the research marked unverified, intake hours and who answers, the qualification definition for a lead, historical conversion data if any, brand-approval requirements from a parent organization, the site vendor contact, and the compliance owner for regulated verticals.

## Deliverables (each on its own, as needed)
- Campaign structure: campaigns and ad groups by cluster and intent, geography settings (presence only; radius or city targets; wider reach only for service lines that draw from farther), ad schedule matched to staffed hours, budgets by campaign in dollars.
- Keyword and match strategy, with a negative list (jobs, training, unrelated meanings, DIY, litigation, and the vertical's own noise) and the judgment calls (cost, insurance, recovery terms) stated.
- Bidding strategy by phase: start with click-based or manual bidding while conversions are sparse, move to conversion-based bidding as the account accumulates conversions; state which thresholds are platform recommendations and which are the agency's evaluation rule. Do not describe a conversion count as a Google requirement.
- Ad copy: responsive search ads per cluster with character counts, angles to test, and assets; policy-safe (no outcome promises, no unverified capabilities, no unapproved trademarks, no competitor names).
- Landing-page briefs: one page per launch cluster with required elements, where pages live (parent site, own site, dedicated domain) and the tracking, privacy, and brand-approval trade-offs; a section outline for the top page.
- Tracking specification: call tracking (number insertion, static numbers for call assets, recording settings), form events without contents, ad-platform conversion actions (primary versus secondary), analytics configuration, and for regulated verticals the data-flow table (what reaches the platform, what stays protected, what is reported in aggregate), vendor data agreements, offline-conversion and enhanced-conversion decisions with the approvals they need.
- Measurement architecture and reporting: the funnel from click to the prospect's outcome, which number steers decisions (the prospect's own qualified counts) and which optimizes bidding (platform conversions), reconciliation, monthly report contents, review cadence.
- Optimization gates and a 30/60/90-day plan: tracking verified, search-term and lead-quality review, scale or hold or cut rules tied to impression share (lost-to-budget versus lost-to-rank analyzed separately), cost per contact, and the prospect's qualified counts.
- Implementation timeline from signature to launch with dependencies (access, approvals, site vendor, data agreements).
- Regulated-vertical detail per `regulated-industries.md` (Stage 2 list), with citations verified against primary sources.

## Standards that carry over
Every number traces to the snapshot or a labeled assumption; ranges, not decimals; unverified facts become confirmations; privacy defaults hold; no em-dashes; no hype; no promised results; human decisions stay placeholders. Use `scripts/check_package.py` on any client-facing document.
