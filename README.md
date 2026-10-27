# home

Generic agent tooling every project starts from. It works the same way in Claude Code, Codex and opencode. It holds a project template (AGENTS.md, wiki, backlog), a few skills that passed their evals and a home base dashboard. A catalog lists the extras you can switch on.

Start with [the diagram](wiki/how-a-project-works.md#how-a-project-works). Agents start at [AGENTS.md](AGENTS.md).

## Use it

1. Clone this repo into your workspaces folder as `home`, next to your projects.
2. Link the skills into each tool with [skillshare](https://github.com/runkids/skillshare).
3. Start a project: copy `templates/project/` into a new folder and run `git init -b main`. Before the first task, set `project_name` and `task_prefix` in `backlog/config.yml` (the prefix is letters only and cannot change later; tested with Backlog.md 1.55.3). Then fill in "What this project is".
4. Make a `work` folder from `templates/work/` and ask any tool there "what's up".

## Skills

- [knowledge](skills/knowledge/README.md): wiki, learn-from-work.
- [productivity](skills/productivity/README.md): discovery interview.
- [review](skills/review/README.md): agent-review, ECRS review.

Everything else: [catalog](wiki/catalog.md#catalog).
