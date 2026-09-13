#!/usr/bin/env python3
"""Check the Definition of Done against the graph, for every node claiming to be done.

specup.md s29 is explicit about the standard it asks for:

    TASK-042.status = DONE is a computed governance state rather than a casual AI declaration.

Until this script it was exactly a casual declaration — an agent wrote `status: done` and
nothing disagreed. The asymmetry was the tell: select_work.py blocked work from *starting*
on evidence, while nothing stopped work being called *finished* on a claim. Of the two, the
claim a gate depends on is the second one.

This is the mirror of select_work.py, and deliberately shaped like it: a declarative rule
table that render_views.py publishes as .specify/governance/definition-of-done.md, so the
document people read is the check the machine applies.

    validate_done.py --json

Exit 0 if every node claiming done survives the check, 1 if any does not, 2 if the graph
will not load.
"""

from __future__ import annotations

import sys
from typing import Any

from openup_model import Verdict, base_parser, load_graph, run

DONE_STATUS = "done"

# The Definition of Done (s29), stated once. Each entry is (check id, what it means).
# Two of s29's clauses are deliberately absent: "Contract tests passing" and "Microcks
# conformance passing" have nothing behind them (see the README's Limitations), and a check
# that cannot fail is worse than a missing one — it reports compliance it never established.
DONE_RULES: dict[str, str] = {
    "DOD-001": "Evidence is recorded, and every evidence reference resolves",
    "DOD-002": "Every linked requirement is both implemented and verified in the graph",
    "DOD-003": "Every linked acceptance criterion has a scenario executing it",
    "DOD-004": "A `risk-mitigation` task has reduced its risk, with evidence on the risk",
    "DOD-005": "No edge touching the node is marked `broken`",
    "DOD-006": "A `test` task names acceptance criteria, and each one is registered",
}


def _evidence_problems(graph, node_id: str, node: dict) -> list[str]:
    references = node.get("evidence", []) or []
    if not references:
        return [f"{node_id}: marked done with no evidence — s29 calls this a declaration, "
                f"not a governance state"]
    return [f"{node_id}: evidence {reference} does not resolve"
            for reference in references if not graph.exists(reference)]


def _requirement_problems(graph, node_id: str, node: dict) -> list[str]:
    problems = []
    for requirement in node.get("requirements", []) or []:
        incoming = graph.inc.get(requirement, [])
        if not any(e.relation == "implements" and e.status != "broken" for e in incoming):
            problems.append(f"{node_id}: {requirement} is not implemented by anything in the graph")
        if not any(e.relation == "verifies" and e.status != "broken" for e in incoming):
            problems.append(f"{node_id}: {requirement} is not verified by anything in the graph")
    return problems


def _acceptance_problems(graph, node_id: str, node: dict) -> list[str]:
    return [
        f"{node_id}: acceptance criterion {criterion} has no scenario executing it"
        for criterion in node.get("acceptance", []) or []
        if not graph.follow(criterion, "executes", reverse=True)
    ]


def _risk_problems(graph, node_id: str, node: dict) -> list[str]:
    if node.get("kind") != "risk-mitigation":
        return []
    problems = []
    for risk_id in node.get("risks", []) or []:
        risk = graph.risks.get(risk_id)
        if risk is None:
            problems.append(f"{node_id}: risk {risk_id} is not registered")
            continue
        if not (risk.get("evidence") or []):
            problems.append(f"{node_id}: mitigation is done but {risk_id} records no evidence")
        exposure = risk.get("probability", 0) * risk.get("impact", 0)
        residual = risk.get("residual_exposure")
        if residual is None:
            problems.append(f"{node_id}: mitigation is done but {risk_id} has no residual exposure — "
                            f"the reassessment was skipped")
        elif residual >= exposure:
            problems.append(f"{node_id}: mitigation is done but {risk_id} residual exposure "
                            f"{residual:.2f} is not below its current {exposure:.2f}")
    return problems


def _broken_edge_problems(graph, node_id: str, node: dict) -> list[str]:
    touching = graph.out.get(node_id, []) + graph.inc.get(node_id, [])
    return [f"{node_id}: edge {edge} is marked broken" for edge in touching
            if edge.status == "broken"]


def _test_task_problems(graph, node_id: str, node: dict) -> list[str]:
    if node.get("kind") != "test":
        return []
    criteria = node.get("acceptance", []) or []
    if not criteria:
        return [f"{node_id}: test task is done but names no acceptance criteria"]
    return [f"{node_id}: acceptance criterion {criterion} is not registered"
            for criterion in criteria if criterion not in graph.artifacts]


CHECKS = {
    "DOD-001": _evidence_problems,
    "DOD-002": _requirement_problems,
    "DOD-003": _acceptance_problems,
    "DOD-004": _risk_problems,
    "DOD-005": _broken_edge_problems,
    "DOD-006": _test_task_problems,
}


def validate(args: Any) -> Verdict:
    graph, _ = load_graph(args.root)
    verdict = Verdict("validate-done")

    done = {node_id: node for node_id, node in graph.wbs.items()
            if node.get("status") == DONE_STATUS and node.get("kind", "structural") != "structural"}

    incomplete: set[str] = set()
    for check_id, rule in DONE_RULES.items():
        problems: list[str] = []
        for node_id, node in sorted(done.items()):
            found = CHECKS[check_id](graph, node_id, node)
            problems += found
            if found:
                incomplete.add(node_id)
        if problems:
            verdict.fail(check_id, f"{len(problems)} violation(s): {rule}", problems)
        else:
            verdict.ok(check_id, f"{rule} — {len(done)} node(s) checked")

    verdict.metrics = {
        "done_claimed": len(done),
        "done_verified": len(done) - len(incomplete),
        "incomplete": sorted(incomplete),
    }
    return verdict


if __name__ == "__main__":
    sys.exit(run(validate, base_parser(__doc__.splitlines()[0])))
