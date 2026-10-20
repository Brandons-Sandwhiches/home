#!/usr/bin/env python3
"""Append one skill-use line to <project>/.agents/skill-log.jsonl.

Usage: log_skill.py <project> <skill> <pass|fail|none> [task] [--tool NAME]

The home base dashboard and the evals read this log: how often each skill
fired, in how many projects, and how often its check passed.
"""
import datetime
import json
import os
import sys
from pathlib import Path


def main():
    args = sys.argv[1:]
    tool = os.environ.get("AGENT_TOOL", "")
    if "--tool" in args:
        i = args.index("--tool")
        tool = args[i + 1]
        del args[i:i + 2]
    if len(args) < 3 or args[2] not in ("pass", "fail", "none"):
        sys.exit(__doc__)
    project, skill, check = Path(args[0]).resolve(), args[1], args[2]
    task = args[3] if len(args) > 3 else ""
    log = project / ".agents" / "skill-log.jsonl"
    log.parent.mkdir(exist_ok=True)
    line = {"date": datetime.date.today().isoformat(), "skill": skill, "check": check,
            "task": task, "tool": tool}
    with log.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(line) + "\n")
    print(f"logged {skill} {check} in {log}")


if __name__ == "__main__":
    main()
