---
name: codex-implement
description: Hand an approved plan to Codex (the implementor) through the Codex plugin, then verify the result as the planner. Use after a plan in docs/plans/ is approved, or when the user asks Codex to implement, fix, or continue something.
argument-hint: "[docs/plans/<file>.md] | [--resume <what to fix or continue>]"
allowed-tools: Skill, Agent, Bash(node:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(ls:*)
---

# Hand implementation to Codex

You are the planner and reviewer. Codex is the implementor. This skill sends
work to Codex through the `codex@openai-codex` plugin and then checks what
came back. Do not write the implementation yourself at any point.

Arguments: `$ARGUMENTS`

## 1. Work out what Codex should do

- If the arguments start with `--resume`, this is a follow-up on the current
  Codex thread (a fix, a review finding, the next step). The instruction is
  the rest of the arguments. Go to step 3 and use the follow-up form.
- If the arguments are a path to a markdown file, that file is the plan.
- Otherwise use the newest plan: `ls -t docs/plans/*.md | grep -v README.md | head -1`.
- If the approved plan exists only in this conversation, write it to
  `docs/plans/YYYY-MM-DD-<slug>.md` first. Codex runs as a separate process in
  this checkout and sees only that file, `AGENTS.md`, and the repository.
- Confirm the plan file contains: goal, files to touch, ordered steps,
  verification commands, out of scope. Add whatever is missing before the
  hand-off. A plan that says "add tests" without naming the command to run
  them is not ready.

## 2. Preflight

- Run `git status --short`. Note what is already modified so Codex's changes
  can be told apart afterwards. If the tree has unrelated uncommitted work,
  tell the user before continuing.
- Run one Codex task at a time in this checkout. If the user mentioned a
  Codex job that is still running, wait for it or ask them to `/codex:cancel`
  it first. `/codex:status`, `/codex:result`, and `/codex:cancel` are
  user-invoked only; you cannot call them yourself.

## 3. Hand off

Invoke the plugin's `codex:rescue` command through the Skill tool. Choose the
execution flag:

- `--wait` when the plan touches at most two files and has no test suite to
  run.
- `--background` for everything else. Implementation runs can take many
  minutes.

Fresh plan (replace the path):

```text
--background --fresh Implement the plan in docs/plans/<file>.md in this repository. Read AGENTS.md first and follow it. Follow the plan as written: same files, same approach, same scope. Do not redesign, refactor beyond the plan, or add extras. If a step is impossible, ambiguous, or wrong, stop at that step and report instead of improvising. Run the verification commands listed in the plan and fix failures in the code you wrote. Do not commit. End with the four-section report from AGENTS.md: files changed, commands run, deviations, open questions.
```

Follow-up on the same Codex thread:

```text
--background --resume <the exact problem: file, line, failing command and its output, what correct looks like>. Follow AGENTS.md. Do not commit. End with the four-section report.
```

Rules:

- Point at the plan file. Never paste the plan text into the prompt.
- Do not add `--model` or `--effort`; the project's `.codex/config.toml` sets
  them. Pass them only if the user asked for a specific model or effort.
- If the plugin reports that Codex is missing or not logged in, stop and tell
  the user to run `/codex:setup`.

## 4. Wait for Codex

- With `--background`, the rescue subagent runs in the background and its
  result arrives when it finishes. Do not poll with sleep loops. Let the user
  know the hand-off started and end the turn if there is nothing else to do.
- If the result says a job "started in the background as task-…", the job is
  detached and only the user can poll it. Give them the id and ask them to
  run `/codex:status <id>` and then `/codex:result <id>`; continue at step 5
  when the result is in.
- If a hand-off appears to time out, ask the user to check `/codex:status`
  before assuming failure; the job may still be running.

## 5. Verify as the planner

When Codex's report is in:

1. Show the user Codex's report as it came back. Keep its caveats and open
   questions; do not paraphrase them away.
2. Run `git status --short` and `git diff --stat`, then read the full diff of
   every changed file.
3. Check the diff against the plan step by step: missing steps, extra scope,
   wrong files, weakened or skipped tests, secrets, risky shell or network
   calls, changes outside the project the plan named.
4. Run the plan's verification commands yourself. Do not trust the report's
   claim that they passed.
5. Decide:
   - **Done**: summarise what was implemented, what you verified, and what is
     left (usually: the user reviews and commits).
   - **Gaps or failures**: do not fix them yourself. Go back to step 3 with
     the follow-up form and describe the exact problem. If the same problem
     fails twice, stop and ask the user how to proceed.
   - **Plan was wrong**: return to planning. Update the plan file, then start
     a fresh hand-off with `--fresh`.

For a second opinion on a finished change, offer `/codex:review --base <branch>`
or `/codex:adversarial-review`. Both are read-only.
