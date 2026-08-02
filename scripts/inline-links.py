#!/usr/bin/env python3
"""Add contextual external links on the first mention of a term in prose.

The `<References>` block at the foot of a page is for a reader who wants to
check us. Inline links serve a different job: they catch a reader at the moment
they hit an unfamiliar word. Both are worth having.

Only the FIRST prose mention of a term is linked, and only terms that have no
page of their own on this site (linking "knowledge graph" outward would compete
with our own page for it).

Protected from rewriting: front matter, fenced and inline code, existing
markdown links, JSX tags and their attributes, and the References block itself.

Run:  python3 scripts/inline-links.py [--check]
"""
from __future__ import annotations

import argparse
import re
import sys

# term -> url, per file. Terms are matched case-insensitively on a word
# boundary, and the matched text is preserved.
LINKS = {
    "docs/concepts/ontology.mdx": [
        ("RDF", "https://www.w3.org/RDF/"),
        ("OWL", "https://www.w3.org/OWL/"),
        ("IRI", "https://en.wikipedia.org/wiki/Internationalized_Resource_Identifier"),
    ],
    "docs/concepts/knowledge-graph.mdx": [
        ("graph database", "https://en.wikipedia.org/wiki/Graph_database"),
        ("graph query language", "https://en.wikipedia.org/wiki/Cypher_(query_language)"),
    ],
    "docs/concepts/naming-and-standards.mdx": [
        ("ISA-5.1", "https://en.wikipedia.org/wiki/Piping_and_instrumentation_diagram"),
        ("IEC/ISO 81346", "https://en.wikipedia.org/wiki/IEC_81346"),
        ("ISO 15926", "https://en.wikipedia.org/wiki/ISO_15926"),
        ("NORSOK", "https://en.wikipedia.org/wiki/NORSOK_standard"),
        ("CFIHOS", "https://www.jip36-cfihos.org/"),
        ("P&ID", "https://en.wikipedia.org/wiki/Piping_and_instrumentation_diagram"),
    ],
    "docs/concepts/lineage-and-quality.mdx": [
        ("provenance", "https://en.wikipedia.org/wiki/Provenance"),
        ("interpolated", "https://en.wikipedia.org/wiki/Interpolation"),
    ],
    "docs/concepts/three-layers.mdx": [
        ("KPI", "https://en.wikipedia.org/wiki/Performance_indicator"),
    ],
    "docs/start/industry-4.mdx": [
        ("interchangeable parts", "https://en.wikipedia.org/wiki/Interchangeable_parts"),
        ("programmable logic controllers", "https://en.wikipedia.org/wiki/Programmable_logic_controller"),
        ("Hannover Fair", "https://en.wikipedia.org/wiki/Hannover_Messe"),
        ("robotics", "https://en.wikipedia.org/wiki/Robotics"),
    ],
    "docs/start/data-liberation.mdx": [
        ("AGPL-3.0", "https://en.wikipedia.org/wiki/GNU_Affero_General_Public_License"),
        ("open formats", "https://en.wikipedia.org/wiki/Open_format"),
    ],
    "docs/start/the-data-problem.mdx": [
        ("historian", "https://en.wikipedia.org/wiki/Operational_historian"),
        ("ERP", "https://en.wikipedia.org/wiki/Enterprise_resource_planning"),
    ],
    "docs/using/timeseries.mdx": [
        ("floating point", "https://en.wikipedia.org/wiki/Floating-point_arithmetic"),
        ("step series", "https://en.wikipedia.org/wiki/Step_function"),
    ],
    "docs/using/relationship-analysis.mdx": [
        ("coherence", "https://en.wikipedia.org/wiki/Coherence_(signal_processing)"),
        ("correlation", "https://en.wikipedia.org/wiki/Cross-correlation"),
    ],
    "docs/using/cdc-integrations.mdx": [
        ("change log", "https://en.wikipedia.org/wiki/Write-ahead_logging"),
        ("publication name", "https://www.postgresql.org/docs/current/logical-replication.html"),
    ],
    "docs/value/industry-examples.mdx": [
        ("OSPAR", "https://en.wikipedia.org/wiki/OSPAR_Convention"),
        ("produced water", "https://en.wikipedia.org/wiki/Produced_water"),
        ("hydrate", "https://en.wikipedia.org/wiki/Clathrate_hydrate"),
        ("soft sensor", "https://en.wikipedia.org/wiki/Soft_sensor"),
        ("demulsifier", "https://en.wikipedia.org/wiki/Demulsifier"),
    ],
    "docs/value/ai-agents.mdx": [
        ("large language model", "https://en.wikipedia.org/wiki/Large_language_model"),
        ("anomaly", "https://en.wikipedia.org/wiki/Anomaly_detection"),
    ],
    "docs/value/cost-of-doing-nothing.mdx": [
        ("opportunity cost", "https://en.wikipedia.org/wiki/Opportunity_cost"),
        ("sunk cost", "https://en.wikipedia.org/wiki/Sunk_cost"),
    ],
    "docs/value/board-briefing.mdx": [
        ("AGPL-3.0", "https://en.wikipedia.org/wiki/GNU_Affero_General_Public_License"),
    ],
    "docs/administration/identity-providers.mdx": [
        ("OAuth2/OIDC", "https://en.wikipedia.org/wiki/OpenID_Connect"),
        ("Keycloak", "https://www.keycloak.org/"),
        ("RFC 7523", "https://datatracker.ietf.org/doc/html/rfc7523"),
    ],
    "docs/administration/security.mdx": [
        ("ISO/IEC 27001", "https://en.wikipedia.org/wiki/ISO/IEC_27001"),
        ("air-gapped", "https://en.wikipedia.org/wiki/Air_gap_(networking)"),
        ("checksum", "https://en.wikipedia.org/wiki/Checksum"),
    ],
    "docs/administration/organizations.mdx": [
        ("Neo4j", "https://en.wikipedia.org/wiki/Neo4j"),
        ("multi-tenancy", "https://en.wikipedia.org/wiki/Multitenancy"),
    ],
    "docs/administration/data-lifecycle.mdx": [
        ("time-to-live", "https://en.wikipedia.org/wiki/Time_to_live"),
    ],
}


def protect(text):
    """Mask everything a link must not be injected into."""
    stash = []

    def keep(m):
        stash.append(m.group(0))
        return f"\x00{len(stash) - 1}\x00"

    patterns = [
        r"^---\n.*?\n---\n",                 # front matter
        r"<References>.*?</References>",     # the reference block itself
        r"```.*?```",                        # fenced code
        r"`[^`\n]*`",                        # inline code
        r"\[[^\]]*\]\([^)]*\)",              # existing markdown links
        r"<[A-Za-z/][^>]*>",                 # JSX / HTML tags and attributes
    ]
    for pat in patterns:
        text = re.sub(pat, keep, text, flags=re.S | re.M)
    return text, stash


def restore(text, stash):
    while "\x00" in text:
        text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


def add_links(text, terms):
    body, stash = protect(text)
    added = []
    # longest first, so "IEC/ISO 81346" wins over a shorter overlapping term
    for term, url in sorted(terms, key=lambda t: -len(t[0])):
        pat = re.compile(r"(?<![\w/-])(" + re.escape(term) + r")(?![\w-])", re.I)
        m = pat.search(body)
        if not m:
            continue
        body = body[:m.start()] + f"[{m.group(1)}]({url})" + body[m.end():]
        added.append(term)
    return restore(body, stash), added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    total = 0
    for path, terms in LINKS.items():
        try:
            src = open(path, encoding="utf-8").read()
        except FileNotFoundError:
            print(f"  MISSING {path}")
            continue
        out, added = add_links(src, terms)
        missed = [t for t, _ in terms if t not in added]
        if out != src and not args.check:
            open(path, "w", encoding="utf-8").write(out)
        total += len(added)
        note = f"  (not found: {', '.join(missed)})" if missed else ""
        print(f"  {path}: +{len(added)}{note}")

    print(f"\n{total} inline links {'would be' if args.check else ''} added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
