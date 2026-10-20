---
name: learn-from-work
description: Turn a correction or a hard-won fix into a lesson in the project wiki, and log which skills ran and whether their check passed. Use when the user corrects you ("no, not like that", "don't do X"), when a fix only worked on a later try, before work in an area that has lessons, and at session end.
---

# Learn from work

A correction should only have to be made once. Lessons live in this project's wiki; they never move to another project.

## When the user corrects you

1. Fix the output first.
2. Look for a page tagged `lesson` on the same thing (`wiki/index.md`, `### lesson`). Update it if there is one.
3. Otherwise write `wiki/lessons/<short-slug>.md`:

   ```markdown
   ---
   title: <the rule, in a few words>
   tags: [lesson, <topic>]
   sources: [<the raw/ note, task or commit where it came up>]
   updated: YYYY-MM-DD
   ---

   # <the rule, in a few words>

   ## Rule
   One or two lines: what to do from now on in this project.

   ## Why
   What went wrong, and what the user said.
   ```

4. Add it to `wiki/index.md` under `### lesson`, log `## [YYYY-MM-DD] lesson | <slug>`, commit with the same subject, and say in one line that you saved it.

Keep it at the narrowest scope: this project. A user-wide rule only when the user asks, or when the home base reports the same lesson slug in three projects; then propose the rule and wait for a yes.

## Before you start work

Skim `### lesson` in `wiki/index.md` and read any lesson that touches the task.

## Log skill use (feeds the evals)

At session end, for each home skill you used, run once:

```sh
python <this skill's folder>/scripts/log_skill.py <project> <skill> <pass|fail|none> "<task, a few words>"
```

`pass` or `fail` is the result of the check you ran for that work (repo-check, a test, the skill's own check); `none` if there was no check. It appends one line to `<project>/.agents/skill-log.jsonl`. Never edit past lines.
