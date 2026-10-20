#!/usr/bin/env python3
"""Eval runner: prove a skill or rule change helps, with real tasks, not feelings.

Usage:
  run.py TASKS --skill NAME      with NAME vs without it (everything else in home on)
  run.py TASKS --base REF        home at REF vs this checkout (for a home PR)
  run.py TASKS --sweep           all of home on vs off
Options:
  --tools claude,codex[,opencode]   default claude,codex
  --runs 3          runs per task, per arm, per tool
  --change add|remove|wording       what the gate checks (default add; --base needs it)
  --tags a,b        only tasks with these tags (default: picked from the mode)
  --holdout         also run the hold-out tasks
  --user-rules FILE user rules for every arm (default: ../home-private/user/AGENTS.md if it exists)
  --max-usd 20      stop when reported cost passes this (logged per run)
  --engine promptfoo|native         default promptfoo (pinned, via npx); native needs no node
  --keep            keep the temp workspaces
  --dry-run         build the workspaces and print the commands, run nothing

TASKS is a golden-tasks.yaml (format: evals/README.md). Results go to
<TASKS folder>/results/<stamp>-<mode>/: runs.jsonl, summary.md, and for a
sweep also results/latest-sweep.json, which the dashboard shows.
Also serves as promptfoo's python provider (call_api) and assertion (get_assert).
"""
import argparse
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
PROMPTFOO = "promptfoo@0.123.1"  # pinned; bump on purpose, never "latest"
DEFAULT_TOOLS = {
    # No "{prompt}" in cmd means the prompt goes on stdin (safe with Windows .cmd shims).
    # User-level settings, skills and MCP are left out so the "off" arm is clean.
    "claude": {"cmd": ["claude", "-p", "--output-format", "stream-json", "--verbose",
                       "--setting-sources", "project,local", "--strict-mcp-config",
                       "--permission-mode", "acceptEdits", "--allowedTools", "Bash Read Write Edit Glob Grep"]},
    # Codex always loads user-level skills, so each run gets a throwaway CODEX_HOME holding only a
    # link (never a copy) to the login file; it is deleted right after the run. On Windows it also
    # links the existing sandbox setup, so the elevated sandbox works without a new admin step.
    "codex": {"cmd": ["codex", "exec", "--json", "--skip-git-repo-check", "--sandbox", "workspace-write"]
                     + (["-c", 'windows.sandbox="elevated"'] if os.name == "nt" else []) + ["-"],
              "temp_home": {"env": "CODEX_HOME", "link": ["~/.codex/auth.json", "~/.codex/.sandbox",
                                                          "~/.codex/.sandbox-bin", "~/.codex/.sandbox-secrets"]}},
    "opencode": {"cmd": ["opencode", "run", "--format", "json", "{prompt}"]},
}


# ---------- loading ----------

def load_tasks(path):
    try:
        import yaml
    except ImportError:
        sys.exit("run.py needs PyYAML to read the tasks file: python -m pip install pyyaml")
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    tools = {**DEFAULT_TOOLS, **(data.get("tools") or {})}
    return data, tools


def pick_tasks(data, args, changed_tags):
    tasks = [t for t in data["tasks"] if args.holdout or not t.get("holdout")]
    if args.tags:
        want = set(args.tags.split(","))
    elif args.skill:
        want = {f"skill:{args.skill}"}
    elif args.base:
        want = changed_tags
    else:
        return tasks
    keep = []
    for t in tasks:
        probes = {f"skill:{p}" for p in t.get("probes", [])}
        if want & (set(t.get("tags", [])) | probes):
            keep.append(t)
    return keep


def changed_tags(base):
    out = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=HOME,
                         capture_output=True, text=True).stdout.split()
    tags = set()
    for f in out:
        m = re.match(r"skills/[^/]+/([^/]+)/", f)
        if m:
            tags.add(f"skill:{m.group(1)}")
        elif f.startswith("templates/project/"):
            tags.add("rule:template")
        elif f.startswith(("templates/work/", "scripts/dashboard.py")):
            tags.add("rule:home-base")
    return tags


# ---------- one run ----------

def home_skills(home):
    return {p.parent.name: p.parent for p in Path(home).glob("skills/*/*/SKILL.md")} if home else {}


def build_workspace(task, arm, tasks_dir):
    ws = Path(tempfile.mkdtemp(prefix=f"eval-{task['id']}-"))
    fixture = tasks_dir / task.get("fixture", "") if task.get("fixture") else None
    if fixture and fixture.is_dir():
        shutil.copytree(fixture, ws, dirs_exist_ok=True)
    home = Path(arm["home"]) if arm.get("home") else None
    root, ws = ws, (ws / task["cwd"] if task.get("cwd") else ws)
    ws.mkdir(parents=True, exist_ok=True)
    if task.get("workspace"):  # fixture is a whole workspaces folder; the agent runs in task["cwd"]
        if home and arm.get("rules", True):
            shutil.copytree(home, root / "home", ignore=shutil.ignore_patterns(".git", "results"), dirs_exist_ok=True)
            for f in (home / "templates" / "work").iterdir():
                if not (ws / f.name).exists():
                    shutil.copyfile(f, ws / f.name)
            if arm.get("user_rules"):
                with (ws / "AGENTS.md").open("a", encoding="utf-8") as fh:
                    fh.write("\n## User rules\n\n" + Path(arm["user_rules"]).read_text(encoding="utf-8"))
        else:
            (ws / "AGENTS.md").write_text("# AGENTS.md\n\nThis folder sits next to my project folders.\n", encoding="utf-8")
            (ws / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
        git_init(root)
        return root, ws
    project = (ws / "PROJECT.md").read_text(encoding="utf-8").strip() if (ws / "PROJECT.md").exists() else ""
    (ws / "PROJECT.md").unlink(missing_ok=True)
    if home and arm.get("rules", True):
        template = home / "templates" / "project"
        for f in template.rglob("*"):
            dest = ws / f.relative_to(template)
            if f.is_file() and not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, dest)
        agents = (template / "AGENTS.md").read_text(encoding="utf-8")
        agents = re.sub(r"One paragraph: what it makes.*Replace this line\.", project or "A test project.", agents)
        if arm.get("user_rules"):
            agents += "\n## User rules\n\n" + Path(arm["user_rules"]).read_text(encoding="utf-8")
        (ws / "AGENTS.md").write_text(agents, encoding="utf-8")
    else:
        (ws / "AGENTS.md").write_text("# AGENTS.md\n\n" + (project or "A test project.") + "\n", encoding="utf-8")
        (ws / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    for name, src in home_skills(home).items():
        if name in arm.get("without", ()):
            continue
        for slot in (".claude/skills", ".agents/skills"):
            shutil.copytree(src, ws / slot / name, dirs_exist_ok=True)
    git_init(ws)
    return root, ws


def git_init(ws):
    env = {**os.environ, "GIT_AUTHOR_NAME": "eval", "GIT_AUTHOR_EMAIL": "eval@example.invalid",
           "GIT_COMMITTER_NAME": "eval", "GIT_COMMITTER_EMAIL": "eval@example.invalid"}
    for cmd in (["git", "init", "-q", "-b", "main"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "fixture"]):
        subprocess.run(cmd, cwd=ws, env=env, capture_output=True)


def command(tools, tool, prompt, model=None):
    cfg = tools[tool]
    cmd = [part.replace("{prompt}", prompt) for part in cfg["cmd"]]
    if model and cfg.get("model_flag"):
        cmd += [cfg["model_flag"], model]
    exe = shutil.which(cmd[0])
    if exe:
        cmd[0] = exe
    env = {**os.environ, **{k: str(v) for k, v in (cfg.get("env") or {}).items()}}
    temp = None
    if cfg.get("temp_home"):
        temp = Path(tempfile.mkdtemp(prefix=f"eval-{tool}-home-"))
        for src in cfg["temp_home"].get("link", []):
            src = Path(os.path.expanduser(src))
            if src.exists():  # a link, never a copy; fails loudly without Developer Mode
                os.symlink(src, temp / src.name, target_is_directory=src.is_dir())
        env[cfg["temp_home"]["env"]] = str(temp)
    return cmd, env, temp


def parse_output(raw, skills):
    final, tokens, cost = "", 0, 0.0
    for line in raw.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        if e.get("type") == "result":  # Claude Code
            final = e.get("result") or final
            u = e.get("usage") or {}
            tokens = sum(u.get(k, 0) or 0 for k in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                                                    "cache_creation_input_tokens"))
            cost = e.get("total_cost_usd") or cost
        item = e.get("item") or {}
        if item.get("type") == "agent_message":  # Codex
            final = item.get("text") or final
        if e.get("type") == "turn.completed":
            u = e.get("usage") or {}
            tokens += (u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)
        part = e.get("part") or {}
        if part.get("type") == "text" and part.get("text"):  # opencode
            final = part["text"]
    if not final:
        final = raw[-4000:]
    fired = sorted(n for n in skills if re.search(
        rf"skills[/\\]+{re.escape(n)}[/\\]+SKILL\.md|\"(?:skill|command|name)\"\s*:\s*\"{re.escape(n)}\"", raw))
    return final, tokens, cost, fired


def check(task, ws, final):
    c, low, fails = task.get("check") or {}, final.lower(), []
    for s in c.get("output_contains", []):
        if s.lower() not in low:
            fails.append(f"output lacks '{s}'")
    for s in c.get("output_not_contains", []):
        if s.lower() in low:
            fails.append(f"output has '{s}'")
    if c.get("output_regex") and not re.search(c["output_regex"], final, re.I | re.S):
        fails.append("output_regex")
    for p in c.get("file_exists", []):
        if not glob.glob(str(ws / p), recursive=True):
            fails.append(f"missing {p}")
    for p in c.get("file_absent", []):
        if glob.glob(str(ws / p), recursive=True):
            fails.append(f"should be absent: {p}")
    for p, needles in (c.get("file_contains") or {}).items():
        texts = [Path(f).read_text(encoding="utf-8", errors="replace").lower()
                 for f in glob.glob(str(ws / p), recursive=True) if Path(f).is_file()]
        if not any(all(n.lower() in t for n in needles) for t in texts):
            fails.append(f"{p} lacks {needles}")
    for p, cap in (c.get("max_lines") or {}).items():
        f = ws / p
        if f.exists() and len(f.read_text(encoding="utf-8").splitlines()) > cap:
            fails.append(f"{p} over {cap} lines")
    if c.get("run"):
        r = subprocess.run(c["run"], cwd=ws, shell=True, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        if r.returncode != 0:
            fails.append(f"run failed: {(r.stdout + r.stderr)[-200:]}")
    return not fails, fails


def kill_tree(p):
    if os.name == "nt":  # a .cmd shim's node child survives p.kill()
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    else:
        p.kill()


def drop_temp_home(temp):
    """Remove the links first, so a failed cleanup never leaves the login file reachable."""
    for entry in temp.iterdir():
        if entry.is_symlink():
            entry.unlink() if not entry.is_dir() else os.rmdir(entry) if os.name == "nt" else entry.unlink()
    for _ in range(5):  # Codex can hold plugin cache files open for a moment after exit
        try:
            rmtree(temp)
            return
        except OSError:
            time.sleep(2)
    print(f"warning: could not remove {temp} (links already removed)")


def rmtree(path):
    def unlock(func, target, _):
        if os.path.islink(target):  # never touch what a link points at (the login file)
            os.unlink(target)
            return
        os.chmod(target, 0o700)
        func(target)
    shutil.rmtree(path, onerror=unlock)


def run_one(task, tool, arm, tools, tasks_dir, timeout_min=15, keep=False, dry=False, model=None):
    root, ws = build_workspace(task, arm, tasks_dir)
    cmd, env, temp_home = command(tools, tool, task["prompt"].strip(), model)
    if dry:
        if temp_home:
            drop_temp_home(temp_home)
        print(f"[dry] {task['id']} {tool} {arm['name']}: {ws}\n      {' '.join(cmd[:3])} ...")
        rmtree(root)
        return None
    start = time.time()
    on_stdin = "{prompt}" not in " ".join(tools[tool]["cmd"])
    p = subprocess.Popen(cmd, cwd=ws, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    try:
        raw, _ = p.communicate(task["prompt"].strip() if on_stdin else "", timeout=timeout_min * 60)
        code = p.returncode
    except subprocess.TimeoutExpired:
        kill_tree(p)
        raw, code = p.communicate()[0] or "", "timeout"
    if temp_home:
        drop_temp_home(temp_home)
    minutes = round((time.time() - start) / 60, 2)
    skills = set(home_skills(HOME)) | set(home_skills(arm.get("home")))
    final, tokens, cost, fired = parse_output(raw, skills)
    passed, fails = check(task, ws, final) if code != "timeout" else (False, ["timeout"])
    wanted = {t.split(":", 1)[1] for t in task.get("tags", []) if t.startswith("skill:")}
    result = {"task": task["id"], "tool": tool, "arm": arm["name"], "pass": passed, "fails": fails,
              "exit": code, "minutes": minutes, "tokens": tokens, "cost_usd": cost, "fired": fired,
              "false_triggers": sorted(set(fired) - wanted), "final": final[-1500:]}
    if keep:
        result["workspace"] = str(root)
    else:
        rmtree(root)
    return result


# ---------- arms and gate ----------

def make_arms(args):
    rules = args.user_rules
    if args.sweep:
        return [{"name": "off", "home": None, "rules": False}, {"name": "on", "home": str(HOME), "user_rules": rules}]
    if args.skill:
        return [{"name": f"without {args.skill}", "home": str(HOME), "user_rules": rules, "without": [args.skill]},
                {"name": f"with {args.skill}", "home": str(HOME), "user_rules": rules}]
    base_dir = Path(tempfile.mkdtemp(prefix="home-base-"))
    subprocess.run(["git", "worktree", "add", "--detach", str(base_dir), args.base], cwd=HOME, check=True)
    return [{"name": f"base {args.base}", "home": str(base_dir), "user_rules": rules},
            {"name": "branch", "home": str(HOME), "user_rules": rules}]


def verdict(results, arms, change):
    a, b = arms[0]["name"], arms[1]["name"]
    lines, ok = [], True
    for tool in sorted({r["tool"] for r in results}):
        ra = [r for r in results if r["tool"] == tool and r["arm"] == a]
        rb = [r for r in results if r["tool"] == tool and r["arm"] == b]
        pa, pb = sum(r["pass"] for r in ra), sum(r["pass"] for r in rb)
        n = max(len(ra), 1)
        task_drop = any(sum(r["pass"] for r in rb if r["task"] == t) <
                        sum(r["pass"] for r in ra if r["task"] == t) - 1 for t in {r["task"] for r in ra})
        regress = pb < pa - 1 or task_drop
        win = (pb - pa) / n >= 0.15 and not regress
        good = win if change == "add" else not regress
        ok = ok and good
        lines.append(f"{tool}: {a} {pa}/{len(ra)}, {b} {pb}/{len(rb)}, "
                     f"{'clear win' if win else 'regression' if regress else 'no clear difference'}")
    return ok, lines


def summary_md(results, arms, ok, lines, mode):
    out = [f"# Eval: {mode}", "", f"Gate: **{'PASS' if ok else 'FAIL'}**", ""] + [f"- {l}" for l in lines]
    out += ["", "| Task | Tool | Arm | Passed | Tokens (avg) | Minutes (avg) | False triggers |", "| --- | --- | --- | --- | --- | --- | --- |"]
    keys = sorted({(r["task"], r["tool"], r["arm"]) for r in results})
    for t, tool, arm in keys:
        rs = [r for r in results if (r["task"], r["tool"], r["arm"]) == (t, tool, arm)]
        ft = sum(len(r["false_triggers"]) for r in rs)
        out.append(f"| {t} | {tool} | {arm} | {sum(r['pass'] for r in rs)}/{len(rs)} | "
                   f"{sum(r['tokens'] for r in rs) // len(rs)} | {sum(r['minutes'] for r in rs) / len(rs):.1f} | {ft} |")
    cost = sum(r["cost_usd"] or 0 for r in results)
    out += ["", f"Reported cost: ${cost:.2f} over {len(results)} runs. Limit: about 15 tasks x 3 runs only spots big effects; small changes pass on no harm and claim no win."]
    return "\n".join(out) + "\n"


# ---------- promptfoo hooks ----------

def call_api(prompt, options, context):
    cfg = options.get("config", {})
    ledger = Path(cfg["ledger"])
    spent = sum(float(x) for x in ledger.read_text().split()) if ledger.exists() else 0.0
    if spent >= cfg["max_usd"]:
        return {"error": f"cost cap ${cfg['max_usd']} reached"}
    data, tools = load_tasks(cfg["tasks"])
    task = next(t for t in data["tasks"] if t["id"] == context["vars"]["task_id"])
    r = run_one(task, cfg["tool"], cfg["arm"], tools, Path(cfg["tasks"]).parent, keep=cfg.get("keep", False),
                model=cfg.get("model"))
    with ledger.open("a") as f:
        f.write(f"{r['cost_usd'] or 0}\n")
    with Path(cfg["runs"]).open("a", encoding="utf-8") as f:
        f.write(json.dumps(r) + "\n")
    return {"output": json.dumps(r), "tokenUsage": {"total": r["tokens"]}, "cost": r["cost_usd"] or 0}


def get_assert(output, context):
    r = json.loads(output)
    return {"pass": r["pass"], "score": 1.0 if r["pass"] else 0.0, "reason": "; ".join(r["fails"]) or "check passed"}


def run_promptfoo(tasks, arms, args, out_dir, tasks_path):
    import yaml
    me = "file://" + os.path.relpath(Path(__file__).resolve(), out_dir).replace("\\", "/")  # Windows: no drive letter
    providers = [{"id": me, "label": f"{tool} | {arm['name']}",
                  "config": {"tool": tool, "arm": arm, "tasks": str(tasks_path), "runs": str(out_dir / "runs.jsonl"),
                             "ledger": str(out_dir / "ledger.txt"), "max_usd": args.max_usd, "keep": args.keep,
                             "model": args.model}}
                 for tool in args.tools.split(",") for arm in arms]
    tests = [{"description": t["id"], "vars": {"task_id": t["id"], "prompt": t["prompt"]},
              "assert": [{"type": "python", "value": me}]} for t in tasks]
    config = out_dir / "promptfooconfig.yaml"
    config.write_text(yaml.safe_dump({"description": out_dir.name, "prompts": ["{{prompt}}"],
                                      "providers": providers, "tests": tests}), encoding="utf-8")
    npx = shutil.which("npx") or "npx"
    env = {**os.environ, "PROMPTFOO_PYTHON": sys.executable, "PROMPTFOO_DISABLE_TELEMETRY": "1"}
    subprocess.run([npx, "-y", PROMPTFOO, "eval", "-c", str(config), "--repeat", str(args.runs),
                    "--max-concurrency", "1", "--no-cache", "-o", str(out_dir / "promptfoo-results.json")],
                   cwd=out_dir, env=env)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tasks", type=Path)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--skill")
    mode.add_argument("--base")
    mode.add_argument("--sweep", action="store_true")
    ap.add_argument("--tools", default="claude,codex")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--change", choices=["add", "remove", "wording"])
    ap.add_argument("--tags")
    ap.add_argument("--holdout", action="store_true")
    ap.add_argument("--user-rules", type=Path)
    ap.add_argument("--max-usd", type=float, default=20.0)
    ap.add_argument("--engine", choices=["promptfoo", "native"], default="promptfoo")
    ap.add_argument("--model", help="model for opencode (for example a local model via LiteLLM)")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.base and not args.change:
        ap.error("--base needs --change add|remove|wording")
    tasks_path = args.tasks.resolve()
    if args.user_rules is None:
        default = HOME.parent / "home-private" / "user" / "AGENTS.md"
        args.user_rules = default if default.exists() else None
    args.user_rules = str(Path(args.user_rules).resolve()) if args.user_rules else None
    data, tools = load_tasks(tasks_path)
    tasks = pick_tasks(data, args, changed_tags(args.base) if args.base else set())
    if not tasks:
        sys.exit("no tasks match; tag golden tasks with skill:<name> or rule:<name>")
    arms = make_arms(args)
    label = "sweep" if args.sweep else f"skill-{args.skill}" if args.skill else f"base-{args.base}"
    out_dir = tasks_path.parent / "results" / f"{datetime.datetime.now():%Y%m%d-%H%M}-{label.replace('/', '-')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{len(tasks)} tasks x {len(arms)} arms x {args.runs} runs x {len(args.tools.split(','))} tools -> {out_dir}")
    if args.dry_run:
        for t in tasks:
            for arm in arms:
                run_one(t, args.tools.split(",")[0], arm, tools, tasks_path.parent, dry=True)
        return
    if args.engine == "promptfoo":
        run_promptfoo(tasks, arms, args, out_dir, tasks_path)
    else:
        spent = 0.0
        with (out_dir / "runs.jsonl").open("a", encoding="utf-8") as f:
            for t in tasks:
                for tool in args.tools.split(","):
                    for arm in arms:
                        for _ in range(args.runs):
                            if spent >= args.max_usd:
                                print(f"cost cap ${args.max_usd} reached, stopping")
                                break
                            r = run_one(t, tool, arm, tools, tasks_path.parent, keep=args.keep, model=args.model)
                            spent += r["cost_usd"] or 0
                            f.write(json.dumps(r) + "\n")
                            f.flush()
                            print(f"{t['id']} {tool} {arm['name']}: {'pass' if r['pass'] else 'FAIL'} "
                                  f"{r['minutes']}m {r['tokens']}t ${r['cost_usd'] or 0:.2f} fired={r['fired']}")
    runs_file = out_dir / "runs.jsonl"
    results = [json.loads(l) for l in runs_file.read_text(encoding="utf-8").splitlines()] if runs_file.exists() else []
    ok, lines = verdict(results, arms, "add" if (args.sweep or args.skill) else args.change)
    md = summary_md(results, arms, ok, lines, label)
    (out_dir / "summary.md").write_text(md, encoding="utf-8")
    print(md)
    if args.sweep:
        line = f"{datetime.date.today()}: " + "; ".join(lines)
        (tasks_path.parent / "results" / "latest-sweep.json").write_text(json.dumps({"line": line}), encoding="utf-8")
    if args.base:
        subprocess.run(["git", "worktree", "remove", "--force", arms[0]["home"]], cwd=HOME)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
