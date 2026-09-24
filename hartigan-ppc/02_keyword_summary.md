# 02 Keyword and demand summary (Agent B)

Run date 2026-09-24. Companion files: 02_keywords.csv (109 rows), sources_B.md (sources B1 to B26, assumptions B50 to B65). Searches in the CSV are monthly, for the Minneapolis-St. Paul metro, which contains the priority suburbs (B50). Suburb-only and Minnesota-only views below are derived with B51 to B53. Every volume is a labeled estimate; no live Keyword Planner data exists in this run.

## Clusters and their role

| Cluster | RFP procedure | Role at launch |
|---|---|---|
| hip_replacement | computer-navigated total hip replacement | Launch. Highest case value, clear surgeon-seeking demand, includes the hip and knee arthritis Tier 3 seeds. |
| knee_replacement | robotic-assisted total knee replacement | Launch. Largest cluster; robotic terms carry a technology story patients already search for (B10). |
| hip_preservation | hip arthroscopy for labral tears, impingement, hip preservation | Launch small, Minnesota-wide. The surgeon's subspecialty differentiator; too thin at metro level for its own budget line (see flag). |
| acl | ACL reconstruction | Phase 1 as part of one combined sports medicine campaign. |
| meniscus | meniscus repair | Same combined sports campaign; almost no surgeon-seeking volume on its own. |
| rotator_cuff | rotator cuff repair | Same combined sports campaign; "shoulder surgeon near me" carries most of the intent. |

## Demand ceilings (monthly Tier 1 plus Tier 2 searches, computed from the CSV)

| Cluster | Tier 1 and 2 rows | Suburbs low | Suburbs high | Metro low | Metro high | Minnesota low | Minnesota high |
|---|---|---|---|---|---|---|---|
| hip_replacement | 20 | 77 | 480 | 800 | 2500 | n/a | n/a |
| knee_replacement | 21 | 90 | 580 | 1000 | 3300 | n/a | n/a |
| hip_preservation | 17 | 16 | 99 | 120 | 430 | 180 | 590 |
| acl | 9 | 24 | 170 | 350 | 1100 | n/a | n/a |
| meniscus | 9 | 13 | 100 | 250 | 800 | n/a | n/a |
| rotator_cuff | 9 | 20 | 140 | 270 | 880 | n/a | n/a |
| all six clusters | 85 | 240 | 1600 | 2800 | 9100 | n/a | n/a |

Tier detail (metro, low to high): hip_replacement Tier 1 120 to 460, Tier 2 680 to 2,100, Tier 3 220 to 690; knee_replacement Tier 1 150 to 560, Tier 2 900 to 2,700, Tier 3 380 to 1,200; hip_preservation Tier 1 21 to 92, Tier 2 99 to 340, Tier 3 380 to 1,200; acl Tier 1 99 to 340, Tier 2 250 to 800; meniscus Tier 1 5 to 23, Tier 2 240 to 780; rotator_cuff Tier 1 33 to 120, Tier 2 240 to 750.

Flags. Hip preservation Tier 1 plus Tier 2 is 120 to 430 searches per month in the metro and 180 to 590 statewide: enough for a small Minnesota-wide campaign, not enough to spend more than a few hundred dollars a month against. Meniscus (Tier 1 of 5 to 23) and rotator cuff (33 to 120) cannot justify separate campaigns at an entry budget; combine acl, meniscus and rotator_cuff into one sports medicine campaign with procedure-level ad groups. The priority suburbs alone (240 to 1,600 across all clusters) are too thin to run as the only geography; use the metro with location bid adjustments up for the three suburbs. Spend cannot usefully exceed available demand: at the metro Tier 1 plus Tier 2 ceiling of 2,800 to 9,100 searches, a plausible 5% to 10% click share means roughly 140 to 910 clicks per month across all clusters.

## Top 25 keywords (priority 1, Tier 1 and 2, ranked by metro searches high)

| # | Keyword | Cluster | Tier | Searches low | Searches high | CPC low | CPC high | Source |
|---|---|---|---|---|---|---|---|---|
| 1 | ACL surgery | acl | 2 | 160 | 490 | 5 | 12 | B14;B59;B60 |
| 2 | rotator cuff surgery | rotator_cuff | 2 | 160 | 490 | 5 | 12 | B13;B59;B60 |
| 3 | meniscus surgery | meniscus | 2 | 88 | 280 | 5 | 12 | B59;B60 |
| 4 | knee replacement surgery | knee_replacement | 2 | 99 | 240 | 6 | 15 | B8;B9;B54;B60 |
| 5 | hip replacement surgery | hip_replacement | 2 | 76 | 180 | 6 | 15 | B8;B54;B60 |
| 6 | hip arthroscopy | hip_preservation | 2 | 55 | 170 | 5 | 12 | B59;B60 |
| 7 | rotator cuff repair | rotator_cuff | 2 | 55 | 170 | 5 | 12 | B59;B60 |
| 8 | ACL reconstruction | acl | 2 | 44 | 140 | 5 | 12 | B59;B60 |
| 9 | meniscus repair | meniscus | 2 | 33 | 110 | 4 | 11 | B59;B60 |
| 10 | robotic knee replacement | knee_replacement | 2 | 33 | 110 | 6 | 16 | B10;B56;B60 |
| 11 | torn meniscus surgery | meniscus | 2 | 33 | 110 | 5 | 12 | B59;B60 |
| 12 | knee replacement near me | knee_replacement | 2 | 28 | 98 | 7 | 18 | B7;B57;B60 |
| 13 | knee replacement surgeon | knee_replacement | 1 | 25 | 87 | 7 | 20 | B8;B9;B56;B57;B60 |
| 14 | hip replacement near me | hip_replacement | 2 | 22 | 84 | 7 | 18 | B7;B57;B60 |
| 15 | knee replacement surgeon near me | knee_replacement | 1 | 22 | 84 | 8 | 22 | B7;B57;B60 |
| 16 | knee surgeon near me | knee_replacement | 1 | 22 | 77 | 8 | 22 | B7;B57;B60 |
| 17 | shoulder surgeon near me | rotator_cuff | 1 | 22 | 70 | 7 | 18 | B7;B57;B60 |
| 18 | hip replacement surgeon | hip_replacement | 1 | 20 | 67 | 7 | 20 | B8;B56;B57;B60 |
| 19 | hip replacement surgeon near me | hip_replacement | 1 | 16 | 63 | 8 | 22 | B7;B57;B60 |
| 20 | hip replacement surgeon Minneapolis | hip_replacement | 1 | 10 | 60 | 7 | 18 | B58;B60 |
| 21 | knee replacement surgeon Minneapolis | knee_replacement | 1 | 10 | 60 | 7 | 18 | B58;B60 |
| 22 | hip labral tear surgery | hip_preservation | 2 | 16 | 56 | 5 | 13 | B59;B60 |
| 23 | hip surgeon near me | hip_replacement | 1 | 16 | 56 | 8 | 22 | B7;B57;B60 |
| 24 | best knee replacement surgeon | knee_replacement | 1 | 11 | 42 | 7 | 20 | B57;B60 |
| 25 | best hip replacement surgeon | hip_replacement | 1 | 9 | 35 | 7 | 20 | B57;B60 |

CPCs are dollars per click, modeled from national category averages of $4.76 to $5.00 for physicians and surgeons (B1, B2) and $5.64 for healthcare (B3) with the uplift in B60. They are not Twin Cities figures.

## Match type recommendations

- Tier 1 (surgeon-seeking): phrase match, plus exact match on the ten highest-intent terms (the surgeon, doctor and near-me rows for hip and knee replacement). No broad match at launch; consider broad match only after 30 or more qualified inquiries exist for Smart Bidding to learn from.
- Tier 2 (procedure and technology): phrase match; exact match added for the RFP technology terms (robotic knee replacement, computer navigated hip replacement, hip arthroscopy labral tear) so budget and messaging can be tracked per procedure.
- Tier 3 (condition research): exact match only, in a separate ad group with its own daily cap, launched in phase 2 for arthritis treatment terms and held as tests for cost, recovery and bare condition terms.
- Geo-modified terms: phrase match; expect Google to report low volume, keep them for message match.

## Starter negative keyword list

jobs, job, careers, hiring, salary, pay, resume, residency, fellowship, program, school, training, course, CE, CME, lecture, CPT, ICD, code, coding, billing, reimbursement, RVU, veterinary, vet, dog, cat, canine, feline, equine, horse, lawsuit, recall, attorney, lawyer, settlement, class action, malpractice, exercises, stretches, physical therapy, PT protocol, rehab protocol, video, youtube, pictures, images, reddit, forum, free, cheap, DIY, brace, pillow, ice machine, walker, Mexico, India, abroad, medical tourism, nurse, technician, sales rep, device company, Stryker careers, Zimmer careers, Wikipedia, definition, anatomy, statistics, market size. Add competitor practice and hospital names as negatives at launch so non-brand budget stays non-brand (Agent A's competitor list).

## Judgment calls

- Cost and price: keep, as a Tier 3 test with its own ad group and a page that addresses cost plainly. Cost searchers are often candidates comparing options (B26 lists financing as a distinct patient need). Exclude only if the practice will not discuss pricing.
- Insurance and Medicare: keep. "Does insurance cover hip replacement" signals a candidate; negative only "insurance jobs" and "claims adjuster".
- Recovery, after surgery, post op, rehab: negative in Tier 1 and Tier 2 ad groups (mostly existing patients, per B13's finding that recovery is the top post-procedure topic); one capped informational test later if the practice wants it.
- Second opinion and revision: keep second opinion (high intent). Park revision terms until Agent A confirms the surgeon performs revisions.
- Injections, PRP, stem cell: negative unless the clinic offers them; they pull non-surgical intent into surgeon ad groups.
- Anterior, Mako, partial knee, PAO: run only after the practice confirms the surgeon offers each (unverified), so the ads never promise a procedure he does not perform.
- Generic "orthopedic surgeon near me" (third-party 90,500 nationally, B7) is left out of the file: it draws spine, hand and fracture intent and would dominate spend; test later with heavy negatives if Tier 1 volume proves thin.

## Data confidence

What is benchmark: the CPC, CTR, conversion rate and cost per lead figures behind B60 come from published national multi-account reports (WordStream 2026 and 2025 physicians and surgeons, LocalIQ healthcare 2024 to 2025 campaigns); they are national, not Twin Cities, and none is orthopedics-specific. What is third-party: three keyword volumes reached without a login ("orthopedic near me" 135,000 and "orthopedic surgeon" 90,500 as of June 2024, B7; "hip replacement surgery" 9,900, undated, B8) plus a knee-to-hip interest ratio from a Google Trends study (B9); these anchor two rows at medium confidence. What is modeled: the other 107 rows (low confidence), every local multiplier (B51 to B53), every ratio (B56 to B59) and every CPC uplift (B60). Google Trends by metro was blocked and not used (B23). A 15-minute Keyword Planner export, with Plymouth, Maple Grove, Edina, the Minneapolis-St. Paul DMA and Minnesota as separate locations and top-of-page bid low and high, would replace every modeled volume and CPC with observed 12-month averages, turn the ceilings into real counts, and let the budget model drop its widest ranges. The relative ordering of clusters and tiers is more trustworthy than any single number.
