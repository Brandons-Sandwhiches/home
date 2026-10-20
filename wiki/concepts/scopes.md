---
title: User space and project space
tags: [harness, install]
sources:
  - https://code.claude.com/docs/en/memory
  - https://code.claude.com/docs/en/skills
  - https://developers.openai.com/codex/guides/agents-md
  - https://opencode.ai/docs/skills
updated: 2026-10-20
---

# User space and project space

Every tool reads agent context from a **user space** in your home folder (all projects) and a **project space** in the repo (this project only). skillshare is the one tool that writes links into user space; nothing is copied there by hand. There is no plugin or marketplace route, so each skill is listed once.

## Where each lives

| Tool | User rules | User skills | Project rules | Project skills |
| --- | --- | --- | --- | --- |
| Codex | `~/.codex/AGENTS.md` | `~/.agents/skills` | `AGENTS.md`, root down to cwd | `.agents/skills` |
| opencode | `~/.config/opencode/AGENTS.md` | `~/.agents/skills` (and `~/.claude/skills`) | `AGENTS.md` | `.agents/skills`, `.opencode/skills` |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/skills` | `CLAUDE.md` (here `@AGENTS.md`) | `.claude/skills` |
| Gemini CLI | `~/.gemini/GEMINI.md` | `~/.agents/skills` | `GEMINI.md` (here `@AGENTS.md`) | `.agents/skills` |

## Traps

- opencode reads both `~/.claude/skills` and `~/.agents/skills`, so skills show twice. Set `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`.
- opencode ignores `disable-model-invocation`; a user-invoked skill also needs `metadata: {opencode/autoinvoke: false}`.
- On Windows, skillshare `target remove` turns links into copies. Don't use it.
- On Windows, a rules file links live only with Developer Mode on; use `mklink`, since PowerShell 5.1 `New-Item -ItemType SymbolicLink` still wants admin. A link that turned into a copy must fail the link check loudly.
- Where a skill exists at user and project level, Claude Code prefers the user copy and Codex lists both.
- Upstream skills are pinned to a commit, so an update is a reviewed bump, not a live change.

See [how a project works](../how-a-project-works.md#in-words).
