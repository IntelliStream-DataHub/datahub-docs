# Parked drafts

Pages that are **not part of the site**. Nothing in this folder is picked up by Docusaurus —
it sits outside `docs/`, so these pages appear in neither the dev server nor a production
build.

| File | Status |
| --- | --- |
| `streams.mdx` | Parked pending rework of how streaming will work. The change-data-capture material was split out and remains live at `docs/using/cdc-integrations.mdx`. |

## Bringing one back

1. Move the file into the right folder under `docs/`.
2. Set its `sidebar_position` to fit the section.
3. Re-point the references that were removed when it was parked — for `streams.mdx` those
   were in `using/console-tour.mdx`, `using/events.mdx`, `using/resources.mdx`,
   `using/timeseries.mdx`, `start/core-ideas.mdx`, `reference/glossary.mdx`,
   `reference/faq.mdx`, and the `administration/` pages on permissions, data lifecycle and
   installing.
4. Run `python3 scripts/check-docs.py` and `npm run build` to confirm links resolve.
