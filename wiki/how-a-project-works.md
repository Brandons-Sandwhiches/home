---
title: How a project works
tags: [overview, diagram]
sources: [wiki/how-a-project-works.svg, templates/project/AGENTS.md, scripts/dashboard.py]
updated: 2026-10-27
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

Set the rulesets once for the whole GitHub org. Every repo then gets them, new repos too. Plans decide what works:
- **Org rulesets** need GitHub Team or Enterprise.
- **Repo rulesets** work on public repos on any plan. Private repos need a paid plan (Pro, Team or Enterprise).
- **Restrict branch names** may need a higher plan than the other rules. If the form lacks it, skip ruleset 3.
- A repo under a personal account gets only its own repo rulesets.

Where: the org page, Settings, then Repository (under "Code, planning, and automation"), then Rulesets, then New ruleset, then New branch ruleset. A bypass list applies to a whole ruleset. A single ruleset would let the admin force-push as well, so the rules split.

### Ruleset 1: `protect main`

| Setting | Value |
| --- | --- |
| Enforcement status | Active |
| Bypass list | Empty, so a tool with the owner's login cannot rewrite main either. To change main in an emergency, switch the rule off for a minute. |
| Target repositories | All repositories |
| Target branches | Add target, then include the default branch |
| Restrict deletions | On. Nobody can delete main. |
| Block force pushes | On. No history rewrites on main. |
| Require linear history | On. It matches squash merges. |

### Ruleset 2: `PRs for others`

| Setting | Value |
| --- | --- |
| Enforcement status | Active |
| Bypass list | Repository admin, set to "Always allow". The owner and their agents can still commit backlog and wiki straight to main. The same bypass lets them push code to main without a PR. We accept that. The PR rule for code is a habit in AGENTS.md, and the gate for the owner is the owner's own yes. |
| Target repositories | All repositories |
| Target branches | Add target, then include the default branch |
| Require a pull request | On, with 1 approval. Anyone else who contributes must open a PR. |
| Require status checks | Add `gitleaks` and `lint`. Turn this on only when every covered repo has the CI workflow, or its PRs wait for ever. |

### Ruleset 3: `branch names`

If the form has no "Restrict branch names" rule, skip this ruleset. Then the `repo-check --pre-push` hook is the only name check, and anyone can bypass it with `--no-verify`.

| Setting | Value |
| --- | --- |
| Enforcement status | Start with Evaluate, check Insights for blocked names, then switch to Active |
| Bypass list | Empty, except any bot app you use, such as Dependabot |
| Target repositories | All repositories |
| Target branches | Add target, include all branches, then exclude the patterns `main`, `dependabot/**` and `renovate/**` |
| Restrict branch names | On, "Must match a given regex pattern", with the pattern below |

```
^([a-z][a-z0-9]*-[0-9]+(\.[0-9]+)*-[a-z0-9-]+|claude/.+)$
```

The pattern checks the shape only. `repo-check --pre-push` checks the exact prefix of each project. The ruleset blocks every other name, including `patch-1` from the web editor. A repo whose default branch is not `main` (for example `master`) needs its own exclusion for that branch.

### Leave these off

- **Signed commits:** agents cannot sign without key setup on every machine.
- **Restrict creations or updates, deployments, code scanning, quality and coverage:** they do not fit a solo repo.
- **Copilot code review:** it costs credits, and the review agents do this job.

### Keep a copy and check it

- Export each ruleset (the ruleset page, the three-dot menu, Export ruleset) and keep the JSON in the org's `.github` repo under `rulesets/`.
- Make the test repo yourself: a new private repo inside the org, with no real work in it. Run `git remote -v` first and check that the URL is the test repo. A personal repo is not covered by the org rulesets, so the test would rewind its main.
- Push two commits to its main, then run `git push --force origin HEAD~1:main`. GitHub must refuse it with a message that names the ruleset (`GH013`).
- Test the names in the same repo. The local hook refuses a bad name first, so add `--no-verify` to each push: `git push --no-verify origin HEAD:bad-name` must fail. `git push --no-verify origin HEAD:task-1-x` and `HEAD:claude/x` must pass. A refusal from GitHub names the ruleset (`GH013`); a refusal without that text came from somewhere else. Delete any branch that got through.
- Check that the admin can still push a backlog or wiki commit straight to main.
- Delete the test repo when done.
