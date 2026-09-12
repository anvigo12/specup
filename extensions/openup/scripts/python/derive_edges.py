#!/usr/bin/env python3
"""Report or regenerate the machine-derivable traceability edges.

Without `--write` this reports what the implemented rules in derivers.py recover and how the
graph compares, under the usual contract: exit 0 if the store already holds every derivable
edge, exit 1 if it is behind, exit 2 if the graph will not load. That makes it usable as a
workflow `shell` step as well as a fix-it command.

With `--write` it regenerates the machine-owned store wholesale. That store is listed in
`traceability.stores` alongside the hand-maintained ones and is the ONLY place a derived edge
should live: a rule that can recompute an edge should not be competing with a human copy of
it, and a file that is rewritten in full has no room for a hand edit to survive in.
"""

from __future__ import annotations

import datetime
import pathlib
import sys

import derivers
from openup_model import SKIP, GraphError, Verdict, base_parser, load_graph, run

DEFAULT_STORE = ".specify/traceability/derived.yaml"

HEADER = """\
# GENERATED — do not edit. Regenerate with:
#   python derive_edges.py --write
#
# Every edge here was recomputed from the filesystem by the rule named in `derived_by`.
# validate_trace.py TRC-010 re-runs those rules and fails any edge they do not reproduce,
# so hand-editing this file does not make a claim true — it only makes the graph fail.
"""


def _store_path(args) -> pathlib.Path:
    """The machine-owned store: whichever configured store is named derived.yaml."""
    _, config = load_graph(args.root)
    for candidate in config["traceability"]["stores"]:
        if candidate.endswith("derived.yaml") and "*" not in candidate:
            return pathlib.Path(args.root) / candidate
    return pathlib.Path(args.root) / DEFAULT_STORE


def write_store(args) -> int:
    graph, _ = load_graph(args.root)
    derivations = derivers.derive_all(graph)
    target = _store_path(args)

    lines = [HEADER, 'schema_version: "1.0"',
             f'generated_at: "{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"',
             "", "edges:"]
    total = 0
    for rule in sorted(derivations):
        triples = sorted(derivations[rule].triples)
        if not triples:
            continue
        lines.append(f"  # {rule}")
        for source, relation, sink in triples:
            lines += [f"  - from: {source}", f"    relation: {relation}", f"    to: {sink}",
                      "    provenance: derived", f"    derived_by: {rule}"]
        total += len(triples)

    if total == 0:
        lines[-1] = "edges: []"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n")

    relative = target.relative_to(pathlib.Path(args.root).resolve()) if target.is_absolute() else target
    print(f"wrote {total} derived edge(s) to {relative}")
    for rule in sorted(derivations):
        for note in derivations[rule].notes:
            print(f"  [{rule}] {note}")
    return 0


def validate(args) -> Verdict:
    graph, _ = load_graph(args.root)
    verdict = Verdict("derive-edges")
    derivations = derivers.derive_all(graph)
    produced = derivers.triples_by_rule(derivations)
    stored = {edge.triple for edge in graph.edges}

    missing = [f"{rule}: {source} --{relation}--> {sink}"
               for (source, relation, sink), rule in sorted(produced.items())
               if (source, relation, sink) not in stored]
    if missing:
        verdict.fail("DRV-001", f"{len(missing)} derivable edge(s) missing from the graph", missing)
    else:
        verdict.ok("DRV-001", f"all {len(produced)} derivable edge(s) are present")

    # A triple a rule can recompute but the graph records as a human claim. Not a failure —
    # understating evidence is the safe direction — but it is free coverage left on the floor.
    understated = [f"{edge} is recorded as '{edge.provenance}' but {produced[edge.triple]} reproduces it"
                   for edge in graph.edges
                   if edge.triple in produced and edge.provenance != "derived"]
    if understated:
        verdict.warn("DRV-002", f"{len(understated)} edge(s) understate their own provenance", understated)
    else:
        verdict.ok("DRV-002", "no edge understates its provenance")

    notes = [f"[{rule}] {note}" for rule in sorted(derivations) for note in derivations[rule].notes]
    if notes:
        verdict.warn("DRV-003", f"{len(notes)} input(s) a rule could not use", notes)
    else:
        verdict.ok("DRV-003", "every scanned input produced an edge")

    if derivers.UNIMPLEMENTED_RULES:
        verdict.add("DRV-004", SKIP,
                    f"{len(derivers.UNIMPLEMENTED_RULES)} of {len(derivers.KNOWN_RULES)} declared "
                    f"rules are not implemented; edges naming them cannot be reproduced",
                    [f"{rule}: {describes}"
                     for rule, describes in sorted(derivers.UNIMPLEMENTED_RULES.items())])

    verdict.metrics = {
        "rules_implemented": len(derivers.RULES),
        "rules_declared": len(derivers.KNOWN_RULES),
        "derivable_edges": len(produced),
        "missing_from_graph": len(missing),
        "by_rule": {rule: len(derivation.triples) for rule, derivation in sorted(derivations.items())},
    }
    return verdict


def main() -> int:
    parser = base_parser(__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true",
                        help="regenerate the machine-owned derived store instead of reporting")
    if "--write" in sys.argv[1:]:
        args = parser.parse_args()
        try:
            return write_store(args)
        except GraphError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    return run(validate, parser)


if __name__ == "__main__":
    sys.exit(main())
