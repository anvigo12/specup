#!/usr/bin/env python3
"""Validate the Work Breakdown Structure.

Enforces the invariants of specup.md s18 and s32 that JSON Schema cannot express,
because they are properties of the graph rather than of any single node.

Depth policy (openup-config.yml wbs.depth_policy):
  semantic  levels keep fixed meanings, but a leaf may terminate above L7 when it
            declares terminal_reason. Resolves s18 against s65.
  strict    s18 read literally - every leaf must be L7.
"""

from __future__ import annotations

import sys
from typing import Any

from openup_model import (
    Verdict,
    base_parser,
    load_graph,
    record,
    run,
    schema_errors,
    wbs_level,
    wbs_parent_id,
    wbs_segments,
)

LEVEL_NAMES = {
    1: "Program / Product",
    2: "OpenUP Phase",
    3: "Iteration",
    4: "Capability / Feature",
    5: "Requirement / User Story",
    6: "Engineering Work Package",
    7: "Executable Task",
}

PHASE_LETTER = {"INCEPTION": "I", "ELABORATION": "E", "CONSTRUCTION": "C", "TRANSITION": "T"}


def validate(args: Any) -> Verdict:
    graph, config = load_graph(args.root)
    verdict = Verdict("validate-wbs")
    policy = config["wbs"].get("depth_policy", "semantic")
    never_terminal_above = config["wbs"].get("never_terminal_above", 3)
    max_children = config["wbs"].get("max_children_warn", 25)

    if not graph.wbs:
        verdict.fail("WBS-000", "no WBS found; run /speckit.openup.wbs to create one")
        return verdict

    # WBS-000 — document shape
    errors = schema_errors(graph.wbs_doc, "wbs.schema.json")
    if errors:
        verdict.fail("WBS-000", f"wbs.yaml violates the schema ({len(errors)} error(s))", errors)
    else:
        verdict.ok("WBS-000", "wbs.yaml conforms to wbs.schema.json")

    # WBS-001 — the id encodes the level, so they must agree
    mismatched = [
        f"{nid}: level {node.get('level')} but id has {wbs_level(nid)} segment(s)"
        for nid, node in graph.wbs.items()
        if node.get("level") != wbs_level(nid)
    ]
    record(verdict, "WBS-001", mismatched, "declared level matches the id's segment count")

    # WBS-002 — parent is the id minus its last segment, and it exists
    bad_parents: list[str] = []
    for nid, node in graph.wbs.items():
        expected = wbs_parent_id(nid)
        declared = node.get("parent")
        if expected is None:
            if declared:
                bad_parents.append(f"{nid}: L1 root must not declare a parent (got {declared})")
            continue
        if declared != expected:
            bad_parents.append(f"{nid}: parent should be {expected}, got {declared or 'none'}")
        elif expected not in graph.wbs:
            bad_parents.append(f"{nid}: parent {expected} does not exist")
    record(verdict, "WBS-002", bad_parents, "every node has exactly one existing parent")

    # WBS-003 — exactly one root
    roots = [nid for nid in graph.wbs if wbs_level(nid) == 1]
    if len(roots) == 1:
        verdict.ok("WBS-003", f"exactly one L1 root ({roots[0]})")
    else:
        verdict.fail(
            "WBS-003",
            f"expected exactly one L1 root, found {len(roots)}",
            roots or ["no L1 node defined"],
        )

    # WBS-004 — leaf depth policy
    leaves = [nid for nid in graph.wbs if graph.is_leaf(nid)]
    bad_leaves: list[str] = []
    early_terminations: list[str] = []
    for nid in leaves:
        level = wbs_level(nid)
        if level == 7:
            continue
        if level <= never_terminal_above:
            bad_leaves.append(
                f"{nid}: L{level} ({LEVEL_NAMES.get(level, '?')}) is pure structure and "
                f"may never be a leaf"
            )
        elif policy == "strict":
            bad_leaves.append(f"{nid}: L{level} leaf, but depth_policy is 'strict' (every leaf must be L7)")
        elif not graph.wbs[nid].get("terminal_reason"):
            bad_leaves.append(f"{nid}: L{level} leaf terminates above L7 without a terminal_reason")
        else:
            early_terminations.append(nid)
    record(verdict, "WBS-004", bad_leaves, f"all {len(leaves)} leaves satisfy depth_policy '{policy}'")

    # WBS-005..007 — referenced ids resolve
    _check_refs(verdict, graph, "WBS-005", "requirements", graph.artifacts, "requirement")
    _check_refs(verdict, graph, "WBS-006", "risks", graph.risks, "risk")
    _check_refs(verdict, graph, "WBS-007", "acceptance", graph.artifacts, "acceptance criterion")

    # WBS-008 — dependencies exist
    missing_deps = [
        f"{nid}: depends on {dep}, which does not exist"
        for nid, node in graph.wbs.items()
        for dep in node.get("dependencies", []) or []
        if dep not in graph.wbs
    ]
    record(verdict, "WBS-008", missing_deps, "all dependency targets exist")

    # WBS-009 — dependency graph is acyclic
    cycle = _dependency_cycle(graph.wbs)
    if cycle:
        verdict.fail("WBS-009", "dependency cycle detected", [" -> ".join(cycle)])
    else:
        verdict.ok("WBS-009", "dependency graph is acyclic")

    # WBS-010 — iteration letter agrees with the node's phase
    inconsistent = []
    for nid, node in graph.wbs.items():
        phase, iteration = node.get("phase"), node.get("iteration")
        if phase and iteration and iteration.split("-")[1] != PHASE_LETTER.get(phase):
            inconsistent.append(f"{nid}: iteration {iteration} does not belong to phase {phase}")
    record(verdict, "WBS-010", inconsistent, "iterations agree with their node's phase")

    # WBS-011 — breadth warning: a very wide parent usually means a missing level
    wide = [
        f"{parent}: {len(kids)} children (> {max_children})"
        for parent, kids in graph.children.items()
        if len(kids) > max_children
    ]
    if wide:
        verdict.warn("WBS-011", "some parents may be missing an intermediate level", wide)
    else:
        verdict.ok("WBS-011", "no parent exceeds the child-count warning threshold")

    counts = {f"L{level}": 0 for level in range(1, 8)}
    for nid in graph.wbs:
        counts[f"L{wbs_level(nid)}"] += 1
    verdict.metrics = {
        "levels": counts,
        "total_nodes": len(graph.wbs),
        "leaves": len(leaves),
        "early_terminations": len(early_terminations),
        "depth_policy": policy,
    }
    return verdict


def _check_refs(
    verdict: Verdict, graph: Any, check_id: str, field: str, universe: dict, label: str
) -> None:
    missing = [
        f"{nid}: references {ref}, which is not a registered {label}"
        for nid, node in graph.wbs.items()
        for ref in node.get(field, []) or []
        if ref not in universe
    ]
    record(verdict, check_id, missing, f"all referenced {label} ids resolve")


def _dependency_cycle(nodes: dict[str, dict]) -> list[str] | None:
    """Iterative DFS over `dependencies`, returning one cycle if present."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {nid: WHITE for nid in nodes}
    for start in nodes:
        if colour[start] != WHITE:
            continue
        stack = [(start, iter(nodes[start].get("dependencies", []) or []))]
        path = [start]
        colour[start] = GREY
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if child not in colour:
                    continue
                if colour[child] == GREY:
                    return path[path.index(child):] + [child]
                if colour[child] == WHITE:
                    colour[child] = GREY
                    path.append(child)
                    stack.append((child, iter(nodes[child].get("dependencies", []) or [])))
                    advanced = True
                    break
            if not advanced:
                colour[node] = BLACK
                stack.pop()
                if path:
                    path.pop()
    return None


if __name__ == "__main__":
    sys.exit(run(validate, base_parser(__doc__.splitlines()[0])))
