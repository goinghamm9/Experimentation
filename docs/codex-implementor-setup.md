# Codex as implementor, Fable as planner

This repository is configured so that Claude Code, running Claude Fable 5.1,
plans and reviews, while OpenAI Codex writes the code. The bridge is OpenAI's
[Codex plugin for Claude Code](https://github.com/openai/codex-plugin-cc),
which wraps the local `codex` CLI and exposes it inside Claude Code as slash
commands and a `codex:codex-rescue` subagent.

## What is in the repo

| File | Purpose |
| :--- | :--- |
| `.claude/settings.json` | Registers the `openai-codex` marketplace, enables `codex@openai-codex`, sets the model to `fable`, starts sessions in plan mode, writes plan files to `docs/plans/`, and runs the cloud login hook. |
| `.claude/skills/codex-implement/SKILL.md` | The `/codex-implement` hand-off: picks the plan, sends it to Codex, waits, then verifies the diff and runs the plan's checks. |
| `.claude/hooks/codex-login.sh` | SessionStart hook. In Claude Code cloud sessions only, installs Codex if missing and logs in with `OPENAI_API_KEY`. No-op locally. |
| `CLAUDE.md` | Tells Claude Code it is the planner: write plans, delegate, verify, never implement by hand. |
| `AGENTS.md` | Tells Codex it is the implementor: follow the plan, no scope creep, run the checks, report, never commit. |
| `.codex/config.toml` | Codex project config: reasoning effort `high`, and a fallback so Codex reads each experiment's `CLAUDE.md` as conventions. |
| `docs/plans/` | Where plan mode saves plans and where Codex reads them. |

## One-time setup on your machine

1. **Claude Code v2.1.257 or later** (needed for Fable 5.1): `claude update`.
2. **Node.js 18.18 or later** for the plugin scripts.
3. **Codex CLI**, signed in with a ChatGPT plan or an API key:

   ```bash
   npm install -g @openai/codex
   codex login            # browser sign-in, or:
   codex login --device-auth
   printenv OPENAI_API_KEY | codex login --with-api-key
   ```

4. **Open the repo in Claude Code and trust the folder.** The project
   settings register the marketplace. If the plugin is reported as not
   installed, run the command Claude Code shows, or:

   ```bash
   claude plugin marketplace add openai/codex-plugin-cc
   claude plugin install codex@openai-codex --scope project
   ```

   Inside a session the equivalents are `/plugin marketplace add
   openai/codex-plugin-cc`, `/plugin install codex@openai-codex`, then
   `/reload-plugins`.

5. **Check the plugin**: `/codex:setup`. It confirms Node, npm, Codex, and
   login, and offers to install Codex if npm is present.
6. **Trust the project for Codex** so `.codex/config.toml` applies: run
   `codex` once inside the repo and accept the trust prompt, or add to
   `~/.codex/config.toml`:

   ```toml
   [projects."/absolute/path/to/Experimentation"]
   trust_level = "trusted"
   ```

   Until then Codex uses your user-level config and ignores the project file.

## The loop

1. **Plan (Fable).** Sessions start in plan mode. Describe the outcome you
   want. Claude explores and writes a plan to `docs/plans/`. Edit it with
   `Ctrl+G` if needed, then approve it.
2. **Hand off.** Run `/codex-implement` (newest plan) or
   `/codex-implement docs/plans/<file>.md`. The skill sends Codex a prompt
   that points at the plan and `AGENTS.md`, in the background for anything
   larger than a couple of files.
3. **Implement (Codex).** Codex edits the checkout with a workspace-write
   sandbox, runs the plan's verification commands, and reports files
   changed, commands run, deviations, and open questions. It does not commit.
4. **Verify (Fable).** Claude reads the diff against the plan and reruns the
   checks. Problems go back to Codex with
   `/codex-implement --resume <exact problem>`. The same failure twice stops
   the loop and asks you.
5. **Commit** when you are happy with the diff.

The `/codex-implement` skill is a thin layer over the plugin. The manual
equivalents are:

| Command | What it does |
| :--- | :--- |
| `/codex:rescue --background --fresh <task>` | Start a new Codex task with write access. |
| `/codex:rescue --resume <task>` | Continue the latest Codex thread for this repo. |
| `/codex:status [id] [--wait]` | Progress of running and recent jobs. |
| `/codex:result [id]` | Final output of a finished job, with the Codex session id for `codex resume <id>`. |
| `/codex:cancel [id]` | Stop a background job. |
| `/codex:review [--base main]` | Read-only Codex review of the working tree or branch. |
| `/codex:adversarial-review <focus>` | Read-only review that challenges the design. |
| `/codex:transfer` | Copy the Claude session into a Codex thread. |
| `/codex:setup --enable-review-gate` | Optional Stop hook that has Codex review every Claude turn. It can loop and burn usage; leave it off unless you are watching. |

Plain language works too: "Ask Codex to implement docs/plans/x.md" routes to
the same subagent.

## Claude Code on the web

Cloud sessions start from a fresh clone, so the repo carries the setup:
`.claude/settings.json` installs the plugin at session start and the
SessionStart hook installs and logs in Codex. Three things must be set on the
cloud environment (claude.ai/code, environment settings):

1. **Network access**: choose **Custom**, add `api.openai.com`, and tick
   "Also include default list of common package managers" so npm still
   works. The default Trusted level blocks OpenAI's API. Browser sign-in is
   not possible in a cloud VM, so an API key is required there.
2. **Environment variable**: `OPENAI_API_KEY=<key>`. Anyone who can use the
   environment can read it, so use a dedicated key with a spend limit.
3. **Optional setup script** to skip the per-session install:

   ```bash
   #!/bin/bash
   npm install -g @openai/codex || true
   ```

Then in a cloud session, `/codex:setup` should report Codex as ready.
Pick the model from the web UI's model selector; `/model fable` also works in
a session.

## Tuning

- **Codex model and effort**: edit `.codex/config.toml`. `codex debug models`
  lists the slugs your account can use. The plugin accepts
  `--model <slug>` and `--effort none|minimal|low|medium|high|xhigh` per
  task as overrides.
- **Fable**: selected by `"model": "fable"` in `.claude/settings.json`;
  `/model fable` or `claude --model fable` does the same per session. On some
  plans Fable bills to usage credits and Claude Code asks once before it
  does.
- **Skip plan mode** for a quick session: `claude --permission-mode auto`
  (or press `Shift+Tab`). The hand-off still works from any mode.
- **Reviews**: Fable reviews Codex's work by default. For an independent
  second opinion use `/codex:adversarial-review`, which is read-only.
