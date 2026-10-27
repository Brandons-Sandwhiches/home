---
name: discovery-interview
description: Interview the user in breadth-first passes to shape a plan, project, or system before building it. Use when the user asks to be interviewed, grilled, or asked questions about what they want, or when a request is too broad to act on without understanding goals first.
---

# Discovery interview

Breadth-first discovery with progressive deepening: establish the big picture, then keep returning with more specific questions. Taxonomy (what kinds of things exist) and ontology (what they are, their properties and how they relate) organize the results. The passes decide how deep to go.

## The five passes

| Pass | Uncover | Example questions |
| --- | --- | --- |
| 1 Purpose | Goals, audience, boundaries, success | What are you trying to accomplish? Who is it for? What does success look like? |
| 2 Territory | Major categories, concepts, activities, unknowns | What are the main parts? What kinds of users or tasks exist? What haven't we discussed? |
| 3 Connections | Definitions, relationships, ownership, dependencies | Who does what? What depends on what? Are these two things, or two names for one thing? |
| 4 Depth | Real workflows, decisions, constraints, exceptions | Walk me through a real example. What happens next? What changes when it fails? |
| 5 Challenge | Unsupported assumptions, contradictions, trade-offs | What makes you believe that? When would this rule be wrong? Can both requirements hold? |

## How to run it

1. Finish one pass before starting the next. Within a pass, ask broad before narrow.
2. Ask at most about ten questions per round. Make each answerable in a word or a line, give options where you know the space, and mark your recommendation.
3. Bring ideas, not only questions: where the user is unsure or asks for options, offer two or three concrete ones with the trade-off of each.
4. Research before asking about anything the web or the repo can answer; ask only what only the user knows.
5. After each round, save the answers verbatim or condensed to `raw/YYYY-MM-DD-interview-pass-N.md` and say which pass comes next.
6. After pass 3, write the taxonomy and ontology as wiki pages (use the `wiki` skill, ingest move), then use passes 4 and 5 to test them.
