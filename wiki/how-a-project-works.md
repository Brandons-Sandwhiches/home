---
title: How a project works
tags: [overview, diagram]
sources: [wiki/how-a-project-works.svg, templates/project/AGENTS.md, scripts/dashboard.py]
updated: 2026-10-20
---

# How a project works

![How a project works with home](how-a-project-works.svg)

## In words

- **home** holds the tools: skills, the project template, the home base script and the eval runner. It changes only through a branch, the evals and the owner's yes.
- **The private repo** holds the owner's user rules (tone, autonomy, session start and end, the sign-off tag), the golden eval tasks and the decision record.
- **skillshare** links the skills and the user rules into every tool, so Claude Code, Codex and opencode behave the same. Details: [scopes](concepts/scopes.md#where-each-lives).
- **A project** is a copy of `templates/project/`: AGENTS.md (the map and habits), `backlog/`, `raw/` into `wiki/`, and `archive/`.
- **Each session** starts with where things left off and the next 3 tasks, then does one task. It ends by updating the backlog, tagging what needs the owner, logging skill use and rebuilding the dashboard.
- **The work folder** is the front door. "What's up" in any tool, or `dashboard.html`, shows Needs you, Active and Parked across every project. More extras: [catalog](catalog.md#catalog).

## Where the tools look

Every tool checks a fixed folder in the user's home on every launch, whatever project is open. skillshare fills those folders with links, so one real copy in home serves every project, like `npm link`.

```
~/
├─ workspaces/home/skills/         the one real copy of each skill
├─ workspaces/<private repo>/user/AGENTS.md   the one real copy of the user rules
├─ .claude/skills/                 links to home's skills (Claude Code)
├─ .claude/CLAUDE.md               link to the user rules
├─ .agents/skills/                 links to home's skills (Codex, opencode, Gemini CLI)
├─ .codex/AGENTS.md                link to the user rules
└─ .config/opencode/AGENTS.md      link to the user rules
```

A project's own `.claude/skills` or `.agents/skills` adds skills for that project only. Every path per tool: [scopes](concepts/scopes.md#where-each-lives).

## Protect main on GitHub

Apply this ruleset once, when you create a repo on GitHub. In the repo, open Settings, then Rules, then Rulesets, then a new branch ruleset.

| Setting | Value |
| --- | --- |
| Ruleset name | `protect main` |
| Enforcement status | Active |
| Bypass list | Empty, so a tool with the owner's login cannot rewrite main either. To change main in an emergency, switch the rule off for a minute. |
| Target branches | Add target, then include the default branch |
| Restrict deletions | On. Nobody can delete main. |
| Block force pushes | On. No history rewrites on main. |
| Require linear history | On. It matches squash merges. |

Leave these off, each for one reason:

- **Require a pull request:** it would block backlog and wiki commits, which go straight to main.
- **Require status checks:** the repo has no CI yet. Turn it on after you decide on CI.
- **Signed commits:** agents cannot sign without key setup on every machine.
- **Restrict creations or updates, deployments, code scanning, quality and coverage:** they do not fit a solo repo.
- **Copilot code review:** it costs credits, and the review agents do this job.
