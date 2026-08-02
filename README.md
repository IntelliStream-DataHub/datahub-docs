# IntelliStream DataHub user documentation

The user-facing documentation site for the **IntelliStream DataHub platform**: what it is,
how to use it, how to create business value with it, and how to administer it.

Written for readers who are **not developers**: engineers, operations staff, domain
experts, and leadership or board members in traditional industry. Developer and API material
lives in the separate [`datahub-sdk-docs`](../datahub-sdk-docs) site.

Built with [Docusaurus](https://docusaurus.io/) 3, using the same IntelliStream brand skin as
the SDK docs.

> **Working on this repo?** Read [AGENT.md](AGENT.md) first. It records the conventions, the
> traps that have already cost time, and, most importantly, which claims in the docs are
> known to be inaccurate and still need correcting.

## Running it

```bash
npm install      # first time
npm start        # dev server with hot reload, http://localhost:3000
npm run build    # production build into build/
npm run serve    # serve the production build locally
```

Requires Node 20 or newer. Node 22 is installed on this host.

> **Keep every `@docusaurus/*` package on the same version.** If they drift, even by a
> patch, e.g. `theme-common` at 3.10.2 while `core` is pinned at 3.10.1, the Mermaid
> renderer fails during static generation with
> `Hook useColorMode is called outside the <ColorModeProvider>`, and the build dies on the
> pages containing diagrams. Bump them together.

Mermaid diagrams render **client-side**: the static HTML contains an empty placeholder and
the SVG is drawn in the browser into `div.docusaurus-mermaid-container`. Diagrams being
absent from built HTML is expected, not a failure, but note that a diagram with invalid
syntax fails silently in the browser rather than breaking the build, so check diagrams
visually after editing them.

## Structure

Docs are served at the site root (GitBook-style, no `/docs` prefix). The sidebar is generated
from the folder tree; ordering comes from `position` in each `_category_.json` and
`sidebar_position` in page front matter.

| Folder | Audience | Covers |
| --- | --- | --- |
| `docs/intro.mdx` | Everyone | Landing page and the four reading paths |
| `docs/start/` | Newcomers, leadership | What DataHub is, the data problem, the four building blocks, first hour, roles |
| `docs/concepts/` | Domain experts, engineers | Ontology, taxonomy, knowledge graphs, the three model layers, naming standards, lineage, modelling workshops |
| `docs/using/` | Daily users | Console tour, data sets, resource graph, time series, insights, relationship analysis, events, files, streams |
| `docs/value/` | Leadership, sponsors | Business case, where to start, value paths, measuring return, board briefing, industry examples |
| `docs/administration/` | Administrators | Install, tenants, users, permissions, data lifecycle, architecture, security |
| `docs/reference/` | Everyone | Glossary and FAQ |

## Writing conventions

The site follows a **progressive disclosure** pattern, a plain answer first, links to the
detail underneath. Every page should:

1. Open with a `<Lead>` sentence or a `<KeyIdea>` box giving the one-minute answer.
2. Keep the body short and concrete, with tables over prose where a table fits.
3. End with a `<Deeper>` block linking onward.
4. Define any term at first use, or link to `/reference/glossary`.

**Never name a competitor.** Where the category's public evidence is relevant, describe the
results without attributing them to a vendor or a named customer.

### Components

Registered globally in `src/theme/MDXComponents.js` (defined in `src/components/DocsUI.jsx`),
so no import line is needed in `.mdx`:

| Component | Use |
| --- | --- |
| `<Lead>` | One-sentence framing under the page title |
| `<KeyIdea title="…">` | The "in one minute" box at the top of a page |
| `<Cards wide>` / `<Card title to icon eyebrow>` | Click-through navigation grid |
| `<Deeper title="…">` | The "go deeper" link list at the foot of a page |
| `<Personas>` / `<Persona primary>` | "Who this page is for" chips |
| `<Stats>` / `<Stat value label note>` | Headline figures |
| `<Steps>` / `<Step title>` | Numbered walkthroughs |

### Diagrams and figures

There are three kinds, and picking the right one matters:

| Kind | Where it lives | Use when |
| --- | --- | --- |
| **Mermaid** | A ```` ```mermaid ```` block in the page | A quick structural diagram where layout does not need controlling |
| **Static SVG** | `static/img/figures/*.svg`, shown with `<Figure src="…">` | A self-contained illustration, including the brand SVGs reused from the marketing site |
| **Themed inline SVG** | `src/figures/*.svg`, imported and passed as `<Figure>` children | Anything animated, or anything that must follow the site's light/dark toggle |

#### Why themed figures are inlined

An SVG loaded through `<img>` is an isolated document. It cannot see the page's
`data-theme` attribute, the most it can react to is the operating system's
`prefers-color-scheme`, which **disagrees with the site's theme toggle** whenever a reader
overrides their OS preference. So anything that needs to match the page is inlined by SVGR
instead, which puts its elements in the page's own DOM where the site CSS reaches them.

The rule that makes this work: **a file in `src/figures/` contains geometry and class names,
never colour.** No `<style>` block, no `fill="#…"`, no `stroke="#…"`, the only literal
permitted is `fill="none"`. Palette *and* animation live in `src/css/custom.css`, under
`:root` / `[data-theme='dark']`. `scripts/check-docs.py` enforces this.

Usage:

```mdx
import AgentLoop from '@site/src/figures/agent-loop.svg';

<Figure caption="What the diagram adds beyond its title." wide>
  <AgentLoop />
</Figure>
```

#### Available figure classes

Defined in `custom.css`, so a new figure normally needs no new CSS at all:

- **Text**: `fig-title`, `fig-sub`, `fig-box-title`, `fig-box-sub`, `fig-centre-title`,
  `fig-centre-sub`, `fig-lit-title`, `fig-lit-sub`, `fig-exit-title`, `fig-exit-sub`,
  `fig-exit-note`
- **Shapes**: `fig-box`, `fig-lit-box` + `c-blue`/`c-orange`/`c-green`, `fig-centre`,
  `fig-track`, `fig-token`, `fig-exit-box`, `fig-exit-path`
- **Animation**: `fig-seq` + `fig-d1`…`fig-d6` (staggered reveal on a shared 8s loop),
  `fig-flow` (marching dashes), `fig-pulse`, `fig-draw` (stroke draws itself in)

All loops share an 8-second cycle so several figures on one page stay in sympathy, and every
animation is disabled under `prefers-reduced-motion`.

Accent **fills** are deliberately darker than the brand colours (`#c2551a`, not `#f6783c`)
because white label text on the raw brand orange sits near 2.6:1. The `--fig-fill-*`
variables clear 4.5:1 in both themes, use them rather than the `--is-*` brand values for
anything with text on top.

#### Generated figures

`scripts/make-figures.py` generates several figures programmatically, which is worth it where
geometry needs computing (sine waves, points on a circle, chart coordinates):

```bash
python3 scripts/make-figures.py
```

It writes static figures to `static/img/figures/` and themed ones to `src/figures/`. When
laying out boxes, **compute the edges**, the first version of the agent-loop diagram had its
centre box overlapping the left and right stations because the radius did not clear
half-centre + half-station + a gap.

### Emphasis and colour

Use `**bold**` for the terms that carry a sentence, and the colour helpers from
`src/css/custom.css` sparingly, one or two per paragraph, on words a reader should be able
to find by scanning:

```html
<span className="t-brand">brand blue</span>
<span className="t-accent">accent orange</span>
<span className="t-success">green</span>
<span className="hl">highlighted term</span>
```

The `--doc-*-text` variables are darkened variants of the raw brand colours so inline text
clears 4.5:1 contrast in both light and dark themes. Use those, not `--is-orange` directly,
for anything made of words.

## Checking your changes

`npm run build` fails on MDX errors and warns on broken links. Three Python checkers cover
what the build cannot, and none of them need Node:

```bash
# internal links, heading anchors, static assets, themed-figure conventions
python3 scripts/check-docs.py

# text or shapes spilling outside a figure's viewBox
python3 scripts/check-figures.py 'static/img/figures/*.svg' 'src/figures/*.svg' \
    --css src/css/custom.css

# text contrast against whatever is actually behind it, in both themes
python3 .claude/skills/svg-contrast/check_svg_contrast.py 'src/figures/*.svg' \
    --css src/css/custom.css --theme both
python3 .claude/skills/svg-contrast/check_svg_contrast.py 'static/img/figures/*.svg' \
    --theme light
```

The last two exist because SVG fails silently: an over-wide label is simply clipped, and
low-contrast text renders perfectly happily. Both defects shipped during authoring before
these were written. See `.claude/skills/svg-contrast/SKILL.md` for what the contrast checker
understands, including animated stacks.

Known remaining: `static/img/figures/knowledge-graph-oilgas.svg` has relationship labels at
4.37–4.38 against the 4.5 threshold. It is imported unchanged from `intellistream-web`, so
the fix belongs upstream rather than in a local fork.

## Deployment

This site publishes at **https://intellistream.ai/documentation**, so
`docusaurus.config.js` sets `url: https://intellistream.ai` and `baseUrl: '/documentation/'`.
The SDK docs keep `docs.intellistream.ai`, which resolves the earlier root conflict.

Consequences of the baseUrl:

- The production web server must serve the contents of `build/` under `/documentation/`.
- Site-rooted asset paths in JSX need `useBaseUrl()`; the shared `Figure` and `IconItem`
  components already do this. Markdown links get the prefix automatically.
- The dev server also serves under the prefix: `http://localhost:3000/documentation/`.
