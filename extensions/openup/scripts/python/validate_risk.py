#!/usr/bin/env python3
"""Validate the risk register.

specup.md s19 insists the register is not passive documentation: a risk must reach
into the WBS as real work, and that work must produce evidence. These checks are what
make that claim enforceable rather than aspirational.
"""

from __future__ import annotations

import sys
from typing import Any

from openup_model import Verdict, base_parser, load_graph, record, run, schema_errors

EPSILON = 1e-9


def validate(args: Any) -> Verdict:
    graph, config = load_graph(args.root)
    verdict = Verdict("validate-risk")

    thresholds = config["risk"]
    high = thresholds.get("high_exposure_threshold", 0.40)
    critical = thresholds.get("critical_exposure_threshold", 0.65)
    require_reduction = thresholds.get("require_residual_reduction", True)

    # Which band a rule applies from. These were declared in openup-config.yml and read by
    # nothing, so both checks silently used `high` whatever the config said — a setting that
    # does not move a verdict is worse than an absent one, because a reader trusts it.
    bands = {"high": high, "critical": critical}
    mitigate_at = bands.get(thresholds.get("require_mitigation_at_or_above", "high"), high)
    verify_at = bands.get(thresholds.get("require_verification_at_or_above", "high"), high)

    if not graph.risks:
        verdict.warn("RISK-000", "no risk register found; risk-driven planning (s39) is inactive")
        verdict.metrics = {"total": 0}
        return verdict

    document = {"schema_version": "1.0", "risks": list(graph.risks.values())}
    errors = schema_errors(document, "risk.schema.json")
    if errors:
        verdict.fail("RISK-000", f"risk register violates the schema ({len(errors)} error(s))", errors)
    else:
        verdict.ok("RISK-000", "risk register conforms to risk.schema.json")

    exposures = {rid: risk["probability"] * risk["impact"] for rid, risk in graph.risks.items()}

    # RISK-001 — a hand-edited exposure is how registers silently drift
    drifted = [
        f"{rid}: exposure {risk['exposure']} but probability x impact = {exposures[rid]:.4f}"
        for rid, risk in graph.risks.items()
        if "exposure" in risk and abs(risk["exposure"] - exposures[rid]) > EPSILON
    ]
    record(verdict, "RISK-001", drifted, "all stored exposures equal probability x impact")

    # RISK-002 — same for residual exposure
    residual_drift = []
    for rid, risk in graph.risks.items():
        if "residual_exposure" not in risk:
            continue
        if "residual_probability" not in risk or "residual_impact" not in risk:
            continue
        computed = risk["residual_probability"] * risk["residual_impact"]
        if abs(risk["residual_exposure"] - computed) > EPSILON:
            residual_drift.append(
                f"{rid}: residual_exposure {risk['residual_exposure']} but computed {computed:.4f}"
            )
    record(verdict, "RISK-002", residual_drift, "all residual exposures are internally consistent")

    # RISK-003 — mitigation that does not reduce exposure is a no-op
    not_reduced = []
    if require_reduction:
        for rid, risk in graph.risks.items():
            if risk.get("status") == "accepted" or "residual_probability" not in risk:
                continue
            residual = risk["residual_probability"] * risk.get("residual_impact", 1.0)
            if residual >= exposures[rid] - EPSILON:
                not_reduced.append(
                    f"{rid}: residual exposure {residual:.4f} is not below current {exposures[rid]:.4f}"
                )
    record(verdict, "RISK-003", not_reduced, "residual exposure is strictly below current exposure")

    # RISK-004 — high-exposure risks must be mitigated by real WBS work
    unmitigated = []
    for rid, risk in graph.risks.items():
        if exposures[rid] < mitigate_at or risk.get("status") in {"closed", "accepted"}:
            continue
        mitigations = risk.get("mitigation", []) or []
        if not mitigations:
            unmitigated.append(
                f"{rid}: exposure {exposures[rid]:.2f} >= {mitigate_at} but has no mitigation")
            continue
        for wbs_id in mitigations:
            if wbs_id not in graph.wbs:
                unmitigated.append(f"{rid}: mitigation {wbs_id} does not exist in the WBS")
    record(
        verdict, "RISK-004", unmitigated,
        f"every open risk at or above exposure {mitigate_at} has existing mitigation work",
    )

    # RISK-005 — high-exposure risks must be verifiable
    unverified = [
        f"{rid}: exposure {exposures[rid]:.2f} >= {verify_at} but has no verification reference"
        for rid, risk in graph.risks.items()
        if exposures[rid] >= verify_at
        and risk.get("status") not in {"closed", "accepted"}
        and not (risk.get("verification", []) or [])
    ]
    record(verdict, "RISK-005", unverified, "every high-exposure risk declares how it will be verified")

    # RISK-006 — the mitigation edge must agree from both ends
    disagreements = []
    for rid, risk in graph.risks.items():
        for wbs_id in risk.get("mitigation", []) or []:
            node = graph.wbs.get(wbs_id)
            if node is None:
                continue  # already reported by RISK-004
            if node.get("kind") != "risk-mitigation":
                disagreements.append(
                    f"{wbs_id} mitigates {rid} but its kind is '{node.get('kind', 'structural')}', "
                    f"not 'risk-mitigation'"
                )
            if rid not in (node.get("risks", []) or []):
                disagreements.append(f"{wbs_id} is listed as mitigating {rid} but does not reference it back")
    record(verdict, "RISK-006", disagreements, "mitigation links agree from both the risk and the WBS")

    # RISK-007 — a risk cannot be mitigated without evidence
    without_evidence = []
    for rid, risk in graph.risks.items():
        if risk.get("status") not in {"mitigated", "closed"}:
            continue
        node_evidence = [
            wbs_id
            for wbs_id in risk.get("mitigation", []) or []
            if wbs_id in graph.wbs and not (graph.wbs[wbs_id].get("evidence", []) or [])
        ]
        if not (risk.get("evidence", []) or []) and node_evidence:
            without_evidence.append(
                f"{rid}: status '{risk['status']}' but no evidence on the risk or on "
                f"{', '.join(node_evidence)}"
            )
    record(verdict, "RISK-007", without_evidence, "every mitigated risk is backed by evidence")

    open_risks = {
        rid: exposures[rid]
        for rid, risk in graph.risks.items()
        if risk.get("status") not in {"closed", "accepted"}
    }
    # s53 asks for risk→mitigation and risk→evidence as coverage ratios, not only as the
    # boolean checks above. A boolean tells you whether you are compliant right now; a ratio
    # tells you whether you are getting better, which is what a trend is for. Both are over
    # OPEN risks: a closed or accepted risk with no mitigation is a decision, not a gap.
    with_mitigation = sum(1 for rid in open_risks if graph.risks[rid].get("mitigation"))
    with_evidence = sum(1 for rid in open_risks if graph.risks[rid].get("evidence"))

    verdict.metrics = {
        "total": len(graph.risks),
        "open": len(open_risks),
        "open_critical": sum(1 for e in open_risks.values() if e >= critical),
        "open_high": sum(1 for e in open_risks.values() if high <= e < critical),
        "unmitigated_high": len([c for c in unmitigated if "no mitigation" in c]),
        "mitigation_coverage": round(_ratio(with_mitigation, len(open_risks)), 4),
        "evidence_coverage": round(_ratio(with_evidence, len(open_risks)), 4),
        "high_exposure_threshold": high,
        "critical_exposure_threshold": critical,
    }
    return verdict


def _ratio(numerator: int, denominator: int) -> float:
    return 1.0 if denominator == 0 else numerator / denominator


if __name__ == "__main__":
    sys.exit(run(validate, base_parser(__doc__.splitlines()[0])))
