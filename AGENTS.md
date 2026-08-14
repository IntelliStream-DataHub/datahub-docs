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
- **A colon in a front-matter value breaks the page's title, silently.** An unquoted YAML
  scalar containing `: ` is a parse error, and Docusaurus responds by falling back to the
  file id: the page appears in the left menu as `stream-processing` rather than
  "Stream processing", and loses its meta description with it. Nothing else complains, the
  build succeeds, and the page body looks perfect because the `# Heading` is markdown rather
  than front matter. `scripts/check-docs.py` now parses every front-matter block as real YAML
  (strictly when PyYAML is importable, otherwise checking for the unquoted colon) and requires
  a `title`. House style is to rephrase with a comma rather than to quote the value.
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
  `WRITE_<id>` realm roles are **no longer read at all**; do not document them. As of the
  platform branch `refactor/blanket-dataset-grants-to-org-groups` (2026-08), the blanket
  `_DATASET_ALL` / `_READ_ALL` / `_WRITE_ALL` roles are gone too, replaced by per-tenant
  wildcard organization groups `/datasets/*/read` and `/datasets/*/write`; do not
  reintroduce them. Only `DATAHUB_ADMIN` stays a realm role, the operator escape hatch,
  resolved from the token alone so it survives an unreachable identity provider.
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

### MCP and agents, 2026-08-14

Two new pages in the using section: `using/mcp.mdx` (position 14) and `using/ai-agents.mdx`
(position 15, "Building AI agents", distinct from the leadership-facing `value/ai-agents`).
Twenty-three new themed figures: `agent-anatomy` (static, the six parts, reusing the
`revolution_contrast` self-loop glyph unchanged as the house pattern says to),
`mcp-one-protocol` (static, the N×M against N+M argument),
`mcp-call-path` (animated, one call through the auth gate), `agent-guardrails` (animated,
the four limits), `agent-graph-join` (a series column and an event column joined only by the
nodes they hang off), and one per industry example: `wind-peer-comparison`,
`vessel-sisters`, `blast-radius-cooling`, `readiness-gate`, `issuer-neighbourhood` and
`ward-devices`. Every example on that page now carries a figure; keep it that way if an
eighth is added. The concept pages add `dirty-data`, `feature-flywheel`,
`synthetic-and-measured`, `rules-vs-learning`, `ml-progression`, `clustering` and
`neural-network`.

Two more figure lessons from that batch. **Draw rings before the dots they single out**: a
`fig-box` circle fills with the surface colour, so drawn afterwards it hid the support
vectors it was meant to highlight. And **put illustrative points where the geometry says
they go**: the first `ml-progression` ringed two arbitrary points as support vectors when
they sat nowhere near the margin, which argued against its own caption.

Three figure lessons from those, all found by looking at the rendered page or by a reader
saying they were lost, none of them by a checker. **Never name a platform rule in a figure.**
`ward-devices` originally ended "traversal is gated on the starting node, so a boundary has
to be an absence of edges, not a label", which is precise and useless: it only parses for
someone who already knows the rule. It now says what the rule *does*, that a question can
reach whatever is linked to where it started, so the way to keep two things apart is to
leave the link out. **Plot the quantity the finding lives in.** Four per cent of a power curve is
five pixels; four per cent of production-relative-to-the-string-median is the whole chart, so
`wind-peer-comparison` plots the ratio. **Get the physics the right way round.** The first
`vessel-sisters` had consumption climbing *after* a hull cleaning and the cleaning dates
plotted backwards; fouling climbs, a cleaning resets it, and the vessel cleaned longest ago
is the one riding highest now. A figure that is merely pretty will pass every check in this
repo.

**Four new concept pages** carry the data-and-models material, positions 11 to 14:
`data-cleaning`, `feature-extraction`, `machine-learning` and `synthetic-data`, in that
reading order (clean, featurise, learn, and generate when the examples run out). They began
as one section on the agents page and were split out on request, because each is its own
topic; `using/ai-agents.mdx` keeps a short "Agents that improve the data itself" section
saying what an agent contributes to each and linking out. Keep that shape: depth in concepts,
the agent angle on the agent page.

The claims worth preserving across them. Cleaning is a **graph** question, because a reading
is convicted by its neighbours rather than on its own terms, which is also why the advice is
"model first, clean second". The **event log is an unintentional labelled training set**,
since the trips and failures are already attached to the equipment they happened to. A
feature kept as a series compounds; one kept in a notebook is recomputed by the next project.
And synthetic data needs a *structural* separation, its own data set, labelled, train on both
but test only on measured, because the failure mode is always plumbing rather than
dishonesty. The cleaning rules (raw stays raw, corrections are events, flag rather than
silently substitute) carry a `<Roadmap>`, because with no quality flag and no lineage the
platform enforces none of them today.

`synthetic-data.mdx` opens with a plain-language **"what it actually is"**, added after a
reader pointed out that it dived straight into the argument: a datapoint is one reading with
a time on it, generated data is a datapoint no sensor produced stored in the same shape, and
the flight-simulator comparison carries the rest. Assume the reader of these four pages is
still new to datapoints and series; for much of this audience it is the first
machine-learning material they will read anywhere.

It also carries a **robotics** section, because that field is the most vivid live proof of the
argument: robot learning is bottlenecked on training data that cannot be downloaded, so it
runs on imitation learning plus reinforcement learning in simulation, and a teaching rig
generates terabytes an hour. One correction already made there, worth not reintroducing: the
cameras are **on the wrist and around the workspace**, not on the hand. The exception is the
tactile fingertip, where the best designs really are a small camera filming a gel pad from
behind: that is GelSight, first built at MIT, and the claim is cited on the page because it
sounds invented and is not. The reason it belongs on this
site rather than being a digression is the last line of that section: the simulator a robot
practises in is a digital twin of somewhere real, so an operation described well enough for a
machine to work in it is the same asset whether the worker is software, a person or steel.

`machine-learning.mdx` is deliberately maths-free: linear regression, logistic regression and
the SVM, then sequences (LSTM, with [xLSTM](https://arxiv.org/abs/2405.04517) named as its
modern extension), clustering and neural networks. The LSTM section carries two jobs, both
requested and both worth keeping: **anomaly detection in sequences**, where the model predicts
the next value and the gap between prediction and arrival is the finding, which catches what
no threshold can because every reading stays in range; and **classifying free text**, where
the illustration is three requests ("can you close my credit card" / "can you open my wife's
credit card" / "I no longer need my mastercard": the third shares only one word with the
first and means the same thing, the second shares nearly every word and means something else) and the payoff is a table of what a classifier assigns
to inspection reports, work permits, alarms, maintenance notes and spare descriptions. It
closes with an honest **LSTM against LLM** comparison, which is the question every reader will
have: the language model needs no training and is far easier to start with, the trained
classifier is more accurate and more auditable on a fixed label set and fails predictably
rather than by hallucinating, and the practical answer is usually to use the first to label
examples and the second to run in production. The recurring point is that everything
gained by moving right is paid for in explainability, and that the method matters far less
than the features and labels underneath it.

`lstm-sequence-anomaly` replaced a first attempt (`lstm-memory`) that drew four labelled
boxes and taught nothing. The lesson generalises: **do not illustrate that a mechanism
exists, illustrate what it buys.** The figure now shows a signal whose cycle quietly
collapses while every reading stays inside its limits, the model's expected continuation as
a ghost line, and the growing gap between them, because that gap is how a sequence model
finds an anomaly no threshold can see. Two placement bugs found by looking: the gap marker
was first put where the two curves cross (no gap to see) and the three right-hand labels all
piled into the same corner.

`ml-progression` is **three panels, and should stay three panels**. It was rebuilt mid-session
as a single scatter that refitted itself three times on a three-state animation, on the
reasoning that "same points, one chart" would show the progression better. It did not: the
three questions need three different pictures (a value read off a line, a probability between
no and yes, a boundary with a margin), and forcing them onto one set of axes made every one of
them harder to read. Reverted at the author's request, and the `.fig-state` CSS utility it
needed was removed with it. Three details in the surviving figure are load-bearing: **panel
three's boundary waves**, because a support vector machine with a kernel draws whatever shape
separates the groups with the most room, and a straight line (or the barely perceptible bow
that was tried in between) makes the third method look like the second. Its points are
derived from the boundary function rather than hand-placed, so the two bands wave with it and
nothing can land on the wrong side; the two ringed points sit exactly
on the margins; and the rings are drawn before the dots, because `fig-box` fills with the
surface colour and would otherwise hide them.

`using/events.mdx` gained `events-from-series`, one trace with three moments marked, because
the page described events well but never showed one being born. The distinction it draws is
the useful part and is easy to lose in editing: a **limit crossed** (which everyone already
records, often too much), a **pattern change** (caught by shape rather than value, and where
the interesting failures start), and a **change of condition** (not a fault at all, and the
row most often skipped, which is why a series later changes character for no recorded reason).

`feature-extraction.mdx` gained `features-on-image`, the pixels-edges-shapes-object ladder,
as the concrete version of "a feature is a number computed from numbers that do not mean
anything". It ends on the point that matters industrially: on images those layers are
learned, on your signals they are usually still designed by hand, because three bearing
failures is not enough to learn them from.

Every page in the left menu was then reviewed for whether it should carry a **"Where agents
help"** section, and nineteen gained one: three in start, five in concepts, eight in using,
one in value, two in administration. The rule applied, and worth keeping: add one only where
there is specific work an agent does on *that page's subject*, say what stays human, and link
out. Pages that already carry agent material in the body (subscriptions, functions,
relationship-analysis, console-tour, security, digital-twin) and pages with nothing to
delegate (installing, architecture, organizations, identity-providers, the value arguments,
reference) were deliberately left alone.

**What an agent is** is now argued on both agent pages rather than defined in a sentence:
decisions and actions rather than content, goals with sub-goals rather than instructions,
plain language, independence from step-by-step supervision, tools plus a planner, memory,
and self-assessment. Two framings carry the weight and should survive editing: agents learn
from **what actually happened** (the event log as training material, not bookkeeping), and
they **build the thing that makes the next job easier**, so capability improves as a
consequence of use. Both are paired with the caveat that autonomy is about steps, not
accountability, which is what keeps the claim compatible with the four limits.

The seven industry examples on `using/ai-agents.mdx` (oil and gas, wind, shipping, data
centres, defence, markets, healthcare) are deliberately written **through the graph**: each one lists the resources, relationships, series and events its own model holds,
then describes the traversal rather than the outcome, because the point being made is that
the same walk, resolve a node then step outward, is what joins a reading to something that
happened. Keep that structure if the examples are edited; a scenario written without the
traversal reads as vendor fiction. The build side of agents lives in `using/`, the strategic case
stays in `value/`; keep that split, and keep them cross-linked.

**Current state, and a trap worth reading before the next MCP edit:**

- **There are two MCP servers.** The API serves `/mcp`, and the analysis service serves its
  own `/mcp` with the single tool `analysis_related_series`. **38 tools between them**, 37
  on the API. The API's resource family has **7** tools, not 6: `resource_fetch_nearest`
  (breadth-first to the nearest nodes carrying a wanted label) joined
  `resource_fetch_related`.
- **How this was nearly got wrong.** A local `../datahub-platform` checkout dated
  2026-08-10 has no analysis MCP server and 36 API tools, and on that basis the two-server
  claim was "corrected" out of `value/ai-agents.mdx` before the mistake was caught. Both
  landed in the platform on 2026-08-11 or 12. **Check `git log -1 --date=short` in
  `../datahub-platform` and `../datahub-sdk-docs` before trusting either as the current
  state**, and note that neither can be fetched from this environment without the user's
  SSH agent: ask them to pull. The sibling SDK docs are written from the code and are
  usually the fresher of the two working copies.
- **The console assistant is an MCP client**, not a server. As of the 2026-08-10 console
  code: `ToolPolicy` is a default-deny allowlist of read-only tool names, anything not
  listed is filtered out before the model sees it and refused again at execution;
  `ChatProperties` caps a turn at 6 model-to-tool round trips, truncates a tool result at
  24k chars and trims the transcript at 40 messages; local `open_*_view` navigation tools
  render a button rather than fetching anything, which is what an "analyze" request
  produces. Whether the assistant now also calls `analysis_related_series` is **unverified
  against the newer platform**; the docs are worded so they hold either way. The exact
  allowlist size was deliberately dropped from the prose because it drifts.
- Gating is `datahub.chat.enabled` in the deployment, the tenant flag, and the
  `DATAHUB_CHAT` authority, and the entry point in the console is the **Ask AI** button in
  the top bar.
- **The analysis service ships in the standard deployment** (confirmed by the product owner,
  2026-08-14). The docs used to say the opposite in six places, and it was the stated reason
  `relationship-analysis.mdx` carried a `<Roadmap>` banner at all. That banner is gone, along
  with the matching claims on `using/insights.mdx`, `reference/faq.mdx` and
  `administration/architecture.mdx`. The compose files in a 2026-08-10 platform checkout do
  not mention the service, which is the stale-checkout trap again, not evidence.

**Unrelated but noticed, and not acted on:** platform commit dbb06bef removed the functions
feature and reverted to a simple metadata store. `docs/using/functions.mdx` already carries
a `<Roadmap>`, so nothing is actively false, but the page deserves a look next time
someone is in there.

**Two mechanical notes from the same session.** `npm install` had to be rerun: both
`@fontsource-variable/*` packages were in `package.json` but missing from `node_modules`, so
every build died on the font `url()`s. And a `<Lead>` (or a raw `<p className="lead">`) whose
content sits on its own lines gets that content wrapped in a second `<p>`, which is invalid
HTML and a React hydration warning visible only in a browser console. Keep the text on the
same line as the opening tag. The warning is still present on `start/what-is-datahub.mdx`,
`value/industry-examples.mdx` and `value/ai-agents.mdx`, which use the raw form.

### Trees, k-means and policy agents, 2026-08-14

`concepts/machine-learning.mdx` gained a **tree family** section (decision tree, random
forest, gradient boosting and XGBoost) sitting between the support vector machine and the
sequence material, and a **k-means** subsection under clustering. The sequences heading was
promoted from H3 to H2 so the new H2 could go between them; heading level does not change a
slug, so `#sequences-lstm-and-why-time-series-need-it`, linked from `using/events.mdx`, still
resolves. The claims worth preserving: trees **cannot extrapolate**, because a tree answers by
averaging examples it has seen, so outside its training range it returns the edge of what it
knows and plain linear regression is the better tool; trees have **no sense of time**, so
order has to be engineered into the features; **feature importance describes the model, not
the process**; k-means needs **scaled features** or the column with the biggest units decides
every group on its own; and once the clusters are named as labels, **the distance to the
nearest centre is an anomaly score nobody had to define**.

`concepts/data-governance.mdx` gained "Rules that act, not just rules that are recorded": the
four moments a rule can act (at the write, while it sits, at the read, at the end of life),
which of them acts today (only naming; note that reads *are* gated, but by organization groups
rather than by anything a policy says, so the honest framing is that the policy is not what
enforces it), how to write a rule something could enforce, and **the policy agent**, one agent
given one rule. That last idea is the one to keep intact: it is a **detective control, not a
preventive one**, it proposes but must never close its own finding, and the rule stays the
artefact so the agent hands it over when platform enforcement ships. The argument for an agent
rather than a scheduled query is the *judgement* class of rule: whether a description says
anything, whether a data set's membership still matches its stated purpose.

Three new themed figures: `tree-ensembles`, `k-means-steps` and `policy-agents`. Two new CSS
primitives, both general: `.fig-dot-c` (a third series dot, stroke-green, matching how
`.fig-dot-b` uses stroke-orange) and `.fig-edge` (**the solid twin of `fig-track`**; at glyph
scale a dashed line breaks into two or three marks and a mini tree stops reading as a tree).

**How to look at a themed figure without starting the site.** Wrap the SVG in an HTML page
that inlines `src/css/custom.css`, then screenshot it with headless chromium; add
`data-theme="dark"` on `<html>` for the dark pass. Snap chromium cannot write into `/tmp`, so
put both the HTML and the PNG under `$HOME`. Worth the two minutes: every defect in this batch
was found by looking and none by a checker, namely dashed branches that read as debris, a
label crossing the cluster it was not about, an agent rail running past its last tick, and a
starting centre parked inside the wrong blob.

### Decision tempo, defence and the guided tutorial, 2026-08-14

`concepts/lineage-and-quality.mdx` gained the business argument it was missing. The page was
written as a compliance story; it now opens the case for **decision speed** before the
mechanism: the slow part of a fast decision is trusting the number, not producing it, so the
two failure modes are deciding late and deciding confidently on something unverified. Then a
worked **Strait of Hormuz** example, forward lineage ("what of ours depends on this?", which
is the direction a crisis needs and the one lineage writing usually ignores), and the
compounding point that cheap revision is what lets you commit on an incomplete picture. New
figure `decision-tempo`.

Two things to preserve there. First, the honesty split: the page-level `<Roadmap>` covers the
whole page, and the new section closes with an explicit "what of this works today" paragraph,
because the forward question is genuinely cheaper today (one queryable model) while the
end-to-end trace and quality flags are not built. Second, **the Hormuz material is deliberately
structural, not topical**: a fifth of the world's petroleum liquids and a comparable share of
its LNG, about 33 km at the narrowest, bypass pipelines that carry only part of the flow. It
is written so it holds whatever is in the news, because this environment cannot verify the
current state of that situation, and a docs page pinned to a specific week's events ages
badly. If someone wants dates and prices in there, they have to supply them.

The same page gained a **"Where agents help"** on lineage: an agent walks the trail backwards
before answering and forwards when an input changes, and the three limits are that it must
never invent a trail, that its own answer is itself a derived value, and that a person still
decides.

`value/industry-examples.mdx` gained **a defence organisation** as the sixth deployment
(readiness computed rather than assembled, sustainment against usage rather than the calendar,
spares and thin supply, the estate as an industrial site, trials data that stays comparable).
Register matters here and was chosen deliberately: **sustainment, readiness and logistics,
never targeting or weapon employment**, the same register as the defence example on
`using/ai-agents.mdx`. It also carries the honest separation note, that classification domains
are a **deployment** boundary rather than a data set one, because tenants share one graph in
the reference stack. The page's "five deployments" counts were updated to six.

**`value/industry-examples.mdx` now carries a figure per example**, which it previously had
none of: `chemical-accounting` (a purchased total against a metered one, the same height,
with the only coloured band being the dose nobody needed), `shortfall-attribution` (the gap
on top, the units and their events underneath, on one axis), `excursion-upstream` (five
stages against a morning, the cause upstream and five hours earlier), `defect-attribution`
(defects clustering where one station meets one material lot), `incident-path` (a latency
step at 14:20 over the chain back to the deploy at 14:00) and `usage-vs-calendar` (two
identical vehicles, one deployed, four calendar services that fit neither). The coda section
reuses `liberation-translate` rather than growing a near-duplicate. Keep the one-per-example
rule if a seventh deployment is added, the same rule `using/ai-agents.mdx` follows.

Four defects in that batch, all found by rendering and none by a checker, and all of a kind
seen before: a label parked on top of the bar it was annotating; two chart labels colliding
because both were anchored inward from their own marks; a demand line hidden underneath the
delivered line everywhere they agreed (fixed by drawing the reference line last and ghosted,
so agreement reads as agreement); and calendar-service ticks drawn in the orange that the
figure had already spent on vehicle B, which silently assigned them to one vehicle. **A
colour that means something elsewhere in the same figure cannot be reused for scenery.**

**New page: `using/guided-tutorial.mdx`** at position 2, with everything from 2 upward
renumbered. The console has carried a guided tutorial for a while and the docs mentioned it
only in a table row. Written from the console code, not the i18n bundle, with the platform
checkout dated `2026-08-14` first. Where it lives:
`datahub-console/src/main/resources/static/js/tutorial-{core,dom,engine-ui,context,page-ui}.js`
plus `static/js/tutorials/datasets.js`, with the modal shells in `templates/layout/main.html`.
The facts worth keeping: one tour exists (`datasets`) with six chapters (datasets, resources,
timeseries, correlation, events, buildout, the last labelled "Build a network"); four industry
scenarios (oil_gas the default, tech, manufacturing, energy) which change vocabulary only;
steps are guarded (a click or a minimum-length input) and everything outside the highlight is
blocked; the tour navigates across pages and resumes silently, or offers a Resume/Restart/Quit
banner; **it writes real objects into the tenant**, a new run deletes the previous run's first,
and the final step offers "Keep it" or "Remove tutorial data" (best effort); chapter one needs
the all-data-sets grant, since creating a data set does; and `tutorial.enabled=false` in the
console configuration removes it everywhere.

### Stream processing, 2026-08-14

New concepts page `concepts/stream-processing.mdx` at position 15, sitting after the
clean, featurise, learn, generate run and opening on the observation that all four of those
pages assumed the data was sitting still. Three figures: `answer-age` (a sawtooth, because
the quantity that separates batch from streaming is **the age of the answer** rather than the
answer), `window-shapes` (tumbling, sliding and session side by side; `windowing` on the
functions page still draws tumbling properly, and this one exists to make the *choice*
legible) and `event-time-arrival`.

The claims worth preserving: batch is not obsolete, it is **periodically right**, and what it
costs is that nobody knows how much of today is missing from the number; a window's length is
a claim about the process, set by how fast the watched thing can change; **state rather than
volume is what makes a stream computation hard**, because state has to survive a restart. And
the one that earns the page its place: **event time against arrival time is the industrial
half of stream processing that web-shaped writing never covers.** Links drop, a vessel sails,
a handheld syncs at end of shift, so a window computed on arrival invents a quiet morning and
a violent afternoon. The three rules that follow (compute on the carried timestamp, decide how
long a window stays open, assume a reading can arrive twice) should survive editing.

**The SDK section is written from `../datahub-sdk-docs`, checkout dated 2026-08-14,
`docs/guides/realtime-subscriptions.mdx`, which is itself written from the code.** The facts
used: SDKs for **Java, Python and Rust**; a subscription names a set of series and a live
connection delivers each datapoint as it lands, with no polling; the consumer acks what it
handled, unacked messages are redelivered and a nack re-queues, so delivery is **at least
once** and handlers have to be idempotent; the interest set can be changed on a live listener
without reconnecting; reconnection is transparent. That last one is why the burst in
`event-time-arrival` is normal operation rather than a fault, which is the join between the
concept half of the page and the SDK half. The deep link used is
`/sdk-documentation/guides/realtime-subscriptions`, following the `/sdk-documentation/mcp-server`
pattern already on `value/ai-agents.mdx`; `check-docs.py` does not validate those, so they
need a manual look if the SDK site is ever reorganised.

`using/subscriptions.mdx` then gained a **worked sliding-window example** on the back of it,
because the page had been all mechanism and no problem: a pump's limit alarm firing four
hundred times a month, suppressed years ago, useless on the one occasion it mattered. The
argument for a sliding rather than a tumbling window is the load-bearing part, and it is
concrete: a twenty-five minute excursion straddling two fifteen-minute slices shows as two
partial slices and neither is sustained, so a tumbling rule stays quiet through the event it
was built for. The figure `sustained-exceedance` draws the four nuisance spikes **higher**
than the real excursion on purpose, because duration rather than severity is what the rule
judges, and a picture where the real one is also the tallest would argue the opposite.

Everything in that example's "survive contact with reality" list is tied to a verified SDK
fact rather than to general streaming advice: at-least-once delivery means dedupe inside your
own window (the platform collapses duplicates you *write*, since datapoints are keyed by
series and timestamp and events by id, but the window is yours); evict on the carried
timestamp; fill the window from the ordinary API on start-up instead of being blind for the
first twenty minutes; a window with holes is not a quiet window; ack after acting, never
before. Also worth keeping: a subscription's service account must be able to read **every**
series bound to it, and a series it cannot read is refused explicitly rather than arriving as
silence.

Keep code samples on this site to about **70 characters a line**. The first version of that
snippet ran to 90 and the trailing comments were clipped at the edge of the code block, which
the checkers cannot see; the fix was moving comments onto their own lines rather than
shortening the code.

`drafts/streams.mdx` stays parked and none of it was resurrected: that draft is a **product**
page (namespaces, topics, backlog quotas, console screens) waiting on a rework of how
streaming will work, while this is a concepts page about the idea. The one place they touch is
backpressure, which the new page states as a principle (drop, buffer or slow the producer, and
the only mistake is not knowing which) without documenting any console screen.

### The lesson

Do not document platform behaviour from i18n strings, console text or the platform's own
prose docs. **Read the code.** Several i18n strings describe behaviour the backend does not
implement, and at least one states the exact opposite.

The MCP episode above adds a second half to that rule: **a stale checkout is as misleading
as prose.** Reading the code is only worth something if the code is current, so date the
working copy before you trust what it does not contain. Absence of a feature in a checkout
is weak evidence; presence is strong.

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
