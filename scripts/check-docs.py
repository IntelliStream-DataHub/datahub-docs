#!/usr/bin/env python3
"""Static checks for the datahub-docs Docusaurus site.

Verifies internal links resolve, anchors exist, and the MDX has no JSX pitfalls
(raw `class=`, unescaped braces / angle brackets in prose).
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")

# ---------------------------------------------------------------- collect routes
routes = {}          # route -> file
anchors = {}         # route -> set of anchor ids
files = []

for dirpath, _dirnames, filenames in os.walk(DOCS):
    for fn in sorted(filenames):
        if not fn.endswith((".md", ".mdx")):
            continue
        files.append(os.path.join(dirpath, fn))


def slugify(text):
    """Mimic github-slugger, which Docusaurus uses.

    The key detail: it replaces each space individually (` ` -> `-`), so a
    removed punctuation character between two spaces yields a DOUBLE hyphen.
    """
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)   # links -> text
    text = re.sub(r"<[^>]+>", "", text)                     # inline html
    text = re.sub(r"[*_]", "", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)                    # drop punctuation
    return text.replace(" ", "-")                           # NOT \s+ -> one dash


def frontmatter(src):
    if not src.startswith("---"):
        return {}, src
    end = src.find("\n---", 3)
    if end == -1:
        return {}, src
    raw = src[3:end]
    fm = {}
    for line in raw.splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip("'\"")
    return fm, src[end + 4:]


for path in files:
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    fm, body = frontmatter(src)
    rel = os.path.relpath(path, DOCS)
    route = "/" + re.sub(r"\.(md|mdx)$", "", rel)
    if "slug" in fm:
        route = fm["slug"]
    routes[route.rstrip("/") or "/"] = path

    ids = set()
    # strip fenced code before scanning headings
    scan = re.sub(r"```.*?```", "", body, flags=re.S)
    for line in scan.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not m:
            continue
        heading = m.group(2).strip()
        explicit = re.search(r"\{#([\w-]+)\}\s*$", heading)
        if explicit:
            ids.add(explicit.group(1))
            heading = heading[: explicit.start()].strip()
        ids.add(slugify(heading))
    anchors[route.rstrip("/") or "/"] = ids

# ---------------------------------------------------------------- check links
problems = []
link_re = re.compile(r"\]\((/[^)\s]*)\)")
to_re = re.compile(r'\bto=["\'](/[^"\']*)["\']')

for path in files:
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    body = re.sub(r"```.*?```", "", src, flags=re.S)
    rel = os.path.relpath(path, DOCS)

    targets = [m.group(1) for m in link_re.finditer(body)]
    targets += [m.group(1) for m in to_re.finditer(body)]

    for target in targets:
        page, _, anchor = target.partition("#")
        page = page.rstrip("/") or "/"
        if page not in routes:
            problems.append(f"{rel}: broken link target -> {target}")
        elif anchor and anchor not in anchors.get(page, set()):
            problems.append(f"{rel}: missing anchor -> {target}")

    # static assets referenced with src="/..." must exist under static/
    for m in re.finditer(r'\bsrc=["\'](/[^"\']*)["\']', body):
        asset = os.path.join(ROOT, "static", m.group(1).lstrip("/"))
        if not os.path.exists(asset):
            problems.append(f"{rel}: missing static asset -> {m.group(1)}")

# ---------------------------------------------------------------- MDX pitfalls
for path in files:
    if not path.endswith(".mdx"):
        continue
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    rel = os.path.relpath(path, DOCS)
    # remove fenced + inline code, which MDX does not parse as JSX
    scan = re.sub(r"```.*?```", "", src, flags=re.S)
    scan = re.sub(r"`[^`\n]*`", "", scan)

    for m in re.finditer(r"<[a-zA-Z][^>]*\sclass=", scan):
        problems.append(f"{rel}: raw `class=` in JSX (use className) near: {m.group(0)[:60]}")

    for i, line in enumerate(scan.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith(("---", "|")):
            continue
        # `## Heading {#explicit-id}` is valid Docusaurus syntax, not a JSX brace
        probe = re.sub(r"\{#[\w-]+\}\s*$", "", stripped) if stripped.startswith("#") else stripped
        if "{" in probe:
            problems.append(f"{rel}:{i}: unescaped '{{' in MDX prose: {stripped[:80]}")
        # a bare `<` followed by a non-tag char is a JSX parse error
        for m in re.finditer(r"<(?![/a-zA-Z!])", probe):
            problems.append(f"{rel}:{i}: bare '<' in MDX prose: {stripped[:80]}")
            break

# ------------------------------------------------------- themed inline figures
# Figures under src/figures/ are inlined by SVGR so page CSS can theme them.
# That only works if they carry NO colour and NO <style> of their own.
FIG_DIR = os.path.join(ROOT, "src", "figures")
if os.path.isdir(FIG_DIR):
    import xml.dom.minidom

    for fn in sorted(os.listdir(FIG_DIR)):
        if not fn.endswith(".svg"):
            continue
        path = os.path.join(FIG_DIR, fn)
        rel = os.path.join("src/figures", fn)
        with open(path, encoding="utf-8") as fh:
            svg = fh.read()

        try:
            xml.dom.minidom.parse(path)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{rel}: malformed XML: {exc}")

        for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", svg):
            problems.append(f"{rel}: hard-coded colour {m.group(0)} — themed figures must use CSS classes")
        if "<style" in svg:
            problems.append(f"{rel}: contains <style> — put CSS in custom.css so [data-theme] can reach it")
        for m in re.finditer(r'\b(fill|stroke)="(?!none")([^"]*)"', svg):
            problems.append(f"{rel}: literal {m.group(1)}=\"{m.group(2)}\" — use a class instead")
        if 'viewBox="0 0 760' not in svg:
            problems.append(f"{rel}: expected a 760-wide viewBox for consistent scaling")

    # every themed figure should actually be imported somewhere
    imported = set()
    for path in files:
        with open(path, encoding="utf-8") as fh:
            for m in re.finditer(r"@site/src/figures/([\w.-]+\.svg)", fh.read()):
                imported.add(m.group(1))
    for fn in sorted(os.listdir(FIG_DIR)):
        if fn.endswith(".svg") and fn not in imported:
            problems.append(f"src/figures/{fn}: never imported by any page")
    for fn in sorted(imported):
        if not os.path.exists(os.path.join(FIG_DIR, fn)):
            problems.append(f"a page imports src/figures/{fn}, which does not exist")

# ---------------------------------------------------------------- category files
for dirpath, _d, filenames in os.walk(DOCS):
    if "_category_.json" in filenames:
        p = os.path.join(dirpath, "_category_.json")
        try:
            with open(p, encoding="utf-8") as fh:
                json.load(fh)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{os.path.relpath(p, DOCS)}: invalid JSON: {exc}")

# ---------------------------------------------------------------- report
print(f"pages: {len(files)}   routes: {len(routes)}")
print("-" * 70)
for r in sorted(routes):
    print(f"  {r}")
print("-" * 70)
if problems:
    print(f"PROBLEMS ({len(problems)}):")
    for p in problems:
        print("  ! " + p)
    sys.exit(1)
print("No problems found.")
