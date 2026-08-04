# IntelliStream DataHub user documentation

The user-facing documentation site for the **IntelliStream DataHub platform**: what it is,
how to use it, how to create business value with it, and how to administer it.

Written for readers who are **not developers**: engineers, operations staff, domain
experts, and leadership or board members in traditional industry. Developer and API material
lives in the separate [`datahub-sdk-docs`](../datahub-sdk-docs) site.

Built with [Docusaurus](https://docusaurus.io/) 3, using the same IntelliStream brand skin as
the SDK docs.

> **Working on this repo?** Read [AGENTS.md](AGENTS.md) first. It records the writing
> conventions, the figure system, the verification tooling, the traps that have already cost
> time, and which claims in the docs have been fact-checked.

## Get it running locally

1. **Install Node.js ≥ 20** — easiest via [nvm](https://github.com/nvm-sh/nvm):

   ```bash
   nvm install 22 && nvm use 22      # or download from https://nodejs.org/
   node --version                    # confirm v20+
   ```

2. **Clone the repo** and enter it:

   ```bash
   git clone https://github.com/IntelliStream-DataHub/datahub-docs.git
   cd datahub-docs
   ```

3. **Install dependencies and start the dev server:**

   ```bash
   npm install        # first time only
   npm start          # http://localhost:3000/data-platform-documentation/ with hot reload
   ```

To preview on the LAN (e.g. for review on another device):

```bash
npm start -- --host 0.0.0.0 --port 3000
```

## Build and check

```bash
npm run build                    # static site into ./build (fails on MDX errors, warns on broken links)
npm run serve                    # serve the production build locally
python3 scripts/check-docs.py    # internal links, anchors, assets, figure conventions
```

`check-docs.py` and the two figure checkers cover what the build cannot see; run the full
set from [AGENTS.md](AGENTS.md#verification-run-all-of-these-before-calling-anything-done)
before calling a change done.

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

## Deployment

The site publishes at **https://intellistream.ai/data-platform-documentation** and is served
by the `intellistream-web` app; that repo's `sync-docs` skill rebuilds and copies `build/`
into place. Details and the baseUrl consequences are in
[AGENTS.md](AGENTS.md#deployment).
