---
id: TASK-1
title: Make the Codex eval home-off arm a real control
status: To Do
assignee: []
created_date: '2026-10-20 16:45'
updated_date: '2026-10-20 16:45'
labels: []
dependencies: []
priority: medium
---

## Description

Codex reads ~/.agents/skills even from a throwaway CODEX_HOME. After the switch its home-off arm still sees home's skills. Find a way to hide them for the run, then add Codex to the eval delta.
