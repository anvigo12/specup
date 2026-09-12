#!/usr/bin/env python3
"""Evaluate an OpenUP lifecycle gate.

specup.md s30 names gate conditions but never implements them; s55 insists a gate must be
machine-checkable and evidence-producing rather than an assertion that "architecture looks
good". This module is where a condition name in openup-config.yml becomes a real check.

One rule governs every condition here: **absence of evidence is not evidence**. A missing
test report, review record, or architecture baseline FAILS the condition. A gate that passes
because a file was never written would be worse than no gate at all.

Usage (the form a workflow shell step uses):

    evaluate_gate.py --gate GATE-LIFECYCLE_ARCHITECTURE --json
"""

from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Callable

import validate_risk
import validate_trace
import validate_wbs
from openup_model import GraphError, Verdict, base_parser, emit, load_graph, write_out

CONDITIONS: dict[str, Callable[["GateContext"], tuple[bool, str, list[str]]]] = {}


def condition(name: str):
    def register(fn):
        CONDITIONS[name] = fn
        return fn
    return register


@dataclass
class _Args:
    root: str
    json: bool = False


@dataclass
class GateContext:
    root: pathlib.Path
    graph: Any
    config: dict[str, Any]
    wbs: Verdict
    risk: Verdict
    trace: Verdict
    _depth: int = 0

    def check(self, verdict: Verdict, check_id: str) -> tuple[bool, list[str]]:
        for item in verdict.checks:
            if item.id == check_id:
                return item.status != "FAIL", item.evidence
        return False, [f"{check_id} was not evaluated"]

    def doc(self, *candidates: str) -> pathlib.Path | None:
        for candidate in candidates:
            for match in sorted(self.root.glob(candidate)):
                if match.is_file():
                    return match
        return None

    def evidence_json(self, name: str) -> dict[str, Any] | None:
        path = self.root / ".specify" / "evidence" / name
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return None


# -- document presence -----------------------------------------------------


@condition("vision_present")
def _vision(ctx: GateContext):
    found = ctx.doc(".specify/lifecycle/vision.md", "docs/vision.md", "specs/*/vision.md")
    return bool(found), f"vision document {'found at ' + str(found.name) if found else 'not found'}", \
        [] if found else ["expected .specify/lifecycle/vision.md"]


@condition("stakeholders_identified")
def _stakeholders(ctx: GateContext):
    found = ctx.doc(".specify/lifecycle/stakeholders.md", "docs/stakeholders.md")
    return bool(found), "stakeholders documented" if found else "no stakeholder document", \
        [] if found else ["expected .specify/lifecycle/stakeholders.md"]


@condition("architecture_baselined")
def _architecture(ctx: GateContext):
    doc = ctx.doc(".specify/architecture/architecture.md", "docs/architecture.md", "specs/*/architecture.md")
    adrs = {aid: a for aid, a in ctx.graph.artifacts.items()
            if ctx.graph.grammar.type_of(aid) == "architecture-decision"}
    unapproved = [aid for aid, a in adrs.items()
                  if a.get("status") not in {"APPROVED", "BASELINED", "IMPLEMENTED", "VERIFIED", "ACCEPTED"}]
    problems = []
    if not doc:
        problems.append("no architecture document found")
    if not adrs:
        problems.append("no architecture decisions (ADR-nnnn) registered")
    problems += [f"{aid} is still {adrs[aid].get('status', 'DRAFT')}" for aid in unapproved]
    return not problems, f"{len(adrs)} ADR(s), {len(unapproved)} not yet approved", problems


@condition("critical_contracts_defined")
def _contracts(ctx: GateContext):
    contracts = {aid: a for aid, a in ctx.graph.artifacts.items()
                 if ctx.graph.grammar.type_of(aid) == "contract"}
    missing = [f"{aid}: declared source {a.get('source')} does not exist"
               for aid, a in contracts.items()
               if not a.get("source") or not (ctx.root / a["source"]).is_file()]
    if not contracts:
        return False, "no API contracts registered", ["expected at least one CONTRACT-<DOMAIN>-nnnn artifact"]
    return not missing, f"{len(contracts)} contract(s) registered", missing


@condition("release_evidence_complete")
def _release_evidence(ctx: GateContext):
    required = ["release-readiness.md", "deployment-plan.md", "operations.md", "acceptance-report.md"]
    missing = [name for name in required
               if not ctx.doc(f".specify/lifecycle/{name}", f"docs/{name}")]
    return not missing, f"{len(required) - len(missing)}/{len(required)} release documents present", \
        [f"missing {name}" for name in missing]


# -- evidence-backed -------------------------------------------------------


@condition("security_review_complete")
def _security_review(ctx: GateContext):
    report = ctx.evidence_json("security-review.json")
    if report is None:
        return False, "no security review evidence", [
            "expected .specify/evidence/security-review.json — absence of evidence is not evidence"
        ]
    ok = report.get("status") == "passed"
    return ok, f"security review status: {report.get('status', 'unknown')}", \
        [] if ok else [json.dumps(report)[:200]]


@condition("security_validation_passed")
def _security_validation(ctx: GateContext):
    report = ctx.evidence_json("security-validation.json")
    if report is None:
        return False, "no security validation evidence", [
            "expected .specify/evidence/security-validation.json"
        ]
    findings = report.get("critical_findings", report.get("findings", 0))
    ok = report.get("status") == "passed" and not findings
    return ok, f"security validation: {report.get('status')}, {findings} critical finding(s)", \
        [] if ok else [json.dumps(report)[:200]]


@condition("acceptance_scenarios_passing")
def _acceptance(ctx: GateContext):
    report = ctx.evidence_json("acceptance-results.json")
    if report is None:
        return False, "no acceptance test evidence", [
            "expected .specify/evidence/acceptance-results.json"
        ]
    failed = report.get("failed", 0)
    total = report.get("total", 0)
    return failed == 0 and total > 0, \
        f"{report.get('passed', 0)}/{total} acceptance scenarios passing", \
        [] if failed == 0 else [f"{failed} failing scenario(s)"] + list(report.get("failures", []))[:10]


# -- graph-derived ---------------------------------------------------------


@condition("initial_risks_registered")
def _initial_risks(ctx: GateContext):
    count = len(ctx.graph.risks)
    return count > 0, f"{count} risk(s) registered", [] if count else ["the risk register is empty"]


@condition("requirements_have_owners")
def _requirement_owners(ctx: GateContext):
    requirements = ctx.graph.requirements()
    missing = [f"{rid}: no owner" for rid, art in requirements.items() if not art.get("owner")]
    if not requirements:
        return False, "no requirements registered", ["expected at least one REQ-<DOMAIN>-nnnn"]
    return not missing, f"{len(requirements) - len(missing)}/{len(requirements)} requirements have owners", missing


@condition("wbs_levels_1_to_3_valid")
def _wbs_skeleton(ctx: GateContext):
    from openup_model import wbs_level
    levels = {level: sum(1 for nid in ctx.graph.wbs if wbs_level(nid) == level) for level in (1, 2, 3)}
    problems = [f"no L{level} ({name}) node" for level, name in
                ((1, "Program"), (2, "Phase"), (3, "Iteration")) if not levels[level]]
    for check_id in ("WBS-001", "WBS-002", "WBS-003"):
        ok, evidence = ctx.check(ctx.wbs, check_id)
        if not ok:
            problems += [f"{check_id}: {item}" for item in evidence[:5]]
    return not problems, f"WBS skeleton L1={levels[1]} L2={levels[2]} L3={levels[3]}", problems


@condition("wbs_valid")
def _wbs_valid(ctx: GateContext):
    ok = ctx.wbs.status != "FAIL"
    failures = [f"{c.id}: {c.message}" for c in ctx.wbs.checks if c.status == "FAIL"]
    return ok, f"WBS validation {ctx.wbs.status}", failures


@condition("all_high_risks_have_mitigation")
def _high_risks(ctx: GateContext):
    ok, evidence = ctx.check(ctx.risk, "RISK-004")
    ok2, evidence2 = ctx.check(ctx.risk, "RISK-005")
    return ok and ok2, "high-exposure risks are mitigated and verifiable", evidence + evidence2


@condition("no_open_critical_risks")
def _no_critical(ctx: GateContext):
    count = ctx.risk.metrics.get("open_critical", 0)
    return count == 0, f"{count} open critical risk(s)", \
        [] if not count else [f"{count} risk(s) at or above the critical exposure threshold"]


@condition("no_open_high_risks")
def _no_high(ctx: GateContext):
    high = ctx.risk.metrics.get("open_high", 0)
    critical = ctx.risk.metrics.get("open_critical", 0)
    return high + critical == 0, f"{high} open high, {critical} open critical", \
        [] if high + critical == 0 else [f"{high + critical} risk(s) still open above the high threshold"]


@condition("requirements_traceable")
def _traceable(ctx: GateContext):
    ok1, ev1 = ctx.check(ctx.trace, "TRC-005")
    ok2, ev2 = ctx.check(ctx.trace, "TRC-006")
    return ok1 and ok2, "every requirement is implemented and verified", ev1 + ev2


@condition("forward_coverage_met")
def _forward(ctx: GateContext):
    ok, evidence = ctx.check(ctx.trace, "TRC-005")
    return ok, f"forward coverage {ctx.trace.metrics.get('forward_coverage', 0):.0%}", evidence


@condition("backward_coverage_met")
def _backward(ctx: GateContext):
    ok, evidence = ctx.check(ctx.trace, "TRC-007")
    return ok, f"backward coverage {ctx.trace.metrics.get('backward_coverage', 0):.0%}", evidence


@condition("no_orphans")
def _no_orphans(ctx: GateContext):
    ok, evidence = ctx.check(ctx.trace, "TRC-008")
    return ok, f"{ctx.trace.metrics.get('orphans', 0)} orphan artifact(s)", evidence


@condition("traceability_final")
def _trace_final(ctx: GateContext):
    ok = ctx.trace.status != "FAIL"
    failures = [f"{c.id}: {c.message}" for c in ctx.trace.checks if c.status == "FAIL"]
    asserted = ctx.trace.metrics.get("asserted_share", 0)
    if ok and asserted > 0.5:
        failures.append(
            f"{asserted:.0%} of edges are merely 'asserted' — the graph is not independently verifiable"
        )
        ok = False
    return ok, f"traceability {ctx.trace.status}, asserted share {asserted:.0%}", failures


@condition("all_gates_passed")
def _all_gates(ctx: GateContext):
    if ctx._depth > 0:
        return True, "nested gate evaluation skipped", []
    failures = []
    for name, spec in ctx.config.get("gates", {}).items():
        if spec.get("phase") == "TRANSITION":
            continue
        nested = evaluate(name, ctx, depth=ctx._depth + 1)
        if nested.status == "FAIL":
            failures.append(f"{name}: FAIL")
    return not failures, f"{len(ctx.config.get('gates', {})) - 1 - len(failures)} prior gate(s) passing", failures


# --------------------------------------------------------------------------


def evaluate(gate_name: str, ctx: GateContext, depth: int = 0) -> Verdict:
    spec = ctx.config.get("gates", {}).get(gate_name)
    verdict = Verdict(f"gate:{gate_name}")
    if spec is None:
        known = ", ".join(sorted(ctx.config.get("gates", {}))) or "none"
        verdict.fail("GATE-000", f"unknown gate '{gate_name}'", [f"configured gates: {known}"])
        return verdict

    ctx._depth = depth
    for name in spec.get("conditions", []):
        implementation = CONDITIONS.get(name)
        if implementation is None:
            verdict.fail(name, "condition is declared in openup-config.yml but not implemented",
                         [f"implement it in evaluate_gate.py, or remove it from {gate_name}"])
            continue
        try:
            ok, message, evidence = implementation(ctx)
        except Exception as exc:  # noqa: BLE001 — a broken check must fail closed, never pass
            verdict.fail(name, f"condition raised {type(exc).__name__}: {exc}")
            continue
        verdict.add(name, "PASS" if ok else "FAIL", message, evidence)

    verdict.metrics = {
        "gate": gate_name,
        "phase": spec.get("phase"),
        "conditions": len(spec.get("conditions", [])),
        "failed": sum(1 for c in verdict.checks if c.status == "FAIL"),
    }
    return verdict


def main() -> int:
    parser = base_parser("Evaluate an OpenUP lifecycle gate")
    parser.add_argument("--gate", required=True, help="gate id, e.g. GATE-LIFECYCLE_ARCHITECTURE")
    args = parser.parse_args()

    try:
        graph, config = load_graph(args.root)
        sub = _Args(root=args.root)
        ctx = GateContext(
            root=graph.root,
            graph=graph,
            config=config,
            wbs=validate_wbs.validate(sub),
            risk=validate_risk.validate(sub),
            trace=validate_trace.validate(sub),
        )
    except GraphError as exc:
        payload = {"validator": f"gate:{args.gate}", "status": "ERROR", "error": str(exc)}
        write_out(args.out, payload)
        print(json.dumps(payload, indent=2) if args.json else f"ERROR: {exc}",
              file=sys.stdout if args.json else sys.stderr)
        return 2

    return emit(evaluate(args.gate, ctx), args.json, args.out)


if __name__ == "__main__":
    sys.exit(main())
