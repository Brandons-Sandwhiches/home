---
title: Zoom maps
tags: [catalog]
sources:
  - https://github.com/kcosr/codemap
  - https://github.com/pdavis68/RepoMapper
updated: 2026-10-20
---
# Zoom maps

Status: **idea, not built, unproven until the eval below runs.**

## What it is

Five zoom levels. The script generates levels 2 and 3 as files and does not commit them. The agent builds level 4 on demand.

| Zoom | Looks at | Code | Markdown | Plain text, media |
| --- | --- | --- | --- | --- |
| 1 Earth | all projects | each project's backlog (the dashboard is for people) | same | same |
| 2 10,000 ft | one project | `.agents/map.md`: each folder, one line | same | same |
| 3 1,000 ft | one folder | file, then class and function names | `wiki/index.md`: page, one line (in v1) | file, one line |
| 4 100 ft | one file | outline with line numbers | headings with line numbers | `rg -n` or first lines |
| 5 1 ft | the lines | read lines 40 to 80 | read the section | read the range |

How the script builds each part:
- **Symbols and headings** come from universal-ctags. Nothing else makes them.
- **One-line descriptions** (folders, plain text, media) are the first line of the folder's README, or written by hand in a small `map-notes` file the rebuild keeps. ctags can't write them.
- **Level 3 is one map file per top-level folder**, capped at about 300 lines. Level 2 is the only one AGENTS.md loads. A bigger repo gets deeper folder maps; the root map lists folders only.
- **Header on every map:** what it covers, the commit the script ran at, and "not listed does not mean missing, search".

AGENTS.md line: "When you don't know where something is, read `.agents/map.md` (build it with `repo-map` if missing). It lists what exists, not what's inside; read the lines before you answer."

Staying fresh: rebuilt on commit and at session start. Line numbers can drift mid-session, so re-read before editing. A fresh clone has no map until the first build, which the AGENTS.md line covers.

## Script rules (found in testing)

- Needs **universal-ctags 6 or newer**. Check `ctags --version` for "Universal Ctags". The apt version on Ubuntu and Debian is 5.9. It drops every markdown heading above a second `---` in a page, including this wiki's own pages. Fail loudly under 6.
- Feed it from `git ls-files | ctags -L -`, never `-R`. `-R` ignores `.gitignore` and maps `node_modules`, `.venv` and Unreal's `Intermediate`, `Binaries` and `Saved`. Use `--sort=no` so a file's symbols stay together.
- Keep only classes, functions, methods and headings. Per 100 Python files that is about 600 lines, roughly 10k tokens. With every variable it is about 1,800 lines and 35k tokens.
- Test: compare ctags' heading count to `grep -c '^#'` on the wiki.
- macOS: an old BSD `ctags` may come first on PATH. Windows: release zip from the universal-ctags/ctags-win32 project (should need no admin; untested here).
- Known gaps: the tool misses TypeScript class methods; C++ prototypes need `--c++-kinds=+p`; Unreal macros (`UCLASS`, `*_API`) and TSX have no tests and are likely rough.

## Ready-made generators

Read from their READMEs on 2026-10-20; not run by us.

| Tool | Covers | Gaps |
| --- | --- | --- |
| [codemap](https://github.com/kcosr/codemap) (MIT, Node, CLI only) | Files, symbols and markdown headings in one map; `--budget` fits a token limit | No Python listed; call queries are TS/JS only; 40 stars, maintenance unknown |
| [RepoMapper](https://github.com/pdavis68/RepoMapper) (MIT, Python, CLI or MCP) | Aider's repo map: tree-sitter, ranks files by references; Python, JS, C++ and more | No markdown; last changelog July 2025; written mostly with AI help; not packaged |
| [Repomix](https://github.com/yamadashy/repomix) `--compress` | Signatures only via tree-sitter, `--token-budget`, has an MCP server (experimental per its README) | Meant for packing a repo, not for saved folder maps |
| universal-ctags | All our languages plus markdown headings; one binary | Plain list, no ranking, noisy for some languages (see above) |

Decision rule: ctags for the base, because it is the only one that covers Python, TS, C++ and markdown in one tool. RepoMapper if ranking by importance is worth a Python dependency. codemap for a TS/JS or Rust repo that also wants markdown headings. The eval picks between them.

## How it compares

| Option | Good at | Weak at | Fit |
| --- | --- | --- | --- |
| **Zoom maps (this)** | Exact names, plain files every tool can read, nothing running in the background | Finds by name, not by meaning; costs map tokens on every use; a script to keep working | No fee. Same in Claude Code, Codex, opencode |
| **Embeddings / vector index** (Cursor-style, local MCP servers like claude-context) | Search by meaning | Needs an index to build and refresh; goes stale | Only if maps plus search fail on a big repo. Continue reportedly deprecated its own codebase embeddings (check its docs) |
| **Code-intelligence tools** (Serena, SCIP indexers) | Exact "who calls this" and "go to definition" | Setup per language; SCIP is a protocol plus indexers, not a ready server | Serena (MIT) runs locally as an MCP server and names Claude Code, Codex and opencode as clients. Good second step |
| **Packers** (Repomix, code2prompt) | One file to paste a repo; Repomix can compress to signatures | Full dump by default | Fine for one-off pastes; Repomix `--compress` is a map candidate |
| **Hosted tools** (Sourcegraph Enterprise, Greptile, Augment, DeepWiki) | No setup, strong on huge repos; Augment and DeepWiki now have MCP servers | Code leaves your machine; vendor bill; Cody Free and Pro ended July 2025 | Needs a per-project check before use with private or client code |
| **Obsidian + plugins** (Dataview, Smart Connections) | Graph and backlinks for a person; Smart Connections embeds locally | A viewer for people, not a map agents read; Smart Connections is source-available, not open source; defaults to `[[wikilinks]]` | Already a catalog item. If used: markdown links, gitignore `.obsidian/` |
| **Agent search alone** (grep, glob) | Built in | Wastes reads on big repos; doesn't know what it hasn't looked at | Baseline the maps start from |

Checked against docs on 2026-10-20: codemap, RepoMapper, Serena, Repomix, Cody's shutdown, Smart Connections. Not checked: Cursor, Greptile, Continue, Dataview.

## Recommendation

1. Try zoom maps on ctags. Compare RepoMapper and Repomix `--compress` in the same eval before writing a custom script.
2. Add Serena only for real call-graph questions.
3. Skip embeddings and hosted tools until maps plus search measurably fail.

## Eval (decides whether we keep this)

- Vague orientation tasks ("which file handles login", "which page covers decisions"), not exact-name lookups where grep already wins.
- One small repo and one large repo; at least 5 runs per arm; Claude Code and Codex.
- Score correctness first, then files opened and tokens, counting the map's own read cost. Log whether the agent opened the map at all.
- Unknown until measured: whether each tool actually follows the AGENTS.md pointer.

## Open questions

- Maps stay local (gitignored) and are rebuilt by a hook; a hook is per clone and skipped by `--no-verify`, hence the build at session start too.
- Windows ctags install needs the owner's yes first, per the install rule.
