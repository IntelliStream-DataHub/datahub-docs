#!/usr/bin/env python3
"""Check that nothing in a figure spills outside its viewBox.

Text overflow is the recurring defect in hand-authored SVG: a label is
positioned relative to a plot edge, the string turns out wider than assumed,
and it runs off the canvas. Nothing in the SVG spec complains — it just gets
clipped in the browser.

This estimates each text run's advance width (honouring `text-anchor`) and each
shape's box, and flags anything crossing the viewBox. Font sizes are read from
the element, from an ancestor, or from a stylesheet passed with --css.

Run:  python3 scripts/check-figures.py 'static/img/figures/*.svg' 'src/figures/*.svg' \
          --css src/css/custom.css
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

# Advance width as a fraction of font-size, averaged over mixed-case text.
# Deliberately a little generous so a near-miss is reported rather than missed.
W_NORMAL, W_BOLD = 0.55, 0.60
SLACK = 1.0        # px of tolerance at the edges


def tag(el):
    return el.tag.split("}")[-1]


def num(el, attr, default=0.0):
    try:
        return float(el.get(attr, default))
    except (TypeError, ValueError):
        return default


def css_props(css):
    """class name -> {prop: value} for the properties we care about."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = {}
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        sel, body = m.group(1), m.group(2)
        if sel.strip().startswith("@"):
            continue
        decls = {}
        for d in body.split(";"):
            if ":" in d:
                k, _, v = d.partition(":")
                k = k.strip().lower()
                if k in ("font-size", "font-weight"):
                    decls[k] = v.strip()
        if decls:
            for one in sel.split(","):
                for cls in re.findall(r"\.([\w-]+)", one):
                    out.setdefault(cls, {}).update(decls)
    return out


def resolve(el, chain, prop, rules, default=None):
    for node in [el] + list(reversed(chain)):
        for cls in (node.get("class") or "").split():
            if cls in rules and prop in rules[cls]:
                return rules[cls][prop]
        v = node.get(prop)
        if v:
            return v
        style = node.get("style") or ""
        m = re.search(rf"(?:^|;)\s*{prop}\s*:\s*([^;]+)", style)
        if m:
            return m.group(1).strip()
    return default


def walk(el, chain=()):
    for child in el:
        yield child, list(chain)
        yield from walk(child, list(chain) + [child])


def check(path, rules):
    problems = []
    name = os.path.basename(path)
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{name}: malformed XML: {exc}"]

    vb = root.get("viewBox")
    if not vb:
        return [f"{name}: no viewBox"]
    try:
        vx, vy, vw, vh = (float(v) for v in vb.replace(",", " ").split())
    except ValueError:
        return [f"{name}: unparseable viewBox {vb!r}"]

    for el, chain in walk(root):
        t = tag(el)
        if t == "text":
            content = "".join(el.itertext()).strip()
            if not content:
                continue
            raw_size = resolve(el, chain, "font-size", rules, "16")
            m = re.match(r"([\d.]+)", str(raw_size).strip())
            size = float(m.group(1)) if m else 16.0
            weight = str(resolve(el, chain, "font-weight", rules, "400")).strip()
            bold = weight in ("bold", "bolder") or (weight.isdigit() and int(weight) >= 600)
            width = len(content) * size * (W_BOLD if bold else W_NORMAL)

            x, y = num(el, "x"), num(el, "y")
            anchor = (resolve(el, chain, "text-anchor", rules, "start") or "start").strip()
            if anchor == "middle":
                left, right = x - width / 2, x + width / 2
            elif anchor == "end":
                left, right = x - width, x
            else:
                left, right = x, x + width
            top, bottom = y - size * 0.8, y + size * 0.25

            label = content[:34] + ("…" if len(content) > 34 else "")
            if left < vx - SLACK:
                problems.append(f'{name}: text "{label}" starts at x={left:.0f}, left of the viewBox ({vx:.0f})')
            if right > vx + vw + SLACK:
                problems.append(f'{name}: text "{label}" reaches x={right:.0f}, past the viewBox width ({vx + vw:.0f})')
            if top < vy - SLACK:
                problems.append(f'{name}: text "{label}" tops at y={top:.0f}, above the viewBox ({vy:.0f})')
            if bottom > vy + vh + SLACK:
                problems.append(f'{name}: text "{label}" reaches y={bottom:.0f}, below the viewBox height ({vy + vh:.0f})')

        elif t in ("rect", "circle", "ellipse"):
            if t == "rect":
                box = (num(el, "x"), num(el, "y"),
                       num(el, "x") + num(el, "width"), num(el, "y") + num(el, "height"))
            elif t == "circle":
                r = num(el, "r")
                box = (num(el, "cx") - r, num(el, "cy") - r, num(el, "cx") + r, num(el, "cy") + r)
            else:
                rx, ry = num(el, "rx"), num(el, "ry")
                box = (num(el, "cx") - rx, num(el, "cy") - ry, num(el, "cx") + rx, num(el, "cy") + ry)
            # A shape that fully contains the viewBox is a backdrop drawn with
            # bleed — intentional, and harmlessly clipped. Only content that is
            # PARTLY outside indicates a layout mistake.
            backdrop = (box[0] <= vx and box[1] <= vy
                        and box[2] >= vx + vw and box[3] >= vy + vh)
            outside = (box[0] < vx - SLACK or box[1] < vy - SLACK
                       or box[2] > vx + vw + SLACK or box[3] > vy + vh + SLACK)
            if outside and not backdrop:
                problems.append(
                    f"{name}: <{t}> at ({box[0]:.0f},{box[1]:.0f})-({box[2]:.0f},{box[3]:.0f}) "
                    f"escapes the viewBox ({vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f})"
                )
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svgs", nargs="+")
    ap.add_argument("--css", action="append", default=[])
    args = ap.parse_args()

    paths = []
    for p in args.svgs:
        paths.extend(sorted(glob.glob(p)) if any(c in p for c in "*?[") else [p])

    css = ""
    for c in args.css:
        for p in (sorted(glob.glob(c)) if any(ch in c for ch in "*?[") else [c]):
            with open(p, encoding="utf-8") as fh:
                css += fh.read() + "\n"

    problems = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            inline = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", fh.read(), re.S))
        problems += check(path, css_props(css + "\n" + inline))

    for p in problems:
        print("  ! " + p)
    print(f"{len(paths)} figure(s) checked, {len(problems)} overflow problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
