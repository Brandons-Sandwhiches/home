#!/usr/bin/env python3
"""Mechanical checks for a Karpathy-style LLM wiki (conventions version 2).

Usage: wiki-lint.py <wiki_dir>

Pass the wiki directory of the project you are linting. Paths in `sources`
resolve against its parent (the project root).

Errors (exit 1): bad frontmatter, missing sources, broken file or heading
links, pages missing from index.md, a page over 300 lines, the project's
AGENTS.md over 60 lines.
Warnings: stale pages (a source changed in git after `updated:`), no links
in or out, tags used only once.
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

if sys.version_info < (3, 8):
    sys.exit("wiki-lint needs Python 3.8 or later")

PAGE_CAP, AGENTS_CAP = 300, 60
REQUIRED = ["title", "tags", "sources", "updated"]
UNFRONTED = {"index.md", "log.md"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TAG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
INLINE_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REF_DEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+\"[^\"]*\")?\s*$", re.M)
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"(`+).*?\1")


def slug(text):
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*~]", "", text).strip().lower()
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", text))


def prose_lines(text):
    out, inside = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
            out.append("")
        else:
            out.append("" if inside else CODE_SPAN.sub("", line))
    return out


def scalar(value):
    return value.strip().strip("'\"")


def frontmatter(text):
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    fields, key = {}, None
    for line in text[4:end].splitlines():
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key and isinstance(fields.get(key), list):
            fields[key].append(scalar(item.group(1)))
            continue
        m = re.match(r"^([\w-]+):\s*(.*?)\s*(#.*)?$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            fields[key] = [scalar(v) for v in value[1:-1].split(",") if v.strip()]
        else:
            fields[key] = scalar(value) if value else []
    return fields


def as_list(value):
    return value if isinstance(value, list) else [value] if value else []


def is_url(target):
    return re.match(r"^[a-z][a-z0-9+.-]*://", target) is not None


def anchors(path, cache={}):
    if path not in cache:
        seen, result = {}, set()
        for line in prose_lines(path.read_text(encoding="utf-8")):
            m = HEADING.match(line)
            if m:
                base = slug(m.group(1))
                n = seen.get(base, 0)
                seen[base] = n + 1
                result.add(base if n == 0 else f"{base}-{n}")
        cache[path] = result
    return cache[path]


def last_change(root, path):
    """Date (YYYY-MM-DD) of the last commit touching path, or None outside git."""
    try:
        out = subprocess.run(["git", "-c", "safe.directory=*", "log", "-1", "--format=%cs", "--", str(path)],
                             cwd=root, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() or None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    wiki_dir = Path(sys.argv[1]).resolve()
    if not wiki_dir.is_dir():
        sys.exit(f"no wiki directory at {wiki_dir}")
    root = wiki_dir.parent
    pages = sorted(p for p in wiki_dir.rglob("*.md") if "archive" not in p.relative_to(wiki_dir).parts)
    errors, warnings, meta = [], [], {}
    inbound, outbound, tags = Counter(), Counter(), Counter()

    agents = root / "AGENTS.md"
    if agents.exists():
        n = len(agents.read_text(encoding="utf-8").splitlines())
        if n > AGENTS_CAP:
            errors.append(f"AGENTS.md: {n} lines, cap is {AGENTS_CAP}")
    for name in UNFRONTED:
        if not (wiki_dir / name).exists():
            errors.append(f"{name}: missing")

    for page in pages:
        rel = page.relative_to(wiki_dir).as_posix()
        text = page.read_text(encoding="utf-8")
        n = len(text.splitlines())
        if n > PAGE_CAP:
            errors.append(f"{rel}: {n} lines, cap is {PAGE_CAP} (split it or archive old parts)")
        if page.name in UNFRONTED:
            continue
        fm = frontmatter(text)
        if fm is None:
            errors.append(f"{rel}: no frontmatter")
            continue
        meta[page.resolve()] = fm
        for key in REQUIRED:
            if not fm.get(key):
                errors.append(f"{rel}: frontmatter '{key}' missing or empty")
        for key in ("updated", "ratified"):
            if fm.get(key) and not DATE.match(str(fm[key])):
                errors.append(f"{rel}: {key} '{fm[key]}' is not YYYY-MM-DD")
        for tag in as_list(fm.get("tags")):
            tags[tag] += 1
            if not TAG.match(tag):
                errors.append(f"{rel}: tag '{tag}' is not lowercase kebab-case")
        newest = None
        for ref in as_list(fm.get("sources")):
            if is_url(ref):
                continue
            src = (root / ref.split("#")[0]).resolve()
            if not src.exists():
                errors.append(f"{rel}: source '{ref}' does not exist")
                continue
            changed = last_change(root, src)
            if changed and (newest is None or changed > newest):
                newest = changed
        updated = str(fm.get("updated", ""))
        if newest and DATE.match(updated) and newest > updated:
            warnings.append(f"{rel}: stale, a source changed {newest} after updated {updated}")

    indexed = set()
    for page in pages:
        rel = page.relative_to(wiki_dir).as_posix()
        body = "\n".join(prose_lines(page.read_text(encoding="utf-8")))
        for target in INLINE_LINK.findall(body) + REF_DEF.findall(body):
            if is_url(target) or target.startswith("mailto:"):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (page.parent / file_part).resolve() if file_part else page.resolve()
            if not dest.exists():
                errors.append(f"{rel}: broken link {target}")
                continue
            if dest.suffix == ".md" and anchor and anchor not in anchors(dest):
                errors.append(f"{rel}: no heading '#{anchor}' in {dest.name}")
            if page.name == "index.md":
                indexed.add(dest)
            elif dest in meta and dest != page.resolve():
                outbound[page.resolve()] += 1
                inbound[dest] += 1

    for page in meta:
        rel = page.relative_to(wiki_dir).as_posix()
        if page not in indexed:
            errors.append(f"{rel}: not listed in index.md")
        if not inbound[page] and not outbound[page] and len(meta) > 1:
            warnings.append(f"{rel}: no links to or from other wiki pages")
    for tag, count in sorted(tags.items()):
        if count == 1 and len(meta) > 3:
            warnings.append(f"tag '{tag}' is used on only one page")

    for line in errors:
        print(f"error   {line}")
    for line in warnings:
        print(f"warning {line}")
    print(f"{len(pages)} pages, {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
