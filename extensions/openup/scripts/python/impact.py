#!/usr/bin/env python3
"""Report what a change to one artifact reaches.

specup.md s52 asks for a computed impact set before a governed artifact is changed, and s22
for the reverse query — "what requirements does this file affect?". The graph already answers
both; nothing exposed it.

    impact.py --of REQ-AUTH-0014                        what changing this requirement touches
    impact.py --of src/auth/authentication_service.ts   what this file affects, upstream

This is a REPORT, not a gate: it always exits 0 when the graph loads (2 if it does not). An
impact set is information for a human decision, and a validator that refused a change because
it had consequences would refuse every change worth making.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from openup_model import GraphError, Grammar, base_parser, load_graph, write_out

# Traversal is undirected for the same reason TRC-007's reachability is: impact does not
# follow the arrows. A file is modified by a task that implements a requirement, so the path
# from file to requirement runs against one edge — and a requirement's blast radius includes
# both what refines it and what implements it.
MAX_HOPS = 6

GROUPS: list[tuple[str, tuple[str, ...]]] = [
    ("Business objectives", ("business-objective",)),
    ("Requirements", ("requirement", "non-functional-requirement")),
    ("User stories & features", ("user-story", "feature", "flow")),
    ("Acceptance criteria", ("acceptance-criterion",)),
    ("Scenarios", ("scenario",)),
    ("Architecture decisions", ("architecture-decision", "security-decision")),
    ("WBS nodes", ("wbs-node", "task")),
    ("Risks", ("risk",)),
    ("Contracts", ("contract", "microcks-test")),
    ("Tests", ("test-case", "unit-test", "integration-test", "e2e-test")),
    ("Source files", ("source-artifact",)),
    ("Evidence", ("evidence",)),
    ("Iterations & gates", ("iteration", "gate")),
]


def _neighbours(graph, node: str) -> list[tuple[str, str, str]]:
    """(id, relation, direction) for everything one hop away, both directions."""
    out = [(e.to_id, e.relation, "→") for e in graph.out.get(node, []) if e.status != "broken"]
    inc = [(e.from_id, e.relation, "←") for e in graph.inc.get(node, []) if e.status != "broken"]
    return out + inc


def impact(graph, start: str) -> dict[str, dict[str, Any]]:
    """Breadth-first closure from `start`, recording how each node was reached."""
    reached: dict[str, dict[str, Any]] = {}
    frontier = [start]
    seen = {start}
    for distance in range(1, MAX_HOPS + 1):
        nxt: list[str] = []
        for node in frontier:
            for neighbour, relation, direction in _neighbours(graph, node):
                if neighbour in seen:
                    continue
                seen.add(neighbour)
                reached[neighbour] = {"hops": distance, "via": f"{node} {direction}{relation}"}
                nxt.append(neighbour)
        if not nxt:
            break
        frontier = nxt
    return reached


def _title(graph, identifier: str) -> str:
    for store in (graph.artifacts, graph.wbs, graph.risks):
        if identifier in store:
            return store[identifier].get("title") or store[identifier].get("name") or ""
    return ""


def main() -> int:
    parser = base_parser(__doc__.splitlines()[0])
    parser.add_argument("--of", required=True, metavar="ID",
                        help="the artifact id or source path that is changing")
    args = parser.parse_args()

    try:
        graph, _ = load_graph(args.root)
    except GraphError as exc:
        payload = {"validator": "impact", "status": "ERROR", "error": str(exc)}
        write_out(args.out, payload)
        print(json.dumps(payload, indent=2) if args.json else f"ERROR: {exc}",
              file=sys.stdout if args.json else sys.stderr)
        return 2

    target = args.of
    if not graph.exists(target):
        payload = {"validator": "impact", "status": "ERROR",
                   "error": f"{target} does not resolve to a known artifact, WBS node, risk or file"}
        write_out(args.out, payload)
        print(json.dumps(payload, indent=2) if args.json else f"ERROR: {payload['error']}",
              file=sys.stdout if args.json else sys.stderr)
        return 2

    reached = impact(graph, target)
    grammar: Grammar = graph.grammar
    grouped: dict[str, list[dict[str, Any]]] = {}
    for identifier, detail in reached.items():
        artifact_type = grammar.type_of(identifier) or "unknown"
        label = next((name for name, types in GROUPS if artifact_type in types), "Other")
        grouped.setdefault(label, []).append(
            {"id": identifier, "type": artifact_type, "title": _title(graph, identifier), **detail}
        )
    for entries in grouped.values():
        entries.sort(key=lambda item: (item["hops"], item["id"]))

    payload = {
        "validator": "impact", "status": "PASS", "of": target,
        "type": grammar.type_of(target), "reached": len(reached),
        "groups": {name: grouped[name] for name, _ in GROUPS if name in grouped},
        "other": grouped.get("Other", []),
    }
    write_out(args.out, payload)

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    heading = f"Impact of changing {target}"
    print(heading)
    print("=" * len(heading))
    if not reached:
        print("\n  Nothing. This artifact has no edges — which for a governed artifact is "
              "itself the finding (TRC-008 calls it an orphan).")
        return 0
    for name, _ in GROUPS + [("Other", ())]:
        entries = grouped.get(name)
        if not entries:
            continue
        print(f"\n{name} ({len(entries)})")
        for entry in entries:
            title = f"  {entry['title']}" if entry["title"] else ""
            print(f"  {entry['id']}{title}")
            print(f"      {entry['hops']} hop(s), via {entry['via']}")
    print(f"\n  {len(reached)} artifact(s) reached within {MAX_HOPS} hops.")
    print("  Traversal is undirected: impact does not follow the arrows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
