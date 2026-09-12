#!/usr/bin/env python3
"""Validate the bi-directional traceability graph.

specup.md s20-s22 asks for a graph that answers both "what implements this requirement?"
and "what requirements does this file affect?". Edges are stored once in active voice;
this validator derives the inverse direction rather than trusting a second hand-maintained
dataset, which is what keeps the two directions from disagreeing.

The provenance mix (s3 of ID-GRAMMAR.md) is always reported: a graph that is overwhelmingly
'asserted' must not be able to present itself as fully covered. TRC-010 goes one step further
and re-runs the derivation rules in derivers.py, because a `derived` label nobody can
reproduce is an assertion with better marketing.
"""

from __future__ import annotations

import sys
from typing import Any

import derivers
from openup_model import ACYCLIC, SKIP, Verdict, base_parser, load_graph, run, schema_errors

REQUIREMENT_TYPES = {"requirement", "non-functional-requirement"}
TEST_TYPES = {"test-case", "unit-test", "integration-test"}
WORK_TYPES = {"wbs-node", "task"}

# Domain and range for each relation (ID-GRAMMAR.md s2). None means "any type".
SIGNATURES: dict[str, tuple[set[str] | None, set[str] | None]] = {
    "refines": ({"requirement", "non-functional-requirement", "user-story", "feature"},
                {"business-objective", "requirement", "feature"}),
    "contains": ({"wbs-node", "feature"}, {"wbs-node", "requirement"}),
    "decomposes-to": ({"wbs-node"}, {"wbs-node", "task"}),
    "implements": (WORK_TYPES | {"source-artifact"}, REQUIREMENT_TYPES),
    "modifies": ({"task"}, {"source-artifact"}),
    "verifies": ({"acceptance-criterion"} | TEST_TYPES, REQUIREMENT_TYPES),
    "executes": ({"scenario"}, {"acceptance-criterion"}),
    "tests": (TEST_TYPES, {"source-artifact"}),
    "conforms-to": ({"source-artifact"}, {"contract"}),
    "validates": ({"microcks-test"}, {"contract"}),
    "mitigates": (WORK_TYPES, {"risk"}),
    "evidences": ({"evidence"}, {"task", "gate", "risk", "wbs-node"}),
    "depends-on": ({"task", "wbs-node"}, {"task", "wbs-node"}),
    "belongs-to": ({"wbs-node", "task"}, {"iteration"}),
    "approves": (None, None),  # the subject is a human actor, which has no id form
    "supersedes": (None, None),
}


def validate(args: Any) -> Verdict:
    graph, config = load_graph(args.root)
    verdict = Verdict("validate-trace")
    grammar = graph.grammar
    thresholds = config["traceability"]["coverage_thresholds"]

    if not graph.edges:
        verdict.fail("TRC-000", "no traceability edges found; the graph is empty")
        verdict.metrics = {"edges": 0}
        return verdict

    for path in set(e.source_file for e in graph.edges if e.source_file):
        document = {
            "schema_version": "1.0",
            "edges": [
                {k: v for k, v in {
                    "from": e.from_id, "relation": e.relation, "to": e.to_id,
                    "provenance": e.provenance, "status": e.status,
                    "derived_by": e.derived_by, "evidence": e.evidence or None,
                }.items() if v is not None}
                for e in graph.edges if e.source_file == path
            ],
        }
        errors = schema_errors(document, "traceability.schema.json")
        if errors:
            verdict.fail("TRC-000", f"{path} violates the schema ({len(errors)} error(s))", errors)
            break
    else:
        verdict.ok("TRC-000", "all traceability stores conform to traceability.schema.json")

    # TRC-001 — duplicate triples across merged stores
    if graph.duplicate_edges:
        verdict.fail(
            "TRC-001",
            f"{len(graph.duplicate_edges)} duplicate edge(s) across merged stores",
            [f"{e} (in {e.source_file})" for e in graph.duplicate_edges],
        )
    else:
        verdict.ok("TRC-001", "no duplicate (from, relation, to) triples")

    # TRC-002 — both endpoints resolve
    broken = [
        f"{edge}: {'from' if not graph.exists(edge.from_id) else 'to'} endpoint does not resolve"
        f" (in {edge.source_file})"
        for edge in graph.edges
        if edge.status != "broken" and not (graph.exists(edge.from_id) and graph.exists(edge.to_id))
    ]
    _record(verdict, "TRC-002", broken, f"all {len(graph.edges)} edges resolve at both ends")

    # TRC-003 — relations are type-legal
    illegal = []
    for edge in graph.edges:
        allowed_from, allowed_to = SIGNATURES.get(edge.relation, (None, None))
        from_type = grammar.type_of(edge.from_id)
        to_type = grammar.type_of(edge.to_id)
        if allowed_from is not None and from_type not in allowed_from:
            illegal.append(f"{edge}: '{edge.relation}' cannot start at a {from_type or 'unknown id'}")
        if allowed_to is not None and to_type not in allowed_to:
            illegal.append(f"{edge}: '{edge.relation}' cannot end at a {to_type or 'unknown id'}")
    _record(verdict, "TRC-003", illegal, "every relation is legal for its endpoint types")

    # TRC-004 — acyclicity
    cycles = []
    for relation in ACYCLIC:
        cycle = graph.find_cycle(relation)
        if cycle:
            cycles.append(f"{relation}: {' -> '.join(cycle)}")
    _record(verdict, "TRC-004", cycles, f"no cycles on {', '.join(ACYCLIC)}")

    # TRC-005 / TRC-006 — forward coverage
    requirements = graph.requirements()
    unimplemented, unverified = [], []
    for req_id in requirements:
        implementers = [e for e in graph.inc.get(req_id, []) if e.relation == "implements"]
        verifiers = [e for e in graph.inc.get(req_id, []) if e.relation == "verifies"]
        if not implementers:
            unimplemented.append(f"{req_id}: nothing implements it")
        if not verifiers:
            unverified.append(f"{req_id}: nothing verifies it")

    forward = _ratio(len(requirements) - len(unimplemented), len(requirements))
    verified_ratio = _ratio(len(requirements) - len(unverified), len(requirements))
    forward_target = thresholds.get("forward", 1.0)

    _threshold(verdict, "TRC-005", forward, forward_target,
               f"requirement-to-implementation coverage {forward:.0%}", unimplemented)
    _threshold(verdict, "TRC-006", verified_ratio, forward_target,
               f"requirement-to-verification coverage {verified_ratio:.0%}", unverified)

    # TRC-007 — backward coverage over the perimeter
    perimeter = graph.perimeter_files()
    untraced = [f"{path}: not reachable from any requirement" for path in perimeter
                if not _reaches_requirement(graph, path)]
    backward = _ratio(len(perimeter) - len(untraced), len(perimeter))
    _threshold(verdict, "TRC-007", backward, thresholds.get("backward", 0.95),
               f"backward coverage {backward:.0%} over {len(perimeter)} in-perimeter file(s)", untraced)

    # TRC-008 — orphans (s54)
    orphans = []
    orphans += [f"orphan requirement: {r}" for r in requirements
                if not graph.inc.get(r) and not graph.out.get(r)]
    orphans += [f"orphan WBS node: {n}" for n, node in graph.wbs.items()
                if graph.is_leaf(n) and not node.get("requirements")
                and not graph.out.get(n) and node.get("kind") != "structural"]
    # Only high-exposure risks can be orphans: accepting a low-exposure risk without
    # mitigation work is a legitimate choice, not a gap in the graph.
    high_threshold = config["risk"].get("high_exposure_threshold", 0.40)
    orphans += [
        f"orphan risk: {r} (exposure {risk['probability'] * risk['impact']:.2f})"
        for r, risk in graph.risks.items()
        if not (risk.get("mitigation") or [])
        and risk.get("status") not in {"closed", "accepted"}
        and risk.get("probability", 0) * risk.get("impact", 0) >= high_threshold
    ]
    orphans += [f"orphan scenario: {a}" for a in graph.artifacts
                if grammar.type_of(a) == "scenario" and not graph.follow(a, "executes")]
    _record(verdict, "TRC-008", orphans, "no orphan artifacts")

    # TRC-009 — provenance of edges touching baselined artifacts
    minimum = config["traceability"].get("baseline_min_provenance", "approved")
    rank = {"derived": 0, "asserted": 1, "approved": 2}
    # Scoped to requirements, per ID-GRAMMAR.md s3: "Baseline gates require 'approved' for
    # requirement-level edges." A verified test case does not need an approved edge to exist.
    baselined = {
        aid for aid, art in graph.artifacts.items()
        if art.get("status") in {"BASELINED", "IMPLEMENTED", "VERIFIED", "ACCEPTED"}
        and grammar.is_requirement(aid)
    }
    weak = [
        f"{edge}: touches baselined {edge.to_id if edge.to_id in baselined else edge.from_id} "
        f"with provenance '{edge.provenance}' (minimum '{minimum}')"
        for edge in graph.edges
        if (edge.from_id in baselined or edge.to_id in baselined)
        and edge.provenance != "derived"
        and rank[edge.provenance] < rank[minimum]
    ]
    _record(verdict, "TRC-009", weak, f"edges on baselined artifacts meet provenance '{minimum}'")

    # TRC-010 / TRC-011 / TRC-012 — is 'derived' true, or only claimed?
    derivations = derivers.derive_all(graph)
    produced = derivers.triples_by_rule(derivations)
    stored = {edge.triple for edge in graph.edges}

    false_claims: list[str] = []
    verified = unverified = 0
    for edge in graph.edges:
        if edge.provenance != "derived":
            continue
        rule = edge.derived_by
        if rule is None:
            continue  # schema violation; TRC-000 owns it
        if rule not in derivers.KNOWN_RULES:
            false_claims.append(f"{edge}: derived_by '{rule}' names no known derivation rule")
        elif rule in derivers.UNIMPLEMENTED_RULES:
            unverified += 1
        elif edge.triple in derivations[rule].triples:
            verified += 1
        else:
            false_claims.append(
                f"{edge}: claims derived_by '{rule}', but that rule does not reproduce it "
                f"from the filesystem — the edge is an assertion wearing a derived label"
            )
    _record(verdict, "TRC-010", false_claims,
            f"{verified} derived edge(s) reproduced by the rule they name"
            + (f"; {unverified} await an unimplemented rule" if unverified else ""))

    missing = [f"{rule} produces {' --'.join(triple[:2])}--> {triple[2]}, which no store declares"
               for triple, rule in sorted(produced.items()) if triple not in stored]
    _record(verdict, "TRC-011", missing,
            f"all {len(produced)} rule-derivable edge(s) are present in the graph")

    criteria = [aid for aid in graph.artifacts if grammar.type_of(aid) == "acceptance-criterion"]
    uncovered = [f"{aid}: no scenario executes it" for aid in sorted(criteria)
                 if not graph.follow(aid, "executes", reverse=True)]
    scenario_coverage = _ratio(len(criteria) - len(uncovered), len(criteria))
    if not config["gherkin"].get("require_scenario_per_ac", True):
        verdict.add("TRC-012", SKIP, "gherkin.require_scenario_per_ac is disabled in config")
    else:
        _record(verdict, "TRC-012", uncovered,
                f"all {len(criteria)} acceptance criterion(s) have at least one scenario")

    mix = {level: sum(1 for e in graph.edges if e.provenance == level)
           for level in ("derived", "asserted", "approved")}
    verdict.metrics = {
        "edges": len(graph.edges),
        "requirements": len(requirements),
        "forward_coverage": round(forward, 4),
        "verification_coverage": round(verified_ratio, 4),
        "backward_coverage": round(backward, 4),
        "perimeter_files": len(perimeter),
        "orphans": len(orphans),
        "provenance_mix": mix,
        "asserted_share": round(_ratio(mix["asserted"], len(graph.edges)), 4),
        # 'derived' is only as good as the rule behind it. These split the label into what a
        # rule actually reproduced and what is merely waiting on one, so the audit cannot
        # present an unimplemented rule as machine-checkable evidence.
        "derived_verified": verified,
        "derived_unverified": unverified,
        "acceptance_criteria": len(criteria),
        "scenario_coverage": round(scenario_coverage, 4),
    }
    return verdict


def _ratio(numerator: int, denominator: int) -> float:
    return 1.0 if denominator == 0 else numerator / denominator


def _record(verdict: Verdict, check_id: str, failures: list[str], ok_message: str) -> None:
    if failures:
        verdict.fail(check_id, f"{len(failures)} violation(s)", failures)
    else:
        verdict.ok(check_id, ok_message)


def _threshold(
    verdict: Verdict, check_id: str, actual: float, target: float, message: str, evidence: list[str]
) -> None:
    if actual + 1e-9 >= target:
        verdict.ok(check_id, f"{message} meets the {target:.0%} threshold")
    else:
        verdict.fail(check_id, f"{message} is below the {target:.0%} threshold", evidence)


def _reaches_requirement(graph: Any, start: str, max_hops: int = 6) -> bool:
    """Undirected reachability from a node to any requirement.

    Undirected on purpose: a file is traced if it is *connected* to intent, whichever
    way the edges happen to point (a task modifies a file and implements a requirement,
    so the path from file to requirement runs against one arrow).
    """
    seen = {start}
    frontier = [start]
    for _ in range(max_hops):
        nxt = []
        for node in frontier:
            neighbours = [e.to_id for e in graph.out.get(node, [])]
            neighbours += [e.from_id for e in graph.inc.get(node, [])]
            for neighbour in neighbours:
                if neighbour in seen:
                    continue
                if graph.grammar.is_requirement(neighbour):
                    return True
                seen.add(neighbour)
                nxt.append(neighbour)
        if not nxt:
            return False
        frontier = nxt
    return False


if __name__ == "__main__":
    sys.exit(run(validate, base_parser(__doc__.splitlines()[0])))
