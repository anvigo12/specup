"""One deliberately-broken fixture per invariant.

These are the acceptance criteria for Stage 3: the workflow gate must abort on exactly
these graphs. A test that only proved the good fixture passes would prove nothing — a
validator that always returns PASS would satisfy it.
"""

from __future__ import annotations

from conftest import assert_fails, failing


# --------------------------------------------------------------------------
# Baseline: the good fixture must pass everything
# --------------------------------------------------------------------------


def test_good_fixture_passes_all_validators(project):
    for module in ("validate_wbs", "validate_risk", "validate_trace"):
        verdict = project.run(module)
        assert verdict.status == "PASS", f"{module} failed: {sorted(failing(verdict))}"


def test_good_fixture_passes_the_architecture_gate(project):
    assert project.gate("GATE-LIFECYCLE_ARCHITECTURE").status == "PASS"


# --------------------------------------------------------------------------
# WBS invariants (specup.md s18, s32)
# --------------------------------------------------------------------------


def test_level_must_match_id_segment_count(project):
    # This is the error in specup.md's own s17 example: id "1.2.3.4.1.2" declared as level 7.
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(level=6))
    assert_fails(project.run("validate_wbs"), "WBS-001")


def test_parent_must_be_the_id_minus_its_last_segment(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(parent="WBS-1.2.3"))
    assert_fails(project.run("validate_wbs"), "WBS-002")


def test_missing_parent_node_is_detected(project):
    project.wbs(lambda d: d["nodes"].append({
        "id": "WBS-1.9.9.9.9.9.9", "name": "Orphan task", "level": 7,
        "parent": "WBS-1.9.9.9.9.9", "status": "planned", "owner": "nobody",
        "iteration": "ITER-E-02", "requirements": ["REQ-AUTH-0014"],
    }))
    assert_fails(project.run("validate_wbs"), "WBS-002")


def test_two_roots_is_an_error(project):
    project.wbs(lambda d: d["nodes"].append({
        "id": "WBS-2", "name": "Second program", "level": 1, "status": "planned",
    }))
    assert_fails(project.run("validate_wbs"), "WBS-003")


def test_leaf_above_l7_without_terminal_reason_fails(project):
    # Delete the three L7 tasks, leaving the L6 work package as an undeclared leaf.
    project.wbs(lambda d: d.update(
        nodes=[n for n in d["nodes"] if not n["id"].startswith("WBS-1.2.3.4.1.1.")]
    ))
    assert_fails(project.run("validate_wbs"), "WBS-004")


def test_leaf_above_l7_with_terminal_reason_passes_under_semantic_policy(project):
    project.wbs(lambda d: d.update(
        nodes=[n for n in d["nodes"] if not n["id"].startswith("WBS-1.2.3.4.1.1.")]
    ))
    project.node("WBS-1.2.3.4.1.1")(lambda n: n.update(
        kind="implementation", owner="backend-team", iteration="ITER-E-02",
        terminal_reason="single-file validator change; decomposition adds no execution detail",
    ))
    assert "WBS-004" not in failing(project.run("validate_wbs"))


def test_the_same_early_termination_fails_under_strict_policy(project):
    """depth_policy is the one knob that changes this verdict — proving the mode is real."""
    project.wbs(lambda d: d.update(
        nodes=[n for n in d["nodes"] if not n["id"].startswith("WBS-1.2.3.4.1.1.")]
    ))
    project.node("WBS-1.2.3.4.1.1")(lambda n: n.update(
        kind="implementation", owner="backend-team", iteration="ITER-E-02",
        terminal_reason="single-file validator change; decomposition adds no execution detail",
    ))
    project.config(lambda c: c["wbs"].update(depth_policy="strict"))
    assert_fails(project.run("validate_wbs"), "WBS-004")


def test_structural_levels_may_never_be_leaves(project):
    project.wbs(lambda d: d.update(
        nodes=[n for n in d["nodes"] if not n["id"].startswith("WBS-1.2.3.")]
    ))
    assert_fails(project.run("validate_wbs"), "WBS-004")


def test_l7_task_without_a_requirement_fails(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.pop("requirements"))
    verdict = project.run("validate_wbs")
    assert verdict.status == "FAIL"
    assert "WBS-000" in failing(verdict)  # schema catches it before the graph checks


def test_unresolvable_requirement_reference_fails(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(requirements=["REQ-AUTH-9999"]))
    assert_fails(project.run("validate_wbs"), "WBS-005")


def test_unresolvable_risk_reference_fails(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(risks=["RISK-9999"]))
    assert_fails(project.run("validate_wbs"), "WBS-006")


def test_missing_dependency_target_fails(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(dependencies=["WBS-1.2.3.4.1.1.9"]))
    assert_fails(project.run("validate_wbs"), "WBS-008")


def test_dependency_cycle_is_detected(project):
    project.node("WBS-1.2.3.4.1.1.1")(lambda n: n.update(dependencies=["WBS-1.2.3.4.1.1.3"]))
    assert_fails(project.run("validate_wbs"), "WBS-009")


def test_iteration_must_belong_to_the_nodes_phase(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(iteration="ITER-C-01"))
    assert_fails(project.run("validate_wbs"), "WBS-010")


# --------------------------------------------------------------------------
# Risk invariants (specup.md s19, s32)
# --------------------------------------------------------------------------


def test_hand_edited_exposure_is_rejected(project):
    project.risk("RISK-0007")(lambda r: r.update(exposure=0.10))
    assert_fails(project.run("validate_risk"), "RISK-001")


def test_inconsistent_residual_exposure_is_rejected(project):
    project.risk("RISK-0007")(lambda r: r.update(residual_exposure=0.99))
    assert_fails(project.run("validate_risk"), "RISK-002")


def test_mitigation_that_does_not_reduce_exposure_is_rejected(project):
    project.risk("RISK-0007")(lambda r: r.update(
        residual_probability=0.9, residual_impact=0.9, residual_exposure=0.81))
    assert_fails(project.run("validate_risk"), "RISK-003")


def test_high_exposure_risk_without_mitigation_fails(project):
    project.risk("RISK-0007")(lambda r: r.update(mitigation=[]))
    assert_fails(project.run("validate_risk"), "RISK-004")


def test_mitigation_pointing_at_a_nonexistent_wbs_node_fails(project):
    project.risk("RISK-0007")(lambda r: r.update(mitigation=["WBS-9.9.9"]))
    assert_fails(project.run("validate_risk"), "RISK-004")


def test_low_exposure_risk_without_mitigation_is_allowed(project):
    """Accepting a low-exposure risk is a legitimate choice, not a gap."""
    verdict = project.run("validate_risk")
    assert verdict.status == "PASS"
    assert verdict.metrics["open_high"] == 1


def test_high_exposure_risk_without_verification_fails(project):
    project.risk("RISK-0007")(lambda r: r.update(verification=[]))
    assert_fails(project.run("validate_risk"), "RISK-005")


def test_mitigation_link_must_agree_from_both_ends(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(risks=[]))
    assert_fails(project.run("validate_risk"), "RISK-006")


def test_mitigation_node_must_be_kind_risk_mitigation(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(kind="implementation"))
    assert_fails(project.run("validate_risk"), "RISK-006")


def test_accepting_a_risk_requires_human_approval(project):
    project.risk("RISK-0012")(lambda r: r.update(status="accepted"))
    assert_fails(project.run("validate_risk"), "RISK-000")


# --------------------------------------------------------------------------
# Traceability invariants (specup.md s20-s22, s54)
# --------------------------------------------------------------------------


def test_duplicate_triple_across_stores_is_rejected(project):
    project.add_edge(**{"from": "REQ-AUTH-0014", "relation": "refines",
                        "to": "BUS-OBJ-0017", "provenance": "asserted"})
    assert_fails(project.run("validate_trace"), "TRC-001")


def test_edge_to_a_nonexistent_artifact_is_broken(project):
    project.add_edge(**{"from": "WBS-1.2.3.4.1.1.2", "relation": "implements",
                        "to": "REQ-AUTH-9999", "provenance": "asserted"})
    assert_fails(project.run("validate_trace"), "TRC-002")


def test_edge_to_a_nonexistent_source_file_is_broken(project):
    project.add_edge(**{"from": "src/does/not/exist.ts", "relation": "implements",
                        "to": "REQ-AUTH-0014", "provenance": "derived",
                        "derived_by": "test"})
    assert_fails(project.run("validate_trace"), "TRC-002")


def test_type_illegal_relation_is_rejected(project):
    # A risk cannot verify a requirement.
    project.add_edge(**{"from": "RISK-0007", "relation": "verifies",
                        "to": "REQ-AUTH-0014", "provenance": "asserted"})
    assert_fails(project.run("validate_trace"), "TRC-003")


def test_relation_outside_the_closed_vocabulary_is_rejected(project):
    project.add_edge(**{"from": "WBS-1.2.3.4.1.1.2", "relation": "implemented-by",
                        "to": "REQ-AUTH-0014", "provenance": "asserted"})
    assert_fails(project.run("validate_trace"), "TRC-000")


def test_refines_cycle_is_detected(project):
    project.add_edge(**{"from": "BUS-OBJ-0017", "relation": "refines",
                        "to": "REQ-AUTH-0014", "provenance": "asserted"})
    assert_fails(project.run("validate_trace"), "TRC-004")


def test_unimplemented_requirement_breaks_forward_coverage(project):
    project.drop_edges(**{"from": "WBS-1.2.3.4.1.1.2", "relation": "implements",
                          "to": "NON-FR-AUTH-0017"})
    assert_fails(project.run("validate_trace"), "TRC-005")


def test_unverified_requirement_breaks_verification_coverage(project):
    project.drop_edges(**{"from": "AC-AUTH-0014-0004", "relation": "verifies",
                          "to": "NON-FR-AUTH-0017"})
    assert_fails(project.run("validate_trace"), "TRC-006")


def test_untraced_source_file_breaks_backward_coverage(project):
    (project.root / "src" / "auth" / "session_manager.ts").write_text(
        "export function newSession(): string { return 'x'; }\n"
    )
    assert_fails(project.run("validate_trace"), "TRC-007")


def test_a_file_outside_the_perimeter_does_not_break_coverage(project):
    """s54 would flag every util as an orphan; the perimeter is what makes it tractable."""
    (project.root / "src" / "security" / "helpers.test.ts").write_text("// excluded\n")
    assert project.run("validate_trace").status == "PASS"


def test_orphan_requirement_is_reported(project):
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "REQ-AUTH-0018", "type": "requirement",
        "title": "Unreferenced requirement", "status": "DRAFT", "owner": "product-owner",
    }))
    verdict = project.run("validate_trace")
    assert verdict.status == "FAIL"
    assert {"TRC-005", "TRC-008"} & failing(verdict)


def test_baselined_requirement_needs_approved_provenance(project):
    project.artifact("REQ-AUTH-0014")(lambda a: a.update(
        status="BASELINED",
        approvals=[{"by": "product-owner", "at": "2026-09-10T09:00:00Z"}],
    ))
    assert_fails(project.run("validate_trace"), "TRC-009")


def test_derived_edge_without_derived_by_is_rejected(project):
    project.add_edge(**{"from": "src/security/certificate_validator.ts",
                        "relation": "tests", "to": "src/auth/authentication_service.ts",
                        "provenance": "derived"})
    assert_fails(project.run("validate_trace"), "TRC-000")


# --------------------------------------------------------------------------
# Gates (specup.md s30, s55) — the checks Stage 3 will bind to workflow steps
# --------------------------------------------------------------------------


def test_gate_fails_when_a_high_risk_loses_its_mitigation(project):
    project.risk("RISK-0007")(lambda r: r.update(mitigation=[]))
    verdict = project.gate("GATE-LIFECYCLE_ARCHITECTURE")
    assert verdict.status == "FAIL"
    assert "all_high_risks_have_mitigation" in failing(verdict)


def test_gate_fails_when_the_wbs_is_broken(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(level=3))
    verdict = project.gate("GATE-LIFECYCLE_ARCHITECTURE")
    assert verdict.status == "FAIL"
    assert "wbs_valid" in failing(verdict)


def test_gate_fails_when_a_requirement_is_untraceable(project):
    project.drop_edges(**{"from": "WBS-1.2.3.4.1.1.2", "relation": "implements",
                          "to": "NON-FR-AUTH-0017"})
    verdict = project.gate("GATE-LIFECYCLE_ARCHITECTURE")
    assert verdict.status == "FAIL"
    assert "requirements_traceable" in failing(verdict)


def test_missing_security_evidence_fails_the_gate(project):
    """Absence of evidence is not evidence — the condition must fail, not skip."""
    (project.root / ".specify" / "evidence" / "security-review.json").unlink()
    verdict = project.gate("GATE-LIFECYCLE_ARCHITECTURE")
    assert verdict.status == "FAIL"
    assert "security_review_complete" in failing(verdict)


def test_unapproved_adr_fails_the_architecture_gate(project):
    project.artifact("ADR-0019")(lambda a: a.update(status="DRAFT"))
    verdict = project.gate("GATE-LIFECYCLE_ARCHITECTURE")
    assert verdict.status == "FAIL"
    assert "architecture_baselined" in failing(verdict)


def test_unknown_gate_fails_closed(project):
    verdict = project.gate("GATE-DOES_NOT_EXIST")
    assert verdict.status == "FAIL"


def test_unimplemented_condition_fails_closed(project):
    """A condition named in config but not implemented must never silently pass."""
    project.config(lambda c: c["gates"]["GATE-LIFECYCLE_ARCHITECTURE"]["conditions"]
                   .append("nonexistent_condition"))
    verdict = project.gate("GATE-LIFECYCLE_ARCHITECTURE")
    assert verdict.status == "FAIL"
    assert "nonexistent_condition" in failing(verdict)


def test_release_gate_rejects_a_graph_that_is_mostly_unverifiable(project):
    """100% coverage built from unverifiable claims must not pass the release gate."""
    project.config(lambda c: c["lifecycle"].update(phase="TRANSITION"))
    verdict = project.gate("GATE-PRODUCT_RELEASE")
    assert verdict.status == "FAIL"
    assert "traceability_final" in failing(verdict)
