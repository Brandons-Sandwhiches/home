---
id: TASK-11
title: Add an optional denylist file to repo-check
status: To Do
assignee: []
created_date: '2026-10-27 15:30'
updated_date: '2026-10-27 15:30'
labels: [needs-owner]
dependencies: []
priority: low
---

## Description

Let a project list words that must never appear in its files, in a file the project owns. repo-check reads the path from one setting. With no file named, it skips the check. The word list stays in the project, never in home. Build only after the owner says yes on the PR.
