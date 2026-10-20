#!/usr/bin/env python3
"""Run before calling work done: gitleaks on new commits, then the project's own check.

Usage: python scripts/repo-check.py

1. gitleaks scans commits not yet on any remote, plus uncommitted changes.
   Missing gitleaks is a failure, not a skip.
2. AGENTS.md must be 60 lines or fewer.
3. The wiki linter runs if the home `wiki` skill is found.
4. The command in .agents/check-command runs, if the file has one.

Exits non-zero on any failure. Paste the whole output into the PR or the
reply. This file is a copy from home's project template and doesn't update
itself.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_CAP = 60


def run(label, cmd, shell=False):
    print(f"== {label}: {cmd if shell else ' '.join(cmd)}", flush=True)
    code = subprocess.run(cmd, cwd=ROOT, shell=shell).returncode
    print(f"== {label}: {'ok' if code == 0 else f'FAILED (exit {code})'}", flush=True)
    return code == 0


def has_commits():
    return subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT,
                          capture_output=True).returncode == 0


def find_wiki_lint():
    tail = Path("wiki") / "scripts" / "wiki-lint.py"
    for base in (ROOT.parent / "home" / "skills" / "knowledge", ROOT / ".agents" / "skills",
                 ROOT / ".claude" / "skills", Path.home() / ".agents" / "skills",
                 Path.home() / ".claude" / "skills"):
        if (base / tail).exists():
            return base / tail
    return None


def main():
    results = []
    gitleaks = shutil.which("gitleaks")
    if not gitleaks:
        print("== gitleaks: FAILED, not installed. Install it once per machine, then re-run.")
        results.append(False)
    else:
        if has_commits():
            results.append(run("gitleaks new commits", [gitleaks, "git", "--no-banner", "--redact",
                                                        "--log-opts=--branches --not --remotes", "."]))
        results.append(run("gitleaks uncommitted", [gitleaks, "git", "--no-banner", "--redact", "--pre-commit", "."]))

    agents = ROOT / "AGENTS.md"
    if agents.exists():
        n = len(agents.read_text(encoding="utf-8").splitlines())
        ok = n <= AGENTS_CAP
        print(f"== AGENTS.md: {n} lines (cap {AGENTS_CAP}) {'ok' if ok else 'FAILED'}")
        results.append(ok)

    lint = find_wiki_lint()
    if (ROOT / "wiki").is_dir():
        if lint:
            results.append(run("wiki lint", [sys.executable, str(lint), str(ROOT / "wiki")]))
        else:
            print("== wiki lint: skipped, home's wiki skill not found on this machine")

    check_file = ROOT / ".agents" / "check-command"
    command = check_file.read_text(encoding="utf-8").strip() if check_file.exists() else ""
    if command:
        results.append(run("project check", command, shell=True))
    else:
        print("== project check: none set in .agents/check-command")

    ok = all(results)
    print(f"repo-check: {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()
