---
name: session-handoff
description: Write a handoff so a fresh session can pick up the work cold, plus a paste-ready start prompt. Use when the user says hand off, hand this session off, wrap up for a new session, or start fresh, when context is running low, or before a long break on multi-session work.
---

# Session handoff

A handoff is for a reader with no memory of this session. It states the goal as outcomes, what is true now, where everything is, and what to do next. It links to the project's files instead of copying them.

## 1. Gather the truth

Memory of the session is stale. Check every fact again before you write it down.

- Git: `git log --oneline -15` on the main branch and the work branch, `git branch -vv`, `git worktree list`, `git status`, `git stash list`.
- Pull requests: `gh pr list --state open` in each repo the session touched.
- Backlog: the status and the latest note of each task in play.
- Other sessions or agents still running, and what they own.
- Note anything that changed since you last looked, especially work other sessions did.

## 2. Write the handoff

Save it as `backlog/docs/handoff-YYYY-MM-DD.md` (add `-2` for a second one that day). Use [the template](reference/template.md). Its sections:

1. **Goal, in outcomes.** One line, then each outcome as a result someone can check. Mark each one done, partly done or not started, with its proof.
2. **Where things stand.** Done, in progress and blocked, each with a commit, file or task id.
3. **Where things are.** Branches, worktrees, open PRs and uncommitted work, each with its purpose. Say which ones to keep and which ones are safe to drop.
4. **Decisions in force.** Each decision in one line, with a link to its record. Quote the user's own words for any decision that only they could make.
5. **Waiting on the user.** Every open question and sign-off, matching the sign-off tag in the backlog.
6. **Lessons and traps.** Link the project's lessons. Add traps that cost time this session.
7. **Do not.** Things a fresh session would likely get wrong.
8. **Next 3 steps,** in order.
9. **Start prompt.** A fenced block under 2,000 characters for the user to paste into a new session. It names the handoff path and the first step, and it repeats the hard rules.

Rules:

- Link, don't copy. A handoff that restates a design doc goes stale fast.
- Every claim has a source: a commit, file, task or PR. If you could not check something, mark it `unverified`.
- Give the commit the handoff is true at.
- No secrets, tokens or personal data.

## 3. Close the loop

1. Add a banner to the top of the previous handoff: `> Superseded by [handoff-YYYY-MM-DD](handoff-YYYY-MM-DD.md).`
2. Point the epic or the active task at the new handoff.
3. Tag every item that waits on the user with the sign-off tag.

## 4. Test it cold (the depth test)

Give a fresh agent only the handoff and the start prompt, with read access to the repo. It answers five questions:

1. What is the goal, and which outcomes are still open?
2. What is the first thing to do, and in which branch or folder?
3. What waits on the user?
4. What must it not do?
5. Which work is safe to drop, and which must stay?

Each wrong or vague answer is a gap: fix the handoff and ask again. Stop when all five are right.

## 5. Commit and report

Run the project's checks. Commit the handoff the way the project commits its backlog. Then tell the user the path, the next 3 steps, and the start prompt as a fenced block.
