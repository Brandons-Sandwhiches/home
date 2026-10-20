# AGENTS.md (home base)

This folder is the home base: the front door to every project in the workspaces folder. It is not a project and has no backlog of its own. `CLAUDE.md` and `GEMINI.md` only point here.

## "What's up"

When asked "what's up", "status", or how things stand:

1. Run `python ../home/scripts/dashboard.py --print` (add `--tag <tag>` if the user rules name a sign-off tag). It reads every project's backlog read-only and rebuilds `dashboard.html` here.
2. Answer from its output in this order: **Needs you** (every sign-off item), **Active** (per project: left off, next 3), **Parked** (idle 30+ days, suggest archiving). One line each. Link `dashboard.html`.
3. Work and client spaces: give only their needs-you count and titles. Never open or quote their content.

If the script can't run, read each project's `backlog/tasks/` yourself and give the same three sections.

## Rules here

- Read-only toward projects. To work on one, open a session in its folder.
- Quick one-off tasks that belong to no project can happen here; anything worth keeping goes into a project.
- Never copy content between projects.
