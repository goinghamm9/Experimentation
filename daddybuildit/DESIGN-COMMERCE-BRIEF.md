# daddybuildit.shop — Design System & Commerce Experience Brief

**Audience:** the Claude Code session working inside the `daddybuildit.shop` repository.
**Goal:** bring the storefront up to two standards at once. The **frontend** should meet the bar set by Apple's Human Interface Guidelines and Apple Design Resources: clarity, restraint, hierarchy, precise typography and spacing, fluid motion, full dark-mode and accessibility support. The **commercial mechanics and shopping experience** should match what the best e-commerce platforms and stores do by default: Shopify's checkout conventions, the Apple Store's product configuration flow, Amazon's delivery and trust clarity, Etsy's maker transparency, and the Baymard Institute's usability research.

Companion document: `CICD-BRIEF.md` in this folder. That pipeline is the delivery mechanism for everything below. If it is not in place yet, build it first; every change in this brief ships as a pull request with a preview URL, automated checks, staging verification, and an approved production deploy.

---

## 0. How to use this brief

### 0.1 Operating rules for the Claude session

1. **Audit before redesign.** Phase 1 produces `docs/UX-AUDIT.md` with a scored baseline. Nothing visual changes until the human has confirmed the audit and the priorities.
2. **Principles, not imitation.** Adopt Apple's design principles and system thinking. Do not clone apple.com layouts, use Apple imagery, product names, San Francisco font files, SF Symbols, or anything that could read as Apple branding. Apple's fonts and symbols are licensed for Apple-platform development only; Section 2.4 gives the compliant choices.
3. **Never build a custom checkout.** Payment, tax, and order capture stay on a hosted, PCI-compliant checkout (Shopify, Stripe, Snipcart, Square). The storefront owns everything up to the hand-off and everything after the confirmation.
4. **Design tokens are the only source of visual values.** No hard-coded colors, sizes, radii, shadows, or durations in components. If a value is not a token, add the token first.
5. **Mobile first, keyboard always, dark mode always.** Every component is designed at 375 px wide before desktop, operable with keyboard and screen reader, and specified in both color schemes.
6. **Measure.** Record Core Web Vitals, Lighthouse, axe, and conversion-funnel baselines before the first visual PR. Every phase ends by re-measuring.
7. **Small PRs with previews.** One page type or one component family per PR. The PR description links the preview URL, lists the checklist items it satisfies (Sections 2–5 numbering), and includes before/after screenshots at 375 px and 1280 px in light and dark.
8. **Honesty in commerce UI.** No fake scarcity, fake timers, pre-ticked upsells, hidden costs, or dark patterns of any kind. Real stock, real lead times, real prices, all costs shown before checkout.
9. **Ask before anything outward-facing or irreversible:** changing the commerce platform, publishing new policy text, changing prices, enabling analytics/consent tooling, sending emails to customers.
10. **Report at the end of each phase**: what shipped, before/after scores, what needs the human (assets, copy, decisions), what you learned.

### 0.2 What the human must provide (ask for all of it up front)

| # | Item | Why | Notes |
|---|------|-----|-------|
| 1 | Brand assets: logo as SVG (mono and full color), existing brand colors, any fonts they own | Token foundation | If none exist, Phase 2 proposes them |
| 2 | Product catalog: every product with name, description, price, variants/options, materials, dimensions, weight, lead time, stock policy, care instructions | PLP/PDP content model | A spreadsheet is fine; you will normalise it |
| 3 | Photography: current source files at full resolution, and whether a reshoot is possible | Imagery standard in Section 2.6 | Send them the shot list in Appendix C |
| 4 | Commerce platform in use (or none), admin access in **test mode**, payment methods enabled | Section 4 decision | Live credentials never leave production |
| 5 | Shipping rules (regions, carriers, rates, free-shipping threshold), tax handling, returns/exchange policy, made-to-order terms | Cart, PDP, policy pages | Written in plain language, you will edit |
| 6 | Business identity: legal name, address, contact email/phone, social links, founder/maker story, years active, anything certifying quality | Trust signals | |
| 7 | Target customers, best sellers, typical order value, geography of buyers | Prioritisation, consent/tax scope | |
| 8 | Three stores they admire and why; three they dislike and why | Calibrates taste | |
| 9 | Analytics account (GA4 or Plausible/Umami), email/newsletter tool, review platform if any | Section 5 | |
| 10 | Constraints: budget for paid tooling, timeline, anything that must not change | Scope | |

### 0.3 Non-goals

- Replatforming for its own sake; a platform change happens only if Section 4.1 shows the current one cannot meet the checkout checklist.
- Custom account systems, loyalty programs, marketplaces, or native apps.
- Copying Apple's trade dress. The target is Apple-grade craft, applied to this maker's own brand.

---

## 1. Phase 1 — Audit and baseline

**Outcome:** `docs/UX-AUDIT.md` with a scored baseline against every checklist in this brief, a prioritised backlog, and measured performance/accessibility numbers.

### 1.1 Inventory

- Every route/page, its template, and its purpose. Screenshot each at 375 px and 1280 px, light and dark (Playwright `page.screenshot({ fullPage: true })` against staging).
- The commerce integration: how products are defined, how the cart works, where checkout happens, which payment methods appear, what the confirmation and emails look like. Complete one **test-mode** purchase end to end and record every screen.
- Content: all copy, policies, image assets (dimensions, formats, weights), structured data present, meta tags, sitemap, robots.
- Third-party scripts and their weight.

### 1.2 Measurements (record in the audit, repeat every phase)

| Metric | Tool | Baseline target after this brief |
|---|---|---|
| LCP / INP / CLS (mobile, 75th percentile) | Lighthouse CI mobile preset + CrUX if available | ≤ 2.5 s / ≤ 200 ms / ≤ 0.1 |
| Lighthouse Performance / Accessibility / Best Practices / SEO (mobile) | `@lhci/cli` | ≥ 90 / 100 / 100 / 100 on home, PLP, PDP |
| axe violations (serious + critical) | `@axe-core/playwright` | 0 on every template |
| Page weight: HTML / CSS / JS / images / fonts on PDP | Lighthouse or WebPageTest | ≤ 50 KB / ≤ 60 KB / ≤ 100 KB (excl. payment SDK) / ≤ 600 KB / ≤ 120 KB |
| Funnel: view_item → add_to_cart → begin_checkout → purchase | analytics | baseline recorded; improvement tracked per phase |
| Time to complete a test purchase on a phone | manual, stopwatch | ≤ 90 s from PDP to confirmation with a wallet |

### 1.3 Heuristic audit

Score every checklist item in Sections 2–5 as `0 missing`, `1 partial`, `2 meets`, `3 exemplary`, with a one-line note and a screenshot reference. Add a benchmark column with how the reference store does it. Benchmarks to open side by side:

- Apple Store (apple.com/shop): product configuration, sticky summary, bag drawer, restraint.
- A store on Shopify's Dawn theme (themes.shopify.com/themes/dawn): baseline conventions for PLP, PDP, cart drawer; Shopify checkout for the hand-off.
- Amazon: delivery promise, availability, reviews structure, trust signals.
- Etsy shop pages: processing times, personalisation fields, maker story, policies.
- Two direct competitors selling similar handmade or custom-built goods.

### 1.4 Backlog and priorities

Rank gaps by (conversion impact × reach) ÷ effort. Anything on the checkout hand-off, PDP buy box, cart, or mobile performance goes first. Present the top 20 to the human with the phase each lands in. Get explicit agreement before Phase 2.

### 1.5 Phase 1 exit criteria

- [ ] `docs/UX-AUDIT.md` merged with scores, screenshots, measurements, and backlog.
- [ ] Human confirmed priorities and provided items 1–10 from Section 0.2 (or dates for the missing ones).
- [ ] Test-mode purchase path documented end to end.

---
## 2. Phase 2 — The design system (Apple HIG principles, applied to this brand)

**Outcome:** a documented, token-driven design system in the repo (`docs/DESIGN-SYSTEM.md`, `src/styles/tokens.css`, a component library) that every page is rebuilt on in later phases. Nothing customer-facing changes in this phase except where a token swap is invisible.

### 2.1 Principles (how to decide when the checklists are silent)

Apple's Human Interface Guidelines reduce to a handful of ideas. Apply them to a store:

| Principle | What it means here |
|---|---|
| **Clarity** | Text is legible at every size, icons are precise, ornament is absent. The product is the hero; the interface recedes. If an element does not help someone understand or buy, remove it. |
| **Deference** | Chrome never competes with product photography. Neutral surfaces, one accent color used only for actions and links, no gradients or textures on UI. |
| **Depth** | Hierarchy through layering and motion, not borders and boxes: a translucent navigation bar, sheets that slide over content, subtle elevation for raised surfaces. |
| **Consistency** | Same component, same behaviour, everywhere. Same spacing scale, same radii, same motion curves. Users learn the interface once. |
| **Direct manipulation and feedback** | Every tap responds within 100 ms. Quantity steppers, swatches, and galleries react immediately, and state is always visible (selected, loading, added, unavailable). |
| **Restraint** | Fewer type sizes, fewer weights, fewer colors, fewer words. Generous whitespace is the primary layout tool. |
| **Accessibility as a default** | Dynamic sizing, contrast, focus, reduced motion, VoiceOver and keyboard paths are part of the definition of each component, not a later pass. |
| **Honesty** | Real inventory, real lead times, real prices, real reviews. The interface never manipulates. |

### 2.2 Tokens (`src/styles/tokens.css`)

Tokens are the only place visual values live. Use `light-dark()` so each color is declared once for both schemes; older browsers get the light values through the `@supports` fallback. A manual theme toggle only sets `color-scheme` on the root.

```css
/* tokens.css — the single source of visual truth. Components reference tokens, never raw values. */
:root {
  color-scheme: light dark;

  /* Typography (Section 2.3). Inter is self-hosted; the stack falls back to the platform UI font. */
  --font-sans: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --text-caption: 0.75rem;    /* 12 */
  --text-footnote: 0.875rem;  /* 14 */
  --text-callout: 0.9375rem;  /* 15 */
  --text-body: 1.0625rem;     /* 17 */
  --text-headline: 1.3125rem; /* 21 */
  --text-title3: 1.5rem;      /* 24 */
  --text-title2: 1.75rem;     /* 28 */
  --text-title1: 2rem;        /* 32 */
  --text-large-title: clamp(2rem, 1.2rem + 3vw, 3rem);        /* 32 → 48 */
  --text-display: clamp(2.5rem, 1.5rem + 4.5vw, 3.5rem);      /* 40 → 56 */
  --leading-tight: 1.08;
  --leading-snug: 1.2;
  --leading-body: 1.47;
  --tracking-display: -0.015em;
  --tracking-title: -0.008em;
  --tracking-body: -0.02em;
  --tracking-caps: 0.06em;
  --weight-regular: 400;
  --weight-semibold: 600;

  /* Spacing: 4 px base, 8 px rhythm. Sections use 12+; components use 1–8. */
  --space-1: 0.25rem;  --space-2: 0.5rem;  --space-3: 0.75rem; --space-4: 1rem;
  --space-5: 1.25rem;  --space-6: 1.5rem;  --space-8: 2rem;    --space-10: 2.5rem;
  --space-12: 3rem;    --space-16: 4rem;   --space-20: 5rem;   --space-24: 6rem;  --space-32: 8rem;

  /* Radii. Nested radius = outer radius − padding. */
  --radius-xs: 6px; --radius-sm: 10px; --radius-md: 14px; --radius-lg: 20px; --radius-xl: 28px; --radius-pill: 980px;

  /* Layout */
  --content-narrow: 40rem;      /* long-form text */
  --content-default: 61.25rem;  /* 980: most sections */
  --content-wide: 90rem;        /* 1440: product grids, full-bleed media */
  --gutter: clamp(1rem, 4vw, 2rem);
  --nav-height: 3rem;
  --target-min: 44px;

  /* Motion. Enter = ease-out, exit = ease-in, move = standard. No bounce on commerce UI. */
  --duration-fast: 150ms; --duration-base: 250ms; --duration-slow: 400ms; --duration-sheet: 500ms;
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-out: cubic-bezier(0.25, 0.1, 0.25, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);

  /* Elevation: two working levels plus modal. Prefer hairlines and background shifts over shadows. */
  --shadow-raised: 0 4px 20px rgba(0, 0, 0, 0.08);
  --shadow-overlay: 0 11px 34px rgba(0, 0, 0, 0.16);
  --z-nav: 100; --z-drawer: 200; --z-modal: 300; --z-toast: 400;

  /* Color — light values first as the fallback for browsers without light-dark(). */
  --color-bg: #ffffff;
  --color-bg-secondary: #f5f5f7;
  --color-surface: #ffffff;
  --color-surface-raised: #ffffff;
  --color-text: #1d1d1f;
  --color-text-secondary: #6e6e73;
  --color-text-tertiary: #86868b;
  --color-separator: rgba(0, 0, 0, 0.12);
  --color-separator-strong: #d2d2d7;
  --color-fill: rgba(120, 120, 128, 0.12);
  --color-fill-strong: rgba(120, 120, 128, 0.2);
  --color-accent: #0071e3;        /* filled buttons: 4.5:1 with white text */
  --color-accent-hover: #0077ed;
  --color-on-accent: #ffffff;
  --color-link: #0066cc;          /* text links: 5.7:1 on white */
  --color-success: #248a3d;       /* Apple's increased-contrast green; #34c759 fails AA for text */
  --color-warning: #c93400;
  --color-danger: #d70015;
  --color-focus: #0071e3;
  --color-scrim: rgba(0, 0, 0, 0.4);
  --material-nav: rgba(255, 255, 255, 0.72);
}

@supports (color: light-dark(#000, #fff)) {
  :root {
    --color-bg: light-dark(#ffffff, #000000);
    --color-bg-secondary: light-dark(#f5f5f7, #1d1d1f);
    --color-surface: light-dark(#ffffff, #1d1d1f);
    --color-surface-raised: light-dark(#ffffff, #2c2c2e);
    --color-text: light-dark(#1d1d1f, #f5f5f7);
    --color-text-secondary: light-dark(#6e6e73, #a1a1a6);
    --color-text-tertiary: light-dark(#86868b, #86868b);
    --color-separator: light-dark(rgba(0, 0, 0, 0.12), rgba(255, 255, 255, 0.16));
    --color-separator-strong: light-dark(#d2d2d7, #424245);
    --color-fill: light-dark(rgba(120, 120, 128, 0.12), rgba(120, 120, 128, 0.24));
    --color-fill-strong: light-dark(rgba(120, 120, 128, 0.2), rgba(120, 120, 128, 0.36));
    --color-accent: light-dark(#0071e3, #0071e3);
    --color-accent-hover: light-dark(#0077ed, #0a84ff);
    --color-link: light-dark(#0066cc, #2997ff);
    --color-success: light-dark(#248a3d, #30d158);
    --color-warning: light-dark(#c93400, #ff9f0a);
    --color-danger: light-dark(#d70015, #ff453a);
    --color-focus: light-dark(#0071e3, #2997ff);
    --color-scrim: light-dark(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.6));
    --material-nav: light-dark(rgba(255, 255, 255, 0.72), rgba(29, 29, 31, 0.72));
  }
}

/* Manual override from a theme switch; otherwise the OS decides. */
:root[data-theme="light"] { color-scheme: light; }
:root[data-theme="dark"]  { color-scheme: dark; }

/* Accessibility preferences are honoured at the token level so every component inherits them. */
@media (prefers-reduced-motion: reduce) {
  :root { --duration-fast: 0ms; --duration-base: 0ms; --duration-slow: 0ms; --duration-sheet: 0ms; }
}
@media (prefers-reduced-transparency: reduce) {
  :root { --material-nav: var(--color-bg); }
}
@media (prefers-contrast: more) {
  :root { --color-text-secondary: var(--color-text); --color-separator: var(--color-separator-strong); }
}
```

Brand color: if the maker has a brand color, it replaces `--color-accent`/`--color-link` **only if** it passes 4.5:1 against white (light) and against `#000`/`#1d1d1f` (dark). Otherwise the brand color lives in the logo and photography, and the accent stays neutral blue. Use the WebAIM contrast checker and record the ratios in `docs/DESIGN-SYSTEM.md`.

### 2.3 Typography

Sizes, line heights and tracking follow Apple's public web type ramp; weights are limited to regular and semibold.

| Role | Size / line height | Weight | Tracking | Use |
|---|---|---|---|---|
| Display | 40→56 px / 1.07 | 600 | −0.015em | home hero only |
| Large title | 32→48 px / 1.08 | 600 | −0.012em | page titles |
| Title 1 | 32 px / 1.125 | 600 | −0.008em | section headings |
| Title 2 | 28 px / 1.14 | 600 | −0.007em | sub-sections, PDP product name (desktop) |
| Title 3 | 24 px / 1.17 | 600 | −0.005em | card titles, PDP product name (mobile) |
| Headline | 21 px / 1.19 | 600 | 0.011em | prices on PDP, drawer titles |
| Body | 17 px / 1.47 | 400 | −0.02em | paragraphs, buttons, inputs, nav |
| Callout | 15 px / 1.4 | 400 | −0.01em | secondary descriptions |
| Footnote | 14 px / 1.43 | 400 | −0.016em | captions, helper text, legal |
| Caption | 12 px / 1.33 | 400 | −0.01em | badges, labels; smallest permitted |

Rules:

- Sentence case everywhere, including buttons and navigation. All-caps only for 12 px badges with `--tracking-caps`.
- Body text measure 45–75 characters (`max-width: var(--content-narrow)` on prose).
- Prices and quantities use `font-variant-numeric: tabular-nums`.
- Headings use `text-wrap: balance`; body uses `text-wrap: pretty` where supported.
- No more than five type sizes and two weights on a single page. Hierarchy comes from size and spacing, not from color or extra weights.
- Root font size stays at the browser default (respect user zoom); everything is in `rem`.

### 2.4 Fonts and icons: what is allowed

- **San Francisco (SF Pro, SF Compact, SF Mono) and SF Symbols are licensed by Apple for designing and developing software for Apple platforms only.** Do not self-host SF font files or ship SF Symbol artwork on the site.
- Two compliant choices; pick one in Phase 2 and record the decision:
  1. **System font stack** (`system-ui, -apple-system, …`): zero bytes, native feel, renders SF on Apple devices legitimately, Segoe UI on Windows, Roboto on Android. Typography differs slightly per platform.
  2. **Inter Variable, self-hosted** (SIL Open Font License): consistent on every platform, metrics close to SF. Subset to Latin, one variable `woff2` (~100 KB), `font-display: swap`, a `size-adjust`-tuned fallback (`@font-face` for "Inter Fallback" over Arial) so the swap causes no layout shift, preloaded on every page.
  Default recommendation: **Inter**. Consistency is a large part of the "Apple" feel, and 100 KB preloaded is inside the performance budget.
- **Icons:** Lucide (ISC licence): 24 px grid, 1.5–2 px stroke matching the semibold text weight, currentColor, inline SVG with `aria-hidden="true"` and a visible or `sr-only` label. No icon fonts, no mixed icon families.

### 2.5 Color usage

- One accent, used only for primary actions, links, and selected states. Everything else is neutral.
- Semantic colors appear only for status (success, warning, danger) and always with an icon or text, never alone.
- Photography supplies the color. Surfaces are white or `--color-bg-secondary`; in dark mode, product images sit on `--color-surface` cards, and photography with pure-white studio backgrounds is re-plated (Section 2.6) so it does not glare.
- Contrast: AA minimum for all text (4.5:1, 3:1 for ≥ 24 px regular or ≥ 19 px semibold) and for UI component boundaries (3:1). Note that iOS system blue `#007AFF` fails AA for normal text on white; the web accent is `#0071e3`/`#0066cc` for that reason.
- Test every token pair in `docs/DESIGN-SYSTEM.md` with recorded ratios in both schemes.

---
### 2.6 Layout, depth, motion, imagery, and voice

**Layout and spacing**

- 8 px rhythm for layout, 4 px for micro-spacing inside components. Section padding on desktop `--space-24` to `--space-32`, on mobile `--space-12` to `--space-16`.
- Breakpoints: 375 (design first here), 744, 1024, 1440. Content widths from the tokens; product grids may go to `--content-wide`, text never beyond `--content-narrow`.
- 12-column grid at ≥ 1024 px with 24 px gutters; 4 columns at 375 px with 16 px gutters. Product grid: 2 columns on phones, 3 at 744, 4 at 1024+.
- Safe areas: `padding-inline: max(var(--gutter), env(safe-area-inset-left))`, sticky bars add `env(safe-area-inset-bottom)`.
- Everything aligns to the grid; icons are optically centred with their labels, not mathematically.
- Sticky elements: navigation bar (48 px, translucent), mobile add-to-bag bar on PDP, drawer footers. Never more than two sticky regions at once.

**Depth and materials**

- Navigation bar: `background: var(--material-nav); backdrop-filter: saturate(180%) blur(20px);` with a hairline `--color-separator` bottom border. Falls back to a solid `--color-bg` under `prefers-reduced-transparency` and where `backdrop-filter` is unsupported.
- Cards are flat on `--color-bg-secondary` sections, or hairline-bordered on white. Shadows only for raised interactive surfaces (`--shadow-raised`) and overlays (`--shadow-overlay`).
- Radius nesting: an image inside a card with `--radius-lg` and `--space-4` padding gets `calc(var(--radius-lg) - var(--space-4))`.
- Hairlines are 1 px at low alpha, never 2 px borders.

**Motion**

- Purposes: feedback (button press, add to bag), continuity (drawer slides from the side it lives on; gallery images move with the finger), orientation (sheet enters from the bottom on phones). Decoration is not a purpose.
- Durations: micro 150 ms, standard 250 ms, large surfaces 400–500 ms. Enter with `--ease-out`, exit with `--ease-in`, move with `--ease-standard`. No bounce or overshoot on commerce UI.
- Animate only `transform` and `opacity`. Never animate layout properties. Never autoplay carousels or video with sound. No parallax on shopping pages.
- Every transition reads its duration from a token, so `prefers-reduced-motion` collapses all of it to instant changes (already wired in `tokens.css`). Crossfades may remain at 100 ms where an instant change would be disorienting (e.g. gallery image swap).
- Press feedback: `transform: scale(0.98)` for 150 ms on buttons and cards; hover raises a card by 2 px on pointer devices only (`@media (hover: hover)`).

**Imagery** (the full shot list is Appendix C)

- Consistent studio setup per product family: neutral background (`#f5f5f7` or white), single soft key light, true-to-life color, no heavy vignettes or filters. Lifestyle shots show the product in use at real scale.
- Per product minimum: 1 hero on neutral, 2 details/macros (joinery, finish, hardware), 1 scale reference (with a hand, a room, or a common object), 1 lifestyle, 1 dimensions diagram. Variants each get their own hero.
- Aspect ratios: product cards and PDP gallery 4:5; hero banners 16:9 desktop and 4:5 mobile (art-directed with `<picture>`); lifestyle 3:2. Never crop the product at the frame edge on cards.
- Pipeline: master TIFF/PNG → AVIF and WebP with JPEG fallback → widths 480, 768, 1024, 1440, 2048 → `srcset`/`sizes` on every image → explicit `width`/`height` attributes → `loading="lazy"` below the fold, `fetchpriority="high"` and a `<link rel="preload">` for the LCP image. Budget: hero ≤ 200 KB, product image ≤ 120 KB at the largest displayed width.
- Alt text describes the product and what the image shows ("Walnut floating shelf, 36 inch, mounted above a desk"), never "image of".
- No text baked into images. No stock photography of people who are not the maker or real customers.

**Voice and microcopy**

- Short sentences. Concrete nouns and numbers ("Ships in 5–7 business days", not "Fast shipping!"). Benefit before feature. Sentence case. No exclamation marks, no jargon, no fake urgency.
- Buttons name the action and its object: "Add to bag", "Check out", "Save changes". Never "Submit", "Click here", "OK".
- Errors say what happened and what to do: "We couldn't find that postcode. Check the number or enter your city." Never "Invalid input".
- Empty states are one line plus one action: "Your bag is empty." → "Continue shopping".
- Prices are always formatted by `Intl.NumberFormat` with the store currency; never hand-formatted.
- A `docs/VOICE.md` page holds the glossary (the product names, the word "bag" vs "cart" chosen once, the maker's name and how it is written), and the words to avoid.

### 2.7 Component library

Build these as the only building blocks for Phases 3–5. Each one has a written spec (template below), light and dark screenshots at 375 px and 1280 px, keyboard behaviour, and an axe check.

| Component | Key spec |
|---|---|
| **Button** | Sizes 44 px (default) and 36 px (compact); pill radius; primary = filled accent, secondary = `--color-fill` with `--color-text`, tertiary = text link. Loading state keeps width and shows a spinner; disabled uses 40 % opacity and `aria-disabled`. Focus ring: 2 px `--color-focus` with 2 px offset. |
| **Text input / select / textarea** | 44 px tall, `--radius-sm`, hairline border, label above (never placeholder-as-label), helper and error text below with an icon, `autocomplete`/`inputmode` attributes, inline validation on blur, error summary at the top of long forms. |
| **Stepper (quantity)** | 44 px targets, `−`/`+` buttons plus an editable number input, min/max enforced with a message, announces changes via `aria-live="polite"`. |
| **Segmented control / option pills** | Variant selection: text options as pills, colors and materials as 44 px swatches with a visible name; unavailable options are shown struck-through and remain focusable with "unavailable" announced; selected state uses a 2 px accent ring, not color alone. |
| **Product card** | 4:5 image, name (Title 3 on desktop, Body semibold on mobile), price with compare-at, up to 4 variant swatches, badge slot (New, Sold out, Made to order), whole card is one link with the name as the accessible label; hover shows the second image on pointer devices. |
| **Price** | Tabular numerals; compare-at price in `<s>` with `sr-only` "was"; unit price optional; "from" prefix for ranged variants. |
| **Badge** | 12 px caps, `--radius-xs`, neutral fill; semantic color only for Sold out/Low stock. |
| **Navigation bar** | 48 px, material background, logo left, primary links centre (desktop) or a full-screen sheet (mobile), search and bag right; bag shows a count with `aria-label="Bag, 3 items"`. |
| **Drawer / sheet** | Bag and filters. Slides from the right on desktop, from the bottom on phones; scrim; focus trapped; `Esc` and scrim close; scroll locked behind; returns focus to the trigger. Uses the native `<dialog>` element. |
| **Modal dialog** | Rare: size guide, image zoom. Same rules as drawer; max width 40 rem. |
| **Toast** | "Added to bag" with a "View bag" action, 4 s, `role="status"`, bottom-centre on phones, top-right on desktop. |
| **Accordion** | Native `<details>/<summary>` styled with a chevron; used for PDP details, shipping, care. |
| **Gallery** | Mobile: horizontal scroll-snap with page dots and swipe; desktop: thumbnails plus a large image; tap/click opens zoom in a dialog; arrow keys navigate; every image has alt text. |
| **Skeleton** | Neutral shimmer respecting reduced motion; matches the final layout exactly to prevent shift. |
| **Empty and error states** | One line plus one action; no illustrations that compete with products. |
| **Table (specs)** | Two columns, hairline row separators, no zebra striping, `<th scope="row">`. |
| **Footer** | Policies, contact, social, newsletter (single field), payment method icons, copyright; sorted by what customers look for: shipping, returns, contact. |

Component spec template (`docs/components/<name>.md`):

```markdown
# <Component>
**Purpose:** …
**Anatomy:** … (numbered parts)
**Variants / sizes:** …
**States:** default · hover (pointer only) · focus-visible · active · disabled · loading · error · selected
**Tokens used:** …
**Behaviour:** pointer · keyboard (keys and focus order) · screen reader (roles, names, announcements) · touch (targets, gestures)
**Motion:** … (token durations and easings)
**Responsive:** 375 · 744 · 1024 · 1440
**Content rules:** …
**Do / Don't:** …
**Tests:** unit (if logic) · Playwright interaction · axe · visual snapshot light + dark
```

### 2.8 Design review checklist (run on every PR that touches UI)

- [ ] Only tokens: `grep -rnE '#[0-9a-fA-F]{3,8}|[0-9]+px' src/components` returns nothing outside `tokens.css` and documented exceptions (1 px hairlines, 44 px targets).
- [ ] Spacing is a multiple of 4; section rhythm a multiple of 8; content within the token widths.
- [ ] Type: ≤ 5 sizes, ≤ 2 weights on the page; sentence case; balanced headings; measure within limits.
- [ ] One primary action per view; secondary actions visibly quieter.
- [ ] Contrast AA in both schemes; focus visible; 44 px targets for primary controls, 24 px minimum for everything.
- [ ] Dark mode parity screenshot attached. Reduced-motion and reduced-transparency checked.
- [ ] Images: right aspect ratio, `srcset`, dimensions set, alt text, no layout shift (CLS 0 in Lighthouse).
- [ ] Motion ≤ 500 ms, transform/opacity only, tokens for durations and easings.
- [ ] Loading, empty, and error states implemented, not just the happy path.
- [ ] Works at 320 px, at 200 % browser zoom, and with keyboard only.
- [ ] Copy follows `docs/VOICE.md`. No exclamation marks, no "click here", no urgency theatre.
- [ ] Nothing reads as a generic UI kit: no default browser blues, no heavy borders, no gradient buttons, no drop shadows on text.

### 2.9 Phase 2 exit criteria

- [ ] `tokens.css`, font and icon decision, and `docs/DESIGN-SYSTEM.md` merged (tokens, type ramp, contrast table, layout, motion, imagery, voice).
- [ ] Component library implemented with specs, stories or a `/design-system` preview route on staging (noindex), Playwright interaction tests, axe passing, visual snapshots in light and dark.
- [ ] Human has reviewed the preview route and approved the look before any page is rebuilt.

---
## 3. Phase 3 — Shopping experience standards, page by page

**Outcome:** every template rebuilt on the design system to the standards below. Order of work: PDP buy box and cart first (money), then PLP, then home and content, then search and secondary pages. Each item is scored in the audit; **Must** items are required for the Definition of Done, **Should** items are expected unless the human waives them in writing.

### 3.1 Global

Must:
- Navigation bar with logo → home, primary categories (≤ 5), search (if catalog > 20 items), bag with live count. Mobile menu is a full-screen sheet with the same links plus contact and policies.
- Announcement bar (optional, one line, dismissible, remembers dismissal) for real information only: free-shipping threshold, holiday cut-offs, made-to-order lead times.
- Footer: shipping, returns, contact, about, privacy, terms, payment icons, newsletter, social. Contact shows a real email and a response-time promise.
- Skip link, landmark regions, one `<h1>` per page, logical heading order, focus management on route changes.
- Currency and country visible if the store ships internationally.
- 404 page suggests categories and search; server returns a real 404 status.

Should:
- Persistent bag across sessions (platform cart or `localStorage` with expiry).
- Back-to-top only on long pages; never floating chat widgets by default.

### 3.2 Home

Must:
- Above the fold on a phone: what is sold, for whom, why it is special, one primary action ("Shop shelves"), one hero image that is a real product. LCP element is that image, preloaded.
- Featured products or categories within the first two screens, using the product card.
- Trust strip: shipping promise, returns window, made-by-hand/made-to-order statement, secure checkout. Four items maximum, plain icons.
- Maker story teaser with a real photo and a link to About.
- Social proof: real reviews with names/initials and dates, or a review platform embed that meets the performance budget.
- Newsletter capture: single email field, clear value ("New pieces and workshop notes, once a month"), no pop-ups on first visit, no exit-intent modals.

Should:
- "How it's made" or process section: this is the differentiator for a maker brand.
- Instagram/social gallery only if it loads lazily and within budget.

### 3.3 Collection / product listing (PLP)

Must:
- Title, one-line description, product count. Breadcrumbs on subcategories.
- Product cards per Section 2.7 with price, variants, availability badges; images never cropped through the product.
- Sort (featured, price low→high, high→low, newest) and, for catalogs > 12 items, filters (category, price, material, size, availability) in a bottom sheet on mobile with an applied-filters summary and a result count that updates without a full reload. Filter state lives in the URL so links are shareable and back button works.
- Pagination or "Load more" that keeps scroll position and is crawlable (real links). Never infinite scroll without a footer escape.
- Empty results state with a clear action.

Should:
- Quick add for single-variant products; variant picker in a small sheet for multi-variant.
- "Made to order · ships in 2–3 weeks" style availability line on cards where relevant, because it changes the buying decision (Etsy's processing-time pattern).

### 3.4 Product detail page (PDP): the page that makes the money

Layout (desktop): gallery left (≈ 60 %), buy box right in a sticky column; below: details accordion, specs table, reviews, related products. Mobile: gallery → name/price → options → sticky add-to-bag bar → details.

Must:
- Gallery per Section 2.7: hero on neutral, details, scale, lifestyle, dimensions; zoom; swipe; alt text; variant selection switches to that variant's images.
- Product name (H1), price with compare-at, unit or "from" logic; rating summary linking to reviews.
- Options: segmented pills / swatches with visible names, unavailable states, and a live price + availability update on selection (Apple Store configurator behaviour). Nothing is selected by default when the choice matters (size); a default is fine for color if it is the hero image's variant.
- Personalisation/customisation fields (engraving, dimensions, wood species) with character limits, live preview text, and price impact shown next to the field.
- Availability and delivery promise directly under the price: "In stock · order by 2 pm for dispatch today" or "Made to order · ready in 2–3 weeks · ships free". This is Amazon's single most effective element.
- Shipping cost and returns summary within one glance of the add-to-bag button ("Free shipping over $75 · 30-day returns"), each linking to policy.
- Add-to-bag: 44 px primary button; on tap: button shows a check + "Added" for 1.5 s, bag count animates, a toast or the bag drawer opens (choose one behaviour store-wide). Express wallet button (Apple Pay / Shop Pay / Google Pay / PayPal) directly below if the platform supports it on PDP.
- Sticky add-to-bag bar on mobile once the primary button scrolls out of view, showing thumbnail, price, and button.
- Details in accordions: description, dimensions and materials (as a specs table), care, shipping and returns, made-to-order terms. Dimensions include a diagram image.
- Reviews: summary distribution, sortable list, verified-purchase marker, photos when available, honest handling of zero reviews ("Be the first to review" without pressure).
- Related products (same category or "completes the set"), 4 max, using product cards.
- Structured data: `Product` + `Offer` (price, currency, availability, `shippingDetails`, `hasMerchantReturnPolicy`), `AggregateRating`/`Review` when present, `BreadcrumbList`. Validate with Google's Rich Results Test.
- Performance: LCP is the hero image; the payment SDK loads after interaction or on idle; INP ≤ 200 ms when switching variants.

Should:
- "Ask a question" link to a contact form pre-filled with the product name.
- Back-in-stock / notify-me for sold-out variants (platform feature or a form).
- Compare or "which size is right" helper for product families.
- Recently viewed (local only, no account).

Never:
- Countdown timers, "12 people are viewing", fake low-stock warnings, forced newsletter modals, auto-added add-ons.

### 3.5 Bag (cart)

Must:
- Bag drawer (Section 2.7) for confirmation and quick edits, plus a full `/bag` page that works without JavaScript for the platform's cart.
- Line items: image, name, selected options and personalisation text, unit price, quantity stepper, line total, remove (with undo toast for 5 s). Editing options happens by removing and re-adding from PDP unless the platform supports inline change.
- Subtotal, then an honest note on what is not yet included ("Shipping and taxes calculated at checkout") or, better, a shipping estimate by country/postcode.
- Free-shipping threshold progress ("Add $18 more for free shipping") when a threshold exists.
- Primary "Check out" button 44 px, full width on mobile, sticky in the drawer footer; express wallet buttons beside or above it.
- Promo code field collapsed behind "Have a code?" to avoid sending people off to hunt for coupons. Applied codes show the discount on their own line with a remove action.
- Trust line under the button: secure checkout, accepted payment icons, returns window.
- Empty bag state with featured products.
- Bag persists across reloads and, if the platform supports it, across devices when logged in.

Should:
- Gift message / gift wrap as an honest optional line item.
- Cross-sell of one complementary item, never pre-added.

### 3.6 Checkout hand-off (hosted checkout)

The checkout is the platform's. Your job is to make the hand-off seamless and to configure the platform to the following standard, which is Shopify checkout's default behaviour and matches Baymard's research on why people abandon (in their 2024 data the top reasons were extra costs discovered late at roughly 48 %, forced account creation at roughly 26 %, distrust of the site with card details at roughly 25 %, slow delivery at roughly 23 %, and a long or complicated checkout at roughly 22 %).

Must (configure or verify on the platform):
- Guest checkout is the default; account creation is offered after purchase, never required.
- Express wallets at the top: Apple Pay, Google Pay, Shop Pay or Link, PayPal as available.
- Single page or clearly stepped flow with a persistent order summary, editable bag, and totals that update as address and shipping change.
- Address autocomplete; postcode-first where supported; only required fields; `autocomplete` attributes; inline validation; specific error messages; phone explained ("for delivery questions only").
- Shipping methods show price and an estimated delivery date range, not just a carrier name.
- All costs visible before the payment step; no surprise fees.
- Branding: logo, accent color, typography as close to the store as the platform allows; the transition from bag to checkout should not feel like leaving the site.
- Policies (shipping, returns, privacy, terms) linked in the checkout footer.
- Payment errors handled inline with a clear retry; declined cards do not lose the entered data.
- Confirmation page: order number, what happens next, delivery estimate, contact, and a "Continue shopping" link back to the store. A matching confirmation email arrives within a minute.

Verify by completing test-mode purchases with a card, a wallet, a discount code, and a personalised item, on a phone and on desktop, and screenshot every step into `docs/UX-AUDIT.md`.

### 3.7 Post-purchase and transactional email

Must:
- Emails: order confirmation, shipping confirmation with tracking, delivery follow-up with a review request 7–14 days after delivery. Brand-consistent, plain-language, mobile-first, from a monitored address.
- Order status page or tracking link that works without an account.
- Made-to-order items get a "we've started making yours" update if lead time exceeds one week.

Should:
- Post-purchase account creation with one tap (platform feature).
- Packaging insert that points to care instructions and the review page (offline, but part of the experience).

### 3.8 Content, trust and policy pages

Must:
- About: the maker, the workshop, the process, real photos, years active, where things are made.
- Shipping: regions, costs, thresholds, processing times, carriers, holiday cut-offs. Returns: window, condition, who pays return shipping, made-to-order/personalised exceptions stated plainly. Privacy and terms current and readable. Contact: form + email + expected response time; physical address if required by law.
- FAQ answering the questions that show up in email, with `FAQPage` structured data.
- Reviews page or section if the platform aggregates them.
- Accessibility statement with a contact route for barriers.

### 3.9 Search (only if catalog > 20 items)

Must: prominent field in the nav, predictive results after 2 characters showing product cards with prices, keyboard navigable, "no results" with suggestions, results page with the PLP controls, synonyms for common misspellings.

### 3.10 Errors, offline, and edge cases

Must: friendly 404/500 pages within the design system; form failures never lose input; slow networks show skeletons, not blank screens; JavaScript failure still allows browsing and reaching the platform cart; out-of-stock variants and discontinued products keep their URL with a clear message and alternatives.

---
## 4. Commercial mechanics

**Outcome:** the store's platform, data model, pricing, shipping, payments, and fulfilment rules are chosen deliberately and configured to the standard of the major platforms, with the storefront reading from one source of truth.

### 4.1 Platform decision

Rule: the fewest custom moving parts that satisfy every **Must** in Section 3.6. Re-platform only if the current provider cannot. Decide in Phase 1 and record it in `docs/UX-AUDIT.md`.

| Option | Best for | Fees (verify current pricing) | Strengths | Costs and limits |
|---|---|---|---|---|
| **Keep the current provider** | It already supports hosted checkout, wallets, tax, shipping rules, inventory, order emails, test mode | as is | no migration | any Must it cannot meet ends the discussion |
| **Shopify Starter or Basic + Storefront API on the static site** (or the Buy Button for minimal code) | small-to-medium catalog wanting Shop Pay, Apple/Google Pay, tax, labels, abandoned-bag email, reviews apps | Starter: low monthly fee plus a higher per-transaction rate; Basic: higher monthly, standard card rates | the reference checkout; admin the human can run alone; ecosystem for reviews, email, shipping | monthly fee; Storefront API needs a small client-side cart layer (public token is safe: read and cart-only) |
| **Snipcart** | pure static site, developer-maintained, catalog defined in HTML/JSON | percentage per transaction with a monthly minimum, plus gateway fees | simplest static integration; customisable cart; Netlify-friendly | checkout less polished than Shop Pay; fewer merchant tools |
| **Stripe Checkout via a Netlify Function, or Payment Links** | ≤ 10 products with few variants; developer comfortable owning logic | standard card rates; Stripe Tax add-on | excellent checkout, Apple/Google Pay, Link; cheap | you own inventory, shipping rates, tax nexus decisions, order emails; Payment Links do not handle variants or stock well |
| **Square Online / Etsy embeds** | already selling in person on Square or on Etsy | platform-dependent | inventory sync with existing channels | limited design control; Etsy embeds send buyers off-site |

Default recommendation for a maker brand on a static Netlify site with more than a handful of products: **Shopify + Storefront API**, storefront rendered by the site, cart created with `cartCreate`, checkout by redirect to `checkoutUrl`. Second choice: **Snipcart** when simplicity beats Shop Pay. Stripe Payment Links only for a tiny, variant-free catalog.

### 4.2 Catalog data model (one source of truth: the platform admin)

The site never hard-codes prices or stock. It reads the platform at build time (static pages) and refreshes price/availability at runtime for the buy box. Model every product with:

| Field | Notes |
|---|---|
| `title`, `handle` (URL slug), `description` (rich text), `category`, `tags` | handles never change once published; redirects if they must |
| `options[]` (e.g. Size, Finish) and `variants[]` with `sku`, `price`, `compareAtPrice`, `weight`, `dimensions`, `images[]`, `inventoryQuantity`, `inventoryPolicy` (stop selling at 0, or continue as made-to-order) | every variant has its own hero image |
| `leadTimeDays` min/max, `shipsFrom`, `shippingClass` (parcel, oversize, freight, pickup-only) | drives the delivery promise on PDP and bag |
| `personalisation[]`: label, type (text, number, choice), `maxLength`, `required`, `priceDelta`, `helpText` | captured as line-item properties and shown in bag, checkout, and emails |
| `materials`, `care`, `warranty`, `madeIn` | feed the specs table and accordions |
| `seoTitle`, `seoDescription`, `ogImage` | fall back to title/description/hero |
| `reviews` | via the platform or a review app; never hand-entered |

### 4.3 Pricing and promotions

- Prices are formatted by `Intl.NumberFormat`; tax-inclusive or exclusive display follows the market (inclusive for EU/UK/AU, exclusive for US) and says which.
- `compareAtPrice` only for a genuine previous selling price. Reference-price rules (US FTC guides, UK CMA guidance) apply; never invent a "was" price.
- Prefer automatic discounts (threshold, bundle) over codes; codes exist for partners and recovery emails. The bag shows every discount as its own line.
- Free-shipping threshold roughly 1.2–1.3× the average order value; show progress in the bag.
- Gift cards through the platform only.
- No sale theatre: no permanent "sale", no strike-through on every item, no urgency timers.

### 4.4 Shipping, delivery promise, and tax

- Rates by zone and shipping class; oversize and freight items (furniture) get their own class, a clear "curbside delivery, 1–3 week transit" explanation, and a phone number capture for the carrier.
- Delivery promise = handling/lead time + transit, shown as a date range on PDP, bag, and checkout, and recalculated by destination where the platform supports it.
- Local pickup as a shipping method if the workshop allows it.
- International: show duties/taxes responsibility plainly (DDP or DDU) or restrict shipping regions honestly.
- Taxes are calculated by the platform (Shopify Tax, Stripe Tax). Nexus and registration decisions go to the human's accountant; flag them, do not decide them.

### 4.5 Payments

- Cards, Apple Pay, Google Pay, and one of Shop Pay / Link, plus PayPal if the audience expects it. Buy-now-pay-later (Affirm, Klarna, Afterpay) only if average order value is high enough for it to matter, shown on PDP as "or 4 payments of …" with the provider's compliant messaging.
- Apple Pay on the web requires domain verification per provider (Shopify handles it; Stripe needs the `/.well-known/apple-developer-merchantid-domain-association` file served by Netlify for **each** domain, staging included).
- 3-D Secure, fraud screening, and PCI scope stay with the provider. The storefront never touches card data.
- Test mode in every non-production environment (see `CICD-BRIEF.md` env matrix); production smoke tests never start a checkout.

### 4.6 Inventory and made-to-order

- Availability states with exact copy: **In stock** ("Order by 2 pm for dispatch today"), **Low stock** (real threshold ≤ 3, "Only 2 left"), **Made to order** ("Ready in 2–3 weeks"), **Pre-order** (with a date), **Sold out** ("Notify me").
- Made-to-order capacity is real inventory: set weekly capacity as quantity so the lead time stays honest when orders spike; extend the lead time in the admin rather than overselling.
- Status emails for anything beyond one week: started, finished, shipped.

### 4.7 Customer service mechanics

- Contact response promise (e.g. one business day) stated on the contact page and in emails; a monitored inbox.
- Order changes and cancellations: a stated window (e.g. 24 h, or until making starts for personalised items).
- Damage in transit: a simple process (photos within 48 h, replacement or refund) written down and linked from the shipping policy.
- Warranty or guarantee on craftsmanship, in plain words.

---

## 5. Performance, SEO, structured data, analytics, and legal

### 5.1 Performance (budgets enforced in CI)

| Item | Standard |
|---|---|
| Core Web Vitals | LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at the 75th percentile on mobile, measured in the field (CrUX/Search Console) and in Lighthouse mobile |
| Rendering | static HTML for every page; buy-box data hydrated after first paint; no client-side routing required to browse |
| CSS | ≤ 60 KB total; critical CSS inline ≤ 14 KB; no utility framework unless purged below budget; tokens + components only |
| JavaScript | ≤ 100 KB on PDP excluding the payment SDK; SDK loaded on interaction or idle; no jQuery-era libraries; no carousel libraries (scroll-snap) |
| Images | Section 2.6 pipeline; LCP image preloaded with `fetchpriority="high"`; every image has dimensions |
| Fonts | ≤ 120 KB; preloaded; `font-display: swap` with metric-matched fallback |
| Third parties | ≤ 2 by default (payments, analytics); each justified in `docs/PERFORMANCE.md`; reviews/chat widgets only if lazy and within budget |
| Caching | hashed assets immutable for a year; HTML short cache; Netlify image CDN or build-time processing |
| Prefetch | PDP links prefetched on hover/viewport from PLP (respecting Save-Data) |
| Monitoring | `web-vitals` library sending LCP/INP/CLS to analytics; monthly review |

Lighthouse CI budgets (`budget.json`, referenced from `lighthouserc.json` via `assert.budgetsFile`):

```json
[
  {
    "path": "/*",
    "resourceSizes": [
      { "resourceType": "document", "budget": 50 },
      { "resourceType": "stylesheet", "budget": 60 },
      { "resourceType": "script", "budget": 150 },
      { "resourceType": "image", "budget": 600 },
      { "resourceType": "font", "budget": 120 },
      { "resourceType": "third-party", "budget": 200 },
      { "resourceType": "total", "budget": 1000 }
    ],
    "resourceCounts": [{ "resourceType": "third-party", "budget": 10 }],
    "timings": [
      { "metric": "largest-contentful-paint", "budget": 2500 },
      { "metric": "cumulative-layout-shift", "budget": 0.1 },
      { "metric": "total-blocking-time", "budget": 200 }
    ]
  }
]
```

### 5.2 SEO

- URLs: `/products/<handle>`, `/collections/<handle>`, `/pages/<slug>`; lowercase, hyphenated, permanent; 301s for any change.
- One canonical per page; variant selection updates the URL query without creating duplicate canonicals.
- Titles ≤ 60 characters with the product and brand; meta descriptions ≤ 155 written for humans; Open Graph and Twitter cards with the product hero at 1200×630.
- XML sitemap with images, submitted to Search Console; `robots.txt` allowing everything on production (non-production is `noindex` via the pipeline).
- Internal linking: breadcrumbs, related products, category links in the footer.
- Product feed to Google Merchant Center free listings (platform feature); ensure prices, availability, and shipping in the feed match the page.
- Content: an About page and process content earn links and trust; a blog only if the human will actually write.

### 5.3 Structured data (validated in CI and in Google's Rich Results Test)

- `Organization` (or `LocalBusiness` if there is a public workshop address) with logo and `sameAs`; `WebSite` with `SearchAction` if search exists.
- `BreadcrumbList` on PLP and PDP; `Product` + `Offer` with `shippingDetails` and `hasMerchantReturnPolicy` on every PDP (Appendix D); `AggregateRating` and `Review` only from real reviews; `FAQPage` on the FAQ.
- Made-to-order items use `InStock` availability with `handlingTime` expressing the lead time; personalised items that cannot be returned use `MerchantReturnNotPermitted` in their own policy object.
- A Playwright test parses every page's JSON-LD and asserts required fields; a broken schema fails the PR.

### 5.4 Analytics and measurement

- One analytics tool. If privacy-first without cookies (Plausible, Umami, Fathom) meets the human's needs, prefer it: no consent banner required in most jurisdictions and no page-weight cost worth mentioning. GA4 if they need Google Ads/Merchant Center attribution.
- E-commerce events (GA4 names, mapped to goals elsewhere): `view_item_list`, `select_item`, `view_item`, `add_to_cart`, `remove_from_cart`, `view_cart`, `begin_checkout`, `add_shipping_info`, `add_payment_info`, `purchase` (from the platform, server-side where possible), plus `search`, `newsletter_signup`, `notify_me`.
- A monthly dashboard the human reads: sessions by device, conversion rate, average order value, funnel drop-off by step, top products, PLP filters used, search terms with zero results, Core Web Vitals field data.
- No session recording or heatmap tools without consent and a written reason.

### 5.5 Consent and legal (flag to the human; do not decide alone)

- Cookie consent banner only if non-essential cookies are set and visitors come from the EU/UK/similar regimes; the cookieless analytics route avoids it. If GA4 or ad pixels are used, implement Google Consent Mode with a compliant banner and honour "reject all" fully.
- Privacy policy naming every processor (platform, payment, analytics, email); terms of sale including made-to-order and personalised-item rules; returns policy consistent across site, checkout, and structured data.
- Email marketing: explicit opt-in (double opt-in for EU/UK), unsubscribe in every message, physical address in the footer.
- Accessibility: WCAG 2.2 AA target, an accessibility statement, and a contact route; in the US, ADA exposure makes this a business requirement, not a nicety.
- Pricing and reference-price claims per Section 4.3; product safety and labelling rules if anything is sold for children (flag for the human).
- Business identity visible: legal name, contact, address where required.

---
## 6. Delivery plan

Work lands in this order, each phase a set of small PRs through the pipeline, each ending with re-measurement against Section 1.2 and re-scoring of the affected checklists.

| Phase | Scope | Exit criteria |
|---|---|---|
| **1 Audit** | Sections 1.1–1.4 | audit merged, priorities agreed, inputs received |
| **2 Design system** | Section 2: tokens, fonts/icons, components, `/design-system` preview route (noindex on staging) | components pass specs, axe, visual snapshots; human approves the look |
| **3 Money path** | PDP (3.4), bag (3.5), checkout hand-off configuration (3.6), platform decision and data model (4.1–4.6), structured data on PDP | test-mode purchases pass on phone and desktop; all PDP/bag Musts ≥ 2 |
| **4 Findability** | PLP (3.3), navigation and global chrome (3.1), search (3.9) | PLP Musts ≥ 2; filters in URL; prefetch working |
| **5 Story and trust** | Home (3.2), content and policy pages (3.8), transactional emails (3.7), errors (3.10) | copy approved; policies consistent everywhere; emails tested |
| **6 Hardening** | Performance budgets (5.1), SEO (5.2), analytics and dashboard (5.4), consent/legal items (5.5), dark-mode and motion QA, 320 px and 200 % zoom pass | budgets enforced in CI; Lighthouse ≥ 90/100/100/100 mobile on home, PLP, PDP; axe clean |
| **7 Measure and iterate** | Two to four weeks of production data; fix the worst funnel step; retire anything unused | conversion, AOV, and CWV compared with baseline; report to the human |

### 6.1 Tests added to the pipeline (extend `CICD-BRIEF.md` Phase 3 suites)

- **Commerce flow (Playwright, staging and previews only):** select variant → price and availability update → personalisation entered → add to bag → drawer shows the correct line → quantity change → checkout hand-off lands on the provider's **test** host → success page renders. Appendix E has the skeleton.
- **Accessibility:** `@axe-core/playwright` on home, PLP, PDP, bag, policies, 404; zero serious/critical; keyboard-only run through the money path.
- **Visual regression:** `toHaveScreenshot` for every component state and every template at 375 and 1280, light and dark; snapshots committed; updates only through a PR that explains the change.
- **Structured data:** parse JSON-LD on PLP/PDP/FAQ and assert required fields and types.
- **Performance:** Lighthouse CI mobile preset with `budget.json`; assertions escalate from warn to error one week after each phase lands.
- **Content:** link checker, image alt presence, `Intl` price formatting, no `!` in UI copy (a lint over the content source).

### 6.2 Definition of Done

- [ ] Every **Must** in Sections 3–5 scores ≥ 2 in the final audit; every **Should** is either ≥ 2 or waived in writing by the human.
- [ ] Section 1.2 targets met on home, PLP, PDP, and bag, in Lighthouse and in field data after two weeks.
- [ ] The design review checklist (2.8) passes on every template in both color schemes at 320, 375, 744, 1024, 1440.
- [ ] Test-mode purchases (card, wallet, discount, personalised item) pass on iPhone Safari, Android Chrome, desktop Safari/Chrome/Firefox, and are covered by Playwright.
- [ ] `docs/DESIGN-SYSTEM.md`, `docs/VOICE.md`, `docs/components/*.md`, `docs/UX-AUDIT.md` (before/after), `docs/PERFORMANCE.md`, and updated `docs/ENVIRONMENTS.md` exist and match reality.
- [ ] The human can add a product, change a price, adjust a lead time, and publish a policy change without touching code.
- [ ] No dark patterns anywhere (checked against deceptive.design's taxonomy). No Apple trademarks, fonts, or symbols in the codebase.

---

## Appendix A — Apple HIG concepts mapped to the web

| HIG concept | Web implementation here |
|---|---|
| Dynamic Type / text styles | `rem`-based type ramp with `clamp()` for display sizes; respects browser zoom and text-size preferences |
| 44 × 44 pt minimum hit target | `--target-min: 44px` on primary controls; WCAG 2.2 24 px floor elsewhere |
| SF Pro / SF Symbols | Inter (or system stack) / Lucide, for licence reasons |
| System colors and semantic labels | `tokens.css` with `light-dark()`; accessible variants for text |
| Materials (vibrancy) | `backdrop-filter` navigation with `prefers-reduced-transparency` fallback |
| Sheets and popovers | native `<dialog>`; bottom sheet on phones, side drawer on desktop |
| Navigation bar / toolbar | 48 px sticky header; sticky add-to-bag bar on PDP |
| Segmented control | radio group styled as pills for variant options |
| Stepper | quantity control with 44 px buttons and live announcements |
| Lists and grouped tables | specs table with hairlines; accordions with `<details>` |
| Dark Mode | first-class tokens; screenshots required in both schemes |
| Reduce Motion / Increase Contrast | media-query overrides at the token level |
| Layout margins and safe areas | `--gutter`, `env(safe-area-inset-*)`, content width tokens |
| Feedback and haptics | 100 ms visual response, press scale, `role="status"` toasts (no web haptics) |
| Writing guidelines | `docs/VOICE.md`: short, concrete, sentence case, no exclamation marks |

## Appendix B — Forms and checkout usability checklist (Baymard and NN/g-derived)

- Single-column forms; labels above fields; required fields marked, optional ones labelled "optional".
- Field count minimised: name, email, address (with autocomplete), phone (explained), payment. No confirm-email, no confirm-password, no account creation before purchase.
- `autocomplete` tokens: `name`, `email`, `tel`, `street-address`, `address-line1/2`, `address-level2` (city), `address-level1` (state), `postal-code`, `country`, `cc-name`, `cc-number`, `cc-exp`, `cc-csc`; `inputmode="numeric"` for numeric fields; `type="email"`/`"tel"`.
- Inline validation on blur, not on every keystroke; success ticks are optional, errors are specific; error summary with links for long forms.
- Formatting forgiveness: accept spaces in card numbers and postcodes, any phone format.
- Address: postcode/zip first with lookup where available; country selector defaults from locale; state/province only when relevant.
- Shipping options show cost and delivery date range; the cheapest or most popular is preselected and stated.
- Order summary visible throughout with line items, discounts, shipping, tax, total; editable bag link.
- Trust: security statement next to payment, accepted cards, return policy link, contact details.
- Progress: clearly numbered steps or a single page; back navigation never loses data.
- Buttons name the next step ("Continue to shipping", "Pay $128.00"); the primary is the only filled button.
- Mobile: numeric keypads, no zoom-on-focus (16 px+ inputs), sticky primary button, wallet buttons first.

## Appendix C — Photography shot list (per product, per variant hero)

| Shot | Purpose | Notes |
|---|---|---|
| Hero on neutral | card and PDP first image | 4:5, product fills 70–80 % of frame, consistent angle per family |
| Second angle | reveals form | same lighting |
| Detail ×2 | joinery, finish, grain, hardware | macro, shallow depth of field |
| Scale | size comprehension | with a hand, a common object, or in a room |
| Lifestyle | context and aspiration | 3:2, real setting, natural light acceptable |
| Dimensions diagram | replaces reading specs | clean line drawing over the hero silhouette, exported as SVG |
| Personalisation example | shows engraving/options | one per personalisable product |
| Process (per family) | About and PDP "how it's made" | workshop, hands, tools |

Deliver masters as TIFF or max-quality JPEG at ≥ 3000 px on the long edge, color-managed (sRGB), with consistent white balance.

## Appendix D — Product JSON-LD example

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "@id": "https://daddybuildit.shop/products/walnut-floating-shelf#product",
  "name": "Walnut floating shelf",
  "description": "Solid black walnut shelf with a hidden steel bracket. Made to order in our workshop.",
  "image": [
    "https://daddybuildit.shop/images/products/walnut-shelf-hero-2048.avif",
    "https://daddybuildit.shop/images/products/walnut-shelf-detail-2048.avif"
  ],
  "sku": "SHELF-WAL-36",
  "brand": { "@type": "Brand", "name": "Daddy Build It" },
  "material": "Black walnut",
  "offers": {
    "@type": "Offer",
    "url": "https://daddybuildit.shop/products/walnut-floating-shelf",
    "priceCurrency": "USD",
    "price": "149.00",
    "priceValidUntil": "2027-12-31",
    "itemCondition": "https://schema.org/NewCondition",
    "availability": "https://schema.org/InStock",
    "shippingDetails": {
      "@type": "OfferShippingDetails",
      "shippingRate": { "@type": "MonetaryAmount", "value": "0", "currency": "USD" },
      "shippingDestination": { "@type": "DefinedRegion", "addressCountry": "US" },
      "deliveryTime": {
        "@type": "ShippingDeliveryTime",
        "handlingTime": { "@type": "QuantitativeValue", "minValue": 10, "maxValue": 15, "unitCode": "DAY" },
        "transitTime": { "@type": "QuantitativeValue", "minValue": 2, "maxValue": 5, "unitCode": "DAY" }
      }
    },
    "hasMerchantReturnPolicy": {
      "@type": "MerchantReturnPolicy",
      "applicableCountry": "US",
      "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
      "merchantReturnDays": 30,
      "returnMethod": "https://schema.org/ReturnByMail",
      "returnFees": "https://schema.org/FreeReturn"
    }
  },
  "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.9", "reviewCount": "27" }
}
```

Generate this from the platform data at build time; never hand-maintain it. Drop `aggregateRating` when there are no reviews.

## Appendix E — Commerce flow test skeleton (Playwright)

```ts
import { test, expect } from "@playwright/test";

const env = process.env.DEPLOY_ENV ?? "preview";
// Hosts of the payment provider's TEST checkout. Fill from discovery, e.g. "checkout.stripe.com" (test-mode session),
// "<store>.myshopify.com" for a development store, "app.snipcart.com" in test mode.
const TEST_CHECKOUT_HOSTS = ["<provider-test-host>"];

test.describe("money path @staging", () => {
  test.skip(env === "production", "never exercise checkout against production");

  test("variant → personalise → add to bag → checkout hand-off", async ({ page }) => {
    await page.goto("/products/<handle-with-variants>");

    const price = page.getByTestId("pdp-price");
    const before = await price.textContent();
    await page.getByRole("radio", { name: /<a non-default option>/i }).check();
    await expect(price).not.toHaveText(before ?? "");
    await expect(page.getByTestId("pdp-availability")).toContainText(/in stock|made to order|ready in/i);

    await page.getByLabel(/engraving|personali[sz]ation/i).fill("For Dad");
    await page.getByRole("button", { name: /add to bag/i }).click();

    const drawer = page.getByRole("dialog", { name: /bag/i });
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText("For Dad")).toBeVisible();
    await expect(page.getByRole("link", { name: /bag, 1 item/i })).toBeVisible();

    await drawer.getByRole("button", { name: /increase quantity/i }).click();
    await expect(drawer.getByRole("spinbutton", { name: /quantity/i })).toHaveValue("2");

    await drawer.getByRole("link", { name: /check out/i }).click();
    await page.waitForURL((url) => TEST_CHECKOUT_HOSTS.some((h) => url.host.endsWith(h)), { timeout: 20_000 });
    await expect(page.getByText(/test mode|sandbox|development store/i).first()).toBeVisible();
  });
});
```

Add `data-testid` hooks (`pdp-price`, `pdp-availability`) to the components; prefer role and label queries everywhere else so the tests also verify accessibility names.

## Appendix F — References

- Apple Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/ (Foundations: accessibility, color, dark mode, layout, materials, motion, typography, writing)
- Apple Design Resources (Figma/Sketch kits, for study only): https://developer.apple.com/design/resources/ · Apple font licence terms: https://developer.apple.com/fonts/ · SF Symbols licence: https://developer.apple.com/sf-symbols/
- Inter: https://rsms.me/inter/ · Lucide icons: https://lucide.dev/ · `light-dark()`: https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/light-dark
- Shopify Polaris (design principles and components): https://polaris.shopify.com/ · Dawn reference theme: https://github.com/Shopify/dawn · Storefront API: https://shopify.dev/docs/api/storefront
- Baymard Institute research and cart-abandonment statistics: https://baymard.com/research · https://baymard.com/lists/cart-abandonment-rate
- Nielsen Norman Group e-commerce UX: https://www.nngroup.com/topic/ecommerce/
- Deceptive design patterns taxonomy: https://www.deceptive.design/
- Core Web Vitals: https://web.dev/articles/vitals · Lighthouse budgets: https://web.dev/articles/use-lighthouse-for-performance-budgets
- WCAG 2.2: https://www.w3.org/TR/WCAG22/ · ARIA Authoring Practices (dialog, tabs, radio group, disclosure): https://www.w3.org/WAI/ARIA/apg/
- Google structured data: Product https://developers.google.com/search/docs/appearance/structured-data/product · Merchant listings https://developers.google.com/search/docs/appearance/structured-data/merchant-listing · Rich Results Test https://search.google.com/test/rich-results
- GA4 e-commerce events: https://developers.google.com/analytics/devguides/collection/ga4/ecommerce
- Stripe Checkout: https://docs.stripe.com/payments/checkout · Apple Pay on the web (domain verification): https://docs.stripe.com/apple-pay?platform=web · Snipcart docs: https://docs.snipcart.com/
