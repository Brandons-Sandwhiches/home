# evals

Nothing enters home on reputation. A skill or rule stays only while it beats "no skill" on real tasks, in Claude Code and Codex.

## Run it

```sh
python evals/run.py <golden-tasks.yaml> --skill wiki      # one skill, with vs without
python evals/run.py <golden-tasks.yaml> --base main --change add   # a home PR, main vs branch
python evals/run.py <golden-tasks.yaml> --sweep           # all of home on vs off (weekly, or after a model update)
```

Needs Python with PyYAML. Each task runs 3 times per arm, per tool, in a fresh temp copy of its fixture. promptfoo (pinned in `run.py`, run through npx) drives the runs and scores them; `--engine native` does the same without node. Paste `summary.md` into the PR's "How it was checked".

## The gate

- **Addition:** a clear win (pass rate up 15 points or more in each tool) and no regression.
- **Removal or simplification:** no regression (no tool down more than 1 run in total, no task down 2 or more).
- **Wording only:** must not drop (same as no regression).
- False triggers (a skill firing on a task not tagged for it) are counted and shown.
- Limit: about 15 tasks x 3 runs only spots big effects. Small changes pass on "no harm" and claim no win.

Skills that don't pass go to the [catalog](../wiki/catalog.md#catalog). A skill is ratified only after evals plus wins in 2+ projects (from each project's `.agents/skill-log.jsonl`).

## Task file

The golden tasks are the owner's real tasks, so they live in the private repo, written down before any skill is tested. Keep a hold-out set.

```yaml
tools:                     # optional overrides of the commands in run.py
  claude: {cmd: ["claude", "-p", "{prompt}", "--output-format", "stream-json", "--verbose"], env: {}}
tasks:
  - id: left-off-summary
    tags: [rule:session-start]       # skill:<name> or rule:<name> it touches
    probes: [wiki]                   # skills that must NOT fire here (false triggers)
    holdout: false
    fixture: fixtures/mid-project    # folder copied in; PROJECT.md is the project paragraph
    prompt: "Where did we leave off?"
    check:                           # all must hold
      output_contains: ["task-3"]
      output_not_contains: []
      output_regex: "next"
      file_exists: ["wiki/lessons/*.md"]
      file_absent: []
      file_contains: {"wiki/log.md": ["ingest"]}
      max_lines: {"AGENTS.md": 60}
      run: "python scripts/repo-check.py"
```
