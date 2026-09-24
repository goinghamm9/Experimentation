# 04 Strategy and budget model (Agent D)

Run date 2026-09-24. Figures are pasted from the recalculated 04_budget_model.xlsx; sources and assumptions are in sources_D.md (D1 to D15, D50 to D68). Volumes are modeled and low confidence (Agent B); benchmarks are national, not Twin Cities figures. The model shows what the assumptions imply, not what will happen.

## 1. Launch clusters and phasing

O13 confirmed (D50): launch hip replacement, knee replacement, and a small hip preservation campaign; ACL, meniscus, and rotator cuff run as one sports medicine campaign from the day 60 gate or the Growth tier. Reasons: demand (B63: hip replacement carries 800 to 2,500 and knee replacement 1,000 to 3,300 Tier 1 plus Tier 2 searches a month, the three sports clusters 250 to 1,100 each, hip preservation 120 to 590 with the O11 ring); fit (hip arthroscopy and anterior outpatient hip replacement are his verified emphasis, A1, A5 to A7, A20; robotic knee is unverified, O12); case value (outpatient hip replacement listed at $27,500, A20; otherwise qualitative); learning (at $3,000 a month, three campaigns each get a readable search term report by day 30, six would not). Sports medicine phases in at day 60 if the launch campaigns are demand-bound (impression share lost to budget under 10%) and cost per qualified inquiry is at or below base. Robotic and navigation ad groups wait for the practice to name the system and facility (O12).

## 2. Campaign architecture

Bidding ladder for every campaign: days 1 to 30 Maximize clicks with a $16 bid limit; Maximize conversions at 15 verified conversions in 30 days; Target CPA at 30 in 30 days (C14, D63). Schedule: Monday to Friday, 8 am to 5 pm Central, a placeholder the practice confirms (C51). Location option "presence" only.

| Campaign | Ad groups | Geography | Match types |
|---|---|---|---|
| HR Search Hip Replacement | Surgeon (Tier 1); procedure (Tier 2); anterior and outpatient (after confirmation); hip arthritis treatment (Tier 3, Growth); geo-modified | 30-mile radius on TCO Robbinsdale; 10-mile radii on the Maple Grove, Plymouth, and Edina clinics at +25% while on click bidding | Tier 1 phrase plus exact on the ten highest-intent terms; Tier 2 phrase; Tier 3 exact |
| KR Search Knee Replacement | Surgeon; procedure; robotic knee (held, O12); knee arthritis treatment (Tier 3, Growth); geo-modified | As HR | As HR |
| HP Search Hip Preservation | Arthroscopy and labral tear; impingement and FAI; hip preservation surgeon; PAO (after confirmation) | Metro plus a 60-mile ring from Maple Grove; excludes Olmsted County, Duluth, Eau Claire (O11) | Phrase; exact on hip arthroscopy labral tear |
| SM Search Sports Medicine (day 60 or Growth) | ACL; meniscus; rotator cuff; sports and shoulder surgeon near me | As HR | Phrase; exact on surgeon terms |

Smart Bidding ignores location bid adjustments except -100% (D15); after the switch, a separate priority-suburb campaign carries suburb priority if the day 30 geo report shows it needed (D68). Negatives: the starter list in 02_keyword_summary.md plus competitor names. No audiences or remarketing (C4 to C7); call reporting off (C17 to C20).

Microsoft Advertising: Bing holds about 9.9% of US searches, 14% on desktop (D1, D2), with an older audience per agency sources (D3, low reliability); test after day 90 at 10% to 15% of Google spend ($300 to $450 a month at Pilot), once Google is demand-bound (D65).

## 3. Budget tiers

Monthly, from the Tiers tab (D67). Low combines low demand, low CPC, and low rates; high the opposite. Clicks are the lower of budget divided by CPC and the demand cap (searches x query expansion x impression share x CTR); deployed spend is clicks times CPC. The cap binds for every cluster in the low and base cases at every tier, never in the high case.

| Tier | Spend cap | Hip replacement | Knee replacement | Hip preservation | ACL | Meniscus | Rotator cuff |
|---|---|---|---|---|---|---|---|
| Pilot | $3,000 | $1,350 | $1,200 | $450 | $0 | $0 | $0 |
| Growth | $6,000 | $1,920 | $1,800 | $600 | $720 | $360 | $600 |
| Full coverage | $9,000 | $2,700 | $2,700 | $900 | $1,080 | $630 | $990 |

Results, low / base / high:

| Tier | Deployed spend | Clicks | Contacts | Qualified inquiries | Consults booked | Consults attended | Cost per qualified inquiry | Cost per consult attended |
|---|---|---|---|---|---|---|---|---|
| Pilot | $317 / $2,050 / $3,000 | 46.1 / 208.2 / 194.0 | 2.8 / 20.8 / 27.2 | 0.8 / 9.4 / 16.3 | 0.4 / 6.1 / 13.0 | 0.3 / 5.2 / 12.0 | $382 / $219 / $184 | $1,019 / $396 / $250 |
| Growth | $501 / $3,462 / $6,000 | 76.3 / 351.2 / 372.9 | 4.6 / 35.1 / 52.2 | 1.4 / 15.8 / 31.3 | 0.7 / 10.3 / 25.1 | 0.5 / 8.7 / 23.1 | $365 / $219 / $192 | $973 / $396 / $260 |
| Full coverage | $558 / $3,986 / $9,000 | 79.5 / 375.6 / 515.4 | 4.8 / 37.6 / 72.2 | 1.4 / 16.9 / 43.3 | 0.7 / 11.0 / 34.6 | 0.5 / 9.3 / 31.9 | $390 / $236 / $208 | $1,040 / $427 / $282 |

Arithmetic, Pilot base, hip replacement: 1,400 x 1.25 = 1,750 searches; cap 1,750 x 60% x 8% = 84 clicks, below the budget's 135, so it binds; 84 x $10 = $840; contacts 8.4 (10%); qualified 3.78 (45%); booked 2.46 (65%); attended 2.09 (85%); $840 / 3.78 = $222 per qualified inquiry; $840 / 2.09 = $402 per consult. Blended CPC runs $6.57 to $17.46 (B60). At base the modeled market absorbs about $2,000 a month at launch and $4,000 with all six procedures, so Growth and Full deploy only part of their caps; at high every tier spends in full; at low about $320 deploys and consults are rare. Cost per qualified inquiry sits near $180 to $390 and cost per attended consult near $250 to $1,050, before fees.

## 4. Recommended entry budget

$3,000 a month in media (range $2,000 to $4,000), the Pilot tier, plus the fee (D60). It sits above the base-case cap for the launch clusters ($2,050), so demand, not budget, is the first constraint and the day 30 impression share report shows which case is real. At high it deploys fully at about 27 contacts a month, near Google's 30-conversion floor for Target CPA (C14); below $2,000 the high case would be budget-bound. Google bills only what serves: 90-day exposure is at most $9,000, with $950 to $9,000 expected to deploy.

## 5. 90-day pilot and gates

Thresholds are formulas in the Pilot Plan tab (Pilot tier, practice-reported measures).
- Pre-launch (days -28 to 0): practice confirms intake hours, systems (O12), and TCO approval; vendor BAAs; DNI number and form event; landing pages; negatives; campaigns built and paused.
- Week 2, tracking verified: 60-second calls and forms appear in the vendor log and as primary conversions; call reporting off; no PHI in any tag. Fail: pause.
- Day 30: search term review; contacts against 2.8 / 20.8 / 27.2; qualified share of contacts at or above 30% (D57), otherwise tighten terms first; lost to rank dominant means the cap is real, lost to budget above 10% means raise the cap in $500 steps between day 60 and day 90 (D13).
- Day 60: sports medicine starts at $1,680 a month if the launch campaigns are demand-bound and cost per qualified inquiry is at or below $219; Target CPA only at 30 conversions in 30 days (C14, C58).
- Days 60 to 90: scale to Growth ($6,000) if two-month cost per qualified inquiry is at or below $219 and cost per attended consult at or below $396, with lost to budget above 10%; hold at $3,000 between $219 and $382 per qualified inquiry; cut (drop the cap to the best cluster's deployed spend, or pause the weakest campaign) above $382 per qualified inquiry or $1,019 per consult for two consecutive months.

## 6. Fee structure options [KRISTINA TO SET]

Benchmarks (D66): Clutch's 2025 survey puts 62% of small and mid-size businesses at $1,500 to $5,000 a month (D4, medium reliability); Credo finds 51% of PPC providers set a $1,000 to $3,000 retainer minimum (D5, medium, 2022 to 2023 data); WebFX's 350-respondent survey and agency guides give 10% to 20% of spend or $1,000 to $3,000 flat (D6, D7, medium to low); setup fees $500 to $3,000 (D8, low). Per-lead pricing is not recommended: qualified inquiries are practice-reported inside BAA-covered systems (C55, C59). Kristina sets every figure.

| Option | Structure | Benchmark range |
|---|---|---|
| A. Flat retainer | Fixed monthly fee plus one setup fee; simplest, does not rise with spend | $1,000 to $3,000 a month; setup $500 to $3,000 |
| B. Percentage with a floor | 10% to 20% of media with a monthly minimum; scales at Growth and Full | 15% of $3,000 is $450, so a $1,000 to $1,500 floor governs at Pilot |
| C. Hybrid | Base fee plus a lower percentage, plus setup | $750 to $1,500 base plus 10% of media |

## 7. Assumptions that most move the result

1. Demand ceilings (Agent B, low confidence): a 15-minute Keyword Planner export (B64) replaces them.
2. The cap terms: query expansion (D52), impression share (D53), CTR (D54); the day 30 report replaces all three.
3. Contact to qualified rate (D57), 30% to 60%: nothing orthopedic exists; practice-reported after month one.
4. CPC (B60, D64): national-derived; auction data at day 30.
5. Click to contact rate (D56): landing page and intake answer rate (C51).
