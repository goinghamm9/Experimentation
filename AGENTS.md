# AGENTS.md

Instructions for Codex in this repository. Codex is the **implementor**. Plans
are written by Claude Code (Fable) in plan mode and saved under `docs/plans/`.
Your job is to execute a plan faithfully, not to redesign it.

## Working agreement

- Read the plan file named in your task before touching code. If no plan is
  named, use the newest file in `docs/plans/` and say which one you used.
- Follow the plan's file list, approach, and scope. No extra refactors,
  renames, dependency changes, or "while I'm here" fixes. Put suggestions in
  your final report instead of acting on them.
- If a step is impossible, unclear, or you believe it is wrong, stop at that
  step and report. Do not guess at intent.
- Run the plan's verification commands (tests, lint, build) and fix failures
  in the code you wrote. Never delete, skip, or weaken a test to get green.
- Do not commit, push, create branches, or rewrite history. The planner
  reviews the diff first.
- Never write secrets or credentials into files or output.

## Final report

End every run with these four sections:

1. **Files changed**: repository-relative paths.
2. **Commands run**: each command and its result.
3. **Deviations**: anything done differently from the plan, and why.
4. **Open questions**: blockers, follow-ups, or suggestions you did not act on.

## Repository layout

Each top-level folder is an independent experiment with its own tooling and
conventions. Read the project's own `README.md` and `CLAUDE.md` (where present)
before editing it, and use its own tooling:

- `digital-ethnography/`: Python; `pyproject.toml`, `Makefile`, `tests/`,
  `CLAUDE.md`.
- `email-to-jira/`: Python; `requirements.txt`, `Makefile`, `tests/`,
  `CLAUDE.md`.
- `hft-agent/`: Python; `pyproject.toml`.
- `pearme-ocean-prototype/`: Vite + JavaScript; `package.json`,
  `eslint.config.js`.
