#!/usr/bin/env python3
"""Select the executable work for the current iteration, Definition-of-Ready first.

specup.md s28: a task is not executable merely because it exists. This applies the Definition
of Ready and reports which tasks are genuinely ready and which are blocked and why.

Work is ordered risk-first (s39): tasks that reduce the highest exposure come first, so an
iteration attacks uncertainty before convenience.

    select_work.py --ids-only     a bare JSON array, for a workflow fan-out `items`
    select_work.py --json         the full verdict with blocking reasons
"""

from __future__ import annotations

import json
import sys
from typing import Any

from openup_model import Verdict, base_parser, load_graph, run, wbs_level

EXECUTABLE_STATUSES = {"planned", "ready"}
DONE_STATUSES = {"done", "cancelled"}

# The Definition of Ready (s28), stated once. render_views.py renders
# .specify/governance/definition-of-ready.md from this table, so the document a person reads
# and the rule the machine applies cannot drift. A hand-written DoR that disagrees with this
# code would be worse than none: people would follow the document while the code decided.
READINESS_RULES: dict[str, str] = {
    "DOR-001": "Linked to at least one requirement",
    "DOR-002": "Has a named owner",
    "DOR-003": "Assigned to an iteration",
    "DOR-004": "Executable: an L7 task, or a higher leaf that declares a `terminal_reason`",
    "DOR-005": "Every declared dependency exists and is done",
    "DOR-006": "A `test` task names the acceptance criteria it covers",
    "DOR-007": "A `risk-mitigation` task names the risk it reduces",
    "DOR-008": "Every linked requirement is registered and past `DRAFT`",
    "DOR-009": "Every capability contract it names exists (`skills/<name>/SKILL.md`)",
}


def _readiness(graph: Any, node_id: str, node: dict) -> list[str]:
    """Return the reasons this node is not ready. Empty means ready.

    Each blocker is tagged with the READINESS_RULES id it comes from, so a reader can trace
    a refusal back to the published Definition of Ready rather than guessing at it.
    """
    blockers: list[str] = []

    if not node.get("requirements"):
        blockers.append("DOR-001: no linked requirement")
    if not node.get("owner"):
        blockers.append("DOR-002: no owner")
    if not node.get("iteration"):
        blockers.append("DOR-003: not assigned to an iteration")

    level = wbs_level(node_id)
    if level < 7 and not node.get("terminal_reason"):
        blockers.append(f"DOR-004: L{level} node is not executable and declares no terminal_reason")

    for dependency in node.get("dependencies", []) or []:
        target = graph.wbs.get(dependency)
        if target is None:
            blockers.append(f"DOR-005: dependency {dependency} does not exist")
        elif target.get("status") not in DONE_STATUSES:
            blockers.append(
                f"DOR-005: dependency {dependency} is {target.get('status', 'unknown')}, not done")

    if node.get("kind") == "test" and not node.get("acceptance"):
        blockers.append("DOR-006: test task with no acceptance criteria")
    if node.get("kind") == "risk-mitigation" and not node.get("risks"):
        blockers.append("DOR-007: risk-mitigation task with no risk reference")

    # s28 lists "Applicable SKILL.md" in the Definition of Ready. Naming one that does not
    # exist is the same defect as naming a requirement that does not: the agent is sent to
    # look for guidance that is not there, and one willing to infer will invent it.
    for skill in node.get("skills", []) or []:
        if not (graph.root / "skills" / skill / "SKILL.md").is_file():
            blockers.append(f"DOR-009: skills/{skill}/SKILL.md does not exist")

    for requirement in node.get("requirements", []) or []:
        artifact = graph.artifacts.get(requirement)
        if artifact is None:
            blockers.append(f"DOR-008: requirement {requirement} is not registered")
        elif artifact.get("status") == "DRAFT":
            blockers.append(f"DOR-008: requirement {requirement} is still DRAFT, not approved")

    return blockers


def _risk_weight(graph: Any, node: dict) -> float:
    """Highest exposure among the risks this node mitigates; 0 if it mitigates none."""
    weights = [
        risk.get("probability", 0) * risk.get("impact", 0)
        for risk_id in node.get("risks", []) or []
        if (risk := graph.risks.get(risk_id))
    ]
    return max(weights, default=0.0)


def select(args: Any) -> Verdict:
    graph, config = load_graph(args.root)
    verdict = Verdict("select-work")

    iteration = getattr(args, "iteration", None) or config["lifecycle"].get("iteration")
    if not iteration:
        verdict.fail("SEL-000", "no iteration is open",
                     ["set lifecycle.iteration, or run /speckit.openup.iteration open"])
        verdict.metrics = {"ready": [], "blocked": [], "iteration": None}
        return verdict

    candidates = {
        node_id: node
        for node_id, node in graph.wbs.items()
        if node.get("iteration") == iteration
        and node.get("kind", "structural") != "structural"
        and node.get("status") in EXECUTABLE_STATUSES
    }

    ready: list[str] = []
    blocked: list[dict[str, Any]] = []
    for node_id, node in candidates.items():
        blockers = _readiness(graph, node_id, node)
        if blockers:
            blocked.append({"id": node_id, "reasons": blockers})
        else:
            ready.append(node_id)

    # Risk first, then dependency order, then id for stability.
    ready.sort(key=lambda nid: (-_risk_weight(graph, graph.wbs[nid]),
                                len(graph.wbs[nid].get("dependencies", []) or []),
                                nid))

    if ready:
        verdict.ok("SEL-001", f"{len(ready)} task(s) ready in {iteration}")
    else:
        verdict.warn("SEL-001", f"no task in {iteration} is ready to execute",
                     [f"{item['id']}: {'; '.join(item['reasons'])}" for item in blocked]
                     or [f"no non-structural task is assigned to {iteration}"])

    if blocked:
        verdict.warn("SEL-002", f"{len(blocked)} task(s) blocked by the Definition of Ready",
                     [f"{item['id']}: {'; '.join(item['reasons'])}" for item in blocked])
    else:
        verdict.ok("SEL-002", "no task is blocked")

    verdict.metrics = {
        "iteration": iteration,
        "ready": ready,
        "blocked": [item["id"] for item in blocked],
        "ready_count": len(ready),
        "blocked_count": len(blocked),
        "blockers": blocked,
    }
    return verdict


def main() -> int:
    parser = base_parser("Select Definition-of-Ready work for the current iteration")
    parser.add_argument("--iteration", default=None, help="override the configured iteration")
    parser.add_argument("--ids-only", action="store_true",
                        help="print a bare JSON array of ready task ids (for a workflow fan-out)")
    args = parser.parse_args()

    if not args.ids_only:
        return run(select, parser)

    # --ids-only must print a JSON ARRAY and nothing else: a fan-out's `items` passes
    # stdout through `from_json`, which has to yield a list rather than an object.
    try:
        verdict = select(args)
    except Exception as exc:  # noqa: BLE001
        print("[]")
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    from openup_model import write_out
    write_out(args.out, verdict.to_dict())
    print(json.dumps(verdict.metrics["ready"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
