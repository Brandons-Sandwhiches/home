# Conventions

Version 2. The one copy of the wiki rules. Every other file links here instead of restating them. A project records the version it follows in its own `AGENTS.md`.

## Three layers

Following the Karpathy LLM-wiki pattern:

1. **Raw sources** in `raw/`: added as `YYYY-MM-DD-slug.ext`, never edited. A correction is a new file.
2. **The wiki** in `wiki/`: pages the agent writes and keeps current, plus `index.md` and `log.md`.
3. **The schema** in `AGENTS.md`: says where the first two live and points here.

`AGENTS.md`, READMEs and skills are instructions, not wiki pages.

## Moves

The `wiki` skill has four moves:

- **drop**: save what the owner gives you (a file, pasted notes, a link, a chat worth keeping) into `raw/`, then ingest it in the same session.
- **ingest**: turn a raw source into pages: update what it touches, link both ways, update the index and log. Act, then report in one line.
- **ask**: answer from the wiki with heading-level links; a useful answer becomes a page.
- **tidy**: run the linter, keep pages under the cap, archive old parts, flag stale pages.

After each move, append to the log and commit with the same subject, `<move> | <subject>`, so git history and the log match. History is git: `git log --follow -p <page>`.

## Frontmatter

```yaml
---
title: Human title
tags: [topic, other-topic]   # lowercase kebab-case; the first tag groups the index
sources:                     # where the facts come from
  - raw/2026-10-19-some-note.md
  - wiki/other-page.md
  - https://example.com/page
updated: 2026-10-19          # the day the content last changed
ratified: 2026-10-20         # optional; only the owner sets it
---
```

- `ratified:` marks a page canon. Only the owner adds it. Agents never set, change or remove it.
- A `sources` path that does not exist is a lint error.
- A page whose sources changed in git after its `updated:` date is flagged stale.

## Size and archive

- A page stays at 300 lines or fewer. Split it by heading, or move old sections to `archive/`.
- `archive/` mirrors the project's paths (`archive/raw/...`, `archive/wiki/log-2026.md`). Tidy moves things there; nothing is deleted.
- `AGENTS.md` stays at 60 lines or fewer.

## Links

- Link at heading level: `[size rules](conventions.md#size-and-archive)`. Link a bare file only when the whole page is meant.
- Slugs are GitHub style: lowercase, spaces to hyphens, punctuation other than `-` and `_` dropped.
- Every page is in [the index](#index-and-log) and links to or from at least one other page.
- Relative paths only, so links work in every tool and on GitHub.

## Tags

Lowercase kebab-case. Prefer an existing tag to a near-synonym. Reserved tags: `lesson` (written by the `learn-from-work` skill).

## Index and log

- `index.md`: one line per page, `[Title](path.md#heading): summary`, grouped under `###` by first tag.
- `log.md`: append-only, newest last, `## [YYYY-MM-DD] move | subject` then a line on what changed. Tidy moves old years to `archive/wiki/`.
