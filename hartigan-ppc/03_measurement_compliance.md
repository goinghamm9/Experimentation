# 03 Measurement, tracking, and compliance (Agent C)

Run date: 2026-09-24. Sources C1 to C49 and assumptions C50 and up are in sources_C.md. Nothing here is legal advice; each item is a flag for the practice's compliance officer and counsel.

## 1. Funnel and qualified patient inquiry

Funnel: click, contact (call or form), qualified inquiry, consult booked, consult attended, surgery scheduled. The last three are practice-reported, as monthly counts only (C50).

Provisional definition, for the practice to confirm (C50): a new patient, in the service area, asking about one of the six target procedures or their conditions, with accepted insurance or a self-pay path. Excludes spam, vendors, job seekers, and existing-patient scheduling.

Rubric (under one minute; five yes answers = qualified; record codes, never reasons in words):

| Question | If no, code |
|---|---|
| New to Dr. Hartigan? | NQ-existing |
| Can be seen in Edina, Maple Grove, or Plymouth, or wants a hip preservation opinion from farther away? | NQ-area |
| Asking about hip or knee replacement, labral tear or impingement, ACL, meniscus, or rotator cuff? | NQ-condition |
| Insurance accepted, or self-pay or MDsave path? | NQ-insurance |
| A real patient, not a vendor, recruiter, or misdial? | NQ-spam |

Plus one field: consult booked (Y/N).

## 2. Tracking design

Calls come first: healthcare-wide data puts calls near 58 percent of new-patient contacts, with about 40 percent converting on the call (C49, vendor data, not orthopedic-specific, C52).

- Landing-page calls: dynamic number insertion (DNI) from a BAA-signed vendor swaps the displayed number per paid session, tying each call to the click ID (GCLID), campaign, and keyword. The number inside a call asset cannot be swapped, so it carries a static vendor number dedicated to the campaign, with Google call reporting off. Reason: call reporting routes calls through Google forwarding numbers, logs caller numbers on calls over 15 seconds, and Google's terms allow it to monitor and record a sample (C17, C20); Google's call recording is off by default for healthcare but can be enabled (C18, C19); Google signs no BAA for Google Ads (C8, C9). Trade-off: call-asset calls are counted by the vendor, not as Google Ads conversions, unless the privacy officer approves call reporting with recording off (C51).
- Forms: a HIPAA-eligible form tool under BAA (C47). Submission fires a "form submitted" event with no field values; contents go only to the practice's intake inbox or CRM under BAA. No Google lead form assets, which deliver lead details to Google (C8, C55).
- Analytics: Google makes no HIPAA representations for Google Analytics, offers no BAA, and says regulated entities must not expose PHI to it (C9). Default: no identifiable health information in GA4 or Google Ads. If GA4 runs on the landing page, form-interaction measurement and Google signals are off and no form values appear in URLs; the privacy officer decides (C60).
- Conversion actions (C13): primary, feeding bidding: "landing-page call of 60 seconds or more" (vendor, GCLID-matched) and "form submitted". Secondary, observation only: call button click, call-asset click, directions click. "Qualified inquiry" is a later option (section 4).

| Flows to Google Ads | Stays in HIPAA-covered systems (BAA) | Aggregate only |
|---|---|---|
| Conversion name, GCLID, timestamp, campaign, keyword | Recordings, transcripts, caller names and numbers, form contents, intake notes | Qualified inquiries by code |
| Call duration bucket, no caller number | Vendor call log and call IDs | Consults booked and attended |
| No hashed email or phone (C8, C10) | CRM and scheduling records | Surgeries scheduled |

## 3. Vendor requirements

Verified from search results on 2026-09-24: CallRail signs a BAA on its Healthcare plan (C42); CallTrackingMetrics offers a BAA (C43); Invoca states BAA support (C44); WhatConverts offers a BAA with a profile-level HIPAA setting (C45); Marchex's recording terms say it is not a business associate (C46). Jotform and Formstack offer BAAs on specific plans; Gravity Forms and Typeform do not offer a standard one (C47). HubSpot signs a BAA only on Enterprise with its Healthcare add-on; Salesforce Health Cloud includes one (C48).

Requirements for any category: BAA signed before routing a call or form; recording off by default, or PHI redaction on; role-based access and audit logs; retention per practice policy (assumed 90 days, C53); no integration sending recordings, transcripts, or caller numbers to any ad platform. Humanus will see the vendor dashboard, so Humanus signs a BAA with the practice or is limited to de-identified fields (C55).

## 4. Offline conversion import (off by default)

Value: importing "qualified inquiry" or "consult booked" lets bidding optimize toward consults instead of contacts. Risk: it links one click to a health-related outcome, and Google's customer data policy bars uploading conversion information related to sensitive categories, which include purchases of medical services (C8, C56). Minimum-data design, if approved: GCLID, a neutral conversion name ("Stage 2", never a condition or procedure), and a timestamp (C11), uploaded within 90 days of the click (C12). Approval: privacy officer and counsel, in writing. Enhanced conversions need hashed email or phone (C10) and exclude sensitive-category conversions (C8), so they stay off.

## 5. Intake

Targets (C51): 80 percent of calls answered within 20 seconds during ad hours; missed calls get a tracked callback within one business hour, or by 10 a.m. the next business day; voicemail states that window; ads run only in staffed hours. Monthly 20-minute de-identified lead-quality review: counts by code, campaign, day, and hour. No names, no recordings.

## 6. Attribution

Google Ads conversions and practice-reported consults will differ: repeat calls from one patient, calls outside the conversion window, front-desk logging gaps, one person calling and submitting a form, and calls with no click match (C57). Steer by practice-reported qualified inquiries and consults, the RFP's stated measure; use Google Ads conversions only as the bidding signal. Reconcile monthly inside the BAA-covered vendor by call ID and timestamp, then export counts only: contacts, Google Ads conversions, qualified, consults, and the explained gap.

## 7. Reporting

Monthly: spend, clicks, CPC, calls, forms, qualified inquiries, consults booked and attended, cost per qualified inquiry, cost per consult, search-term findings, next actions with budget changes in dollars. Cadence: one-line weekly check in month one, monthly report, quarterly review. Quarterly agenda: funnel by procedure cluster, cost per consult against the proposal range, intake performance, compliance check (audiences, conversion actions, vendor settings, BAAs), landing-page changes, next quarter's budget. No PHI in any report (C59).

## 8. Compliance verification

a. Google certifications cover pharmacies, prescription drug services, telemedicine, addiction services, health insurance, and drug makers; in-person surgical services need none (C1, C2). The July 2026 update (effective October 29) only loosens non-promotional drug terms (C3). Improbable-outcome and cure claims are barred, and Google defers to local rules on testimonials (C24).

b. Health, including invasive procedures, is a sensitive interest category; advertiser-curated audiences are not allowed for it; the May 2025 exception covers only ads to licensed clinicians (C4 to C7).

c. The OCR bulletin (December 1, 2022; revised March 18, 2024) lost its "IP address plus unauthenticated health page equals PHI" portion on June 20, 2024; OCR withdrew its appeal August 29, 2024 (C25 to C28). Still in effect: the rest, including BAAs for any tool receiving PHI and no tracking on authenticated or scheduling pages; OCR still names tracking a priority, and no newer guidance was found (C29). FTC settlements require express consent before health data goes to ad platforms (C31); class actions continue, including Allina Health in Minnesota (C30).

d. The Minnesota Consumer Data Privacy Act sits at Minn. Stat. 325M.10 to 325M.21, not chapter 325O (C32). Effective July 31, 2025; thresholds of 100,000 consumers or 25 percent revenue from data sales with 25,000 consumers; health data is sensitive and needs consent; data under HIPAA is exempt, entities are not; attorney general enforcement, no cure period since February 1, 2026, up to 7,500 dollars per violation, no private action (C32 to C34). HF 2700 (health data, geofencing) did not pass before the May 18, 2026 adjournment (C35). The Health Records Act (144.291 to 144.298) requires signed, dated consent to release records and is read as stricter than HIPAA (C36).

e. Minn. Stat. 147.091 subd. 1(e) disciplines false or misleading advertising, unsubstantiated cure claims, and superiority claims (C37); no Board of Medical Practice testimonial rule was found, only the chiropractic board's (C38). FTC Endorsement Guides (July 26, 2023) and the review rule (October 21, 2024, penalties to 51,744 dollars per violation) govern testimonials and reviews (C39, C40); HIPAA requires written authorization to use PHI in marketing (C41). Meaning: no "best" claims, no outcome promises, testimonials only with authorization and release.

f. Google does not restrict trademarks as US keywords but may restrict ad text after an owner complaint (C23). Device names only for systems Dr. Hartigan uses and after checking maker terms (C54); the group name only with written approval (C53); competitor names never in ad text.

g. Consent signals are required only for EEA, UK, and Swiss traffic (C22); restricted data processing for US state laws is a counsel choice (C21). No US healthcare certification applies here (C1, C2).

h. Google recommends judging Target CPA over 30 days with at least 30 conversions (C14); Smart Bidding relies on minimum conversion history (C15, C16). Plan: Maximize conversions at launch, Target CPA after two months at 30 or more primary conversions (C58).

| Flag | What it affects | Default we hold | Owner | Status as verified (date) | Source ID |
|---|---|---|---|---|---|
| Healthcare policy | Ad approval | No certification; no outcome or cure claims | Google policy, Humanus | Verified 2026-09-24, search summary | C1 to C3, C24 |
| Personalized ads, health | Audiences | No remarketing, Customer Match, or health audiences | Google policy, Humanus | Verified 2026-09-24 | C4 to C7 |
| OCR tracking bulletin | Tags, analytics | No PHI to Google; BAA for any PHI recipient | Practice compliance, counsel | Part vacated 2024-06-20; appeal withdrawn; nothing newer found; recheck | C25 to C29 |
| FTC and class actions | Pixels, disclosures | No health data to ad platforms | Counsel | Verified 2026-09-24 | C30, C31 |
| MCDPA and HF 2700 | Consent, notices | Treat as applicable; health data needs consent | Counsel | In force; HF 2700 failed 2026-05-18 | C32 to C35 |
| Health Records Act | Record disclosure | Signed consent before any release | Practice compliance | Verified 2026-09-24 | C36 |
| 147.091, FTC endorsements | Copy, testimonials | No superiority claims; authorization plus release | Counsel, practice | Verified 2026-09-24 | C37 to C41 |
| Trademarks | Keywords, ad text | Device names only if used; group name with approval | Humanus, practice | Verified 2026-09-24 | C23, C53, C54 |
| Consent, RDP | Tag setup | No US consent mode; RDP per counsel | Counsel | Verified 2026-09-24 | C21, C22 |
| Google call recording | Call assets | Call reporting off; vendor static number | Humanus, practice compliance | Verified 2026-09-24 | C17 to C20 |
| GA4 BAA | Analytics | No PHI in GA4; privacy officer decides use | Practice compliance | Verified 2026-09-24 | C9, C60 |
| Offline import, enhanced conversions | Bidding | Off until privacy officer and counsel approve | Practice compliance, counsel | Verified 2026-09-24 | C8, C10 to C12, C56 |
| Vendor BAAs | Calls, forms, CRM | BAA before go-live; Humanus BAA with practice | Practice compliance, Humanus | Verified 2026-09-24 | C42 to C48, C55 |
| Bidding thresholds | Strategy by phase | Maximize conversions, then Target CPA at 30 per month | Humanus | Verified 2026-09-24 | C14 to C16, C58 |
