# AGENTS.md
Working notes for anyone, human or agent, picking up this repository. Read this before
editing. It records the conventions, the traps that have already cost time, and, most
importantly, **which claims in the docs are known to be wrong**.

See `README.md` for the reader-facing description of the site. This file is about how to
work on it.

---

## What this is

The user-facing documentation for the IntelliStream DataHub platform, built with Docusaurus 3.
The audience is explicitly **not developers**: engineers and operations staff without coding
background, domain experts, and leadership or board members in traditional industry moving
toward Industry 4.0.

Developer and API material lives in the separate `../datahub-sdk-docs` site. The design skin,
brand palette and Docusaurus setup were copied from there.

Source material for the content: `../datahub-platform` (README, ARCHITECTURE, FAQ,
GETTING_STARTED, INSTALL, EntraID.md, SPESIFICATIONS, `datahub-api/DATASET_ACL_SETUP.md`, and
the console i18n bundle), plus reusable brand SVGs from `../intellistream-website`.

---

## Running and building

Node 22 is installed system-wide (`sudo dnf install nodejs` on AlmaLinux 10), so this is a
normal npm project:

```bash
npm install
npm start -- --host 0.0.0.0 --port 3000   # dev server, reachable on the LAN
npm run build                              # production build
npm run serve                              # serve the build locally
```

A full build takes about 40 seconds.

> **History:** this was previously run through a `node:20-alpine` container because no Node
> was installed. If you ever reintroduce a container, remember that `node_modules` built on
> Alpine is musl-linked and will not load on glibc, so it must be reinstalled when switching.
> Also never run a build while the dev server is up: both write `.docusaurus/` and `build/`,
> and the dev server dies.

---

## Verification, run all of these before calling anything done

```bash
python3 scripts/check-docs.py          # links, anchors, static assets, themed-figure rules
python3 scripts/check-figures.py 'static/img/figures/*.svg' 'src/figures/*.svg' \
    --css src/css/custom.css           # text or shapes escaping the viewBox
python3 .claude/skills/svg-contrast/check_svg_contrast.py 'src/figures/*.svg' \
    --css src/css/custom.css --theme both
python3 .claude/skills/svg-contrast/check_svg_contrast.py 'static/img/figures/*.svg' \
    --theme light
```

These exist because SVG fails **silently**: an over-wide label is clipped without complaint,
and low-contrast text renders perfectly happily. Both defects shipped before the tools were
written. `npm run build` catches MDX errors and broken links but none of the above.

Current state: docs checker clean, figures clean, themed contrast clean. The only outstanding
contrast failures are 14 in `static/img/figures/knowledge-graph-oilgas.svg` at 4.37 to 4.38
against a 4.5 threshold. That file is imported unchanged from `../intellistream-website`, so the
fix belongs upstream rather than in a local fork.

`knowledge-graph-oilgas.svg` has one local divergence from the upstream copy: the node label
`FPSO A` was changed to `Plant A`, because the docs deliberately describe a generic oil and
gas processing facility rather than a floating production vessel. Keep that in mind if the
file is ever re-copied from `../intellistream-website`.

---

## Writing conventions

- **Progressive disclosure.** Plain answer first, links to depth underneath. Open with
  `<Lead>` or `<KeyIdea>`, keep the body short, close with `<Deeper>`.
- **Never name a competitor.** Where the category's public evidence matters, describe results
  without attributing them to a vendor or a named customer.
- **No em dashes.** A house style decision: they are heavier than this prose wants. 766 were
  removed from 44 files. Use commas, or a colon for a link followed by a gloss
  (`- [Page](/x): what it covers`), where a comma collides with the gloss's own commas.
  `scripts/dedash.py` does the conversion, code-fence and table aware. It can produce comma
  splices; re-read what it changes.
- **Lots of external links.** They help SEO and let a reader check us against neutral
  sources. Around 100 across the site, in a `<References>` block above `<Deeper>`. Wikipedia
  for concepts, W3C for RDF and friends, IETF for RFCs, OSPAR and Havtilsynet for the
  chemical categories.
- **Flag anything not shipped** with `<Roadmap>`. See the accuracy section below.
- British spelling, sentence case headings, hard wrap near 88 characters.

### Components

Registered globally in `src/theme/MDXComponents.js`, defined in `src/components/DocsUI.jsx`,
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
| `<Figure src caption wide>` | All three figure kinds (see Figures below) |
| `<IconRow>` / `<IconItem>` | Icon-led bullet rows |
| `<Roadmap>` | Marks capabilities that are planned, not shipped |
| `<References>` | External source links, above `<Deeper>` |

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

---

## Figures

Three kinds, and the choice matters:

| Kind | Location | When |
| --- | --- | --- |
| Mermaid | ```` ```mermaid ```` in the page | Quick structural diagram, layout not important |
| Static SVG | `static/img/figures/`, via `<Figure src="…">` | Self-contained illustration, including reused brand SVGs |
| Themed inline SVG | `src/figures/`, imported and passed as `<Figure>` children | Anything animated, or anything that must follow the light/dark toggle |

**Why themed figures are inlined.** An SVG loaded through `<img>` is an isolated document.
It cannot see the page's `data-theme`; the most it can react to is the OS
`prefers-color-scheme`, which disagrees with the site's toggle whenever a reader overrides
their OS preference. Inlining via SVGR puts the elements in the page DOM where site CSS
reaches them.

**The rule that makes it work:** a file in `src/figures/` contains geometry and class names,
**never colour**. No `<style>`, no `fill="#…"`, no `stroke="#…"`; the only literal allowed is
`fill="none"`. Palette and animation both live in `src/css/custom.css`.
`scripts/check-docs.py` enforces this.

`scripts/make-figures.py` generates the figures whose geometry needs computing. Run
`python3 scripts/make-figures.py` after editing it. It writes static figures to
`static/img/figures/` and themed ones to `src/figures/`.

Themed-figure usage in a page:

```mdx
import AgentLoop from '@site/src/figures/agent-loop.svg';

<Figure caption="What the diagram adds beyond its title." wide>
  <AgentLoop />
</Figure>
```

### Available figure classes

Defined in `custom.css`, so a new figure normally needs no new CSS at all:

- **Text**: `fig-title`, `fig-sub`, `fig-box-title`, `fig-box-sub`, `fig-centre-title`,
  `fig-centre-sub`, `fig-lit-title`, `fig-lit-sub`, `fig-exit-title`, `fig-exit-sub`,
  `fig-exit-note`
- **Shapes**: `fig-box`, `fig-lit-box` + `c-blue`/`c-orange`/`c-green`, `fig-centre`,
  `fig-track`, `fig-token`, `fig-exit-box`, `fig-exit-path`, `fig-dot-a/b`,
  `fig-badge*` (the ai-agents robot chips)
- **Animation**: `fig-seq` + `fig-d1`…`fig-d6` (staggered reveal on a shared 8s loop),
  `fig-flow` (marching dashes), `fig-pulse`, `fig-draw` (stroke draws itself in)

All loops share an 8-second cycle so several figures on one page stay in sympathy, and
every animation is disabled under `prefers-reduced-motion`.

### Figure lessons learned

- **Compute box edges before writing them.** The first agent-loop diagram had its centre box
  overlapping the left and right stations, because the radius did not clear
  half-centre plus half-station plus a gap.
- **Never cross-fade a base box against a lit twin.** While both are part-opaque, dark base
  text and white lit text blend over a half-tinted fill and neither is readable. Use
  `steps(1, end)` so the swap is instant. This is what "traversal.svg still has bad contrast"
  turned out to be, and the contrast checker could not see it because it is a transient state.
- **Animate only what changes over time.** A comparison figure should be static, so the
  reader can look between its parts. `three-layers-build`, `industrial-revolutions`,
  `experiment-rate` and the nodes of `silos-to-model` were all animated first and are better
  static. Flow along a path (`fig-flow`) is the exception that earns its motion: it shows
  direction continuously without ever hiding anything.
- **Accent fills carrying text must be darkened.** White on the brand orange `#f6783c` is
  2.6:1. Use `--fig-fill-*`, which clear 4.5:1 in both themes.
- **Animated connectors are two classes, not one.** The house style for a data-carrying
  path is `class="fig-exit-path fig-flow" fill="none"`: `fig-exit-path` paints the stroke,
  `fig-flow` only adds the marching dashes. A bare `fig-flow` path has no stroke rule and no
  `fill="none"`, so it renders as a solid black filled shape, reported in review as "weird
  style" on liberation-translate and digital-twin-mirror.
- **Thin strokes need brighter dark-theme colours than filled boxes.** `--fig-stroke-green`
  and `--fig-stroke-orange` exist for 2.5px lines: same as the fill colours in light, but
  `#3fcb7e` / `#f6783c` in dark, where a thin line at the fill shade nearly vanishes.
  `.fig-line-a/b/c` chart traces use stroke-green; `.fig-loop-arc`/`.fig-loop-head` use
  stroke-orange.
- **The self-loop glyph** (`loop_glyph` inside `revolution_contrast`) went through four
  rounds of review; the settled form is a 300° circle perched on the node's
  **top-right corner** (centre nudged +5,−5 along the diagonal), gap facing down-left into
  the node, arrowhead tangent at the arc end pointing back into the node, orange. Reuse it
  rather than redesigning if another figure ever needs a control-loop mark.

---

## Traps that have already cost time

- **Fonts are self-hosted; do not reintroduce a Google Fonts `@import`.** Manrope and
  JetBrains Mono are served from our own origin, from the `@fontsource-variable/*` packages
  via `src/css/fonts.css`. Webpack rewrites the `url()`s to hashed files under
  `build/assets/fonts/`, so the baseUrl is handled for you. If you add a weight or a style,
  check the variable axis covers it (Manrope 200 to 800, JetBrains Mono 100 to 800) rather
  than reaching for the CDN. Italic monospace is not declared, as it was not in the old
  import either; browsers synthesise it.
- **Keep every `@docusaurus/*` package on the same version.** A drift of one patch
  (`theme-common` 3.10.2 against `core` 3.10.1) makes Mermaid fail during static generation
  with `Hook useColorMode is called outside the <ColorModeProvider>`, and the build dies on
  every page containing a diagram.
- **Mermaid sizing.** Do not force `width: 100%`; that stretches small diagrams to the full
  column and they become enormous. Let mermaid size naturally and only constrain overflow.
  Legibility comes from the font size, not from stretching.
- **Mermaid renders client-side.** Static HTML holds an empty placeholder, so diagrams being
  absent from the build output is expected. A malformed diagram fails silently in the browser
  rather than breaking the build, so check diagrams visually.
- **Punctuation in headings changes their slug.** Removing em dashes from headings silently
  broke four internal anchors. Run `scripts/check-docs.py` after any bulk text change.
- **Editing `make-figures.py` by slicing between markers is dangerous.** One such edit left
  duplicate function definitions, and Python used the later, stale one, so the regenerated
  figure looked unchanged. Verify the output, not the edit.

---

## Accuracy: read this before trusting the docs

The content was originally written from the platform's prose docs and console i18n strings
rather than from code. A code-level fact-check found that **a substantial number of the "how
it works" claims were wrong**, several of them the opposite of actual behaviour. That backlog
was worked through and closed out on 2026-08-02, with only the cosmetic residue noted at the
end of this section. What follows is the record of what was corrected and why, because the
same mistakes are easy to reintroduce.

### Fixed

- Files with no data set are **public to any authenticated user**. The docs said the
  opposite. Resources, time series and events are conservative; files are the exception.
- **Graph traversal is gated only on the starting node.** The reachable network is not data
  set filtered, so reading one resource can expose connected resources in data sets the
  caller cannot read. Was undocumented.
- **Tenant isolation was overstated.** Neo4j Community supports one database, so all tenants
  share one graph. PostgreSQL and ClickHouse get separate databases but share one credential
  in the reference stack. `organizations.mdx` now separates what the platform supports from
  what the shipped deployment configures.
- File reads return **404, not 403**, when denied, deliberately, so a denial cannot confirm
  a file exists.
- OSPAR **black** category means discharge prohibited outright, not "use where nothing else
  will do". Verified against OSPAR and Havtilsynet.
- First industrial revolution dated from **1760**; Industry 4.0 traced to the 2011 German
  high-tech strategy, introduced at the Hannover Fair. Verified against Wikipedia.

### Flagged as roadmap, confirmed with the product team

Also flagged as roadmap **building blocks** on `start/core-ideas.mdx`: **policies with
enforcement** (retention, access, requirements, retention enforcement planned together with
measurement expiry) and **executable functions** (data cleaning, transformation, feature
extraction, streaming computation with windowing).

**Keycloak Organizations: landed, no longer roadmap** (was flagged here as "expected during
the second half of 2026"; that instruction is discharged as of 2026-08-03). Both halves
shipped, verified in `../datahub-platform/datahub-api/KEYCLOAK_ORG_GROUPS.md` against a live
Keycloak 26.7. What is now true, and what the docs say:

- **Tenant identity is the real Organizations feature**, one organization per tenant. The
  old per-user `datahub_org` attribute shortcut is gone from the platform and the dev realm.
  Do not reintroduce "a per-user attribute, a development shortcut" anywhere.
- **Membership is the mechanism.** A user or service account that is not a member of its
  organization gets no tenant. A non-member service account authenticates fine and then sees
  nothing, which reads as a data problem rather than an access one. Likely support ticket,
  documented on `users-and-access.mdx` and `identity-providers.mdx`.
- **Clients must request an organization selector**, `scope=openid organization:*` or
  `organization:<alias>`. Without one there is no organization claim and the token is
  rejected. A user in several organizations gets an ambiguous token, also rejected.
- **Data set access is organization groups**, `/datasets/<externalId>/read` and `/write`,
  inheriting down the data set hierarchy. The id-bearing `DATAHUB_DATASET_READ_<id>` /
  `WRITE_<id>` realm roles are **no longer read at all**; do not document them. The blanket
  `DATAHUB_ADMIN` / `_DATASET_ALL` / `_READ_ALL` / `_WRITE_ALL` roles stay realm roles.
- **Grants are not read from the token**, so "there is no cached permission state, revoking
  takes effect at the next token issue" is wrong and was corrected on `security.mdx`,
  `overview.mdx`, `users-and-access.mdx` and `building-applications.mdx`. Correct user-facing
  wording: changes take effect **within about a minute**. If the identity provider is
  unreachable, requests are refused rather than returning empty results.
- **Creating, updating or deleting a data set itself needs an all-data-sets grant.** A grant
  on individual data sets never confers it, because a data set is the unit access is granted
  on. Documented on `dataset-permissions.mdx` and `using/datasets.mdx`.

Still true and worth keeping: an organization may have several identity providers, but an
identity provider may belong to only one organization, so a shared directory cannot be linked
to many organizations.

Documented with `<Roadmap>` rather than removed: **lineage and data quality** (no lineage
subsystem exists; the only artefact is a `WAS_DERIVED_FROM` edge, and no data-quality flag
exists in any model or migration), **change data capture** (the console screens are not wired
up end to end), **relationship analysis** (implemented in `datahub-analysis`, which is not in
the shipped compose), **measurement expiry** (no ClickHouse TTL, so datapoints are kept
indefinitely), and **data set policies** (declarative records that nothing enforces).

### Value-section review, August 2026

The `docs/value/` pages were reviewed and elaborated as a set. Two things worth carrying
forward:

- **Lineage claims leak.** "Audit-ready reporting" is really a lineage play, and the claim had
  propagated into `business-case.mdx`, `measuring-return.mdx`, `board-briefing.mdx`,
  `industry-examples.mdx` and `security.mdx`. All now split what works today (one queryable
  model, reproducible figures) from what arrives with lineage. If lineage ships, search for
  "roadmap" across `docs/value/` and `docs/administration/security.mdx` and unwind those
  qualifiers together.
- **`value-paths.mdx` now carries an "Available" column** and marks two plays as partly
  available. Keep that column honest as capabilities land; it is the first thing a reader
  uses to choose.

### Fixed in the 2026-08-02 review pass

A fresh full-site review fixed the highest-priority items from the earlier fact-check,
plus overclaims that had survived on high-traffic pages: the landing page's
lineage row, the FAQ value proposition and "git branches" answer (now framed as the planned
model), the glossary's lineage and quality-signal entries, and the lineage page's meta
description. Also fixed: external-id mutability (guidance, not enforcement; the locked field
is the type label), the stranded-resource behaviour (the platform refuses the delete, nothing
is removed), events immutability (they can be corrected or deleted; treat as append-only in
practice), file versioning (none exists; update edits details only), type label semantics
(at most one, not exactly one), clone semantics (labels and relationships, not metadata), the
language switcher (a `?lang=` parameter, not a menu), a stale "live streams" mention on the
landing page, and two comma splices left by the em-dash pass. Query-cursor keys were already
fixed earlier. New content in the same pass: `concepts/contextualization.mdx` (position 4,
concepts renumbered), a robot-for-knowledge-work analogy and a dynamic-incentives section on
`value/ai-agents.mdx` (incentives framed as direction, with the Goodhart's-law caveat), and
footer/glossary wiring for the newer pages.

Later the same day: `concepts/digital-twin.mdx` (position 5, concepts renumbered again;
"grown, not built" is the through-line, consistent with where-to-start's bad-question list,
and the maturity ladder maps levels 3–4 onto the functions/agents roadmap honestly), three
new themed figures (`liberation-translate` on data-liberation, `resource-anatomy` on
ontology, `digital-twin-mirror` on digital-twin), and five FAQ answers (digital twin,
agents, subscriptions, functions/policies status, Entra ID sign-in). The FAQ's Entra answer
used to repeat the Keycloak-organisations "when it lands" framing; unwound on 2026-08-03, see
the Organizations entry above.

### The 2026-08-02 site-wide review pass

Five parallel section audits (start, concepts, using, value, administration + reference)
were run against everything added recently, and all confirmed findings were applied. The
themes, so the next pass knows what to watch:

- **Roadmap tense drift** was found on ~10 pages (lineage, functions, relationship
  analysis described in shipped present tense) and fixed. It regrows; grep for it.
- **New-page reciprocity**: digital-twin, contextualization, data-governance and
  subscriptions now have inbound body links from every section. The twin anatomy table's
  five target pages all link back.
- **Real contradictions fixed**: organizations.mdx had the IdP rule inverted (correct
  rule: an organisation may have several IdPs; an IdP belongs to exactly one organisation);
  the FAQ claimed per-tenant credentials that the reference stack does not configure;
  dataset-permissions described the Policies tab as answering access; datasets.mdx
  contradicted the files-are-public-without-a-data-set exception; glossary Retention/Tenant
  overstated; functions.mdx had a "tank story above" pointing below.
- ai-agents' Coordination/incentives/workforce sections were re-nested under a new H2
  "An organisation of agents"; the org-chart figure got per-node "agent" robot badges
  (`.fig-badge*` classes, ink chip/surface glyphs; Leadership deliberately unbadged).
- New: `docs/using/building-applications.mdx` (position 13; equipment-360 as the first
  app, success stories referenced generically, never by vendor name), `aliasing-illusion`
  figure on timeseries (right panel's slow wave is the mathematically exact alias:
  sin 2πx/34 sampled every 30px lands exactly on sin 2πx/255), `.fig-dot-a/b` classes.
- Installing: minimum RAM raised to 16 GB, 6 GB was too low to run the stack.
- Git: public repo, remote `git@github.com:IntelliStream-DataHub/datahub-docs.git`.
  AGENTS.md (then named AGENT.md) was gitignored and local-only until 2026-08-03, when it was brought under version
  control. It is now committed, so it is as public as the docs themselves: keep it candid
  about conventions and traps, but weigh anything that describes unshipped or weak platform
  behaviour before writing it down here.

Also: `agent-organisation` figure (org chart of agents: leadership → coordinator →
three managers → four workers, all standing on a knowledge-graph bar; work flows down,
results return up the right-hand path) placed in the ai-agents Coordination section, with
new prose on the organisation pattern (explicitly framed as architecture, not a product
module) and a new "The workforce will not stay virtual" subsection: humanoid robots,
normally unmanned installations, the unmanned facility operated through its digital twin,
and "a robot that does not know which pipe it is looking at is a camera on legs". The
framing to preserve: agents as business managers plus a master coordinator, and unmanned
offshore platforms as where this is heading.

### Fact-check backlog: closed out 2026-08-02

Every remaining item from the August code-level fact-check has now been corrected: the
events filter list (external id prefix, source, type/sub type/status, metadata; no resource
or free-text filter; times shown local), the missing **analysis** and **housekeeping**
services (now on the architecture page, marked not-yet-in-reference-stack), label and
relationship names being stored upper-cased (advice now says spaces, not camelCase), data
set "Part of" semantics (multi-select, fixed at creation) and the unconditional folder
cascade, the insights cap of six and live-mode windows, the non-existent depth control
(Expand search adds ten per click, cap 200), the console-tour filter and Streams-area
claims, the resource form's API-only data set field, the identity role table
(`DATAHUB_ADMIN` added, read-gating corrected), the broken SSH-tunnel tip (replaced with the
honest constraint), the housekeeping task list (30-day file grace, report-only subscription
sweep, 30-day tenant quarantine), and the phantom "lineage endpoint" in the API
descriptions.

**Residual, cosmetic only:** concept pages still use camelCase relationship names
(`partOf`, `contributesTo`) in illustrative examples. Conceptually fine, and the RDF example
is legitimately camelCase, but a sweep to spaced names would match what the platform stores.

### The lesson

Do not document platform behaviour from i18n strings, console text or the platform's own
prose docs. **Read the code.** Several i18n strings describe behaviour the backend does not
implement, and at least one states the exact opposite.

---

## Parked work

`drafts/streams.mdx` holds the Streams documentation, moved out of `docs/` pending a rework
of how streaming will work. It is outside `docs/`, so it
appears in neither dev nor production. The CDC material was split out of it and remains live
at `docs/using/cdc-integrations.mdx`. `drafts/README.md` lists the references that were
removed and would need re-pointing.

---

## Deployment

Publishes at **https://intellistream.ai/data-platform-documentation**
(`baseUrl: '/data-platform-documentation/'`); the SDK docs sit alongside at `/sdk-documentation/`.
Serve `build/` under `/data-platform-documentation/` on the main site's web server. The main
site already serves a marketing page at `/documentation`, and its controller mapping would
win over static resources, so this site cannot be mounted there. Markdown links pick up the baseUrl automatically, but any raw `<img src>`
in JSX must go through `useBaseUrl()`, `Figure` and `IconItem` already do. The dev server
lives at `http://<host>:3000/data-platform-documentation/`, the bare root shows only a
redirect hint.

The build is served by the `intellistream-website` Spring Boot app out of
`src/main/resources/static/`. That repo's `sync-docs` skill rebuilds this site and copies
`build/` into place; use it rather than copying by hand.
