---
name: wiki
description: Keep the project's LLM wiki (raw/ and wiki/). Use when the user drops a file, pastes notes, shares a link or a chat to keep, says "add this to the wiki", "ingest", "file this", asks what we know or why something was decided, or asks to tidy, lint or clean up the wiki.
---

# Wiki

The rules are in `reference/conventions.md` next to this file; read it first. Four moves. Act, then report in one line. Ask only before a delete or a taste call.

## drop

The user hands you something to keep.

1. Save it to `raw/YYYY-MM-DD-short-slug.ext` (a link becomes a short note with the URL and what matters in it). Never edit an existing `raw/` file.
2. Go straight to **ingest** in the same session.

## ingest

1. Read `wiki/index.md` and the pages the source touches.
2. Update those pages, or write a new one. Set `sources` to the real evidence and `updated` to today. Never set `ratified`.
3. If the source disagrees with a page, say so on the page under its own heading, with both sources. Do not quietly rewrite the old claim.
4. Link related pages at heading level, both ways. Add new pages to `wiki/index.md`.
5. Run **tidy** step 1 and fix what it reports.
6. Append `## [YYYY-MM-DD] ingest | <source>` to `wiki/log.md`, commit with the subject `ingest | <source>`, and tell the user in one line what changed.

## ask

1. Read `wiki/index.md`, then the pages that look relevant, following links one or two hops.
2. Answer with a heading-level link for every claim. Say when a page is stale (lint flags it) or not `ratified`.
3. If the wiki has no answer, say so first, then label anything from outside as outside.
4. If the answer is worth keeping, file it as a page whose `sources` are the cited pages, log it as `ask | <question>`, and commit.

## tidy

1. Run `python <this skill's folder>/scripts/wiki-lint.py <project>/wiki`. Fix every error: bad frontmatter, missing sources, broken links or headings, pages missing from the index, pages over 300 lines, an `AGENTS.md` over 60 lines.
2. For a page over the cap, split it by heading or move old sections to `archive/` (same path under `archive/`). For `log.md`, move past years to `archive/wiki/log-YYYY.md`. Never delete.
3. For each stale warning (a source changed after `updated:`), re-read the source and update the page, or tell the user why not.
4. Read for what the script can't catch: contradictions, near-duplicate tags, a concept on several pages that deserves its own.
5. Log `## [YYYY-MM-DD] tidy | <summary>`, commit with the same subject, and list anything left for the user.
