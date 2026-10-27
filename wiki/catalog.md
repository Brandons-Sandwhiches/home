---
title: Catalog
tags: [catalog, extras]
sources: [wiki/how-a-project-works.md]
updated: 2026-10-20
---

# Catalog

Everything that isn't in the basics. Switch an item on in one project; it moves into home only after three projects need it and it passes the [evals](../evals/README.md). Before any client space: check the client allows its data on a personal machine and personal GitHub.

## Items

| Item | What it does | When you'd want it | How to switch it on |
| --- | --- | --- | --- |
| Code kit | Bug fixes start with a failing test, CI runs tests and repo-check on every PR, coverage may not drop | A code repo with real users or a test suite | Add a GitHub Actions workflow calling `scripts/repo-check.py`, and a coverage step picked for the language |
| Drift sync | Opens a branch in each repo when the template's baseline files change | Three or more repos use the baseline | Write a script that diffs each repo's copies against `templates/project/` |
| Guard hooks | Blocks reading secret files and force-pushes in the tool itself | Agents run unattended | Add a deny list to the tool's settings (for example `.claude/settings.json` permissions) |
| Ponytail | A lean second review that returns a delete list | A big change you want trimmed | Track the upstream ponytail skill in skillshare, pinned to a commit |
| Bootstrap | Sets up a new machine: clone home, install tools, link skills | A second machine joins | Write one script per OS; it reports each step and stops on a copy instead of a link |
| Gated live copy | Tools load a separate clone that only moves after lint passes | Home changes often | Add a second clone on main that pulls with `--ff-only` after checks |
| SOPS and age | Secrets encrypted in git, decrypted at run time | Tokens need to move between machines | Install sops and age, one age key per machine with an offline backup |
| Media kit | Prompt and take logs, an audio-reactive three.js starter, render presets | Music and video projects | Copy the kit folder into the project |
| Ops kit | Runbooks and a change log for servers and containers | Server or homelab projects | Copy the kit folder into the project |
| Scheduled agents | Runs a prompt on a timer (tidy, sweeps, briefings) | A chore repeats weekly | Use the tool's scheduler or a cron job on an always-on box |
| ADR folder | One file per big decision in `.agents/adr/` | Decisions need more than a wiki line | Create the folder and a template |
| MEMORY.md and SOUL.md | Small capped memory and persona files | A tool without its own memory | Add both, capped at one screen; skip in Claude Code (clashes with its auto-memory) |
| Assistant connectors | Email, calendars, speech in and out for a home assistant | The assistant project starts | Connect each service in its own project space |
| Client spaces | One space per client in the project shape, beside their repos, never changing them | Client or employer work | Copy the template, set `.agents/space` to `client`, add a per-client connector that drops into its raw/ |
| Life-notes space | Private notes sorted by Projects, Areas, Resources, Archive | Personal notes | Copy the template; the wiki skill files notes by those four |
| Delegation rules | When to hand work to which agent or model | Several agents share work | Add a short rules page and link it from AGENTS.md |
| Obsidian | A visual browser over the wiki folder | You want to click through the wiki | Open the project folder as a vault; nothing else changes |
| Spec-driven kits | Spec, plan and task files per feature | Large features across many files | Assess against the backlog first; they install their own folders |
| Memory MCP servers | Memory served to tools over MCP | Tools need shared memory | Assess; the wiki usually covers it |
| herdr | A terminal cockpit for many agents | Several agents at once on Linux or WSL | Install herdr in WSL |
| Session backup | Copies each tool's session folders to a backup drive on a schedule | Old sessions matter | A scheduled copy job |
| Session-to-wiki | Mines old sessions for wiki pages | Knowledge is stuck in old chats | Try an existing tool (for example llm-wiki) on one project |
| Zoom maps (idea, not built) | Generated maps of folders, functions and headings, so an agent finds things without reading whole files. [Details](zoom-maps.md#zoom-maps) | An agent keeps opening the wrong file, or a repo passes roughly 30 files (a guess) | Install universal-ctags 6 or newer, add a small script (not written yet) and one AGENTS.md line |
