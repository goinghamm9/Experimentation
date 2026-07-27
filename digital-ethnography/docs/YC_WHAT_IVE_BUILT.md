# "What have you built?" — draft material for the Quantu YC application

*Working draft. First person, founder voice. Pick the length that fits the field; cut freely.
Everything here is true of the repo as of commit `f6f6074` — nothing is aspirational dressed as shipped.*

---

## Short version (~100 words)

I built Quantu — a research-measurement engine that makes AI-assisted qualitative research auditable.
It runs ethnographic studies through a hard ethics gate (consent, PII redaction, k-anonymity,
tamper-evident audit log), codes data with panels of LLM coders whose citations are mechanically
verified against the source — a fabricated quote cannot reach a result — and scores validity only
against human-coded gold samples, never against model agreement. The statistics layer (saturation
estimation, Krippendorff's α, Cultural Consensus Theory, effective-sample-size deflation) includes what
appear to be the only Python implementations of several standard estimators. 107 tests, fully offline,
zero dependencies in the core.

---

## Longer version (~250 words)

Quantu is a system for digital ethnographic research whose numbers can be trusted — built because
AI insight tools ship confidence, not calibration.

**What's working today** (Python, 107 passing tests, runs fully offline):

- **An ethics kernel as a hard gate, not a checklist.** No observation reaches analysis without passing
  consent, purpose limitation, data minimisation, retention, and PII redaction. Every keep/drop/redact
  decision lands in a SHA-256 hash-chained audit log with tamper detection. Right-to-erasure cascades;
  personas carry a k-anonymity floor.
- **LLM coders that are treated as claims, not oracles.** Every label must cite a verbatim span from the
  source, verified mechanically — the one hallucination gate that closes without ground truth. Invented
  codes are refused; refusals are counted as coverage loss rather than becoming silent absences.
- **A measurement layer nobody has productised.** Saturation as an auditable number (Good–Turing/Chao1),
  Krippendorff's α, Cultural Consensus Theory with random-matrix noise thresholds, and effective sample
  size that treats correlated model coders honestly — three same-family coders count as ~one, not three.
  Several of these estimators have no other Python implementation.
- **A blind human gold-coding surface**, keyboard-driven, served from the standard library, feeding the
  only validity claim the system makes: agreement with humans on a probability sample.

The design was stress-tested the way I intend to run the company: adversarial fact-checking reversed
four of my own architectural decisions, and my test suite caught an arithmetic error in my source
literature. Both kinds of correction are recorded in the repo, not papered over.

---

## One-liners to reuse anywhere

- "Estimators, not vibes: every research claim ships with its own error rate."
- "A fabricated quote cannot move a number — citations are verified mechanically before a label counts."
- "Model agreement routes disagreement to humans; only human-coded gold supports a validity claim."
- "The ethics gate is architecture: nothing un-consented ever reaches analysis, and erasure is a
  bounded graph walk, not an archaeology project."

## Numbers that are safe to quote

- 107 automated tests, offline, zero-dependency core
- 13 commits of working system + ~50 pages of researched, adversarially-verified architecture
- 3 estimator families implemented that have **no other Python implementation**
  (Cultural Consensus Theory, generalizability-theory scaffolding, PPI-ready panel design)
- 5-version formal-methods corpus integrated; 1 arithmetic error in it found by my test suite

## What NOT to claim (yet)

- A running web product, users, or revenue — the platform is designed, not deployed
- "Supports N languages" — language support is tiered and this is documented honestly
- Any dollar figures from the research — they are directional and marked unverifiable
