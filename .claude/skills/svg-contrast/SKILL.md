---
name: svg-contrast
description: Check that text in SVG files has sufficient contrast against whatever is actually behind it, including CSS-class-styled and animated SVGs, and including light/dark theme variants. Use when authoring, reviewing or fixing SVG diagrams and figures, when text in a diagram may be hard to read, or after changing a figure's palette or theme variables. Triggers on "svg contrast", "is this diagram readable", "check figure colours", "text on dark background", "WCAG contrast in svg", "diagram accessibility".
---

# SVG text contrast

Checks one thing and checks it properly: **can the text in an SVG be read against what
is behind it.** Nothing else — not colour harmony, not layout, not accessibility in
general.

## When to use this

- After writing or editing any SVG figure
- After changing a palette, a CSS variable, or a theme
- When someone reports a diagram is hard to read
- Before publishing figures that appear in both light and dark themes

## Run it

```bash
python3 .claude/skills/svg-contrast/check_svg_contrast.py <svg files...> [options]
```

Options:

| Option | Purpose |
| --- | --- |
| `--css FILE` | Stylesheet(s) that colour the SVG. Required for class-styled figures that carry no inline colour. Repeatable. |
| `--theme light\|dark\|both` | Which theme's custom-property values to resolve. Default `both`. |
| `--page-bg COLOR` | What sits behind the SVG when no shape does. Defaults per theme. |
| `--min-ratio N` | Override the pass threshold. Default follows WCAG: 4.5, or 3.0 for large text. |
| `--quiet` | Only print failures. |

Examples:

```bash
# self-contained SVG with inline colours
python3 .claude/skills/svg-contrast/check_svg_contrast.py static/img/figures/*.svg

# themed figures whose colours live in the site stylesheet, both themes
python3 .claude/skills/svg-contrast/check_svg_contrast.py src/figures/*.svg \
    --css src/css/custom.css --theme both
```

## What it understands

- **Inline paint** — `fill` on the element or inherited from an ancestor `<g>`.
- **CSS classes** — parses the given stylesheets plus any `<style>` inside the SVG,
  and resolves `var(--x)` custom properties, including `[data-theme='dark']` overrides
  so a figure is checked in each theme.
- **Real stacking** — the background of a text run is the *topmost shape that actually
  sits under it in paint order*, found geometrically, not the first shape in the file.
- **Large-text thresholds** — 3.0 instead of 4.5 at ≥24px, or ≥18.66px when bold.

### Animation

This is where naive checkers give false passes, so it handles three cases:

1. **Animated opacity on the background.** A shape that fades in is evaluated at
   *both* ends — text must stay readable while the shape is absent AND present.
2. **Fade-over stacks.** If text is painted underneath a shape that later fades in on
   top of it, the two are visible simultaneously mid-transition. That is reported as
   `OVERLAP`, because it is the defect that produces "dark text showing through a
   coloured box".
3. **Animated fill.** A `fill` that changes via CSS animation or `<animate>` is
   evaluated at every declared keyframe value.

## Reading the output

Each finding names the file, the text, the two colours, the ratio and the verdict:

```
FAIL  traversal.svg:  "Checkout"  #ffffff on #169a4f  ratio 3.03  (needs 4.5)
OVERLAP traversal.svg: "Billing" (#1d2b36) can show through animated overlay fill #169a4f
```

Exit code is non-zero if anything failed, so it works in a pre-commit hook or CI.

## Fixing what it finds

- **White label on a mid-tone accent** — darken the *fill*, do not lighten the text.
  Brand accents are usually display colours; a text-bearing fill needs a darker variant.
- **`OVERLAP`** — do not stack differently-coloured text. Either fade the base layer out
  as the overlay fades in, or draw one element whose fill animates.
- **Muted label on a light background** — muted greys are frequently below 4.5 even
  though they look fine to the author on a good monitor.
- **Passes in light, fails in dark** — the theme's variable needs its own value, not a
  shared one.
