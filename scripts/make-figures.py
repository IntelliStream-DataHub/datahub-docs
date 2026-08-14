#!/usr/bin/env python3
"""Generate the animated explanatory SVGs used in the docs.

These are standalone files rendered inside the light `.figure` frame (see
custom.css), so they use fixed brand colours rather than inheriting the page
theme. Animation is plain CSS so it runs inside an <img>, and every file
honours `prefers-reduced-motion` by settling into a readable final state.

Run:  python3 scripts/make-figures.py
"""
import math
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "static", "img", "figures")

BLUE = "#005984"
ORANGE = "#f6783c"        # decorative only — never behind text
# Text-safe variants. The raw brand orange/green are display colours: white on
# #f6783c is 2.6:1 and on #169a4f is 3.6:1, both below the 4.5 threshold. Use
# these wherever a fill carries a label, or where the colour IS the text.
ORANGE_FILL = "#c2551a"   # white on this = 5.2:1
ORANGE_TEXT = "#b8480f"   # on white = 5.3:1
GREEN = "#0f7a3d"         # white on this = 5.1:1; on white = 4.9:1
TEAL = "#c2d5dd"
MUTED = "#5c6b75"         # on white = 5.6:1 (was #8fa3ae at 2.6:1 — failed)
INK = "#1d2b36"
FONT = "Manrope, 'Open Sans', Helvetica, Arial, sans-serif"


def sine_path(x0, x1, y, amp, period, phase=0.0, step=4):
    pts = []
    x = x0
    while x <= x1:
        y_ = y - amp * math.sin(2 * math.pi * (x - phase) / period)
        pts.append(f"{x:.1f} {y_:.1f}")
        x += step
    return "M" + " L".join(pts)


# ---------------------------------------------------------------- traversal
def traversal():
    """Blast radius: a query walking outward from one asset, hop by hop."""
    nodes = [
        (0, 88, 170, "Switch SW-04", BLUE),
        (1, 268, 92, "Host db-primary", BLUE),
        (1, 268, 248, "Host app-07", BLUE),
        (2, 470, 56, "Billing", GREEN),
        (2, 470, 170, "Checkout", GREEN),
        (2, 470, 284, "Search", GREEN),
        (3, 656, 170, "Invoice accuracy", ORANGE_FILL),
    ]
    edges = [
        (1, 88, 170, 268, 92), (1, 88, 170, 268, 248),
        (2, 268, 92, 470, 56), (2, 268, 248, 470, 170), (2, 268, 248, 470, 284),
        (3, 470, 56, 656, 170), (3, 470, 170, 656, 170),
    ]
    # each hop lights up 8% of the cycle later than the previous one, and they
    # all fade together — so the "expanding ring" reads as one motion
    starts = [6, 16, 26, 36]
    css = [
        "@keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }",
        f"text {{ font-family: {FONT}; font-size: 13px; }}",   # no fill: it would beat every fill=""
        ".lit { opacity: 0; }",
        ".flow { stroke-dasharray: 6 6; }",
    ]
    for h, s in enumerate(starts):
        css.append(
            f"@keyframes lit{h} {{ 0%,{s}% {{opacity:0}} {s + 4}%,72% {{opacity:1}} "
            f"80%,100% {{opacity:0}} }}"
        )
        # steps(1, end) removes interpolation, so the swap between the unlit and
        # lit box is instantaneous. A cross-fade leaves BOTH labels half-opaque
        # for a moment: dark text and white text blended over a half-tinted box,
        # which is unreadable while it lasts and reads as "bad contrast".
        css.append(f".hop{h} {{ animation: lit{h} 7s steps(1, end) infinite; }}")
        # The unlit node must fade OUT exactly as its lit twin fades in. Without
        # this the dark base label shows through the translucent coloured box
        # mid-transition — dark text on a dark fill, unreadable for ~0.3s.
        css.append(
            f"@keyframes dim{h} {{ 0%,{s}% {{opacity:1}} {s + 4}%,72% {{opacity:0}} "
            f"80%,100% {{opacity:1}} }}"
        )
        css.append(f".base{h} {{ animation: dim{h} 7s steps(1, end) infinite; }}")
    css.append("@keyframes march { to { stroke-dashoffset: -24 } }")
    css.append(".flow { animation: march 1.2s linear infinite; }")
    css.append(
        "@media (prefers-reduced-motion: reduce) {"
        " .lit { opacity: 1; animation: none } .flow { animation: none } }"
    )

    def node(x, y, label, colour, cls=""):
        w = 9.2 * len(label) + 26
        return (
            f'<g class="{cls}">'
            f'<rect x="{x - w/2:.0f}" y="{y - 17}" width="{w:.0f}" height="34" rx="17" '
            f'fill="{"#ffffff" if not cls else colour}" stroke="{colour}" stroke-width="2"/>'
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" '
            f'fill="{"#ffffff" if cls else INK}" font-weight="600">{label}</text></g>'
        )

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 350" '
        'role="img" aria-label="A query expanding outward from a switch through '
        'the hosts it serves, the services on those hosts, and the business '
        'measure that depends on them.">',
        f"<style>{''.join(css)}</style>",
        f'<text x="20" y="26" font-weight="800" font-size="15" fill="{BLUE}">'
        "&quot;What is the blast radius of taking down SW-04?&quot;</text>",
    ]
    # base (unlit) edges and nodes
    for _h, x1, y1, x2, y2 in edges:
        parts.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{TEAL}" stroke-width="2" fill="none"/>')
    for h, x, y, label, colour in nodes:
        parts.append(f'<g class="base{h}">{node(x, y, label, MUTED)}</g>')
    # lit overlay, per hop
    for h, x1, y1, x2, y2 in edges:
        parts.append(
            f'<path class="lit flow hop{h}" d="M{x1} {y1} L{x2} {y2}" '
            f'stroke="{BLUE}" stroke-width="2.5" fill="none"/>'
        )
    for h, x, y, label, colour in nodes:
        parts.append(node(x, y, label, colour, cls=f"lit hop{h}"))

    for h, label, x in ((0, "start here", 88), (1, "1 hop", 268),
                        (2, "2 hops", 470), (3, "3 hops", 656)):
        parts.append(
            f'<text class="lit hop{h}" x="{x}" y="330" text-anchor="middle" '
            f'font-size="12" font-weight="700" fill="{MUTED}">{label}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


# ------------------------------------------------------------------ lead/lag
def lead_lag():
    """Two signals; sliding one back by the lag makes them line up."""
    period, amp, lag = 170, 30, 58
    x0, x1 = 70, 720
    wave_a = sine_path(x0, x1, 108, amp, period)
    wave_b = sine_path(x0, x1, 232, amp, period, phase=lag)

    css = f"""
    text {{ font-family: {FONT}; }}   /* no fill: a type rule beats every fill="" attribute */
    @keyframes slide {{
      0%, 18%   {{ transform: translateX(0) }}
      38%, 72%  {{ transform: translateX(-{lag}px) }}
      92%, 100% {{ transform: translateX(0) }}
    }}
    @keyframes showAligned {{
      0%, 34%  {{ opacity: 0 }}
      42%, 70% {{ opacity: 1 }}
      78%, 100%{{ opacity: 0 }}
    }}
    @keyframes showOffset {{
      0%, 20%  {{ opacity: 1 }}
      34%, 76% {{ opacity: 0 }}
      90%,100% {{ opacity: 1 }}
    }}
    .slider  {{ animation: slide 7s ease-in-out infinite; }}
    .aligned {{ opacity: 0; animation: showAligned 7s ease-in-out infinite; }}
    .offset  {{ animation: showOffset 7s ease-in-out infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .slider {{ animation: none; transform: translateX(-{lag}px) }}
      .aligned {{ animation: none; opacity: 1 }}
      .offset {{ animation: none; opacity: 0 }}
    }}
    """
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 320" '
        'role="img" aria-label="Two signals with the same shape. The second '
        'lags the first; sliding it back by the measured lag makes the two '
        'line up.">',
        f"<style>{css}</style>",
        f'<text x="20" y="26" font-weight="800" font-size="15" fill="{BLUE}">'
        "Lead and lag: the same shape, arriving later</text>",
        # axes
        f'<line x1="{x0}" y1="160" x2="{x1}" y2="160" stroke="{TEAL}" stroke-width="1.5"/>',
        f'<line x1="{x0}" y1="284" x2="{x1}" y2="284" stroke="{TEAL}" stroke-width="1.5"/>',
        # focus signal
        f'<path d="{wave_a}" stroke="{BLUE}" stroke-width="2.5" fill="none"/>',
        f'<text x="{x0}" y="66" font-size="12.5" font-weight="700" fill="{BLUE}">'
        "Suction temperature (focus)</text>",
        # ghost of the lagging signal in its recorded position
        f'<path class="offset" d="{wave_b}" stroke="{ORANGE}" stroke-width="1.5" '
        f'stroke-dasharray="4 5" fill="none" opacity=".55"/>',
        # the signal that slides
        f'<g class="slider"><path d="{wave_b}" stroke="{ORANGE}" stroke-width="2.5" fill="none"/></g>',
        f'<text x="{x0}" y="190" font-size="12.5" font-weight="700" fill="{ORANGE_TEXT}">'
        "Compressor power</text>",
        # lag bracket
        f'<g class="offset">',
        f'<line x1="{x0 + period//4}" y1="108" x2="{x0 + period//4}" y2="300" '
        f'stroke="{BLUE}" stroke-width="1.2" stroke-dasharray="3 4"/>',
        f'<line x1="{x0 + period//4 + lag}" y1="232" x2="{x0 + period//4 + lag}" y2="300" '
        f'stroke="{ORANGE}" stroke-width="1.2" stroke-dasharray="3 4"/>',
        f'<line x1="{x0 + period//4}" y1="300" x2="{x0 + period//4 + lag}" y2="300" '
        f'stroke="{INK}" stroke-width="1.5"/>',
        f'<text x="{x0 + period//4 + lag + 12}" y="304" font-size="12.5" font-weight="700" '
        f'fill="{INK}">focus leads by 25 min</text>',
        "</g>",
        # aligned confirmation
        f'<g class="aligned">'
        f'<rect x="{x1 - 268}" y="252" width="250" height="34" rx="17" fill="#eaf6ee" stroke="{GREEN}" stroke-width="1.5"/>'
        f'<text x="{x1 - 143}" y="274" text-anchor="middle" font-size="13" font-weight="700" '
        f'fill="{GREEN}">shifted back 25 min — they line up</text></g>',
        "</svg>",
    ]
    return "\n".join(p)


# ------------------------------------------------------- cost of doing nothing
def compounding_gap():
    """Cost per question over time, with and without a model.

    Deliberately honest: the first question costs MORE with the platform,
    because the model does not exist yet. The crossover is the point of the
    whole argument, so the chart should show it rather than hide it.
    """
    without = [100, 100, 102, 103, 104, 106, 107, 108, 110, 111]
    with_model = [128, 88, 64, 50, 40, 33, 28, 25, 22, 21]
    n = len(without)
    # px1 stops well short of the 760 canvas: the series labels sit to the RIGHT
    # of the last point, and "with a model" is ~84px wide at 12.5px bold. Ending
    # the plot at 700 pushed that label to ~792 and out of the viewBox.
    px0, px1, py0, py1 = 92, 612, 70, 288
    vmax = 135

    def X(i):
        return px0 + i * (px1 - px0) / (n - 1)

    def Y(v):
        return py1 - (v / vmax) * (py1 - py0)

    def poly(vals):
        return " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))

    # shaded gap, from the crossover onward
    cross = next(i for i in range(n) if with_model[i] < without[i])
    area = ([f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(without) if i >= cross]
            + [f"{X(i):.1f},{Y(v):.1f}" for i, v in reversed(list(enumerate(with_model))) if i >= cross])

    css = f"""
    text {{ font-family: {FONT}; }}   /* no fill: a type rule beats every fill="" attribute */
    @keyframes draw {{ to {{ stroke-dashoffset: 0 }} }}
    @keyframes fadeUp {{ 0%,38% {{opacity:0}} 62%,100% {{opacity:.20}} }}
    @keyframes appear {{ 0%,55% {{opacity:0}} 75%,100% {{opacity:1}} }}
    .line {{ stroke-dasharray: 900; stroke-dashoffset: 900;
             animation: draw 3.2s ease-out forwards; }}
    .line2 {{ animation-delay: .5s; }}
    .gap {{ opacity: 0; animation: fadeUp 6s ease-out forwards; }}
    .note {{ opacity: 0; animation: appear 6s ease-out forwards; }}
    @media (prefers-reduced-motion: reduce) {{
      .line {{ stroke-dashoffset: 0; animation: none }}
      .gap {{ opacity: .20; animation: none }}
      .note {{ opacity: 1; animation: none }}
    }}
    """
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 360" '
        'role="img" aria-label="A chart of effort per question answered. Without '
        'a model the cost stays flat and drifts upward. With a model the first '
        'question costs more, then the cost falls steeply. The widening gap '
        'between the two lines is the cost of doing nothing.">',
        f"<style>{css}</style>",
        f'<text x="20" y="26" font-weight="800" font-size="15" fill="{BLUE}">'
        "Effort to answer each successive question</text>",
        f'<text x="20" y="46" font-size="12.5" fill="{MUTED}">'
        "The gap between the lines is what doing nothing costs — and it widens.</text>",
        # axes
        f'<line x1="{px0}" y1="{py1}" x2="{px1}" y2="{py1}" stroke="{TEAL}" stroke-width="1.5"/>',
        f'<line x1="{px0}" y1="{py0}" x2="{px0}" y2="{py1}" stroke="{TEAL}" stroke-width="1.5"/>',
        f'<text x="{px0 - 8}" y="{py0 + 6}" text-anchor="end" font-size="11.5" fill="{MUTED}">high</text>',
        f'<text x="{px0 - 8}" y="{py1}" text-anchor="end" font-size="11.5" fill="{MUTED}">low</text>',
        f'<text x="{(px0 + px1) / 2:.0f}" y="{py1 + 34}" text-anchor="middle" font-size="12" '
        f'fill="{MUTED}">1st question  →  10th question</text>',
        # the gap
        f'<polygon class="gap" points="{" ".join(area)}" fill="{ORANGE}"/>',
        # lines
        f'<polyline class="line" points="{poly(without)}" fill="none" stroke="{MUTED}" '
        f'stroke-width="3" stroke-linecap="round"/>',
        f'<polyline class="line line2" points="{poly(with_model)}" fill="none" stroke="{BLUE}" '
        f'stroke-width="3" stroke-linecap="round"/>',
        # labels
        f'<text x="{X(n-1) + 8:.0f}" y="{Y(without[-1]) + 4:.0f}" font-size="12.5" '
        f'font-weight="700" fill="{MUTED}">no model</text>',
        f'<text x="{X(n-1) + 8:.0f}" y="{Y(with_model[-1]) + 4:.0f}" font-size="12.5" '
        f'font-weight="700" fill="{BLUE}">with a model</text>',
        # honest note about the first question
        f'<g class="note">'
        f'<circle cx="{X(0):.0f}" cy="{Y(with_model[0]):.0f}" r="5" fill="{BLUE}"/>'
        f'<text x="{X(0) + 12:.0f}" y="{Y(with_model[0]) - 8:.0f}" font-size="12" '
        f'font-weight="700" fill="{BLUE}">the first question costs more</text>'
        f'<circle cx="{X(cross):.0f}" cy="{Y(with_model[cross]):.0f}" r="5" fill="{GREEN}"/>'
        f'<text x="{X(cross) + 12:.0f}" y="{Y(with_model[cross]) - 10:.0f}" font-size="12" '
        f'font-weight="700" fill="{GREEN}">break-even</text></g>',
        "</svg>",
    ]
    return "\n".join(p)


# ----------------------------------------------------------------- agent loop
def agent_loop():
    """The observe / reason / act / check cycle an agent runs.

    THEMED. This one carries no colours and no <style> block: it is inlined
    into the page (see `Figure` / SVGR), so both its palette and its animation
    live in custom.css under `.fig-agent-loop`, where `[data-theme='dark']`
    can reach them. That is what makes it follow the site's theme toggle
    rather than the operating system's preference.
    """
    # Geometry note: the centre box is 190 wide and the stations are 172 wide,
    # so the radius must clear 95 + 86 + a gap or the left/right stations sit on
    # top of the centre. r = 196 leaves ~15px either side.
    cx, cy, r = 380, 290, 196
    stations = [
        (-90, "Observe", "read the graph,", "signals and events", "c-blue", 0),
        (0, "Reason", "decide the single", "next step", "c-blue", 25),
        (90, "Act", "traverse, analyse,", "or draft an action", "c-orange", 50),
        (180, "Check", "did that answer it?", "if not, go again", "c-green", 75),
    ]

    def pos(angle):
        rad = math.radians(angle)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 540" '
        'class="fig-agent-loop" role="img" aria-label="An agent loop: observe, '
        'reason, act, check, and around again — with the knowledge graph at the '
        'centre supplying context at every step, and an exit to a sourced answer '
        'once the goal is met.">',
        '<text class="fig-title" x="20" y="24">An agent loop</text>',
        '<text class="fig-sub" x="20" y="44">One step at a time, checking its own '
        "work, until the goal is met or a limit stops it.</text>",
        f'<circle class="fig-track" cx="{cx}" cy="{cy}" r="{r}"/>',
        f'<rect class="fig-centre" x="{cx - 95}" y="{cy - 30}" width="190" height="60" rx="14"/>',
        f'<text class="fig-centre-title" x="{cx}" y="{cy - 6}" text-anchor="middle">'
        "Your knowledge graph</text>",
        f'<text class="fig-centre-sub" x="{cx}" y="{cy + 14}" text-anchor="middle">'
        "context at every step</text>",
    ]
    for angle, title, sub1, sub2, colour_cls, start in stations:
        x, y = pos(angle)
        w, h = 172, 56
        bx, by_ = x - w / 2, y - h / 2
        # `fig-unlit` fades this out exactly as its lit twin fades in, so the
        # dark base label never shows through the coloured box mid-transition.
        p.append(
            f'<g class="fig-unlit s{start}">'
            f'<rect class="fig-box" x="{bx:.0f}" y="{by_:.0f}" width="{w}" height="{h}" rx="14"/>'
            f'<text class="fig-box-title" x="{x:.0f}" y="{y - 8:.0f}" text-anchor="middle">{title}</text>'
            f'<text class="fig-box-sub" x="{x:.0f}" y="{y + 9:.0f}" text-anchor="middle">{sub1}</text>'
            f'<text class="fig-box-sub" x="{x:.0f}" y="{y + 22:.0f}" text-anchor="middle">{sub2}</text></g>'
        )
        p.append(
            f'<g class="fig-lit s{start}">'
            f'<rect class="fig-lit-box {colour_cls}" x="{bx:.0f}" y="{by_:.0f}" width="{w}" height="{h}" rx="14"/>'
            f'<text class="fig-lit-title" x="{x:.0f}" y="{y - 8:.0f}" text-anchor="middle">{title}</text>'
            f'<text class="fig-lit-sub" x="{x:.0f}" y="{y + 9:.0f}" text-anchor="middle">{sub1}</text>'
            f'<text class="fig-lit-sub" x="{x:.0f}" y="{y + 22:.0f}" text-anchor="middle">{sub2}</text></g>'
        )
    p.append(f'<g class="fig-orbit"><circle class="fig-token" cx="{cx}" cy="{cy - r}" r="9"/></g>')
    # Exit leaves from Check (the left station), curving down-left into clear
    # space — it must not cross the loop or collide with the Act box.
    p.append(
        f'<path class="fig-exit-path" d="M{cx - r} {cy + 28} Q 150 400 128 448"/>'
        f'<rect class="fig-exit-box" x="24" y="450" width="190" height="62" rx="14"/>'
        f'<text class="fig-exit-title" x="119" y="474" text-anchor="middle">Sourced answer</text>'
        f'<text class="fig-exit-sub" x="119" y="492" text-anchor="middle">or a drafted action</text>'
        f'<text class="fig-exit-note" x="119" y="530" text-anchor="middle">only when the goal is met</text>'
    )
    p.append("</svg>")
    return "\n".join(p)


# --------------------------------------------------------------- lineage trace
def lineage_trace():
    """A figure traced back to its inputs. THEMED.

    Rewritten from a staggered box-by-box reveal, which just made boxes pop on
    and off without conveying anything. The idea being illustrated is direction:
    the calculation runs left to right, the trace runs right to left. So the
    boxes are drawn once and stay put, and a single stroke draws itself
    backwards along the chain.
    """
    bw, bh = 130, 58
    xs = [11, 163, 315, 467, 619]
    mid_y = 96
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 322" '
        'class="fig-lineage-trace" role="img" aria-label="A reported KPI traced back '
        'through an hourly aggregate, a filter by event window and a clean or gap-fill '
        'step, to two raw sensor series and a maintenance event. The calculation runs '
        'left to right; the trace runs right to left.">',
        '<text class="fig-title" x="20" y="24">Tracing a figure back to its inputs</text>',
        '<text class="fig-sub" x="20" y="44">The calculation runs left to right. The trace '
        'runs the other way, naming what each step consumed.</text>',
    ]

    def box(x, y, title, sub, cls="fig-box", t="fig-box-title", s="fig-box-sub"):
        return (f'<g><rect class="{cls}" x="{x}" y="{y}" width="{bw}" height="{bh}" rx="12"/>'
                f'<text class="{t}" x="{x + bw / 2:.0f}" y="{y + 26}" text-anchor="middle">{title}</text>'
                f'<text class="{s}" x="{x + bw / 2:.0f}" y="{y + 44}" text-anchor="middle">{sub}</text></g>')

    # sources
    p.append(box(xs[0], 60, "Sensor A", "raw samples"))
    p.append(box(xs[0], 132, "Sensor B", "gap-filled"))
    p.append(f'<circle class="fig-token fig-pulse" cx="{xs[0] + bw - 8}" cy="140" r="7"/>')
    # transformations
    p.append(box(xs[1], mid_y, "Clean", "and gap-fill"))
    p.append(box(xs[2], mid_y, "Filter", "by event window"))
    p.append(box(xs[3], mid_y, "Aggregate", "hourly"))
    # the reported figure
    p.append(box(xs[4], mid_y, "Reported KPI", "with its evidence",
                 cls="fig-lit-box c-blue", t="fig-lit-title", s="fig-lit-sub"))
    # the event that the filter consumes
    p.append(box(xs[1], 214, "Maintenance", "event"))

    cy = mid_y + bh / 2
    # static connectors showing the calculation direction
    conns = [
        f"M{xs[0] + bw} 89 L{xs[1]} {cy:.0f}",
        f"M{xs[0] + bw} 161 L{xs[1]} {cy:.0f}",
        f"M{xs[1] + bw} {cy:.0f} L{xs[2]} {cy:.0f}",
        f"M{xs[1] + bw} 243 L{xs[2] + 40} {mid_y + bh}",
        f"M{xs[2] + bw} {cy:.0f} L{xs[3]} {cy:.0f}",
        f"M{xs[3] + bw} {cy:.0f} L{xs[4]} {cy:.0f}",
    ]
    for d in conns:
        p.append(f'<path class="fig-track" d="{d}" fill="none"/>')

    # the trace itself, authored right-to-left so it draws backwards
    trace = (f"M{xs[4]} {cy:.0f} L{xs[3] + bw} {cy:.0f} "
             f"M{xs[3]} {cy:.0f} L{xs[2] + bw} {cy:.0f} "
             f"M{xs[2]} {cy:.0f} L{xs[1] + bw} {cy:.0f} "
             f"M{xs[1]} {cy:.0f} L{xs[0] + bw} 89")
    p.append(f'<path class="fig-exit-path fig-trace" d="{trace}" fill="none"/>')

    p.append(f'<text class="fig-box-sub" x="{xs[4] + bw / 2:.0f}" y="82" text-anchor="middle">start here</text>')
    p.append('<text class="fig-box-sub" x="20" y="300">Each step names the inputs it consumed, '
             'so the walk ends on real samples rather than on an assumption.</text>')
    p.append("</svg>")
    return "\n".join(p)


# --------------------------------------------------------------- decision tempo
def decision_tempo():
    """Two organisations meeting the same shock. THEMED, static.

    Static because the reader compares the lanes, and the comparison IS the
    argument. The point is not that the second lane decides earlier: it is that
    it decides *again*, twice, because re-verifying is cheap. A version that
    showed only an earlier decision made the weaker of the two claims.
    """
    shock, close = 140, 470
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 374" '
        'class="fig-decision-tempo" role="img" aria-label="One shock, two lanes. In '
        'the first, finding the figures, finding who built them and checking they are '
        'current push the decision past the point where acting was still possible. In '
        'the second, the figures name their own inputs, so the decision lands inside '
        'the window and is revised twice afterwards as more becomes known.">',
        '<text class="fig-title" x="20" y="24">The shock is the same. The time to trust a number '
        'is not.</text>',
        '<text class="fig-sub" x="20" y="44">Nobody in either lane saw it coming. Only one of '
        'them can tell which of its figures still hold.</text>',
        f'<text class="fig-box-sub" x="{shock}" y="68" text-anchor="middle">the shock lands</text>',
        f'<rect class="fig-centre" x="{shock}" y="76" width="{close - shock}" height="26" '
        f'rx="10"/>',
        f'<text class="fig-centre-sub" x="{(shock + close) // 2}" y="94" '
        f'text-anchor="middle">while the option is still open</text>',
    ]
    # Both verticals are drawn in two segments, skipping the rows the lane titles
    # sit on. Run through them and the titles read as struck through.
    for y0, y1 in ((140, 200), (244, 288)):
        p.append(f'<line class="fig-line-b" x1="{shock}" y1="{y0}" x2="{shock}" y2="{y1}"/>')
        p.append(f'<line class="fig-track" x1="{close}" y1="{y0}" x2="{close}" y2="{y1}"/>')
    p.append(f'<text class="fig-box-sub" x="{close}" y="316" text-anchor="middle">the window '
             f'closes</text>')

    def step(x, w, y, label):
        return (f'<rect class="fig-box" x="{x}" y="{y}" width="{w}" height="34" rx="10"/>'
                f'<text class="fig-box-sub" x="{x + w // 2}" y="{y + 21}" '
                f'text-anchor="middle">{label}</text>')

    def call(x, w, y, label, colour, h=34):
        return (f'<rect class="fig-lit-box {colour}" x="{x}" y="{y}" width="{w}" '
                f'height="{h}" rx="10"/>'
                f'<text class="fig-lit-title" x="{x + w // 2}" y="{y + h // 2 + 5}" '
                f'text-anchor="middle">{label}</text>')

    # ---- lane 1: the verification is the work
    p.append('<text class="fig-box-title" x="20" y="130">Without a trail, every figure has to be '
             'chased down by hand</text>')
    for x, w, label in ((140, 118, "find the figures"), (264, 132, "find who built them"),
                        (402, 140, "check they are current")):
        p.append(step(x, w, 140, label))
    p.append(call(556, 110, 140, "decide", "c-orange"))
    p.append('<text class="fig-box-sub" x="611" y="192" text-anchor="middle">after the option has '
             'gone</text>')

    # ---- lane 2: the figures answer for themselves
    p.append('<text class="fig-box-title" x="20" y="236">With lineage, each figure already names '
             'its inputs and their condition</text>')
    p.append(step(140, 140, 246, "verify from the trail"))
    p.append(call(288, 110, 246, "decide", "c-green"))
    for x in (490, 610):
        p.append(call(x, 96, 250, "revise", "c-green", h=26))
    p.append('<text class="fig-box-sub" x="140" y="298">and again, as more becomes known, because '
             'each revision costs minutes rather than days</text>')

    p.append('<text class="fig-sub" x="20" y="344">Forecasting the shock is not the advantage on '
             'offer, and nobody sells it. Knowing which of your own</text>')
    p.append('<text class="fig-sub" x="20" y="362">numbers still hold, in minutes, is what lets '
             'you decide while it still matters and change your mind after.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------ policy enforcement
def policy_enforcement():
    """A data set governed by a policy, enforced by a function, in the graph.

    THEMED, static except the enforcement flow. The point of the figure is that
    the rule, its enforcer and the governed data are all nodes in one graph,
    not settings in three different admin screens.
    """
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 360" '
        'class="fig-policy-enforcement" role="img" aria-label="A knowledge graph '
        'fragment: a data set of valve pressure series is governed by a lifecycle '
        'policy, retain for ten years, which is enforced by a function that expires '
        'datapoints older than ten years, acting back on the series in the data '
        'set.">',
        '<text class="fig-title" x="20" y="24">The rule, its enforcer and the data, one graph</text>',
        '<text class="fig-sub" x="20" y="44">A policy is a node. So is the function that '
        'enforces it. Governance becomes something you can traverse.</text>',
        # ---- the data set container with two series inside
        '<rect class="fig-track" x="20" y="90" width="280" height="210" rx="14" fill="none"/>',
        '<rect class="fig-centre" x="36" y="106" width="228" height="40" rx="12"/>',
        '<text class="fig-centre-title" x="150" y="131" text-anchor="middle">Valve pressure sensors</text>',
        '<rect class="fig-lit-box c-green" x="52" y="170" width="200" height="40" rx="12"/>',
        '<text class="fig-lit-title" x="152" y="195" text-anchor="middle">21-PT-1034 · pressure</text>',
        '<rect class="fig-lit-box c-green" x="52" y="224" width="200" height="40" rx="12"/>',
        '<text class="fig-lit-title" x="152" y="249" text-anchor="middle">21-PT-1035 · pressure</text>',
        '<text class="fig-box-sub" x="160" y="288" text-anchor="middle">Data set</text>',
        # ---- governed by -> policy
        '<line class="fig-track" x1="300" y1="132" x2="450" y2="132"/>',
        '<path class="fig-centre" d="M450 126 L462 132 L450 138 z"/>',
        '<text class="fig-box-sub" x="378" y="122" text-anchor="middle">governed by</text>',
        '<rect class="fig-lit-box c-orange" x="462" y="100" width="200" height="64" rx="12"/>',
        '<text class="fig-lit-title" x="562" y="124" text-anchor="middle">Policy · lifecycle</text>',
        '<text class="fig-lit-sub" x="562" y="141" text-anchor="middle">retain for 10 years,</text>',
        '<text class="fig-lit-sub" x="562" y="155" text-anchor="middle">a named obligation</text>',
        # ---- enforced by -> function
        '<line class="fig-track" x1="562" y1="164" x2="562" y2="226"/>',
        '<path class="fig-centre" d="M556 226 L562 238 L568 226 z"/>',
        '<text class="fig-box-sub" x="578" y="200">enforced by</text>',
        '<rect class="fig-lit-box c-blue" x="462" y="238" width="200" height="64" rx="12"/>',
        '<text class="fig-lit-title" x="562" y="262" text-anchor="middle">Function</text>',
        '<text class="fig-lit-sub" x="562" y="279" text-anchor="middle">expire datapoints</text>',
        '<text class="fig-lit-sub" x="562" y="293" text-anchor="middle">older than 10 years</text>',
        # ---- the enforcement action, flowing back onto the data
        '<path class="fig-exit-path fig-flow" d="M462 270 L316 270" fill="none"/>',
        '<path class="fig-centre" d="M316 264 L304 270 L316 276 z"/>',
        '<text class="fig-box-sub" x="389" y="318" text-anchor="middle">acts on the series it governs</text>',
        '<text class="fig-box-sub" x="20" y="348">Recording this works today. The function '
        'runs automatically once execution ships, and the loop closes without remodelling.</text>',
        "</svg>",
    ]
    return "\n".join(p)


# ------------------------------------------------------- cleaning by correlation
def cleaning_by_correlation():
    """A tank level that breathes with the weather, corrected by correlation.

    From a real deployment: a chemical tank level computed from two pressure
    sensors climbed on warm afternoons, because the sensors feel temperature,
    not chemical. THEMED, static: raw and corrected drawn in one band so the
    difference is the picture.
    """
    import math as _m
    x0, x1, period = 90, 710, 155

    def temp_y(x):
        return 128 - 18 * _m.sin(2 * _m.pi * (x - x0) / period)

    def base(x):
        return 258 + 28 * (x - x0) / (x1 - x0)      # slow decline: consumption

    def raw_y(x):
        return base(x) - 13 * _m.sin(2 * _m.pi * (x - x0) / period)

    def path(fn, xa, xb):
        pts = []
        x = xa
        while x <= xb:
            pts.append(f"{x:.0f} {fn(x):.1f}")
            x += 4
        return "M" + " L".join(pts)

    peak = x0 + 155 * 2.25                           # a warm afternoon
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 384" '
        'class="fig-cleaning" role="img" aria-label="Two chart bands. Air temperature '
        'swings daily. The measured tank level swings with it while slowly declining; '
        'the corrected level shows only the decline, because the temperature-driven '
        'swing has been subtracted.">',
        '<text class="fig-title" x="20" y="24">Cleaning a tank level that breathes with the weather</text>',
        '<text class="fig-sub" x="20" y="44">A chemical tank level computed from two pressure sensors climbs on warm'
        ' afternoons.</text>',
        '<text class="fig-sub" x="20" y="60">Nothing was added: the sensors feel the temperature, not the chemical.</text>',
        f'<text class="fig-box-sub" x="{x0}" y="88">Air temperature</text>',
        f'<path class="fig-line-b" d="{path(temp_y, x0, x1)}"/>',
        f'<text class="fig-box-sub" x="{x0}" y="212">Tank level</text>',
        '<line class="fig-line-a" x1="500" y1="208" x2="528" y2="208"/>',
        '<text class="fig-box-sub" x="534" y="212">as measured</text>',
        '<line class="fig-line-c" x1="618" y1="208" x2="646" y2="208"/>',
        '<text class="fig-box-sub" x="652" y="212">corrected</text>',
        f'<path class="fig-line-a" d="{path(raw_y, x0, x1)}"/>',
        f'<path class="fig-line-c" d="{path(base, x0, x1)}"/>',
        f'<circle class="fig-token fig-pulse" cx="{peak:.0f}" cy="{raw_y(peak):.1f}" r="5"/>',
        f'<text class="fig-box-sub" x="{peak:.0f}" y="238" text-anchor="middle">warm afternoon, phantom fill</text>',
        '<text class="fig-box-sub" x="20" y="348">The function subtracts the level swing the '
        'temperature correlation predicts, and nothing else.</text>',
        '<text class="fig-box-sub" x="20" y="366">Raw stays raw; the corrected series is '
        'derived, flagged, and the one reports and reorder decisions consume.</text>',
        "</svg>",
    ]
    return "\n".join(p)


# ----------------------------------------------------------- feature extraction
def feature_extraction():
    """A dense raw signal reduced to a few meaningful numbers. THEMED, static."""
    import math as _m
    xa, xb, yc = 36, 284, 176

    def noisy():
        pts = []
        x = xa
        while x <= xb:
            y = (yc - 18 * _m.sin(2 * _m.pi * (x - xa) / 70)
                    - 9 * _m.sin(2 * _m.pi * (x - xa) / 23)
                    - 5 * _m.sin(2 * _m.pi * (x - xa) / 11))
            pts.append(f"{x:.0f} {y:.1f}")
            x += 2
        return "M" + " L".join(pts)

    tiles = [
        ("RMS 4.2 mm/s", "the energy of the vibration"),
        ("Peak 9.8 mm/s", "the worst single impact"),
        ("Crest factor 2.3", "spikiness, a bearing tell"),
    ]
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 356" '
        'class="fig-features" role="img" aria-label="A dense, noisy vibration signal '
        'on the left passes through a function and comes out as three named numbers: '
        'RMS, peak, and crest factor.">',
        '<text class="fig-title" x="20" y="24">Feature extraction: many numbers in, a few meaningful ones out</text>',
        '<text class="fig-sub" x="20" y="44">The raw signal is too dense to act on. The '
        'features are what people, models and agents actually use.</text>',
        '<rect class="fig-track" x="20" y="70" width="280" height="200" rx="12" fill="none"/>',
        '<text class="fig-box-sub" x="36" y="92">Vibration, raw</text>',
        f'<path class="fig-line-a" d="{noisy()}"/>',
        '<text class="fig-box-sub" x="160" y="256" text-anchor="middle">millions of samples per shift</text>',
        '<line class="fig-track" x1="300" y1="170" x2="322" y2="170"/>',
        '<path class="fig-centre" d="M322 164 L334 170 L322 176 z"/>',
        '<rect class="fig-lit-box c-blue" x="334" y="146" width="122" height="48" rx="12"/>',
        '<text class="fig-lit-title" x="395" y="166" text-anchor="middle">Function</text>',
        '<text class="fig-lit-sub" x="395" y="183" text-anchor="middle">every shift</text>',
        '<line class="fig-track" x1="456" y1="170" x2="478" y2="170"/>',
        '<path class="fig-centre" d="M478 164 L490 170 L478 176 z"/>',
    ]
    for i, (value, meaning) in enumerate(tiles):
        y = 82 + i * 64
        p.append(
            f'<rect class="fig-box" x="490" y="{y}" width="250" height="52" rx="12"/>'
            f'<text class="fig-box-title" x="615" y="{y + 23}" text-anchor="middle">{value}</text>'
            f'<text class="fig-box-sub" x="615" y="{y + 41}" text-anchor="middle">{meaning}</text>'
        )
    p.append('<text class="fig-box-sub" x="20" y="330">Each feature is a new series in its own '
             'right, smaller, comparable across machines, and carrying its derivation.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------------- windowing
def windowing():
    """Tumbling windows, drawn the way the classic stream-processing diagram
    draws them: parallel event lanes, equal full-height slices, a window-size
    bracket and a time arrow. THEMED; lanes flow, structure holds still."""
    lanes = [
        ("21-PT-1034", 126, (124, 166, 231, 287, 352, 376, 447, 522, 608, 671)),
        ("21-PT-1035", 188, (139, 201, 246, 318, 401, 438, 491, 580, 645, 702)),
        ("21-TT-2001", 250, (151, 183, 272, 335, 391, 467, 529, 553, 624, 688)),
    ]
    seps = (112, 263, 414, 565, 716)
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 392" '
        'class="fig-windowing" role="img" aria-label="Three sensor streams as '
        'horizontal lanes of events. Vertical slices divide time into four equal '
        'tumbling windows; every event falls in exactly one window. A bracket marks '
        'the window size and an arrow marks time.">',
        '<text class="fig-title" x="20" y="24">Tumbling windows: every event lands in exactly one slice</text>',
        '<text class="fig-sub" x="20" y="44">Three sensors streaming, time cut into equal windows.</text>'
        '<text class="fig-sub" x="20" y="60">When a window closes, its aggregate is emitted seconds later.</text>',
    ]
    for i in range(4):
        cx = (seps[i] + seps[i + 1]) / 2
        p.append(f'<text class="fig-box-sub" x="{cx:.0f}" y="88" text-anchor="middle">window {i + 1}</text>')
    for x in seps:
        p.append(f'<line class="fig-track" x1="{x}" y1="96" x2="{x}" y2="272"/>')
    for label, y, xs in lanes:
        p.append(f'<text class="fig-box-sub" x="100" y="{y + 4}" text-anchor="end">{label}</text>')
        p.append(f'<path class="fig-exit-path fig-flow" d="M112 {y} L716 {y}" fill="none"/>')
        for x in xs:
            cls = "fig-token fig-pulse" if x >= 690 else "fig-token"
            p.append(f'<circle class="{cls}" cx="{x}" cy="{y}" r="5"/>')
    # window-size bracket under the first slice
    p.append('<line class="fig-track" x1="112" y1="290" x2="263" y2="290"/>')
    p.append('<line class="fig-track" x1="112" y1="284" x2="112" y2="296"/>')
    p.append('<line class="fig-track" x1="263" y1="284" x2="263" y2="296"/>')
    p.append('<text class="fig-box-sub" x="187" y="310" text-anchor="middle">window size</text>')
    # time arrow, clear of the bracket
    p.append('<line class="fig-track" x1="300" y1="290" x2="700" y2="290"/>')
    p.append('<path class="fig-centre" d="M700 284 L712 290 L700 296 z"/>')
    p.append('<text class="fig-box-sub" x="720" y="294">time</text>')
    p.append('<text class="fig-box-sub" x="20" y="344">Every event belongs to exactly one window, '
             'no overlaps, no gaps. One aggregate per sensor per window,</text>')
    p.append('<text class="fig-box-sub" x="20" y="362">emitted while the stream keeps flowing. '
             'Sliding windows overlap instead; the slicing idea is identical.</text>')
    p.append("</svg>")
    return "\n".join(p)


# -------------------------------------------------------------- event detection
def event_detection():
    """A continuous signal becoming discrete, typed events. THEMED, animated:
    the trace draws itself in and each event chip appears as its moment passes,
    which is the one case where sequenced appearance IS the semantics.
    """
    import math as _m

    def seg(fn, xa, xb, step=3):
        pts = []
        x = xa
        while x <= xb:
            pts.append(f"{x:.0f} {fn(x):.1f}")
            x += step
        return pts

    def normal(yc=150, amp=12, period=60, phase=0):
        return lambda x: yc - amp * _m.sin(2 * _m.pi * (x - phase) / period)

    pts = []
    pts += seg(normal(), 70, 196)
    pts += seg(lambda x: 150 - 54 * _m.exp(-((x - 215) / 11) ** 2), 196, 244)   # alarm spike
    pts += seg(normal(), 244, 330)
    pts += seg(lambda x: 128 - 5 * _m.sin(2 * _m.pi * (x - 330) / 34), 330, 430)  # stress plateau
    pts += seg(normal(), 430, 498)
    pts += seg(lambda x: 150 - 20 * _m.sin(2 * _m.pi * (x - 498) / 12), 498, 560, 2)  # anomaly burst
    pts += seg(normal(), 560, 622)
    pts += seg(normal(yc=184, amp=8, period=45, phase=622), 622, 740)             # regime change
    path = "M" + " L".join(pts)

    chips = [
        (215, 96,  80,  "Alarm",         "fig-lit-box c-orange", "fig-lit-title", "fig-d2"),
        (380, 126, 92,  "Stress",        "fig-lit-box c-blue",   "fig-lit-title", "fig-d3"),
        (529, 130, 104, "Anomaly",       "fig-lit-box c-green",  "fig-lit-title", "fig-d4"),
        (680, 180, 124, "New condition", "fig-centre",           "fig-centre-title", "fig-d5"),
    ]
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 372" '
        'class="fig-event-detection" role="img" aria-label="A continuous signal with '
        'four episodes: a spike past the alarm threshold, a sustained elevated '
        'plateau, a burst of abnormal oscillation, and a shift to a new operating '
        'level. Beneath the trace, each episode produces a typed event chip: alarm, '
        'stress, anomaly, new condition.">',
        '<text class="fig-title" x="20" y="24">From a continuous signal to typed events</text>',
        '<text class="fig-sub" x="20" y="44">The signal never says anything; it just varies.</text>'
        '<text class="fig-sub" x="20" y="60">Detection functions decide when the variation means something.</text>',
        '<line class="fig-track" x1="70" y1="112" x2="740" y2="112"/>',
        '<text class="fig-box-sub" x="70" y="104">alarm threshold</text>',
        f'<path class="fig-line-a fig-draw" d="{path}"/>',
        '<text class="fig-box-sub" x="70" y="272" text-anchor="start">Events</text>',
    ]
    for cx, ay, w, label, box, tcls, delay in chips:
        bx = min(max(cx - w / 2, 74), 744 - w)
        p.append(
            f'<g class="fig-seq {delay}">'
            f'<line class="fig-track" x1="{cx}" y1="{ay + 8}" x2="{cx}" y2="246"/>'
            f'<rect class="{box}" x="{bx:.0f}" y="250" width="{w}" height="32" rx="16"/>'
            f'<text class="{tcls}" x="{bx + w / 2:.0f}" y="271" text-anchor="middle">{label}</text>'
            f'</g>'
        )
    p.append('<text class="fig-box-sub" x="20" y="330">The signal is continuous; what it '
             'means is discrete. Each detection lands as a typed event, anchored to the'
             '</text>')
    p.append('<text class="fig-box-sub" x="20" y="348">equipment it concerns, in the same '
             'event log as every alarm and work order, ready to overlay, query, or wake an '
             'agent.</text>')
    p.append("</svg>")
    return "\n".join(p)


# --------------------------------------------------------------- function wiring
def function_wiring():
    """A function node in the graph: reads several series and an event stream,
    writes new typed events, anchored to equipment. THEMED; structure static,
    flow on the data paths because data movement is what flow is for.
    """
    inputs = [
        ("21-VT-2101 · vibration", "c-green", 100),
        ("21-TT-2102 · bearing temp", "c-green", 158),
        ("21-ST-2103 · shaft speed", "c-green", 216),
        ("Maintenance events", "c-orange", 274),
    ]
    entries = (146, 162, 178, 194)
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 352" '
        'class="fig-function-wiring" role="img" aria-label="A graph fragment: three '
        'time series and a maintenance event stream flow into a bearing stress '
        'detector function, which writes new stress-detected events, anchored to '
        'Pump P-101.">',
        '<text class="fig-title" x="20" y="24">A function is a node: it reads, and it writes</text>',
        '<text class="fig-sub" x="20" y="44">Three signals and the maintenance history in; '
        'new typed events out, anchored to the equipment.</text>',
    ]
    for i, (label, colour, cy) in enumerate(inputs):
        p.append(
            f'<rect class="fig-lit-box {colour}" x="20" y="{cy - 22}" width="216" height="44" rx="12"/>'
            f'<text class="fig-lit-title" x="128" y="{cy + 5}" text-anchor="middle">{label}</text>'
        )
        p.append(f'<path class="fig-exit-path fig-flow" d="M236 {cy} L330 {entries[i]}" fill="none"/>')
        p.append(f'<path class="fig-centre" d="M330 {entries[i] - 5} L340 {entries[i]} L330 {entries[i] + 5} z"/>')
    p.append('<text class="fig-box-sub" x="283" y="112" text-anchor="middle">reads</text>')
    p.append(
        '<rect class="fig-lit-box c-blue" x="340" y="138" width="170" height="64" rx="12"/>'
        '<text class="fig-lit-title" x="425" y="164" text-anchor="middle">Function</text>'
        '<text class="fig-lit-sub" x="425" y="182" text-anchor="middle">bearing stress detector</text>'
    )
    p.append('<path class="fig-exit-path fig-flow" d="M510 155 L560 124" fill="none"/>')
    p.append('<path class="fig-centre" d="M556 118 L566 121 L558 129 z"/>')
    p.append('<text class="fig-box-sub" x="533" y="118" text-anchor="middle">writes</text>')
    p.append(
        '<rect class="fig-lit-box c-orange" x="566" y="90" width="174" height="56" rx="12"/>'
        '<text class="fig-lit-title" x="653" y="113" text-anchor="middle">Events</text>'
        '<text class="fig-lit-sub" x="653" y="131" text-anchor="middle">stress detected</text>'
    )
    p.append('<line class="fig-track" x1="653" y1="146" x2="653" y2="190"/>')
    p.append('<text class="fig-box-sub" x="665" y="172">concerns</text>')
    p.append(
        '<rect class="fig-centre" x="566" y="190" width="174" height="44" rx="12"/>'
        '<text class="fig-centre-title" x="653" y="217" text-anchor="middle">Pump P-101</text>'
    )
    p.append('<text class="fig-box-sub" x="20" y="322">Wiring this, which series a function reads, '
             'what it writes, and which equipment its output concerns, works today.</text>')
    p.append('<text class="fig-box-sub" x="20" y="340">When execution ships, this exact wiring is '
             'what runs, and what lineage is read from.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------ detection to action
def detection_to_action():
    """Signals in, function detects, event wakes an agent, agent drafts an
    action for human approval. THEMED; flow on every data hop, structure still.
    """
    inputs = [
        ("21-PT-3105 · pressure", "c-green", 96),
        ("21-TT-3106 · line temp", "c-green", 148),
        ("Pigging events", "c-orange", 200),
    ]
    entries = (132, 148, 164)
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 376" '
        'class="fig-detection-action" role="img" aria-label="A chain in the graph: '
        'line pressure, line temperature and pigging events feed a hydrate risk watch '
        'function, which writes a hydrate risk event. The event wakes an inhibitor '
        'planner agent, which drafts a dose and a pigging run for control-room '
        'approval.">',
        '<text class="fig-title" x="20" y="24">From detection to action, every hop in the graph</text>',
        '<text class="fig-sub" x="20" y="44">A function detects, the event wakes an agent, '
        'and the agent drafts. A person still approves.</text>',
    ]
    for i, (label, colour, cy) in enumerate(inputs):
        p.append(
            f'<rect class="fig-lit-box {colour}" x="20" y="{cy - 20}" width="180" height="40" rx="12"/>'
            f'<text class="fig-lit-sub" x="110" y="{cy + 4}" text-anchor="middle">{label}</text>'
        )
        p.append(f'<path class="fig-exit-path fig-flow" d="M200 {cy} L250 {entries[i]}" fill="none"/>')
        p.append(f'<path class="fig-centre" d="M250 {entries[i] - 5} L260 {entries[i]} L250 {entries[i] + 5} z"/>')
    p.append('<text class="fig-box-sub" x="225" y="100" text-anchor="middle">reads</text>')
    p.append(
        '<rect class="fig-lit-box c-blue" x="260" y="118" width="160" height="60" rx="12"/>'
        '<text class="fig-lit-title" x="340" y="142" text-anchor="middle">Function</text>'
        '<text class="fig-lit-sub" x="340" y="160" text-anchor="middle">hydrate risk watch</text>'
    )
    p.append('<path class="fig-exit-path fig-flow" d="M420 148 L548 148" fill="none"/>')
    p.append('<path class="fig-centre" d="M548 143 L560 148 L548 153 z"/>')
    p.append('<text class="fig-box-sub" x="485" y="140" text-anchor="middle">writes</text>')
    p.append(
        '<rect class="fig-lit-box c-orange" x="560" y="120" width="180" height="56" rx="12"/>'
        '<text class="fig-lit-title" x="650" y="143" text-anchor="middle">Events</text>'
        '<text class="fig-lit-sub" x="650" y="161" text-anchor="middle">hydrate risk</text>'
    )
    # the event wakes the agent
    p.append('<path class="fig-exit-path fig-flow" d="M650 176 L650 232" fill="none"/>')
    p.append('<path class="fig-centre" d="M645 232 L650 244 L655 232 z"/>')
    p.append('<text class="fig-box-sub" x="662" y="210">wakes</text>')
    p.append(
        '<rect class="fig-lit-box c-blue" x="560" y="244" width="180" height="56" rx="28"/>'
        '<text class="fig-lit-title" x="650" y="267" text-anchor="middle">Agent</text>'
        '<text class="fig-lit-sub" x="650" y="285" text-anchor="middle">inhibitor planner</text>'
    )
    # the agent drafts, for approval
    p.append('<path class="fig-exit-path fig-flow" d="M560 272 L522 272" fill="none"/>')
    p.append('<path class="fig-centre" d="M522 267 L510 272 L522 277 z"/>')
    p.append('<text class="fig-box-sub" x="541" y="264" text-anchor="middle">acts</text>')
    p.append(
        '<rect class="fig-centre" x="250" y="244" width="260" height="56" rx="12"/>'
        '<text class="fig-centre-title" x="380" y="268" text-anchor="middle">drafts dose + pigging run</text>'
        '<text class="fig-centre-sub" x="380" y="286" text-anchor="middle">for control-room approval</text>'
    )
    p.append('<text class="fig-box-sub" x="20" y="344">The agent bypasses no one: it drafts, and '
             'the control room approves. And because every hop is a node or an event,</text>')
    p.append('<text class="fig-box-sub" x="20" y="362">the whole chain from raw signal to action '
             'is traceable afterwards, which is what makes autonomy auditable.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------- revolution contrast
def revolution_contrast():
    """Third revolution: every machine has a loop, and no machine knows its
    neighbour. Fourth: same machines, same loops, now facts in one model.
    THEMED; static comparison, flow only on the right half's connections.

    Geometry note: the right half's chip must clear the panel heading at y=86,
    the first version started it at y=78 and overlapped the title text.
    """
    def loop_glyph(cx, cy):
        """A self-loop perched on the node's top-right corner, graph-editor
        style: the circle straddles the corner, its opening faces down-left
        into the node, and the arrow returns into it.

        (cx, cy) is the node's top-right corner.
        """
        import math as _m
        r = 9
        ccx, ccy = cx + 5, cy - 5                  # centre nudged out along the diagonal
        a0, a1 = _m.radians(165), _m.radians(105)  # 300-degree arc, gap toward the node
        sx, sy = ccx + r * _m.cos(a0), ccy + r * _m.sin(a0)
        ex, ey = ccx + r * _m.cos(a1), ccy + r * _m.sin(a1)
        tx, ty = -_m.sin(a1), _m.cos(a1)           # clockwise travel at the arc end
        nx, ny = _m.cos(a1), _m.sin(a1)
        tip = (ex + 5.5 * tx, ey + 5.5 * ty)       # points back into the node
        b1 = (ex - 2 * tx + 3.6 * nx, ey - 2 * ty + 3.6 * ny)
        b2 = (ex - 2 * tx - 3.6 * nx, ey - 2 * ty - 3.6 * ny)
        return (
            f'<path class="fig-loop-arc" d="M{sx:.1f} {sy:.1f} A {r} {r} 0 1 1 {ex:.1f} {ey:.1f}"/>'
            f'<path class="fig-loop-head" d="M{tip[0]:.1f} {tip[1]:.1f} L{b1[0]:.1f} {b1[1]:.1f} L{b2[0]:.1f} {b2[1]:.1f} z"/>'
        )

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 348" '
        'class="fig-revolution-contrast" role="img" aria-label="Two halves. Left, '
        'the third revolution: three machines, each with its own closed control loop '
        'and no connection between them. Right, the fourth: the same machines and '
        'loops, now connected to each other and upward to the process they serve.">',
        '<text class="fig-title" x="20" y="24">The difference is not more automation</text>',
        '<text class="fig-sub" x="20" y="44">Revolution three gave every machine a loop. '
        'Revolution four lets the loops be reasoned about together.</text>',
        '<line class="fig-track" x1="380" y1="66" x2="380" y2="336"/>',
        '<text class="fig-box-title" x="30" y="86">Third: each machine, alone</text>',
        '<text class="fig-box-title" x="395" y="86">Fourth: connected, in context</text>',
    ]
    # left: isolated machines, loops attached, nothing between them
    for (x, y, label) in ((30, 116, "Pump"), (200, 116, "Compressor"), (115, 218, "Separator")):
        p.append(
            f'<rect class="fig-box" x="{x}" y="{y}" width="150" height="48" rx="12"/>'
            f'<text class="fig-box-title" x="{x + 75}" y="{y + 29}" text-anchor="middle">{label}</text>'
        )
        p.append(loop_glyph(x + 150, y))
    p.append('<text class="fig-box-sub" x="30" y="330">Each controller holds its loop '
             'perfectly, and knows nothing else.</text>')
    # right: same machines, connected, with the process above (chip clears the heading)
    p.append(
        '<rect class="fig-centre" x="490" y="100" width="150" height="40" rx="12"/>'
        '<text class="fig-centre-title" x="565" y="125" text-anchor="middle">Process · KPI</text>'
    )
    for (x1, y1, x2, y2) in ((530, 140, 470, 170), (600, 140, 640, 170),
                             (535, 192, 585, 192), (450, 214, 525, 260), (670, 214, 595, 260)):
        p.append(f'<path class="fig-exit-path fig-flow" d="M{x1} {y1} L{x2} {y2}" fill="none"/>')
    for x, y, label in ((395, 170, "Pump"), (585, 170, "Compressor"), (490, 260, "Separator")):
        p.append(
            f'<rect class="fig-lit-box c-blue" x="{x}" y="{y}" width="140" height="44" rx="12"/>'
            f'<text class="fig-lit-title" x="{x + 70}" y="{y + 27}" text-anchor="middle">{label}</text>'
        )
        p.append(loop_glyph(x + 140, y))
    p.append('<text class="fig-box-sub" x="395" y="330">Same machines, same loops, now facts '
             'in one model.</text>')
    p.append("</svg>")
    return "\n".join(p)


# -------------------------------------------------------- famous vs foundation
def famous_vs_foundation():
    """Each revolution\'s celebrated technology over the boring foundation that
    actually enabled it, with the fourth foundation highlighted because it is
    the one still being built. THEMED, static.
    """
    cols = [
        ("c. 1780", "Steam engine", ("power, placed", "where needed"), False),
        ("c. 1870", "Assembly line", ("interchangeable", "parts"), False),
        ("c. 1970", "Computers + PLCs", ("computation cheap", "enough for everything"), False),
        ("now", "AI and agents", ("a machine-readable", "model of the operation"), True),
    ]
    bw, gap, x0 = 170, 16, 20
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 328" '
        'class="fig-famous-foundation" role="img" aria-label="Four columns, one per '
        'industrial revolution. The top row holds the celebrated technology: steam '
        'engine, assembly line, computers and PLCs, AI and agents. The bottom row '
        'holds the foundation each stood on: placed power, interchangeable parts, '
        'cheap computation, and a machine-readable model of the operation, the last '
        'one highlighted because it is the one still being built.">',
        '<text class="fig-title" x="20" y="24">The famous part, and the part that made it work</text>',
        '<text class="fig-sub" x="20" y="44">Every revolution is named after its technology '
        'and enabled by its foundation.</text>',
        '<text class="fig-box-sub" x="20" y="90">the celebrated part</text>',
        '<text class="fig-box-sub" x="20" y="186">the foundation it stood on</text>',
    ]
    for i, (era, famous, (f1, f2), lit) in enumerate(cols):
        x = x0 + i * (bw + gap)
        cx = x + bw / 2
        p.append(
            f'<rect class="fig-box" x="{x}" y="{98}" width="{bw}" height="52" rx="12"/>'
            f'<text class="fig-box-title" x="{cx:.0f}" y="{129}" text-anchor="middle">{famous}</text>'
        )
        p.append(f'<line class="fig-track" x1="{cx:.0f}" y1="194" x2="{cx:.0f}" y2="162"/>')
        p.append(f'<path class="fig-centre" d="M{cx - 5:.0f} 162 L{cx:.0f} 150 L{cx + 5:.0f} 162 z"/>')
        box = "fig-lit-box c-blue" if lit else "fig-centre"
        sub = "fig-lit-sub" if lit else "fig-centre-sub"
        p.append(
            f'<rect class="{box}" x="{x}" y="{194}" width="{bw}" height="60" rx="12"/>'
            f'<text class="{sub}" x="{cx:.0f}" y="{219}" text-anchor="middle">{f1}</text>'
            f'<text class="{sub}" x="{cx:.0f}" y="{237}" text-anchor="middle">{f2}</text>'
        )
        p.append(f'<text class="fig-box-sub" x="{cx:.0f}" y="278" text-anchor="middle">{era}</text>')
    p.append('<text class="fig-box-sub" x="20" y="312">The foundation is always less glamorous '
             'than the technology, and always the part that decides who wins.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------ function branching
def function_branching():
    """Clone a function, improve the copy, race both against the same inputs.
    THEMED; the branch drawn outlined until it earns promotion, flow on every
    data edge because the race is two pipelines running at once.
    """
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 404" '
        'class="fig-function-branching" role="img" aria-label="A pipeline forking '
        'like a git branch: tank level and air temperature feed both the production '
        'cleaning function v1 and its cloned, modified copy v2. Each writes its own '
        'corrected series, and both outputs feed a comparison against lab '
        'measurements, which decides promotion.">',
        '<text class="fig-title" x="20" y="24">Branching a pipeline, like branching code</text>',
        '<text class="fig-sub" x="20" y="44">Clone the cleaning function, improve the '
        'algorithm in the copy, and race both against the same inputs.</text>',
    ]
    # shared inputs
    for label, cy in (("21-LT-4012 · tank level", 120), ("21-TT-4013 · air temp", 176)):
        p.append(
            f'<rect class="fig-lit-box c-green" x="20" y="{cy - 21}" width="190" height="42" rx="12"/>'
            f'<text class="fig-lit-sub" x="115" y="{cy + 4}" text-anchor="middle">{label}</text>'
        )
    # the fork: both inputs feed both branches
    for x1, y1, x2, y2 in ((210, 120, 260, 110), (210, 176, 260, 122),
                           (210, 120, 260, 226), (210, 176, 260, 238)):
        p.append(f'<path class="fig-exit-path fig-flow" d="M{x1} {y1} L{x2} {y2}" fill="none"/>')
        p.append(f'<path class="fig-centre" d="M{x2} {y2 - 5} L{x2 + 10} {y2} L{x2} {y2 + 5} z"/>')
    p.append('<text class="fig-box-sub" x="233" y="196" text-anchor="middle">clone</text>')
    # v1, in production
    p.append(
        '<rect class="fig-lit-box c-blue" x="270" y="88" width="180" height="56" rx="12"/>'
        '<text class="fig-lit-title" x="360" y="111" text-anchor="middle">Clean · v1</text>'
        '<text class="fig-lit-sub" x="360" y="129" text-anchor="middle">in production</text>'
    )
    # v2, the branch: outlined until it earns promotion
    p.append(
        '<rect class="fig-box" x="270" y="204" width="180" height="56" rx="12"/>'
        '<text class="fig-box-title" x="360" y="227" text-anchor="middle">Clean · v2</text>'
        '<text class="fig-box-sub" x="360" y="245" text-anchor="middle">cloned, new algorithm</text>'
    )
    # parallel outputs
    for y1, y2 in ((116, 116), (232, 232)):
        p.append(f'<path class="fig-exit-path fig-flow" d="M450 {y1} L500 {y2}" fill="none"/>')
        p.append(f'<path class="fig-centre" d="M500 {y2 - 5} L510 {y2} L500 {y2 + 5} z"/>')
    p.append(
        '<rect class="fig-lit-box c-green" x="510" y="88" width="180" height="56" rx="12"/>'
        '<text class="fig-lit-title" x="600" y="111" text-anchor="middle">level · corrected v1</text>'
        '<text class="fig-lit-sub" x="600" y="129" text-anchor="middle">what reports use today</text>'
    )
    p.append(
        '<rect class="fig-box" x="510" y="204" width="180" height="56" rx="12"/>'
        '<text class="fig-box-title" x="600" y="227" text-anchor="middle">level · corrected v2</text>'
        '<text class="fig-box-sub" x="600" y="245" text-anchor="middle">the challenger</text>'
    )
    # both outputs rail into the comparison
    p.append('<line class="fig-track" x1="690" y1="116" x2="724" y2="116"/>')
    p.append('<line class="fig-track" x1="690" y1="232" x2="724" y2="232"/>')
    p.append('<line class="fig-track" x1="724" y1="116" x2="724" y2="318"/>')
    p.append('<line class="fig-track" x1="724" y1="318" x2="694" y2="318"/>')
    p.append('<path class="fig-centre" d="M694 313 L682 318 L694 323 z"/>')
    p.append(
        '<rect class="fig-centre" x="502" y="290" width="180" height="56" rx="12"/>'
        '<text class="fig-centre-title" x="592" y="313" text-anchor="middle">compare accuracy</text>'
        '<text class="fig-centre-sub" x="592" y="331" text-anchor="middle">against the lab dips</text>'
    )
    p.append('<text class="fig-box-sub" x="20" y="372">Both branches read the same inputs and '
             'write parallel series, so the race is fair and cheap to judge.</text>')
    p.append('<text class="fig-box-sub" x="20" y="390">Promote the winner. The loser and the '
             'comparison stay in the graph, so the pipeline improves without losing its history.</text>')
    p.append("</svg>")
    return "\n".join(p)


# --------------------------------------------------------------- data governance
def data_governance():
    """Governance assembled from four platform pieces. THEMED, static.

    Filled boxes work end to end today; outlined ones record today and act
    later, the same convention as the value-plays map.
    """
    pieces = [
        ("Knowledge graph", "what we have,", "who is accountable,", "the living register", True),
        ("Data sets", "who may use it,", "access granted per set,", "reviewed in one pass", True),
        ("Policies", "the rules, recorded", "on the data itself;", "enforcement coming", False),
        ("Functions", "trusted computation,", "one shared definition;", "execution coming", False),
    ]
    bw, gap, x0, top, bh = 168, 16, 20, 170, 100
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 348" '
        'class="fig-data-governance" role="img" aria-label="Data governance at the '
        'centre, carried by four platform pieces: the knowledge graph holds the '
        'inventory and ownership, data sets hold access, policies hold the recorded '
        'rules with enforcement coming, and functions hold trusted computation with '
        'execution coming.">',
        '<text class="fig-title" x="20" y="24">Governance, assembled from pieces you already know</text>',
        '<text class="fig-sub" x="20" y="44">Each answer lives on the thing it governs, '
        'instead of in a document beside it.</text>',
        '<rect class="fig-centre" x="285" y="66" width="190" height="56" rx="14"/>',
        '<text class="fig-centre-title" x="380" y="90" text-anchor="middle">Data governance</text>',
        '<text class="fig-centre-sub" x="380" y="108" text-anchor="middle">five questions, one place</text>',
    ]
    for i, (title, l1, l2, l3, shipped) in enumerate(pieces):
        x = x0 + i * (bw + gap)
        cx = x + bw / 2
        p.append(f'<line class="fig-track" x1="380" y1="122" x2="{cx:.0f}" y2="{top}"/>')
        box = "fig-lit-box c-blue" if shipped else "fig-box"
        t = "fig-lit-title" if shipped else "fig-box-title"
        sub = "fig-lit-sub" if shipped else "fig-box-sub"
        p.append(
            f'<rect class="{box}" x="{x}" y="{top}" width="{bw}" height="{bh}" rx="12"/>'
            f'<text class="{t}" x="{cx:.0f}" y="{top + 26}" text-anchor="middle">{title}</text>'
            f'<text class="{sub}" x="{cx:.0f}" y="{top + 48}" text-anchor="middle">{l1}</text>'
            f'<text class="{sub}" x="{cx:.0f}" y="{top + 64}" text-anchor="middle">{l2}</text>'
            f'<text class="{sub}" x="{cx:.0f}" y="{top + 80}" text-anchor="middle">{l3}</text>'
        )
    p.append(
        '<rect class="fig-lit-box c-blue" x="20" y="304" width="14" height="14" rx="4"/>'
        '<text class="fig-box-sub" x="42" y="315">working end to end today</text>'
        '<rect class="fig-box" x="220" y="304" width="14" height="14" rx="4"/>'
        '<text class="fig-box-sub" x="242" y="315">recording works today; acting on it is on the roadmap</text>'
    )
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------------ policy agent
def policy_agents():
    """The four moments a rule can act, and the agent covering the gap. THEMED.

    Filled means the platform enforces it today, outlined means the rule is
    recorded and enforcement is on the roadmap, the same convention as the
    data-governance map. The only motion is `fig-flow` on the agent's rail,
    because "checks it continuously" is the whole claim being made.
    """
    gw, gap, gy, gh = 168, 16, 104, 84
    gates = (
        ("At the write", ("the id must match the", "convention, so a write is",
                          "refused or flagged"), True),
        ("While it sits", ("owner named, description", "filled, review not overdue"), False),
        ("At the read", ("who may see it, and", "on what terms"), False),
        ("At the end of life", ("kept ten years, then", "expired on schedule"), False),
    )
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 372" '
        'class="fig-policy-agents" role="img" aria-label="Four moments where a '
        'policy can act: at the write, while the data sits, at the read, and at the '
        'end of its life. Only the first is filled in, meaning the platform enforces '
        'it today. A policy agent underneath feeds a rail up to the other three, '
        'checking them continuously and passing findings to a person who decides.">',
        '<text class="fig-title" x="20" y="24">A rule that acts, and what acts on it</text>',
        '<text class="fig-sub" x="20" y="44">One policy, four moments where it can bite. The '
        'platform enforces the first today.</text>',
    ]
    for i, (title, subs, shipped) in enumerate(gates):
        x = 20 + i * (gw + gap)
        cx = x + gw / 2
        box = "fig-lit-box c-blue" if shipped else "fig-box"
        t = "fig-lit-title" if shipped else "fig-box-title"
        sub = "fig-lit-sub" if shipped else "fig-box-sub"
        p.append(f'<rect class="{box}" x="{x}" y="{gy}" width="{gw}" height="{gh}" rx="12"/>')
        p.append(f'<text class="{t}" x="{cx:.0f}" y="{gy + 28}" text-anchor="middle">{title}'
                 f'</text>')
        for j, line in enumerate(subs):
            p.append(f'<text class="{sub}" x="{cx:.0f}" y="{gy + 50 + j * 16}" '
                     f'text-anchor="middle">{line}</text>')
        if i < 3:
            p.append(f'<path class="fig-centre" d="M{x + gw + 3} {gy + 36} L{x + gw + 12} '
                     f'{gy + 42} L{x + gw + 3} {gy + 48} z"/>')

    # the agent's rail: one continuous check, feeding the three gates the
    # platform does not enforce yet
    p.append('<path class="fig-exit-path fig-flow" d="M120 248 L120 210 L656 210" '
             'fill="none"/>')
    for cx in (288, 472, 656):
        p.append(f'<line class="fig-exit-path" x1="{cx}" y1="210" x2="{cx}" y2="196"/>')
        p.append(f'<path class="fig-lit-box c-green" d="M{cx - 6} 198 L{cx} 188 L{cx + 6} '
                 f'198 z"/>')
    p.append('<text class="fig-box-sub" x="238" y="232">checks continuously what the platform '
             'does not enforce yet</text>')

    p.append('<rect class="fig-exit-box" x="20" y="248" width="330" height="76" rx="14"/>')
    p.append('<text class="fig-exit-title" x="185" y="276" text-anchor="middle">Policy '
             'agent</text>')
    p.append('<text class="fig-exit-sub" x="185" y="296" text-anchor="middle">reads the rule off '
             'the data set, watches</text>')
    p.append('<text class="fig-exit-sub" x="185" y="312" text-anchor="middle">for what breaks it, '
             'drafts the correction</text>')
    p.append('<path class="fig-exit-path fig-flow" d="M350 286 L430 286" fill="none"/>')
    p.append('<rect class="fig-box" x="430" y="248" width="310" height="76" rx="14"/>')
    p.append('<text class="fig-box-title" x="585" y="276" text-anchor="middle">A person '
             'decides</text>')
    p.append('<text class="fig-box-sub" x="585" y="296" text-anchor="middle">closes the finding, '
             'fixes the data, changes</text>')
    p.append('<text class="fig-box-sub" x="585" y="312" text-anchor="middle">the rule, or records '
             'the exception</text>')
    p.append('<rect class="fig-lit-box c-blue" x="20" y="342" width="14" height="14" rx="4"/>'
             '<text class="fig-box-sub" x="42" y="353">enforced by the platform today</text>'
             '<rect class="fig-box" x="260" y="342" width="14" height="14" rx="4"/>'
             '<text class="fig-box-sub" x="282" y="353">recorded today, enforced when the '
             'feature ships</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------- subscription flow
def subscription_flow():
    """Polling against push delivery. THEMED.

    Static structure per the house rule; the only motion is fig-flow on the
    subscription lane (continuous delivery) and a pulse on the datapoint stuck
    waiting in the polling lane. The contrast IS the argument.
    """
    bw, bh = 150, 44
    lx, rx = 20, 590          # platform box left, consumer box right
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 372" '
        'class="fig-subscription-flow" role="img" aria-label="Two lanes comparing '
        'polling with a subscription. In the polling lane a new datapoint sits '
        'waiting on the platform until the next scheduled ask. In the subscription '
        'lane data flows continuously to the consumer the moment it arrives.">',
        '<text class="fig-title" x="20" y="24">Polling asks. A subscription is told.</text>',
        '<text class="fig-sub" x="20" y="44">Same data, same consumer. The difference is '
        'who initiates, and therefore how long new data waits.</text>',
    ]

    def lane(y, heading):
        return (
            f'<text class="fig-box-title" x="20" y="{y - 14}">{heading}</text>'
            f'<rect class="fig-box" x="{lx}" y="{y}" width="{bw}" height="{bh}" rx="12"/>'
            f'<text class="fig-box-title" x="{lx + bw/2:.0f}" y="{y + 27}" text-anchor="middle">DataHub</text>'
            f'<rect class="fig-box" x="{rx}" y="{y}" width="{bw}" height="{bh}" rx="12"/>'
            f'<text class="fig-box-title" x="{rx + bw/2:.0f}" y="{y + 27}" text-anchor="middle">Your system</text>'
        )

    # ---- lane 1: polling
    y1 = 92
    mid1 = y1 + bh / 2
    p.append(lane(y1, "Polling"))
    p.append(f'<line class="fig-track" x1="{lx + bw}" y1="{mid1:.0f}" x2="{rx}" y2="{mid1:.0f}"/>')
    # scheduled asks, marked as ticks along the track
    for i, tx in enumerate((300, 420, 540)):
        p.append(f'<line class="fig-track" x1="{tx}" y1="{mid1 - 9:.0f}" x2="{tx}" y2="{mid1 + 9:.0f}"/>')
        p.append(f'<text class="fig-box-sub" x="{tx}" y="{mid1 - 16:.0f}" text-anchor="middle">ask</text>')
    # the datapoint that arrived just after an ask, pulsing while it waits
    p.append(f'<circle class="fig-token fig-pulse" cx="318" cy="{mid1:.0f}" r="7"/>')
    p.append(
        f'<text class="fig-box-sub" x="318" y="{mid1 + 28:.0f}" text-anchor="middle">arrives here</text>'
        f'<text class="fig-box-sub" x="420" y="{mid1 + 44:.0f}" text-anchor="middle">and waits for the next ask</text>'
    )
    p.append('<text class="fig-box-sub" x="20" y="188">Latency is set by the schedule: on average half the '
             'polling interval, however fresh the data is.</text>')

    # ---- lane 2: subscription
    y2 = 248
    mid2 = y2 + bh / 2
    p.append(lane(y2, "Subscription"))
    p.append(f'<path class="fig-exit-path fig-flow" d="M{lx + bw} {mid2:.0f} L{rx} {mid2:.0f}" fill="none"/>')
    p.append(f'<circle class="fig-token" cx="380" cy="{mid2:.0f}" r="7"/>')
    p.append(
        f'<text class="fig-box-sub" x="380" y="{mid2 + 28:.0f}" text-anchor="middle">pushed the moment it arrives</text>'
    )
    p.append('<text class="fig-box-sub" x="20" y="344">Latency is set by delivery: milliseconds inside the '
             'platform, plus whatever your network adds.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------------ value plays
def value_plays():
    """The six plays positioned by effort and time to value. THEMED, static.

    Static: a reader compares positions, so everything must be visible at once.
    Shipped plays are filled, planned ones outlined, because that distinction
    changes which one you should pick first.
    """
    plays = [
        ("Data liberation", 0.10, 0.10, False),
        ("Faster investigations", 0.20, 0.30, False),
        ("Capital handover", 0.05, 0.50, False),
        ("Condition monitoring", 0.58, 0.66, False),
        ("Audit-ready reporting", 0.52, 0.50, True),
        ("Energy and emissions", 0.86, 0.86, True),
    ]
    px0, px1, py0, py1 = 120, 690, 92, 300
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 400" '
        'class="fig-value-plays" role="img" aria-label="Six value plays plotted by '
        'effort against time to value. Data liberation and faster investigations sit '
        'lowest on both axes. Audit-ready reporting and energy and emissions are marked '
        'as planned rather than available today.">',
        '<text class="fig-title" x="20" y="24">Which play to start with</text>',
        '<text class="fig-sub" x="20" y="44">Lower and further left is cheaper to reach. '
        'Start bottom-left and work outward.</text>',
        f'<line class="fig-track" x1="{px0}" y1="{py1}" x2="{px1}" y2="{py1}"/>',
        f'<line class="fig-track" x1="{px0}" y1="{py0}" x2="{px0}" y2="{py1}"/>',
        f'<text class="fig-box-sub" x="{px0 - 10}" y="{py0 + 8}" text-anchor="end">more</text>',
        f'<text class="fig-box-sub" x="{px0 - 10}" y="{py1}" text-anchor="end">less</text>',
        f'<text class="fig-box-sub" x="{px0 - 66}" y="{(py0 + py1) / 2:.0f}">effort</text>',
        f'<text class="fig-box-sub" x="{(px0 + px1) / 2:.0f}" y="{py1 + 30}" text-anchor="middle">'
        'weeks, to quarters, to a year</text>',
    ]
    for label, fx, fy, planned in plays:
        x = px0 + fx * (px1 - px0)
        y = py1 - fy * (py1 - py0)
        box = "fig-box" if planned else "fig-lit-box c-blue"
        txt = "fig-box-sub" if planned else "fig-lit-sub"
        w = max(112, int(6.4 * len(label)) + 22)
        bx = min(max(x - w / 2, px0 + 4), 744 - w)
        p.append(f'<circle class="fig-token" cx="{x:.0f}" cy="{y:.0f}" r="6"/>')
        p.append(
            f'<rect class="{box}" x="{bx:.0f}" y="{y - 34:.0f}" width="{w}" height="24" rx="10"/>'
            f'<text class="{txt}" x="{bx + w / 2:.0f}" y="{y - 18:.0f}" text-anchor="middle">{label}</text>'
        )
    p.append(
        '<rect class="fig-lit-box c-blue" x="20" y="342" width="14" height="14" rx="4"/>'
        '<text class="fig-box-sub" x="42" y="353">available today</text>'
        '<rect class="fig-box" x="176" y="342" width="14" height="14" rx="4"/>'
        '<text class="fig-box-sub" x="198" y="353">depends on capability still on the roadmap</text>'
    )
    p.append("</svg>")
    return "\n".join(p)


# ----------------------------------------------------------------- board gates
def board_gates():
    """The four points at which a board sees evidence. THEMED, static.

    Static on purpose: a board reads this as a comparison across gates, not as
    a sequence unfolding.
    """
    gates = [
        ("Day 0", "Approve", "One question named,", "an owner named,", "baseline recorded", "fig-lit-box c-blue"),
        ("90 days", "Continue?", "The question answered,", "and how, in writing.", "Compared to baseline", "fig-lit-box c-orange"),
        ("6 months", "Compounding", "Second question costs", "less than the first,", "or we find out why", "fig-box"),
        ("12 months", "Return", "Recurring hours saved,", "per cycle and per", "incident", "fig-box"),
    ]
    bw, bh, gap, top = 170, 132, 20, 118
    x0 = (760 - (len(gates) * bw + (len(gates) - 1) * gap)) / 2
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 296" '
        'class="fig-board-gates" role="img" aria-label="Four board decision points: '
        'day zero approval, a ninety day continue decision, a six month test of whether '
        'the second question cost less than the first, and a twelve month recurring '
        'return.">',
        '<text class="fig-title" x="20" y="24">What the board sees, and when</text>',
        '<text class="fig-sub" x="20" y="44">Four pre-agreed tests. Each one produces '
        'evidence rather than a status update.</text>',
        f'<line class="fig-track" x1="{x0:.0f}" y1="92" x2="{x0 + 4 * bw + 3 * gap:.0f}" y2="92"/>',
    ]
    for i, (when, title, l1, l2, l3, box) in enumerate(gates):
        x = x0 + i * (bw + gap)
        cx = x + bw / 2
        lit = box != "fig-box"
        t = "fig-lit-title" if lit else "fig-box-title"
        sub = "fig-lit-sub" if lit else "fig-box-sub"
        p.append(f'<circle class="fig-token" cx="{cx:.0f}" cy="92" r="7"/>')
        p.append(
            f'<rect class="{box}" x="{x:.0f}" y="{top}" width="{bw}" height="{bh}" rx="12"/>'
            f'<text class="{sub}" x="{cx:.0f}" y="{top + 24}" text-anchor="middle">{when}</text>'
            f'<text class="{t}" x="{cx:.0f}" y="{top + 48}" text-anchor="middle">{title}</text>'
            f'<text class="{sub}" x="{cx:.0f}" y="{top + 74}" text-anchor="middle">{l1}</text>'
            f'<text class="{sub}" x="{cx:.0f}" y="{top + 90}" text-anchor="middle">{l2}</text>'
            f'<text class="{sub}" x="{cx:.0f}" y="{top + 106}" text-anchor="middle">{l3}</text>'
        )
    p.append(
        '<text class="fig-box-sub" x="20" y="278">If the evidence is not there at a gate, '
        'stopping is the correct outcome, and it is cheap.</text>'
    )
    p.append("</svg>")
    return "\n".join(p)


# ----------------------------------------------------------------- tag anatomy
def tag_anatomy():
    """Break a real plant tag into the four questions it answers. THEMED."""
    # segment widths sized to their text; separators sit between them
    segs = [
        ("VAL", 122, "c-blue", "Installation", "VAL = Valhall", "which facility the", "equipment sits on"),
        ("21", 92, "c-green", "System", "21 = process system", "the functional area", "within the facility"),
        ("PT", 92, "c-orange", "Instrument type", "P = pressure", "T = transmitter", "read per ISA-5.1"),
        ("1234", 134, "centre", "Sequence number", "1234 = this one", "unique inside the", "system, not globally"),
    ]
    sep_w, tag_y, tag_h = 26, 86, 54
    total = sum(s[1] for s in segs) + sep_w * (len(segs) - 1)
    x = (760 - total) / 2

    # explanation boxes spread evenly, leader lines connect them to their segment
    bw, bgap = 168, 18
    b_total = len(segs) * bw + (len(segs) - 1) * bgap
    bx0 = (760 - b_total) / 2
    box_y, box_h = 202, 96

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 340" '
        'class="fig-tag-anatomy" role="img" aria-label="The plant tag VAL-21-PT-1234 '
        'broken into four parts: VAL for the Valhall installation, 21 for the process '
        'system, PT for a pressure transmitter under ISA-5.1, and 1234 as the sequence '
        'number unique within that system.">',
        '<text class="fig-title" x="20" y="24">Anatomy of a plant tag</text>',
        '<text class="fig-sub" x="20" y="44">Every segment answers one question: where, '
        'which system, what kind of instrument, which one.</text>',
    ]
    seg_centres = []
    cx = x
    for i, (text, w, colour, *_rest) in enumerate(segs):
        centre = cx + w / 2
        seg_centres.append(centre)
        if colour == "centre":
            p.append(f'<rect class="fig-centre" x="{cx:.0f}" y="{tag_y}" width="{w}" height="{tag_h}" rx="12"/>')
            p.append(f'<text class="fig-tag fig-tag--dark" x="{centre:.0f}" y="{tag_y + 36}" text-anchor="middle">{text}</text>')
        else:
            p.append(f'<rect class="fig-lit-box {colour}" x="{cx:.0f}" y="{tag_y}" width="{w}" height="{tag_h}" rx="12"/>')
            p.append(f'<text class="fig-tag" x="{centre:.0f}" y="{tag_y + 36}" text-anchor="middle">{text}</text>')
        cx += w
        if i < len(segs) - 1:
            p.append(f'<text class="fig-sep" x="{cx + sep_w / 2:.0f}" y="{tag_y + 36}" text-anchor="middle">-</text>')
            cx += sep_w

    for i, (_t, _w, _c, title, l1, l2, l3) in enumerate(segs):
        bx = bx0 + i * (bw + bgap)
        bcx = bx + bw / 2
        p.append(
            f'<path class="fig-track" d="M{seg_centres[i]:.0f} {tag_y + tag_h} '
            f'L{bcx:.0f} {box_y}" fill="none"/>'
        )
        p.append(
            f'<g><rect class="fig-box" x="{bx:.0f}" y="{box_y}" width="{bw}" height="{box_h}" rx="12"/>'
            f'<text class="fig-box-title" x="{bcx:.0f}" y="{box_y + 24}" text-anchor="middle">{title}</text>'
            f'<text class="fig-box-sub" x="{bcx:.0f}" y="{box_y + 46}" text-anchor="middle">{l1}</text>'
            f'<text class="fig-box-sub" x="{bcx:.0f}" y="{box_y + 62}" text-anchor="middle">{l2}</text>'
            f'<text class="fig-box-sub" x="{bcx:.0f}" y="{box_y + 78}" text-anchor="middle">{l3}</text></g>'
        )

    p.append(
        '<text class="fig-box-sub" x="20" y="326">Tagging schemes differ between operators. '
        'Mirror whichever one your facility already uses rather than inventing another.</text>'
    )
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------ industrial revolutions
def industrial_revolutions():
    """Four revolutions, each enabled by a new foundation. THEMED."""
    stages = [
        ("c. 1780", "Mechanisation", "Steam and water power.", "Machines replace muscle."),
        ("c. 1870", "Mass production", "Electricity, assembly", "lines and standard parts."),
        ("c. 1970", "Automation", "Electronics, computers,", "a controller per machine."),
        ("now", "Context", "The whole operation", "modelled as one system."),
    ]
    w, gap, x0, top, h = 168, 16, 20, 104, 92
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 272" '
        'class="fig-industrial-revolutions" role="img" aria-label="A timeline of '
        'four industrial revolutions: mechanisation around 1780, mass production '
        'around 1870, automation around 1970, and today\'s contextual, connected '
        'operations.">',
        '<text class="fig-title" x="20" y="24">Four industrial revolutions</text>',
        '<text class="fig-sub" x="20" y="44">Each one arrived when a new foundation '
        'made a new kind of operation possible.</text>',
        f'<line class="fig-track" x1="{x0}" y1="82" x2="{x0 + 4 * w + 3 * gap}" y2="82"/>',
    ]
    for i, (date, title, l1, l2) in enumerate(stages):
        x = x0 + i * (w + gap)
        cx = x + w / 2
        last = i == len(stages) - 1
        box = 'fig-lit-box c-blue' if last else 'fig-box'
        t_cls = 'fig-lit-title' if last else 'fig-box-title'
        s_cls = 'fig-lit-sub' if last else 'fig-box-sub'
        p.append(
            f'<g class="fig-seq fig-d{i + 1}">'
            f'<circle class="fig-token" cx="{cx:.0f}" cy="82" r="7"/>'
            f'<rect class="{box}" x="{x}" y="{top}" width="{w}" height="{h}" rx="12"/>'
            f'<text class="{s_cls}" x="{cx:.0f}" y="{top + 20}" text-anchor="middle">{date}</text>'
            f'<text class="{t_cls}" x="{cx:.0f}" y="{top + 42}" text-anchor="middle">{title}</text>'
            f'<text class="{s_cls}" x="{cx:.0f}" y="{top + 64}" text-anchor="middle">{l1}</text>'
            f'<text class="{s_cls}" x="{cx:.0f}" y="{top + 79}" text-anchor="middle">{l2}</text>'
            f'</g>'
        )
    p.append(
        '<text class="fig-box-sub" x="20" y="232">Power, then standardisation, then '
        'computation — and now context: a machine-readable</text>'
        '<text class="fig-box-sub" x="20" y="250">model of the operation itself, '
        'which is the part most organisations do not yet have.</text>'
    )
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------- experiment rate
def experiment_rate():
    """Same team, same year, different cost per experiment. THEMED, static.

    Deliberately NOT animated: the two rows are meant to be compared against
    each other, and a staggered reveal stops a reader holding both in view at
    once. The counters carry the point instead.
    """
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 372" '
        'class="fig-experiment-rate" role="img" aria-label="Two rows comparing '
        'experiment throughput over one month. Without a shared model, three long '
        'trials each spend most of their time preparing data. With liberated data '
        'the preparation collapses and twelve experiments fit into the same month.">',
        '<text class="fig-title" x="20" y="24">Innovation runs at the speed of its slowest experiment</text>',
        '<text class="fig-sub" x="20" y="44">Same team, same month. The only difference is what one trial costs to start.</text>',
    ]

    def counter(x, y, value, l1, l2, lit):
        box = 'fig-lit-box c-green' if lit else 'fig-box'
        vc = 'fig-stat fig-stat--on-fill' if lit else 'fig-stat'
        lc = 'fig-stat-label--on-fill' if lit else 'fig-stat-label'
        cx = x + 80
        return (f'<rect class="{box}" x="{x}" y="{y}" width="160" height="58" rx="12"/>'
                f'<text class="{vc}" x="{cx}" y="{y + 30}" text-anchor="middle">{value}</text>'
                f'<text class="{lc}" x="{cx}" y="{y + 44}" text-anchor="middle">{l1}</text>'
                f'<text class="{lc}" x="{cx}" y="{y + 55}" text-anchor="middle">{l2}</text>')

    # ---- slow row
    p.append('<text class="fig-box-title" x="20" y="84">Without a shared model</text>')
    p.append('<line class="fig-track" x1="20" y1="152" x2="560" y2="152"/>')
    for i in range(3):
        x = 20 + i * 188
        p.append(
            f'<rect class="fig-box" x="{x}" y="100" width="116" height="42" rx="10"/>'
            f'<text class="fig-box-sub" x="{x + 58}" y="126" text-anchor="middle">preparing data</text>'
            f'<rect class="fig-lit-box c-blue" x="{x + 120}" y="100" width="44" height="42" rx="10"/>'
            f'<text class="fig-lit-sub" x="{x + 142}" y="126" text-anchor="middle">trial</text>'
        )
    p.append('<text class="fig-box-sub" x="20" y="176">Each trial has to be worth funding before it starts</text>')
    p.append(counter(580, 92, "3", "experiments", "per month", lit=False))

    # ---- fast row
    p.append('<text class="fig-box-title" x="20" y="228">With liberated data</text>')
    p.append('<line class="fig-track" x1="20" y1="296" x2="560" y2="296"/>')
    for j in range(12):
        x = 20 + j * 45
        p.append(
            f'<rect class="fig-box" x="{x}" y="244" width="10" height="42" rx="4"/>'
            f'<rect class="fig-lit-box c-green" x="{x + 12}" y="244" width="30" height="42" rx="8"/>'
        )
    p.append('<text class="fig-box-sub" x="20" y="320">A trial no longer needs a business case, so more of them happen</text>')
    p.append(counter(580, 236, "12", "experiments", "per month", lit=True))

    # ---- legend
    p.append(
        '<rect class="fig-box" x="20" y="344" width="14" height="14" rx="4"/>'
        '<text class="fig-box-sub" x="42" y="355">preparing data</text>'
        '<rect class="fig-lit-box c-green" x="150" y="344" width="14" height="14" rx="4"/>'
        '<text class="fig-box-sub" x="172" y="355">actually experimenting</text>'
    )
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------------- token bridge
def token_bridge():
    """An external IdP token becoming a Keycloak token before reaching the API."""
    boxes = [
        (60, "Your corporate\nidentity provider", "e.g. Entra ID", MUTED),
        (300, "Keycloak", "the issuer DataHub trusts", BLUE),
        (548, "DataHub API", "validates and serves", GREEN),
    ]
    bw, bh, by = 152, 76, 116
    css = f"""
    text {{ font-family: {FONT}; }}   /* no fill: a type rule beats every fill="" attribute */
    /* One token, travelling the whole way and passing BEHIND the boxes.
       It keeps ONE colour the whole way: a colour change mid-flight reads as
       a second, different token, which is not what happens. */
    @keyframes ride {{
      0%, 5%   {{ transform: translateX(0); opacity: 0 }}
      9%       {{ opacity: 1 }}
      23%      {{ transform: translateX(183px) }}
      45%      {{ transform: translateX(440px); opacity: 1 }}
      50%,100% {{ transform: translateX(440px); opacity: 0 }}
    }}
    /* visible 49%-89% of 12s = 4.8s, three times the previous 1.6s */
    @keyframes checks {{ 0%,43% {{opacity:0}} 49%,89% {{opacity:1}} 93%,100% {{opacity:0}} }}
    .rider {{ animation: ride 12s ease-in-out infinite; }}
    .checks {{ opacity:0; animation: checks 12s ease-in-out infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .t1,.t2 {{ animation: none; opacity: 1 }} .checks {{ animation: none; opacity: 1 }} }}
    """
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 330" role="img" '
        'aria-label="A token from your corporate identity provider is exchanged at '
        'Keycloak for a Keycloak-issued token, which is what the DataHub API accepts. '
        'The API checks the issuer, the roles and the organization claim.">',
        f"<style>{css}</style>",
        f'<text x="20" y="26" font-weight="800" font-size="15" fill="{BLUE}">'
        "Whatever your identity provider, DataHub trusts one issuer</text>",
        f'<text x="20" y="46" font-size="12.5" fill="{MUTED}">'
        "An external token is exchanged for a Keycloak token before it reaches the API.</text>",
    ]
    # arrows
    for x1, x2 in ((212, 300), (452, 548)):
        p.append(
            f'<line x1="{x1}" y1="{by + bh/2:.0f}" x2="{x2 - 8}" y2="{by + bh/2:.0f}" '
            f'stroke="{TEAL}" stroke-width="2.5"/>'
            f'<path d="M{x2 - 8} {by + bh/2 - 5:.0f} L{x2} {by + bh/2:.0f} L{x2 - 8} '
            f'{by + bh/2 + 5:.0f} z" fill="{TEAL}"/>'
        )
    # the token floats above the connector lines but below the boxes, so it
    # slides out from behind one box, across the arrow, and under the next
    p.append(
        f'<g class="rider"><rect x="176" y="{by + bh/2 - 13:.0f}" '
        f'width="34" height="26" rx="8" fill="{BLUE}"/>'
        f'<text x="193" y="{by + bh/2 + 5:.0f}" text-anchor="middle" font-size="11" '
        f'font-weight="800" fill="#ffffff">JWT</text></g>'
    )
    for x, title, sub, colour in boxes:
        lines = title.split("\n")
        p.append(
            f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="14" fill="#ffffff" '
            f'stroke="{colour}" stroke-width="2.5"/>'
        )
        for i, ln in enumerate(lines):
            p.append(
                f'<text x="{x + bw/2:.0f}" y="{by + 28 + i*16}" text-anchor="middle" '
                f'font-size="13" font-weight="800" fill="{colour}">{ln}</text>'
            )
        p.append(
            f'<text x="{x + bw/2:.0f}" y="{by + 28 + len(lines)*16 + 4}" text-anchor="middle" '
            f'font-size="10.5" fill="{MUTED}">{sub}</text>'
        )
    p.append(
        f'<text x="256" y="{by - 12}" text-anchor="middle" font-size="10.5" font-weight="700" '
        f'fill="{MUTED}">exchange</text>'
        f'<text x="500" y="{by - 12}" text-anchor="middle" font-size="10.5" font-weight="700" '
        f'fill="{MUTED}">bearer</text>'
    )
    # what the API checks
    checks = ["issuer is Keycloak", "roles in realm_access.roles", "organization claim present"]
    p.append(f'<g class="checks">')
    for i, c in enumerate(checks):
        y = 232 + i * 24
        p.append(
            f'<circle cx="{560}" cy="{y - 4}" r="6" fill="{GREEN}"/>'
            f'<path d="M557 {y - 4} l2.4 2.4 l4.4 -4.8" stroke="#ffffff" stroke-width="1.8" '
            f'fill="none" stroke-linecap="round"/>'
            f'<text x="574" y="{y}" font-size="12" fill="{INK}">{c}</text>'
        )
    p.append(
        f'<text x="548" y="212" font-size="11.5" font-weight="800" fill="{GREEN}">'
        "the API checks all three</text></g>"
    )
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------- liberation translate
def liberation_translate():
    """Four vendor record shapes become three primitives. THEMED.

    The only motion is the fig-flow dashes on the arrows: data moving through
    the translation. Boxes and chips are structure, so they hold still.
    """
    rows = [  # (system, what it sends, left centre-y, right attach-y)
        ("Maintenance system", "equipment master record", 102, 114),
        ("Historian", "tag 21-PT-1034.PV", 162, 194),
        ("Work-permit system", "permit 4471, hot work", 222, 266),
        ("ERP", "purchase order 4500171", 282, 282),
    ]
    chips = [
        ("Resources", "the things it all concerns", "c-blue", 86),
        ("Time series", "measurements over time", "c-green", 166),
        ("Events", "things that happened, at a time", "c-orange", 246),
    ]
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 376" '
        'class="fig-liberation-translate" role="img" aria-label="Four differently '
        'shaped vendor records, an equipment master record, a historian tag, a hot '
        'work permit and a purchase order, flow into three primitives: resources, time '
        'series and events. The permit and the purchase order land in the same '
        'events chip.">',
        '<text class="fig-title" x="20" y="24">Liberation simplifies, it does not copy</text>',
        '<text class="fig-sub" x="20" y="44">Whatever a silo sends becomes one of a '
        'few primitives, without copying its schema.</text>',
        '<text class="fig-box-sub" x="148" y="68" text-anchor="middle">What the silos send</text>',
        '<text class="fig-box-sub" x="616" y="68" text-anchor="middle">What you read, one interface</text>',
    ]
    for title, sends, ly, ry in rows:
        p.append(
            f'<path class="fig-exit-path fig-flow" d="M268 {ly} C 340 {ly} 420 {ry} 492 {ry}" fill="none"/>'
        )
    for title, sends, ly, ry in rows:
        y = ly - 24
        p.append(
            f'<rect class="fig-box" x="28" y="{y}" width="240" height="48" rx="12"/>'
            f'<text class="fig-box-title" x="148" y="{ly - 4}" text-anchor="middle">{title}</text>'
            f'<text class="fig-box-sub" x="148" y="{ly + 14}" text-anchor="middle">{sends}</text>'
        )
    for title, sub, c, y in chips:
        p.append(
            f'<rect class="fig-lit-box {c}" x="492" y="{y}" width="248" height="56" rx="12"/>'
            f'<text class="fig-lit-title" x="616" y="{y + 23}" text-anchor="middle">{title}</text>'
            f'<text class="fig-lit-sub" x="616" y="{y + 41}" text-anchor="middle">{sub}</text>'
        )
    p.append(
        '<text class="fig-sub" x="20" y="344">One interface reads all of it, and '
        'nobody has to learn a vendor schema again.</text>'
        '<text class="fig-sub" x="20" y="362">No new cage: the model is tiny and '
        'documented, and data leaves in open formats.</text>'
    )
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------- resource anatomy
def resource_anatomy():
    """The anatomy of one ontology entry. THEMED, static: pure structure.

    A resource card with its three fields, each annotated with the standard
    RDF role it plays, plus the relationship below that makes it a graph.
    """
    fields = [  # (field label, value, label baseline y)
        ("Name, changes freely", "21-PT-1234 Separator inlet pressure", 124),
        ("Label, the kind of thing", "PressureTransmitter", 168),
        ("External id, never changes", "21-PT-1234", 212),
    ]
    anns = [  # (role, note, box top y)
        ("rdfs:label", "for people; rename freely", 115),
        ("rdf:type", "for querying whole kinds at once", 159),
        ("the IRI", "for systems; matched on, forever", 203),
    ]
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 384" '
        'class="fig-resource-anatomy" role="img" aria-label="A resource card with '
        'three fields: the name, which is the rdfs:label and changes freely; the '
        'label PressureTransmitter, which is the rdf:type; and the external id '
        '21-PT-1234, which is the IRI part that never changes. Below, a monitors '
        'relationship connects it to the separator V-201, annotated as the '
        'predicate that makes the model a graph.">',
        '<text class="fig-title" x="20" y="24">One entry, three promises</text>',
        '<text class="fig-sub" x="20" y="44">The resource form\'s three fields, and '
        'the standard role each one plays.</text>',
        '<rect class="fig-centre" x="36" y="70" width="340" height="190" rx="14"/>',
        '<text class="fig-centre-title" x="206" y="98" text-anchor="middle">A resource in the ontology</text>',
    ]
    for (label, value, ly), (role, note, ay) in zip(fields, anns):
        rc = ly + 10  # row centre, aligned with its annotation box centre
        p.append(
            f'<text class="fig-centre-sub" x="56" y="{ly}">{label}</text>'
            f'<text class="fig-box-title" x="56" y="{ly + 18}">{value}</text>'
            f'<line class="fig-track" x1="376" y1="{rc}" x2="470" y2="{rc}"/>'
            f'<rect class="fig-box" x="470" y="{ay}" width="270" height="38" rx="10"/>'
            f'<text class="fig-box-title" x="486" y="{ay + 16}">{role}</text>'
            f'<text class="fig-box-sub" x="486" y="{ay + 31}">{note}</text>'
        )
    p.append(
        '<path class="fig-track" d="M206 260 L206 278 L335 278 L335 296" fill="none"/>'
        '<text class="fig-box-sub" x="225" y="273">monitors</text>'
        '<rect class="fig-lit-box c-blue" x="240" y="296" width="190" height="48" rx="12"/>'
        '<text class="fig-lit-title" x="335" y="316" text-anchor="middle">V-201</text>'
        '<text class="fig-lit-sub" x="335" y="334" text-anchor="middle">the separator it monitors</text>'
        '<line class="fig-track" x1="430" y1="320" x2="470" y2="320"/>'
        '<rect class="fig-box" x="470" y="301" width="270" height="38" rx="10"/>'
        '<text class="fig-box-title" x="486" y="317">the predicate</text>'
        '<text class="fig-box-sub" x="486" y="332">relationships make it a graph</text>'
    )
    p.append(
        '<text class="fig-sub" x="20" y="372">The same three roles RDF defines, '
        'which is why your model is portable rather than proprietary.</text>'
    )
    p.append("</svg>")
    return "\n".join(p)



# ------------------------------------------------------------ digital twin mirror
def digital_twin_mirror():
    """The physical operation mirrored by its digital twin. THEMED.

    Perfect row-for-row symmetry is the point: each physical thing has exactly
    one digital counterpart. The fig-flow arrows are the live sync, and the
    return path along the bottom is the loop closing, decisions flowing back.
    """
    rows = [  # (physical title, physical sub, digital title, digital sub, colour, cy)
        ("Pump P-101", "the machine itself",
         "Resource P-101", "in the knowledge graph", "c-blue", 114),
        ("Sensor 21-PT-1034", "measuring inlet pressure",
         "Time series", "datapoints, seconds behind reality", "c-green", 194),
        ("Maintenance crew", "opening a work order",
         "Event", "the work order, in the log", "c-orange", 274),
    ]
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 364" '
        'class="fig-digital-twin-mirror" role="img" aria-label="Three physical '
        'things, a pump, a sensor and a maintenance crew, each mirrored by a '
        'digital counterpart: a resource in the knowledge graph, a time series and '
        'an event. Live data flows left to right keeping the twin in sync, and a '
        'return path along the bottom carries decisions and actions back to the '
        'operation, closing the loop.">',
        '<text class="fig-title" x="20" y="24">One operation, mirrored</text>',
        '<text class="fig-sub" x="20" y="44">Each physical thing has one digital '
        'counterpart, and live data keeps the mirror honest.</text>',
        '<text class="fig-box-sub" x="148" y="68" text-anchor="middle">The physical operation</text>',
        '<text class="fig-box-sub" x="616" y="68" text-anchor="middle">The digital twin</text>',
    ]
    for pt, ps, dt, ds, c, cy in rows:
        p.append(f'<path class="fig-exit-path fig-flow" d="M268 {cy} L492 {cy}" fill="none"/>')
    p.append('<path class="fig-exit-path fig-flow" d="M616 302 L616 330 L148 330 L148 298" fill="none"/>')
    for pt, ps, dt, ds, c, cy in rows:
        p.append(
            f'<rect class="fig-box" x="28" y="{cy - 24}" width="240" height="48" rx="12"/>'
            f'<text class="fig-box-title" x="148" y="{cy - 4}" text-anchor="middle">{pt}</text>'
            f'<text class="fig-box-sub" x="148" y="{cy + 14}" text-anchor="middle">{ps}</text>'
            f'<rect class="fig-lit-box {c}" x="492" y="{cy - 28}" width="248" height="56" rx="12"/>'
            f'<text class="fig-lit-title" x="616" y="{cy - 5}" text-anchor="middle">{dt}</text>'
            f'<text class="fig-lit-sub" x="616" y="{cy + 13}" text-anchor="middle">{ds}</text>'
        )
    p.append(
        '<text class="fig-box-sub" x="382" y="348" text-anchor="middle">decisions '
        'and actions flow back, closing the loop</text>'
    )
    p.append("</svg>")
    return "\n".join(p)



# --------------------------------------------------------- agent organisation
def agent_organisation():
    """An organisation chart of agents. THEMED.

    Worker agents do tasks, manager agents own domains, one coordinator holds
    the whole against goals humans set. Work flows down the chart (fig-flow),
    results flow back up the right-hand return path, and everyone stands on
    the same knowledge-graph bar: the shared workplace.
    """
    managers = [  # (title, sub, centre x)
        ("Operations", "keeps the work moving", 97),
        ("Reporting", "reports what matters", 269),
        ("Integrity", "hunts faults and drift", 527),
    ]
    workers = [  # (title, sub, centre x, manager centre x)
        ("Integrations", "runs and repairs feeds", 97, 97),
        ("Reports", "drafts and delivers", 269, 269),
        ("Fault watch", "flags faults early", 441, 527),
        ("Data quality", "spots drift and gaps", 613, 527),
    ]

    def badge(bx, by):
        """The chip that marks a node as run by an AI agent: a little robot
        head and the word, perched on the box's top-left corner. Leadership
        never gets one, that contrast is the figure's point."""
        return (
            f'<rect class="fig-badge" x="{bx}" y="{by}" width="58" height="18" rx="9"/>'
            f'<line class="fig-badge-line" x1="{bx + 11}" y1="{by + 5}" x2="{bx + 11}" y2="{by + 2.5}"/>'
            f'<circle class="fig-badge-dot" cx="{bx + 11}" cy="{by + 2.2}" r="1.1"/>'
            f'<rect class="fig-badge-line" x="{bx + 6}" y="{by + 5}" width="10" height="8.5" rx="2"/>'
            f'<circle class="fig-badge-dot" cx="{bx + 9}" cy="{by + 9.4}" r="1.2"/>'
            f'<circle class="fig-badge-dot" cx="{bx + 13}" cy="{by + 9.4}" r="1.2"/>'
            f'<text class="fig-badge-text" x="{bx + 21}" y="{by + 13}">agent</text>'
        )

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 412" '
        'class="fig-agent-organisation" role="img" aria-label="An organisation '
        'chart of AI agents. Leadership sets the goals for a coordinator agent, '
        'which divides them among three manager agents for operations, reporting '
        'and integrity. Under them, worker agents run integrations, draft reports, '
        'flag faults and watch data quality. Work flows down the chart, results '
        'flow back up a return path, and all of the agents stand on one shared '
        'bar: the knowledge graph, the context and workplace they have in '
        'common. Every agent node carries a small robot badge reading agent; '
        'the leadership box carries none, because leadership is human.">',
        '<text class="fig-title" x="20" y="24">An organisation of agents</text>',
        '<text class="fig-sub" x="20" y="44">The same shape as a human organisation, '
        'because it solves the same problem: many hands, one goal.</text>',
    ]
    # work flowing down the chart
    for mt, ms, mx in managers:
        p.append(f'<path class="fig-exit-path fig-flow" '
                 f'd="M380 152 C 380 168, {mx} 164, {mx} 180" fill="none"/>')
    for wt, ws, wx, mx in workers:
        p.append(f'<path class="fig-exit-path fig-flow" '
                 f'd="M{mx} 236 C {mx} 250, {wx} 250, {wx} 264" fill="none"/>')
    # results and scores flowing back up the right-hand side
    p.append('<path class="fig-exit-path fig-flow" '
             'd="M710 368 L730 368 L730 124 L490 124" fill="none"/>')
    p.append('<text class="fig-box-sub" x="610" y="116" text-anchor="middle">results flow back up</text>')
    # every agent stands on the graph
    for wt, ws, wx, mx in workers:
        p.append(f'<line class="fig-track" x1="{wx}" y1="320" x2="{wx}" y2="344"/>')
    p.append('<line class="fig-track" x1="170" y1="124" x2="270" y2="124"/>')
    # leadership and the coordinator
    p.append(
        '<rect class="fig-box" x="20" y="96" width="150" height="56" rx="12"/>'
        '<text class="fig-box-title" x="95" y="120" text-anchor="middle">Leadership</text>'
        '<text class="fig-box-sub" x="95" y="138" text-anchor="middle">sets the goals</text>'
        '<rect class="fig-centre" x="270" y="96" width="220" height="56" rx="14"/>'
        '<text class="fig-centre-title" x="380" y="120" text-anchor="middle">Coordinator agent</text>'
        '<text class="fig-centre-sub" x="380" y="138" text-anchor="middle">divides goals, sets incentives</text>'
    )
    p.append(badge(280, 87))
    for mt, ms, mx in managers:
        p.append(
            f'<rect class="fig-lit-box c-blue" x="{mx - 75}" y="180" width="150" height="56" rx="12"/>'
            f'<text class="fig-lit-title" x="{mx}" y="204" text-anchor="middle">{mt}</text>'
            f'<text class="fig-lit-sub" x="{mx}" y="222" text-anchor="middle">{ms}</text>'
        )
        p.append(badge(mx - 65, 171))
    for wt, ws, wx, mx in workers:
        p.append(
            f'<rect class="fig-lit-box c-green" x="{wx - 77}" y="264" width="155" height="56" rx="12"/>'
            f'<text class="fig-lit-title" x="{wx}" y="288" text-anchor="middle">{wt}</text>'
            f'<text class="fig-lit-sub" x="{wx}" y="306" text-anchor="middle">{ws}</text>'
        )
        p.append(badge(wx - 67, 255))
    p.append(
        '<rect class="fig-lit-box c-orange" x="20" y="344" width="690" height="48" rx="12"/>'
        '<text class="fig-lit-title" x="365" y="364" text-anchor="middle">The knowledge graph</text>'
        '<text class="fig-lit-sub" x="365" y="381" text-anchor="middle">the shared '
        'context, and the shared workplace, for every agent</text>'
    )
    p.append("</svg>")
    return "\n".join(p)



# --------------------------------------------------------------- aliasing illusion
def aliasing_illusion():
    """The same fast signal sampled two ways. THEMED, static: a comparison.

    Right panel is the trap: every dot is a genuine measurement of the fast
    ghost signal, and the smooth slow wave through them is pure invention.
    The alias curve is exact, not sketched: sampling sin(2*pi*x/34) every
    30px produces samples that lie exactly on sin(2*pi*x/255) flipped, so
    the dots genuinely sit on both curves.
    """
    import math as _m
    mid, amp, t_true = 175, 42, 34.0

    def true_sine(x0, x1):
        return sine_path(x0, x1, mid, amp, t_true, phase=x0)

    def alias_sine(x0, x1):
        pts = []
        x = x0
        while x <= x1:
            y = mid + amp * _m.sin(2 * _m.pi * (x - x0) / 255.0)
            pts.append(f"{x:.1f} {y:.1f}")
            x += 4
        return "M" + " L".join(pts)

    def sample_dots(x0, x1, step, cls):
        out = []
        x = x0
        while x <= x1:
            y = mid - amp * _m.sin(2 * _m.pi * (x - x0) / t_true)
            out.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="3.2"/>')
            x += step
        return "".join(out)

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 338" '
        'class="fig-aliasing-illusion" role="img" aria-label="Two panels sampling '
        'the same fast signal. On the left, sampled fast enough, the reconstructed '
        'curve follows every oscillation. On the right, sampled too slowly, the '
        'genuine measurement dots trace out a smooth slow wave that does not '
        'exist in the real signal, the aliasing illusion.">',
        '<text class="fig-title" x="20" y="24">Aliasing: undersampling invents a slower signal</text>',
        '<text class="fig-sub" x="20" y="44">The same fast signal, sampled two ways. '
        'Every dot in both panels is a real measurement.</text>',
        '<text class="fig-box-title" x="195" y="76" text-anchor="middle">Sampled fast enough</text>',
        '<text class="fig-box-title" x="565" y="76" text-anchor="middle">Sampled too slowly</text>',
        f'<line class="fig-track" x1="30" y1="253" x2="360" y2="253"/>',
        f'<line class="fig-track" x1="420" y1="253" x2="730" y2="253"/>',
        f'<path class="fig-line-a" d="{true_sine(30, 360)}" fill="none"/>',
        sample_dots(30, 360, 8, "fig-dot-a"),
        f'<path class="fig-line--ghost" d="{true_sine(420, 730)}" fill="none"/>',
        f'<path class="fig-line-b" d="{alias_sine(420, 730)}" fill="none"/>',
        sample_dots(420, 730, 30, "fig-dot-b"),
        '<text class="fig-box-sub" x="195" y="285" text-anchor="middle">every behaviour you care about survives</text>',
        '<text class="fig-box-sub" x="565" y="285" text-anchor="middle">the dots are real; the slow wave they draw is not</text>',
        '<text class="fig-sub" x="20" y="308">The defence is chosen at the instrument, not '
        'repaired downstream:</text>'
        '<text class="fig-sub" x="20" y="326">sample faster than twice the fastest behaviour '
        'that matters.</text>',
    ]
    p.append("</svg>")
    return "\n".join(p)



# ------------------------------------------------------------ mcp one protocol
def mcp_one_protocol():
    """Bespoke integrations against one shared protocol. THEMED.

    Static, because the reader compares the two panels: the argument IS the
    line count. The only motion is fig-flow on the right-hand connectors, the
    same device subscription_flow uses to mark the lane that works.
    """
    bw, bh = 104, 34
    rows = (100, 150, 200)                       # box tops, both panels
    mids = [y + bh / 2 for y in rows]
    clients = ("Assistant", "Agent", "Copilot")
    systems = ("DataHub", "CMMS", "Historian")

    def box(x, y, label, w=bw):
        return (f'<rect class="fig-box" x="{x}" y="{y}" width="{w}" height="{bh}" rx="10"/>'
                f'<text class="fig-box-sub" x="{x + w / 2:.0f}" y="{y + 21}" '
                f'text-anchor="middle">{label}</text>')

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 340" '
        'class="fig-mcp-one-protocol" role="img" aria-label="Two panels. On the '
        'left, three AI clients each wired to three systems by a separate '
        'integration, nine lines in total. On the right, the same three clients '
        'and three systems connected through one shared protocol in the middle, '
        'six connections and none of them bespoke.">',
        '<text class="fig-title" x="20" y="24">One protocol instead of one integration per pair</text>',
        '<text class="fig-sub" x="20" y="44">Any client that speaks MCP can use any system that '
        'serves it. The system’s owner writes the server once.</text>',
        '<text class="fig-box-title" x="185" y="78" text-anchor="middle">Before: bespoke each time</text>',
        '<text class="fig-box-title" x="575" y="78" text-anchor="middle">With a shared protocol</text>',
    ]

    # ---- left panel: 3 x 3 bespoke connectors
    lx_sys = 246                                  # 246 + 104 = 350, the panel edge
    for cy in mids:
        for sy in mids:
            p.append(f'<line class="fig-track" x1="{bw + 20}" y1="{cy:.0f}" '
                     f'x2="{lx_sys}" y2="{sy:.0f}"/>')
    for y, label in zip(rows, clients):
        p.append(box(20, y, label))
    for y, label in zip(rows, systems):
        p.append(box(lx_sys, y, label))
    p.append('<text class="fig-box-sub" x="185" y="266" text-anchor="middle">'
             '3 clients × 3 systems = 9 integrations to write and maintain</text>')
    p.append('<text class="fig-box-sub" x="185" y="284" text-anchor="middle">'
             'add a fourth system and you write three more</text>')

    # ---- right panel: everything through one protocol
    rx_cli, bar_x, bar_w, rx_sys = 410, 548, 68, 650
    p.append(f'<rect class="fig-centre" x="{bar_x}" y="{rows[0]}" width="{bar_w}" '
             f'height="{rows[-1] + bh - rows[0]}" rx="14"/>')
    p.append(f'<text class="fig-centre-title" x="{bar_x + bar_w / 2:.0f}" y="{mids[1] + 5:.0f}" '
             f'text-anchor="middle">MCP</text>')
    for y, cy in zip(rows, mids):
        p.append(f'<path class="fig-exit-path fig-flow" d="M{rx_cli + bw} {cy:.0f} '
                 f'L{bar_x} {cy:.0f}" fill="none"/>')
        p.append(f'<path class="fig-exit-path fig-flow" d="M{bar_x + bar_w} {cy:.0f} '
                 f'L{rx_sys} {cy:.0f}" fill="none"/>')
    for y, label in zip(rows, clients):
        p.append(box(rx_cli, y, label))
    for y, label in zip(rows, systems):
        p.append(box(rx_sys, y, label, w=90))
    p.append('<text class="fig-box-sub" x="575" y="266" text-anchor="middle">'
             '3 clients + 3 systems = 6 connections, none of them bespoke</text>')
    p.append('<text class="fig-box-sub" x="575" y="284" text-anchor="middle">'
             'add a fourth system and it serves every client on day one</text>')

    p.append('<text class="fig-sub" x="20" y="316">DataHub sits on the right-hand side: it '
             'publishes its tools once, and an assistant, an agent</text>')
    p.append('<text class="fig-sub" x="20" y="334">you wrote or a coding tool all reach them the '
             'same way, with nothing written for any one of them.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------------- mcp call path
def mcp_call_path():
    """What one MCP call passes through. THEMED, animated.

    Motion earns its place here: this is a request travelling, not a comparison.
    fig-flow marches along every hop, and the four checks inside the gate reveal
    in sequence because they happen in that order, before any tool body runs.
    """
    row_y, row_h = 96, 52
    mid = row_y + row_h / 2
    gate_x, gate_w, gate_y, gate_h = 344, 176, 64, 132
    tool_x, tool_w, tool_h = 560, 180, 36
    tool_rows = (64, 110, 156)

    def arrow(x, y):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + 11} {y} L{x} {y + 5} z"/>'

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 320" '
        'class="fig-mcp-call-path" role="img" aria-label="A question travels from '
        'a person to an agent, which makes an MCP call carrying the user’s token. '
        'The call passes a gate that checks the token signature and issuer, the '
        'DataHub access role, the organization claim that selects the tenant, and '
        'the data set grants, before reaching the tools. The answer returns along '
        'the bottom with the ids and timestamps it used.">',
        '<text class="fig-title" x="20" y="24">An MCP call is an ordinary authenticated request</text>',
        '<text class="fig-sub" x="20" y="44">There is no agent door and no agent key. The same '
        'token, the same checks, in the same order.</text>',
        f'<text class="fig-box-sub" x="140" y="88" text-anchor="middle">a question</text>',
        f'<text class="fig-box-sub" x="333" y="88" text-anchor="end">MCP call, carrying your token</text>',
        f'<text class="fig-box-title" x="650" y="52" text-anchor="middle">37 tools</text>',
    ]

    # ---- person -> agent -> gate
    p.append(f'<rect class="fig-box" x="20" y="{row_y}" width="100" height="{row_h}" rx="12"/>'
             f'<text class="fig-box-title" x="70" y="{row_y + 31}" text-anchor="middle">You</text>')
    p.append(f'<path class="fig-exit-path fig-flow" d="M120 {mid:.0f} L149 {mid:.0f}" fill="none"/>')
    p.append(arrow(149, mid))
    p.append(f'<rect class="fig-lit-box c-blue" x="160" y="{row_y}" width="130" height="{row_h}" rx="12"/>'
             f'<text class="fig-lit-title" x="225" y="{row_y + 23}" text-anchor="middle">Agent</text>'
             f'<text class="fig-lit-sub" x="225" y="{row_y + 40}" text-anchor="middle">or assistant</text>')
    p.append(f'<path class="fig-exit-path fig-flow" d="M290 {mid:.0f} L333 {mid:.0f}" fill="none"/>')
    p.append(arrow(333, mid))

    # ---- the gate: four checks, in the order they are applied
    p.append(f'<rect class="fig-centre" x="{gate_x}" y="{gate_y}" width="{gate_w}" '
             f'height="{gate_h}" rx="12"/>')
    p.append(f'<text class="fig-centre-title" x="{gate_x + gate_w / 2:.0f}" y="{gate_y + 24}" '
             f'text-anchor="middle">Before any tool runs</text>')
    checks = ("signature and issuer", "DATAHUB_ACCESS role",
              "organization → tenant", "data set grants")
    for i, check in enumerate(checks):
        cy = gate_y + 48 + i * 21
        p.append(f'<g class="fig-seq fig-d{i + 1}">'
                 f'<circle class="fig-dot-a" cx="{gate_x + 16}" cy="{cy - 4}" r="4"/>'
                 f'<text class="fig-box-sub" x="{gate_x + 28}" y="{cy}">{check}</text></g>')

    # ---- gate -> the three tools it fans out to
    for y in tool_rows:
        ty = y + tool_h / 2
        p.append(f'<path class="fig-exit-path fig-flow" d="M{gate_x + gate_w} {mid:.0f} '
                 f'L{tool_x - 11} {ty:.0f}" fill="none"/>')
        p.append(arrow(tool_x - 11, ty))
    for y, name in zip(tool_rows, ("resource_fetch_related", "timeseries_fetch_datapoints",
                                   "event_filter")):
        p.append(f'<rect class="fig-box" x="{tool_x}" y="{y}" width="{tool_w}" '
                 f'height="{tool_h}" rx="10"/>'
                 f'<text class="fig-box-sub" x="{tool_x + tool_w / 2:.0f}" y="{y + 22}" '
                 f'text-anchor="middle">{name}</text>')

    # ---- and back again, with the evidence attached
    p.append(f'<path class="fig-exit-path fig-flow" d="M650 {tool_rows[-1] + tool_h} L650 236 '
             f'L70 236 L70 {row_y + row_h + 11}" fill="none"/>')
    p.append(f'<path class="fig-centre" d="M65 {row_y + row_h + 11} L70 {row_y + row_h} '
             f'L75 {row_y + row_h + 11} z"/>')
    p.append('<text class="fig-box-sub" x="360" y="256" text-anchor="middle">the answer, plus the '
             'ids, timestamps and values behind it</text>')
    p.append('<text class="fig-sub" x="20" y="288">A read-only agent is simply one holding a '
             'read-only token, which is why scoping an agent is</text>')
    p.append('<text class="fig-sub" x="20" y="306">the same administrative act as scoping any '
             'other service account, in the same place.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------- agent guardrails
def agent_guardrails():
    """The four limits an agent's action passes through. THEMED, animated.

    The boxes stay visible: a reader compares where each limit comes from. Only
    the connectors march, because the thing that moves here is the proposal.
    """
    bw, bh, by = 150, 64, 96
    xs = (20, 210, 400, 590)
    mid = by + bh / 2
    gates = (
        ("Token scope", "reads only its data sets", "set in your identity provider"),
        ("Step cap", "stops instead of churning", "set in the agent you build"),
        ("Human gate", "drafts, never dispatches", "set in your own process"),
        ("Event log", "every action recorded", "given by the platform"),
    )

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 300" '
        'class="fig-agent-guardrails" role="img" aria-label="A proposal passes '
        'through four limits in order: the token scope, which lets it read only '
        'its own data sets; a step cap, which stops it churning; a human gate, '
        'where it drafts rather than dispatches; and the event log, which records '
        'every action. The chain ends in autonomy you can audit.">',
        '<text class="fig-title" x="20" y="24">Four limits between an agent and a mistake</text>',
        '<text class="fig-sub" x="20" y="44">The first three you set, in three different places. '
        'The fourth is what makes the other three checkable.</text>',
    ]

    for i, (x, (title, sub, source)) in enumerate(zip(xs, gates)):
        if i:
            p.append(f'<path class="fig-exit-path fig-flow" d="M{x - 40} {mid:.0f} '
                     f'L{x - 11} {mid:.0f}" fill="none"/>')
            p.append(f'<path class="fig-centre" d="M{x - 11} {mid - 5:.0f} L{x} {mid:.0f} '
                     f'L{x - 11} {mid + 5:.0f} z"/>')
        p.append(f'<rect class="fig-box" x="{x}" y="{by}" width="{bw}" height="{bh}" rx="12"/>'
                 f'<text class="fig-box-title" x="{x + bw / 2:.0f}" y="{by + 26}" '
                 f'text-anchor="middle">{title}</text>'
                 f'<text class="fig-box-sub" x="{x + bw / 2:.0f}" y="{by + 45}" '
                 f'text-anchor="middle">{sub}</text>')
        p.append(f'<text class="fig-box-sub" x="{x + bw / 2:.0f}" y="{by + 94}" '
                 f'text-anchor="middle">{source}</text>')

    # the proposal entering the chain, and the outcome it earns by surviving it
    p.append(f'<circle class="fig-token fig-pulse" cx="10" cy="{mid:.0f}" r="6"/>')
    # Drop from the box's right edge, not its centre: the centre line would strike
    # through the "given by the platform" caption sitting directly under the box.
    p.append(f'<path class="fig-exit-path fig-flow" d="M{xs[-1] + bw} {by + bh} '
             f'L{xs[-1] + bw} 249 L541 249" fill="none"/>')
    p.append('<path class="fig-centre" d="M541 244 L530 249 L541 254 z"/>')
    p.append('<rect class="fig-exit-box" x="230" y="222" width="300" height="54" rx="14"/>'
             '<text class="fig-exit-title" x="380" y="246" text-anchor="middle">Autonomy you can '
             'audit</text>'
             '<text class="fig-exit-sub" x="380" y="264" text-anchor="middle">what it did, why, '
             'and what happened next</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------- agent graph join
def agent_graph_join():
    """Series on the left, events on the right, joined only by the model. THEMED.

    The point is the join, so the two outer columns are deliberately plain lists:
    what makes them one story is which node each one hangs off. Motion is
    fig-flow on the six connectors, the direction a question travels.
    """
    cw, ch = 170, 38
    rows = (94, 150, 206)
    mids = [y + ch / 2 for y in rows]
    lx, rx = 20, 570                                # chip columns
    # Gaps of 24px between the three nodes: the relationship labels sit in them, and
    # at 16px the FEEDS label disappeared behind the centre box.
    up_y, up_h = 88, 40
    ce_y, ce_h = 152, 54
    lo_y, lo_h = 230, 40
    up_mid, ce_mid, lo_mid = up_y + up_h / 2, ce_y + ce_h / 2, lo_y + lo_h / 2

    def chip(x, y, label):
        return (f'<rect class="fig-box" x="{x}" y="{y}" width="{cw}" height="{ch}" rx="10"/>'
                f'<text class="fig-box-sub" x="{x + cw / 2:.0f}" y="{y + 23}" '
                f'text-anchor="middle">{label}</text>')

    def node(x, w, y, h, title, sub):
        return (f'<rect class="fig-box" x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>'
                f'<text class="fig-box-title" x="{x + w / 2:.0f}" y="{y + 18}" '
                f'text-anchor="middle">{title}</text>'
                f'<text class="fig-box-sub" x="{x + w / 2:.0f}" y="{y + 33}" '
                f'text-anchor="middle">{sub}</text>')

    def link(x1, y1, x2, y2):
        return (f'<path class="fig-exit-path fig-flow" d="M{x1:.0f} {y1:.0f} '
                f'L{x2:.0f} {y2:.0f}" fill="none"/>')

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 344" '
        'class="fig-agent-graph-join" role="img" aria-label="Three time series on '
        'the left and three events on the right, with a small graph in the middle: '
        'a compressor, its lube system and the export line it feeds. Every series '
        'and every event connects to the node it belongs to, so the vibration '
        'trace, the high-vibration alarm and the lube work order meet on the same '
        'machine.">',
        '<text class="fig-title" x="20" y="24">The model is what joins a number to something that '
        'happened</text>',
        '<text class="fig-sub" x="20" y="44">A reading and an event have nothing in common until '
        'both hang off the same thing in the graph.</text>',
        '<text class="fig-box-title" x="105" y="78" text-anchor="middle">Time series</text>',
        '<text class="fig-box-title" x="390" y="78" text-anchor="middle">Your model</text>',
        '<text class="fig-box-title" x="655" y="78" text-anchor="middle">Events</text>',
    ]

    # ---- the six connectors, drawn first so the boxes sit on top of them
    p.append(link(lx + cw, mids[0], 290, ce_mid - 8))          # vibration -> compressor
    p.append(link(lx + cw, mids[1], 290, ce_mid))              # bearing temp -> compressor
    p.append(link(lx + cw, mids[2], 310, lo_mid))              # discharge -> export line
    p.append(link(rx, mids[0], 470, up_mid))                   # work order -> lube system
    p.append(link(rx, mids[1], 490, ce_mid + 8))               # alarm -> compressor
    p.append(link(rx, mids[2], 470, lo_mid))                   # inspection -> export line

    # ---- relationship edges inside the model
    p.append(f'<line class="fig-track" x1="390" y1="{up_y + up_h}" x2="390" y2="{ce_y}"/>')
    p.append(f'<line class="fig-track" x1="390" y1="{ce_y + ce_h}" x2="390" y2="{lo_y}"/>')
    p.append(f'<text class="fig-box-sub" x="398" y="{ce_y - 8}">HAS_PART</text>')
    p.append(f'<text class="fig-box-sub" x="398" y="{lo_y - 8}">FEEDS</text>')

    # ---- the three columns
    for y, label in zip(rows, ("21-VT-4013 · vibration", "21-TT-4015 · bearing temp",
                               "21-PT-3105 · discharge")):
        p.append(chip(lx, y, label))
    for y, label in zip(rows, ("WO-4471 · lube service", "ALM-8823 · high vibration",
                               "INSP-311 · flange check")):
        p.append(chip(rx, y, label))
    p.append(node(310, 160, up_y, up_h, "LUBE-12", "lube system"))
    p.append(f'<rect class="fig-lit-box c-blue" x="290" y="{ce_y}" width="200" '
             f'height="{ce_h}" rx="12"/>'
             f'<text class="fig-lit-title" x="390" y="{ce_y + 23}" text-anchor="middle">K-401</text>'
             f'<text class="fig-lit-sub" x="390" y="{ce_y + 40}" text-anchor="middle">export '
             f'compressor</text>')
    p.append(node(310, 160, lo_y, lo_h, "EXP-LINE", "export line"))

    p.append('<text class="fig-sub" x="20" y="304">Without the model these are two lists that '
             'happen to cover the same week. With it, one question</text>')
    p.append('<text class="fig-sub" x="20" y="322">reaches all six, and the agent can say which '
             'machine the story is about.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------- wind peer comparison
def wind_peer_comparison():
    """A07 against the turbines sharing its wind. THEMED.

    Plotted as a percentage of the string's median rather than as raw power,
    which is how the finding is actually visible: four per cent of a power curve
    is five pixels, four per cent of a relative trace is the whole point. Static,
    because the reader compares traces; the only motion is the string cable.
    """
    # ---- left: the string, which is what makes the peers peers
    sub_x, sub_y, sub_w, sub_h = 20, 140, 92, 44
    t_y = sub_y + sub_h / 2
    t_xs = [148, 196, 244, 292, 340]
    names = ["A05", "A06", "A07", "A08", "A09"]

    # ---- right: nine days, each turbine as a percentage of the string median
    x0, x1 = 452, 730
    y_lo, y_hi = 94.0, 102.0          # axis range, chosen so A07 clears the baseline
    py_bot, py_top = 252, 112

    def to_y(pct):
        return py_bot - (pct - y_lo) / (y_hi - y_lo) * (py_bot - py_top)

    def trace(level, amp, phase):
        pts = []
        steps = 36
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i / steps
            pct = level + amp * math.sin(2 * math.pi * (i / steps) * 1.7 + phase)
            pts.append(f"{x:.1f} {to_y(pct):.1f}")
        return "M" + " L".join(pts)

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 330" '
        'class="fig-wind-peer" role="img" aria-label="On the left, five turbines on '
        'one string running to a substation, with A07 highlighted. On the right, '
        'nine days of production for each turbine as a percentage of the string '
        'median: four traces sit around one hundred per cent and A07 sits steadily '
        'near ninety-six.">',
        '<text class="fig-title" x="20" y="24">Underperformance only exists as a comparison</text>',
        '<text class="fig-sub" x="20" y="44">Against its own history A07 looks normal. Against '
        'the turbines that shared its wind, it does not.</text>',
        '<text class="fig-box-title" x="20" y="78">String B</text>',
        '<text class="fig-box-sub" x="20" y="96">one cable, one wind, five comparable machines</text>',
    ]
    p.append(f'<path class="fig-exit-path fig-flow" d="M{t_xs[-1]} {t_y:.0f} '
             f'L{sub_x + sub_w} {t_y:.0f}" fill="none"/>')
    p.append(f'<rect class="fig-box" x="{sub_x}" y="{sub_y}" width="{sub_w}" '
             f'height="{sub_h}" rx="12"/>'
             f'<text class="fig-box-sub" x="{sub_x + sub_w / 2:.0f}" y="{sub_y + 27}" '
             f'text-anchor="middle">substation</text>')
    for x, name in zip(t_xs, names):
        lit = name == "A07"
        cls = "fig-lit-box c-orange" if lit else "fig-box"
        p.append(f'<circle class="{cls}" cx="{x}" cy="{t_y:.0f}" r="15"/>')
        p.append(f'<text class="fig-box-sub" x="{x}" y="{t_y + 34:.0f}" '
                 f'text-anchor="middle">{name}</text>')
    p.append(f'<text class="fig-box-sub" x="{t_xs[2]}" y="{t_y - 26:.0f}" '
             f'text-anchor="middle">never faulted</text>')

    # ---- the chart
    p.append(f'<line class="fig-track" x1="{x0}" y1="{py_bot}" x2="{x1}" y2="{py_bot}"/>')
    p.append(f'<line class="fig-track" x1="{x0}" y1="{to_y(100):.0f}" x2="{x1}" '
             f'y2="{to_y(100):.0f}"/>')
    p.append(f'<text class="fig-box-sub" x="{x0}" y="{py_top - 16}">production, as a percentage '
             f'of the string median</text>')
    p.append(f'<text class="fig-box-sub" x="{x0 - 8}" y="{to_y(100) + 4:.0f}" '
             f'text-anchor="end">100%</text>')
    for level, amp, phase in ((100.8, 0.45, 0.0), (100.2, 0.5, 1.9), (99.6, 0.4, 3.4),
                              (100.4, 0.45, 5.1)):
        p.append(f'<path class="fig-line-a" d="{trace(level, amp, phase)}" fill="none"/>')
    p.append(f'<path class="fig-line-b" d="{trace(96.2, 0.3, 2.2)}" fill="none"/>')
    p.append(f'<text class="fig-box-sub" x="{x0 + 4}" y="{to_y(96.2) - 12:.0f}">A07 · 4% down for '
             f'nine days · 120 MWh</text>')
    p.append(f'<text class="fig-box-sub" x="{x0}" y="{py_bot + 20}">nine days</text>')
    p.append(f'<text class="fig-box-sub" x="{x1}" y="{py_bot + 20}" text-anchor="end">today</text>')

    p.append('<text class="fig-sub" x="20" y="300">No alarm fired, because nothing was wrong '
             'with A07 on its own terms. The graph supplies the</text>')
    p.append('<text class="fig-sub" x="20" y="318">only thing that makes the loss visible: '
             'which turbines were standing in the same wind.</text>')
    p.append("</svg>")
    return "\n".join(p)


# --------------------------------------------------------------- vessel sisters
def vessel_sisters():
    """Three sisters, one drifting, and the event that explains it. THEMED.

    fig-draw on the three consumption traces: they are drifts over time, and
    watching one climb away from the other two is the finding.
    """
    rows = (108, 176, 244)
    lx, tx0, tx1 = 20, 210, 720
    RISE = 34.0                       # pixels of fouling drift across a full year
    # (name, note, line class, when it was last cleaned as a fraction of the axis,
    #  caption). Fouling climbs, a cleaning drops it back to a clean hull, and it
    #  climbs again: the vessel cleaned longest ago is the one riding highest now.
    vessels = (
        ("MV-Nord", "+6% per tonne-mile", "fig-line-b", 0.34, "cleaned 240 days ago"),
        ("MV-Sør", "the reference", "fig-line-a", 0.84, "cleaned 60 days ago"),
        ("MV-Vest", "+1%", "fig-line-a", 0.75, "cleaned 90 days ago"),
    )

    def drift(y, clean_at):
        """Fouling climbs, the cleaning resets it, then it climbs again."""
        pts = []
        steps = 48
        for i in range(steps + 1):
            t = i / steps
            grown = t if t < clean_at else t - clean_at
            pts.append(f"{tx0 + (tx1 - tx0) * t:.1f} {y - grown * RISE:.1f}")
        return "M" + " L".join(pts)

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 330" '
        'class="fig-vessel-sisters" role="img" aria-label="Three sister vessels on '
        'the same route. Each trace climbs as the hull fouls and drops back when the '
        'hull is cleaned. The two cleaned recently sit low; MV-Nord, cleaned 240 '
        'days ago, has been climbing ever since and now rides highest.">',
        '<text class="fig-title" x="20" y="24">A sister ship is a control group you already own</text>',
        '<text class="fig-sub" x="20" y="44">Same route, same season, same design. What differs '
        'is one event in each vessel’s history.</text>',
        '<text class="fig-box-sub" x="210" y="78">consumption per tonne-mile · the dot is a hull '
        'cleaning · the dashed line is a clean hull</text>',
    ]
    for (name, note, line_cls, clean_at, caption), y in zip(vessels, rows):
        base = y + 8
        p.append(f'<text class="fig-box-title" x="{lx}" y="{y - 2}">{name}</text>')
        p.append(f'<text class="fig-box-sub" x="{lx}" y="{y + 15}">{note}</text>')
        p.append(f'<line class="fig-track" x1="{tx0}" y1="{base}" x2="{tx1}" y2="{base}"/>')
        p.append(f'<path class="{line_cls} fig-draw" d="{drift(base, clean_at)}" fill="none"/>')
        cx = tx0 + (tx1 - tx0) * clean_at
        dot = "fig-dot-b" if line_cls == "fig-line-b" else "fig-dot-a"
        p.append(f'<circle class="{dot}" cx="{cx:.0f}" cy="{base}" r="5"/>')
        anchor = "end" if clean_at > 0.6 else "start"
        dx = -10 if anchor == "end" else 10
        p.append(f'<text class="fig-box-sub" x="{cx + dx:.0f}" y="{base + 18}" '
                 f'text-anchor="{anchor}">{caption}</text>')
    p.append(f'<text class="fig-box-sub" x="{tx0}" y="{rows[-1] + 48}">January</text>')
    p.append(f'<text class="fig-box-sub" x="{tx1}" y="{rows[-1] + 48}" text-anchor="end">now</text>')
    p.append('<text class="fig-sub" x="20" y="312">The gap is a number; the cleaning date is the '
             'reason. One is a time series, the other is an event.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------- blast radius cooling
def blast_radius_cooling():
    """One chiller down, walked outward hop by hop. THEMED, animated.

    The staggered reveal is the traversal itself, which is a thing that happens
    in order, so the motion is the content rather than decoration.
    """
    def arrow(x, y):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + 11} {y} L{x} {y + 5} z"/>'

    rows = (84, 148, 212)
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 336" '
        'class="fig-blast-radius" role="img" aria-label="A chiller at the left, '
        'feeding a loop, which feeds three cooling units, which serve three groups '
        'of racks. Two groups also have a second path from an unaffected loop; the '
        'third group of six racks does not, and is highlighted.">',
        '<text class="fig-title" x="20" y="24">One traversal answers what actually breaks</text>',
        '<text class="fig-sub" x="20" y="44">Walking downstream from the failure reaches every '
        'rack depending on it, and shows which have a way out.</text>',
    ]
    # level 0: the failure
    p.append('<rect class="fig-lit-box c-orange" x="20" y="126" width="132" height="56" rx="12"/>'
             '<text class="fig-lit-title" x="86" y="150" text-anchor="middle">CHILLER-02</text>'
             '<text class="fig-lit-sub" x="86" y="168" text-anchor="middle">tripped 14:20</text>')
    # level 1: the loop
    p.append('<g class="fig-seq fig-d1">'
             '<path class="fig-exit-path fig-flow" d="M152 154 L187 154" fill="none"/>'
             + arrow(187, 154) +
             '<rect class="fig-box" x="204" y="130" width="104" height="48" rx="12"/>'
             '<text class="fig-box-title" x="256" y="152" text-anchor="middle">LOOP-B</text>'
             '<text class="fig-box-sub" x="256" y="168" text-anchor="middle">chilled water</text>'
             '</g>')
    # level 2: the cooling units
    for i, y in enumerate(rows):
        p.append(f'<g class="fig-seq fig-d2">'
                 f'<path class="fig-exit-path fig-flow" d="M308 154 L347 {y + 22}" fill="none"/>'
                 + arrow(347, y + 22) +
                 f'<rect class="fig-box" x="364" y="{y}" width="96" height="44" rx="12"/>'
                 f'<text class="fig-box-title" x="412" y="{y + 27}" '
                 f'text-anchor="middle">CRAH-{i + 1}</text>'
                 f'</g>')
    # level 3: the racks
    racks = (("12 racks", "second path from LOOP-A", False),
             ("20 racks", "second path from LOOP-A", False),
             ("6 racks", "no second path", True))
    for (title, note, at_risk), y in zip(racks, rows):
        cls = "fig-lit-box c-orange" if at_risk else "fig-box"
        t_cls = "fig-lit-title" if at_risk else "fig-box-title"
        s_cls = "fig-lit-sub" if at_risk else "fig-box-sub"
        p.append(f'<g class="fig-seq fig-d3">'
                 f'<path class="fig-exit-path fig-flow" d="M460 {y + 22} L499 {y + 22}" fill="none"/>'
                 + arrow(499, y + 22) +
                 f'<rect class="{cls}" x="516" y="{y}" width="180" height="44" rx="12"/>'
                 f'<text class="{t_cls}" x="606" y="{y + 20}" text-anchor="middle">{title}</text>'
                 f'<text class="{s_cls}" x="606" y="{y + 35}" text-anchor="middle">{note}</text>'
                 f'</g>')
    p.append('<rect class="fig-exit-box" x="20" y="266" width="676" height="46" rx="14"/>'
             '<text class="fig-exit-title" x="40" y="288">38 racks reached · 6 with no second '
             'path · 2 of those already ran hot in July</text>'
             '<text class="fig-exit-sub" x="40" y="304">the same walk, costed differently, is '
             'where the stranded capacity is</text>')
    p.append("</svg>")
    return "\n".join(p)


# --------------------------------------------------------------- readiness gate
def readiness_gate():
    """Fourteen airframes, three down, two of them for the same reason. THEMED.

    The convergence is the whole figure: two edges arriving at one part node is
    what turns a status report into a decision, and it is a fact about the graph
    rather than about any single record.
    """
    def arrow(x, y):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + 11} {y} L{x} {y + 5} z"/>'

    cw, chh, gap = 30, 24, 6
    gx, g_rows = 196, (86, 116)

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 356" '
        'class="fig-readiness-gate" role="img" aria-label="A squadron of fourteen '
        'airframes, eleven available and three gated. Below, the three gated tails '
        'connect to what is holding them: two of them to the same hydraulic part '
        'with a nine day lead time, and one to a scheduled inspection.">',
        '<text class="fig-title" x="20" y="24">Readiness is a rollup, and the answer is which '
        'nodes gate it</text>',
        '<text class="fig-sub" x="20" y="44">Fourteen airframes is a number anyone can produce. '
        'Which three, and why, is a traversal.</text>',
    ]
    # ---- the squadron and its fleet
    p.append('<rect class="fig-box" x="20" y="82" width="130" height="52" rx="12"/>'
             '<text class="fig-box-title" x="85" y="104" text-anchor="middle">SQN-4</text>'
             '<text class="fig-box-sub" x="85" y="120" text-anchor="middle">14 airframes</text>')
    p.append(f'<path class="fig-exit-path fig-flow" d="M150 108 L177 108" fill="none"/>')
    p.append(arrow(177, 108))
    down = {(0, 6), (1, 6), (1, 5)}
    for r, y in enumerate(g_rows):
        for c in range(7):
            x = gx + c * (cw + gap)
            cls = "fig-lit-box c-orange" if (r, c) in down else "fig-box"
            p.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{cw}" height="{chh}" rx="7"/>')
    p.append('<text class="fig-box-title" x="510" y="104">11 available</text>')
    p.append('<text class="fig-box-sub" x="510" y="122">3 gated, and not by three '
             'different things</text>')

    # ---- why the three are down
    p.append('<text class="fig-box-title" x="20" y="176">What is holding the other three</text>')
    tails = (("TAIL-07", 190), ("TAIL-11", 234), ("TAIL-03", 278))
    for name, y in tails:
        p.append(f'<rect class="fig-lit-box c-orange" x="190" y="{y}" width="110" height="36" '
                 f'rx="10"/>'
                 f'<text class="fig-lit-sub" x="245" y="{y + 22}" text-anchor="middle">{name}</text>')
    for y in (208, 252):
        p.append(f'<path class="fig-exit-path fig-flow" d="M300 {y} L419 214" fill="none"/>')
    p.append(arrow(419, 214))
    p.append('<path class="fig-exit-path fig-flow" d="M300 296 L419 298" fill="none"/>')
    p.append(arrow(419, 298))
    p.append('<rect class="fig-box" x="436" y="190" width="270" height="48" rx="12"/>'
             '<text class="fig-box-title" x="571" y="211" text-anchor="middle">PN-4471 hydraulic '
             'pack</text>'
             '<text class="fig-box-sub" x="571" y="228" text-anchor="middle">9-day lead, none on '
             'hand</text>')
    p.append('<rect class="fig-box" x="436" y="274" width="270" height="48" rx="12"/>'
             '<text class="fig-box-title" x="571" y="295" text-anchor="middle">50-hour '
             'inspection</text>'
             '<text class="fig-box-sub" x="571" y="312" text-anchor="middle">could be pulled '
             'forward</text>')
    p.append('<text class="fig-sub" x="20" y="346">One requisition returns two airframes. That is '
             'a fact about the graph, not about any one record.</text>')
    p.append("</svg>")
    return "\n".join(p)


# -------------------------------------------------------- issuer neighbourhood
def issuer_neighbourhood():
    """One filing, and everything it reaches through the graph. THEMED.

    The sparkline in each node is the point that a reader might otherwise miss:
    every node the event reaches carries its own series, so one arrival turns
    into five things worth reading.
    """
    def arrow(x, y, dx=11):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + dx} {y} L{x} {y + 5} z"/>'

    def spark(x, y, seed, w=46, h=12):
        pts = []
        for i in range(9):
            t = i / 8
            v = math.sin(t * 5.4 + seed) * 0.5 + math.sin(t * 2.1 + seed * 1.7) * 0.5
            pts.append(f"{x + w * t:.1f} {y - v * h / 2:.1f}")
        return f'<path class="fig-line-a" d="M{" L".join(pts)}" fill="none"/>'

    nodes = (
        (40, 96, "Supplier B", "held in the portfolio", 0.4),
        (40, 216, "Supplier C", "held in the portfolio", 2.3),
        (550, 96, "Fund D", "holds both of them", 4.1),
        (550, 216, "Peer E", "same end market", 5.6),
    )
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 330" '
        'class="fig-issuer-neighbourhood" role="img" aria-label="A results release '
        'arrives as an event on Issuer A. From there the graph reaches two suppliers '
        'held in the portfolio, a fund holding both, and a peer in the same end '
        'market, each of which carries its own price and fundamentals series.">',
        '<text class="fig-title" x="20" y="24">One filing, and everything it is allowed to '
        'move</text>',
        '<text class="fig-sub" x="20" y="44">The event lands on one issuer. What it means for '
        'the book is a question about relationships.</text>',
        '<rect class="fig-lit-box c-orange" x="310" y="76" width="150" height="30" rx="10"/>'
        '<text class="fig-lit-sub" x="385" y="96" text-anchor="middle">results release, '
        '06:59</text>',
        '<path class="fig-exit-path fig-flow" d="M385 106 L385 129" fill="none"/>',
        '<path class="fig-centre" d="M380 129 L385 140 L390 129 z"/>',
        '<rect class="fig-lit-box c-blue" x="300" y="140" width="170" height="56" rx="12"/>'
        '<text class="fig-lit-title" x="385" y="164" text-anchor="middle">Issuer A</text>'
        '<text class="fig-lit-sub" x="385" y="182" text-anchor="middle">the one that just '
        'reported</text>',
    ]
    # Labels ride the midpoint of their own edge: parked beside the nodes they were
    # hidden behind them, since the gap either side of the issuer is only 80px.
    edges = ((300, 168, 231, 120, "SUPPLIES"),
             (300, 168, 231, 240, "SUPPLIES"),
             (470, 168, 539, 120, "OWNED_BY"),
             (470, 168, 539, 240, "COMPETES_WITH"))
    for x1, y1, x2, y2, label in edges:
        p.append(f'<path class="fig-exit-path fig-flow" d="M{x1} {y1} L{x2} {y2}" fill="none"/>')
        p.append(arrow(x2, y2, 11 if x2 > x1 else -11))
        p.append(f'<text class="fig-box-sub" x="{(x1 + x2) / 2:.0f}" y="{(y1 + y2) / 2 - 7:.0f}" '
                 f'text-anchor="middle">{label}</text>')
    for x, y, title, sub, seed in nodes:
        p.append(f'<rect class="fig-box" x="{x}" y="{y}" width="{180}" height="48" rx="12"/>'
                 f'<text class="fig-box-title" x="{x + 14}" y="{y + 21}">{title}</text>'
                 f'<text class="fig-box-sub" x="{x + 14}" y="{y + 37}">{sub}</text>')
        p.append(spark(x + 122, y + 28, seed))
    p.append('<text class="fig-sub" x="20" y="298">Every node the walk reaches carries its own '
             'series, which is why one arrival at 06:59 becomes</text>')
    p.append('<text class="fig-sub" x="20" y="316">five things worth reading by 07:04 rather than '
             'one headline worth repeating.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------------ ward devices
def ward_devices():
    """The ward outward to its devices, and the boundary that is deliberately absent.

    THEMED. The unconnected patient node is the honest half, and its wording was
    rewritten once: "traversal is gated on the starting node" means nothing to a
    reader who does not already know the rule, so the figure says what the rule
    does instead of naming it.
    """
    def arrow(x, y):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + 11} {y} L{x} {y + 5} z"/>'

    rows = ((96, "Infusion pumps ×12", "run hours", "12 calibrations due"),
            (160, "Ventilator V-207", "self-test result", "3 warnings this week"),
            (224, "MRI suite", "helium boil-off", "boil-off drift opened"))
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 384" '
        'class="fig-ward-devices" role="img" aria-label="A ward node connected to '
        'three device groups, each carrying a time series and an event. A patient '
        'records node sits below, with no line connecting it to any of them, '
        'deliberately.">',
        '<text class="fig-title" x="20" y="24">The same walk as the compressor, on a different '
        'kind of plant</text>',
        '<text class="fig-sub" x="20" y="44">Resolve the ward, step out to what is deployed in '
        'it, read the series and the events on each.</text>',
        '<rect class="fig-lit-box c-blue" x="20" y="160" width="140" height="52" rx="12"/>'
        '<text class="fig-lit-title" x="90" y="184" text-anchor="middle">WARD-3B</text>'
        '<text class="fig-lit-sub" x="90" y="201" text-anchor="middle">where the question '
        'starts</text>',
    ]
    for y, name, series, event in rows:
        mid = y + 24
        p.append(f'<path class="fig-exit-path fig-flow" d="M160 186 L189 {mid}" fill="none"/>')
        p.append(arrow(189, mid))
        p.append(f'<rect class="fig-box" x="206" y="{y}" width="186" height="48" rx="12"/>'
                 f'<text class="fig-box-title" x="299" y="{mid + 5}" '
                 f'text-anchor="middle">{name}</text>')
        p.append(f'<line class="fig-track" x1="392" y1="{mid}" x2="422" y2="{mid}"/>')
        p.append(f'<rect class="fig-box" x="422" y="{mid - 17}" width="140" height="34" rx="9"/>'
                 f'<text class="fig-box-sub" x="492" y="{mid + 5}" '
                 f'text-anchor="middle">{series}</text>')
        p.append(f'<line class="fig-track" x1="562" y1="{mid}" x2="586" y2="{mid}"/>')
        p.append(f'<rect class="fig-box" x="586" y="{mid - 17}" width="154" height="34" rx="9"/>'
                 f'<text class="fig-box-sub" x="663" y="{mid + 5}" '
                 f'text-anchor="middle">{event}</text>')
    p.append('<text class="fig-box-sub" x="492" y="82" text-anchor="middle">time series</text>')
    p.append('<text class="fig-box-sub" x="663" y="82" text-anchor="middle">events</text>')
    p.append('<rect class="fig-box" x="20" y="284" width="150" height="40" rx="12"/>'
             '<text class="fig-box-sub" x="95" y="308" text-anchor="middle">Patient records</text>')
    p.append('<text class="fig-box-sub" x="186" y="303">Notice there is no line from here to '
             'anything above.</text>')
    p.append('<text class="fig-box-sub" x="186" y="319">That is deliberate, and it is the '
             'point.</text>')
    p.append('<text class="fig-sub" x="20" y="352">A question can reach whatever is linked to '
             'where it started. So the dependable way</text>')
    p.append('<text class="fig-sub" x="20" y="370">to keep two things apart is to leave the link '
             'out, rather than to rely on a permission at the far end.</text>')
    p.append("</svg>")
    return "\n".join(p)


# --------------------------------------------------------------- agent anatomy
def agent_anatomy():
    """The six parts, and the self-loop that makes them an agent. THEMED, static.

    Static by the house rule: a reader compares the parts, so all six must be
    visible at once. The only mark that moves the eye is the loop glyph, reused
    unchanged from revolution_contrast, because it is the one thing here that
    means "and then it goes round again".
    """
    def loop_glyph(cx, cy):
        """The house self-loop, perched on a node's top-right corner."""
        r = 9
        ccx, ccy = cx + 5, cy - 5
        a0, a1 = math.radians(165), math.radians(105)
        sx, sy = ccx + r * math.cos(a0), ccy + r * math.sin(a0)
        ex, ey = ccx + r * math.cos(a1), ccy + r * math.sin(a1)
        tx, ty = -math.sin(a1), math.cos(a1)
        nx, ny = math.cos(a1), math.sin(a1)
        tip = (ex + 5.5 * tx, ey + 5.5 * ty)
        b1 = (ex - 2 * tx + 3.6 * nx, ey - 2 * ty + 3.6 * ny)
        b2 = (ex - 2 * tx - 3.6 * nx, ey - 2 * ty - 3.6 * ny)
        return (
            f'<path class="fig-loop-arc" d="M{sx:.1f} {sy:.1f} A {r} {r} 0 1 1 '
            f'{ex:.1f} {ey:.1f}"/>'
            f'<path class="fig-loop-head" d="M{tip[0]:.1f} {tip[1]:.1f} L{b1[0]:.1f} '
            f'{b1[1]:.1f} L{b2[0]:.1f} {b2[1]:.1f} z"/>'
        )

    bw, bh = 210, 50
    rows = (86, 148, 210)
    cx, cy, cw, chh = 292, 130, 176, 76        # the agent itself

    left = (("A goal, and its sub-goals", "not an instruction to follow"),
            ("Plain language in and out", "no query syntax to learn"),
            ("Memory", "what it did, and how that went"))
    right = (("Tools", "the graph, series, events, files"),
             ("A planner", "picks the next step, not the plan"),
             ("Judgement", "was that step any good?"))

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 330" '
        'class="fig-agent-anatomy" role="img" aria-label="An agent in the middle, '
        'with six parts around it: a goal and its sub-goals, a plain-language '
        'interface and memory on the left; tools, a planner and judgement on the '
        'right. A loop mark on the agent shows that it repeats.">',
        '<text class="fig-title" x="20" y="24">Six parts, and the loop that makes them an '
        'agent</text>',
        '<text class="fig-sub" x="20" y="44">Remove any one and it stops being an agent. Remove '
        'the loop and it is a very good search box.</text>',
    ]
    for (title, sub), y in zip(left, rows):
        p.append(f'<rect class="fig-box" x="20" y="{y}" width="{bw}" height="{bh}" rx="12"/>'
                 f'<text class="fig-box-title" x="34" y="{y + 22}">{title}</text>'
                 f'<text class="fig-box-sub" x="34" y="{y + 39}">{sub}</text>')
        p.append(f'<path class="fig-exit-path" d="M{20 + bw} {y + bh / 2:.0f} L{cx} '
                 f'{cy + chh / 2:.0f}" fill="none"/>')
    for (title, sub), y in zip(right, rows):
        x = 760 - 20 - bw
        p.append(f'<rect class="fig-box" x="{x}" y="{y}" width="{bw}" height="{bh}" rx="12"/>'
                 f'<text class="fig-box-title" x="{x + 14}" y="{y + 22}">{title}</text>'
                 f'<text class="fig-box-sub" x="{x + 14}" y="{y + 39}">{sub}</text>')
        p.append(f'<path class="fig-exit-path" d="M{cx + cw} {cy + chh / 2:.0f} L{x} '
                 f'{y + bh / 2:.0f}" fill="none"/>')
    p.append(f'<rect class="fig-lit-box c-blue" x="{cx}" y="{cy}" width="{cw}" height="{chh}" '
             f'rx="16"/>'
             f'<text class="fig-lit-title" x="{cx + cw / 2:.0f}" y="{cy + 34}" '
             f'text-anchor="middle">The agent</text>'
             f'<text class="fig-lit-sub" x="{cx + cw / 2:.0f}" y="{cy + 52}" '
             f'text-anchor="middle">decides what to do next</text>')
    p.append(loop_glyph(cx + cw, cy))
    p.append('<text class="fig-sub" x="20" y="290">A chatbot has the language interface and '
             'nothing else. What an agent adds is the right-hand</text>')
    p.append('<text class="fig-sub" x="20" y="308">column: it can act, decide the next move, and '
             'tell whether the last one helped.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------- feature flywheel
def feature_flywheel():
    """A feature discovered, tested, kept, and then available to the next lap.

    THEMED, animated: this is a cycle in time, and the return arc is the whole
    argument, so the marching dashes are the content rather than decoration.
    """
    def arrow(x, y):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + 11} {y} L{x} {y + 5} z"/>'

    by, bh = 96, 68
    mid = by + bh / 2
    boxes = (
        (20, 172, "The series you have", "and every feature kept before"),
        (232, 168, "A candidate feature", "proposed and computed"),
        (440, 160, "Does it predict?", "tested against the events"),
        (640, 100, "Kept", "as a new series"),
    )
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 320" '
        'class="fig-feature-flywheel" role="img" aria-label="Four stages in a loop: '
        'the series you have, a candidate feature, a test against the events, and '
        'the feature kept as a new series. An arc returns from the last stage to the '
        'first, because a kept feature becomes an input for the next lap.">',
        '<text class="fig-title" x="20" y="24">Every kept feature makes the next one easier to '
        'find</text>',
        '<text class="fig-sub" x="20" y="44">A feature is a number that means something. Finding '
        'one used to be a specialist project.</text>',
    ]
    for i, (x, w, title, sub) in enumerate(boxes):
        if i:
            prev_x, prev_w = boxes[i - 1][0], boxes[i - 1][1]
            p.append(f'<path class="fig-exit-path fig-flow" d="M{prev_x + prev_w} {mid:.0f} '
                     f'L{x - 11} {mid:.0f}" fill="none"/>')
            p.append(arrow(x - 11, mid))
        cls = "fig-lit-box c-blue" if i == 3 else "fig-box"
        t_cls = "fig-lit-title" if i == 3 else "fig-box-title"
        s_cls = "fig-lit-sub" if i == 3 else "fig-box-sub"
        p.append(f'<rect class="{cls}" x="{x}" y="{by}" width="{w}" height="{bh}" rx="12"/>'
                 f'<text class="{t_cls}" x="{x + w / 2:.0f}" y="{by + 28}" '
                 f'text-anchor="middle">{title}</text>'
                 f'<text class="{s_cls}" x="{x + w / 2:.0f}" y="{by + 46}" '
                 f'text-anchor="middle">{sub}</text>')
    p.append(f'<path class="fig-exit-path fig-flow" d="M690 {by + bh} L690 228 L106 228 '
             f'L106 {by + bh + 11}" fill="none"/>')
    p.append(f'<path class="fig-centre" d="M101 {by + bh + 11} L106 {by + bh} '
             f'L111 {by + bh + 11} z"/>')
    p.append('<text class="fig-box-sub" x="390" y="248" text-anchor="middle">and the next lap '
             'starts with one more thing worth looking at</text>')
    p.append('<text class="fig-sub" x="20" y="288">The test is the part that keeps it honest: a '
             'feature is kept because it predicted something,</text>')
    p.append('<text class="fig-sub" x="20" y="306">not because it looked clever. The events are '
             'what it is tested against.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------- synthetic and measured
def synthetic_and_measured():
    """Three real failures against as many generated ones as you need. THEMED.

    Static: the two panels are a comparison, and the whole point is how sparse
    the left one is next to the right.
    """
    y = 152
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 330" '
        'class="fig-synthetic-measured" role="img" aria-label="Two timelines. The '
        'measured one holds three examples of a failure in ten years. The synthetic '
        'one holds hundreds, generated from a model of how the failure develops. '
        'Below, the two rules: train on both, test only on measured, and keep them '
        'in separate data sets.">',
        '<text class="fig-title" x="20" y="24">The failures you most want to predict are the ones '
        'you have barely seen</text>',
        '<text class="fig-sub" x="20" y="44">Nothing learns a pattern from three examples. '
        'Generating more is how that stops being a dead end.</text>',
        '<text class="fig-box-title" x="20" y="96">Measured</text>',
        '<text class="fig-box-sub" x="20" y="114">ten years of real history</text>',
        '<text class="fig-box-title" x="400" y="96">Synthetic</text>',
        '<text class="fig-box-sub" x="400" y="114">generated from how the failure develops</text>',
        f'<line class="fig-track" x1="20" y1="{y}" x2="350" y2="{y}"/>',
        f'<line class="fig-track" x1="400" y1="{y}" x2="740" y2="{y}"/>',
    ]
    for x in (78, 191, 296):
        p.append(f'<circle class="fig-dot-b" cx="{x}" cy="{y}" r="6"/>')
    # Deterministic even spread with a small jitter, on two rows. A modulo stride
    # was tried first and rendered as visible clumps, which read as a pattern in
    # the data rather than as density.
    n = 56
    for i in range(n):
        x = 406 + 330 * (i / (n - 1)) + 3 * math.sin(i * 2.4)
        row = y - 9 if i % 2 else y + 9
        p.append(f'<circle class="fig-dot-a" cx="{x:.1f}" cy="{row}" r="4"/>')
    p.append(f'<text class="fig-box-sub" x="20" y="{y + 40}">three examples, and two of them '
             f'were logged differently</text>')
    p.append(f'<text class="fig-box-sub" x="400" y="{y + 40}">as many as the training needs, '
             f'with the conditions varied</text>')
    p.append('<rect class="fig-exit-box" x="20" y="228" width="720" height="72" rx="14"/>'
             '<text class="fig-exit-title" x="40" y="254">Train on both. Test only on what was '
             'actually measured.</text>'
             '<text class="fig-exit-sub" x="40" y="274">Keep the generated data in its own data '
             'set, labelled, so the two can never be confused later,</text>'
             '<text class="fig-exit-sub" x="40" y="290">by a person, by a report, or by the next '
             'model that comes looking for training data.</text>')
    p.append("</svg>")
    return "\n".join(p)


# -------------------------------------------------------------------- dirty data
def dirty_data():
    """The five defects that actually turn up, and the rule for handling them.

    THEMED, static: five small panels a reader scans side by side. Orange is
    always the defect, blue is the signal behaving, so the eye learns the code
    once and reads the rest of the row without the captions.
    """
    pw, ph, gap = 140, 60, 8
    top, ctr = 104, 134
    xs = [20 + i * (pw + gap) for i in range(5)]

    def wave(x0, x1, phase=0.0, amp=11.0, step=4, shift=0.0, slope=0.0):
        pts = []
        x = x0
        while x <= x1:
            t = (x - x0) / pw
            y = ctr - amp * math.sin(2 * math.pi * t * 1.6 + phase) + shift + slope * t
            pts.append(f"{x:.1f} {y:.1f}")
            x += step
        return "M" + " L".join(pts)

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 306" '
        'class="fig-dirty-data" role="img" aria-label="Five small charts showing the '
        'defects that turn up in industrial measurements: a frozen sensor, a spike, '
        'a slow drift, a gap, and a unit change that looks like a step. Below them, '
        'the rule: raw stays raw, a correction is a new series, and the correction '
        'itself is an event.">',
        '<text class="fig-title" x="20" y="24">What dirty data actually looks like</text>',
        '<text class="fig-sub" x="20" y="44">None of these announce themselves. Four of the five '
        'look like perfectly ordinary readings.</text>',
    ]
    titles = ("Frozen", "Spike", "Drift", "Gap", "Wrong unit")
    caps = (("the sensor stopped,", "the plant did not"),
            ("one impossible value,", "and every average moves"),
            ("slowly wrong,", "and nobody notices"),
            ("missing hours,", "quietly filled in later"),
            ("bar became psi:", "a step, not a fault"))
    for x, title, cap in zip(xs, titles, caps):
        p.append(f'<rect class="fig-box" x="{x}" y="{top}" width="{pw}" height="{ph}" rx="10"/>')
        p.append(f'<text class="fig-box-title" x="{x + pw / 2:.0f}" y="{top - 12}" '
                 f'text-anchor="middle">{title}</text>')
        p.append(f'<text class="fig-box-sub" x="{x + pw / 2:.0f}" y="{top + ph + 20}" '
                 f'text-anchor="middle">{cap[0]}</text>')
        p.append(f'<text class="fig-box-sub" x="{x + pw / 2:.0f}" y="{top + ph + 35}" '
                 f'text-anchor="middle">{cap[1]}</text>')

    # 1 frozen: fine, then flat while the world carries on
    p.append(f'<path class="fig-line-a" d="{wave(xs[0] + 8, xs[0] + 58)}" fill="none"/>')
    frozen_y = ctr - 11 * math.sin(2 * math.pi * (50 / pw) * 1.6)
    p.append(f'<path class="fig-line-b" d="M{xs[0] + 58} {frozen_y:.1f} L{xs[0] + pw - 8} '
             f'{frozen_y:.1f}" fill="none"/>')
    # 2 spike
    p.append(f'<path class="fig-line-a" d="{wave(xs[1] + 8, xs[1] + pw - 8, phase=1.1)}" '
             f'fill="none"/>')
    sx = xs[1] + 74
    sy = ctr - 11 * math.sin(2 * math.pi * (66 / pw) * 1.6 + 1.1)
    p.append(f'<path class="fig-line-b" d="M{sx - 6} {sy:.1f} L{sx} {top + 6} L{sx + 6} '
             f'{sy:.1f}" fill="none"/>')
    # 3 drift: the truth in ghost, the drifting reading in orange
    p.append(f'<path class="fig-line-a fig-line--ghost" d="{wave(xs[2] + 8, xs[2] + pw - 8, phase=2.2)}" '
             f'fill="none"/>')
    p.append(f'<path class="fig-line-b" d="{wave(xs[2] + 8, xs[2] + pw - 8, phase=2.2, slope=-18)}" '
             f'fill="none"/>')
    # 4 gap
    p.append(f'<path class="fig-line-a" d="{wave(xs[3] + 8, xs[3] + 52, phase=0.6)}" fill="none"/>')
    p.append(f'<path class="fig-line-a" d="{wave(xs[3] + 92, xs[3] + pw - 8, phase=0.6)}" '
             f'fill="none"/>')
    p.append(f'<line class="fig-track" x1="{xs[3] + 52}" y1="{ctr}" x2="{xs[3] + 92}" '
             f'y2="{ctr}"/>')
    # 5 unit change: the same signal, suddenly on another scale
    p.append(f'<path class="fig-line-a" d="{wave(xs[4] + 8, xs[4] + 66, phase=3.0, amp=7)}" '
             f'fill="none"/>')
    shifted = wave(xs[4] + 66, xs[4] + pw - 8, phase=3.0, amp=7, shift=-20)
    p.append(f'<path class="fig-line-b" d="{shifted}" fill="none"/>')

    p.append('<rect class="fig-exit-box" x="20" y="228" width="720" height="62" rx="14"/>'
             '<text class="fig-exit-title" x="40" y="252">Raw stays raw. A correction is a new '
             'series beside it, never an edit to the original.</text>'
             '<text class="fig-exit-sub" x="40" y="274">And the correction is itself an event, so '
             'anyone can see what was changed, when, and on what grounds.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ----------------------------------------------------------- rules vs learning
def rules_vs_learning():
    """Writing the rule against learning it from examples. THEMED, static."""
    def arrow(x, y):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + 11} {y} L{x} {y + 5} z"/>'

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 300" '
        'class="fig-rules-learning" role="img" aria-label="On the left, a person '
        'writes a threshold rule which then makes decisions. On the right, examples '
        'of what happened are used to train a model, which works the rule out and '
        'then makes decisions.">',
        '<text class="fig-title" x="20" y="24">Two ways to get a decision out of a '
        'measurement</text>',
        '<text class="fig-sub" x="20" y="44">Both end in the same place. They differ entirely in '
        'what you have to know beforehand.</text>',
        '<text class="fig-box-title" x="20" y="82">You write the rule</text>',
        '<text class="fig-box-title" x="400" y="82">The rule is learned from examples</text>',
    ]
    # left lane
    p.append('<rect class="fig-box" x="20" y="100" width="150" height="56" rx="12"/>'
             '<text class="fig-box-title" x="95" y="124" text-anchor="middle">An expert</text>'
             '<text class="fig-box-sub" x="95" y="141" text-anchor="middle">who knows the '
             'threshold</text>')
    p.append('<path class="fig-exit-path fig-flow" d="M170 128 L199 128" fill="none"/>')
    p.append(arrow(199, 128))
    p.append('<rect class="fig-box" x="216" y="100" width="144" height="56" rx="12"/>'
             '<text class="fig-box-sub" x="288" y="124" text-anchor="middle">if vibration '
             '&gt; 4.5</text>'
             '<text class="fig-box-sub" x="288" y="141" text-anchor="middle">then raise an '
             'alarm</text>')
    p.append('<text class="fig-box-sub" x="20" y="186">Readable by anyone, and wrong the moment '
             'the</text>')
    p.append('<text class="fig-box-sub" x="20" y="202">machine, the duty or the season '
             'changes.</text>')
    # right lane
    p.append('<rect class="fig-box" x="400" y="100" width="164" height="56" rx="12"/>'
             '<text class="fig-box-title" x="482" y="124" text-anchor="middle">What happened '
             'before</text>'
             '<text class="fig-box-sub" x="482" y="141" text-anchor="middle">readings, and how '
             'each ended</text>')
    p.append('<path class="fig-exit-path fig-flow" d="M564 128 L593 128" fill="none"/>')
    p.append(arrow(593, 128))
    p.append('<rect class="fig-lit-box c-blue" x="610" y="100" width="130" height="56" rx="12"/>'
             '<text class="fig-lit-title" x="675" y="124" text-anchor="middle">A model</text>'
             '<text class="fig-lit-sub" x="675" y="141" text-anchor="middle">the rule, worked '
             'out</text>')
    p.append('<text class="fig-box-sub" x="400" y="186">Nobody had to know the threshold, and it '
             'can be</text>')
    p.append('<text class="fig-box-sub" x="400" y="202">relearned when the plant changes. Harder '
             'to read.</text>')
    p.append('<rect class="fig-exit-box" x="20" y="226" width="720" height="56" rx="14"/>'
             '<text class="fig-exit-title" x="40" y="250">Machine learning is the right-hand '
             'lane, and that is the whole of it.</text>'
             '<text class="fig-exit-sub" x="40" y="270">Everything below is a different answer to '
             'one question: what shape is the rule allowed to be?</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------- ml progression
def ml_progression():
    """Linear regression to logistic regression to a support vector machine.

    THEMED, static. One chart, three panels, because the point is that they are
    the same idea answering harder questions: fit a line, bend it into an S so it
    can express a probability, then use it as a boundary with the widest gap it
    can find.

    History, so nobody repeats it: this was rebuilt once as a single animated
    scatter that refitted itself three times, and it was worse. The three
    questions need three different pictures (a value read off a line, a
    probability between no and yes, a boundary with a margin), and forcing them
    onto one set of axes made all three harder to read. It was reverted.

    The two ringed points in panel three sit exactly on the margins, because a
    support vector that is not touching the margin argues against its own caption.
    """
    px, pw = (20, 270, 520), 220
    ct, cb = 116, 252                      # chart top and bottom
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 344" '
        'class="fig-ml-progression" role="img" aria-label="Three panels. First, '
        'linear regression fits a straight line through scattered points to predict '
        'a number. Second, logistic regression bends that line into an S-curve '
        'between no and yes, to predict a probability. Third, a support vector '
        'machine separates two groups of points with the line that leaves the '
        'widest margin, resting on a few points at the edges.">',
        '<text class="fig-title" x="20" y="24">The same idea, answering three harder '
        'questions</text>',
        '<text class="fig-sub" x="20" y="44">Fit a line. Bend it into a probability. Then use it '
        'as a boundary, and make the gap as wide as possible.</text>',
    ]
    heads = (("Linear regression", "how much?", "days until service"),
             ("Logistic regression", "how likely?", "chance it fails this month"),
             ("Support vector machine", "which side?", "healthy or failing"))
    for x, (title, q, sub) in zip(px, heads):
        p.append(f'<text class="fig-box-title" x="{x}" y="{78}">{title}</text>')
        p.append(f'<text class="fig-box-sub" x="{x}" y="{96}">{q} · {sub}</text>')
        p.append(f'<line class="fig-track" x1="{x}" y1="{cb}" x2="{x + pw}" y2="{cb}"/>')
    for x in (px[0] + pw + 8, px[1] + pw + 8):
        p.append(f'<path class="fig-centre" d="M{x} {178} L{x + 12} {184} L{x} {190} z"/>')

    # ---- 1: a straight line through a rising scatter
    x0 = px[0]
    for i in range(9):
        dx = 16 + i * 23
        wob = (-6, 5, -3, 7, -5, 4, -7, 3, -2)[i]
        p.append(f'<circle class="fig-dot-a" cx="{x0 + dx}" cy="{cb - 14 - i * 13 + wob}" r="4"/>')
    p.append(f'<path class="fig-line-a" d="M{x0 + 14} {cb - 16} L{x0 + 200} {cb - 118}" '
             f'fill="none"/>')
    p.append(f'<text class="fig-box-sub" x="{x0}" y="{cb + 22}">the line is the prediction: read '
             f'it off</text>')
    p.append(f'<text class="fig-box-sub" x="{x0}" y="{cb + 38}">anywhere along the bottom '
             f'axis</text>')

    # ---- 2: the same line bent into an S between no and yes
    x1 = px[1]
    p.append(f'<text class="fig-box-sub" x="{x1 - 4}" y="{ct + 8}" text-anchor="end">yes</text>')
    p.append(f'<text class="fig-box-sub" x="{x1 - 4}" y="{cb + 4}" text-anchor="end">no</text>')
    pts = []
    for i in range(41):
        t = i / 40
        y = cb - (cb - ct - 6) / (1 + math.exp(-(t - 0.5) * 11))
        pts.append(f"{x1 + 10 + t * 200:.1f} {y:.1f}")
    p.append(f'<path class="fig-line-b" d="M{" L".join(pts)}" fill="none"/>')
    for dx in (18, 40, 62, 88):
        p.append(f'<circle class="fig-dot-a" cx="{x1 + dx}" cy="{cb - 4}" r="4"/>')
    for dx in (128, 152, 176, 200):
        p.append(f'<circle class="fig-dot-b" cx="{x1 + dx}" cy="{ct + 2}" r="4"/>')
    mid_y = (ct + cb) / 2
    p.append(f'<line class="fig-track" x1="{x1}" y1="{mid_y:.0f}" x2="{x1 + pw}" '
             f'y2="{mid_y:.0f}"/>')
    p.append(f'<text class="fig-box-sub" x="{x1}" y="{cb + 22}">above the middle line, act on '
             f'it;</text>')
    p.append(f'<text class="fig-box-sub" x="{x1}" y="{cb + 38}">below it, keep watching</text>')

    # ---- 3: two groups, the widest gap, and the points holding it up
    #
    # The boundary bends. A support vector machine is not limited to a straight
    # line, and drawing one straight was the single thing wrong with an earlier
    # version of this panel: it made the third method look like the second.
    x2 = px[2]

    def bound(dx):
        """Boundary in panel coordinates: a shallow diagonal with real waves in it.

        A support vector machine with a kernel does not draw a line, it draws
        whatever shape separates the groups with the most room. Earlier versions
        of this panel drew a straight line and then a barely perceptible bow, and
        both made the third method look like the second.
        """
        return 68 + 0.12 * (dx - 8) + 26 * math.sin(3 * math.pi * (dx - 8) / 200)

    def bound_path(off=0.0, step=4):
        pts = [f"{x2 + dx} {ct + bound(dx) + off:.1f}" for dx in range(8, 209, step)]
        return "M" + " L".join(pts)

    # Points are derived from the boundary rather than hand-placed, so the two
    # bands wave with it and nothing can end up on the wrong side of the curve.
    blues = [(dx, bound(dx) + 16 + extra)
             for dx, extra in ((12, 26), (55, 10), (96, 0), (124, 22), (200, 8))]
    oranges = [(dx, bound(dx) - 16 - extra)
               for dx, extra in ((28, 8), (68, 24), (108, 22), (145, 0), (182, 12), (208, 22))]
    supports = ((96, bound(96) + 16), (145, bound(145) - 16))
    p.append(f'<path class="fig-line-a" d="{bound_path()}" fill="none"/>')
    for off in (-16, 16):
        p.append(f'<path class="fig-track" d="{bound_path(off)}" fill="none"/>')
    # rings before the dots: fig-box fills with the surface colour and would
    # otherwise hide the very points it is meant to single out
    for dx, dy in supports:
        p.append(f'<circle class="fig-box" cx="{x2 + dx}" cy="{ct + dy:.1f}" r="9"/>')
    for dx, dy in blues:
        p.append(f'<circle class="fig-dot-a" cx="{x2 + dx}" cy="{ct + dy:.1f}" r="4"/>')
    for dx, dy in oranges:
        p.append(f'<circle class="fig-dot-b" cx="{x2 + dx}" cy="{ct + dy:.1f}" r="4"/>')
    p.append(f'<text class="fig-box-sub" x="{x2}" y="{cb + 22}">the ringed points are the only '
             f'ones that</text>')
    p.append(f'<text class="fig-box-sub" x="{x2}" y="{cb + 38}">matter: move them and the '
             f'boundary moves</text>')

    p.append('<text class="fig-sub" x="20" y="312">Start at the left. Move right only when the '
             'question demands it, because everything you gain</text>')
    p.append('<text class="fig-sub" x="20" y="330">going right is paid for in how easily you can '
             'explain the answer afterwards.</text>')
    p.append("</svg>")
    return "\n".join(p)


# --------------------------------------------------------------- tree ensembles
def tree_ensembles():
    """One decision tree, a random forest, then gradient boosting. THEMED, static.

    Static, because the reader compares the three panels. Each panel shows what
    its method buys rather than how it is implemented: a tree you can read out
    loud, a crowd whose vote stops swinging with every new example, and a
    sequence where each tree is trained on what is still wrong.
    """
    px, pw = (20, 270, 520), 220
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 388" '
        'class="fig-tree-ensembles" role="img" aria-label="Three panels. First, a '
        'single decision tree of yes-or-no questions ending in fails or fine. '
        'Second, a random forest of six small trees each casting a vote, five of '
        'six saying it fails. Third, gradient boosting: four trees in sequence '
        'with a bar under each showing the error still left, shrinking from tree '
        'to tree.">',
        '<text class="fig-title" x="20" y="24">One tree, a crowd of them, then a queue of '
        'them</text>',
        '<text class="fig-sub" x="20" y="44">The same questions asked of the same table. What '
        'changes is how many trees, and how they are combined.</text>',
    ]

    def mini_tree(cx, cy, spread=16, drop=22):
        """The three-node glyph that stands for a whole tree.

        Solid branches, not `fig-track`: at this length a dashed line breaks
        into two or three marks and the glyph stops reading as a tree.
        """
        return [
            f'<line class="fig-edge" x1="{cx}" y1="{cy}" x2="{cx - spread}" y2="{cy + drop}"/>',
            f'<line class="fig-edge" x1="{cx}" y1="{cy}" x2="{cx + spread}" y2="{cy + drop}"/>',
            f'<circle class="fig-box" cx="{cx}" cy="{cy}" r="5"/>',
            f'<circle class="fig-box" cx="{cx - spread}" cy="{cy + drop}" r="4"/>',
            f'<circle class="fig-box" cx="{cx + spread}" cy="{cy + drop}" r="4"/>',
        ]

    # ---- 1: one tree, small enough to read
    x = px[0]
    p += [
        f'<text class="fig-box-title" x="{x}" y="78">One decision tree</text>',
        f'<text class="fig-box-sub" x="{x}" y="96">questions it worked out itself</text>',
        f'<line class="fig-edge" x1="{x + 110}" y1="140" x2="{x + 56}" y2="168"/>',
        f'<line class="fig-edge" x1="{x + 110}" y1="140" x2="{x + 168}" y2="168"/>',
        f'<text class="fig-box-sub" x="{x + 66}" y="160">yes</text>',
        f'<text class="fig-box-sub" x="{x + 146}" y="160">no</text>',
        f'<rect class="fig-box" x="{x + 35}" y="112" width="150" height="28" rx="8"/>',
        f'<text class="fig-box-sub" x="{x + 110}" y="130" text-anchor="middle">vibration above '
        f'4.5?</text>',
        f'<line class="fig-edge" x1="{x + 56}" y1="196" x2="{x + 36}" y2="224"/>',
        f'<line class="fig-edge" x1="{x + 56}" y1="196" x2="{x + 112}" y2="224"/>',
        f'<rect class="fig-box" x="{x + 4}" y="168" width="104" height="28" rx="8"/>',
        f'<text class="fig-box-sub" x="{x + 56}" y="186" text-anchor="middle">over 900 hours '
        f'run?</text>',
        f'<rect class="fig-lit-box c-blue" x="{x + 124}" y="168" width="88" height="28" rx="8"/>',
        f'<text class="fig-lit-sub" x="{x + 168}" y="186" text-anchor="middle">fine</text>',
        f'<rect class="fig-lit-box c-orange" x="{x + 2}" y="224" width="68" height="28" rx="8"/>',
        f'<text class="fig-lit-sub" x="{x + 36}" y="242" text-anchor="middle">fails</text>',
        f'<rect class="fig-lit-box c-blue" x="{x + 78}" y="224" width="68" height="28" rx="8"/>',
        f'<text class="fig-lit-sub" x="{x + 112}" y="242" text-anchor="middle">fine</text>',
    ]
    for i, line in enumerate(("you can read it out loud, which",
                              "is why people trust it,",
                              "but move a few examples and the",
                              "whole tree redraws itself")):
        p.append(f'<text class="fig-box-sub" x="{x}" y="{272 + i * 16}">{line}</text>')

    # ---- 2: many trees, each on its own slice, voting
    x = px[1]
    p += [
        f'<text class="fig-box-title" x="{x}" y="78">A random forest</text>',
        f'<text class="fig-box-sub" x="{x}" y="96">hundreds of trees, one vote each</text>',
    ]
    votes = ("b", "b", "a", "b", "b", "b")      # b = fails, a = fine
    for i, vote in enumerate(votes):
        cx = x + (36, 110, 184)[i % 3]
        cy = 124 + (i // 3) * 62
        p += mini_tree(cx, cy, spread=14, drop=20)
        cls = "fig-dot-b" if vote == "b" else "fig-dot-a"
        p.append(f'<circle class="{cls}" cx="{cx}" cy="{cy + 36}" r="5.5"/>')
    for i, line in enumerate(("each tree sees a random slice of",
                              "the rows and of the columns, so",
                              "they make different mistakes;",
                              "five of these six say it fails,",
                              "and the majority is the answer")):
        p.append(f'<text class="fig-box-sub" x="{x}" y="{256 + i * 16}">{line}</text>')

    # ---- 3: trees in sequence, each on what is still wrong
    x = px[2]
    p += [
        f'<text class="fig-box-title" x="{x}" y="78">Gradient boosting</text>',
        f'<text class="fig-box-sub" x="{x}" y="96">in sequence, not in parallel: XGBoost</text>',
    ]
    bars, base = (46, 27, 14, 6), 220
    for i, h in enumerate(bars):
        cx = x + (30, 88, 146, 204)[i]
        p += mini_tree(cx, 124, spread=14, drop=20)
        p.append(f'<rect class="fig-lit-box c-orange" x="{cx - 7}" y="{base - h}" width="14" '
                 f'height="{h}" rx="3"/>')
        if i < 3:
            p.append(f'<path class="fig-centre" d="M{cx + 21} 118 L{cx + 31} 124 L{cx + 21} '
                     f'130 z"/>')
    p.append(f'<line class="fig-track" x1="{x + 12}" y1="{base}" x2="{x + 218}" y2="{base}"/>')
    p.append(f'<text class="fig-box-sub" x="{x + 110}" y="{base + 16}" text-anchor="middle">what '
             f'is still wrong</text>')
    for i, line in enumerate(("each new tree is trained on what",
                              "the ones before it got wrong,",
                              "which makes it the most accurate",
                              "and the hardest to argue with")):
        p.append(f'<text class="fig-box-sub" x="{x}" y="{272 + i * 16}">{line}</text>')

    p.append('<text class="fig-sub" x="20" y="352">A tree explains itself and moves with every '
             'new example. A forest averages that away. Boosting, built</text>')
    p.append('<text class="fig-sub" x="20" y="370">on the leftovers, usually wins on a table of '
             'numbers, and each step costs you a little readability.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------------- clustering
def clustering():
    """The same points, before and after a machine grouped them. THEMED, static."""
    pts = ((44, 62), (68, 48), (58, 86), (86, 70), (36, 92), (74, 100),
           (168, 150), (196, 132), (180, 176), (206, 166), (150, 168), (214, 190),
           (250, 54), (272, 78), (292, 52), (266, 40), (296, 84), (240, 76))
    # Radii are generous: the vertical compression below turns each round cluster
    # into a slight ellipse, and a tight circle then cuts a corner point.
    rings = ((62, 76, 50), (186, 158, 54), (270, 62, 48))
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 326" '
        'class="fig-clustering" role="img" aria-label="The same scatter of points '
        'twice. On the left it is unlabelled. On the right, three rings mark the '
        'groups a clustering method found without being told what to look for.">',
        '<text class="fig-title" x="20" y="24">Learning without being told the answer</text>',
        '<text class="fig-sub" x="20" y="44">Nobody labelled these points. The grouping is the '
        'output, not the input.</text>',
        '<text class="fig-box-title" x="20" y="80">What you have</text>',
        '<text class="fig-box-sub" x="20" y="98">every pump, described by how it behaves</text>',
        '<text class="fig-box-title" x="400" y="80">What clustering found</text>',
        '<text class="fig-box-sub" x="400" y="98">three groups, and no idea what they mean</text>',
    ]
    # Compressed vertically and lifted: at full spread the lowest ring ran into the
    # closing text underneath it.
    sc, base = 0.74, 106

    def py(dy):
        return base + 40 + (dy - 40) * sc

    for dx, dy in pts:
        p.append(f'<circle class="fig-dot-a" cx="{20 + dx}" cy="{py(dy):.0f}" r="4.5"/>')
    for cx, cy, r in rings:
        p.append(f'<circle class="fig-track" cx="{400 + cx}" cy="{py(cy):.0f}" '
                 f'r="{r * sc:.0f}" fill="none"/>')
    for dx, dy in pts:
        p.append(f'<circle class="fig-dot-a" cx="{400 + dx}" cy="{py(dy):.0f}" r="4.5"/>')
    p.append('<text class="fig-sub" x="20" y="296">Useful when you do not know what you are '
             'looking for: which machines behave alike, which readings sit</text>')
    p.append('<text class="fig-sub" x="20" y="314">outside every group. Naming the groups is a '
             'job for somebody who knows the plant.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------------------- k-means
def k_means_steps():
    """How k-means works, and what the result is worth. THEMED, static.

    Two panels rather than three: the left one is the whole algorithm (assign,
    move, repeat), the right one is what you are left with, which is the part a
    reader can act on. The crosses on the left start off the blobs and are
    joined to where they end up, because the movement IS the method.

    The lone point is deliberately far from all three centres: k-means still
    files it under its nearest one, and that distance is the anomaly score.
    """
    lx, rx, base = 20, 400, 124
    groups = (
        ("fig-dot-a", "fig-line-a", ((40, 30), (66, 16), (54, 52), (82, 38), (30, 64), (70, 70)),
         (57, 45), "start-up"),
        ("fig-dot-b", "fig-line-b", ((150, 104), (178, 90), (162, 126), (196, 112), (136, 126),
                                     (206, 96)), (171, 109), "steady load"),
        ("fig-dot-c", "fig-line-c", ((248, 34), (276, 58), (292, 28), (258, 66), (300, 68),
                                     (236, 12)), (268, 44), "recirculating"),
    )
    # Where the centres were dropped. The third sits below the green blob rather
    # than inside the orange one, where it read as an orange member.
    starts = ((110, 20), (120, 74), (236, 118))
    odd = (160, 8)                                  # belongs to no group
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 376" '
        'class="fig-k-means" role="img" aria-label="Two panels. On the left, three '
        'cross-shaped centres start at arbitrary positions and are joined by dashed '
        'lines to where they settle, in the middle of three groups of points. On the '
        'right, the same three groups carry the names a person gave them, and one '
        'point sits far from every centre.">',
        '<text class="fig-title" x="20" y="24">k-means: the whole method, and what it leaves '
        'you</text>',
        '<text class="fig-sub" x="20" y="44">You choose how many groups. Everything after that '
        'is repetition until nothing moves.</text>',
        f'<text class="fig-box-title" x="{lx}" y="78">How it works</text>',
        f'<text class="fig-box-sub" x="{lx}" y="96">the centres move to where the points '
        'are</text>',
        f'<text class="fig-box-title" x="{rx}" y="78">What you get</text>',
        f'<text class="fig-box-sub" x="{rx}" y="96">three groups, named afterwards by somebody '
        'who knows the plant</text>',
    ]

    def cross(x0, dx, dy, cls, size=9):
        return (f'<path class="{cls}" d="M{x0 + dx - size} {base + dy} L{x0 + dx + size} '
                f'{base + dy} M{x0 + dx} {base + dy - size} L{x0 + dx} {base + dy + size}" '
                f'fill="none"/>')

    # ---- left: the centres start badly placed and walk to the middle
    for (dot, line, pts, centre, _), start in zip(groups, starts):
        p.append(f'<line class="fig-track" x1="{lx + start[0]}" y1="{base + start[1]}" '
                 f'x2="{lx + centre[0]}" y2="{base + centre[1]}"/>')
    for (dot, line, pts, centre, _), start in zip(groups, starts):
        for dx, dy in pts:
            p.append(f'<circle class="{dot}" cx="{lx + dx}" cy="{base + dy}" r="4.5"/>')
        p.append(cross(lx, start[0], start[1], f"{line} fig-line--ghost", size=7))
        p.append(cross(lx, centre[0], centre[1], line))
    p.append(f'<circle class="fig-dot-b" cx="{lx + odd[0]}" cy="{base + odd[1]}" r="4.5"/>')
    p.append(f'<text class="fig-box-sub" x="{lx + starts[0][0] + 12}" '
             f'y="{base + starts[0][1] + 4}">where they started</text>')
    for i, line in enumerate(("1 · drop k centres anywhere; k is your choice",
                              "2 · every point joins the centre nearest to it",
                              "3 · each centre moves to the middle of its points",
                              "then repeat 2 and 3 until nothing moves")):
        p.append(f'<text class="fig-box-sub" x="{lx}" y="{270 + i * 16}">{line}</text>')

    # ---- right: the same groups, named, plus the point that belongs to none
    for dot, line, pts, centre, _ in groups:
        for dx, dy in pts:
            p.append(f'<circle class="{dot}" cx="{rx + dx}" cy="{base + dy}" r="4.5"/>')
        p.append(cross(rx, centre[0], centre[1], line))
    p.append(f'<line class="fig-track" x1="{rx + odd[0]}" y1="{base + odd[1]}" '
             f'x2="{rx + groups[1][3][0]}" y2="{base + groups[1][3][1]}"/>')
    # ring before the dot: fig-box fills with the surface colour and would hide it
    p.append(f'<circle class="fig-box" cx="{rx + odd[0]}" cy="{base + odd[1]}" r="10"/>')
    p.append(f'<circle class="fig-dot-b" cx="{rx + odd[0]}" cy="{base + odd[1]}" r="4.5"/>')
    # The odd point's explanation goes in the legend, not beside it: every
    # position next to that point runs over one of the three clusters.
    for i, (dot, line, pts, centre, name) in enumerate(groups):
        gx = rx + (0, 116, 226)[i]
        p.append(cross(gx + 8, 0, 146, line, size=6))
        p.append(f'<text class="fig-box-sub" x="{gx + 20}" y="{base + 150}">{name}</text>')
    p.append(f'<circle class="fig-box" cx="{rx + 8}" cy="{base + 170}" r="9"/>')
    p.append(f'<circle class="fig-dot-b" cx="{rx + 8}" cy="{base + 170}" r="4.5"/>')
    p.append(f'<text class="fig-box-sub" x="{rx + 22}" y="{base + 174}">filed under its nearest '
             f'group, and nowhere near it</text>')

    p.append('<text class="fig-sub" x="20" y="344">k-means finds the groups and nothing else. '
             'Naming them is human work, and the name is worth keeping as a</text>')
    p.append('<text class="fig-sub" x="20" y="362">label, because from then on the distance to '
             'the nearest centre is an anomaly score you got for free.</text>')
    p.append("</svg>")
    return "\n".join(p)


# --------------------------------------------------------------- neural network
def neural_network():
    """Layers, connections, and one signal's route through them. THEMED.

    The single highlighted path is animated: it is the only thing here that
    happens in an order, and it saves the reader from tracing 32 grey lines.
    """
    cols = (150, 330, 500, 670)
    ins = (120, 175, 230)
    h1 = (100, 155, 210, 265)
    h2 = (100, 155, 210, 265)
    out = 175
    r = 13
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 330" '
        'class="fig-neural-network" role="img" aria-label="Three input features on '
        'the left, two middle layers of four nodes each, and one output on the '
        'right, with every node connected to every node in the next layer. One '
        'route through the network is highlighted.">',
        '<text class="fig-title" x="20" y="24">When the rule is a shape nobody can write '
        'down</text>',
        '<text class="fig-sub" x="20" y="44">Every connection is a number. Training adjusts them '
        'until the answers come out right.</text>',
        '<text class="fig-box-sub" x="150" y="76" text-anchor="middle">what you feed in</text>',
        '<text class="fig-box-sub" x="415" y="76" text-anchor="middle">layers that combine '
        'them</text>',
        '<text class="fig-box-sub" x="670" y="76" text-anchor="middle">the answer</text>',
    ]
    for a in ins:
        for b in h1:
            p.append(f'<line class="fig-track" x1="{cols[0] + r}" y1="{a}" x2="{cols[1] - r}" '
                     f'y2="{b}"/>')
    for a in h1:
        for b in h2:
            p.append(f'<line class="fig-track" x1="{cols[1] + r}" y1="{a}" x2="{cols[2] - r}" '
                     f'y2="{b}"/>')
    for a in h2:
        p.append(f'<line class="fig-track" x1="{cols[2] + r}" y1="{a}" x2="{cols[3] - r}" '
                 f'y2="{out}"/>')
    # one route, so the eye has something to follow
    route = ((cols[0] + r, ins[1], cols[1] - r, h1[2]),
             (cols[1] + r, h1[2], cols[2] - r, h2[1]),
             (cols[2] + r, h2[1], cols[3] - r, out))
    for x1, y1, x2, y2 in route:
        p.append(f'<path class="fig-exit-path fig-flow" d="M{x1} {y1} L{x2} {y2}" fill="none"/>')
    for y, label in zip(ins, ("vibration", "temperature", "hours since start")):
        p.append(f'<circle class="fig-box" cx="{cols[0]}" cy="{y}" r="{r}"/>')
        p.append(f'<text class="fig-box-sub" x="{cols[0] - r - 8}" y="{y + 4}" '
                 f'text-anchor="end">{label}</text>')
    for col, ys in ((cols[1], h1), (cols[2], h2)):
        for y in ys:
            p.append(f'<circle class="fig-box" cx="{col}" cy="{y}" r="{r}"/>')
    p.append(f'<circle class="fig-lit-box c-blue" cx="{cols[3]}" cy="{out}" r="{r + 3}"/>')
    p.append(f'<text class="fig-box-sub" x="{cols[3]}" y="{out + 36}" '
             f'text-anchor="middle">chance it fails</text>')
    p.append('<text class="fig-sub" x="20" y="298">Nobody chooses what the middle layers stand '
             'for. That is why a network can learn a pattern you could</text>')
    p.append('<text class="fig-sub" x="20" y="316">never have described, and why it cannot '
             'explain itself the way a straight line can.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------- lstm sequence anomaly
def lstm_sequence_anomaly():
    """What a sequence model sees that a threshold cannot. THEMED, animated.

    The first version of this figure drew four boxes with words in them and
    explained nothing, because the thing worth showing is not "there is a memory",
    it is what the memory buys: a prediction of what should come next, and
    therefore a way to notice that the shape is wrong while every single value is
    still comfortably in range.

    fig-draw on the actual trace, so it draws itself and visibly peels away from
    the prediction rather than the reader having to find the divergence.
    """
    x0, x1 = 120, 730
    mid, amp, period = 190, 54, 150
    split = 470                                  # where the behaviour changes
    hi, lo = 112, 268                            # the limits, never crossed

    def normal(x):
        return mid - amp * math.sin(2 * math.pi * (x - x0) / period)

    def actual(x):
        """Same range, wrong shape: the cycle collapses and drifts."""
        if x <= split:
            return normal(x)
        t = (x - split) / (x1 - split)
        decay = 1 - 0.72 * min(1.0, t * 1.6)
        return mid - amp * decay * math.sin(2 * math.pi * (x - x0) / period) - 26 * t

    def path(fn, a, b, step=3):
        pts = [f"{x} {fn(x):.1f}" for x in range(a, b + 1, step)]
        return "M" + " L".join(pts)

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 350" '
        'class="fig-lstm-anomaly" role="img" aria-label="A signal cycling regularly '
        'between a high and a low limit. Two thirds of the way along, the actual '
        'trace stops matching the prediction: the cycle flattens and drifts. Every '
        'value stays inside the limits, so no threshold fires, but the shape has '
        'changed and that is what a sequence model detects.">',
        '<text class="fig-title" x="20" y="24">An anomaly that never crosses a limit</text>',
        '<text class="fig-sub" x="20" y="44">A sequence model predicts what should come next. '
        'The gap between that and what arrives is the finding.</text>',
        f'<line class="fig-track" x1="{x0}" y1="{hi}" x2="{x1}" y2="{hi}"/>',
        f'<line class="fig-track" x1="{x0}" y1="{lo}" x2="{x1}" y2="{lo}"/>',
        f'<text class="fig-box-sub" x="{x0}" y="{hi - 8}">high limit, never reached</text>',
        f'<text class="fig-box-sub" x="{x0}" y="{lo + 18}">low limit, never reached</text>',
        f'<line class="fig-track" x1="{split}" y1="96" x2="{split}" y2="{lo + 4}"/>',
        f'<text class="fig-box-sub" x="{split + 8}" y="96">the shape changes here</text>',
    ]
    # what the model expected, from everything it had seen before
    p.append(f'<path class="fig-line-a fig-line--ghost" d="{path(normal, split, x1)}" '
             f'fill="none"/>')
    # Parked above the ghost's last peak: at the right-hand edge all three labels
    # piled into the same corner.
    p.append(f'<text class="fig-box-sub" x="682" y="124" text-anchor="middle">what the model '
             f'expected</text>')
    # what actually arrived
    p.append(f'<path class="fig-line-a" d="{path(normal, x0, split)}" fill="none"/>')
    p.append(f'<path class="fig-line-b fig-draw" d="{path(actual, split, x1)}" fill="none"/>')
    p.append(f'<text class="fig-box-sub" x="{x1}" y="192" text-anchor="end">what '
             f'arrived</text>')
    # the surprise, which is the thing worth raising an event about
    # A trough of the prediction, where the two are furthest apart. The first
    # attempt marked x=640, where they happen to cross and there is no gap to see.
    gap_x = 608
    p.append(f'<line class="fig-track" x1="{gap_x}" y1="{normal(gap_x):.1f}" x2="{gap_x}" '
             f'y2="{actual(gap_x):.1f}"/>')
    p.append(f'<circle class="fig-token fig-pulse" cx="{gap_x}" cy="{actual(gap_x):.1f}" r="7"/>')
    p.append(f'<text class="fig-box-sub" x="{gap_x}" y="256" text-anchor="middle">the '
             f'surprise, and it is growing</text>')

    p.append('<text class="fig-sub" x="20" y="316">Every reading is in range, so no threshold '
             'fires and no snapshot model has anything to say.</text>')
    p.append('<text class="fig-sub" x="20" y="334">What changed is the pattern, and a pattern '
             'only exists across time.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------ text as sequence
def text_sequence_intent():
    """Three requests built from almost the same words, meaning three things.

    THEMED, static: the reader compares three rows, so nothing may be hidden.
    The chips are sized from the text, because hand-tuned widths drift the moment
    a word is edited.
    """
    rows = (
        (["can", "you", "close", "my", "credit card"], (2, 4), "close · my own card"),
        (["can", "you", "open", "my wife’s", "credit card"], (2, 3), "open · somebody else’s"),
        # No shared verb at all with row one, which is the point of the third row
        (["I", "no longer need", "my", "mastercard"], (1, 3), "close · my own card"),
    )
    y0, dy, ch = 116, 62, 34
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 336" '
        'class="fig-text-sequence" role="img" aria-label="Three requests written as '
        'rows of word chips. The first and third share an intent but not their '
        'words; the first and second share nearly all their words but not their '
        'intent. The words that decide the meaning are highlighted.">',
        '<text class="fig-title" x="20" y="24">Almost the same words, three different '
        'requests</text>',
        '<text class="fig-sub" x="20" y="44">Counting words cannot separate these. Reading them '
        'in order can.</text>',
        '<text class="fig-box-sub" x="20" y="92">what was asked</text>',
        '<text class="fig-box-sub" x="530" y="92">what it means</text>',
    ]
    for i, (words, lit, intent) in enumerate(rows):
        y = y0 + i * dy
        x = 20
        for j, w in enumerate(words):
            cw = len(w) * 6.4 + 20
            hot = j in lit
            cls = "fig-lit-box c-orange" if hot else "fig-box"
            t_cls = "fig-lit-sub" if hot else "fig-box-sub"
            p.append(f'<rect class="{cls}" x="{x:.0f}" y="{y}" width="{cw:.0f}" height="{ch}" '
                     f'rx="9"/>'
                     f'<text class="{t_cls}" x="{x + cw / 2:.0f}" y="{y + 22}" '
                     f'text-anchor="middle">{w}</text>')
            x += cw + 7
        p.append(f'<path class="fig-exit-path fig-flow" d="M{x + 6:.0f} {y + ch / 2:.0f} '
                 f'L520 {y + ch / 2:.0f}" fill="none"/>')
        p.append(f'<rect class="fig-box" x="530" y="{y}" width="210" height="{ch}" rx="9"/>'
                 f'<text class="fig-box-sub" x="635" y="{y + 22}" '
                 f'text-anchor="middle">{intent}</text>')
    p.append('<text class="fig-sub" x="20" y="300">Rows one and three mean the same thing and '
             'share only the word “my”. Rows one and two share nearly</text>')
    p.append('<text class="fig-sub" x="20" y="318">every word and mean different things. Order '
             'and context are the whole difference.</text>')
    p.append("</svg>")
    return "\n".join(p)


# -------------------------------------------------------- measured vs generated
def measured_vs_generated():
    """What a generated reading is, for a reader still new to datapoints.

    THEMED, static. Deliberately plain: two lanes that differ in one box, because
    the point being made is that they differ in one box.
    """
    def arrow(x, y):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + 11} {y} L{x} {y + 5} z"/>'

    lanes = (
        (104, "Measured", "A sensor on the pump", "71.2 °C at 09:14",
         "one datapoint, stored", False),
        (196, "Generated", "A model of the pump", "71.4 °C at 09:14",
         "one datapoint, stored, marked generated", True),
    )
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 320" '
        'class="fig-measured-generated" role="img" aria-label="Two lanes. In the '
        'first a sensor produces a reading which is stored as a datapoint. In the '
        'second a model of the same pump produces a reading of the same kind, '
        'stored the same way, and marked as generated.">',
        '<text class="fig-title" x="20" y="24">The only difference is where the number came '
        'from</text>',
        '<text class="fig-sub" x="20" y="44">A reading with a time on it is a datapoint. Both '
        'lanes end with one, and they look alike.</text>',
    ]
    for y, lane, source, reading, stored, gen in lanes:
        mid = y + 26
        p.append(f'<text class="fig-box-title" x="20" y="{y - 8}">{lane}</text>')
        p.append(f'<rect class="fig-box" x="20" y="{y}" width="186" height="52" rx="12"/>'
                 f'<text class="fig-box-sub" x="113" y="{mid + 4}" '
                 f'text-anchor="middle">{source}</text>')
        p.append(f'<path class="fig-exit-path fig-flow" d="M206 {mid} L235 {mid}" fill="none"/>')
        p.append(arrow(235, mid))
        p.append(f'<rect class="fig-box" x="252" y="{y}" width="150" height="52" rx="12"/>'
                 f'<text class="fig-box-title" x="327" y="{mid + 5}" '
                 f'text-anchor="middle">{reading}</text>')
        p.append(f'<path class="fig-exit-path fig-flow" d="M402 {mid} L431 {mid}" fill="none"/>')
        p.append(arrow(431, mid))
        cls = "fig-lit-box c-orange" if gen else "fig-box"
        t_cls = "fig-lit-sub" if gen else "fig-box-sub"
        p.append(f'<rect class="{cls}" x="448" y="{y}" width="292" height="52" rx="12"/>'
                 f'<text class="{t_cls}" x="594" y="{mid + 4}" '
                 f'text-anchor="middle">{stored}</text>')
    p.append('<text class="fig-sub" x="20" y="286">Nothing in the number itself says which lane '
             'it came from. The mark on the second one is the</text>')
    p.append('<text class="fig-sub" x="20" y="304">only thing keeping the two apart, which is '
             'why it is not optional.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------- robot learning loop
def robot_learning_loop():
    """How a robot is taught, and where the data comes from. THEMED, animated.

    The return arc is the argument: the loop runs continuously, and the middle
    stage, which produces almost all of the data, is generated rather than
    measured.
    """
    def arrow(x, y):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + 11} {y} L{x} {y + 5} z"/>'

    by, bh = 104, 72
    mid = by + bh / 2
    stages = (
        (20, 158, "A person shows it", "a few hundred demonstrations", False),
        (206, 168, "It copies", "imitation learning", False),
        (402, 158, "It practises", "millions of tries, in simulation", True),
        (588, 152, "It works", "and records everything", False),
    )
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 300" '
        'class="fig-robot-learning" role="img" aria-label="Four stages in a loop: a '
        'person demonstrates the task, the robot copies the demonstrations, the '
        'robot practises millions of times in simulation, and then it works for '
        'real and records everything. The practice stage is highlighted because '
        'almost all of the data comes from there, and it is generated.">',
        '<text class="fig-title" x="20" y="24">Where a robot’s training data comes from</text>',
        '<text class="fig-sub" x="20" y="44">A person can demonstrate a task a few hundred '
        'times. Learning it takes millions of attempts.</text>',
    ]
    for i, (x, w, title, sub, lit) in enumerate(stages):
        if i:
            px_prev = stages[i - 1][0] + stages[i - 1][1]
            p.append(f'<path class="fig-exit-path fig-flow" d="M{px_prev} {mid:.0f} '
                     f'L{x - 11} {mid:.0f}" fill="none"/>')
            p.append(arrow(x - 11, mid))
        cls = "fig-lit-box c-orange" if lit else "fig-box"
        t_cls = "fig-lit-title" if lit else "fig-box-title"
        s_cls = "fig-lit-sub" if lit else "fig-box-sub"
        p.append(f'<rect class="{cls}" x="{x}" y="{by}" width="{w}" height="{bh}" rx="12"/>'
                 f'<text class="{t_cls}" x="{x + w / 2:.0f}" y="{by + 30}" '
                 f'text-anchor="middle">{title}</text>'
                 f'<text class="{s_cls}" x="{x + w / 2:.0f}" y="{by + 50}" '
                 f'text-anchor="middle">{sub}</text>')
    p.append(f'<path class="fig-exit-path fig-flow" d="M664 {by + bh} L664 214 L99 214 '
             f'L99 {by + bh + 11}" fill="none"/>')
    p.append(f'<path class="fig-centre" d="M94 {by + bh + 11} L99 {by + bh} '
             f'L104 {by + bh + 11} z"/>')
    p.append('<text class="fig-box-sub" x="380" y="234" text-anchor="middle">what it learns in '
             'the world becomes the next round of demonstrations</text>')
    p.append('<text class="fig-sub" x="20" y="268">Nearly all of the training data comes from '
             'the highlighted stage, and none of it was measured.</text>')
    p.append('<text class="fig-sub" x="20" y="286">The real robot is where the result is tested, '
             'not where the practice happens.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------- features on image
def features_on_image():
    """The same idea as a computed feature, on a photograph. THEMED.

    Four panels, static, because a reader compares them. The point of the figure
    is that only the last panel has a name a person would use: everything before
    it is a feature built out of the panel to its left.
    """
    def arrow(x, y):
        return f'<path class="fig-centre" d="M{x} {y - 5} L{x + 11} {y} L{x} {y + 5} z"/>'

    pw = 150
    xs = (20, 205, 390, 575)
    mid_y = 146
    heads = ("Pixels", "Edges", "Shapes", "An object")
    caps = (("brightness at a point,", "and nothing else"),
            ("where the brightness", "changes, and which way"),
            ("edges that keep company:", "a ring, a pointer, ticks"),
            ("a name, and how sure", "the model is of it"))
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 322" '
        'class="fig-features-image" role="img" aria-label="Four panels. A grid of '
        'pixels, then the edges found in it, then the shapes those edges form, a '
        'ring with a pointer and tick marks, and finally the object itself, '
        'recognised as a pressure gauge with a confidence score.">',
        '<text class="fig-title" x="20" y="24">The same idea, on a photograph</text>',
        '<text class="fig-sub" x="20" y="44">Nobody writes down what a gauge looks like. Each '
        'panel is built out of the one to its left.</text>',
    ]
    for i, (x, head, cap) in enumerate(zip(xs, heads, caps)):
        p.append(f'<text class="fig-box-title" x="{x + pw / 2:.0f}" y="82" '
                 f'text-anchor="middle">{head}</text>')
        # Captions clear of the confidence chip in the last panel, which sits at 218
        p.append(f'<text class="fig-box-sub" x="{x + pw / 2:.0f}" y="240" '
                 f'text-anchor="middle">{cap[0]}</text>')
        p.append(f'<text class="fig-box-sub" x="{x + pw / 2:.0f}" y="256" '
                 f'text-anchor="middle">{cap[1]}</text>')
        if i:
            p.append(f'<path class="fig-exit-path fig-flow" d="M{x - 35} {mid_y} '
                     f'L{x - 11} {mid_y}" fill="none"/>')
            p.append(arrow(x - 11, mid_y))

    # 1: a grid of cells, lit roughly where the gauge is
    cell, cols = 15, 6
    gx = xs[0] + (pw - cols * (cell + 1)) / 2
    for r in range(6):
        for c in range(cols):
            d = math.hypot(r - 2.5, c - 2.5)
            cls = "fig-lit-box c-blue" if d < 2.7 else "fig-box"
            p.append(f'<rect class="{cls}" x="{gx + c * (cell + 1):.0f}" '
                     f'y="{98 + r * (cell + 1)}" width="{cell}" height="{cell}" rx="2"/>')

    # 2: short segments where the brightness changes, tangent to the ring
    cx2, r2 = xs[1] + pw / 2, 32
    for k in range(12):
        a = 2 * math.pi * k / 12
        ox, oy = cx2 + r2 * math.cos(a), mid_y + r2 * math.sin(a)
        tx, ty = -math.sin(a) * 9, math.cos(a) * 9
        p.append(f'<path class="fig-line-a" d="M{ox - tx:.1f} {oy - ty:.1f} L{ox + tx:.1f} '
                 f'{oy + ty:.1f}" fill="none"/>')
    p.append(f'<path class="fig-line-a" d="M{cx2:.0f} {mid_y} L{cx2 + 18:.0f} {mid_y - 14}" '
             f'fill="none"/>')

    # 3: the shapes those edges add up to
    cx3 = xs[2] + pw / 2
    p.append(f'<circle class="fig-line-a" cx="{cx3:.0f}" cy="{mid_y}" r="34" fill="none"/>')
    for k in range(8):
        a = 2 * math.pi * k / 8
        p.append(f'<path class="fig-line-a" d="M{cx3 + 27 * math.cos(a):.1f} '
                 f'{mid_y + 27 * math.sin(a):.1f} L{cx3 + 33 * math.cos(a):.1f} '
                 f'{mid_y + 33 * math.sin(a):.1f}" fill="none"/>')
    p.append(f'<path class="fig-line-b" d="M{cx3:.0f} {mid_y} L{cx3 + 22:.0f} {mid_y - 17}" '
             f'fill="none"/>')

    # 4: the object, named
    cx4 = xs[3] + pw / 2
    p.append(f'<rect class="fig-centre" x="{cx4 - 44:.0f}" y="{mid_y - 44}" width="88" '
             f'height="88" rx="10"/>')
    p.append(f'<circle class="fig-line-a" cx="{cx4:.0f}" cy="{mid_y}" r="30" fill="none"/>')
    p.append(f'<path class="fig-line-b" d="M{cx4:.0f} {mid_y} L{cx4 + 20:.0f} {mid_y - 15}" '
             f'fill="none"/>')
    p.append(f'<rect class="fig-lit-box c-blue" x="{cx4 - 62:.0f}" y="{mid_y + 48}" width="124" '
             f'height="24" rx="8"/>'
             f'<text class="fig-lit-sub" x="{cx4:.0f}" y="{mid_y + 64}" '
             f'text-anchor="middle">pressure gauge · 0.94</text>')

    p.append('<text class="fig-sub" x="20" y="292">Only the last panel has a name a person would '
             'use. The two in the middle are features the model</text>')
    p.append('<text class="fig-sub" x="20" y="310">worked out for itself, and they are what the '
             'answer is actually built from.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ------------------------------------------------------------- events from series
def events_from_series():
    """Three different reasons the same trace produces an event. THEMED.

    Static: the reader compares the three moments. The trace is one continuous
    signal on purpose, because the point is that nothing about the series
    changes, only what somebody decided was worth recording.
    """
    x_l, x_r = 120, 730
    base, limit = 172, 112
    marks = (255, 440, 600)

    def trace(x):
        y = base - 8 * math.sin(x / 22)
        if 205 < x < 315:                      # the excursion that breaks the limit
            y -= 74 * math.exp(-(((x - 255) / 26) ** 2))
        if 390 < x < 500:                      # same range, unfamiliar rhythm
            y -= 15 * math.sin((x - 390) / 6.5)
        if x > 545:                            # settles into a different regime
            y += 34 / (1 + math.exp(-(x - 585) / 7))
        return y

    pts = [f"{x} {trace(x):.1f}" for x in range(x_l, x_r + 1, 3)]
    chips = (
        (170, "ALARM", "pressure over the limit"),
        (350, "ANOMALY", "shape nothing like normal"),
        (520, "NEW CONDITION", "pump switched to standby"),
    )
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 340" '
        'class="fig-events-series" role="img" aria-label="One pressure trace with '
        'three moments marked. The first crosses a limit and raises an alarm. The '
        'second stays inside the limit but changes shape, and raises an anomaly. '
        'The third settles at a new level and records a change of condition. Each '
        'becomes an event underneath the chart.">',
        '<text class="fig-title" x="20" y="24">Three reasons the same trace becomes an '
        'event</text>',
        '<text class="fig-sub" x="20" y="44">The series keeps every reading. An event records '
        'the moment something decided a reading mattered.</text>',
        f'<line class="fig-track" x1="{x_l}" y1="{limit}" x2="{x_r}" y2="{limit}"/>',
        f'<text class="fig-box-sub" x="{x_l}" y="{limit - 8}">high limit</text>',
        f'<text class="fig-box-sub" x="20" y="{base + 4}">21-PT-3105</text>',
        f'<path class="fig-line-a" d="M{" L".join(pts)}" fill="none"/>',
    ]
    for mx, (cx, title, sub) in zip(marks, chips):
        my = trace(mx)
        p.append(f'<circle class="fig-token" cx="{mx}" cy="{my:.1f}" r="7"/>')
        p.append(f'<line class="fig-track" x1="{mx}" y1="{my + 10:.1f}" x2="{cx + 80}" '
                 f'y2="240"/>')
        p.append(f'<rect class="fig-lit-box c-orange" x="{cx}" y="240" width="160" height="46" '
                 f'rx="12"/>'
                 f'<text class="fig-lit-title" x="{cx + 80}" y="{262}" '
                 f'text-anchor="middle">{title}</text>'
                 f'<text class="fig-lit-sub" x="{cx + 80}" y="{278}" '
                 f'text-anchor="middle">{sub}</text>')
    p.append('<text class="fig-sub" x="20" y="316">All three hang off the same pump, so they sit '
             'alongside the work orders, the inspections and</text>')
    p.append('<text class="fig-sub" x="20" y="334">everything else recorded against it, and '
             'against the equipment around it.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ================================================================ stream processing
def answer_age():
    """How old the answer is at the moment somebody needs it. THEMED, static.

    The quantity plotted is the age of the answer rather than the answer, because
    that is where the finding lives: a nightly job is not wrong, it is
    periodically right, and the sawtooth is what that costs.
    """
    x0, x1, base, top = 90, 668, 280, 110
    day = (x1 - x0) / 2                       # two midnights to midnight spans
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 366" '
        'class="fig-answer-age" role="img" aria-label="The age of an answer over two '
        'days. A nightly batch job produces a sawtooth: the answer is fresh just after '
        'midnight and a full day old just before the next run. A streaming computation '
        'holds a nearly flat line close to zero. At four in the afternoon the batch '
        'answer is sixteen hours old and the streamed one is seconds old.">',
        '<text class="fig-title" x="20" y="24">The nightly answer is only fresh at '
        'breakfast</text>',
        '<text class="fig-sub" x="20" y="44">Same question, same data. What differs is how old '
        'the answer is at the moment somebody acts on it.</text>',
        '<text class="fig-box-sub" x="20" y="86">Age of the answer</text>',
        f'<line class="fig-track" x1="{x0}" y1="{base}" x2="{x1}" y2="{base}"/>',
        f'<line class="fig-track" x1="{x0}" y1="{top}" x2="{x1}" y2="{top}"/>',
        f'<text class="fig-box-sub" x="{x1 + 6}" y="{top + 4}">a day</text>',
        f'<text class="fig-box-sub" x="{x1 + 6}" y="{base + 4}">current</text>',
    ]
    # the batch sawtooth: two runs, each ageing for a full day
    saw = (f'M{x0} {base} L{x0 + day:.0f} {top} L{x0 + day:.0f} {base} '
           f'L{x1} {top}')
    p.append(f'<path class="fig-line-b" d="{saw}" fill="none"/>')
    p.append(f'<line class="fig-line-a" x1="{x0}" y1="{base - 6}" x2="{x1}" y2="{base - 6}"/>')
    p.append(f'<text class="fig-box-title" x="{x0 + 12}" y="{top - 10}">Nightly batch</text>')
    p.append(f'<text class="fig-box-title" x="{x0 + 12}" y="{base - 16}">Streamed</text>')
    # the moment of asking: 16:00 on the second day
    ask = x0 + day + day * 16 / 24
    ask_y = base - (base - top) * 16 / 24
    p.append(f'<line class="fig-track" x1="{ask:.0f}" y1="{top - 6}" x2="{ask:.0f}" '
             f'y2="{base + 6}"/>')
    p.append(f'<text class="fig-box-sub" x="{ask:.0f}" y="{top - 14}" '
             f'text-anchor="middle">somebody asks, 16:00</text>')
    p.append(f'<circle class="fig-dot-b" cx="{ask:.0f}" cy="{ask_y:.0f}" r="6"/>')
    p.append(f'<text class="fig-box-sub" x="{ask - 12:.0f}" y="{ask_y + 4:.0f}" '
             f'text-anchor="end">16 hours old</text>')
    p.append(f'<circle class="fig-dot-a" cx="{ask:.0f}" cy="{base - 6}" r="6"/>')
    p.append(f'<text class="fig-box-sub" x="{ask + 12:.0f}" y="{base - 12}">seconds old</text>')
    for i, label in ((0, "midnight"), (1, "midnight"), (2, "midnight")):
        p.append(f'<text class="fig-box-sub" x="{x0 + i * day:.0f}" y="{base + 24}" '
                 f'text-anchor="middle">{label}</text>')
    p.append('<text class="fig-sub" x="20" y="338">A nightly job is not wrong, it is '
             'periodically right. The cost is that nobody in the room knows</text>')
    p.append('<text class="fig-sub" x="20" y="356">how much of today the number in front of '
             'them is missing.</text>')
    p.append("</svg>")
    return "\n".join(p)


def window_shapes():
    """Tumbling, sliding and session windows, side by side. THEMED, static.

    `windowing` on the functions page draws tumbling properly; this one exists to
    make the choice between the three legible, so it stays compact.
    """
    px, pw = (20, 270, 520), 220
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 312" '
        'class="fig-window-shapes" role="img" aria-label="Three panels of the same '
        'stream. Tumbling windows are equal boxes that do not overlap. Sliding windows '
        'overlap, stepping along so a reading falls in several. Session windows hug '
        'bursts of readings and are ended by the quiet between them.">',
        '<text class="fig-title" x="20" y="24">A stream has no end, so a window '
        'manufactures one</text>',
        '<text class="fig-sub" x="20" y="44">Three ways to cut the same readings, answering '
        'three different questions.</text>',
    ]
    heads = (("Tumbling", "what happened in each 15 minutes"),
             ("Sliding", "what has happened in the last 15, now"),
             ("Session", "one box per burst, ended by the quiet"))
    for x, (title, sub) in zip(px, heads):
        p.append(f'<text class="fig-box-title" x="{x}" y="80">{title}</text>')
        p.append(f'<text class="fig-box-sub" x="{x}" y="98">{sub}</text>')

    lane = 172
    # ---- tumbling: four equal boxes, nothing shared
    x = px[0]
    for i in range(4):
        p.append(f'<rect class="fig-centre" x="{x + i * 54 + 2}" y="146" width="50" '
                 f'height="52" rx="8"/>')
    for dx in (14, 30, 46, 70, 96, 118, 140, 158, 182, 200):
        p.append(f'<circle class="fig-dot-a" cx="{x + dx}" cy="{lane}" r="4"/>')
    p.append(f'<text class="fig-box-sub" x="{x}" y="228">every reading in exactly one box,</text>')
    p.append(f'<text class="fig-box-sub" x="{x}" y="244">one answer per box, no overlap</text>')

    # ---- sliding: the same boxes stepped, drawn as a staircase so overlap shows
    x = px[1]
    for i in range(4):
        p.append(f'<rect class="fig-centre" x="{x + i * 34 + 2}" y="{134 + i * 6}" width="86" '
                 f'height="56" rx="8"/>')
    for dx in (14, 30, 46, 70, 96, 118, 140, 158, 182, 200):
        p.append(f'<circle class="fig-dot-a" cx="{x + dx}" cy="{lane}" r="4"/>')
    p.append(f'<text class="fig-box-sub" x="{x}" y="228">boxes overlap, so a reading counts</text>')
    p.append(f'<text class="fig-box-sub" x="{x}" y="244">in several: the answer is always '
             f'current</text>')

    # ---- session: boxes hug the bursts, and the gaps end them
    x = px[2]
    bursts = ((8, 62), (86, 132), (156, 208))
    for a, b in bursts:
        p.append(f'<rect class="fig-centre" x="{x + a}" y="146" width="{b - a}" height="52" '
                 f'rx="8"/>')
    for dx in (14, 26, 38, 54, 94, 106, 122, 164, 178, 196):
        p.append(f'<circle class="fig-dot-a" cx="{x + dx}" cy="{lane}" r="4"/>')
    p.append(f'<text class="fig-box-sub" x="{x}" y="228">boxes of unequal length, because the</text>')
    p.append(f'<text class="fig-box-sub" x="{x}" y="244">process decides when one ends</text>')

    p.append('<text class="fig-sub" x="20" y="286">The window is a claim about the process. '
             'Too short and it reports noise, too long and it reports late,</text>')
    p.append('<text class="fig-sub" x="20" y="304">and the right length is set by how fast the '
             'thing being watched can actually change.</text>')
    p.append("</svg>")
    return "\n".join(p)


def event_time_arrival():
    """When it happened against when it turned up. THEMED, static.

    The industrial case that web-shaped streaming advice never covers: the link
    goes down, and four hours of readings land in one burst. Windowed on arrival
    they invent a quiet morning and a violent afternoon.
    """
    x0, x1 = 150, 720
    t0, t1 = 8.0, 15.0
    top_y, bot_y = 138, 258

    def tx(t):
        return x0 + (t - t0) * (x1 - x0) / (t1 - t0)

    events = [8.0 + 0.75 * i for i in range(9)]      # 08:00 to 14:00, every 45 minutes

    def arrival(t):
        # everything from the outage onward lands together once the link returns,
        # spread only far enough to be counted
        return t + 0.05 if t < 10.25 else 14.08 + (t - 10.25) * 0.22

    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 366" '
        'class="fig-event-time-arrival" role="img" aria-label="Two lanes sharing a time '
        'axis. On the top lane nine readings are evenly spaced from eight to two. On '
        'the bottom lane the first three arrive immediately, then nothing arrives for '
        'four hours while the link is down, and the remaining six land together just '
        'after two. '
        'Connecting lines fan from the top lane into that burst.">',
        '<text class="fig-title" x="20" y="24">When it happened is not when it turned '
        'up</text>',
        '<text class="fig-sub" x="20" y="44">The same nine readings, once by the time they '
        'carry and once by the time they landed.</text>',
        f'<text class="fig-box-title" x="20" y="{top_y + 4}">When it</text>',
        f'<text class="fig-box-title" x="20" y="{top_y + 20}">happened</text>',
        f'<text class="fig-box-title" x="20" y="{bot_y + 4}">When it</text>',
        f'<text class="fig-box-title" x="20" y="{bot_y + 20}">arrived</text>',
        f'<line class="fig-track" x1="{x0}" y1="{top_y}" x2="{x1}" y2="{top_y}"/>',
        f'<line class="fig-track" x1="{x0}" y1="{bot_y}" x2="{x1}" y2="{bot_y}"/>',
    ]
    # the two windows, drawn under the dots
    p.append(f'<rect class="fig-centre" x="{tx(10):.0f}" y="{top_y - 22}" '
             f'width="{tx(14) - tx(10):.0f}" height="44" rx="8"/>')
    p.append(f'<rect class="fig-centre" x="{tx(14):.0f}" y="{bot_y - 22}" '
             f'width="{tx(15) - tx(14):.0f}" height="44" rx="8"/>')
    for t in events:
        p.append(f'<line class="fig-edge" x1="{tx(t):.0f}" y1="{top_y + 8}" '
                 f'x2="{tx(arrival(t)):.0f}" y2="{bot_y - 8}"/>')
    for t in events:
        p.append(f'<circle class="fig-dot-a" cx="{tx(t):.0f}" cy="{top_y}" r="5"/>')
        cls = "fig-dot-b" if t >= 10.0 else "fig-dot-a"
        p.append(f'<circle class="{cls}" cx="{tx(arrival(t)):.0f}" cy="{bot_y}" r="5"/>')
    p.append(f'<text class="fig-box-sub" x="{tx(12):.0f}" y="{top_y - 30}" '
             f'text-anchor="middle">four hours of readings, spread across four hours</text>')
    p.append(f'<text class="fig-box-sub" x="{tx(14.9):.0f}" y="{bot_y - 30}" '
             f'text-anchor="end">the same four hours, inside one window</text>')
    p.append(f'<text class="fig-box-sub" x="{tx(12):.0f}" y="{bot_y + 26}" '
             f'text-anchor="middle">nothing arriving: the link is down</text>')
    for t, label in ((8, "08:00"), (10, "10:00"), (12, "12:00"), (14, "14:00")):
        p.append(f'<text class="fig-box-sub" x="{tx(t):.0f}" y="{bot_y + 52}" '
                 f'text-anchor="middle">{label}</text>')
    p.append('<text class="fig-sub" x="20" y="338">Window on the time a reading carries and '
             'the morning is where it belongs. Window on the time it</text>')
    p.append('<text class="fig-sub" x="20" y="356">arrived and you have invented a quiet morning '
             'and a violent afternoon, out of data containing neither.</text>')
    p.append("</svg>")
    return "\n".join(p)


def sustained_exceedance():
    """Four spikes and one real excursion, through a limit and through a window.

    THEMED, static. The spikes are drawn HIGHER than the sustained excursion on
    purpose: severity is not what the window is judging, duration is, and a
    figure where the real one is also the tallest would make the wrong argument.
    """
    x0, x1, span = 90, 730, 360.0            # six hours across the axis
    limit_y = 175

    def tx(t):
        return x0 + t * (x1 - x0) / span

    def ty(t):
        v = 205 - 6 * math.sin(t / 23.0) - 4 * math.sin(t / 7.5)
        for ts, h, w in ((30, 80, 4.0), (75, 75, 3.4), (140, 85, 4.0), (200, 78, 3.4)):
            v -= h * math.exp(-(((t - ts) / w) ** 2))
        if 245 < t < 335:
            v -= 58 * min(1.0, (t - 245) / 8.0, (335 - t) / 8.0)
        return v

    trace = "M" + " L".join(f"{tx(t):.1f} {ty(t):.1f}" for t in [i * 2 for i in range(181)])
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 396" '
        'class="fig-sustained-exceedance" role="img" aria-label="A pressure trace over '
        'six hours crossing its limit four times in brief spikes and once in a long '
        'excursion. The raw limit alarm fires five times. The windowed rule fires once, '
        'twenty minutes into the long excursion, and not at all for the spikes.">',
        '<text class="fig-title" x="20" y="24">Four of these are noise. One of them is the '
        'pump.</text>',
        '<text class="fig-sub" x="20" y="44">The same readings and the same limit, judged on '
        'one reading at a time and then on the last twenty minutes.</text>',
        '<text class="fig-box-sub" x="20" y="92">Discharge pressure</text>',
        f'<line class="fig-track" x1="{x0}" y1="{limit_y}" x2="{x1}" y2="{limit_y}"/>',
        f'<text class="fig-box-sub" x="{x0 + 4}" y="{limit_y - 6}">limit</text>',
        f'<path class="fig-line-a" d="{trace}" fill="none"/>',
    ]
    for t, label, anchor in ((0, "08:00", "start"), (120, "10:00", "middle"),
                             (240, "12:00", "middle"), (360, "14:00", "end")):
        p.append(f'<text class="fig-box-sub" x="{tx(t):.0f}" y="264" '
                 f'text-anchor="{anchor}">{label}</text>')

    # ---- what a bare limit does with it
    p.append('<text class="fig-box-title" x="20" y="293">Limit alarm</text>')
    for t in (30, 75, 140, 200, 250):
        p.append(f'<rect class="fig-lit-box c-orange" x="{tx(t) - 2:.0f}" y="280" width="5" '
                 f'height="17" rx="2"/>')
    p.append(f'<text class="fig-box-sub" x="{tx(250) + 16:.0f}" y="293">four cleared before '
             f'anybody looked</text>')

    # ---- what the window does with it
    p.append('<text class="fig-box-title" x="20" y="331">Windowed</text>')
    p.append(f'<line class="fig-track" x1="{tx(250):.0f}" y1="326" x2="{tx(270):.0f}" '
             f'y2="326"/>')
    p.append(f'<text class="fig-box-sub" x="{tx(250) - 12:.0f}" y="330" text-anchor="end">the '
             f'window has to fill first</text>')
    p.append(f'<rect class="fig-lit-box c-green" x="{tx(270):.0f}" y="314" width="104" '
             f'height="26" rx="8"/>')
    p.append(f'<text class="fig-lit-sub" x="{tx(270) + 52:.0f}" y="331" '
             f'text-anchor="middle">event raised</text>')
    p.append('<text class="fig-sub" x="20" y="368">The window costs twenty minutes on the '
             'excursion that mattered. It buys the four that did not, and an</text>')
    p.append('<text class="fig-sub" x="20" y="386">alarm the control room has not quietly '
             'switched off.</text>')
    p.append("</svg>")
    return "\n".join(p)


# ================================================================ industry examples
# One figure per example on value/industry-examples.mdx. Each shows the finding that
# example's model makes available, not the architecture underneath it: a total that
# has structure against one that has none, a gap resolved into the units that caused
# it, a reading explained by something upstream and earlier, and so on.

def chemical_accounting():
    """Purchased against metered: the same total, only one of them actionable.

    THEMED, static. The argument of the oil and gas example is that a figure built
    from purchase records is structurally incapable of showing which pump
    over-doses, so the two bars are deliberately the same height.
    """
    base, top = 290, 120
    lx, rx, bw = 60, 260, 110
    # (label, height, class, extra note)
    segs = [
        ("Glycol", 56, None),
        ("Scale inhibitor", 34, None),
        ("Oxygen scavenger", 20, None),
        ("Demulsifier", 30, None),
        ("Biocide", 30, 18),          # 18px of it is dose the process never needed
    ]
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 366" '
        'class="fig-chemical-accounting" role="img" aria-label="Two bars of identical '
        'height. The left one is a single block, the annual chemical figure taken from '
        'purchase records. The right one is the same quantity split by chemical and by '
        'injection point, and the topmost band is marked as dose above what the process '
        'needs.">',
        '<text class="fig-title" x="20" y="24">The same total, twice. Only one of them can be '
        'acted on.</text>',
        '<text class="fig-sub" x="20" y="44">A figure assembled from what was bought cannot show '
        'that one pump has been over-dosing for a year.</text>',
        f'<text class="fig-box-title" x="20" y="78">What was purchased</text>',
        f'<text class="fig-box-sub" x="20" y="96">invoiced, accurate, and silent</text>',
        f'<text class="fig-box-title" x="260" y="78">What was metered</text>',
        f'<text class="fig-box-sub" x="260" y="96">the same quantity, with structure</text>',
        f'<rect class="fig-lit-box c-blue" x="{lx}" y="{top}" width="{bw}" '
        f'height="{base - top}" rx="10"/>',
        f'<text class="fig-box-sub" x="{lx + bw // 2}" y="310" text-anchor="middle">one number, '
        f'no structure</text>',
        f'<text class="fig-sep" x="200" y="215" text-anchor="middle">=</text>',
        f'<text class="fig-box-sub" x="{rx + bw // 2}" y="310" text-anchor="middle">per chemical, '
        f'per injection point</text>',
    ]
    y = base
    for label, h, waste in segs:
        y -= h
        p.append(f'<rect class="fig-box" x="{rx}" y="{y}" width="{bw}" height="{h}" rx="4"/>')
        if waste:
            # the only coloured band in the figure is the part nobody needed
            p.append(f'<rect class="fig-lit-box c-orange" x="{rx}" y="{y}" width="{bw}" '
                     f'height="{waste}" rx="4"/>')
        mid = y + (waste // 2 if waste else h // 2)
        p.append(f'<line class="fig-edge" x1="{rx + bw}" y1="{mid}" x2="{rx + bw + 24}" '
                 f'y2="{mid}"/>')
        if waste:
            p.append(f'<text class="fig-box-title" x="{rx + bw + 32}" y="{mid - 2}">{label}'
                     f'</text>')
            p.append(f'<text class="fig-box-sub" x="{rx + bw + 32}" y="{mid + 14}">the shaded '
                     f'band is dose the process never needed</text>')
        else:
            p.append(f'<text class="fig-box-sub" x="{rx + bw + 32}" y="{mid + 4}">{label}</text>')
    p.append('<text class="fig-sub" x="20" y="338">Both bars are the same height and both are '
             'honest. Only the right-hand one says where any of it</text>')
    p.append('<text class="fig-sub" x="20" y="356">went, which is the difference between a number '
             'you can defend and one you can improve.</text>')
    p.append("</svg>")
    return "\n".join(p)


def shortfall_attribution():
    """Yesterday's capacity gap, resolved into the units that caused it. THEMED.

    Two things share one time axis: the gap on top, the units and their events
    underneath. The alignment IS the claim, so nothing here animates.
    """
    x0, x1 = 180, 740
    hours = 12.0                     # 10:00 to 22:00 across the axis

    def tx(h):
        return x0 + (h - 10.0) * (x1 - x0) / hours

    def demand(h):
        return 210 - 1.3 * (20 + 70 * math.sin(math.pi * (h - 8.0) / 18.0))

    def delivered(h):
        y = demand(h)
        if 14.0 <= h <= 18.3:
            y += 1.3 * 40 * math.sin(math.pi * (h - 14.0) / 4.3)
        return y

    def curve(fn, lo=10.0, hi=22.0):
        pts = []
        h = lo
        while h <= hi + 0.01:
            pts.append(f"{tx(h):.1f} {fn(h):.1f}")
            h += 0.25
        return "M" + " L".join(pts)

    # the gap itself, drawn first so both lines sit on top of it
    gap = (curve(demand, 14.0, 18.3)
           + " L" + " L".join(f"{tx(h):.1f} {delivered(h):.1f}"
                              for h in [18.3 - i * 0.25 for i in range(18)] + [14.0])
           + " z")
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 384" '
        'class="fig-shortfall-attribution" role="img" aria-label="An afternoon demand '
        'curve with delivered output falling below it between two and six in the '
        'afternoon, and three rows underneath on the same time axis showing which units '
        'were unavailable and what was raised against them.">',
        '<text class="fig-title" x="20" y="24">A shortfall is a number. Which assets made it is a '
        'traversal.</text>',
        '<text class="fig-sub" x="20" y="44">One afternoon, one axis: the gap on top, and what was '
        'happening underneath it.</text>',
        f'<path class="fig-centre" d="{gap}"/>',
        f'<path class="fig-line-b" d="{curve(delivered)}" fill="none"/>',
        # demand drawn last and dashed: where the two coincide you can see that they do
        f'<path class="fig-line-a fig-line--ghost" d="{curve(demand)}" fill="none"/>',
        '<text class="fig-box-sub" x="20" y="86">Demand against delivered</text>',
        f'<text class="fig-box-sub" x="{tx(16.15):.0f}" y="{demand(16.15) - 12:.0f}" '
        f'text-anchor="middle">demand</text>',
        f'<text class="fig-box-sub" x="{tx(16.15):.0f}" y="{delivered(16.15) + 20:.0f}" '
        f'text-anchor="middle">delivered</text>',
        f'<text class="fig-box-title" x="{tx(18.7):.0f}" y="{(demand(16.15) + delivered(16.15)) / 2:.0f}">'
        f'the shortfall</text>',
        '<text class="fig-box-title" x="20" y="240">What the model says was underneath it</text>',
    ]
    rows = (
        ("GT-2", "tripped 13:58, back at 18:20", 14.0, 18.3, 258, True),
        ("GT-5", "derated to 60% on ambient", 12.0, 20.0, 294, False),
        ("BESS-1", "fully discharged 15:20", 15.3, 18.0, 330, True),
    )
    for name, note, hs, he, y, out in rows:
        p.append(f'<text class="fig-box-title" x="20" y="{y + 17}">{name}</text>')
        p.append(f'<line class="fig-track" x1="{x0}" y1="{y + 12}" x2="{x1}" y2="{y + 12}"/>')
        # a filled bar is an outage, an outlined one a derate: they cost different amounts
        cls = "fig-lit-box c-orange" if out else "fig-box"
        t_cls = "fig-lit-sub" if out else "fig-box-sub"
        p.append(f'<rect class="{cls}" x="{tx(hs):.0f}" y="{y}" '
                 f'width="{tx(he) - tx(hs):.0f}" height="24" rx="7"/>')
        p.append(f'<text class="{t_cls}" x="{tx(hs) + 10:.0f}" y="{y + 16}">{note}</text>')
    for h, label in ((12, "12:00"), (15, "15:00"), (18, "18:00"), (21, "21:00")):
        p.append(f'<text class="fig-box-sub" x="{tx(h):.0f}" y="374" '
                 f'text-anchor="middle">{label}</text>')
    p.append("</svg>")
    return "\n".join(p)


def excursion_upstream():
    """An effluent excursion explained by a stage upstream and hours earlier.

    THEMED. The only motion is `fig-flow` along the propagation path, which is the
    house exception: it shows direction continuously without hiding anything.
    """
    x0, x1 = 190, 730
    t0, t1 = 6.0, 15.0

    def tx(h):
        return x0 + (h - t0) * (x1 - x0) / (t1 - t0)

    stages = (("Intake", 104), ("Primary settling", 142), ("Aeration", 180),
              ("Clarifier", 218), ("Outfall", 256))
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 334" '
        'class="fig-excursion-upstream" role="img" aria-label="Five treatment stages as '
        'rows against a morning time axis. A blower swap on the aeration stage at ten '
        'past six, a rising sludge blanket on the clarifier at half past nine, and a '
        'turbidity excursion at the outfall at twenty to twelve, joined by a path '
        'running down the stages and forward in time.">',
        '<text class="fig-title" x="20" y="24">The reading that fails is downstream, and '
        'late</text>',
        '<text class="fig-sub" x="20" y="44">Same morning, five stages. What the model adds is '
        'the chain and the delay between them.</text>',
    ]
    for name, y in stages:
        p.append(f'<text class="fig-box-sub" x="20" y="{y + 4}">{name}</text>')
        p.append(f'<line class="fig-track" x1="{x0}" y1="{y}" x2="{x1}" y2="{y}"/>')
    # the propagation path: down the stages, forward in time
    p.append(f'<path class="fig-exit-path fig-flow" d="M{tx(6.2):.0f} 180 '
             f'L{tx(9.5):.0f} 218 L{tx(11.7):.0f} 256" fill="none"/>')
    marks = (
        (6.2, 180, "blower B swapped, 06:10", "fig-lit-box c-orange", False),
        (9.5, 218, "sludge blanket rising, 09:30", "fig-lit-box c-orange", False),
        (11.7, 256, "turbidity above limit, 11:40", "fig-lit-box c-orange", True),
    )
    for h, y, label, cls, big in marks:
        r = 9 if big else 6
        p.append(f'<circle class="{cls}" cx="{tx(h):.0f}" cy="{y}" r="{r}"/>')
        p.append(f'<text class="fig-box-sub" x="{tx(h) + 16:.0f}" y="{y - 12}">{label}</text>')
    p.append(f'<text class="fig-box-sub" x="{tx(9.0):.0f}" y="{292}" text-anchor="middle">'
             f'five and a half hours, and three stages, between cause and reading</text>')
    for h, label in ((6, "06:00"), (8, "08:00"), (10, "10:00"), (12, "12:00"), (14, "14:00")):
        p.append(f'<text class="fig-box-sub" x="{tx(h):.0f}" y="{276}" '
                 f'text-anchor="middle">{label}</text>')
    p.append('<text class="fig-sub" x="20" y="324">Without the chain, the excursion belongs to '
             'the outfall, which is the one place it did not come from.</text>')
    p.append("</svg>")
    return "\n".join(p)


def defect_attribution():
    """Defects plotted against the station and the material lot. THEMED, static.

    The cluster only exists once each defect is attached to what made it: the same
    dots against a calendar are a defect rate, and against the model they are one
    machine and one delivery.
    """
    cols = ("Mon A", "Mon B", "Tue A", "Tue B", "Wed A", "Wed B")
    x0, cw = 150, 98
    rows = ("ST-1", "ST-2", "ST-3", "ST-4", "ST-5")
    ry0, rh = 140, 35
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 362" '
        'class="fig-defect-attribution" role="img" aria-label="A grid of five stations '
        'against six shifts, with defects as dots. Dots are scattered thinly everywhere '
        'except where the fourth station meets the two shifts that ran material lot B, '
        'where they cluster.">',
        '<text class="fig-title" x="20" y="24">The same defects, plotted against what made '
        'them</text>',
        '<text class="fig-sub" x="20" y="44">A defect count says there is a problem. Attached to '
        'a station and a material lot, the dots say whose.</text>',
        f'<rect class="fig-centre" x="{x0 + 2 * cw}" y="112" width="{2 * cw}" height="188" '
        f'rx="10"/>',
        f'<text class="fig-centre-sub" x="{x0 + 3 * cw}" y="130" text-anchor="middle">material '
        f'lot B</text>',
    ]
    for i, c in enumerate(cols):
        p.append(f'<text class="fig-box-sub" x="{x0 + i * cw + cw // 2}" y="320" '
                 f'text-anchor="middle">{c}</text>')
    for r, name in enumerate(rows):
        y = ry0 + r * rh
        p.append(f'<text class="fig-box-title" x="20" y="{y + 4}">{name}</text>')
        p.append(f'<line class="fig-track" x1="{x0}" y1="{y}" x2="{x0 + 6 * cw}" y2="{y}"/>')
    # background defects: thin and everywhere
    bg = ((0, 0, 22), (0, 3, 61), (1, 1, 40), (1, 4, 18), (2, 0, 74), (2, 5, 33),
          (3, 0, 56), (3, 5, 70), (4, 1, 27), (4, 2, 66), (4, 4, 44), (0, 5, 12))
    for r, c, off in bg:
        p.append(f'<circle class="fig-dot-a" cx="{x0 + c * cw + off}" cy="{ry0 + r * rh}" '
                 f'r="4"/>')
    # The cluster: one station, the two shifts that ran lot B. Spacing is uneven on
    # purpose; a perfectly regular row of dots reads as a pattern somebody drew.
    cluster = ((2, 12), (2, 31), (2, 58), (2, 86), (3, 8), (3, 20), (3, 47), (3, 78))
    for c, off in cluster:
        p.append(f'<circle class="fig-dot-b" cx="{x0 + c * cw + off}" cy="{ry0 + 3 * rh}" '
                 f'r="4"/>')
    p.append(f'<text class="fig-box-sub" x="{x0 + 4 * cw + 12}" y="{ry0 + 3 * rh - 6}">one '
             f'station, one lot</text>')
    p.append('<text class="fig-sub" x="20" y="336">On a weekly report these are one defect '
             'rate. Against the station that made each unit, and the lot it</text>')
    p.append('<text class="fig-sub" x="20" y="354">came from, they are a question with an '
             'answer.</text>')
    p.append("</svg>")
    return "\n".join(p)


def incident_path():
    """A degradation at 14:20, and the deploy twenty minutes before it. THEMED.

    The chart carries the timing and the chain carries the explanation; either
    alone is what an operations team already has.
    """
    x0, x1 = 150, 740
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 362" '
        'class="fig-incident-path" role="img" aria-label="A latency trace that steps up '
        'at twenty past two, with a marker at two o clock for a deploy, and beneath it a '
        'chain from the degraded service through its host, a storage array with rising '
        'errors, a switch dropping packets, to that deploy.">',
        '<text class="fig-title" x="20" y="24">Twenty minutes apart, and four hops '
        'away</text>',
        '<text class="fig-sub" x="20" y="44">The chart says when. The chain says what, and it is '
        'the same walk every time.</text>',
        '<text class="fig-box-sub" x="20" y="88">Checkout latency</text>',
    ]
    # latency: flat, then a step up that stays up
    step = 470
    pts = []
    for i in range(61):
        x = x0 + i * (x1 - x0) / 60
        wob = (-2, 1, 2, -1, 0, 2, -2, 1, 1, -2, 0, 2)[i % 12]
        y = 150 + wob if x < step else 108 + wob
        pts.append(f"{x:.0f} {y}")
    p.append(f'<path class="fig-line-a" d="M{" L".join(pts)}" fill="none"/>')
    p.append(f'<line class="fig-line-b" x1="{step - 78}" y1="96" x2="{step - 78}" y2="176"/>')
    p.append(f'<text class="fig-box-sub" x="{step - 84}" y="{92}" text-anchor="end">deploy 918, '
             f'14:00</text>')
    p.append(f'<line class="fig-track" x1="{step}" y1="96" x2="{step}" y2="176"/>')
    p.append(f'<text class="fig-box-sub" x="{step + 6}" y="{92}">latency steps up, 14:20</text>')

    chain = (("Checkout", "degraded"), ("host-14", "hosting it"), ("array-3", "errors climbing"),
             ("sw-04", "dropping packets"), ("deploy 918", "went out at 14:00"))
    bw, gap, cy = 128, 18, 234
    for i, (title, sub) in enumerate(chain):
        x = 20 + i * (bw + gap)
        cls = "fig-lit-box c-blue" if i == 0 else "fig-box"
        t = "fig-lit-title" if i == 0 else "fig-box-title"
        s = "fig-lit-sub" if i == 0 else "fig-box-sub"
        p.append(f'<rect class="{cls}" x="{x}" y="{cy}" width="{bw}" height="54" rx="12"/>')
        p.append(f'<text class="{t}" x="{x + bw // 2}" y="{cy + 24}" '
                 f'text-anchor="middle">{title}</text>')
        p.append(f'<text class="{s}" x="{x + bw // 2}" y="{cy + 42}" '
                 f'text-anchor="middle">{sub}</text>')
        if i < len(chain) - 1:
            p.append(f'<path class="fig-exit-path fig-flow" d="M{x + bw} {cy + 27} '
                     f'L{x + bw + gap} {cy + 27}" fill="none"/>')
    p.append('<text class="fig-box-sub" x="20" y="216">start at the symptom</text>')
    p.append('<text class="fig-sub" x="20" y="326">Every hop is a relationship somebody recorded '
             'once. The alternative is four people in a call, each</text>')
    p.append('<text class="fig-sub" x="20" y="344">holding one hop of it in their head.</text>')
    p.append("</svg>")
    return "\n".join(p)


def usage_vs_calendar():
    """Two identical vehicles, one deployed, both serviced on the same calendar.

    THEMED, static. The finding lives in the gap between the two lines, so the
    quantity plotted is cumulative running hours rather than anything prettier.
    """
    x0, x1, base, top = 90, 720, 288, 110
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 372" '
        'class="fig-usage-vs-calendar" role="img" aria-label="Cumulative running hours '
        'over a year for two identical vehicles. The deployed one climbs steeply and '
        'crosses two service intervals; the one held in reserve barely climbs and '
        'crosses none. Along the bottom, four calendar services fall on both of them '
        'alike.">',
        '<text class="fig-title" x="20" y="24">Two identical vehicles. One of them '
        'deployed.</text>',
        '<text class="fig-sub" x="20" y="44">A calendar cannot tell them apart. Hours, cycles and '
        'conditions can.</text>',
        '<text class="fig-box-sub" x="20" y="86">Cumulative running hours</text>',
        f'<line class="fig-track" x1="{x0}" y1="{base}" x2="{x1}" y2="{base}"/>',
    ]
    # two service thresholds
    for level, label in ((0.42, "600 h"), (0.84, "1200 h")):
        y = base - (base - top) * level
        p.append(f'<line class="fig-track" x1="{x0}" y1="{y:.0f}" x2="{x1}" y2="{y:.0f}"/>')
        p.append(f'<text class="fig-box-sub" x="{x1 + 6}" y="{y + 4:.0f}">{label}</text>')

    def line(frac_end, cls):
        pts = []
        for i in range(13):
            x = x0 + i * (x1 - x0) / 12
            v = frac_end * (i / 12) ** 1.04
            pts.append(f"{x:.0f} {base - (base - top) * v:.1f}")
        return f'<path class="{cls}" d="M{" L".join(pts)}" fill="none"/>'

    p.append(line(0.96, "fig-line-a"))
    p.append(line(0.22, "fig-line-b"))
    p.append(f'<text class="fig-box-title" x="{x1 - 4}" y="{base - (base - top) * 0.96 - 12:.0f}" '
             f'text-anchor="end">Vehicle A, deployed</text>')
    p.append(f'<text class="fig-box-title" x="{x1 - 4}" y="{base - (base - top) * 0.22 - 12:.0f}" '
             f'text-anchor="end">Vehicle B, in reserve</text>')
    # where A actually crosses each threshold
    for level, label, dx, dy, anchor in ((0.42, "A crosses it here", -14, -14, "end"),
                                         (0.84, "and again here", 14, 20, "start")):
        frac = (level / 0.96) ** (1 / 1.04)
        x = x0 + frac * (x1 - x0)
        y = base - (base - top) * level
        p.append(f'<circle class="fig-box" cx="{x:.0f}" cy="{y:.0f}" r="9"/>')
        p.append(f'<circle class="fig-dot-a" cx="{x:.0f}" cy="{y:.0f}" r="4.5"/>')
        p.append(f'<text class="fig-box-sub" x="{x + dx:.0f}" y="{y + dy:.0f}" '
                 f'text-anchor="{anchor}">{label}</text>')
    # the calendar, applied to both regardless
    for i in (3, 6, 9, 12):
        x = x0 + i * (x1 - x0) / 12
        p.append(f'<line class="fig-edge" x1="{x:.0f}" y1="{base + 6}" x2="{x:.0f}" '
                 f'y2="{base + 20}"/>')
    p.append(f'<text class="fig-box-sub" x="{x0}" y="{base + 38}">calendar service, four times, '
             f'both vehicles, whatever they did</text>')
    p.append('<text class="fig-sub" x="20" y="348">A was serviced on neither occasion that '
             'mattered, B four times without needing it, and on paper</text>')
    p.append('<text class="fig-sub" x="20" y="366">they are the same vehicle with the same '
             'maintenance record.</text>')
    p.append("</svg>")
    return "\n".join(p)


THEMED_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "src", "figures")

# Files in static/ are served as-is and loaded with <img>: self-contained, but
# blind to the site's theme toggle, so they sit in an always-light frame.
STATIC_FIGURES = (
    ("traversal.svg", traversal),
    ("lead-lag.svg", lead_lag),
    ("compounding-gap.svg", compounding_gap),
    ("token-bridge.svg", token_bridge),
)
# Files in src/figures/ are inlined into the page by SVGR, so page CSS reaches
# them and they follow the theme toggle. They carry classes, never colours.
THEMED_FIGURES = (
    ("agent-loop.svg", agent_loop),
    ("experiment-rate.svg", experiment_rate),
    ("industrial-revolutions.svg", industrial_revolutions),
    ("tag-anatomy.svg", tag_anatomy),
    ("lineage-trace.svg", lineage_trace),
    ("decision-tempo.svg", decision_tempo),
    ("board-gates.svg", board_gates),
    ("value-plays.svg", value_plays),
    ("subscription-flow.svg", subscription_flow),
    ("data-governance.svg", data_governance),
    ("policy-enforcement.svg", policy_enforcement),
    ("policy-agents.svg", policy_agents),
    ("cleaning-by-correlation.svg", cleaning_by_correlation),
    ("feature-extraction.svg", feature_extraction),
    ("windowing.svg", windowing),
    ("event-detection.svg", event_detection),
    ("events-from-series.svg", events_from_series),
    ("function-wiring.svg", function_wiring),
    ("detection-to-action.svg", detection_to_action),
    ("revolution-contrast.svg", revolution_contrast),
    ("famous-vs-foundation.svg", famous_vs_foundation),
    ("function-branching.svg", function_branching),
    ("liberation-translate.svg", liberation_translate),
    ("resource-anatomy.svg", resource_anatomy),
    ("digital-twin-mirror.svg", digital_twin_mirror),
    ("agent-organisation.svg", agent_organisation),
    ("aliasing-illusion.svg", aliasing_illusion),
    ("mcp-one-protocol.svg", mcp_one_protocol),
    ("mcp-call-path.svg", mcp_call_path),
    ("agent-guardrails.svg", agent_guardrails),
    ("agent-graph-join.svg", agent_graph_join),
    ("wind-peer-comparison.svg", wind_peer_comparison),
    ("vessel-sisters.svg", vessel_sisters),
    ("blast-radius-cooling.svg", blast_radius_cooling),
    ("readiness-gate.svg", readiness_gate),
    ("issuer-neighbourhood.svg", issuer_neighbourhood),
    ("ward-devices.svg", ward_devices),
    ("agent-anatomy.svg", agent_anatomy),
    ("dirty-data.svg", dirty_data),
    ("feature-flywheel.svg", feature_flywheel),
    ("features-on-image.svg", features_on_image),
    ("synthetic-and-measured.svg", synthetic_and_measured),
    ("measured-vs-generated.svg", measured_vs_generated),
    ("robot-learning-loop.svg", robot_learning_loop),
    ("rules-vs-learning.svg", rules_vs_learning),
    ("ml-progression.svg", ml_progression),
    ("tree-ensembles.svg", tree_ensembles),
    ("clustering.svg", clustering),
    ("k-means-steps.svg", k_means_steps),
    ("neural-network.svg", neural_network),
    ("lstm-sequence-anomaly.svg", lstm_sequence_anomaly),
    ("text-sequence-intent.svg", text_sequence_intent),
    ("answer-age.svg", answer_age),
    ("sustained-exceedance.svg", sustained_exceedance),
    ("window-shapes.svg", window_shapes),
    ("event-time-arrival.svg", event_time_arrival),
    ("chemical-accounting.svg", chemical_accounting),
    ("shortfall-attribution.svg", shortfall_attribution),
    ("excursion-upstream.svg", excursion_upstream),
    ("defect-attribution.svg", defect_attribution),
    ("incident-path.svg", incident_path),
    ("usage-vs-calendar.svg", usage_vs_calendar),
)

if __name__ == "__main__":
    for out_dir, figures in ((OUT, STATIC_FIGURES), (THEMED_OUT, THEMED_FIGURES)):
        os.makedirs(out_dir, exist_ok=True)
        for name, fn in figures:
            svg = fn()
            with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
                fh.write(svg)
            where = os.path.relpath(out_dir, os.path.dirname(os.path.dirname(out_dir)))
            print(f"wrote {name} ({len(svg)} bytes) -> {where}")
