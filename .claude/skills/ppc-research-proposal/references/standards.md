# Standards for every deliverable

Contents: numbers and sources; source priority for demand and cost; verification depth; privacy defaults; writing rules; ID conventions; what "done" means per file.

## Numbers and sources
Numbers are the credibility of the proposal; treat them as evidence.
1. Every number in every deliverable traces to sources.md, either to a cited source (publisher, URL, date accessed, what it measures, geography, year, verification depth) or to a numbered assumption with its reasoning and what would change it.
2. Low, base, and high everywhere. No false precision: modeled figures round to two significant figures in prose; the workbook may carry full precision.
3. Never present a national benchmark as a local figure. Label benchmarks with category and year, third-party tool data as third-party, modeled figures as modeled.
4. A labeled estimate is useful; an invented precise figure is disqualifying. If data is thin, say so in one line and move on.
5. Never state unverified facts about the prospect, its group, or competitors. Mark anything unverifiable as unverified, and turn it into a kickoff confirmation in the proposal ("we confirm X at kickoff"), never an assertion.
6. Prefer the relative ordering of clusters and tiers over any single number when the volumes are modeled; say so in the data-confidence statement.

## Source priority for search volume and cost
(a) A Keyword Planner export supplied by the sender; (b) Keyword Planner run live in a browser session that is already logged into a Google Ads account (never create accounts, accept terms, or add billing; if anything prompts for that, abandon the path); (c) published Google Ads benchmarks from the last 24 months for the vertical (WordStream by LocalIQ annual search benchmarks, LocalIQ vertical reports, other multi-account studies); (d) third-party keyword tool data reachable without logging in; (e) modeled estimates from population share and ratio assumptions. Log every fallback in decisions.md.

## Verification depth
Cloud sessions often cannot fetch pages directly (network policy). Label every source with the depth actually achieved: "page read" (the page itself was fetched), "search snippet" (a search result snippet), "search summary" (a search engine's summary of the page). A claim that rests on search depth is verified at search depth; say so in the note to the sender and offer the two-minute browser checks that would upgrade it.

## Privacy defaults (hold unless verification says otherwise)
- No audience targeting or remarketing on sensitive categories (health conditions, legal troubles, financial hardship, and so on).
- No protected or personal information to ad platforms: conversion events carry a name, click ID, and timestamp only.
- Any vendor that receives call recordings or form contents signs the vertical's data agreement (a BAA in healthcare).
- Offline conversion import is offered only as an option that needs the prospect's privacy or compliance owner's written approval, described in minimum-data form.
- Outcomes come back from the prospect in aggregate, monthly.
- If the sender would receive protected information, it needs its own agreement with the prospect (state it in the terms and in the note to the sender).
- Nothing is legal advice; the prospect's compliance owner and counsel decide. Say so once in the proposal.

## Writing
American English, plain and specific. No em-dashes or en-dashes anywhere, in any file, including spreadsheet cells and document metadata; use commas, periods, or colons. No hype words (cutting-edge, unlock, supercharge, game-changer, world-class, state-of-the-art, leverage). No promised results (guarantee, "will generate", "will deliver"). Superlatives about the prospect or the sender only when substantiated, and usually not at all. Budgets and budget changes in absolute dollars, not percentages alone. Competitor references factual and brief, never disparaging. Ranges carry a one-line basis; detail goes to the appendix.

## ID conventions
Agents prefix IDs with their letter (A1, B1, C1, D1, E1); assumptions start at 50 (A50, B50). Orchestrator decisions are O1, O2, ... in decisions.md. Each agent writes sources_<LETTER>.md; the orchestrator merges with scripts/merge_sources.py after each phase. Cite IDs inline like [A3] in research files; the proposal appendix cites publisher and year, with URLs only for the four or five most important sources.

## What "done" means per file
- 01 market intel: every claim has an ID or an unverified label; six tasks answered; an "Unverified and gaps" list at the end.
- 02 keywords: CSV parses, seeds present, IDs defined, ceilings match Python totals; the summary has a data-confidence paragraph naming what is benchmark, third-party, and modeled, and how an export upgrades it.
- 03 measurement and compliance: every legal, policy, and vendor claim has a source ID with a URL; the flags table is complete with owners and verification dates.
- 04 budget model: recalculates with zero errors, formula-only results tabs, inputs move outputs, and 04_strategy.md figures match the recalculated workbook.
- 05 landing and creative: every ad line within its character limit (Python-verified), conditional and confirm-at-kickoff labels on anything unverified, no brand names or superlatives.
- 06 proposal: every RFP item answered in the RFP's order; body within the page limit measured on a fresh PDF; every placeholder highlighted; clean metadata; no hidden-party name.
- 07 QA: issues ranked with exact fixes; blockers and majors fixed and rechecked once.
- 08 note to the sender: about one page; verified versus estimated, decisions, private risk read, draft reply, three call questions.
