---
name: ecrs-review
description: ECRS review (Eliminate, Combine, Rearrange, Simplify) of a plan, process, workflow, or system. Use when the user asks for an ECRS review, wants to streamline a process or roadmap, or asks how to make a sequence of steps or components leaner.
---

# ECRS review

ECRS is the lean improvement sequence: **Eliminate, Combine, Rearrange, Simplify**, always tried in that order, because removing a step beats improving it.

## 1. Map the elements

- Read the whole artifact and write its goal in one sentence.
- List its elements in order: steps, phases, sections, components, files, hand-offs. For each, note what it produces, what it needs, and who or what does it.
- When order matters (a roadmap, a pipeline, an install flow), note the dependencies between elements.

## 2. Ask the four questions of every element, in order

1. **Eliminate.** Would the goal still be met without it? Waiting, duplicate checks, rework loops, steps that only feed another removable step, and outputs nobody reads are the usual candidates.
2. **Combine.** Does it do the same job, touch the same files, or need the same inputs as another element? Merge them so the work happens once.
3. **Rearrange.** Would a different order, owner, or timing remove waiting, rework, or risk? Move checks earlier, move blockers off the critical path, and do the riskiest unknown first.
4. **Simplify.** For what is left, what is the simplest form that works: fewer options, a default instead of a choice, a convention instead of a tool.

Stop at the first question that changes the element. Never eliminate safety controls, data-loss protection, or anything the user explicitly asked for.

## 3. Check before you report

- Every change names the element, the question that triggered it, and why the goal still holds.
- Rearrangements state the new order and the dependency that allows it.
- No change without a concrete reason. "Looks heavy" is not a reason.

## 4. Output

Start with `Goal:` in one sentence. Then one table in the artifact's original order:

| # | Element | E / C / R / S / keep | Change | Why the goal still holds |
| --- | --- | --- | --- | --- |

Then the proposed new sequence as a numbered list, and the single change with the biggest effect. Do not apply changes unless the user asks.
