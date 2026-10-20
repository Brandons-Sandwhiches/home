#!/usr/bin/env python3
"""Home base: every project's state on one screen, read from its backlog.

Usage:
  dashboard.py [--root DIR] [--out FILE] [--tag TAG[,TAG]] [--print]
  dashboard.py --here [PROJECT]     where this project left off, and the next 3

--root  the workspaces folder (default: the folder that holds home)
--out   the page to write (default: <root>/work/dashboard.html)
--tag   the sign-off tag(s) (default: $HOME_SIGNOFF_TAG or needs-owner)
--print also print the summary as text (what "what's up" reads)

A project is a folder under --root with backlog/ or AGENTS.md. home,
home-private, work, archive and dot-folders are skipped. A project whose
.agents/space says `work` or `client` shows only its needs-you count and
titles, never its content. Read-only except for the --out file.
"""
import argparse
import datetime
import html
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
SKIP = {"home", "home-private", "work", "archive"}
PRIORITY = {"high": 0, "medium": 1, "low": 2}
PARKED_DAYS = 30
TEXT = {".md", ".py", ".js", ".ts", ".json", ".yml", ".yaml", ".toml", ".txt", ".html", ".css", ".sh", ".ps1"}


def frontmatter(text):
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    fields, key = {}, None
    for line in text[4:end].splitlines():
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key and isinstance(fields.get(key), list):
            fields[key].append(item.group(1).strip().strip("'\""))
            continue
        m = re.match(r"^([\w-]+):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            fields[key] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        else:
            fields[key] = value.strip("'\"") if value else []
    return fields


def as_list(v):
    return v if isinstance(v, list) else [v] if v else []


def git(root, *args):
    try:
        out = subprocess.run(["git", "-c", "safe.directory=*", *args], cwd=root,
                             capture_output=True, text=True, encoding="utf-8", timeout=30)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def task_num(task):
    m = re.search(r"(\d+)", str(task.get("id", "")))
    return int(m.group(1)) if m else 0


def read_tasks(project):
    tasks = []
    for path in sorted((project / "backlog" / "tasks").glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(text)
        if not fm:
            continue
        notes = re.search(r"## Implementation Notes\s*\n(.*?)(?:\n## |\Z)", text, re.S)
        fm["note"] = notes.group(1).strip().splitlines()[-1].strip() if notes and notes.group(1).strip() else ""
        fm["when"] = str(fm.get("updated_date") or fm.get("created_date") or "")
        fm["path"] = path
        tasks.append(fm)
    return tasks


def next_tasks(tasks, n=3):
    open_ = [t for t in tasks if t.get("status") != "Done"]
    open_.sort(key=lambda t: (t.get("status") != "In Progress", PRIORITY.get(t.get("priority"), 3),
                              float(t.get("ordinal") or 1e9), task_num(t)))
    return open_[:n]


def stale_pages(project):
    stale = []
    for page in (project / "wiki").rglob("*.md") if (project / "wiki").is_dir() else []:
        if "archive" in page.parts:
            continue
        fm = frontmatter(page.read_text(encoding="utf-8", errors="replace"))
        updated = str(fm.get("updated", ""))
        for src in as_list(fm.get("sources")):
            if "://" in src or not (project / src).exists():
                continue
            changed = git(project, "log", "-1", "--format=%cs", "--", src)
            if changed and updated and changed > updated:
                stale.append(page.relative_to(project).as_posix())
                break
    return stale


def counts(project):
    listed = git(project, "ls-files")
    files = [project / f for f in listed.splitlines()] if listed else [
        p for p in project.rglob("*") if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts]
    lines = 0
    for f in files:
        if f.suffix.lower() in TEXT and f.exists():
            try:
                lines += sum(1 for _ in f.open(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    skills = sum(1 for d in (".agents/skills", ".claude/skills") for _ in (project / d).glob("*/SKILL.md"))
    return len(files), lines, skills


def summarize(project, tags):
    tasks = read_tasks(project)
    space = (project / ".agents" / "space").read_text(encoding="utf-8").strip().lower() \
        if (project / ".agents" / "space").exists() else ""
    own_repo = Path(git(project, "rev-parse", "--show-toplevel") or "/nonexistent").resolve() == project.resolve()
    last_commit = git(project, "log", "-1", "--format=%cs %s") if own_repo else ""
    dates = [t["when"][:10] for t in tasks if t["when"]] + ([last_commit[:10]] if last_commit else [])
    last = max(dates) if dates else ""
    if not last:
        stamp = max((p.stat().st_mtime for p in project.rglob("*") if p.is_file() and ".git" not in p.parts), default=0)
        last = datetime.date.fromtimestamp(stamp).isoformat() if stamp else ""
    idle = (datetime.date.today() - datetime.date.fromisoformat(last)).days if last else 9999
    doing = [t for t in tasks if t.get("status") == "In Progress"]
    recent = sorted(doing or tasks, key=lambda t: (t["when"], task_num(t)))[-1] if tasks else None
    needs = [t for t in tasks if t.get("status") != "Done" and set(as_list(t.get("labels"))) & tags]
    restricted = space in ("work", "client")
    lessons = [] if restricted else [p.stem for p in (project / "wiki" / "lessons").glob("*.md")]
    files, lines, skills = (0, 0, 0) if restricted else counts(project)
    return {"name": project.name, "path": project, "restricted": restricted,
            "has_backlog": (project / "backlog").is_dir(), "tasks": tasks, "recent": recent,
            "last_commit": last_commit, "last": last, "idle": idle, "next": next_tasks(tasks),
            "needs": needs, "lessons": lessons, "stale": [] if restricted else stale_pages(project),
            "files": files, "lines": lines, "skills": skills}


def left_off_text(p):
    out = [f"{p['name']}:"]
    r = p["recent"]
    if r:
        note = f" ({r['note']})" if r["note"] else ""
        out.append(f"  Left off: {r.get('id')} {r.get('title')} [{r.get('status')}], {r['when'][:10]}{note}")
    elif not p["has_backlog"]:
        out.append("  Left off: no backlog/ yet")
    else:
        out.append("  Left off: backlog is empty")
    if p["last_commit"]:
        out.append(f"  Last commit: {p['last_commit']}")
    out.append("  Next: " + ("; ".join(f"{t.get('id')} {t.get('title')}" for t in p["next"]) or "nothing open"))
    if p["needs"]:
        out.append("  Needs you: " + "; ".join(f"{t.get('id')} {t.get('title')}" for t in p["needs"]))
    return "\n".join(out)


def skill_log(projects):
    stats = defaultdict(lambda: {"uses": 0, "pass": 0, "fail": 0, "projects": set()})
    for p in projects:
        log = p["path"] / ".agents" / "skill-log.jsonl"
        for line in log.read_text(encoding="utf-8").splitlines() if log.exists() else []:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            s = stats[e.get("skill", "?")]
            s["uses"] += 1
            s["projects"].add(p["name"])
            if e.get("check") in ("pass", "fail"):
                s[e["check"]] += 1
    return stats


def link(path, label):
    return f'<a href="{html.escape(path.resolve().as_uri())}">{html.escape(label)}</a>'


def render(projects, home_skills, stats, sweep, tags):
    own = [p for p in projects if not p["restricted"]]
    lesson_count = defaultdict(list)
    for p in own:
        for slug in p["lessons"]:
            lesson_count[slug].append(p["name"])
    repeated = {s: ps for s, ps in lesson_count.items() if len(ps) >= 3}
    needs = [(p, t) for p in projects for t in p["needs"]]
    active = [p for p in own if p["idle"] < PARKED_DAYS]
    parked = [p for p in own if p["idle"] >= PARKED_DAYS]
    e = html.escape
    rows = []
    rows.append(f"<h2>Needs you <span class=n>{len(needs) + len(repeated)}</span></h2><ul>")
    for p, t in needs:
        rows.append(f"<li><b>{e(p['name'])}</b> {e(str(t.get('id')))} {e(str(t.get('title')))}</li>")
    for s, ps in repeated.items():
        rows.append(f"<li><b>lesson in {len(ps)} projects</b> {e(s)}: make it a user rule? ({e(', '.join(ps))})</li>")
    rows.append("</ul>" if needs or repeated else "<p class=m>Nothing waiting on you.</p></ul>")
    rows.append(f"<h2>Active <span class=n>{len(active)}</span></h2>")
    for p in sorted(active, key=lambda p: p["idle"]):
        r = p["recent"]
        left = f"{r.get('id')} {r.get('title')} [{r.get('status')}]" if r else "no tasks yet"
        nxt = "".join(f"<li>{e(str(t.get('id')))} {e(str(t.get('title')))}</li>" for t in p["next"]) or "<li class=m>nothing open</li>"
        stale = f" · <span class=w>{len(p['stale'])} stale wiki pages</span>" if p["stale"] else ""
        rows.append(f"<section><h3>{link(p['path'], p['name'])}</h3>"
                    f"<p class=m>{p['last'] or 'never'} · {link(p['path'] / 'backlog', 'backlog')} · "
                    f"{link(p['path'] / 'wiki' / 'index.md', 'wiki')} · {p['files']} files, {p['lines']} lines{stale}</p>"
                    f"<p><b>Left off:</b> {e(left)}</p><ol>{nxt}</ol></section>")
    rows.append(f"<h2>Parked <span class=n>{len(parked)}</span></h2><ul>")
    for p in sorted(parked, key=lambda p: -p["idle"]):
        rows.append(f"<li>{link(p['path'], p['name'])} · {link(p['path'] / 'backlog', 'backlog')} · "
                    f"{link(p['path'] / 'wiki' / 'index.md', 'wiki')} <span class=m>idle {p['idle']} days. Archive it?</span></li>")
    rows.append("</ul>")
    restricted = [p for p in projects if p["restricted"]]
    if restricted:
        rows.append("<h2>Work and client spaces</h2><ul>")
        for p in restricted:
            titles = "; ".join(str(t.get("title")) for t in p["needs"])
            rows.append(f"<li><b>{e(p['name'])}</b> needs you: {len(p['needs'])}{e(' · ' + titles) if titles else ''}</li>")
        rows.append("</ul>")
    rows.append(f"<h2>Size</h2><p class=m>home: {home_skills} skills. Projects: {sum(p['files'] for p in own)} files, "
                f"{sum(p['lines'] for p in own)} lines.</p>")
    if stats:
        rows.append("<table><tr><th>Skill</th><th>Used</th><th>Projects</th><th>Check passed</th></tr>")
        for name, s in sorted(stats.items()):
            checked = s["pass"] + s["fail"]
            rate = f"{s['pass']}/{checked}" if checked else "no checks"
            rows.append(f"<tr><td>{e(name)}</td><td>{s['uses']}</td><td>{len(s['projects'])}</td><td>{rate}</td></tr>")
        rows.append("</table>")
    if sweep:
        rows.append(f"<p><b>Evals, home on vs off:</b> {e(sweep)}</p>")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return PAGE.format(now=now, tag=e(", ".join(sorted(tags))), body="\n".join(rows))


PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Home Base</title>
<style>
:root{{--bg:#f6f7f9;--ink:#17212b;--m:#5b6876;--line:#d5dbe2;--acc:#c2620f;--warn:#a33}}
@media (prefers-color-scheme:dark){{:root{{--bg:#11161c;--ink:#e4eaf0;--m:#97a5b3;--line:#2b3743;--acc:#f0913f;--warn:#f77}}}}
body{{background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif;max-width:860px;margin:0 auto;padding:16px}}
h1{{margin:.2em 0}} h2{{border-bottom:1px solid var(--line);padding-bottom:4px;margin-top:1.4em}}
h3{{margin:.6em 0 0}} .n{{color:var(--acc)}} .m{{color:var(--m)}} .w{{color:var(--warn)}}
a{{color:inherit}} section{{border-left:3px solid var(--acc);padding-left:12px;margin:12px 0}}
table{{border-collapse:collapse}} td,th{{border:1px solid var(--line);padding:4px 8px;text-align:left}}
</style></head><body><h1>Home Base</h1><p class=m>Rebuilt {now}. Sign-off tag: {tag}.</p>
{body}
</body></html>
"""


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=HOME.parent)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--tag", default=os.environ.get("HOME_SIGNOFF_TAG", "needs-owner"))
    ap.add_argument("--print", action="store_true")
    ap.add_argument("--here", nargs="?", const=".", type=Path)
    ap.add_argument("--sweep", type=Path, help="latest eval sweep summary (JSON with a 'line' field)")
    a = ap.parse_args()
    tags = {t.strip() for t in a.tag.split(",") if t.strip()}
    if a.here:
        print(left_off_text(summarize(a.here.resolve(), tags)))
        return
    root = a.root.resolve()
    dirs = [d for d in sorted(root.iterdir()) if d.is_dir() and d.name not in SKIP and not d.name.startswith(".")
            and ((d / "backlog").is_dir() or (d / "AGENTS.md").exists())]
    projects = [summarize(d, tags) for d in dirs]
    home_skills = sum(1 for _ in (HOME / "skills").glob("*/*/SKILL.md"))
    sweep = ""
    sweep_file = a.sweep or root / "home-private" / "evals" / "results" / "latest-sweep.json"
    if sweep_file.exists():
        sweep = json.loads(sweep_file.read_text(encoding="utf-8")).get("line", "")
    out = a.out or root / "work" / "dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(projects, home_skills, skill_log([p for p in projects if not p["restricted"]]), sweep, tags),
                   encoding="utf-8")
    if a.print:
        for p in projects:
            if p["restricted"]:
                print(f"{p['name']}: needs you {len(p['needs'])}" + "".join(f"\n  {t.get('title')}" for t in p["needs"]))
            else:
                print(left_off_text(p) + (f"\n  Parked: idle {p['idle']} days" if p["idle"] >= PARKED_DAYS else ""))
    print(f"wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
