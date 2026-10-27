#!/usr/bin/env python3
"""Run before calling work done: gitleaks on new commits, then the project's own check.

Usage: python scripts/repo-check.py
       python scripts/repo-check.py --pre-push   (git runs this before a push)

1. gitleaks scans commits not yet on any remote, plus uncommitted changes.
   Missing gitleaks is a failure, not a skip.
2. AGENTS.md must be 60 lines or fewer.
3. The wiki linter runs if the home `wiki` skill is found.
4. The STE prose check runs on every markdown file except raw/, archive/ and
   the paths listed in .agents/prose-ignore (one prefix per line).
5. The command in .agents/check-command runs, if the file has one.

It also turns on the commit gate: git runs this file before every commit
(.githooks/pre-commit). Skip it once with `git commit --no-verify`.

With --pre-push it only checks branch names, from the refs git sends on stdin.
A new branch must be <prefix>-<number>-<short-slug>, in lowercase letters, digits
and hyphens. Branches that already exist on the remote pass. The prefix is task_prefix in backlog/config.yml (else `task`, the
Backlog.md default). `main` and `claude/*` are allowed.

Exits non-zero on any failure. Paste the whole output into the PR or the
reply. This file is a copy from home's project template and doesn't update
itself.
"""
import re
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


def find_prose_check():
    for base in (ROOT / "scripts", ROOT.parent / "home" / "scripts"):
        if (base / "prose-check.mjs").exists() and (base / "prose-score.mjs").exists():
            return base / "prose-check.mjs"
    return None


def git_out(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def prose_files():
    listed = git_out("ls-files", "--cached", "--others", "--exclude-standard", "-z", "*.md") or ""
    ignore_file = ROOT / ".agents" / "prose-ignore"
    skip = ["raw/", "archive/"]
    if ignore_file.exists():
        skip += [l.strip() for l in ignore_file.read_text(encoding="utf-8-sig").splitlines()
                 if l.strip() and not l.startswith("#")]
    return [p for p in listed.split("\0") if p and (ROOT / p).is_file() and not any(p.startswith(s) for s in skip)]


def backlog_prefix():
    config = ROOT / "backlog" / "config.yml"
    if config.exists():
        found = re.search(r"^task_prefix:\s*[\"']?([A-Za-z]+)[\"']?\s*$", config.read_text(encoding="utf-8-sig"), re.M)
        if found:
            return found.group(1).lower()
    return "task"


def pre_push():
    prefix = backlog_prefix()
    rule = re.compile(rf"^{prefix}-[0-9]+(\.[0-9]+)*-[a-z0-9-]+$")
    bad = []
    for line in sys.stdin.read().splitlines():
        parts = line.split()
        if len(parts) < 4 or not parts[2].startswith("refs/heads/") or set(parts[1]) == {"0"}:
            continue  # not a branch, or a delete
        if set(parts[3]) != {"0"}:
            continue  # the branch already exists on the remote, so only new names are checked
        name = parts[2][len("refs/heads/"):]
        if name != "main" and not name.startswith("claude/") and not rule.match(name):
            bad.append(name)
    for name in bad:
        print(f"repo-check: branch '{name}' refused. Name it {prefix}-<number>-<short-slug>, "
              f"for example {prefix}-12-short-slug. The number is the backlog task. "
              "'main' and 'claude/*' are allowed.")
    sys.exit(1 if bad else 0)


def commit_gate():
    if (ROOT / ".githooks" / "pre-commit").exists() and git_out("rev-parse", "--git-dir") is not None:
        if (git_out("config", "core.hooksPath") or "").strip() != ".githooks":
            subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT)
            print("== commit gate: turned on (git runs repo-check before every commit)")


def main():
    commit_gate()
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

    prose = find_prose_check()
    node = shutil.which("node")
    if not prose or not node:
        print(f"== STE prose: skipped, {'node' if prose else 'home/scripts/prose-check.mjs'} not found on this machine")
    else:
        files = prose_files()
        print(f"== STE prose: {len(files)} markdown files", flush=True)
        code = subprocess.run([node, str(prose)], cwd=ROOT, input="\n".join(files), text=True,
                              encoding="utf-8").returncode
        print(f"== STE prose: {'ok' if code == 0 else 'FAILED (fix each finding, or list the path in .agents/prose-ignore)'}")
        results.append(code == 0)

    check_file = ROOT / ".agents" / "check-command"
    command = check_file.read_text(encoding="utf-8-sig").strip() if check_file.exists() else ""
    if command:
        results.append(run("project check", command, shell=True))
    else:
        print("== project check: none set in .agents/check-command")

    ok = all(results)
    print(f"repo-check: {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--pre-push" in sys.argv:
        pre_push()
    main()
