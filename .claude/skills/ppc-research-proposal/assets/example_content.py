"""Minimal example of the content module that scripts/docx_builder.py consumes.
Copy this file, replace every value, keep the block shapes. Bracketed text becomes a
yellow-highlighted placeholder in the docx; **bold** lead-ins render bold."""

COVER = {
    "wordmark": "Example Agency",
    "title": "Google Ads program for Example Clinic: proposal",
    "lines": [
        "Prepared for: Jordan Lee, [TITLE], Example Clinic",
        "Prepared by: Sam Rivera | Founder, Example Agency",
        "Date: [SEND DATE] | Valid through: [DATE, 30 days from send]",
    ],
}
FOOTER_TEXT = "Example Agency | Springfield, State | Confidential"
META = {"author": "Sam Rivera", "company": "Example Agency", "created": "2026-01-15"}
SECTIONS = [
    {"title": "1. Opening", "blocks": [
        ("p", "Thank you for the clear request. This proposal answers each item you listed, in your order, with every figure as a range and its basis in one line."),
    ]},
    {"title": "2. At a glance", "blocks": [
        ("table", ["Item", "Summary"], [
            ["Recommended entry budget", "$3,000 a month in media (range $2,000 to $4,000) plus the management fee (section 11)."],
            ["Time to launch", "3 to 4 weeks from signature, dependent on account access, approvals, and tracking."],
        ], [1.8, 4.7]),
    ]},
    {"title": "11. Management and setup fees [SENDER TO SET]", "blocks": [
        ("p", "[Option A, flat retainer. $X,XXX a month plus a one-time setup fee of $X,XXX.]"),
        ("bullets", ["**Term:** 90-day pilot, then month-to-month.", "**Ownership:** the client owns its ad account and data."]),
        ("sig", "Sam Rivera | Founder, Example Agency | [PHONE] | [EMAIL]"),
    ]},
]
APPENDIX = {"title": "Appendix", "blocks": [
    ("h2", "A. Top keywords"),
    ("table", ["#", "Keyword", "Searches a month", "CPC"], [["1", "example surgeon near me", "20 to 60", "$7 to $20"]], [0.4, 3.1, 1.5, 1.5]),
]}
