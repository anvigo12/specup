#!/usr/bin/env python3
"""Record a human approval on one traceability edge.

`provenance: approved` requires an `approved_endpoints_hash` that binds the signature to
the content it was given for (validate_trace.py TRC-013 re-computes it and downgrades the
edge if it no longer matches). Nobody can produce that hash by hand, so shipping the check
without this tool would recreate the defect it closes: a required field nobody can write
correctly.

    approve_edge.py --from REQ-AUTH-0014 --relation refines --to BUS-OBJ-0017 \\
                    --by product-owner [--commit <sha>] [--note "..."]

The file is edited in place, one list item at a time, so the comments and ordering of a
hand-maintained store survive. Exit 0 on success, 1 if the approval is refused, 2 if the
graph will not load or the edge does not exist.

HONEST LIMIT: this binds an approval to content. It does not prove a human was involved —
an agent can run this command and pass --by product-owner. The only real anchor is
--commit pointing at a signed commit, verified against git, which is not implemented.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import sys

from openup_model import Edge, GraphError, approval_hash, base_parser, load_graph

# Keys this tool owns and rewrites. Everything else in the item is preserved verbatim.
OWNED_KEYS = ("provenance", "approval", "approved_endpoints_hash")


def _now() -> str:
    return f"{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"


def _find_edge(graph, from_id: str, relation: str, to_id: str) -> tuple[str, int, Edge]:
    """Locate the edge in the store that declares it. Returns (store, index, edge)."""
    for rel, doc in sorted(graph.raw_stores.items()):
        for index, raw in enumerate(doc.get("edges", []) or []):
            if (raw.get("from"), raw.get("relation"), raw.get("to")) == (from_id, relation, to_id):
                for edge in graph.edges:
                    if edge.triple == (from_id, relation, to_id):
                        return rel, index, edge
    raise GraphError(
        f"no edge {from_id} --{relation}--> {to_id} in any configured store; "
        f"declare it first, then approve it"
    )


def _item_bounds(lines: list[str], index: int) -> tuple[int, int, int]:
    """Line range [start, end) of the `index`-th item of the `edges:` list, and its key indent."""
    for position, line in enumerate(lines):
        if line.rstrip() == "edges:":
            break
    else:
        raise GraphError("store has no top-level `edges:` key")

    starts: list[int] = []
    item_indent: int | None = None
    end = len(lines)
    for position in range(position + 1, len(lines)):
        line = lines[position]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if item_indent is None:
            if not line.lstrip().startswith("- "):
                raise GraphError("`edges:` is not a list")
            item_indent = indent
        if indent < item_indent:
            end = position
            break
        if indent == item_indent and line.lstrip().startswith("- "):
            starts.append(position)

    if index >= len(starts):
        raise GraphError(f"store declares {len(starts)} edge(s); cannot reach index {index}")
    start = starts[index]
    stop = starts[index + 1] if index + 1 < len(starts) else end
    return start, stop, (item_indent or 0) + 2


def _rewrite_item(lines: list[str], start: int, stop: int, key_indent: int,
                  approval: dict, digest: str) -> list[str]:
    """Drop the keys this tool owns from one item and append the new ones."""
    kept: list[str] = []
    skipping = False
    for line in lines[start:stop]:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if skipping and (not stripped or indent > key_indent):
            continue  # a nested block belonging to a key we dropped
        skipping = False
        # The first line is "- from: ...", whose key sits at key_indent once the dash is gone.
        key = stripped[2:].split(":")[0] if stripped.startswith("- ") else stripped.split(":")[0]
        if indent <= key_indent and key in OWNED_KEYS:
            skipping = True
            continue
        kept.append(line)

    while kept and not kept[-1].strip():
        kept.pop()

    pad = " " * key_indent
    kept.append(f"{pad}provenance: approved")
    kept.append(f"{pad}approval:")
    for field in ("by", "at", "commit", "note"):
        if approval.get(field):
            kept.append(f"{pad}  {field}: {json.dumps(approval[field])}")
    kept.append(f"{pad}approved_endpoints_hash: {digest}")
    return kept


def approve(args) -> int:
    graph, config = load_graph(args.root)
    store, index, edge = _find_edge(graph, getattr(args, "from"), args.relation, args.to)

    if store.endswith("derived.yaml"):
        print(
            f"REFUSED: {store} is machine-owned and rewritten in full by derive_edges.py --write.\n"
            f"  A rule already reproduces this edge from the filesystem; a signature on it would "
            f"be erased on the next regeneration and adds nothing a rule does not already prove.",
            file=sys.stderr,
        )
        return 1
    if edge.provenance == "derived":
        print(
            f"REFUSED: {edge} claims provenance 'derived'.\n"
            f"  Approving it would replace reproducible evidence with a signature — strictly "
            f"weaker. Fix the claim or move the edge to a hand-maintained store first.",
            file=sys.stderr,
        )
        return 1
    if not (graph.exists(edge.from_id) and graph.exists(edge.to_id)):
        print(f"REFUSED: {edge} has an endpoint that does not resolve; approving a broken edge "
              f"records a signature on nothing.", file=sys.stderr)
        return 1

    approval = {"by": args.by, "at": args.at or _now()}
    if args.commit:
        approval["commit"] = args.commit
    if args.note:
        approval["note"] = args.note
    digest = approval_hash(graph, edge)

    path = pathlib.Path(graph.root) / store
    lines = path.read_text().splitlines()
    start, stop, key_indent = _item_bounds(lines, index)
    rewritten = lines[:start] + _rewrite_item(lines, start, stop, key_indent, approval, digest) \
        + lines[stop:]
    path.write_text("\n".join(rewritten) + "\n")

    payload = {
        "edge": str(edge), "store": store, "provenance": "approved",
        "approval": approval, "approved_endpoints_hash": digest,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"approved {edge}\n  in {store}\n  by {approval['by']} at {approval['at']}"
              f"\n  endpoints hash {digest[:12]}…")
    return 0


def main() -> int:
    parser = base_parser("Record a human approval on one traceability edge")
    parser.add_argument("--from", required=True, dest="from", metavar="ID",
                        help="the edge's source endpoint")
    parser.add_argument("--relation", required=True, help="the edge's relation")
    parser.add_argument("--to", required=True, metavar="ID", help="the edge's target endpoint")
    parser.add_argument("--by", required=True, metavar="WHO",
                        help="named human or role accountable for the approval")
    parser.add_argument("--at", default=None, metavar="TIMESTAMP",
                        help="ISO-8601 approval time (default: now)")
    parser.add_argument("--commit", default=None, metavar="SHA",
                        help="commit the approval is recorded in; a signed commit is the "
                             "strongest binding available")
    parser.add_argument("--note", default=None, help="why this was approved")
    args = parser.parse_args()

    try:
        return approve(args)
    except GraphError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
