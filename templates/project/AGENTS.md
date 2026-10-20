# AGENTS.md

The one source of agent rules for this project, in every tool. `CLAUDE.md` and `GEMINI.md` only point here. These rules hold even where the owner's user rules aren't installed (CI, cloud, another machine).

## What this project is

One paragraph: what it makes, for whom, and what done looks like. Replace this line.

## Map

| Part | What it holds |
| --- | --- |
| `AGENTS.md` | These rules. 60 lines max |
| `backlog/` | Tasks (Backlog.md): To Do, In Progress, Done. Requirements and plan live in the task. Never run `backlog init` here; if a tool must, use `--agent-instructions none` |
| `raw/` | Sources, added as `YYYY-MM-DD-slug.ext`, never edited |
| `wiki/` | What we know: pages, `index.md`, `log.md`. Lessons are pages tagged `lesson` |
| `archive/` | Old raw files, log years and cut sections. We archive, never delete |
| `scripts/repo-check.py` | gitleaks, wiki lint, STE prose, then this project's own check. Git runs it before every commit |

Add a row for each code or media folder this project adds.

## Commands

- Check before done: `python scripts/repo-check.py`
- Project check (tests or lint): set it in `.agents/check-command`, one line. Leave the file empty if there's none.

## Habits

- Run repo-check and paste its output before calling work done.
- One task per session. Start a fresh session after two failed fixes.
- Interview and write a spec only for multi-file or uncertain work; a one-sentence change skips the plan.
- Anything waiting on the owner gets the sign-off tag on its backlog task (`needs-owner`, unless the user rules name another).
- Knowledge stays in this project. Never copy content in from, or out to, another project.
- Git is the source of truth. Cloud shared files are drafts only; move anything worth keeping into the repo.

## Commits and pull requests

- Code: Conventional Commits. Wiki: `<move> | <subject>`.
- Code and rule changes go on a branch (`<type>/<short-name>`) and through a PR using `.github/pull_request_template.md`. The owner's yes merges.
- `backlog/`, `wiki/`, `raw/` and `archive/` commit straight to main.
- A new GitHub repo gets the `protect main` ruleset from home's wiki (`how-a-project-works.md#protect-main-on-github`).

## Knowledge

The wiki follows conventions version 2 from home's `wiki` skill (`reference/conventions.md`). Use the `wiki` skill to drop, ingest, ask and tidy, and `learn-from-work` when corrected.
