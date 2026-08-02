#!/usr/bin/env python3
"""Check SVG text contrast against whatever is actually behind it.

Handles inline paint, CSS classes (including custom properties and
`[data-theme='dark']` overrides), real paint-order stacking, and animation —
both animated backgrounds and text that can show through a fading overlay.

See SKILL.md for usage.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

NAMED = {
    "white": "#ffffff", "black": "#000000", "red": "#ff0000", "green": "#008000",
    "blue": "#0000ff", "grey": "#808080", "gray": "#808080", "silver": "#c0c0c0",
    "navy": "#000080", "teal": "#008080", "orange": "#ffa500",
}


# ------------------------------------------------------------------ colour maths
def parse_color(value, variables=None, _depth=0):
    """Return #rrggbb, or None for none/transparent/unresolvable."""
    if value is None or _depth > 10:
        return None
    v = value.strip().lower()
    if not v or v in ("none", "transparent", "currentcolor", "inherit"):
        return None

    m = re.match(r"var\(\s*(--[\w-]+)\s*(?:,\s*(.+?))?\s*\)$", v)
    if m:
        if variables and m.group(1) in variables:
            return parse_color(variables[m.group(1)], variables, _depth + 1)
        return parse_color(m.group(2), variables, _depth + 1) if m.group(2) else None

    if v in NAMED:
        v = NAMED[v]
    if v.startswith("#"):
        h = v[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 8:          # #rrggbbaa — ignore alpha for the base colour
            h = h[:6]
        if len(h) == 6 and re.fullmatch(r"[0-9a-f]{6}", h):
            return "#" + h
        return None
    m = re.match(r"rgba?\(([^)]+)\)", v)
    if m:
        parts = [p.strip() for p in m.group(1).replace("/", ",").split(",")]
        try:
            rgb = []
            for p in parts[:3]:
                rgb.append(int(round(float(p[:-1]) * 255 / 100)) if p.endswith("%") else int(float(p)))
            return "#%02x%02x%02x" % tuple(max(0, min(255, c)) for c in rgb)
        except ValueError:
            return None
    return None


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(fg, bg):
    l1, l2 = luminance(fg), luminance(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def blend(fg, bg, alpha):
    """Composite fg over bg at the given alpha."""
    out = []
    for i in (1, 3, 5):
        f, b = int(fg[i:i + 2], 16), int(bg[i:i + 2], 16)
        out.append(int(round(f * alpha + b * (1 - alpha))))
    return "#%02x%02x%02x" % tuple(out)


# ------------------------------------------------------------------ CSS parsing
def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def parse_variables(css, theme):
    """Custom properties from :root, plus [data-theme='dark'] when theme == dark."""
    css = strip_comments(css)
    variables = {}
    selectors = [r":root"]
    if theme == "dark":
        selectors.append(r"\[data-theme=['\"]dark['\"]\]")
    for sel in selectors:
        for m in re.finditer(sel + r"\s*\{([^}]*)\}", css):
            for decl in m.group(1).split(";"):
                if ":" in decl:
                    name, _, val = decl.partition(":")
                    if name.strip().startswith("--"):
                        variables[name.strip()] = val.strip()
    return variables


def parse_rules(css, theme):
    """class name -> {property: value}, later rules winning.

    Dark-theme-scoped rules are applied only when checking the dark theme.
    """
    css = strip_comments(css)
    rules = {}
    order = 0
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        selector_group, body = m.group(1).strip(), m.group(2)
        if selector_group.startswith("@") or "--" == selector_group[:2]:
            continue
        dark_scoped = "data-theme" in selector_group
        if dark_scoped and theme != "dark":
            continue
        decls = {}
        for decl in body.split(";"):
            if ":" in decl:
                k, _, v = decl.partition(":")
                decls[k.strip().lower()] = v.strip()
        if not decls:
            continue
        for sel in selector_group.split(","):
            # A bare type selector such as `text { fill: ... }` outranks every
            # fill="" presentation attribute. Missing this hid a real bug where
            # white labels on dark fills rendered as dark ink.
            bare = sel.strip()
            if re.fullmatch(r"[a-zA-Z][\w-]*", bare):
                bucket = rules.setdefault("type:" + bare.lower(), {})
                for k, v in decls.items():
                    bucket[k] = (order, v)
            for cls in re.findall(r"\.([\w-]+)", sel):
                # Keep source order: with equal specificity CSS applies the rule
                # that appears LAST, regardless of the order classes are written
                # in the element's class attribute.
                bucket = rules.setdefault(cls, {})
                for k, v in decls.items():
                    bucket[k] = (order, v)
        order += 1
    return rules


# ------------------------------------------------------------------ geometry
def tag(el):
    return el.tag.split("}")[-1]


def num(el, attr, default=0.0):
    try:
        return float(el.get(attr, default))
    except (TypeError, ValueError):
        return default


def shape_box(el):
    """Axis-aligned box for shapes we can reason about; None otherwise."""
    t = tag(el)
    if t == "rect":
        x, y, w, h = num(el, "x"), num(el, "y"), num(el, "width"), num(el, "height")
        return (x, y, x + w, y + h) if w and h else None
    if t == "circle":
        cx, cy, r = num(el, "cx"), num(el, "cy"), num(el, "r")
        return (cx - r, cy - r, cx + r, cy + r) if r else None
    if t == "ellipse":
        cx, cy = num(el, "cx"), num(el, "cy")
        rx, ry = num(el, "rx"), num(el, "ry")
        return (cx - rx, cy - ry, cx + rx, cy + ry) if rx and ry else None
    return None


def contains(box, px, py):
    return box and box[0] <= px <= box[2] and box[1] <= py <= box[3]


# ------------------------------------------------------------------ style model
class Styler:
    def __init__(self, rules, variables):
        self.rules, self.variables = rules, variables

    def declared(self, el, prop):
        """Resolve one property: the last-defined matching rule, then attribute."""
        # CSS precedence: inline style > class rule > type rule > presentation attribute
        style = el.get("style") or ""
        m = re.search(rf"(?:^|;)\s*{prop}\s*:\s*([^;]+)", style)
        if m:
            return m.group(1).strip()
        best = None
        for cls in (el.get("class") or "").split():
            entry = self.rules.get(cls, {}).get(prop)
            if entry and (best is None or entry[0] >= best[0]):
                best = entry
        if best is not None:
            return best[1]
        type_rule = self.rules.get("type:" + tag(el), {}).get(prop)
        if type_rule is not None:
            return type_rule[1]
        return el.get(prop)

    def paint(self, el, chain, prop="fill"):
        """Computed colour for `prop`, walking up the ancestor chain."""
        for node in [el] + list(reversed(chain)):
            raw = self.declared(node, prop)
            if raw is not None:
                c = parse_color(raw, self.variables)
                if c or (raw or "").strip().lower() in ("none", "transparent"):
                    return c
        return None

    def opacity(self, el):
        for prop in ("opacity", "fill-opacity"):
            raw = self.declared(el, prop)
            if raw:
                try:
                    return max(0.0, min(1.0, float(raw)))
                except ValueError:
                    pass
        return 1.0

    def animated(self, el):
        """Does this element's visibility or fill change over time?"""
        for cls in (el.get("class") or "").split():
            decls = self.rules.get(cls, {})
            if "animation" in decls or "animation-name" in decls:
                return True
        if any(tag(c) in ("animate", "animateTransform", "set") for c in el):
            return True
        return False

    def font_size(self, el, chain):
        for node in [el] + list(reversed(chain)):
            raw = self.declared(node, "font-size")
            if raw:
                m = re.match(r"([\d.]+)", raw.strip())
                if m:
                    return float(m.group(1))
        return 16.0

    def bold(self, el, chain):
        for node in [el] + list(reversed(chain)):
            raw = self.declared(node, "font-weight")
            if raw:
                raw = raw.strip()
                return raw in ("bold", "bolder") or (raw.isdigit() and int(raw) >= 600)
        return False


# ------------------------------------------------------------------ the check
def flatten(root):
    """Elements in paint order, each with its ancestor chain."""
    out = []

    def walk(el, chain):
        for child in el:
            out.append((child, list(chain)))
            walk(child, chain + [child])

    walk(root, [])
    return out


def check_file(path, styler, page_bg, min_ratio_override, theme):
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [("ERROR", f"{os.path.basename(path)}: malformed XML: {exc}")]

    order = flatten(tree.getroot())
    index = {id(el): i for i, (el, _) in enumerate(order)}
    findings = []
    name = os.path.basename(path)

    def anim_owners(el, chain):
        """Every animated ancestor-or-self, as a set.

        Two elements sharing an animated ancestor fade together, so checking one
        against the other's absence is a false positive. A set is used rather
        than the nearest ancestor because a shape may carry its own animation
        (recolouring, say) while its visibility is still governed by an
        enclosing group that the text sits in too.
        """
        return {id(n) for n in [el] + list(reversed(chain)) if styler.animated(n)}

    # every shape that could act as a background
    shapes = []
    for el, chain in order:
        box = shape_box(el)
        if not box:
            continue
        fill = styler.paint(el, chain, "fill")
        if not fill:
            continue
        owners = anim_owners(el, chain)
        alpha = styler.opacity(el)
        for a in chain:
            alpha *= styler.opacity(a)
        # A declared `opacity: 0` on an animated element is its START state, not
        # its painted state — the animation raises it. Evaluating the literal 0
        # would report every lit overlay as invisible and give a false pass.
        if owners:
            alpha = 1.0
        shapes.append({"el": el, "box": box, "fill": fill, "anim": bool(owners),
                       "owners": owners, "alpha": alpha, "z": index[id(el)]})

    for el, chain in order:
        if tag(el) != "text":
            continue
        text = "".join(el.itertext()).strip()
        if not text:
            continue
        fg = styler.paint(el, chain, "fill") or "#000000"
        size = styler.font_size(el, chain)
        min_ratio = min_ratio_override or (
            3.0 if (size >= 24 or (size >= 18.66 and styler.bold(el, chain))) else 4.5
        )

        px = num(el, "x")
        py = num(el, "y") - size * 0.35          # baseline -> rough visual centre
        z = index[id(el)]
        text_owners = anim_owners(el, chain)

        under = [s for s in shapes if s["z"] < z and contains(s["box"], px, py)]
        over = [s for s in shapes if s["z"] > z and contains(s["box"], px, py)]

        # background = topmost opaque-ish shape beneath the text
        bg, bg_anim = page_bg, False
        for s in sorted(under, key=lambda s: s["z"]):
            if s["alpha"] >= 0.99:
                bg, bg_anim = s["fill"], s["anim"]
            else:
                bg = blend(s["fill"], bg, s["alpha"])
                bg_anim = bg_anim or s["anim"]

        label = f'"{text[:38]}"'
        ratio = contrast(fg, bg)
        verdict = "PASS" if ratio >= min_ratio else "FAIL"
        findings.append((verdict,
                         f"{name} [{theme}]: {label}  {fg} on {bg}  "
                         f"ratio {ratio:.2f} (needs {min_ratio})"))

        # animated background: also check the state where it is absent, unless
        # the text fades together with it (same animated group)
        same_group = bg_anim and any(
            s["owners"] & text_owners for s in under if s["anim"]
        )
        if bg_anim and not same_group:
            beneath = page_bg
            for s in sorted([u for u in under if not u["anim"]], key=lambda s: s["z"]):
                beneath = s["fill"] if s["alpha"] >= 0.99 else blend(s["fill"], beneath, s["alpha"])
            if beneath != bg:
                r2 = contrast(fg, beneath)
                if r2 < min_ratio:
                    findings.append(("FAIL",
                                     f"{name} [{theme}]: {label} while its animated "
                                     f"background is absent — {fg} on {beneath} "
                                     f"ratio {r2:.2f} (needs {min_ratio})"))

        # Text that an animated shape later covers: both are visible mid-fade.
        # Skipped when the text is itself animated, since the author has then
        # given it its own timing (typically a complementary fade-out).
        for s in over:
            if s["anim"] and s["fill"] and not text_owners:
                r3 = contrast(fg, s["fill"])
                if r3 < min_ratio:
                    findings.append(("OVERLAP",
                                     f"{name} [{theme}]: {label} ({fg}) can show through an "
                                     f"animated overlay filled {s['fill']} — ratio {r3:.2f} "
                                     f"mid-transition"))
    return findings


def main():
    ap = argparse.ArgumentParser(description="Check SVG text contrast.")
    ap.add_argument("svgs", nargs="+")
    ap.add_argument("--css", action="append", default=[])
    ap.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    ap.add_argument("--page-bg", default=None)
    ap.add_argument("--min-ratio", type=float, default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    paths = []
    for pattern in args.svgs:
        paths.extend(sorted(glob.glob(pattern)) if any(c in pattern for c in "*?[") else [pattern])
    if not paths:
        print("no SVG files matched")
        return 1

    external = ""
    for c in args.css:
        for p in (sorted(glob.glob(c)) if any(ch in c for ch in "*?[") else [c]):
            with open(p, encoding="utf-8") as fh:
                external += fh.read() + "\n"

    themes = ["light", "dark"] if args.theme == "both" else [args.theme]
    all_findings = []

    for theme in themes:
        default_bg = args.page_bg or ("#131d28" if theme == "dark" else "#ffffff")
        for path in paths:
            with open(path, encoding="utf-8") as fh:
                svg_text = fh.read()
            inline = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", svg_text, re.S))
            css = external + "\n" + inline
            styler = Styler(parse_rules(css, theme), parse_variables(css, theme))
            all_findings += check_file(path, styler, default_bg, args.min_ratio, theme)

    bad = [f for f in all_findings if f[0] != "PASS"]
    for verdict, msg in all_findings:
        if args.quiet and verdict == "PASS":
            continue
        print(f"{verdict:8s} {msg}")

    print("-" * 72)
    print(f"{len(all_findings)} checks, {len(bad)} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
