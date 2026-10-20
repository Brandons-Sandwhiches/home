# AGENTS.md

The one source of agent rules for this repo, in every tool. `CLAUDE.md` and `GEMINI.md` only point here.

## What this repo is

`home` is the generic layer every project gets: skills, the project template, the home base script, the eval runner and the catalog. No names, machines, paths or preferences; those live in a separate private repo next to it. How it fits together: [one diagram](wiki/how-a-project-works.md#how-a-project-works).

## Map

| Path | What lives there |
| --- | --- |
| `skills/<bucket>/<skill>/` | Skills: `SKILL.md`, `agents/openai.yaml`, and any `scripts/` or `reference/` |
| `templates/project/` | What a new project gets: AGENTS.md, raw/, wiki/, backlog/, archive/, repo-check, commit gate, PR template |
| `templates/work/` | The home base folder's AGENTS.md |
| `scripts/dashboard.py` | "What's up" and `work/dashboard.html`, read from every backlog |
| `scripts/repo-lint.py`, `scripts/repo-check.py` | This repo's checks. Git runs repo-check before every commit |
| `scripts/prose-score.mjs`, `scripts/prose-check.mjs` | The STE prose scorer and its commit gate |
| `evals/run.py` | The eval runner; the golden tasks live in the private repo |
| `wiki/` | How home works, the catalog of extras |
| `backlog/` | Home's own follow-ups. Tag `needs-owner` when a task waits on the owner |

## Rules

- **Skills** follow the [mattpocock/skills](https://github.com/mattpocock/skills) layout. Frontmatter has `name` and `description`. A user-invoked skill sets `disable-model-invocation: true` in SKILL.md and `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. A skill bundles what it needs and refers to it relative to its own folder. List each skill once in its bucket README.
- **Wiki rules** have one copy: `skills/knowledge/wiki/reference/conventions.md`. Link to it; never restate it.
- **Generic only.** `repo-lint` fails on personal details. Personal wording goes in the private repo.
- **Stay small.** AGENTS.md 60 lines, wiki pages 300 lines, one line per catalog item. New ideas go to the [catalog](wiki/catalog.md#catalog) first.
- **Writing:** plain words, no em-dashes.

## Changing home

- Home is live: tools load the clone in the workspaces folder. Never edit that clone. Work in a separate worktree on a branch, and open a PR. The owner's yes merges (squash); the live clone only pulls.
- Every change to a skill or rule re-runs its tagged golden tasks on main vs the branch: `python evals/run.py <golden-tasks.yaml> --base main`. Paste the delta into the PR. Additions need a clear win, removals no regression, wording-only no drop.
- Cheap models may draft a skill; a top model reviews only the diff and the eval results.
- Run an ECRS cut pass (`ecrs-review`) on code and rule PRs before merge.

## Before you call it done

```sh
python scripts/repo-check.py
```

It runs gitleaks, this repo's lint (`.agents/check-command`) and the wiki lint. Paste the output.
