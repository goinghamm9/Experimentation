# Plans

Claude Code's plan mode writes plan files here (see `plansDirectory` in
`.claude/settings.json`). Each plan is the hand-off contract between the
planner (Claude Code running Fable) and the implementor (Codex).

A plan is ready to hand off when it has:

1. **Goal**: what changes and why, in one paragraph.
2. **Files**: every file to create or modify, by path.
3. **Steps**: ordered, concrete, one change per step.
4. **Verification**: the exact commands that prove it works (tests, lint, build).
5. **Out of scope**: what Codex must not touch.

Hand it off with `/codex-implement` (uses the newest file here) or
`/codex-implement docs/plans/<file>.md`.

Plans are committed on purpose: they document why the code looks the way it
does. Delete a plan when the work it describes has been superseded.
