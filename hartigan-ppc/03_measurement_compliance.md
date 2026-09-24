# 03 Measurement, tracking, and compliance (Agent C)

Run date 2026-09-24. Sources C1 to C49 and assumptions C50 to C60 are in sources_C.md. Not legal advice: each item is a flag for the practice's compliance officer and counsel.

## 1. Funnel and qualified patient inquiry

Funnel: click, contact (call or form), qualified inquiry, consult booked, consult attended, surgery scheduled. The last three are practice-reported, as monthly counts only (C50).

Provisional definition, for the practice to confirm (C50): a new patient, in the service area, asking about a target condition or procedure, with accepted insurance or a payment path; excludes spam, vendors, job seekers, and existing-patient scheduling.

Rubric (under one minute; five yes answers = qualified; record codes only, plus consult booked Y/N):

| Question | If no, code |
|---|---|
| New to Dr. Hartigan? | NQ-existing |
| Can be seen in Edina, Maple Grove, or Plymouth (or wants a hip preservation opinion)? | NQ-area |
| Asking about hip or knee replacement, labral tear, ACL, meniscus, or rotator cuff? | NQ-condition |
| Insurance accepted, or self-pay or MDsave path? | NQ-insurance |
| A real patient, not a vendor, recruiter, or misdial? | NQ-spam |

## 2. Tracking design

Calls first: vendor data puts calls near 58 percent of new-patient contacts (C49, not orthopedic-specific, C52).

- Calls: dynamic number insertion (DNI) from a BAA-signed vendor swaps the landing-page number per paid session, so each call carries the GCLID, campaign, and keyword. Call assets carry a static vendor number dedicated to the campaign, with Google call reporting off, because call reporting routes calls through Google forwarding numbers, logs caller numbers, and lets Google record a sample (C17 to C20), and Google signs no BAA for Google Ads (C8, C9). Trade-off: call-asset calls count in the vendor system, not in Google Ads, unless the privacy officer approves call reporting with recording off (C51).
- Forms: a HIPAA-eligible form tool under BAA (C47) fires a "form submitted" event with no field values; contents go only to the practice's intake inbox or CRM. No Google lead form assets, which send lead details to Google (C55).
- Analytics: Google offers no BAA for Google Analytics and says regulated entities must not expose PHI to it (C9). Default: no identifiable health information in GA4 or Google Ads; if GA4 runs at all, the privacy officer approves a stripped configuration (C60).
- Conversion actions (C13): primary, feeding bidding: "landing-page call of 60 seconds or more" (GCLID-matched) and "form submitted". Secondary, observation only: call button, call-asset, and directions clicks.

| Flows to Google Ads | Stays in HIPAA-covered systems (BAA) | Aggregate only |
|---|---|---|
| Conversion name, GCLID, timestamp, campaign, keyword | Recordings, transcripts, caller names and numbers, form contents, intake notes | Qualified inquiries by code |
| Call duration bucket, no caller number | Vendor call log and call IDs | Consults booked and attended |
| No hashed email or phone (C8, C10) | CRM and scheduling records | Surgeries scheduled |

## 3. Vendor requirements

Search results confirm BAAs from CallRail (Healthcare plan, C42), CallTrackingMetrics (C43), Invoca (C44), and WhatConverts (C45); Marchex's terms say it is not a business associate (C46). Jotform and Formstack offer BAAs, Gravity Forms and Typeform do not (C47); HubSpot only on Enterprise with its Healthcare add-on, Salesforce Health Cloud by default (C48).

Requirements for any category: BAA before the first call or form is routed; recording off by default, or PHI redaction on; role-based access and audit logs; retention per practice policy (assumed 90 days, C53); no integration that sends recordings, transcripts, or caller numbers to any ad platform. Humanus signs a BAA with the practice or is limited to de-identified fields (C55).

## 4. Offline conversion import (off by default)

Value: bidding toward consults instead of contacts. Risk: it links one click to a health-related outcome, and Google's customer data policy bars uploading conversion information related to sensitive categories, including purchases of medical services (C8, C56). Minimum-data design, if approved: GCLID, a neutral conversion name ("Stage 2", never a condition or procedure), and a timestamp (C11), within 90 days of the click (C12). Approval: privacy officer and counsel, in writing. Enhanced conversions need hashed email or phone (C10) and exclude sensitive-category conversions (C8), so they stay off.

## 5. Intake

Targets (C51): answer 80 percent of calls within 20 seconds during ad hours; tracked callback within one business hour or by 10 a.m. the next business day; voicemail states that window; ads run only in staffed hours. Monthly 20-minute de-identified lead-quality review: counts by code, campaign, day, and hour.

## 6. Attribution

Google Ads conversions and practice-reported consults will differ: repeat calls, calls outside the conversion window, logging gaps, one person calling and submitting a form (C57). Steer by practice-reported qualified inquiries and consults, the RFP's measure; Google Ads conversions are the bidding signal only. Reconcile monthly inside the BAA-covered vendor by call ID and timestamp; export counts only, with the explained gap.

## 7. Reporting

Monthly: spend, clicks, CPC, calls, forms, qualified inquiries, consults booked and attended, cost per qualified inquiry, cost per consult, search-term findings, next actions with budget changes in dollars. Cadence: weekly one-line check in month one, monthly report, quarterly review. Quarterly agenda: funnel by cluster, cost per consult versus the proposal range, intake, compliance check (audiences, conversion actions, vendor settings, BAAs), landing pages, next quarter's budget. No PHI (C59).

## 8. Compliance verification

a. In-person surgical services need no Google healthcare certification (C1 to C3); improbable-outcome and cure claims are barred (C24).

b. Health, including invasive procedures, is a sensitive interest category with no advertiser-curated audiences; the May 2025 exception covers only ads to clinicians (C4 to C7).

c. The OCR bulletin lost its "IP address plus unauthenticated health page equals PHI" portion on June 20, 2024, and OCR withdrew its appeal August 29, 2024 (C25, C26, C28). Still in effect: the rest, including BAAs for any tool receiving PHI and no tracking on authenticated or scheduling pages. Nothing newer from OCR was found; tracking remains an enforcement priority (C29), FTC settlements require express consent before health data reaches ad platforms (C31), and class actions continue, including Allina Health in Minnesota (C27, C30).

d. The Consumer Data Privacy Act sits at Minn. Stat. 325M.10 to 325M.21, not chapter 325O (C32): effective July 31, 2025; thresholds of 100,000 consumers, or 25 percent of revenue from data sales with 25,000 consumers; health data needs consent; HIPAA-covered data is exempt, entities are not; attorney general enforcement with no cure period since February 1, 2026 (C32 to C34). HF 2700 died at the May 18, 2026 adjournment (C35). The Health Records Act requires signed, dated consent to release records and is read as stricter than HIPAA (C36).

e. Minn. Stat. 147.091 subd. 1(e) disciplines misleading advertising, unsubstantiated cure claims, and superiority claims (C37); no Board of Medical Practice testimonial rule was found (C38). FTC Endorsement Guides (2023) and the review rule (October 21, 2024) govern testimonials and reviews (C39, C40); HIPAA requires written authorization to use PHI in marketing (C41). So: no "best" claims, no outcome promises, testimonials only with authorization and a signed release.

f. Google restricts trademarks in ad text only after an owner complaint, not as US keywords (C23): device names only for systems Dr. Hartigan uses (C54), the group name only with written approval (C53), no competitor names in ad text.

g. Consent signals apply only to EEA, UK, and Swiss traffic (C22); restricted data processing is counsel's call (C21).

h. Target CPA needs about 30 conversions in 30 days to evaluate (C14 to C16): Maximize conversions at launch, Target CPA after two months at 30 or more primary conversions (C58).

| Flag | What it affects | Default we hold | Owner | Status as verified (date) | Source ID |
|---|---|---|---|---|---|
| Healthcare policy | Ad approval | No certification; no outcome or cure claims | Google, Humanus | 2026-09-24, search summary | C1 to C3, C24 |
| Personalized ads, health | Audiences | No remarketing, Customer Match, or health audiences | Google, Humanus | 2026-09-24 | C4 to C7 |
| OCR bulletin, FTC, class actions | Tags, pixels, analytics | No PHI to Google; BAA for any PHI recipient | Compliance, counsel | Part vacated 2024-06-20; nothing newer found; recheck | C25 to C31 |
| Minnesota: 325M, 144.293, HF 2700 | Consent, notices, records | Health data needs consent; signed consent before release | Counsel, compliance | In force; HF 2700 failed 2026-05-18 | C32 to C36 |
| 147.091, FTC endorsements | Copy, testimonials | No superiority claims; authorization plus release | Counsel, practice | 2026-09-24 | C37 to C41 |
| Trademarks | Keywords, ad text | Device names only if used; group name with approval | Humanus, practice | 2026-09-24 | C23, C53, C54 |
| Consent, RDP | Tag setup | No US consent mode; RDP per counsel | Counsel | 2026-09-24 | C21, C22 |
| Google call recording | Call assets | Call reporting off; vendor static number | Humanus, compliance | 2026-09-24 | C17 to C20 |
| GA4 BAA | Analytics | No PHI in GA4; privacy officer decides use | Compliance | 2026-09-24 | C9, C60 |
| Offline import, enhanced conversions | Bidding | Off until privacy officer and counsel approve | Compliance, counsel | 2026-09-24 | C8, C10 to C12, C56 |
| Vendor BAAs | Calls, forms, CRM | BAA before go-live; Humanus BAA with practice | Compliance, Humanus | 2026-09-24 | C42 to C48, C55 |
| Bidding thresholds | Strategy by phase | Maximize conversions, then Target CPA at 30 per month | Humanus | 2026-09-24 | C14 to C16, C58 |
