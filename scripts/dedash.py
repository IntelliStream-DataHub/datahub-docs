#!/usr/bin/env python3
"""Replace em dashes with commas in prose, leaving code and tables alone.

Heavy em-dash use reads as machine-written, so prose should prefer commas.
This is careful about the places a naive replace would break:

  * fenced code blocks and inline code spans are untouched
  * markdown table delimiter rows are hyphens, not em dashes, so they are safe,
    but table CELLS are prose and do get rewritten
  * the docs are hard-wrapped at ~88 chars, so an em dash often sits at the end
    of one line or the start of the next; both forms are handled
  * en dashes in numeric ranges (1–2 days) are a different character and stay

Run:  python3 scripts/dedash.py docs/**/*.mdx      (or with --check)
"""
from __future__ import annotations

import argparse
import glob
import re
import sys

FENCE = re.compile(r"^(```|~~~)")


def protect_inline_code(line):
    """Swap inline code spans for placeholders so their contents are safe."""
    spans = []

    def stash(m):
        spans.append(m.group(0))
        return f"\x00{len(spans) - 1}\x00"

    return re.sub(r"`[^`\n]*`", stash, line), spans


def restore(line, spans):
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], line)


def dedash(text):
    lines = text.split("\n")
    out, in_fence = [], False

    for line in lines:
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or "—" not in line:
            out.append(line)
            continue

        body, spans = protect_inline_code(line)

        # A link followed by a gloss ("- [Page](/x) — what it covers") is a
        # formatting convention, not a sentence. A comma there collides with the
        # commas inside the gloss itself, so use a colon.
        body = re.sub(r"^(\s*[-*] \[[^\]]*\]\([^)]*\)) +— +", r"\1: ", body)
        # Same shape inside a <Deeper> block without the leading bullet.
        body = re.sub(r"^(\s*\[[^\]]*\]\([^)]*\)) +— +", r"\1: ", body)

        # " — "  ->  ", "     (the common mid-sentence case)
        body = re.sub(r" +— +", ", ", body)
        # trailing "... —" at a wrap point -> "...,"
        body = re.sub(r" +—$", ",", body)
        # leading "— ..." continuing the previous line -> drop the dash
        body = re.sub(r"^(\s*)— +", r"\1", body)
        # any survivor with no spaces (word—word)
        body = re.sub(r"(?<=\w)—(?=\w)", ", ", body)

        # tidy artefacts
        body = re.sub(r",\s*,", ",", body)
        body = re.sub(r",\s+\.", ".", body)
        body = re.sub(r"\(\s*,\s*", "(", body)
        body = re.sub(r",\s*\)", ")", body)
        body = re.sub(r",(\s*)$", r",\1", body)

        out.append(restore(body, spans))

    text = "\n".join(out)
    # a comma immediately before a sentence end or another comma across a wrap
    text = re.sub(r",\n(\s*), ", r",\n\1", text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--check", action="store_true", help="report only, do not write")
    args = ap.parse_args()

    files = []
    for p in args.paths:
        files.extend(sorted(glob.glob(p, recursive=True)) if any(c in p for c in "*?[") else [p])

    changed = total_before = total_after = 0
    for path in files:
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        before = src.count("—")
        if not before:
            continue
        new = dedash(src)
        after = new.count("—")
        total_before += before
        total_after += after
        if new != src:
            changed += 1
            if not args.check:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
            print(f"  {path}: {before} -> {after}")

    print(f"\n{changed} file(s) {'would change' if args.check else 'changed'}; "
          f"em dashes {total_before} -> {total_after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
