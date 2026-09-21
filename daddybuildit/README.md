# daddybuildit.shop — hand-off briefs

Documents written for the Claude Code session that works inside the daddybuildit.shop repository. Give the session one file at a time.

| Order | Brief | What it delivers |
|---|---|---|
| 1 | **[CICD-BRIEF.md](./CICD-BRIEF.md)** | Delivery pipeline and environments: GitHub guardrails, a staging site, PR previews, staging → approval → production deploys with automatic rollback, tests, cutover plan, runbook. Everything else ships through this. |
| 2 | **[MOBILE-RESPONSIVE-BRIEF.md](./MOBILE-RESPONSIVE-BRIEF.md)** | Mobile responsiveness remediation: device-matrix audit, mobile-first CSS foundations, navigation sheet and sticky-bar patterns, template-by-template fixes, touch and keyboard behaviour, mobile performance, and automated overflow, tap-target, zoom, image, and snapshot tests in CI. Can run on its own; fastest customer-visible win after the pipeline. |
| 3 | **[DESIGN-COMMERCE-BRIEF.md](./DESIGN-COMMERCE-BRIEF.md)** | Design system derived from Apple's Human Interface Guidelines (tokens, typography, components, motion, imagery, voice) and shopping-experience standards drawn from Shopify, the Apple Store, Amazon, Etsy, and Baymard research (PDP, bag, checkout hand-off, commercial mechanics, performance, SEO, structured data, analytics, legal). |

Each brief opens with operating rules for the session and a list of what only the human can provide. All three are stack-agnostic: discovery comes first, then the work adapts to what the repository actually contains. The mobile brief uses the design system's tokens when they exist and a minimal token set when they do not, so the order of 2 and 3 can be swapped.
