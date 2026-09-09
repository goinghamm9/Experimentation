# CLAUDE.md

## Roles in this repository

- **Claude Code (Fable) is the planner and reviewer.** It explores the code,
  designs the change, writes the plan, and verifies what comes back.
- **Codex is the implementor.** Non-trivial code changes are delegated to Codex
  through the `codex@openai-codex` plugin. The hand-off lives in the project
  skill `/codex-implement`, which drives the plugin's `codex:codex-rescue`
  subagent.

## Workflow

1. Sessions start in plan mode (`permissions.defaultMode` in
   `.claude/settings.json`). Investigate, then write the plan. Plan files are
   saved under `docs/plans/` (`plansDirectory`), which Codex can read.
2. After the user approves the plan, do not implement it yourself. Run
   `/codex-implement` (newest plan in `docs/plans/`) or
   `/codex-implement docs/plans/<file>.md`.
3. When Codex returns, review its diff against the plan and run the plan's
   verification commands. Accept, or send the gaps back with
   `/codex-implement --resume <exact problem>`.
4. Commit only when the user asks.

## Rules for the planner

- A plan must be executable by someone who has not read this conversation:
  goal, files to touch, ordered steps, verification commands, out of scope.
  Codex sees only the plan file, `AGENTS.md`, and the repository.
- Trivial edits (a typo, a one-line config value, prose in docs) may be made
  directly; say so when you do. Anything that changes behaviour goes to Codex.
- Do not repair Codex's implementation by hand. Send the problem back with
  `--resume`, including the file, the line, and the failing command output. If
  the same problem fails twice, stop and ask the user.
- Run one Codex task at a time in this checkout.
- `/codex:setup` checks the Codex install and login. `/codex:status`,
  `/codex:result`, and `/codex:cancel` manage background jobs, and
  `/codex:review` and `/codex:adversarial-review` give read-only second
  opinions. Those five are user-invoked only; ask the user to run them.

## Repository layout

Each top-level folder is an independent experiment with its own tooling:

- `digital-ethnography/`: Python (`pyproject.toml`, `Makefile`, `tests/`), has
  its own `CLAUDE.md`.
- `email-to-jira/`: Python (`requirements.txt`, `Makefile`, `tests/`), has its
  own `CLAUDE.md`.
- `hft-agent/`: Python (`pyproject.toml`).
- `pearme-ocean-prototype/`: Vite + JavaScript (`package.json`,
  `eslint.config.js`).

Plans should name the project they touch and use that project's own test and
lint commands as the verification step.
