#!/usr/bin/env python3
"""Repo checks for home. Usage: python scripts/repo-lint.py

- Pointer files (CLAUDE.md, GEMINI.md, in home and the templates) contain only `@AGENTS.md`.
- Every AGENTS.md is 60 lines or fewer. No em-dashes in markdown.
- Every skill has SKILL.md (name, description), agents/openai.yaml, matching
  invocation settings, and a line in its bucket README.
- The template's repo-check.py and home's own copy are identical.
- Home stays generic: no personal names, machines or paths (see PERSONAL).
- No trust ladder words in skills, wiki or templates.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POINTERS = ["CLAUDE.md", "GEMINI.md", "templates/project/CLAUDE.md", "templates/project/GEMINI.md",
            "templates/work/CLAUDE.md", "templates/work/GEMINI.md"]
AGENTS_CAP = 60
# Kept as fragments so this file doesn't trip its own check.
PERSONAL = ["bran" + "don", "black" + "box", "jah" + "nel", "at" + "las", "bct" + "9321", "30" + "90",
            "c:\\" + "users", "h:" + "\\"]
LADDER = ["eleva" + "tion", "pro" + "mote"]
SKIP_DIRS = {".git", "node_modules", "__pycache__", "results"}


def frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    return dict(re.findall(r"^([\w-]+):\s*(.*)$", m.group(1), re.M)) if m else None


def files():
    for path in ROOT.rglob("*"):
        if path.is_file() and not SKIP_DIRS & set(path.relative_to(ROOT).parts):
            yield path


def main():
    errors = []
    for rel in POINTERS:
        path = ROOT / rel
        if not path.exists() or path.read_text(encoding="utf-8").strip() != "@AGENTS.md":
            errors.append(f"{rel}: must contain only @AGENTS.md")
    for path in files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        low = text.lower()
        for word in PERSONAL:
            if word in low and rel != "scripts/repo-lint.py":
                errors.append(f"{rel}: personal detail '{word}' (it belongs in home-private)")
        if rel.split("/")[0] in ("skills", "wiki", "templates"):
            for word in LADDER:
                if word in low:
                    errors.append(f"{rel}: trust-ladder word '{word}'")
        if path.suffix == ".md":
            for n, line in enumerate(text.splitlines(), 1):
                if "\u2014" in line:
                    errors.append(f"{rel}:{n}: em-dash")
        if path.name == "AGENTS.md" and len(text.splitlines()) > AGENTS_CAP:
            errors.append(f"{rel}: {len(text.splitlines())} lines, cap is {AGENTS_CAP}")
    for skill_md in sorted((ROOT / "skills").glob("*/*/SKILL.md")):
        skill = skill_md.parent
        rel = skill.relative_to(ROOT).as_posix()
        fm = frontmatter(skill_md.read_text(encoding="utf-8"))
        if not fm or fm.get("name") != skill.name or not fm.get("description"):
            errors.append(f"{rel}: SKILL.md needs name: {skill.name} and a description")
            continue
        yaml = skill / "agents" / "openai.yaml"
        if not yaml.exists():
            errors.append(f"{rel}: missing agents/openai.yaml")
        else:
            user_only = fm.get("disable-model-invocation") == "true"
            codex_off = "allow_implicit_invocation: false" in yaml.read_text(encoding="utf-8")
            if user_only != codex_off:
                errors.append(f"{rel}: invocation differs between SKILL.md and openai.yaml")
        readme = skill.parent / "README.md"
        if not readme.exists() or f"]({skill.name}/SKILL.md)" not in readme.read_text(encoding="utf-8"):
            errors.append(f"{rel}: not listed in {skill.parent.name}/README.md")
    for rel in ("scripts/repo-check.py", ".githooks/pre-commit", ".githooks/pre-push",
                ".github/workflows/ci.yml", ".github/pull_request_template.md"):
        a, b = ROOT / rel, ROOT / "templates" / "project" / rel
        if not a.exists() or not b.exists() or a.read_bytes() != b.read_bytes():
            errors.append(f"{rel} and templates/project/{rel} differ")
    for line in errors:
        print(f"error {line}")
    print(f"{len(errors)} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
