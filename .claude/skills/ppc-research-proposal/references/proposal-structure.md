# Proposal structure, voice, and build rules (Agent F)

Contents: who and voice; structure (16 sections plus appendix); placeholders; length and how to measure it; build and checks; presenting modeled results honestly.

## Who and voice
- Sender line: "{{Sender name}} | {{Title}}, {{Agency}}". The hidden party (the consultancy doing the work) never appears, in text or metadata.
- The prospect's contact is comparing several firms and set a measurement standard. Lead with that standard. Answer every item they asked for so they can check items off. Length does not win; specificity does.
- Voice: plain, confident, specific, warm but not salesy; first person plural; short paragraphs. Local knowledge used briefly. Competitor references factual and brief. Every number a range with a one-line basis; detail in the appendix. No hype, no promised results, no em-dashes, budgets in absolute dollars.

## Structure (numbered headings 1 to 16, then Appendix)
1. Opening, 3 to 4 sentences: thanks, what was asked, what this proposal does, and that it is built around the prospect's measurement standard.
2. At a glance: a compact table (recommended entry budget with range plus the fee reference; strategy in three lines; what we measure; time to launch with its dependencies; terms in one line; conflict check pointing to section 14). Then a "Your checklist" table mapping each RFP item to the section that answers it.
3. Our understanding: goals, the listed services, geographies (the prospect's locations as verified, the wider ring if any), and the qualified-inquiry standard with the provisional definition to confirm at kickoff.
4. Recommended strategy: launch clusters and why (demand, verified emphasis, learning speed); campaign table (campaign, ad groups, geography); targeting and match types; bidding by phase; negatives and audiences (none on sensitive categories); confirmations (conditional claims run only after the prospect confirms); one line on Microsoft Advertising.
5. Suggested monthly ad spend: the entry budget and the tier table with allocation by cluster in dollars; a modeled-results table (contacts, qualified inquiries, outcomes) low / base / high; one plain sentence that the low case is demand-bound (the platform finds little to buy, and the day 30 impression share report shows which case is real); media paid directly to the platform.
6. Expected cost per click, per contact, per qualified inquiry, and per outcome: ranges with a one-line basis each; state plainly that they are modeled from national benchmarks and demand estimates, not local auction data, and that the first 30 days replace them.
7. Landing page recommendations: what exists and why it is not a finished ad destination (specific, kind); one page per launch cluster and its required elements; where pages live with trade-offs (tracking, privacy, brand approval) and the conditions that change the choice; sample ads and an outline are ready for the call.
8. Conversion tracking, privacy-first: funnel; calls (data-agreement vendor, number insertion, static number for call assets, platform recording off); forms (event only); the three-column table (flows to the platform / stays protected / aggregate only); analytics stance; offline import as an approved option; the qualification rubric; monthly de-identified review; compliance owner and counsel review, not legal advice.
9. Reporting: monthly contents, cadence, quarterly review, no protected information; which number we steer by and why platform counts differ.
10. Timeline: signature to launch as a week-by-week table with the three dependencies that move the date; then the 90-day pilot milestones with decision rules and thresholds as rounded ranges.
11. Management and setup fees [SENDER TO SET]: two or three client-facing structures with highlighted amount placeholders and an instruction line to keep one.
12. Contract and cancellation terms [SENDER TO CONFIRM]: pilot term then month-to-month; notice period; the client owns its ad account, data, and page content; media billed by the platform directly; data agreement if the sender handles protected information; approvals; validity window.
13. Not included: media; site work beyond the scoped pages; SEO; photo or video; legal and compliance review; intake staffing; other channels until tested.
14. Conflict disclosure [SENDER TO CONFIRM]: two highlighted drafts (no conflicts; disclosed relationship and how it is walled off) and a keep-one instruction.
15. Market exclusivity [SENDER TO DECIDE]: one highlighted sentence with a suggested position (scope, geography, duration, conditions; broader exclusivity at a different fee level) so the reader sees a stance, then the four option bullets as highlighted placeholders. A section that is only blanks reads as "we have not decided."
16. Next steps: a 30-minute call with two highlighted windows; access needed (ad account, site vendor, group marketing contact if approval is needed, intake lead, privacy owner, the kickoff confirmations); what week one delivers; signature line.
Appendix (new page): A. Top 20 to 25 keywords with ranges and source labels; B. Tier detail table with one worked arithmetic example using unrounded intermediates; C. Assumptions that most move the result, and a compact source list (publisher, what it measures, geography, year; URLs for the top four or five).

## Placeholders
Everything the sender must set, confirm, or decide is written in square brackets with a tag ([SENDER TO SET], [SENDER TO CONFIRM], [SENDER TO DECIDE], [SEND DATE], [PHONE]) and highlighted yellow in the docx; the markdown keeps the same brackets. Expect 25 to 30 in a full proposal. Anything unverified about the prospect becomes a kickoff confirmation, not a placeholder and not an assertion.

## Length and how to measure it
Main body 4 to 6 pages at 11-point body text with one-inch margins (about 2,500 to 3,300 words including tables). Measure on a FRESH PDF (delete any earlier PDF first): convert the docx with LibreOffice, open it with pymupdf, and find the first page whose text starts with the appendix heading. When the body runs over, cut prose, not answers: shorten hosting, tracking, reporting, and next-steps wording; drop sample headlines from section 7 (they live in 05); tighten paragraph spacing from 3 to 2 points before touching any table. scripts/check_package.py does the measurement.

## Build and checks
- Write the content as Python data (COVER, SECTIONS, APPENDIX, FOOTER_TEXT, META) in a content module and build both files with scripts/docx_builder.py so the docx and the md cannot drift and a fix is a one-line edit plus a rebuild.
- US Letter, one-inch margins, Arial 11 body, headings 14 and 12 in a dark navy, tables in Table Grid with a gray header row at 10 point, footer with agency, city, "Confidential", and a page number field. Metadata: author and last modified by the sender, title set, comments cleared, a real created date, one Company element in app.xml (the builder handles this).
- Before handing off, run scripts/check_package.py with the hidden party's name in --banned-names and the appendix heading; render three pages and look at them (tables inside margins, highlights visible, footer present).
- Facts about the prospect, its group, or competitors appear only if 01 or 05 carries them with a source ID; anything those files mark unverified is not asserted (attribute the prospect's own claims to the prospect: "the services you listed").

## Presenting modeled results honestly
A three-case model can produce a low case where spend collapses (little demand at a low CPC) while cost per outcome rises; presenting that as a spend line confuses a reader. Present it as a demand-bound scenario in one sentence and lead the tables with contacts, qualified inquiries, and outcomes rather than clicks. Note in the appendix why the high case can show fewer clicks than base when its CPC is also high. Fractions in model averages are fine when labeled as model averages.
