# daddybuildit.shop — Mobile Responsiveness Brief

**Audience:** the Claude Code session working inside the `daddybuildit.shop` repository.
**Goal:** make the site excellent on phones and tablets: no horizontal overflow at any width from 320 px up, legible text, reachable and correctly sized controls, layouts that reflow instead of shrink, images that fit their containers and budgets, navigation and drawers that behave natively, forms that bring up the right keyboard, and Core Web Vitals that pass on a mid-range Android over slow 4G. Fix root causes, not symptoms.

Companion documents in this folder: `CICD-BRIEF.md` (ship everything through that pipeline; previews and staging are how mobile fixes get verified) and `DESIGN-COMMERCE-BRIEF.md` (tokens, components, page standards). This brief can run before the design-system work: it uses the tokens if they exist and plain CSS custom properties if they do not.

---

## 0. How to use this brief

### 0.1 Operating rules for the Claude session

1. **Audit before fixing.** Phase 0 produces `docs/MOBILE-AUDIT.md` with screenshots across the device matrix, an automated overflow and tap-target scan, and a defect log with severities. The human confirms the priorities before the first fix ships.
2. **Mobile first in CSS.** Base styles describe the phone layout; `min-width` media queries widen it. Never write desktop-first CSS with `max-width` overrides for phones. Components adapt to their container with container queries where their size depends on where they are placed.
3. **Root causes only.** `overflow-x: hidden` on `html`/`body`, `user-scalable=no`, `maximum-scale=1`, `zoom`, `!important` cascades, and JavaScript resize handlers that compute layout are not fixes. Appendix C lists the band-aids that fail review. The automated overflow test in Section 8 is written so that hiding overflow does not make it pass.
4. **Content parity.** Google indexes the mobile version. Whatever is on desktop (content, links, structured data, meta) is on mobile. Reflow or collapse, never remove.
5. **Real devices decide.** Emulators and Playwright find most defects; iPhone Safari and Android Chrome on physical devices sign off every phase. If the human has no Android device, use the Android emulator or a real-device cloud for the sign-off run; if no iPhone, the Xcode Simulator.
6. **One template or one component family per PR**, each with before/after screenshots at 320, 375, 393, 412, 768 and 1280 in light and dark, and the automated mobile tests green on the preview.
7. **Measure.** Lighthouse mobile and Core Web Vitals before the first PR and after every phase; numbers in the audit doc.
8. **Do not redesign.** Keep the brand and the page structure. Where a component genuinely cannot work on a phone (a six-column table, a hover mega-menu), replace it with the pattern in this brief and note it for the design-system work.
9. **Ask before anything outward-facing**: changing navigation structure, hiding a section on phones, changing the checkout hand-off, or spending money on device-cloud minutes.
10. **Report at the end of each phase**: defects closed by severity, screenshots, measurements, what needs the human.

### 0.2 What the human must provide

| # | Item | Why |
|---|------|-----|
| 1 | Analytics device mix (phone / tablet / desktop share, top phone models and OS versions, top screen widths) | Sets the device matrix priorities; if unknown, assume 65–75 % phone traffic |
| 2 | Known complaints or screenshots from customers about the mobile site | Fastest path to S1 defects |
| 3 | Which physical devices they own (iPhone model and iOS version, Android model and version, tablet) | Real-device sign-off plan |
| 4 | Priority pages: home, the top three product pages, the collection page that gets the most traffic | Audit and fix order |
| 5 | Whether the design-system tokens from `DESIGN-COMMERCE-BRIEF.md` exist yet | Decides whether this brief creates a minimal token set |
| 6 | Permission to use a real-device cloud (BrowserStack, LambdaTest, or similar) if they lack devices; free alternatives are the Xcode Simulator and Android Studio emulator | Coverage of Safari versions |

### 0.3 Non-goals

- A separate mobile site, an app, or AMP pages. One responsive site.
- Visual redesign, new features, or platform changes.
- Supporting browsers older than the last two major versions of Safari, Chrome, Firefox, and Samsung Internet, except that layout must still not break in them.

---

## 1. What excellent looks like (the standard)

| Area | Standard |
|---|---|
| **Widths** | No horizontal scroll and no clipped content at any viewport from 320 to 1440 px, in portrait and landscape, at 100 % and 200 % browser zoom (WCAG 2.2 1.4.10 Reflow at 320 CSS px). |
| **Viewport** | `width=device-width, initial-scale=1, viewport-fit=cover`. Pinch zoom always enabled (WCAG 1.4.4). Safe areas respected on notched devices. |
| **Text** | Body ≥ 16 px (17 px preferred), line height ≥ 1.4, measure ≤ 75 characters, long words wrap. Headings scale fluidly with `clamp()`; nothing depends on `vw` alone. No text in images. |
| **Targets** | Primary controls ≥ 44 × 44 CSS px (Apple HIG). Every other control ≥ 24 × 24 with ≥ 8 px spacing (WCAG 2.2 2.5.8). Primary actions in the bottom half of the screen where the thumb rests. |
| **Forms** | Inputs ≥ 16 px font (prevents iOS focus zoom), labels above fields, correct `type`/`inputmode`/`autocomplete`/`enterkeyhint`, 44 px tall, the keyboard never covers the focused field or the submit button. |
| **Navigation** | Header ≤ 56 px tall; menu opens as a full-screen sheet with focus trap, scroll lock, `Esc`/back-swipe/scrim close; bag opens as a bottom sheet on phones. No hover-only interactions anywhere. |
| **Images and media** | `srcset`/`sizes` on every content image; `<picture>` art direction for heroes; explicit dimensions; lazy loading below the fold; embeds keep their aspect ratio; no image wider than its container. |
| **Layout** | Intrinsic, content-based breakpoints; grid and flex children can shrink; `dvh`/`svh` for full-height regions instead of `vh`; sticky bars with safe-area padding; landscape phones still usable. |
| **Motion and gestures** | Native scrolling and `scroll-snap` carousels; no custom gesture libraries; `prefers-reduced-motion` honoured; no scroll-jacking; passive listeners. |
| **Performance (mobile)** | LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at the 75th percentile on Lighthouse's default mobile emulation and in the field. Lighthouse mobile performance ≥ 90 on home, PLP, PDP. |
| **Accessibility on touch** | VoiceOver and TalkBack can complete a purchase; focus order matches visual order; zoom to 400 % still reflows; orientation not locked (WCAG 1.3.4); dragging never the only way (2.5.7). |
| **Parity** | Same content, links, structured data, and meta on phone and desktop. |

### 1.1 Device and viewport matrix

Test every template at these widths (CSS px). Playwright device names are in Section 8.1.

| Class | Widths | Devices represented | Notes |
|---|---|---|---|
| Smallest phones / WCAG floor | **320** | iPhone SE (1st gen), Galaxy S9+ (CSS px), folded foldables | Nothing may break here; layout may be single column and plain |
| Compact phones | **360**, **375** | most Androids, iPhone SE 2/3, iPhone 12/13 mini | The design baseline width |
| Standard phones | **390–393**, **412–414** | iPhone 14/15/16, Pixel 7/8, Galaxy S23 | Most traffic; notch and home indicator present |
| Large phones | **430** | iPhone Pro Max, Galaxy Ultra | Two-column product grids still hold |
| Phone landscape | **667–932 × 375–430** | any phone rotated | Header must not eat the viewport; sheets must scroll |
| Small tablets | **744–768** | iPad mini, iPad portrait | Tablet layout begins here |
| Large tablets / landscape | **820–1024** | iPad Air/Pro portrait, iPad landscape | Desktop nav may appear at 1024 |
| Desktop | 1280, 1440 | laptops | Regression check only |

Breakpoints are content-based, but the working set is: base (phone), `≥ 480` (large phones: two columns of cards get more air), `≥ 744` (tablet), `≥ 1024` (desktop navigation and multi-column PDP), `≥ 1280` (wide grids). Add a breakpoint only when a component visibly breaks between two of these, and add it at the width where it breaks.

---
## 2. Phase 0 — Audit and baseline

**Outcome:** `docs/MOBILE-AUDIT.md` with a screenshot matrix, automated scan results, real-device findings, measurements, and a defect log ordered by severity. No fixes ship in this phase.

### 2.1 Automated screenshot matrix

Add `tests/mobile/screenshots.spec.ts` (Section 8.1 config) and run it against staging or a preview:

```ts
import { test } from "@playwright/test";

// The templates that matter; add the human's priority pages.
const PATHS = ["/", "/collections/<top-collection>", "/products/<top-product>", "/bag", "/pages/shipping", "/404-test"];

for (const path of PATHS) {
  test(`screenshot ${path}`, async ({ page }, testInfo) => {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    const name = `${testInfo.project.name}-${path.replace(/\W+/g, "_") || "home"}`;
    for (const scheme of ["light", "dark"] as const) {
      await page.emulateMedia({ colorScheme: scheme });
      await page.screenshot({ path: `audit/${name}-${scheme}.png`, fullPage: true });
    }
  });
}
```

Review every screenshot and record each defect (Section 2.5). Do not skim; overflow, clipped text, overlapping sticky elements, tiny controls, and unreadable contrast on photos are all visible at this stage.

### 2.2 Automated scans (run on every page at 320, 375, and 393 px)

The tests in Section 8.2 are written for CI, but run them now, unfixed, to populate the audit: horizontal overflow with offender lists, undersized targets, inputs under 16 px, viewport meta, image responsiveness, fixed-position elements, and text clipped by `overflow: hidden`. Save each run's output into `docs/MOBILE-AUDIT.md`.

For live debugging, this console snippet lists the elements that reach past the right edge on the current viewport:

```js
// Paste into DevTools (device mode, 320–393 px wide). Lists elements extending past the viewport, widest first.
const vw = document.documentElement.clientWidth;
console.table(
  [...document.querySelectorAll("body *")]
    .map((el) => ({ el, rect: el.getBoundingClientRect(), cs: getComputedStyle(el) }))
    .filter(({ rect, cs }) => rect.width > 0 && (rect.right > vw + 1 || rect.left < -1) && cs.position !== "fixed")
    .sort((a, b) => b.rect.right - a.rect.right)
    .slice(0, 25)
    .map(({ el, rect }) => ({ tag: el.tagName.toLowerCase(), cls: String(el.className).slice(0, 40), right: Math.round(rect.right), width: Math.round(rect.width) }))
);
```

The first offender in document order is usually the cause; everything after it is often its ancestor or a sibling pushed by it.

### 2.3 Measurements

| Metric | How | Record |
|---|---|---|
| Lighthouse mobile (default emulation: mid-range Android, 4× CPU slowdown, slow 4G) on home, top PLP, top PDP, bag | `npx lhci collect --url=<staging url> && npx lhci assert` with the mobile config in Section 8.3, or PageSpeed Insights | performance, accessibility, best practices, SEO; LCP, INP/TBT, CLS; the LCP element |
| Field Core Web Vitals (mobile) | Search Console → Core Web Vitals, or the CrUX dashboard | pass/fail per template group |
| Page weight on PDP over mobile | Lighthouse "network requests" or DevTools | HTML, CSS, JS, images, fonts, third parties |
| axe at 375 px | `@axe-core/playwright` on each template | serious/critical counts |
| Tap-target and font-size failures | Section 8.2 tests | counts per page |

### 2.4 Real-device pass (iPhone Safari and Android Chrome, physical devices)

Walk the money path (home → PLP → PDP → add to bag → bag → checkout hand-off) and the content pages. Check and note:

- Address bar collapse and expansion: does the hero, a `100vh` section, or a sticky bar jump or get cut off?
- Rotate to landscape on every template: is anything unreachable behind the header or a sticky bar?
- Tap every control with a thumb: anything under 44 px, anything too close to its neighbour, anything that needs two tries.
- Focus each form field: does the page zoom (font under 16 px)? Does the keyboard cover the field or the submit button? Is the keyboard type right (email, numeric, phone)? Does autofill offer contact and card details?
- Open the menu and the bag: does the page behind still scroll (scroll lock missing)? Does `Esc`/back gesture close it? Does focus return to the trigger?
- Swipe the gallery: native feel, no accidental page navigation, dots update, zoom works with pinch.
- Pinch-zoom the page to 200 %: still readable, no horizontal scroll trap.
- Dark mode, Low Power Mode (animations), Reader mode on a product page (content order sane), "Request desktop site" (does not break).
- Back/forward: bfcache restores the page instantly; the bag count is correct after returning.
- VoiceOver (iOS) and TalkBack (Android) through PDP → bag: everything has a name, order is logical, the add-to-bag result is announced.
- Third-party embeds (maps, video, reviews, payment buttons): sized to the container, no overflow, no layout shift as they load.

### 2.5 Defect log (`docs/MOBILE-AUDIT.md`)

```markdown
# Mobile audit — daddybuildit.shop

_Date:_ …  _Staging build:_ …  _Devices:_ iPhone <model, iOS>, <Android model, version>, iPad <model>

## Baseline measurements
| Page | LH perf | LH a11y | LCP | INP/TBT | CLS | Weight | axe S/C | Overflow at 320/375/393 | Small targets | Inputs < 16px |
|---|---|---|---|---|---|---|---|---|---|---|

## Defects
| ID | Sev | Page / component | Width(s) | What happens | Root cause (if known) | Screenshot | Fix phase |
|---|---|---|---|---|---|---|---|
| M-001 | S1 | PDP buy box | 320–393 | Add-to-bag button pushed off-screen right by fixed-width option pills | `.options { width: 420px }` | audit/… | 1 |

Severity: **S1** blocks reading or buying (overflow on money pages, unreachable primary action, zoom trap, checkout hand-off broken).
**S2** breaks layout or expectations (overlaps, clipped text, targets under 24 px, keyboard covering inputs, missing scroll lock).
**S3** polish (spacing, crops, animation jank, inconsistent radii).

## Root-cause themes
- …

## Priorities agreed with the human
- …
```

### 2.6 Phase 0 exit criteria

- [ ] Screenshot matrix for every template, light and dark, in `audit/` (git-ignored) with the important ones embedded in the audit doc.
- [ ] Scan outputs and measurements recorded; every S1 and S2 defect has an ID and a suspected root cause.
- [ ] Real-device pass done on at least one iPhone and one Android phone.
- [ ] Human confirmed priorities and the fix order.

---
## 3. Phase 1 — Foundations (fixes that make every later fix smaller)

**Outcome:** a correct document head, a mobile-first base stylesheet, fluid type and space, image and font rules, viewport-height and safe-area handling, and the horizontal overflow on every template eliminated at its root.

### 3.1 Document head

```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>
```

- Never `maximum-scale`, `minimum-scale`, `user-scalable=no`, or a fixed `width=`. They break zoom for people who need it and Lighthouse flags them.
- `viewport-fit=cover` is required for `env(safe-area-inset-*)` to return anything.
- Optional for Android Chrome: `interactive-widget=resizes-content` makes the layout viewport shrink when the keyboard opens. Safari ignores it; Section 6.5 covers Safari with the VisualViewport API.
- `theme-color` tints Safari's and Chrome's browser chrome to match the page in each scheme; keep the values equal to the page background tokens.

### 3.2 `src/styles/base.css` (mobile-first foundations, loaded before component styles)

```css
/* base.css — mobile-first foundations. Every rule here removes a class of mobile defect. */
*, *::before, *::after { box-sizing: border-box; }
* { margin: 0; }

html {
  -webkit-text-size-adjust: 100%;   /* iOS: do not inflate text in landscape */
  text-size-adjust: 100%;
  scroll-padding-block-start: calc(var(--nav-height, 3rem) + 1rem); /* anchors land below the sticky header */
}
@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }

body {
  min-block-size: 100svh;            /* small viewport height: stable while the address bar shows */
  font-family: var(--font-sans, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif);
  font-size: var(--text-body, 1.0625rem);
  line-height: var(--leading-body, 1.47);
  -webkit-font-smoothing: antialiased;
  overflow-wrap: break-word;         /* long URLs, SKUs and words wrap instead of forcing horizontal scroll */
}

/* Media never exceed their container and always reserve their aspect ratio. */
img, picture, video, canvas, svg, iframe, embed, object { display: block; max-inline-size: 100%; }
img, video { block-size: auto; }

/* Form controls inherit typography; 16 px minimum stops iOS Safari zooming on focus. */
input, button, textarea, select { font: inherit; color: inherit; }
input, select, textarea { font-size: max(16px, 1em); }

/* Touch: remove the double-tap-to-zoom delay on controls; provide our own pressed state instead of the grey flash. */
a, button, input, select, textarea, summary, [role="button"] { touch-action: manipulation; }
button, [role="button"], summary { -webkit-tap-highlight-color: transparent; }
button:active, [role="button"]:active { transform: scale(0.98); }

/* Flex and grid children may shrink below their content size; this is the most common overflow cause. */
:where(.flex, .grid, .cluster, .auto-grid) > * { min-inline-size: 0; }

/* Headings and prose wrap well; nothing hyphenates by default. */
h1, h2, h3, h4 { text-wrap: balance; line-height: var(--leading-snug, 1.2); }
p, li, dd, figcaption { text-wrap: pretty; max-inline-size: var(--measure, 70ch); }

/* Focus is always visible; never remove outlines. */
:focus-visible { outline: 2px solid var(--color-focus, #0071e3); outline-offset: 2px; }

/* Layout primitives: intrinsic, no breakpoints needed. */
.container { inline-size: min(100% - 2 * var(--gutter, 1rem), var(--content-default, 61.25rem)); margin-inline: auto; }
.stack > * + * { margin-block-start: var(--stack-space, var(--space-4, 1rem)); }
.cluster { display: flex; flex-wrap: wrap; gap: var(--space-3, 0.75rem); align-items: center; }
.auto-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--min-col, 16rem)), 1fr)); gap: var(--space-4, 1rem); }
.visually-hidden { position: absolute; inline-size: 1px; block-size: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0; }

/* Horizontal scrollers: native scrolling, snap points, contained overscroll, thin scrollbar. */
.scroll-x { overflow-x: auto; overscroll-behavior-x: contain; scroll-snap-type: x mandatory; scrollbar-width: thin; }
.scroll-x > * { scroll-snap-align: start; flex-shrink: 0; }

/* Safe areas on notched phones; requires viewport-fit=cover. */
.safe-inline { padding-inline: max(var(--gutter, 1rem), env(safe-area-inset-left)) max(var(--gutter, 1rem), env(safe-area-inset-right)); }
.safe-bottom { padding-block-end: max(var(--space-4, 1rem), env(safe-area-inset-bottom)); }

/* Embeds keep their ratio without JavaScript. */
.embed { inline-size: 100%; aspect-ratio: var(--ratio, 16 / 9); }
.embed > iframe, .embed > video { inline-size: 100%; block-size: 100%; }

/* Tables that are wider than a phone scroll inside a labelled region instead of breaking the page (Section 5.6). */
.table-scroll { overflow-x: auto; overscroll-behavior-x: contain; }
.table-scroll > table { min-inline-size: 36rem; }
```

Logical properties (`inline-size`, `margin-block`) are used throughout so a future right-to-left locale costs nothing.

### 3.3 Fluid type and space

If `tokens.css` from the design brief exists, use it. Otherwise add this minimal set and migrate later:

```css
:root {
  --text-body: 1.0625rem;
  --text-title: clamp(1.5rem, 1.1rem + 2vw, 2rem);
  --text-large-title: clamp(2rem, 1.2rem + 3vw, 3rem);
  --text-display: clamp(2.5rem, 1.5rem + 4.5vw, 3.5rem);
  --space-section: clamp(3rem, 2rem + 5vw, 8rem);
  --gutter: clamp(1rem, 4vw, 2rem);
  --nav-height: 3rem;
  --measure: 70ch;
}
```

Rules: every `clamp()` keeps a `rem` term in the middle value so text still grows with browser zoom and text-size settings (`5vw` alone fails WCAG 1.4.4); minimum body text is 16 px; headings never exceed 56 px on a phone. Utopia's calculators produce a coherent scale if more steps are needed.

### 3.4 Query conventions

```css
/* Mobile-first: the base rule is the phone layout; widen with min-width only. */
.product-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); }
@media (width >= 744px) { .product-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-4); } }
@media (width >= 1024px) { .product-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-6); } }

/* Components adapt to the space they are given, not to the screen. */
.product-card { container-type: inline-size; }
.product-card__meta { display: grid; gap: var(--space-1); }
@container (width >= 20rem) { .product-card__meta { grid-template-columns: 1fr auto; align-items: baseline; } }

/* Hover affordances only where hover exists; touch devices get the information without hovering. */
@media (hover: hover) and (pointer: fine) { .product-card:hover .product-card__alt-image { opacity: 1; } }

/* Short landscape phones: reclaim vertical space. */
@media (orientation: landscape) and (height <= 500px) { .hero { min-block-size: auto; padding-block: var(--space-8); } }
```

- `minmax(0, 1fr)` instead of `1fr`, so a long word or wide image cannot expand a column past the viewport.
- Range syntax (`width >= 744px`) is Baseline; if the toolchain cannot transpile it for an older target, write `(min-width: 744px)`. Never mix `max-width` overrides into a mobile-first file.
- Media queries in `px` respond to zoom correctly; `em` queries are acceptable if the codebase already uses them. Do not switch mid-project.

### 3.5 Images and media

```html
<!-- Hero with art direction: portrait crop on phones, landscape on tablets and up; AVIF with JPEG fallback. -->
<picture>
  <source type="image/avif" media="(min-width: 744px)" width="2048" height="1152"
          srcset="/img/hero-1024.avif 1024w, /img/hero-1440.avif 1440w, /img/hero-2048.avif 2048w" sizes="100vw">
  <source type="image/avif" width="1080" height="1350"
          srcset="/img/hero-p-480.avif 480w, /img/hero-p-768.avif 768w, /img/hero-p-1080.avif 1080w" sizes="100vw">
  <img src="/img/hero-1024.jpg" width="1024" height="576" alt="Walnut console table in a sunlit hallway"
       fetchpriority="high" decoding="async">
</picture>

<!-- Product card image in a 2/3/4-column grid: sizes tells the browser how wide it will render. -->
<picture>
  <source type="image/avif" srcset="/img/p/shelf-480.avif 480w, /img/p/shelf-768.avif 768w, /img/p/shelf-1024.avif 1024w"
          sizes="(min-width: 1024px) 25vw, (min-width: 744px) 33vw, 50vw">
  <img src="/img/p/shelf-768.jpg" width="768" height="960" alt="Walnut floating shelf, 36 inch" loading="lazy" decoding="async">
</picture>
```

- `width` and `height` on the `<img>` **and** on each `<source>` whose ratio differs, so the box is reserved before the image loads (no CLS).
- `sizes` must match the CSS; a wrong `sizes` downloads 2–4× the bytes on phones. Verify with DevTools' "Rendered size" vs "Intrinsic size".
- Candidates up to 2× the largest rendered width; 3× screens use the 2× candidate without visible loss.
- The LCP image: `fetchpriority="high"`, no `loading="lazy"`, optionally `<link rel="preload" as="image" imagesrcset imagesizes>`. Everything below the fold: `loading="lazy"`.
- Logos as inline SVG or `<img src=".svg">` with explicit dimensions. Background images only for decoration; use `image-set()` for resolution switching.
- Video: `playsinline muted loop preload="none"` with a `poster`; never autoplay with sound; give it an aspect-ratio box.
- Iframes (maps, video, reviews): inside `.embed`, `loading="lazy"`, a `title`, and for maps a static image that activates the live map on tap so the map cannot capture the page scroll.

### 3.6 Fonts

- One variable `woff2` per family, subset to Latin, preloaded; total ≤ 120 KB.
- `font-display: swap` plus a metric-matched fallback so the swap does not shift text:

```css
@font-face { font-family: "Inter"; src: url("/fonts/inter-latin.woff2") format("woff2"); font-weight: 100 900; font-display: swap; }
@font-face { font-family: "Inter Fallback"; src: local("Arial"); size-adjust: 107%; ascent-override: 90%; descent-override: 22%; line-gap-override: 0%; }
:root { --font-sans: "Inter", "Inter Fallback", system-ui, sans-serif; }
```

Generate the override values with a tool such as Fontaine or the Capsize metrics for the chosen font; the numbers above are illustrative.

### 3.7 Heights, safe areas, and browser chrome

- `100vh` is the **largest** viewport on iOS and Android; a "full-screen" hero built with it is cut off while the address bar shows. Use `min-block-size: 100svh` for heroes and `block-size: 100dvh` for sheets and overlays. Never fix heights on text containers.
- Sticky over fixed: `position: sticky; inset-block-start: 0` for the header (scrolls naturally, no keyboard problems). `position: fixed` only for the bottom buy bar and toasts, always with `padding-block-end: env(safe-area-inset-bottom)` and hidden while a text field is focused (Section 6.5).
- Nothing important within the bottom 34 px on notched iPhones unless padded by the safe-area inset.
- Full-bleed sections use `inline-size: 100%`, never `100vw` (which includes the desktop scrollbar and causes a horizontal scrollbar).

### 3.8 Horizontal overflow: root-cause playbook

Work through the offender list from Section 2.2 in document order. Each cause has one correct fix:

| Cause | Fix |
|---|---|
| Fixed `width`/`min-width` in px on a wrapper, form, or card | `inline-size: 100%` or `max-inline-size: 100%`; `min-inline-size: 0` |
| `width: 100vw` | `inline-size: 100%` |
| Grid columns declared `1fr` | `minmax(0, 1fr)` |
| Flex children with long text or images | `min-inline-size: 0` on the child; `flex-wrap: wrap` on the row |
| Bootstrap-style negative-margin rows outside a padded container | give the parent matching padding or remove the negative margins |
| Images or SVGs without `max-inline-size: 100%` | base.css rule; explicit `width`/`height` attributes |
| Long unbroken strings (URLs, SKUs, emails) | `overflow-wrap: break-word` (base), `overflow-wrap: anywhere` on the specific element if needed |
| `white-space: nowrap` on nav or buttons | allow wrapping, or put the row in a `.scroll-x` container |
| Tables | `.table-scroll` wrapper or the stacked pattern in Section 5.6 |
| Off-canvas menus positioned with `translateX(100%)` while visible | `visibility: hidden` when closed, `<dialog>` for the open state, or `overflow: clip` on the parent |
| Absolutely positioned decorations | `overflow: clip` on their positioned parent (not on `body`) |
| `<pre>`/code blocks | `overflow-x: auto` on the block, `white-space: pre-wrap` where acceptable |
| `letter-spacing` or `vw` font sizes on long headings | `clamp()` type, `text-wrap: balance`, allow wrapping |
| Third-party embeds injecting fixed widths | wrap in `.embed` or `.table-scroll`; override widths with `!important` only inside that wrapper and document it |
| Border/padding added to a `width: 100%` box | `box-sizing: border-box` (base) |
| Transformed ancestors of fixed elements | move overlays to `<dialog>` or the end of `<body>` |

Only after the automated overflow test passes on every template may `html { overflow-x: clip; }` be added as a documented last-line defence against future regressions. `overflow-x: hidden` on `body` never, because it silently creates a second scroll container and breaks `position: sticky`.

### 3.9 Phase 1 exit criteria

- [ ] Head, `base.css`, fluid tokens, font strategy merged.
- [ ] Overflow test (Section 8.2) passes at 320, 375, 393, 412, 768 on every template without any band-aid.
- [ ] Every image on the priority pages has dimensions and `srcset`/`sizes`; the LCP image is preloaded; CLS ≤ 0.05 in Lighthouse mobile on those pages.
- [ ] Zoom to 200 % on a phone and 400 % on desktop: content reflows to one column, no horizontal scrolling.

---

## 4. Phase 2 — Global chrome: header, navigation sheet, sticky bars, footer

### 4.1 Header

- Height 48 px (never above 56 px on phones); sticky at the top; translucent material with a hairline; contents: skip link (first focusable), logo (home), menu button, bag link. Search icon only if search exists.
- Menu and bag controls are 44 × 44 px with visible or `visually-hidden` labels; the bag count is inside the accessible name ("Bag, 2 items").
- Announcement bar sits above the header, is not sticky, has its height reserved in CSS so it never shifts content, and remembers dismissal in `localStorage`.
- Logo width is capped (`max-inline-size: 40%`) so long wordmarks cannot push the controls off-screen at 320 px.

### 4.2 Navigation sheet

Built on `<dialog>`: the browser provides the top layer, focus trap, `Esc`, and back-gesture close on Android.

```html
<header class="site-header">
  <a class="skip-link" href="#main">Skip to content</a>
  <a class="site-header__logo" href="/" aria-label="Daddy Build It home">…logo svg…</a>
  <button class="site-header__menu icon-button" type="button" aria-expanded="false" aria-controls="menu" data-open-menu>
    <svg aria-hidden="true" width="24" height="24">…</svg><span class="visually-hidden">Menu</span>
  </button>
  <a class="site-header__bag icon-button" href="/bag" aria-label="Bag, 2 items"><svg aria-hidden="true" width="24" height="24">…</svg><span class="bag-count" aria-hidden="true">2</span></a>
</header>

<dialog id="menu" class="sheet sheet--full" aria-labelledby="menu-title">
  <div class="sheet__header">
    <h2 id="menu-title" class="visually-hidden">Menu</h2>
    <button class="icon-button" type="button" data-close-menu><svg aria-hidden="true" width="24" height="24">…</svg><span class="visually-hidden">Close menu</span></button>
  </div>
  <nav class="sheet__body" aria-label="Primary">
    <ul class="menu-list">…44 px tall rows…</ul>
    <ul class="menu-secondary">…contact, shipping, returns…</ul>
  </nav>
</dialog>
```

```js
// menu.js — navigation sheet on <dialog>: focus trap, Esc and back gesture from the browser; scroll lock and focus return here.
const menu = document.getElementById("menu");
const openButton = document.querySelector("[data-open-menu]");
const closeButton = menu.querySelector("[data-close-menu]");
const desktop = window.matchMedia("(min-width: 1024px)");

function openMenu() {
  menu.showModal();
  openButton.setAttribute("aria-expanded", "true");
  document.documentElement.classList.add("scroll-locked");
}

menu.addEventListener("close", () => {
  openButton.setAttribute("aria-expanded", "false");
  document.documentElement.classList.remove("scroll-locked");
  openButton.focus();
});

openButton.addEventListener("click", openMenu);
closeButton.addEventListener("click", () => menu.close());
// A tap on the backdrop registers on the dialog element itself (its content sits inside .sheet__* wrappers).
menu.addEventListener("click", (event) => { if (event.target === menu) menu.close(); });
// If the viewport grows into the desktop layout while open, close so the inline navigation takes over.
desktop.addEventListener("change", (event) => { if (event.matches && menu.open) menu.close(); });
```

```css
/* Sheets: full-screen on phones; the same element becomes a side drawer or bottom sheet by modifier. */
.sheet { inline-size: 100%; max-inline-size: none; block-size: 100dvh; max-block-size: none; margin: 0; padding: 0; border: 0; background: var(--color-bg, #fff); color: var(--color-text, #1d1d1f); }
.sheet::backdrop { background: var(--color-scrim, rgba(0, 0, 0, 0.4)); }
.sheet__header { display: flex; justify-content: flex-end; align-items: center; block-size: var(--nav-height, 3rem); padding-inline: var(--gutter, 1rem); }
.sheet__body { overflow-y: auto; overscroll-behavior: contain; padding: var(--space-4, 1rem) var(--gutter, 1rem) max(var(--space-6, 1.5rem), env(safe-area-inset-bottom)); }
.menu-list a { display: flex; align-items: center; min-block-size: 44px; font-size: var(--text-title3, 1.5rem); }
.scroll-locked { overflow: hidden; }
.sheet[open] { animation: sheet-in var(--duration-slow, 400ms) var(--ease-out, ease-out); }
@keyframes sheet-in { from { transform: translateY(1rem); opacity: 0; } to { transform: none; opacity: 1; } }
@media (prefers-reduced-motion: reduce) { .sheet[open] { animation: none; } }
@media (min-width: 1024px) { .site-header__menu { display: none; } }
```

Desktop shows an inline `<nav>` in the header; the sheet exists only for phones and tablets. iOS 15 and older may still scroll the page behind the dialog; if analytics show meaningful traffic there, add the `position: fixed; inset: 0` body lock with saved scroll position as a fallback.

### 4.3 Sticky bottom bar (PDP add-to-bag; also the bag sheet footer)

```css
.buy-bar { position: fixed; inset-inline: 0; inset-block-end: 0; z-index: var(--z-nav, 100); display: grid; grid-template-columns: auto 1fr auto; gap: var(--space-3, 0.75rem); align-items: center; padding: var(--space-3, 0.75rem) var(--gutter, 1rem) max(var(--space-3, 0.75rem), env(safe-area-inset-bottom)); background: var(--material-nav, rgba(255, 255, 255, 0.72)); -webkit-backdrop-filter: saturate(180%) blur(20px); backdrop-filter: saturate(180%) blur(20px); border-block-start: 1px solid var(--color-separator, rgba(0, 0, 0, 0.12)); }
.buy-bar[hidden] { display: none; }
.buy-bar .button { min-block-size: 44px; }
/* Reserve room so the bar never covers the end of the page. */
.pdp { padding-block-end: calc(72px + env(safe-area-inset-bottom)); }
@media (min-width: 1024px) { .buy-bar { display: none; } .pdp { padding-block-end: 0; } }
```

```js
// buy-bar.js — show the fixed bar only while the in-page add-to-bag button is off screen, and never while typing.
const bar = document.querySelector(".buy-bar");
const primary = document.getElementById("add-to-bag");
if (bar && primary && "IntersectionObserver" in window) {
  const observer = new IntersectionObserver(([entry]) => { bar.toggleAttribute("hidden", entry.isIntersecting); }, { rootMargin: "0px 0px -48px 0px" });
  observer.observe(primary);
  const syncToPrimary = () => {
    const r = primary.getBoundingClientRect();
    const primaryVisible = r.bottom > 0 && r.top < window.innerHeight - 48;
    bar.toggleAttribute("hidden", primaryVisible);
  };
  // Never sit on top of the keyboard: hide while a field is focused, re-evaluate after blur.
  document.addEventListener("focusin", (e) => { if (e.target.matches("input, textarea, select")) bar.setAttribute("hidden", ""); });
  document.addEventListener("focusout", () => setTimeout(syncToPrimary, 100));
}
```

The bar duplicates the primary action for screen readers, so mark the bar's button `aria-hidden="true" tabindex="-1"` and keep the in-page button as the accessible one, or give the bar's button the same accessible name and let only one exist in the accessibility tree at a time.

### 4.4 Footer

- Columns stack to a single column below 744 px; link groups become `<details>` accordions with 44 px rows, or a flat list if there are fewer than eight links.
- Newsletter form: full-width email field above a full-width button; both 44 px.
- Payment icons and social icons wrap with `.cluster`; legal text at 14 px minimum.
- Nothing in the footer sits under the buy bar: the reserved padding in 4.3 handles it.

### 4.5 Phase 2 exit criteria

- [ ] Header, menu sheet, buy bar, and footer pass the Section 8.2 tests at every width, in both orientations.
- [ ] Menu: opens/closes with tap, `Esc`, back gesture (Android), and scrim; background does not scroll; focus returns to the button; VoiceOver reads "Menu, button, collapsed/expanded".
- [ ] Buy bar never overlaps the keyboard or the footer; safe-area padding visible on a notched iPhone.

---
## 5. Phase 3 — Templates

Fix in money order: PDP, bag, PLP, home, content pages, errors. Every template is checked at the full matrix before its PR is opened.

### 5.1 Product detail page

- **Order on phones:** gallery → name and price → availability and delivery promise → options → personalisation → add to bag → shipping/returns line → details accordions → reviews → related.
- **Gallery:** horizontal scroll-snap, one image per viewport width, page dots, pinch-zoom on the image itself (never disable zoom), tap opens a full-screen `<dialog>` with the same scroller. No third-party carousel.

```css
.gallery { display: grid; grid-auto-flow: column; grid-auto-columns: 100%; overflow-x: auto; scroll-snap-type: x mandatory; overscroll-behavior-x: contain; scrollbar-width: none; }
.gallery::-webkit-scrollbar { display: none; }
.gallery > figure { scroll-snap-align: center; }
.gallery img { inline-size: 100%; aspect-ratio: 4 / 5; object-fit: cover; }
.gallery-dots { display: flex; justify-content: center; gap: var(--space-2, 0.5rem); padding-block: var(--space-3, 0.75rem); }
.gallery-dots button { inline-size: 44px; block-size: 44px; display: grid; place-items: center; background: none; border: 0; }
.gallery-dots button::before { content: ""; inline-size: 8px; block-size: 8px; border-radius: 50%; background: var(--color-fill-strong, rgba(120, 120, 128, 0.2)); }
.gallery-dots button[aria-current="true"]::before { background: var(--color-text, #1d1d1f); }
```

  Dots are updated from an `IntersectionObserver` on the figures; each dot is a 44 px button that scrolls its image into view (`scrollIntoView({ inline: "center", behavior: "smooth" })`, respecting reduced motion).
- **Options:** pills in a wrapping `.cluster`, each ≥ 44 px tall, selected state by ring and text, unavailable options struck through but focusable. Swatches ≥ 44 px with names visible below or on selection.
- **Price and availability** update in place without layout shift: reserve the line heights.
- **Add to bag** full width, 44–50 px tall, in the flow, plus the fixed buy bar from 4.3.
- **Accordions** with `<details>`; summary rows 48 px; open state remembered per page load only.
- **Specs table** stays two-column (label/value) and never scrolls; long values wrap.
- **Related products** in a `.rail` (horizontal, next card peeking so people know to swipe):

```css
.rail { display: grid; grid-auto-flow: column; grid-auto-columns: min(75%, 18rem); gap: var(--space-3, 0.75rem); overflow-x: auto; scroll-snap-type: x proximity; overscroll-behavior-x: contain; padding-inline: var(--gutter, 1rem); scroll-padding-inline: var(--gutter, 1rem); }
.rail > * { scroll-snap-align: start; }
@media (min-width: 1024px) { .rail { grid-auto-flow: row; grid-template-columns: repeat(4, minmax(0, 1fr)); overflow: visible; padding-inline: 0; } }
```

### 5.2 Bag

- **Phones:** a bottom sheet (`.sheet--bottom`) opened from the bag icon and after add-to-bag; **tablets and up:** a right-hand drawer. Both are the same `<dialog>` with a modifier.

```css
.sheet--bottom { block-size: auto; max-block-size: min(90dvh, var(--vvh, 100dvh)); inset-block-start: auto; inset-block-end: 0; border-start-start-radius: var(--radius-lg, 20px); border-start-end-radius: var(--radius-lg, 20px); display: grid; grid-template-rows: auto 1fr auto; }
.sheet__footer { padding: var(--space-3, 0.75rem) var(--gutter, 1rem) max(var(--space-3, 0.75rem), env(safe-area-inset-bottom)); border-block-start: 1px solid var(--color-separator, rgba(0, 0, 0, 0.12)); background: var(--color-bg, #fff); }
@media (min-width: 744px) { .sheet--bottom { inline-size: min(28rem, 100%); block-size: 100dvh; max-block-size: none; inset-block-start: 0; inset-inline-start: auto; inset-inline-end: 0; border-radius: 0; } }
```

- Footer of the sheet: subtotal line, shipping note or estimate, full-width **Check out** button (44–50 px), express wallet button(s) above it if the platform renders them, trust line. The footer is always visible; the line items scroll.
- Line items: 72 px image, name and options on two lines with `-webkit-line-clamp: 2`, price right-aligned with tabular numerals, stepper row with 44 px buttons, remove as a text button (not a tiny ×) with a 5-second undo toast.
- The full `/bag` page mirrors the sheet for people who land on it directly and for no-JavaScript fallbacks.

### 5.3 Collection / listing page

- Two columns from 320 px, three from 744, four from 1024 (Section 3.4 grid). Card image 4:5, product name clamped to two lines, price on its own line; the whole card is one link.
- A slim sticky bar under the header with **Filter** and **Sort** buttons (44 px) and the result count; filters open a bottom sheet with checkboxes at 44 px rows, an "Apply (23)" footer button, and the applied filters as removable chips above the grid; state in the URL.
- Sort can be a native `<select>` on phones (it opens the platform picker); label it visibly.
- "Load more" as a 44 px button that appends and preserves scroll; the footer is always reachable.

### 5.4 Home

- Hero: art-directed portrait image (Section 3.5), heading at `--text-display` capped for phones, one primary button ≥ 44 px placed in the lower half of the first screen, secondary link below it. `min-block-size: 100svh` at most, usually less.
- Sections stack in one column with `--space-section` between them; trust strip becomes a 2 × 2 grid at 320–743 px; featured products use the same 2-column grid as PLP; newsletter field and button stack vertically.
- Any horizontal content on the home page (categories, testimonials) uses `.rail`, never a JavaScript slider.

### 5.5 Forms and the checkout hand-off

- Single column; label above every field; 44 px tall inputs; 16 px font; helper text before the field when it prevents errors; errors inline under the field and summarised at the top of long forms with links.
- Attributes per field type from Appendix B (`type`, `inputmode`, `autocomplete`, `enterkeyhint`, `autocapitalize`, `autocorrect`, `spellcheck`). Correct attributes mean the right keyboard and one-tap autofill of contact and card details.
- Radio pills instead of `<select>` for five options or fewer; native `<select>` and `<input type="date">` otherwise (they open the platform's picker, which is the best mobile control there is).
- The submit button is in flow at the end of the form; sticky only in sheets, and hidden while the keyboard is open (Section 6.5).
- Never `position: fixed` on a form field; never disable autofill; never clear a field on error.
- The hosted checkout is configured, not built: verify on both phones that wallets appear first, fields do not zoom, address autocomplete works, keyboards match field types, the order summary is collapsible, and the pay button is reachable with the keyboard closed. Screenshot every step into the audit.

### 5.6 Content pages, tables, and embeds

- Prose in `.container` with `--measure`; images inside prose are full container width; pull-quotes and callouts stack.
- Tables: two-column specs tables stay as they are. Wider tables either scroll inside `.table-scroll` (add `tabindex="0"`, `role="region"`, and an `aria-label` so keyboard users can scroll them) or stack on phones:

```css
/* Stacked table for phones: each cell shows its column header from data-label. */
@media (max-width: 743px) {
  .table-stack thead { position: absolute; inline-size: 1px; block-size: 1px; overflow: hidden; clip-path: inset(50%); }
  .table-stack tr { display: grid; gap: var(--space-1, 0.25rem); padding-block: var(--space-3, 0.75rem); border-block-end: 1px solid var(--color-separator, rgba(0, 0, 0, 0.12)); }
  .table-stack td { display: grid; grid-template-columns: 8rem minmax(0, 1fr); gap: var(--space-3, 0.75rem); }
  .table-stack td::before { content: attr(data-label); color: var(--color-text-secondary, #6e6e73); }
}
```

  (`max-width` is acceptable here because the phone presentation is the exception, not the base.)
- Code and `<pre>` blocks wrap or scroll inside their box. Maps, video, and review widgets sit in `.embed` boxes and load lazily.
- Policy pages: headings as anchors with `scroll-margin`, a short table of contents at the top on phones.

### 5.7 Errors and empty states

404, 500, empty search, and empty bag follow the same rules: one heading, one sentence, one 44 px action, no full-height layouts that push the action below the fold.

### 5.8 Phase 3 exit criteria

- [ ] Every template passes the Section 8.2 tests at all widths and both orientations, light and dark.
- [ ] Real-device money path (PDP → bag → checkout hand-off) completed on iPhone Safari and Android Chrome with screenshots; wallets render; no zoom traps; keyboard never covers the active field.
- [ ] Visual snapshots for every template committed.

---

## 6. Phase 4 — Touch, focus, keyboard, and motion

### 6.1 Target sizing

- Primary and icon controls 44 × 44 px; everything else ≥ 24 × 24 with ≥ 8 px between neighbours (WCAG 2.2 2.5.8). Inline links inside sentences are exempt but get `padding-block: 0.25em` and generous line height.
- Enlarge the hit area of visually small controls without changing the layout:

```css
.icon-button { position: relative; inline-size: 44px; block-size: 44px; display: grid; place-items: center; border-radius: var(--radius-pill, 980px); }
.hit-area { position: relative; }
.hit-area::before { content: ""; position: absolute; inset: -8px; }
```

### 6.2 Hover, active, and focus

- Anything revealed on hover is also available on tap or is visible by default on touch devices (`@media (hover: none)`). Product-card second image, tooltips, and dropdown menus all need a non-hover path.
- Every control has an `:active` state (press scale or fill change) so taps feel acknowledged within 100 ms.
- `:focus-visible` rings on everything; `outline: none` never appears in the codebase. Focus order equals visual order; the sheet and dialog return focus to their triggers.

### 6.3 Scroll containment

- Sheets and drawers: `overscroll-behavior: contain` on the scrolling body; the page behind is locked (`scroll-locked`); `inert` on `<main>` and `<header>` while a non-`<dialog>` overlay is open (dialogs get this from the browser).
- Horizontal rails: `overscroll-behavior-x: contain`, snap points, visible partial next item; never trap vertical scrolling.
- No scroll-jacking, no `wheel`/`touchmove` `preventDefault` on the page, listeners passive.

### 6.4 Gestures

- Swipe in galleries and rails is native scrolling; swipe-to-dismiss on sheets is optional and never the only way to close.
- Nothing requires a long-press, multi-finger, or drag gesture without a button alternative (WCAG 2.5.7).
- Pull-to-refresh is left to the browser; do not intercept it.

### 6.5 Keyboard avoidance (virtual keyboard)

```js
// viewport.js — expose the visual viewport height so sheets and sticky footers shrink above the on-screen keyboard (iOS Safari does not resize the layout viewport).
const vv = window.visualViewport;
if (vv) {
  const update = () => document.documentElement.style.setProperty("--vvh", `${Math.round(vv.height)}px`);
  vv.addEventListener("resize", update);
  update();
}
// Keep the focused field visible inside sheets.
document.addEventListener("focusin", (e) => {
  if (e.target.matches("input, textarea, select") && e.target.closest(".sheet")) {
    setTimeout(() => e.target.scrollIntoView({ block: "center", behavior: "smooth" }), 300);
  }
});
```

Sheets use `max-block-size: min(90dvh, var(--vvh, 100dvh))`; fixed bars hide on `focusin` (Section 4.3); form fields get `scroll-margin-block: 5rem`.

### 6.6 Motion

- Transitions only on `transform` and `opacity`, durations from tokens, all collapsed by `prefers-reduced-motion`.
- No autoplaying carousels; no parallax on shopping pages; skeletons instead of spinners for content areas.
- `scroll-behavior: smooth` only under `prefers-reduced-motion: no-preference` (already in base.css).

### 6.7 Orientation and unusual viewports

- Never lock orientation (WCAG 1.3.4). Landscape phones get the short-viewport rule from Section 3.4.
- 320 px renders a plain single-column layout with nothing hidden. Foldables and split-screen tablets simply see one of the existing breakpoints.
- Test with a system font size of 120–150 % on Android and with browser zoom 200 % on iOS: layouts reflow, nothing overlaps.

### 6.8 Phase 4 exit criteria

- [ ] Target-size and clipped-text tests pass on every template.
- [ ] Keyboard-only and screen-reader runs through the money path recorded on both phones.
- [ ] No hover-only interaction remains (grep for `:hover` rules without a touch equivalent, reviewed by hand).

---

## 7. Phase 5 — Mobile performance

Targets are the Section 1 numbers, measured with Lighthouse's default mobile emulation and confirmed in the field.

| Lever | What to do |
|---|---|
| LCP | Hero/product image as the LCP element, preloaded with `fetchpriority="high"`, AVIF, correctly sized; critical CSS inline (≤ 14 KB); no render-blocking third-party scripts; fonts preloaded with `swap` |
| CLS | Dimensions on every image and embed; reserved heights for the announcement bar, buy bar, and late-loading widgets; metric-matched font fallback; never insert content above the viewport after load |
| INP | Break long tasks (`scheduler.yield()` or `setTimeout` chunks); no heavy work in `scroll`/`touchmove`; variant switching updates the DOM in one pass; payment SDK loaded on interaction or `requestIdleCallback` |
| JavaScript | ≤ 100 KB on PDP excluding the payment SDK; ship modern syntax only; remove polyfills for evergreen browsers; no carousel or modal libraries (native `<dialog>` and scroll-snap) |
| Third parties | Analytics, reviews, chat, maps: lazy, after interaction or idle, with reserved space; each justified in `docs/PERFORMANCE.md` |
| Below the fold | `content-visibility: auto` with `contain-intrinsic-size` on long sections (reviews, related, footer) |
| Navigation | Prefetch PDP links from PLP on viewport/hover with `Save-Data` respected; bfcache-friendly (no `unload` listeners, no `Cache-Control: no-store` on HTML) |
| Data saving | `prefers-reduced-data` / `Save-Data` header: skip autoplay video and secondary images |
| Testing | Chrome DevTools 4× CPU slowdown + "Slow 4G" for every PR that touches the money path; Lighthouse CI mobile in the pipeline (Section 8.3) |

Exit criteria: Lighthouse mobile ≥ 90 performance on home, PLP, PDP; LCP ≤ 2.5 s, CLS ≤ 0.1, TBT ≤ 200 ms in CI; field CWV "good" within 28 days of the last phase.

---
## 8. Phase 6 — Verification in CI and on devices

### 8.1 Playwright device projects

Extend `playwright.config.ts` from the CI/CD brief. iPhone and iPad descriptors run on WebKit, so CI installs both engines: `npx playwright install --with-deps chromium webkit`.

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  // …existing options (testDir, baseURL, reporters, retries) stay as they are…
  projects: [
    // Mobile matrix: runs tests/mobile/*.spec.ts on every project.
    { name: "phone-320", testMatch: /mobile/, use: { ...devices["Galaxy S9+"] } },
    { name: "iphone-se", testMatch: /mobile/, use: { ...devices["iPhone SE"] } },
    { name: "iphone", testMatch: /mobile/, use: { ...devices["iPhone 14 Pro"] } },
    { name: "iphone-landscape", testMatch: /mobile/, use: { ...devices["iPhone 14 Pro landscape"] } },
    { name: "android", testMatch: /mobile/, use: { ...devices["Pixel 7"] } },
    { name: "tablet", testMatch: /mobile/, use: { ...devices["iPad Mini"] } },
    { name: "tablet-landscape", testMatch: /mobile/, use: { ...devices["iPad Mini landscape"] } },
    // Existing smoke/e2e projects keep running the non-mobile suites.
    { name: "desktop-chromium", testIgnore: /mobile/, use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-chromium", testIgnore: /mobile/, use: { ...devices["Pixel 7"] } },
  ],
});
```

Device names are Playwright's registry names; check `npx playwright devices` if one is missing in the installed version and pick the nearest equivalent.

### 8.2 `tests/mobile/responsive.spec.ts`

These run on previews and staging in the PR workflow (`npm run test:e2e -- --project "phone-320" --project iphone …` or simply all projects) and are required checks.

```ts
import { test, expect, type Page } from "@playwright/test";

const PATHS = (process.env.MOBILE_PATHS ?? "/,/collections/<top-collection>,/products/<top-product>,/bag,/pages/shipping").split(",");

async function settle(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => document.fonts.ready);
}

for (const path of PATHS) {
  test.describe(`mobile ${path}`, () => {
    test.beforeEach(async ({ page }) => settle(page, path));

    test("no horizontal overflow, and no overflow band-aid", async ({ page }) => {
      const result = await page.evaluate(() => {
        const doc = document.documentElement;
        const vw = doc.clientWidth;
        const hides = (el: Element) => ["hidden", "clip"].includes(getComputedStyle(el).overflowX);
        const inScroller = (el: Element) => {
          let node = el.parentElement;
          while (node && node !== document.body) {
            const ox = getComputedStyle(node).overflowX;
            if (ox === "auto" || ox === "scroll") return true;
            node = node.parentElement;
          }
          return false;
        };
        const offenders = [...document.querySelectorAll<HTMLElement>("body *")]
          .filter((el) => {
            const r = el.getBoundingClientRect();
            return r.width > 0 && (r.right > vw + 1 || r.left < -1) && getComputedStyle(el).position !== "fixed" && !inScroller(el);
          })
          .slice(0, 8)
          .map((el) => `${el.tagName.toLowerCase()}.${String(el.className).split(" ")[0]} right=${Math.round(el.getBoundingClientRect().right)}`);
        return { scrollWidth: doc.scrollWidth, vw, bandAid: hides(document.body) || hides(doc), offenders };
      });
      expect(result.bandAid, "overflow-x hidden/clip on html or body hides overflow instead of fixing it").toBe(false);
      expect(result.scrollWidth, `page overflows by ${result.scrollWidth - result.vw}px: ${result.offenders.join(" | ")}`).toBeLessThanOrEqual(result.vw);
      expect(result.offenders, result.offenders.join(" | ")).toEqual([]);
    });

    test("interactive targets meet minimum size", async ({ page }) => {
      const small = await page.evaluate(() => {
        const selector = 'a[href], button, input:not([type="hidden"]), select, textarea, summary, [role="button"], [role="link"], [role="checkbox"], [role="radio"], [tabindex]:not([tabindex="-1"])';
        const isInlineTextLink = (el: Element) => el.tagName === "A" && !!el.closest("p, li, td, dd, figcaption, blockquote");
        return [...document.querySelectorAll<HTMLElement>(selector)]
          .filter((el) => {
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            if (r.width === 0 || r.height === 0 || cs.visibility === "hidden" || isInlineTextLink(el)) return false;
            const min = el.matches('[data-primary], .button--primary, [type="submit"], .icon-button') ? 44 : 24;
            return r.width < min || r.height < min;
          })
          .map((el) => {
            const r = el.getBoundingClientRect();
            const name = (el.getAttribute("aria-label") ?? el.textContent ?? "").trim().slice(0, 30);
            return `${el.tagName.toLowerCase()} "${name}" ${Math.round(r.width)}×${Math.round(r.height)}`;
          });
      });
      expect(small, small.join("\n")).toEqual([]);
    });

    test("form controls will not trigger focus zoom on iOS", async ({ page }) => {
      const small = await page.evaluate(() =>
        [...document.querySelectorAll<HTMLElement>('input:not([type="hidden"]), select, textarea')]
          .filter((el) => parseFloat(getComputedStyle(el).fontSize) < 16)
          .map((el) => el.outerHTML.slice(0, 100)),
      );
      expect(small, small.join("\n")).toEqual([]);
    });

    test("viewport meta uses device width and allows zoom", async ({ page }) => {
      const content = (await page.locator('meta[name="viewport"]').getAttribute("content")) ?? "";
      expect(content).toContain("width=device-width");
      expect(content).not.toMatch(/user-scalable\s*=\s*(no|0)/i);
      expect(content).not.toMatch(/maximum-scale\s*=\s*1(\.0+)?(\s|,|$)/i);
    });

    test("images are responsive and reserve their space", async ({ page }) => {
      const problems = await page.evaluate(() =>
        [...document.images]
          .filter((img) => {
            const r = img.getBoundingClientRect();
            if (r.width === 0) return false;
            const isSvg = img.currentSrc.endsWith(".svg");
            const noDimensions = !img.getAttribute("width") || !img.getAttribute("height");
            const noSrcset = !isSvg && r.width > 160 && !img.srcset && !img.closest("picture");
            const parentWidth = img.parentElement?.getBoundingClientRect().width ?? Infinity;
            return noDimensions || noSrcset || r.width > parentWidth + 1;
          })
          .map((img) => img.currentSrc || img.src),
      );
      expect(problems, problems.join("\n")).toEqual([]);
    });

    test("text is not clipped", async ({ page }) => {
      const clipped = await page.evaluate(() =>
        [...document.querySelectorAll<HTMLElement>("h1, h2, h3, h4, p, li, a, button, label, td, th, dt, dd, summary")]
          .filter((el) => {
            const cs = getComputedStyle(el);
            const intentionallyClamped = cs.webkitLineClamp !== "none" || cs.textOverflow === "ellipsis";
            return !intentionallyClamped && cs.overflow !== "visible" && el.scrollWidth > el.clientWidth + 1 && el.innerText.trim().length > 0;
          })
          .map((el) => `${el.tagName.toLowerCase()}: "${el.innerText.trim().slice(0, 40)}"`),
      );
      expect(clipped, clipped.join("\n")).toEqual([]);
    });

    test("visual snapshot", async ({ page }) => {
      await expect(page).toHaveScreenshot({ fullPage: true, animations: "disabled", mask: [page.locator("[data-dynamic]")] });
    });
  });
}
```

Snapshots: the first run creates baselines; commit them. A snapshot change is reviewed like code. Mark rotating content (`data-dynamic`) so it is masked.

### 8.3 Lighthouse CI mobile configuration (`lighthouserc.mobile.json`)

```json
{
  "ci": {
    "collect": {
      "numberOfRuns": 3,
      "settings": { "formFactor": "mobile", "throttlingMethod": "simulate" }
    },
    "assert": {
      "budgetsFile": "./budget.json",
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.95 }],
        "viewport": "error",
        "unsized-images": "error",
        "uses-responsive-images": "warn",
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "total-blocking-time": ["error", { "maxNumericValue": 200 }]
      }
    },
    "upload": { "target": "temporary-public-storage" }
  }
}
```

Run it against the preview URL in the PR workflow (`treosh/lighthouse-ci-action` with `configPath: ./lighthouserc.mobile.json`). Keep the desktop config from the design brief as a second job if desired; mobile is the gate.

### 8.4 Real-device sign-off (every phase, recorded in the audit doc)

| Check | iPhone Safari | Android Chrome |
|---|---|---|
| Money path completed in test mode | | |
| No zoom on any input; keyboard never covers field or button | | |
| Menu and bag sheets: lock, close paths, focus return | | |
| Gallery swipe, pinch zoom, dots | | |
| Landscape on home, PDP, bag | | |
| 200 % zoom / 150 % system font | | |
| VoiceOver / TalkBack through PDP → bag | | |
| Dark mode | | |
| Back/forward instant (bfcache) | | |
| Safe areas on notched device | n/a for older models | |

Each cell gets ✅/❌ plus a note and a screenshot filename.

### 8.5 Phase 6 exit criteria

- [ ] Mobile test suite required in the ruleset; green across all projects on the current `main`.
- [ ] Lighthouse CI mobile gate active with the thresholds above.
- [ ] Sign-off table complete for the final build, both platforms, all ✅.

---

## 9. Definition of Done

- [ ] No horizontal overflow or clipped text at 320–1440 px, portrait and landscape, light and dark, on every template. Verified by the automated suite without any overflow band-aid in the codebase.
- [ ] Viewport meta correct; pinch zoom works everywhere; safe areas respected.
- [ ] Body text ≥ 16 px; fluid headings; inputs never trigger focus zoom.
- [ ] All primary controls ≥ 44 px, everything else ≥ 24 px with spacing; no hover-only interactions.
- [ ] Menu, bag, filters, and zoom use `<dialog>` with focus trap, scroll lock, `Esc`/back/scrim close, and focus return.
- [ ] Every image has dimensions and `srcset`/`sizes`; heroes are art-directed; LCP image preloaded; embeds keep aspect ratio.
- [ ] Forms: correct keyboards and autofill; keyboard never covers the active field; hosted checkout verified on both phones.
- [ ] Lighthouse mobile ≥ 90 performance and ≥ 95 accessibility on home, PLP, PDP; LCP ≤ 2.5 s, CLS ≤ 0.1, TBT ≤ 200 ms in CI; field CWV good.
- [ ] axe: zero serious/critical at 375 px on every template; VoiceOver and TalkBack complete the money path.
- [ ] Content parity with desktop confirmed (same links, copy, structured data).
- [ ] `docs/MOBILE.md` documents breakpoints, layout primitives, sheet and rail patterns, testing commands, and the device sign-off procedure; `docs/MOBILE-AUDIT.md` shows before/after scores and all S1/S2 defects closed.

---

## Appendix A — iOS Safari and Android Chrome quirks and their fixes

| Symptom | Cause | Fix |
|---|---|---|
| Hero cut off or jumping as the address bar hides | `100vh` equals the largest viewport | `min-block-size: 100svh` for heroes, `block-size: 100dvh` for overlays |
| Page zooms when tapping a field | input font-size under 16 px (iOS) | `font-size: max(16px, 1em)` on controls |
| Fixed bottom bar floats mid-screen when the keyboard opens (iOS) | layout viewport does not shrink | hide the bar on `focusin`; size sheets with `--vvh` from VisualViewport |
| Android keyboard overlays the form | default `interactive-widget=resizes-visual` | add `interactive-widget=resizes-content` to the viewport meta, or handle with VisualViewport |
| Background scrolls behind an open menu | no scroll lock | `<dialog>` + `overflow: hidden` on `html`; `overscroll-behavior: contain` on the sheet body |
| Page wobbles sideways / rubber-bands | an element wider than the viewport | Section 3.8 |
| Grey flash on tap | default tap highlight | provide `:active` styling; set `-webkit-tap-highlight-color: transparent` on that control only |
| Two taps needed to open a menu | hover-only interaction | first tap opens, or use a click-driven disclosure |
| Sticky header covers anchor targets | no scroll padding | `scroll-padding-block-start` on `html` (base.css) |
| Blurry images on 3× screens | no 2× candidate | `srcset` widths up to 2× the rendered size |
| Text jumps when fonts load | no metric-matched fallback | `size-adjust` fallback face + preload (Section 3.6) |
| Safe-area padding has no effect | `viewport-fit=cover` missing | add it to the viewport meta |
| Backdrop blur missing on older iOS | unprefixed only | keep `-webkit-backdrop-filter` alongside |
| Map or embed captures scrolling | iframe swallows touch | static image placeholder that activates on tap |
| Fixed element disappears or misplaces | transformed ancestor becomes its containing block | never transform ancestors of fixed elements; use `<dialog>` top layer |
| Horizontal scrollbar on desktop only | `100vw` includes the scrollbar | `inline-size: 100%` |
| Text huge in landscape or tiny on small phones | `vw`-only type | `clamp()` with a `rem` term |
| Focus lost after closing a sheet | no focus return | `close` handler focuses the trigger (Section 4.2) |
| Slow back navigation | `unload` handlers or `no-store` HTML | remove them; use `pagehide` |
| Pull-to-refresh triggers inside a scroller | overscroll chaining | `overscroll-behavior: contain` on the scroller |

## Appendix B — Form field attribute cheat sheet

| Field | `type` | `inputmode` | `autocomplete` | Other |
|---|---|---|---|---|
| Email | `email` | `email` | `email` | `autocapitalize="off" autocorrect="off" spellcheck="false" enterkeyhint="next"` |
| Phone | `tel` | `tel` | `tel` | |
| Full name | `text` | | `name` | `autocapitalize="words"` |
| Address line | `text` | | `address-line1` / `address-line2` | |
| City | `text` | | `address-level2` | |
| State / province | `select` or `text` | | `address-level1` | |
| Postal code | `text` | `numeric` (US), `text` (UK, CA) | `postal-code` | `autocapitalize="characters"` |
| Country | `select` | | `country` | |
| Search | `search` | `search` | `off` | `enterkeyhint="search"` |
| Discount code | `text` | | `off` | `autocapitalize="characters" autocorrect="off" spellcheck="false" enterkeyhint="done"` |
| Quantity | `text` | `numeric` | `off` | `pattern="[0-9]*"`, paired with stepper buttons |
| Personalisation text | `text` | | `off` | `maxlength`, live counter, `enterkeyhint="done"` |
| Card details | handled by the hosted checkout | | `cc-*` | never rendered by the storefront |

## Appendix C — Band-aids that fail review

- `html, body { overflow-x: hidden }` (or `clip`) as a "fix" for overflow.
- `user-scalable=no`, `maximum-scale=1`, `minimum-scale`, `width=<number>` in the viewport meta.
- `-webkit-text-size-adjust: none`; `zoom:`; `font-size` under 16 px on inputs to "make it fit".
- `100vh` for anything full-height on phones; fixed pixel heights on text containers.
- `100vw` widths; `1fr` grid tracks holding text or images; `white-space: nowrap` on navigation.
- Desktop-first `max-width` overrides layered on a mobile-first file; breakpoints named after devices.
- JavaScript that measures the window and sets widths or heights on layout containers.
- Device sniffing or UA redirects to a separate mobile site; `display: none` on content that exists on desktop.
- Custom carousel, modal, or gesture libraries where scroll-snap and `<dialog>` do the job.
- `outline: none` without a replacement focus style; `touch-action: none` on the page; `preventDefault` on `touchmove`/`wheel` at document level.
- `!important` outside a documented third-party override wrapper.

## Appendix D — References

- MDN: Responsive design https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design · Viewport meta https://developer.mozilla.org/en-US/docs/Web/HTML/Guides/Viewport_meta_element · Viewport units (`dvh`, `svh`) https://developer.mozilla.org/en-US/docs/Web/CSS/length · Container queries https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment/Container_queries · `<dialog>` https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog · VisualViewport https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport · `inert` https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/inert
- web.dev: Learn Responsive Design https://web.dev/learn/design · Learn Images https://web.dev/learn/images · Core Web Vitals https://web.dev/articles/vitals · Optimize INP https://web.dev/articles/optimize-inp · bfcache https://web.dev/articles/bfcache
- WebKit: Designing websites for iPhone X (safe areas, `viewport-fit`) https://webkit.org/blog/7929/designing-websites-for-iphone-x/
- Apple HIG: Layout and touch targets https://developer.apple.com/design/human-interface-guidelines/layout
- Google Search: Mobile-first indexing best practices https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing
- WCAG 2.2: 1.3.4 Orientation, 1.4.4 Resize Text, 1.4.10 Reflow, 1.4.12 Text Spacing, 2.5.7 Dragging Movements, 2.5.8 Target Size (Minimum) https://www.w3.org/TR/WCAG22/
- Every Layout (intrinsic layout primitives) https://every-layout.dev/ · Utopia fluid type and space https://utopia.fyi/
- Playwright emulation and device registry https://playwright.dev/docs/emulation · Visual comparisons https://playwright.dev/docs/test-snapshots
- Lighthouse CI configuration https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md · Chrome DevTools device mode https://developer.chrome.com/docs/devtools/device-mode
