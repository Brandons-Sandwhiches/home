---
id: TASK-8
title: Decide red-team pass and CI on PRs
status: Done
assignee: []
created_date: '2026-10-20 16:45'
updated_date: '2026-10-27 15:30'
labels: [needs-owner]
dependencies: []
priority: low
---

## Description

Two repo standards are still open: a red-team pass before merge, and CI on every PR. Decide each, then add the winners to the template.

Decided: a red team runs when a PR reaches ready, and CI stays tiny (gitleaks and lint). The build work is in TASK-13.
