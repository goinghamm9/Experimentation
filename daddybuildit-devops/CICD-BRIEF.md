# daddybuildit.shop — CI/CD Pipeline & Environments Brief

**Audience:** the Claude Code session working inside the `daddybuildit.shop` repository.
**Goal:** replace "push to `main` → Netlify auto-publishes whatever landed" with a proper, tested, reversible delivery pipeline and real dev / preview / staging / production environments, without changing the site's content, design, or host.

Read this whole document before touching anything. Then execute the phases in order. Each phase ends with a verification step and a short status report to the human.

---

## 0. How to use this brief

### 0.1 Operating rules for the Claude session

1. **Discovery before change.** Phase 0 produces `docs/DISCOVERY.md`. Nothing else is modified until it exists and the human has confirmed the decision table in it.
2. **Everything ships through a pull request**, including the pipeline itself. Dogfood the process you are building. Small PRs, one concern each.
3. **Never commit secrets.** Tokens, API keys, and passwords live only in GitHub Actions secrets or Netlify environment variables. If you need a value, ask the human for it by name and tell them exactly where to put it. Run `gitleaks` before every push.
4. **Production stays deployable at every step.** The existing Netlify Git auto-deploy remains switched on until the new pipeline has been proven end to end on staging (see Phase 5 cutover checklist). Never leave production in a half-migrated state overnight.
5. **Ask before anything irreversible or outward-facing:** DNS changes, stopping Netlify builds on the production site, changing the production branch, deleting deploys, changing domain settings, or spending money.
6. **Prefer boring, widely adopted tools.** Pin versions. Keep configs minimal and commented. Stay within free tiers unless the human opts into a paid plan. If a stack-specific choice must be made, use the matrix in Appendix A.
7. **Keep an evidence log** in `docs/EVIDENCE.md` (template in Section 7): every verification you run, the command, the URL, the result, the timestamp.
8. **Do not redesign, refactor, or "improve" site code** beyond what the pipeline needs (for example adding a lockfile, `.nvmrc`, or lint fixes). Fixing a real bug you find is fine, in its own PR, flagged to the human.
9. **Report at the end of each phase**: what was done, what was verified, what the human must do next (with exact clicks or commands), and anything that surprised you.

### 0.2 What only the human can do (collect these up front)

Ask for all of these in one message at the start so the human can do them in one sitting. Where a CLI path exists, offer it as an alternative to clicking.

| # | Item | Why | How the human provides it |
|---|------|-----|---------------------------|
| 1 | GitHub repo URL, visibility (public/private), and plan (Free/Pro/Team) | Rulesets and environment protection rules are free on public repos; private repos need GitHub Pro or higher | Tell you, or run `gh repo view --json visibility,owner,name` |
| 2 | Netlify team plan (Starter/Pro) and who owns the site | Password protection, some analytics, and team seats are paid features | Netlify dashboard → Team settings |
| 3 | A Netlify **Personal Access Token** dedicated to CI (name it `github-actions-ci`) | The pipeline deploys with it | Netlify → User settings → Applications → New access token. Paste it into GitHub: `gh secret set NETLIFY_AUTH_TOKEN` or Settings → Secrets → Actions |
| 4 | Permission to create a **second Netlify site** for staging | Isolated env vars, forms, functions, logs | Say yes; you create it with `netlify sites:create` |
| 5 | DNS provider for `daddybuildit.shop` and access to add a CNAME | `staging.daddybuildit.shop` needs one record | Tell you where DNS lives (Netlify DNS, Cloudflare, registrar) |
| 6 | Third-party services in use and whether each has a **test/sandbox mode** (payments, forms, CMS, analytics, email, search) | Non-production environments must never touch live money or live customer data | List them, and provide test-mode keys for staging |
| 7 | Who should be able to approve a production deploy | Becomes the GitHub Environment required reviewer | GitHub handle(s) |
| 8 | Where deploy notifications should go (email, Slack, Discord) | Failure alerts | Email address or webhook URL |
| 9 | Whether staging may be publicly reachable (with `noindex`) or must be password protected | Determines whether the optional basic-auth edge function is enabled | Yes/no |

### 0.3 Non-goals

- Migrating off Netlify. Changing frameworks. Redesigning pages. Adding paid tooling by default.
- Achieving 100% test coverage. The target is a **fast, trustworthy smoke net**, not an exhaustive suite.

---

## 1. Target architecture

### 1.1 Delivery model in one paragraph

Trunk-based development. Every change is a short-lived branch merged into `main` through a pull request. Nothing can reach `main` without green checks. Every PR gets an ephemeral **preview** URL. Every merge to `main` deploys **staging** automatically and runs end-to-end smoke tests against it. **Production** is a promotion of that exact commit, gated by a one-click human approval in GitHub, followed by post-deploy smoke tests and an automatic restore of the previous deploy if they fail. GitHub Actions orchestrates; Netlify hosts; Netlify's own Git-triggered builds are turned off once the pipeline is proven, so the pipeline is the only path to production.

### 1.2 Environments

| Environment | Purpose | Source of truth | URL | Netlify site | Deployed by |
|---|---|---|---|---|---|
| **local** | develop with production-like routing, functions, env | working tree | `http://localhost:8888` | linked to the staging site | `netlify dev` |
| **preview** | review a single PR | PR head commit | `https://pr-<N>--daddybuildit-staging.netlify.app` | staging site (deploy alias) | CI on `pull_request` |
| **staging** | integration testing, client review, third-party services in test mode | `main` (latest merge) | `https://staging.daddybuildit.shop` | staging site (`--prod` on that site) | CI on `push` to `main` |
| **production** | live customers | the same `main` commit that passed staging | `https://daddybuildit.shop` (+ `www` redirect) | production site (the existing one) | CI, after approval in the `production` GitHub Environment |

Why two Netlify sites instead of one site with branch deploys:

- Separate environment variables, forms, function logs, notifications, and access. A mistake in staging cannot leak into production.
- Branch subdomains on a custom domain require Netlify DNS. A second site works with any DNS provider through a plain CNAME.
- Deploys from GitHub Actions do not consume Netlify build minutes (300/month on Starter). GitHub gives 2,000 Actions minutes/month to private repos and unlimited to public ones.

Why trunk-based (no long-lived `develop` branch): staging always mirrors `main`, so what you test is what you promote. A `develop` → `main` promotion branch drifts and doubles the merge work for a one-person team.

### 1.3 Pipeline at a glance

```
feature branch ──PR──▶ CI: lint · typecheck · unit · build
                        │
                        ├─▶ preview deploy (staging site, alias pr-N)
                        │      └─▶ Playwright smoke + Lighthouse + link check ──▶ sticky PR comment
                        │
               merge ◀── required checks green + conversations resolved
                 │
                 ▼
main ──push──▶ Deploy workflow
                 ├─▶ verify (same checks as CI, re-run on the merge commit)
                 ├─▶ deploy STAGING  ──▶ Playwright e2e against staging.daddybuildit.shop
                 ├─▶ ⏸ approval (GitHub Environment "production", required reviewer)
                 ├─▶ capture current prod deploy id ──▶ deploy PRODUCTION ──▶ smoke
                 │        └─ smoke fails ──▶ restore previous deploy ──▶ alert
                 └─▶ tag + GitHub Release (auto-generated notes) ──▶ notify
```

### 1.4 Decision record (fill during Phase 0; confirm with the human)

| Decision | Value | Notes |
|---|---|---|
| Framework / generator | `<from discovery>` | e.g. plain HTML, Astro, Eleventy, Vite, Next static export, Hugo |
| Package manager | `<npm/pnpm/yarn>` | lockfile **must** be committed |
| Node version | `<LTS in use>` | pinned in `.nvmrc` and `netlify.toml` |
| Build command | `<…>` | |
| Publish directory | `<…>` | |
| Netlify features used | `<functions / edge / forms / identity / redirects / plugins / none>` | |
| Third-party services | `<payments, CMS, analytics, forms, email>` | each with test-mode availability |
| GitHub plan / visibility | `<…>` | decides ruleset availability |
| Netlify plan | `<…>` | decides password protection option |
| Staging privacy | `noindex only` / `basic auth` | |
| Production approver(s) | `<handles>` | |

---
## 2. Phase 0 — Discovery and safety net (no behaviour changes)

**Outcome:** `docs/DISCOVERY.md`, a filled decision record, a baseline tag, a clean secrets scan, and a confirmed rollback path. Nothing about production changes in this phase.

### 2.1 Inventory the repository

Run and record the results:

```bash
git log --oneline -20
git remote -v
ls -la
cat package.json 2>/dev/null
ls package-lock.json pnpm-lock.yaml yarn.lock bun.lockb 2>/dev/null   # exactly one should exist and be committed
cat .nvmrc .node-version .tool-versions 2>/dev/null
cat netlify.toml 2>/dev/null; ls _redirects _headers 2>/dev/null
ls netlify/functions netlify/edge-functions 2>/dev/null
grep -rIl --exclude-dir=node_modules --exclude-dir=.git -iE 'stripe|shopify|snipcart|square|paypal|formspree|sanity|contentful|decap|gtag|googletagmanager|plausible|umami|sentry' . | head -50
```

Identify: framework/generator, build command, publish directory, Node version, package manager, Netlify features used, third-party scripts and SDKs (especially anything that moves money or collects customer data), existing tests or linters (probably none), and any secrets checked into git.

### 2.2 Inventory the Netlify site (read-only)

Ask the human to run `netlify login` locally and `netlify link` in the repo, or to hand you the CI token in the environment as `NETLIFY_AUTH_TOKEN`. Then:

```bash
npx netlify-cli status
npx netlify-cli api getSite --data '{"site_id":"<SITE_ID>"}' | jq '{name, url, ssl_url, build_settings: {cmd: .build_settings.cmd, dir: .build_settings.dir, repo_branch: .build_settings.repo_branch, stop_builds: .build_settings.stop_builds}, published_deploy: {id: .published_deploy.id, created_at: .published_deploy.created_at, commit_ref: .published_deploy.commit_ref}}'
npx netlify-cli env:list --context production   # names only; do NOT paste values into any file
npx netlify-cli api listSiteDeploys --data '{"site_id":"<SITE_ID>","per_page":10}' | jq '.[] | {id, state, context, branch, commit_ref, created_at}'
```

Record: production branch, whether build settings live only in the UI (they must move into `netlify.toml`), env var names and which context each is scoped to, domains configured, deploy notifications configured, whether Netlify Forms/Identity/Functions are active, and the Netlify plan.

### 2.3 Secrets scan of the full history

```bash
# gitleaks: https://github.com/gitleaks/gitleaks
gitleaks git --redact -v . || echo "FINDINGS — review before continuing"
```

If anything real is found (a live payment key, an API token), stop and tell the human. The key must be **rotated at the provider** and removed from Netlify/GitHub config as needed. Do not rewrite git history without an explicit decision from the human; rotation is what actually closes the hole.

### 2.4 Baseline tag and rollback rehearsal (read-only)

```bash
git tag -a baseline-pre-pipeline -m "State of main before CI/CD work" && git push origin baseline-pre-pipeline
```

Confirm with the human that they know how to restore a previous deploy in the Netlify UI today: **Deploys → pick an older "Published" deploy → Publish deploy**. Note the current published deploy id in `docs/DISCOVERY.md`. This is the emergency exit for the whole project.

### 2.5 Write `docs/DISCOVERY.md`

Template:

```markdown
# Discovery — daddybuildit.shop

_Date:_ …  _Author:_ Claude (session …)  _Confirmed by:_ …

## Stack
- Framework/generator: …
- Package manager / lockfile: …
- Node version (local / Netlify): …
- Build command: …   Publish dir: …
- Netlify features: functions [y/n], edge functions [y/n], forms [y/n], identity [y/n], redirects/headers files [y/n], build plugins: …

## Third-party services
| Service | Purpose | Where configured | Test mode available? | Env var names |
|---|---|---|---|---|

## Netlify (production site)
- Site name / id: …   Production branch: …   Auto-publish: on/off
- Domains: …   DNS provider: …
- Env vars (names only, by context): …
- Notifications: …
- Current published deploy id: …   (rollback target)

## GitHub
- Repo: …   Visibility: …   Plan: …   Collaborators: …
- Existing Actions/workflows: …

## Findings & risks
- …

## Decision record
(copy of Section 1.4, filled)
```

### 2.6 Phase 0 exit criteria

- [ ] `docs/DISCOVERY.md` merged via PR.
- [ ] Human confirmed the decision record.
- [ ] `gitleaks` clean (or findings rotated and documented).
- [ ] Baseline tag pushed. Rollback path understood by the human.

---
## 3. Phase 1 — GitHub guardrails (stop bad pushes reaching production today)

**Outcome:** `main` can only change through a PR with green checks; a baseline CI workflow exists; the repo has the standard hygiene files. This phase alone fixes the "push to main and pray" problem while the fuller pipeline is built.

### 3.1 Repository hygiene files

Create (adapt to the stack; keep each file small):

- `.nvmrc` — the Node LTS major the site already builds with (for example `22`). Also set `"engines": { "node": ">=22" }` in `package.json`.
- `.editorconfig`, `.gitattributes` (`* text=auto eol=lf`), and a `.gitignore` covering `node_modules/`, `.netlify/`, `.env`, `.env.*`, `!.env.example`, `dist/` (or the publish dir if it is generated), `playwright-report/`, `test-results/`, `.lighthouseci/`.
- `.env.example` — every env var name the site needs, with placeholder values and a one-line comment each. No real values.
- `.github/CODEOWNERS`:

```
# Every change requests review from the site owner.
* @<buddy-github-handle>
```

- `.github/pull_request_template.md`:

```markdown
## What changed

## Why

## How to verify
- [ ] Preview URL checked on desktop and mobile
- [ ] No console errors on the changed pages
- [ ] (if content/pricing) numbers and links double-checked

## Risk
- [ ] Low (copy/style)  - [ ] Medium (layout/nav/forms)  - [ ] High (checkout, payments, redirects, headers)

## Rollback
Previous production deploy can be re-published from Netlify → Deploys. Anything else needed? …
```

- `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
      day: monday
    open-pull-requests-limit: 5
    groups:
      dev-dependencies:
        dependency-type: development
      production-minor-patch:
        dependency-type: production
        update-types: [minor, patch]
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
      day: monday
```

### 3.2 `package.json` scripts baseline

Every stack gets the same script names so CI stays generic. Map them to real tools using Appendix A.

```json
{
  "scripts": {
    "dev": "netlify dev",
    "build": "<framework build command>",
    "lint": "<eslint/html-validate/stylelint … >",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "typecheck": "<tsc --noEmit | astro check | echo skip>",
    "test": "<vitest run | echo \"no unit tests\">",
    "test:e2e": "playwright test",
    "links": "lychee --offline <publish-dir> || true"
  }
}
```

Install the tooling these scripts need now (`npm i -D prettier` plus the stack's linter from Appendix A); Phase 4 only adds hooks and tightens rules. Phase 2 adds the `postbuild` script.

If the site has no `package.json` (plain HTML), create one with `npm init -y`, set `"private": true`, and use it purely for tooling. The build command becomes a copy into a publish directory (for example `rm -rf dist && mkdir dist && cp -R public/. dist/`), so downstream steps always have a single publish directory to test and deploy.

### 3.3 Baseline CI workflow

`.github/workflows/ci.yml` (Phase 3 extends it with preview deploys and browser tests):

```yaml
name: CI

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  quality:
    name: Lint, typecheck, unit tests
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm run format:check
      - run: npm run lint
      - run: npm run typecheck --if-present
      - run: npm test --if-present

  build:
    name: Build
    needs: quality
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm run build
        env:
          DEPLOY_ENV: preview
      - uses: actions/upload-artifact@v4
        with:
          name: site-${{ github.sha }}
          path: <publish-dir>
          retention-days: 7
          if-no-files-found: error

  secrets-scan:
    name: Secrets scan
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Action versions: use the current major tags when you write the file, then pin each `uses:` to a full commit SHA (`uses: actions/checkout@<sha> # v4.x.y`). Dependabot's `github-actions` ecosystem keeps SHA pins updated.

### 3.4 Protect `main` with a ruleset

Preferred path (works on public repos on any plan, and private repos on GitHub Pro or higher). Save as `.github/rulesets/protect-main.json` for the record and apply with the CLI:

```json
{
  "name": "protect-main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "bypass_actors": [],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "required_linear_history" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          { "context": "Lint, typecheck, unit tests" },
          { "context": "Build" },
          { "context": "Secrets scan" }
        ]
      }
    }
  ]
}
```

```bash
gh api -X POST repos/{owner}/{repo}/rulesets --input .github/rulesets/protect-main.json
gh api repos/{owner}/{repo}/rulesets --jq '.[] | {id, name, enforcement}'
```

Notes:

- `required_approving_review_count` is `0` because a solo maintainer cannot approve their own PR; the human gate lives on the **production deploy** instead (Phase 3). Raise it to `1` and set `require_code_owner_review: true` as soon as a second trusted reviewer exists.
- The `context` strings must match the job `name:` values exactly. When Phase 3 adds the preview job, add its name here too.
- `strict_required_status_checks_policy: true` forces the branch to be up to date with `main` before merge, so what was tested is what merges. Use GitHub's "Update branch" button or enable auto-merge.
- Repository settings to set alongside (Settings → General): **Allow squash merging only**, default commit message = PR title and description, **Automatically delete head branches**, **Allow auto-merge**.
- UI equivalent: Settings → Rules → Rulesets → New branch ruleset, replicate the JSON above.

**If rulesets are unavailable** (private repo on GitHub Free): tell the human the two options — make the repo public (fine for a static shop site with no secrets in git) or upgrade to GitHub Pro. Until then, the pipeline in Phase 3 is still safe: deploys happen only from CI, and CI refuses to deploy anything that fails checks, so a direct push to `main` cannot publish broken code. It just skips code review.

### 3.5 Security settings (Settings → Code security)

Enable everything available on the plan: Dependabot alerts and security updates, secret scanning and push protection, CodeQL default setup (JavaScript/TypeScript, if the site has meaningful JS). If a feature is greyed out, the `secrets-scan` CI job and `npm audit` cover the gap.

### 3.6 Phase 1 exit criteria

- [ ] Hygiene files, `dependabot.yml`, PR template, CODEOWNERS merged.
- [ ] CI workflow green on a trivial PR.
- [ ] Ruleset active. Proof: `git push origin main` from a local branch is rejected (record the error in `docs/EVIDENCE.md`).
- [ ] A PR with a deliberate lint error shows a red check and a disabled merge button (record it, then close the PR).

---
## 4. Phase 2 — Environments (local, preview, staging, production)

**Outcome:** a second Netlify site for staging with its own domain and env vars, `netlify.toml` as the single source of build truth, an environment variable matrix with test-mode credentials everywhere except production, non-production environments hidden from search engines, and a working local dev loop.

### 4.1 Create the staging site (CLI, no Git connection)

```bash
npx netlify sites:create --name daddybuildit-staging      # choose the same team as the production site; note the Site ID
npx netlify sites:list
```

Do **not** connect the staging site to the Git repository in the Netlify UI. It is deployed only by GitHub Actions. Set its primary domain (or do it in Domain management):

```bash
npx netlify api updateSite --data '{"site_id":"<STAGING_SITE_ID>","body":{"custom_domain":"staging.daddybuildit.shop"}}'
```

DNS (human, at the DNS provider): `CNAME staging → daddybuildit-staging.netlify.app`. If DNS is on Cloudflare, use DNS-only (grey cloud) so Netlify can issue the certificate. After propagation, Netlify → Domain management → HTTPS → **Verify DNS / Provision certificate** if it has not happened automatically. Until DNS is ready, the pipeline works fine on `https://daddybuildit-staging.netlify.app`.

Turn on deploy notifications for both sites (Site configuration → Notifications): deploy failed and deploy succeeded, to the email/Slack from Section 0.2.

### 4.2 `netlify.toml` — single source of truth for build settings

Move every build setting out of the Netlify UI into this file (both sites read it from the repo checkout that CI deploys). Replace the placeholders with values from the decision record.

```toml
# netlify.toml — build configuration for BOTH Netlify sites (staging and production).
# Site-specific values (DEPLOY_ENV, keys, URLs) live in each site's environment variables, never in this file.

[build]
  command = "npm run build"          # npm runs "postbuild" (scripts/postbuild-env.mjs) automatically afterwards
  publish = "dist"                   # <publish-dir> from the decision record
  # functions = "netlify/functions"  # uncomment only if the site has serverless functions

[build.environment]
  NODE_VERSION = "22"                # keep in sync with .nvmrc
  NPM_FLAGS = "--no-audit --no-fund"

# Pull-request previews are built by CI with `netlify build --context deploy-preview`.
[context.deploy-preview.environment]
  DEPLOY_ENV = "preview"

# Long-lived redirects live here so they are reviewed like code. Delete this example.
# [[redirects]]
#   from = "/old-page"
#   to = "/new-page"
#   status = 301
#   force = true

# Security headers on every response. CSP starts in report-only mode; tighten it after
# reviewing which third-party origins (payments, fonts, analytics) the site really uses.
[[headers]]
  for = "/*"
  [headers.values]
    X-Content-Type-Options = "nosniff"
    X-Frame-Options = "DENY"
    Referrer-Policy = "strict-origin-when-cross-origin"
    Permissions-Policy = "camera=(), microphone=(), geolocation=()"
    Strict-Transport-Security = "max-age=31536000; includeSubDomains"
    Content-Security-Policy-Report-Only = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self' https:; connect-src 'self'; base-uri 'self'; form-action 'self'"

# Content-hashed assets can be cached forever. Apply only to directories whose filenames include a hash.
[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

# Optional staging password (Section 4.6). No-op unless STAGING_BASIC_AUTH is set on the site.
# [[edge_functions]]
#   path = "/*"
#   function = "staging-auth"
```

Validation: `npx netlify build --context production --dry` prints the resolved config without building. If the site already has `_redirects` or `_headers` files, keep them; Netlify merges both sources.

### 4.3 Environment variable matrix

Rules:

1. **Non-production never holds live payment, email, or customer-data credentials.** If a service has no test mode, staging gets an empty value and the feature degrades gracefully (document this).
2. Site-specific values are set on each Netlify site (`netlify env:set`). GitHub holds only the Netlify token and the two site IDs. CI builds with `netlify build`, which injects the linked site's variables for the given context, so there is one place to look.
3. Every variable appears in `.env.example` with a comment.

| Variable | local (`.env`) | preview | staging | production | Set where |
|---|---|---|---|---|---|
| `DEPLOY_ENV` | `staging` | `preview` | `staging` | `production` | `netlify.toml` (preview) / site env (staging, production) |
| `PUBLIC_SITE_URL` | `http://localhost:8888` | (Netlify provides `DEPLOY_PRIME_URL`) | `https://staging.daddybuildit.shop` | `https://daddybuildit.shop` | site env |
| `PAYMENT_PUBLISHABLE_KEY` (name per provider) | test | test | test | **live** | site env |
| `PAYMENT_SECRET_KEY` (functions only) | test | test | test | **live**, marked secret | site env |
| `ANALYTICS_ID` | empty | empty | staging property or empty | production property | site env |
| forms / email / CMS endpoints | sandbox | sandbox | sandbox | live | site env |
| `STAGING_BASIC_AUTH` (`user:pass`) | unset | staging site value | set only if Section 4.6 is enabled | **never** | staging site env + GitHub secret (so tests can log in) |

```bash
# The CLI targets whichever site NETLIFY_SITE_ID names (no `netlify link` needed).
# Staging site (its "production" context IS the staging environment)
export NETLIFY_SITE_ID="<STAGING_SITE_ID>"
npx netlify env:set DEPLOY_ENV staging --context production
npx netlify env:set PUBLIC_SITE_URL https://staging.daddybuildit.shop --context production
# … test-mode keys …

# Production site
export NETLIFY_SITE_ID="<PRODUCTION_SITE_ID>"
npx netlify env:set DEPLOY_ENV production --context production
npx netlify env:set PUBLIC_SITE_URL https://daddybuildit.shop --context production
# … live keys, added by the human; add --secret for anything private (check `npx netlify env:set --help`) …
```

Audit afterwards with `NETLIFY_SITE_ID=<id> npx netlify env:list` for both sites (names only in the evidence log).

### 4.4 Keep non-production out of search engines

Add `"postbuild": "node scripts/postbuild-env.mjs"` to `package.json` scripts (npm runs it automatically after `npm run build`). The script writes a blocking `robots.txt` plus an `X-Robots-Tag` header into the publish directory unless `DEPLOY_ENV` is `production`:

```js
// scripts/postbuild-env.mjs — environment-specific post-processing of the publish directory.
import { appendFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const publishDir = process.env.PUBLISH_DIR ?? "dist"; // keep equal to [build].publish in netlify.toml
const env = process.env.DEPLOY_ENV ?? "preview";     // unset => treat as non-production (safe default)

mkdirSync(publishDir, { recursive: true });

if (env === "production") {
  console.log("[postbuild-env] production build: indexing allowed, nothing to do");
} else {
  writeFileSync(join(publishDir, "robots.txt"), "User-agent: *\nDisallow: /\n");
  appendFileSync(join(publishDir, "_headers"), "\n/*\n  X-Robots-Tag: noindex, nofollow\n");
  console.log(`[postbuild-env] ${env} build: wrote blocking robots.txt and X-Robots-Tag header`);
}
```

The Playwright smoke test in Phase 3 asserts this in every environment, so a misconfigured `DEPLOY_ENV` is caught before customers or Google see it.

### 4.5 Local development

```bash
npm ci
npx netlify link --id "<STAGING_SITE_ID>" # local dev uses staging's env vars (test mode) — never production's
cp .env.example .env                      # local-only overrides; .env is git-ignored
npx netlify dev                           # http://localhost:8888 with redirects, headers, functions, and env injected
```

Document in the README: `npm run dev`, `npm run lint`, `npm test`, `npm run test:e2e` (against a local server or `BASE_URL=<preview url>`), and `npx netlify env:list`.

### 4.6 Optional: password-protect staging

Netlify's built-in site password is a paid feature. A free equivalent is an Edge Function that enforces HTTP Basic auth only when `STAGING_BASIC_AUTH` is set (staging site only). Create `netlify/edge-functions/staging-auth.ts` and uncomment the `[[edge_functions]]` block in `netlify.toml`:

```ts
// netlify/edge-functions/staging-auth.ts — Basic auth, active only where STAGING_BASIC_AUTH is set.
import type { Context } from "@netlify/edge-functions";

export default async (request: Request, context: Context) => {
  const expected = Netlify.env.get("STAGING_BASIC_AUTH"); // "user:password"
  if (!expected) return context.next();                    // production: variable absent => no auth

  const header = request.headers.get("authorization") ?? "";
  if (header.startsWith("Basic ") && atob(header.slice(6)) === expected) return context.next();

  return new Response("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="staging"', "Cache-Control": "no-store" },
  });
};
```

Playwright sends the credentials through `httpCredentials` (Section 5.5). For Lighthouse, pass the same credentials via `extraHeaders` in `lighthouserc.json` or run Lighthouse only against PR previews. The exact same production build never carries the variable, so it cannot lock customers out.

### 4.7 Phase 2 exit criteria

- [ ] Staging site exists, deploys manually via `NETLIFY_SITE_ID=<STAGING_SITE_ID> npx netlify build --context production && NETLIFY_SITE_ID=<STAGING_SITE_ID> npx netlify deploy --prod --no-build`, and serves `https://staging.daddybuildit.shop` over HTTPS.
- [ ] `curl -sI https://staging.daddybuildit.shop | grep -i x-robots-tag` shows `noindex`; production shows nothing.
- [ ] `netlify.toml` merged; Netlify UI build fields are empty or identical to the file.
- [ ] Env var matrix documented in `docs/ENVIRONMENTS.md`; both sites audited; no live keys on staging.
- [ ] `netlify dev` runs the site locally with staging env vars.

---
## 5. Phase 3 — The pipeline (preview → staging → approval → production → smoke → rollback)

**Outcome:** two workflows. `ci.yml` runs on every PR and publishes a preview with test results. `deploy.yml` runs on every merge to `main`: staging, end-to-end tests, human approval, production, post-deploy smoke, automatic restore on failure, release tag. Production deploys stay behind a feature flag (`PRODUCTION_DEPLOYS_ENABLED`) until the Phase 5 cutover.

### 5.1 GitHub secrets, variables, and environments

```bash
OWNER_REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)

gh secret set NETLIFY_AUTH_TOKEN                      # paste the CI token when prompted; never echo it
gh variable set NETLIFY_STAGING_SITE_ID    --body "<STAGING_SITE_ID>"
gh variable set NETLIFY_PRODUCTION_SITE_ID --body "<PRODUCTION_SITE_ID>"
# gh secret set STAGING_BASIC_AUTH --body "user:password"   # only if Section 4.6 is enabled

gh api -X PUT "repos/$OWNER_REPO/environments/staging" >/dev/null

APPROVER_ID=$(gh api "users/<buddy-github-handle>" --jq .id)
gh api -X PUT "repos/$OWNER_REPO/environments/production" --input - <<JSON
{
  "reviewers": [ { "type": "User", "id": $APPROVER_ID } ],
  "deployment_branch_policy": { "protected_branches": false, "custom_branch_policies": true }
}
JSON
gh api -X POST "repos/$OWNER_REPO/environments/production/deployment-branch-policies" -f name=main -f type=branch
```

If "Required reviewers" is unavailable on the plan (private repo on GitHub Free): add `github.event_name == 'workflow_dispatch'` to the `deploy-production` job's `if:` below. Promotion then happens through Actions → Deploy → **Run workflow** on `main`; staging remains automatic on every merge.

Add `netlify-cli` and the test tooling to the repo so versions are pinned by the lockfile:

```bash
npm i -D netlify-cli @playwright/test @lhci/cli
```

### 5.2 `ci.yml` — pull requests

Every deploy is two explicit steps: `netlify build --context <ctx>` (runs the build with that context's env vars and any build plugins) then `netlify deploy --no-build` (uploads the publish and functions directories named in `netlify.toml`). Recent CLI majors build by default on `deploy`, so `--no-build` states the intent and an old CLI fails loudly on the unknown flag instead of silently deploying a stale directory; confirm with `npx netlify deploy --help`.

Replace the Phase 1 `Build` job with a job that builds through Netlify's CLI (so the preview gets the staging site's `deploy-preview` env vars), deploys a PR alias, and tests the live preview. Update the ruleset's required checks to `Lint, typecheck, unit tests`, `Preview deploy + smoke`, `Secrets scan`.

```yaml
name: CI

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  quality:
    name: Lint, typecheck, unit tests
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm run format:check
      - run: npm run lint
      - run: npm run typecheck --if-present
      - run: npm test --if-present

  secrets-scan:
    name: Secrets scan
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  preview:
    name: Preview deploy + smoke
    needs: quality
    # Secrets are not exposed to PRs from forks; skip the deploy there instead of failing.
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    timeout-minutes: 25
    permissions:
      contents: read
      pull-requests: write
    env:
      NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
      NETLIFY_SITE_ID: ${{ vars.NETLIFY_STAGING_SITE_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci

      - name: Build (Netlify context deploy-preview)
        run: npx netlify build --context deploy-preview

      - name: Deploy preview alias
        id: deploy
        run: |
          npx netlify deploy --no-build \
            --alias "pr-${{ github.event.pull_request.number }}" \
            --message "PR #${{ github.event.pull_request.number }} @ ${{ github.event.pull_request.head.sha }}" \
            --json > deploy.json
          echo "url=$(jq -r .deploy_url deploy.json)" >> "$GITHUB_OUTPUT"

      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium

      - name: Smoke test the preview
        run: npm run test:e2e
        env:
          BASE_URL: ${{ steps.deploy.outputs.url }}
          DEPLOY_ENV: preview
          STAGING_BASIC_AUTH: ${{ secrets.STAGING_BASIC_AUTH }}

      - name: Lighthouse
        id: lighthouse
        uses: treosh/lighthouse-ci-action@v12
        with:
          urls: ${{ steps.deploy.outputs.url }}
          configPath: ./lighthouserc.json
          uploadArtifacts: true
          temporaryPublicStorage: true

      - name: Link check (warn only until the baseline is clean)
        uses: lycheeverse/lychee-action@v2
        with:
          args: --no-progress --base ${{ steps.deploy.outputs.url }} --exclude-mail '<publish-dir>/**/*.html'
          fail: false

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-pr-${{ github.event.pull_request.number }}
          path: playwright-report
          retention-days: 7

      - name: Comment preview link on the PR
        if: always()
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          header: preview
          message: |
            ### Preview: ${{ steps.deploy.outputs.url }}
            Commit `${{ github.event.pull_request.head.sha }}` · smoke tests: **${{ job.status }}**
            Lighthouse: ${{ steps.lighthouse.outputs.links }}
            Playwright report: see the `playwright-report-pr-${{ github.event.pull_request.number }}` artifact on this run.
```

### 5.3 `deploy.yml` — main → staging → approval → production

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      skip_staging_tests:
        description: "Emergency only: skip e2e on staging (production approval is still required)"
        type: boolean
        default: false

permissions:
  contents: read

# One deploy pipeline at a time; never cancel a run that may be mid-deploy.
concurrency:
  group: deploy-main
  cancel-in-progress: false

env:
  NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}

jobs:
  verify:
    name: Verify main
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm run format:check
      - run: npm run lint
      - run: npm run typecheck --if-present
      - run: npm test --if-present

  deploy-staging:
    name: Deploy staging
    needs: verify
    runs-on: ubuntu-latest
    timeout-minutes: 20
    environment:
      name: staging
      url: ${{ steps.deploy.outputs.url }}
    env:
      NETLIFY_SITE_ID: ${{ vars.NETLIFY_STAGING_SITE_ID }}
    outputs:
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - name: Build (staging site, production context)
        run: npx netlify build --context production
      - name: Deploy
        id: deploy
        run: |
          npx netlify deploy --prod --no-build \
            --message "main @ ${{ github.sha }} (run ${{ github.run_id }})" \
            --json > deploy.json
          echo "url=$(jq -r .url deploy.json)" >> "$GITHUB_OUTPUT"
          echo "deploy_id=$(jq -r .deploy_id deploy.json)" >> "$GITHUB_OUTPUT"

  e2e-staging:
    name: E2E on staging
    needs: deploy-staging
    if: ${{ !inputs.skip_staging_tests }}
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npm run test:e2e
        env:
          BASE_URL: ${{ needs.deploy-staging.outputs.url }}
          DEPLOY_ENV: staging
          STAGING_BASIC_AUTH: ${{ secrets.STAGING_BASIC_AUTH }}
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-staging-${{ github.run_id }}
          path: playwright-report
          retention-days: 14

  deploy-production:
    name: Deploy production
    needs: [deploy-staging, e2e-staging]
    # Feature flag: production deploys are off until the Phase 5 cutover sets PRODUCTION_DEPLOYS_ENABLED=true.
    if: ${{ always() && vars.PRODUCTION_DEPLOYS_ENABLED == 'true' && needs.deploy-staging.result == 'success' && (needs.e2e-staging.result == 'success' || needs.e2e-staging.result == 'skipped') }}
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment:
      name: production          # required reviewer => the run pauses here until approved
      url: https://daddybuildit.shop
    env:
      NETLIFY_SITE_ID: ${{ vars.NETLIFY_PRODUCTION_SITE_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - name: Record the currently published deploy (rollback target)
        run: ./scripts/netlify-rollback.sh capture
      - name: Build (production site, production context)
        run: npx netlify build --context production
      - name: Deploy
        id: deploy
        run: |
          npx netlify deploy --prod --no-build \
            --message "main @ ${{ github.sha }} (run ${{ github.run_id }})" \
            --json > deploy.json
          echo "deploy_id=$(jq -r .deploy_id deploy.json)" >> "$GITHUB_OUTPUT"
      - run: npx playwright install --with-deps chromium
      - name: Post-deploy smoke (read-only tests only)
        run: npm run test:e2e -- --grep @smoke
        env:
          BASE_URL: https://daddybuildit.shop
          DEPLOY_ENV: production
      - name: Restore previous deploy because smoke failed
        if: failure() && steps.deploy.outcome == 'success'
        run: ./scripts/netlify-rollback.sh restore
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-production-${{ github.run_id }}
          path: playwright-report
          retention-days: 30

  release:
    name: Tag and release
    needs: deploy-production
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - name: Create release with generated notes
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          TAG="prod-$(date -u +%Y%m%d-%H%M%S)"
          gh release create "$TAG" --target "$GITHUB_SHA" --title "$TAG" --generate-notes

  notify-failure:
    name: Notify on failure
    if: failure()
    needs: [verify, deploy-staging, e2e-staging, deploy-production]
    runs-on: ubuntu-latest
    steps:
      - name: Post to webhook if configured
        env:
          ALERT_WEBHOOK_URL: ${{ secrets.ALERT_WEBHOOK_URL }}
          RUN_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
        run: |
          if [ -z "$ALERT_WEBHOOK_URL" ]; then echo "No ALERT_WEBHOOK_URL secret; relying on GitHub's failure email"; exit 0; fi
          curl -sS -X POST -H 'Content-Type: application/json' \
            -d "{\"text\":\"Deploy pipeline FAILED for daddybuildit.shop: $RUN_URL\"}" "$ALERT_WEBHOOK_URL"
```

Behaviour worth stating to the human:

- Merge → staging is live in a few minutes → the run pauses at **Deploy production** with an "Review deployments" button in the Actions UI (and an email). Approve to ship, reject to stop.
- If several merges queue up, approve the newest run and reject the older ones; each deploy is the full state of `main` at that commit.
- A failed production smoke test restores the previous deploy within seconds. The run is marked failed so nobody mistakes it for a success.

### 5.4 `scripts/netlify-rollback.sh`

```bash
#!/usr/bin/env bash
# Capture the currently published Netlify deploy id, or restore it. Used by deploy.yml and by humans.
#   ./scripts/netlify-rollback.sh capture   # writes .previous-deploy-id
#   ./scripts/netlify-rollback.sh restore   # re-publishes the deploy id in .previous-deploy-id
#   ./scripts/netlify-rollback.sh restore <deploy-id>
set -euo pipefail
: "${NETLIFY_AUTH_TOKEN:?set NETLIFY_AUTH_TOKEN}" "${NETLIFY_SITE_ID:?set NETLIFY_SITE_ID}"
MODE="${1:-capture}"
FILE=".previous-deploy-id"

case "$MODE" in
  capture)
    npx netlify api getSite --data "{\"site_id\":\"$NETLIFY_SITE_ID\"}" | jq -r '.published_deploy.id' > "$FILE"
    echo "Captured published deploy $(cat "$FILE") for site $NETLIFY_SITE_ID"
    ;;
  restore)
    DEPLOY_ID="${2:-$(cat "$FILE")}"
    [ -n "$DEPLOY_ID" ] && [ "$DEPLOY_ID" != "null" ] || { echo "No deploy id to restore" >&2; exit 1; }
    npx netlify api restoreSiteDeploy --data "{\"site_id\":\"$NETLIFY_SITE_ID\",\"deploy_id\":\"$DEPLOY_ID\"}" > /dev/null
    echo "Restored deploy $DEPLOY_ID on site $NETLIFY_SITE_ID"
    ;;
  *) echo "usage: $0 capture|restore [deploy-id]" >&2; exit 2 ;;
esac
```

`chmod +x scripts/netlify-rollback.sh` and add `.previous-deploy-id` to `.gitignore`. Test both modes against the **staging** site before relying on it.

### 5.5 Playwright configuration and smoke tests

`playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.BASE_URL ?? "http://localhost:8888";
const basicAuth = process.env.STAGING_BASIC_AUTH; // "user:password"; only set where Section 4.6 is enabled

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    httpCredentials: basicAuth
      ? { username: basicAuth.split(":")[0], password: basicAuth.split(":").slice(1).join(":") }
      : undefined,
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
  ],
  // Local runs without BASE_URL start the site through netlify dev.
  webServer: process.env.BASE_URL
    ? undefined
    : { command: "npx netlify dev", url: "http://localhost:8888", reuseExistingServer: true, timeout: 120_000 },
});
```

`tests/e2e/smoke.spec.ts` (fill `CRITICAL_PATHS` and the checkout test from discovery):

```ts
import { test, expect } from "@playwright/test";

const env = process.env.DEPLOY_ENV ?? "preview";
// Pages that must never break. Adjust after discovery.
const CRITICAL_PATHS = ["/", "/shop", "/about", "/contact"];

test.describe("smoke @smoke", () => {
  for (const path of CRITICAL_PATHS) {
    test(`${path} responds 200 and renders without errors`, async ({ page }) => {
      const errors: string[] = [];
      page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
      page.on("console", (m) => { if (m.type() === "error") errors.push(`console: ${m.text()}`); });

      const res = await page.goto(path, { waitUntil: "domcontentloaded" });
      expect(res, `no response for ${path}`).not.toBeNull();
      expect(res!.status(), `status for ${path}`).toBe(200);
      await expect(page).toHaveTitle(/\S/);
      await expect(page.locator("body")).toBeVisible();
      expect(errors, errors.join("\n")).toEqual([]);
    });
  }

  test("security headers are present", async ({ request }) => {
    const h = (await request.get("/")).headers();
    expect(h["x-content-type-options"]).toBe("nosniff");
    expect(h["referrer-policy"]).toBeTruthy();
    expect(h["strict-transport-security"]).toBeTruthy();
  });

  test("search-engine indexing matches the environment", async ({ request }) => {
    const robotsHeader = (await request.get("/")).headers()["x-robots-tag"] ?? "";
    const robotsTxt = await (await request.get("/robots.txt")).text();
    if (env === "production") {
      expect(robotsHeader).not.toMatch(/noindex/i);
      expect(robotsTxt).not.toMatch(/^Disallow: \/$/m);
    } else {
      expect(robotsHeader).toMatch(/noindex/i);
      expect(robotsTxt).toMatch(/^Disallow: \/$/m);
    }
  });

  test("primary navigation links resolve", async ({ page, request }) => {
    await page.goto("/");
    const hrefs = await page
      .locator("header a[href], nav a[href]")
      .evaluateAll((els) => els.map((a) => a.getAttribute("href") ?? ""));
    const internal = [...new Set(hrefs.filter((h) => h.startsWith("/") && !h.startsWith("//")))];
    expect(internal.length).toBeGreaterThan(0);
    for (const href of internal) {
      expect((await request.get(href)).status(), href).toBeLessThan(400);
    }
  });
});

test.describe("checkout path @staging", () => {
  test.skip(env === "production", "never exercise checkout against production");

  test("add to cart reaches the payment provider in test mode", async ({ page }) => {
    // Fill in after discovery. Example shape:
    //   await page.goto("/shop");
    //   await page.getByRole("link", { name: /product/i }).first().click();
    //   await page.getByRole("button", { name: /add to cart|buy/i }).click();
    //   await expect(page).toHaveURL(/cart|checkout/);
    //   assert the provider's sandbox/test indicator is visible, never a live payment form.
    test.fixme(true, "implement once the commerce flow is known");
    await page.goto("/");
  });
});
```

Production runs only `@smoke` tests. They are read-only: no form submissions, no cart actions, no purchases.

### 5.6 `lighthouserc.json`

```json
{
  "ci": {
    "collect": { "numberOfRuns": 3, "settings": { "preset": "desktop" } },
    "assert": {
      "assertions": {
        "categories:performance": ["warn", { "minScore": 0.85 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "categories:best-practices": ["error", { "minScore": 0.9 }],
        "categories:seo": ["warn", { "minScore": 0.9 }]
      }
    },
    "upload": { "target": "temporary-public-storage" }
  }
}
```

Run it once against the current production site to get a baseline. Set thresholds a little below the baseline so the check fails only on regressions, then ratchet up. The `seo` assertion is `warn` because previews are intentionally `noindex`.

### 5.7 Phase 3 exit criteria

- [ ] A PR shows: green quality and secrets checks, a sticky preview comment with a working URL, Playwright and Lighthouse results.
- [ ] Merging deploys staging automatically and E2E passes against `staging.daddybuildit.shop`.
- [ ] The run pauses at **Deploy production** (skipped while the flag is off; paused for approval once on).
- [ ] `scripts/netlify-rollback.sh capture` and `restore` verified on the staging site: deploy a visible change, restore, confirm the old version is back, re-deploy.
- [ ] Ruleset required checks updated to the new job names.

---
## 6. Phase 4 — Quality gates, release hygiene, observability

**Outcome:** consistent formatting and linting enforced locally and in CI, Conventional Commits, dependency and security automation, uptime and failure alerting, and documentation the human can operate from without you.

### 6.1 Formatting and linting

- **Prettier** for everything it understands (`.prettierrc`: `{ "printWidth": 100, "singleQuote": false }` plus `.prettierignore` for the publish dir, `node_modules`, lockfiles). Run `npm run format` once in its own PR so later diffs stay readable.
- Linters per stack from Appendix A (ESLint flat config for JS/TS, `stylelint` with `stylelint-config-standard` for CSS, `html-validate` for raw HTML). Start with the recommended presets; do not hand-tune rules.
- Accessibility in the browser tests: add `@axe-core/playwright` and one test that runs `new AxeBuilder({ page }).analyze()` on each critical path, failing on `serious` and `critical` violations. Start as warn if the baseline is noisy, then enforce.

### 6.2 Pre-commit hooks (fast feedback before CI)

```bash
npm i -D husky lint-staged @commitlint/cli @commitlint/config-conventional
npx husky init
echo 'npx lint-staged' > .husky/pre-commit
echo 'npx --no -- commitlint --edit "$1"' > .husky/commit-msg
```

`package.json` additions:

```json
{
  "lint-staged": {
    "*.{js,mjs,cjs,ts,tsx,astro,vue,svelte}": ["eslint --fix", "prettier --write"],
    "*.{css,scss}": ["stylelint --fix", "prettier --write"],
    "*.{html,md,json,yml,yaml,toml}": ["prettier --write"]
  }
}
```

`commitlint.config.js`:

```js
export default { extends: ["@commitlint/config-conventional"] };
```

Hooks are a convenience, not a gate: CI is the gate. Never make a hook slow enough that people reach for `--no-verify`.

### 6.3 Commit and PR conventions

- **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `perf:`, `test:`, `ci:`). With squash merging, the PR title becomes the commit message, so enforce the title format with `amannn/action-semantic-pull-request` in `ci.yml` (job name `PR title`; add it to the ruleset's required checks).
- One PR per change. Draft PRs for work in progress. Preview URL checked before requesting review.
- Auto-merge is fine for Dependabot PRs touching **dev** dependencies once checks pass. Production dependency bumps and anything touching checkout get a human look on the preview.

### 6.4 Releases and changelog

`deploy.yml` already creates a `prod-<timestamp>` tag and a GitHub Release with auto-generated notes on every production deploy. That is the deploy log: who shipped what, when, from which commit.

If the human wants semantic versions and a `CHANGELOG.md`, add `googleapis/release-please-action` (release type `simple` or `node`). It opens a release PR that accumulates Conventional Commits; merging it tags `vX.Y.Z` and deploys through the normal path. Do not add both mechanisms without deciding which tag scheme is canonical.

### 6.5 Dependency and security automation

- Dependabot (Phase 1) for npm and Actions, weekly, grouped.
- `npm audit --audit-level=high` as a CI step: `continue-on-error: true` for the first two weeks while the baseline is cleaned up, then blocking.
- Secret scanning + push protection and CodeQL default setup wherever the plan allows; `gitleaks` in CI regardless.
- Security headers: after two weeks of `Content-Security-Policy-Report-Only`, review what would have been blocked (browser console on staging, or a free CSP report endpoint), add the payment provider, fonts, and analytics origins, then switch the header to enforcing `Content-Security-Policy` **on staging first**. Verify checkout end to end in test mode before promoting. Check the result with securityheaders.com and Mozilla Observatory.
- Netlify token hygiene: the CI token belongs to a named purpose (`github-actions-ci`), is stored only in GitHub secrets, and is rotated on a calendar reminder every 6 months or immediately if a workflow log ever prints it. Rotation procedure is in the runbook.

### 6.6 Observability and alerting

Minimum viable, all free:

| Signal | Tool | Configuration |
|---|---|---|
| Site down / wrong content | UptimeRobot or Better Stack free tier | HTTPS monitor on `https://daddybuildit.shop/` every 5 min with a keyword check (a string from the home page); second monitor on staging at low priority; alerts to the human's phone/email |
| Deploy failed / succeeded | Netlify notifications (both sites) + GitHub Actions failure email | Section 4.1; `ALERT_WEBHOOK_URL` secret for Slack/Discord |
| Pipeline paused for approval | GitHub environment review email | automatic once required reviewers are set |
| JavaScript errors in production | Sentry free tier (optional, only if the site has meaningful JS) | separate DSN per environment via `DEPLOY_ENV`; disabled in preview |
| Payments / forms failing | provider dashboards (webhook failure alerts, form notification emails) | staging points at sandbox endpoints so alerts stay meaningful |
| Traffic | analytics with one property per environment, or none in non-production | `ANALYTICS_ID` per site |

Add a `docs/ENVIRONMENTS.md` table of every URL, dashboard, and alert destination so the human can find things at 2 a.m.

### 6.7 Documentation set

- `README.md`: what the site is, quick start (`npm ci`, `npm run dev`), how to ship (link to the runbook), status badges for CI and Deploy.
- `docs/ARCHITECTURE.md`: Section 1 of this brief, adapted to what was actually built, with the pipeline diagram.
- `docs/ENVIRONMENTS.md`: env var matrix (names only), URLs, site IDs, DNS records, who has access to what.
- `docs/DEPLOYING.md`: the runbook (Section 7.4).
- `docs/DISCOVERY.md` and `docs/EVIDENCE.md` from Phases 0 and 5.
- `CONTRIBUTING.md`: branch naming, Conventional Commits, PR checklist, "never push to main", how to run tests locally.

### 6.8 Phase 4 exit criteria

- [ ] `npm run format:check`, `npm run lint`, and unit tests are green on `main`; hooks installed and documented.
- [ ] PR title check active and required.
- [ ] Uptime monitor alerting verified (pause the monitor's target once on staging or use the tool's test alert).
- [ ] CSP plan documented with a date to switch to enforcing on staging.
- [ ] Documentation set merged; a fresh reader can deploy, roll back, and rotate the token using only the docs.

---
## 7. Phase 5 — Production cutover and end-to-end verification

**Outcome:** production is deployed only by the pipeline, the old auto-publish path is off, every drill below has been executed with evidence, and the human has performed one deploy and one rollback themselves.

### 7.1 Cutover checklist (do this in one sitting, during a quiet hour)

Pre-conditions: Phases 0–4 exit criteria met; staging has been deployed by the pipeline at least five times without manual intervention; rollback script proven on staging; the human is available.

1. **Snapshot.** Record the production site's current published deploy id in `docs/EVIDENCE.md` (`netlify api getSite … | jq .published_deploy.id`).
2. **Enable the flag.** `gh variable set PRODUCTION_DEPLOYS_ENABLED --body true`.
3. **No-op deploy.** Actions → Deploy → Run workflow on `main`. Watch: verify → staging → e2e → pause. Human clicks **Review deployments → Approve**. Confirm the production deploy lands, smoke passes, and a `prod-…` release appears. Production content is unchanged because the commit is the same.
4. **Turn off Netlify's Git builds on the production site.** Netlify → production site → Site configuration → Build & deploy → Build settings → **Stop builds** (or unlink the repository). From now on Netlify only receives deploys from CI. Do **not** enable "Lock deploy"; the approval gate lives in GitHub.
5. **Prove the old path is dead.** Merge a trivial PR (a comment in the README). Confirm no Netlify Git build starts on the production site and the pipeline runs instead.
6. **Update `docs/ENVIRONMENTS.md` and `docs/DEPLOYING.md`** to say production deploys come from GitHub Actions only.
7. **Announce** to the human: what changed, where to approve, where to roll back.

Reverting the cutover, if ever needed: set `PRODUCTION_DEPLOYS_ENABLED` to `false`, re-enable builds on the Netlify production site, and confirm a push to `main` builds on Netlify again. Nothing else has to change.

### 7.2 Verification drills (execute every one; record evidence)

| # | Drill | Steps | Expected | Evidence |
|---|---|---|---|---|
| 1 | Direct push blocked | From a local clone: commit on `main`, `git push origin main` | Rejected by ruleset (or, without rulesets: CI runs and no deploy happens on a failing commit) | Terminal output |
| 2 | Bad PR cannot merge | Open a PR that breaks lint **and** a smoke test (e.g. rename `/contact`) | Red checks, merge button disabled, preview comment shows failure | PR URL, screenshot description |
| 3 | Good PR full path | Open a PR with a visible, harmless change (footer text) | Preview URL renders the change; checks green; merge → staging shows it; run pauses; approve → production shows it; release created | PR URL, run URL, staging and production `curl` output, release tag |
| 4 | Production smoke failure auto-restores | On staging first: temporarily set `CRITICAL_PATHS` to include a bogus path via a PR, deploy to staging, watch e2e fail. Then simulate on production **only** by pointing the smoke step at a wrong `BASE_URL` in a `workflow_dispatch` test branch of the workflow, or by reviewing the staging behaviour if the human prefers not to touch production | Rollback script restores the previous deploy; run marked failed; alert received | Run URL, `published_deploy.id` before/after |
| 5 | Manual rollback | Netlify UI: Deploys → previous → **Publish deploy**; and CLI `scripts/netlify-rollback.sh restore <id>` | Old version live within seconds; smoke passes | `curl` output, timestamps |
| 6 | Hotfix path timing | Create a PR labelled `hotfix`, merge, approve immediately | Time from PR open to production live is under 15 minutes | Timestamps |
| 7 | Environment isolation | Inspect network calls on staging and production for the payment/forms provider | Staging hits sandbox/test endpoints; production hits live; staging serves `noindex`; production does not | Header dumps, request hostnames |
| 8 | Secrets and access | `gitleaks git .`; `gh secret list`; `netlify env:list` on both sites; list GitHub collaborators and Netlify team members | No secrets in git; only expected people have access; CI token is the dedicated one | Command output (names only) |
| 9 | Human-operated deploy | The human ships and rolls back one change using only `docs/DEPLOYING.md` | They succeed without asking you | Their confirmation |

### 7.3 `docs/EVIDENCE.md` template

```markdown
# Verification evidence — daddybuildit.shop pipeline

| Date (UTC) | Drill | Command / URL | Result | Notes |
|---|---|---|---|---|
| 2026-… | 1 Direct push blocked | `git push origin main` → `remote: error: GH013: Repository rule violations…` | PASS | |
| … | | | | |

## Baseline
- Pre-pipeline production deploy id: …
- Lighthouse baseline (production, desktop): perf … / a11y … / bp … / seo …

## Open items
- …
```

### 7.4 Runbook — `docs/DEPLOYING.md`

Write it for the human, in this order, each as a numbered procedure with the exact clicks or commands:

1. **Ship a change.** Branch from `main` → commit → open PR → check the preview URL on phone and desktop → wait for green checks → squash-merge → watch the Deploy run → staging is live → review staging → **Review deployments → Approve** → production is live → glance at the release notes.
2. **Hotfix.** Same path, no shortcuts. Label the PR `hotfix`. Approve production as soon as staging e2e is green. If e2e itself is what is broken and the fix is unrelated, use **Run workflow → skip_staging_tests** once, then fix the test in the next PR.
3. **Roll back production (instant).** Netlify → production site → Deploys → the previous "Published" deploy → **Publish deploy**. Or `NETLIFY_SITE_ID=<prod> ./scripts/netlify-rollback.sh restore <deploy-id>`. Then open a PR that reverts the offending change (`git revert`), because the next merge would otherwise redeploy the bug.
4. **Redeploy production without a code change.** Actions → Deploy → Run workflow on `main` → approve.
5. **Add or change an environment variable.** `NETLIFY_SITE_ID=<id> npx netlify env:set NAME value --context production` on the right site (staging first). Add the name to `.env.example` and `docs/ENVIRONMENTS.md`. Redeploy (variables are read at build time).
6. **Rotate the Netlify CI token.** Create a new token in Netlify → `gh secret set NETLIFY_AUTH_TOKEN` → run a staging deploy to confirm → delete the old token in Netlify.
7. **Add or rename a CI job.** Update the ruleset's required checks to the new job name, or PRs will never become mergeable.
8. **When CI is red and you do not understand why.** Open the failed job log, read the first error, not the last. Re-run once only if the failure was infrastructure (runner lost, download failed). A failing test is never a flake to be re-run into passing.
9. **When staging is broken but production is fine.** Nothing is urgent. Fix forward through a PR.
10. **When production is broken.** Roll back first (step 3), investigate second.
11. **Who has access to what.** Table of GitHub collaborators, Netlify team members, DNS, payment provider, with the principle that every person has their own login and no shared passwords.

### 7.5 Definition of Done (the whole project)

- [ ] A direct push to `main` cannot reach production. Proven.
- [ ] Every PR gets automated checks, a preview URL, browser smoke tests, Lighthouse, and a secrets scan. Merging requires all of them.
- [ ] Every merge deploys staging automatically and runs end-to-end tests against it.
- [ ] Production is a one-click, audited promotion of the commit that passed staging. Only the pipeline deploys production. Netlify Git builds are off on the production site.
- [ ] Post-deploy production smoke tests run; a failure restores the previous deploy automatically and alerts a human.
- [ ] Manual rollback takes under two minutes and is documented; the human has done it once.
- [ ] Non-production environments use test-mode credentials, are `noindex`, and have separate analytics.
- [ ] Secrets live only in GitHub and Netlify. Git history is clean. Dependabot and secrets scanning are on. Security headers are set.
- [ ] Each production deploy produces a tag and release notes.
- [ ] Uptime and failure alerts reach the human.
- [ ] `README`, `CONTRIBUTING`, `docs/ARCHITECTURE`, `docs/ENVIRONMENTS`, `docs/DEPLOYING`, `docs/DISCOVERY`, `docs/EVIDENCE` exist and match reality.
- [ ] All nine drills in Section 7.2 recorded as PASS.

---

## Appendix A — Stack matrix (pick the row that matches discovery)

| Stack | `build` | `lint` | `typecheck` | `test` | Notes |
|---|---|---|---|---|---|
| Plain HTML/CSS/JS, no bundler | copy `public/` (or repo root files) to `dist/` | `html-validate "dist/**/*.html"`, `stylelint "**/*.css"`, `eslint .` | skip | skip | `package.json` exists only for tooling; smoke + Lighthouse + link check do the real work |
| Vite (vanilla/React/Vue/Svelte) | `vite build` | `eslint .` | `tsc --noEmit` / `vue-tsc --noEmit` / `svelte-check` | `vitest run` | hashed assets under `/assets/*` match the cache header in `netlify.toml` |
| Astro | `astro build` | `eslint .` with `eslint-plugin-astro` | `astro check` | `vitest run` | change the cache header path to `/_astro/*` |
| Eleventy | `eleventy` | `eslint .` | skip | `vitest run` if there is JS logic | passthrough copy for static files |
| Next.js (static export) | `next build` with `output: "export"` | `next lint` | `tsc --noEmit` | `vitest run` or `jest` | if the site needs SSR/ISR, keep Netlify's Next runtime; the pipeline is unchanged |
| Hugo | `hugo --minify` | `html-validate` on output | n/a | n/a | pin `HUGO_VERSION` in `[build.environment]`; npm used for tooling only |
| Jekyll | `bundle exec jekyll build` | `htmlproofer ./_site` | n/a | n/a | pin `RUBY_VERSION`; add `bundler-cache` via `ruby/setup-ruby` in CI |
| Gatsby | `gatsby build` | `eslint .` | `tsc --noEmit` | `jest` | cache `.cache` and `public` in CI to keep builds under 10 min |

Commerce add-ons (the domain is `.shop`, so expect one of these):

| Provider | Test mode for staging | CSP origins to allow later | Production smoke rule |
|---|---|---|---|
| Stripe (Checkout / Payment Links / Elements) | `pk_test_…` keys, test-mode payment links, test webhooks per environment | `js.stripe.com`, `checkout.stripe.com`, `api.stripe.com` (`script-src`, `frame-src`, `connect-src`) | never start a checkout session |
| Shopify Buy Button / Storefront | a development store with its own Storefront token | `sdks.shopifycdn.com`, `*.myshopify.com`, `cdn.shopify.com` | never add to cart |
| Snipcart | test API key (`test` mode toggle) | `cdn.snipcart.com`, `app.snipcart.com` | never add to cart |
| Square / PayPal buttons | sandbox application credentials | provider docs | never click buy |
| Etsy / external marketplace links | n/a (outbound links) | none | link check only |

## Appendix B — Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `netlify build` says the site is not linked | `NETLIFY_SITE_ID`/`NETLIFY_AUTH_TOKEN` not in the job's `env` | Check the job-level `env:` block and the GitHub variable names |
| Preview deployed but tests hit a 401 | Basic auth enabled on staging without `STAGING_BASIC_AUTH` in GitHub secrets | Add the secret; confirm `httpCredentials` in `playwright.config.ts` |
| PR never becomes mergeable | Required check name in the ruleset does not match the job `name:` | Rename one side; names are case-sensitive |
| "Review deployments" button never appears | Plan does not support required reviewers, or the approver is not in the environment | Check Settings → Environments → production; fall back to `workflow_dispatch` promotion |
| Lighthouse score flaps between runs | Preview cold start, third-party scripts | `numberOfRuns: 3` (median is used); keep performance at `warn`; assert on `accessibility`/`best-practices` |
| `npm ci` fails with lockfile mismatch | `package.json` changed without updating the lockfile | Run `npm install` locally, commit the lockfile; never `npm install` in CI |
| Staging certificate pending | DNS not propagated or Cloudflare proxy on | Wait, or set the record to DNS-only; click Verify DNS in Netlify |
| Checkout broken after CSP enforcement | Provider origin missing from CSP | Revert to report-only immediately (PR), add the origin, retest on staging |
| Production smoke failed but the site looks fine | Test asserted something environment-specific (`noindex`, header) | Check `DEPLOY_ENV` on the production site; check `_headers` merge; fix the test if it is wrong, in a PR |
| Rollback restored an old deploy but the next merge redeployed the bug | Rollback is not a code change | Merge a `git revert` PR after every rollback |
| `netlify deploy` uploads an empty or stale directory | Build step skipped or publish dir mismatch | Keep `netlify build` before `deploy --no-build`; check `[build].publish` equals the framework's output dir |
| `gitleaks-action` fails asking for a licence | Repo belongs to a GitHub organization | Personal accounts need no licence; for organizations request the free `GITLEAKS_LICENSE` or run the `gitleaks` binary directly in the step |

## Appendix C — Suggested PR sequence

1. `docs: discovery report` (Phase 0)
2. `chore: repo hygiene (nvmrc, gitignore, editorconfig, env example, CODEOWNERS, PR template, dependabot)`
3. `ci: baseline quality/build/secrets workflow`  → then apply the ruleset
4. `chore: netlify.toml as source of truth + postbuild env script + security headers (CSP report-only)`
5. `test: playwright config and smoke tests` (runs against a local `netlify dev` in CI until previews exist)
6. `ci: preview deploys, lighthouse, link check, sticky comment`
7. `ci: deploy workflow (staging, approval gate, production behind flag, rollback, release)`
8. `style: one-time prettier formatting pass` then `chore: husky + lint-staged + commitlint + PR title check` (formatting PR kept separate so the tooling diff stays readable)
9. `docs: architecture, environments, deploying runbook, contributing, README badges`
10. Cutover (no code change; variables and Netlify settings) → `docs: evidence log`

## Appendix D — References (official docs; search by title if a URL has moved)

- Netlify deploy contexts and `netlify.toml`: https://docs.netlify.com/site-deploys/overview/ and https://docs.netlify.com/configure-builds/file-based-configuration/
- Netlify CLI `build` / `deploy` / `env` / `api`: https://cli.netlify.com/
- Netlify environment variables and contexts: https://docs.netlify.com/environment-variables/overview/
- Netlify headers and redirects: https://docs.netlify.com/routing/headers/ and https://docs.netlify.com/routing/redirects/
- Netlify Edge Functions: https://docs.netlify.com/edge-functions/overview/
- Netlify API (`getSite`, `restoreSiteDeploy`): https://open-api.netlify.com/
- GitHub rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
- GitHub Actions environments and required reviewers: https://docs.github.com/en/actions (search "Managing environments for deployment")
- GitHub Actions security hardening (SHA pinning, least-privilege `permissions`): https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
- Dependabot configuration: https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file
- Playwright in CI: https://playwright.dev/docs/ci
- Lighthouse CI: https://github.com/GoogleChrome/lighthouse-ci and https://github.com/treosh/lighthouse-ci-action
- gitleaks: https://github.com/gitleaks/gitleaks · lychee: https://github.com/lycheeverse/lychee-action
- Conventional Commits: https://www.conventionalcommits.org/ · release-please: https://github.com/googleapis/release-please-action
- OWASP Secure Headers Project: https://owasp.org/www-project-secure-headers/ · check with https://securityheaders.com/
