#!/usr/bin/env python3
"""Filesystem-first compliance audit (specup.md s33).

Aggregates every validator and the gate for the current phase into one report, so the
governance state is observable rather than inferred. Fails on the conditions listed under
`audit.fail_on` in openup-config.yml.

The provenance mix is always printed. A project can show 100% coverage while every edge is
an unverified agent claim; the report must make that visible instead of hiding it behind a
single green number.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

import evaluate_gate
import validate_approvals
import validate_context
import validate_done
import validate_risk
import validate_trace
import validate_wbs
from openup_model import GraphError, Verdict, base_parser, load_graph, write_out

FAIL_CONDITIONS = {
    "broken_references": ("validate-trace", "TRC-002"),
    "orphan_requirements": ("validate-trace", "TRC-008"),
    "orphan_wbs_nodes": ("validate-trace", "TRC-008"),
    "unmitigated_high_risk": ("validate-risk", "RISK-004"),
    "coverage_below_threshold": ("validate-trace", "TRC-005"),
    # s59: an approval under a name the matrix does not record is not an approval.
    "unnamed_approver": ("validate-approvals", "APV-003"),
}


@dataclass
class _Args:
    root: str
    json: bool = False


def audit(args: Any) -> tuple[dict[str, Any], int]:
    graph, config = load_graph(args.root)
    sub = _Args(root=args.root)

    wbs = validate_wbs.validate(sub)
    risk = validate_risk.validate(sub)
    trace = validate_trace.validate(sub)
    done = validate_done.validate(sub)
    approvals = validate_approvals.validate(sub)
    context = validate_context.validate(sub)

    phase = config["lifecycle"].get("phase")
    iteration = config["lifecycle"].get("iteration")
    gate_name = next(
        (name for name, spec in config.get("gates", {}).items() if spec.get("phase") == phase),
        None,
    )

    gate: Verdict | None = None
    if gate_name:
        ctx = evaluate_gate.GateContext(
            root=graph.root, graph=graph, config=config,
            wbs=wbs, risk=risk, trace=trace, done=done, approvals=approvals,
        )
        gate = evaluate_gate.evaluate(gate_name, ctx)

    reasons: list[str] = []
    for name in config.get("audit", {}).get("fail_on", []):
        target = FAIL_CONDITIONS.get(name)
        if not target:
            continue
        validator, check_id = target
        verdict = {"validate-wbs": wbs, "validate-risk": risk, "validate-trace": trace,
                   "validate-done": done, "validate-context": context,
                   "validate-approvals": approvals}[validator]
        failing = next((c for c in verdict.checks if c.id == check_id and c.status == "FAIL"), None)
        if failing:
            reasons.append(f"{check_id} {name}: {failing.message}")

    sections = {"wbs": wbs, "risk": risk, "traceability": trace, "done": done,
                "context": context, "approvals": approvals}
    if gate:
        sections["gate"] = gate

    final = "PASS" if all(v.status != "FAIL" for v in sections.values()) and not reasons else "FAIL"

    report = {
        "validator": "audit",
        "status": final,
        "lifecycle": {"phase": phase, "iteration": iteration, "gate": gate_name},
        "sections": {name: verdict.to_dict() for name, verdict in sections.items()},
        "reasons": reasons or [
            f"{c.id}: {c.message}" for v in sections.values() for c in v.checks if c.status == "FAIL"
        ],
        "files_loaded": graph.loaded_files,
    }
    return report, (1 if final == "FAIL" else 0)


def render(report: dict[str, Any]) -> str:
    sections = report["sections"]
    wbs = sections["wbs"]["metrics"]
    risk = sections["risk"]["metrics"]
    trace = sections["traceability"]["metrics"]
    lines = ["OPENUP AI ENGINEERING AUDIT", "=" * 27, ""]

    lines += [
        "Lifecycle",
        f"  Phase:        {report['lifecycle']['phase']}",
        f"  Iteration:    {report['lifecycle']['iteration'] or '-'}",
        f"  Gate:         {report['lifecycle']['gate'] or '-'}",
        "",
    ]

    levels = wbs.get("levels", {})
    lines.append("WBS")
    lines += [f"  {name}: {count}" for name, count in levels.items()]
    lines += [
        f"  Leaves: {wbs.get('leaves', 0)}  (early terminations: {wbs.get('early_terminations', 0)})",
        f"  Policy: {wbs.get('depth_policy', '-')}",
        f"  Status: {sections['wbs']['status']}",
        "",
        "Requirements",
        f"  Total:        {trace.get('requirements', 0)}",
        f"  Implemented:  {trace.get('forward_coverage', 0):.0%}",
        f"  Verified:     {trace.get('verification_coverage', 0):.0%}",
        f"  Status: {'PASS' if trace.get('forward_coverage', 0) >= 1 else 'FAIL'}",
        "",
        "Risks",
        f"  Total:         {risk.get('total', 0)}",
        f"  Open critical: {risk.get('open_critical', 0)}",
        f"  Open high:     {risk.get('open_high', 0)}",
        f"  Unmitigated:   {risk.get('unmitigated_high', 0)}",
        f"  Status: {sections['risk']['status']}",
        "",
        "Traceability",
        f"  Edges:             {trace.get('edges', 0)}",
        f"  Forward coverage:  {trace.get('forward_coverage', 0):.0%}",
        f"  Backward coverage: {trace.get('backward_coverage', 0):.0%}",
        f"  Orphans:           {trace.get('orphans', 0)}",
        f"  Status: {sections['traceability']['status']}",
        "",
    ]

    # Claimed vs verified, not a count of 'done'. s29 asks for done to be a computed state,
    # so the report has to show the two numbers separately or it repeats the claim it checks.
    done = sections["done"]["metrics"]
    claimed = done.get("done_claimed", 0)
    lines += [
        "Definition of Done",
        f"  Claimed done:  {claimed}",
        f"  Verified done: {done.get('done_verified', 0)}",
        f"  Status: {sections['done']['status']}",
        "",
    ]

    mix = trace.get("provenance_mix", {})
    total = sum(mix.values()) or 1
    # Both signed labels are split, because neither proves anything on its own. An edge is
    # machine-checkable only if the rule it names exists and reproduces it (TRC-010), and an
    # approval counts only while its hash still matches the endpoints it was given for
    # (TRC-013). What is left over in each case is a claim wearing a better label.
    reproduced = trace.get("derived_verified", 0)
    unreproduced = trace.get("derived_unverified", 0)
    approved = trace.get("approved_verified", 0)
    stale = trace.get("approved_stale", 0)
    lines += [
        "Evidence quality",
        f"  derived:   {reproduced:>4}  ({reproduced / total:.0%})  reproduced by a rule",
        f"  unverified:{unreproduced:>4}  ({unreproduced / total:.0%})  claims a rule that is not implemented",
        f"  asserted:  {mix.get('asserted', 0):>4}  ({mix.get('asserted', 0) / total:.0%})  agent claim only",
        f"  approved:  {approved:>4}  ({approved / total:.0%})  signed off, and still matching what was signed",
        f"  stale:     {stale:>4}  ({stale / total:.0%})  approved for content that has since changed",
        "",
    ]

    # s33 says the audit inspects the "AGENTS.md hierarchy -> index.md hierarchy". It did
    # neither until validate_context existed. CTX-002 is the one that matters: a context map
    # pointing at a deleted requirement misleads the agent reading it.
    ctx = sections["context"]["metrics"]
    lines += [
        "Context hierarchy",
        f"  index.md files:  {ctx.get('index_files', 0)} over "
        f"{ctx.get('governed_directories', 0)} governed directory(s)",
        f"  Skills:          {', '.join(ctx.get('skills', [])) or '-'}",
        f"  Dangling refs:   {ctx.get('dangling_references', 0)}",
        f"  Status: {sections['context']['status']}",
        "",
    ]

    # The approval witness mix, and it is deliberately printed next to the evidence mix above
    # rather than folded into it. Those two "approved" numbers count different things: an edge
    # is `approved` when someone signed off on content that still matches, and an approval is
    # `witnessed` when git can verify a person made it. A project can be 100% approved and 0%
    # witnessed, and reporting one number would hide exactly that.
    apv = sections["approvals"]["metrics"]
    approvals_total = apv.get("approvals", 0) or 1
    witnessed = apv.get("witnessed", 0)
    claimed = apv.get("claimed", 0)
    floor = apv.get("witness_floor")
    lines += [
        "Approvals",
        f"  witnessed: {witnessed:>4}  ({witnessed / approvals_total:.0%})  a signature git verified",
        f"  claimed:   {claimed:>4}  ({claimed / approvals_total:.0%})  a name, and nothing tying "
        f"it to a person",
        f"  Named approvers: {', '.join(apv.get('named_approvers', [])) or '-'}",
        f"  Witness floor:   {floor or 'not set (approvals.require_witness_at_or_above)'}",
        f"  Status: {sections['approvals']['status']}",
        "",
    ]

    if "gate" in sections:
        gate = sections["gate"]
        lines += [f"Gate {report['lifecycle']['gate']}"]
        lines += [f"  [{c['status']}] {c['id']}  {c['message']}" for c in gate["checks"]]
        lines += [f"  Status: {gate['status']}", ""]

    lines.append(f"FINAL GATE: {report['status']}")
    if report["status"] == "FAIL":
        lines.append("")
        lines.append("Reasons:")
        lines += [f"  {reason}" for reason in report["reasons"][:20]]
    return "\n".join(lines)


def main() -> int:
    parser = base_parser("Filesystem-first compliance audit")
    args = parser.parse_args()
    try:
        report, code = audit(args)
    except GraphError as exc:
        payload = {"validator": "audit", "status": "ERROR", "error": str(exc)}
        write_out(args.out, payload)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    write_out(args.out, report)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return code


if __name__ == "__main__":
    sys.exit(main())
