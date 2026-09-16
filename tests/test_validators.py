"""One deliberately-broken fixture per invariant.

These are the acceptance criteria for Stage 3: the workflow gate must abort on exactly
these graphs. A test that only proved the good fixture passes would prove nothing — a
validator that always returns PASS would satisfy it.
"""

from __future__ import annotations

import pytest
from conftest import assert_fails, failing
from openup_model import GraphError


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
# Store integrity — an id names exactly one thing (ID-GRAMMAR.md s1)
# --------------------------------------------------------------------------
#
# These raise GraphError (exit 2) rather than failing a check, because a store declaring one
# id twice does not describe a graph that breaks a rule — it describes no graph at all. The
# loader has to discard one of the two to build anything, so every check downstream would be
# computing over an arbitrary choice, and reporting THAT as a governance verdict would
# misrepresent what was actually read.


def test_duplicate_wbs_node_id_is_refused(project):
    def add_a_second_copy(document):
        original = next(n for n in document["nodes"] if n["id"] == "WBS-1.2.3.4.1.1.3")
        document["nodes"].append({**original, "name": "A different task reusing the id"})

    project.wbs(add_a_second_copy)
    with pytest.raises(GraphError, match="duplicate WBS node WBS-1.2.3.4.1.1.3"):
        project.run("validate_wbs")


def test_duplicate_risk_id_is_refused(project):
    def add_a_second_copy(document):
        original = next(r for r in document["risks"] if r["id"] == "RISK-0007")
        document["risks"].append({**original, "title": "A different risk reusing the id"})

    project.risks(add_a_second_copy)
    with pytest.raises(GraphError, match="duplicate risk RISK-0007"):
        project.run("validate_risk")


def test_duplicate_artifact_id_is_refused(project):
    """The case that used to pass in silence.

    Before this check the second entry simply replaced the first, so a graph could report
    100% coverage while the requirement everything pointed at had been quietly swapped for a
    DRAFT one with a different owner. Nothing in fourteen traceability checks noticed.
    """
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "REQ-AUTH-0014", "type": "requirement",
        "title": "A different requirement that reused the id",
        "status": "DRAFT", "owner": "someone-else"}))
    with pytest.raises(GraphError, match="duplicate artifact REQ-AUTH-0014"):
        project.run("validate_trace")


def test_duplicate_artifact_id_across_feature_stores_names_both_files(project):
    """Artifacts are the only store spanning several files, so the error must name both.

    Two features independently reaching for the same number is the realistic collision, and
    an error naming only the file it was caught in leaves the reader hunting for the other.
    """
    project.config(lambda c: c["artifacts"].update(
        stores=[".specify/traceability/requirements.yaml", "specs/*/artifacts.yaml"]))
    (project.root / "specs/001-auth/artifacts.yaml").write_text(
        'schema_version: "1.0"\n'
        "artifacts:\n"
        "  - id: REQ-AUTH-0014\n"
        "    type: requirement\n"
        '    title: "A second feature reached for the same number"\n'
        "    status: DRAFT\n"
        "    owner: billing-team\n"
    )
    with pytest.raises(GraphError) as caught:
        project.run("validate_trace")
    assert "specs/001-auth/artifacts.yaml" in str(caught.value)
    assert ".specify/traceability/requirements.yaml" in str(caught.value)


def test_an_artifact_with_no_id_is_refused(project):
    """Consistency with the WBS and risk stores, which always refused this.

    A typo'd `id:` key used to drop the artifact out of the graph without a word — the same
    silent data loss as a duplicate, wearing a different hat.
    """
    project.artifacts(lambda d: d["artifacts"].append({
        "di": "REQ-AUTH-0099", "type": "requirement", "title": "Typo in the id key",
        "status": "DRAFT", "owner": "someone"}))
    with pytest.raises(GraphError, match=r"artifact with no id \('Typo in the id key'\)"):
        project.run("validate_trace")


def test_a_duplicate_id_is_exit_2_not_exit_1(project):
    """A workflow branches on the difference.

    Exit 2 takes the setup-fault path, exit 1 the governance path. Telling someone their
    architecture milestone failed when the truth is a copy-pasted id would send them to fix
    the wrong thing.
    """
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "REQ-AUTH-0014", "type": "requirement", "title": "Reused id",
        "status": "DRAFT", "owner": "someone-else"}))
    assert project.script_rc("validate_trace.py", "--json") == 2
    assert project.script_rc("audit.py", "--json") == 2


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
# Approval (specup.md s31, s59) — the positive path TRC-009 demands
# --------------------------------------------------------------------------


def test_an_approved_edge_validates(project):
    """TRC-000 used to validate a document rebuilt from the loaded Edge objects, which had
    dropped exactly the fields an approved edge is required to carry. The result was a
    schema check that failed on a file the schema accepts."""
    project.approve("REQ-AUTH-0014", "refines", "BUS-OBJ-0017", by="product-owner")
    assert "TRC-000" not in failing(project.run("validate_trace"))


def test_a_baselined_requirement_can_actually_be_approved(project):
    """The regression test for the dead end: TRC-009 demanded 'approved' on edges touching a
    BASELINED requirement, and complying made TRC-000 fail. No state satisfied both, so s31's
    upper lifecycle (BASELINED -> IMPLEMENTED -> VERIFIED -> ACCEPTED) was unreachable."""
    project.artifact("REQ-AUTH-0014")(lambda a: a.update(
        status="BASELINED",
        approvals=[{"by": "product-owner", "at": "2026-09-10T09:00:00Z"}],
    ))
    for triple in project.asserted_edges_touching("REQ-AUTH-0014"):
        project.approve(*triple, by="product-owner")

    verdict = project.run("validate_trace")
    assert verdict.status == "PASS", f"still unreachable: {sorted(failing(verdict))}"
    assert verdict.metrics["approved_stale"] == 0


def test_an_unknown_key_in_a_store_is_rejected(project):
    """additionalProperties: false could never fire while TRC-000 validated a dict the loader
    built by hand — a stray key had nowhere to survive. This is the typo it now catches."""
    project.add_edge(**{"from": "TC-AUTH-0031", "relation": "tests",
                        "to": "src/auth/authentication_service.ts",
                        "provenance": "asserted", "provenence": "asserted"})
    assert_fails(project.run("validate_trace"), "TRC-000")


def test_editing_an_approved_endpoint_downgrades_the_edge(project):
    """The template promises "editing an endpoint downgrades the edge". Until TRC-013 it did
    not: approved_endpoints_hash was schema-required and read by nothing."""
    project.approve("REQ-AUTH-0014", "refines", "BUS-OBJ-0017", by="product-owner")
    project.artifact("REQ-AUTH-0014")(lambda a: a.update(title="Rewritten after approval"))

    verdict = project.run("validate_trace")
    assert verdict.metrics["approved_stale"] == 1
    assert verdict.metrics["approved_verified"] == 0
    assert any(c.id == "TRC-013" and c.status == "WARN" for c in verdict.checks)
    # WARN, not FAIL: a stale hash is a normal event in a live project. The consequence is
    # that the edge stops counting as evidence, not that the validator collapses.
    assert "TRC-013" not in failing(verdict)


def test_advancing_the_lifecycle_does_not_void_an_approval(project):
    """s31 status changes are bookkeeping about the artifact, not changes to what was
    approved. If BASELINED voided every signature, no project could ever leave the state."""
    project.approve("REQ-AUTH-0014", "refines", "BUS-OBJ-0017", by="product-owner")
    project.artifact("REQ-AUTH-0014")(lambda a: a.update(
        status="BASELINED",
        approvals=[{"by": "product-owner", "at": "2026-09-10T09:00:00Z"}],
    ))
    assert project.run("validate_trace").metrics["approved_stale"] == 0


def test_a_relabelled_edge_does_not_count_as_verifiable(project):
    """The bypass G2 closes: before TRC-013, relabelling asserted edges 'approved' with any
    syntactically valid hash moved traceability_final from 38% to 81% verifiable."""
    def relabel(document):
        for edge in document["edges"]:
            if edge["provenance"] == "asserted":
                edge["provenance"] = "approved"
                edge["approval"] = {"by": "release-owner", "at": "2026-09-12T10:00:00Z"}
                edge["approved_endpoints_hash"] = "0" * 64
    project.edges(relabel)
    project.config(lambda c: c["lifecycle"].update(phase="TRANSITION"))

    verdict = project.gate("GATE-PRODUCT_RELEASE")
    assert verdict.status == "FAIL"
    assert "traceability_final" in failing(verdict)


def test_approving_a_derived_edge_is_refused(project):
    """A signature on a machine-reproducible edge is strictly weaker evidence than the rule
    that reproduces it, so accepting one would be a downgrade dressed as governance."""
    assert project.approve_rc(
        "src/security/certificate_validator.ts", "conforms-to", "CONTRACT-AUTH-0001",
        by="product-owner",
    ) == 1


def test_approving_an_edge_in_the_machine_owned_store_is_refused(project):
    """derived.yaml is rewritten in full by derive_edges.py --write, so a signature written
    there would be erased on the next regeneration — a promise the file cannot keep."""
    assert project.approve_rc("SCEN-AUTH-0031", "executes", "AC-AUTH-0014-0003",
                              by="qa-team") == 1


def test_approving_an_edge_that_does_not_exist_is_an_operator_error(project):
    """Exit 2, not 1: the graph could not be evaluated, which is not a governance verdict."""
    assert project.approve_rc("REQ-AUTH-0014", "refines", "REQ-AUTH-0014",
                              by="product-owner") == 2


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


# --------------------------------------------------------------------------
# Definition of Done (specup.md s29) — the DoR/DoD symmetry
# --------------------------------------------------------------------------


def test_done_without_evidence_is_not_done(project):
    """s29: `status: done` is "a computed governance state rather than a casual AI
    declaration". Before validate_done.py it was exactly the declaration — an agent wrote
    `done` and nothing disagreed."""
    project.node("WBS-1.2.3.4.1.1.1")(lambda n: n.pop("evidence"))
    assert_fails(project.run("validate_done"), "DOD-001")


def test_done_with_an_evidence_reference_that_does_not_resolve_fails(project):
    project.node("WBS-1.2.3.4.1.1.1")(lambda n: n.update(evidence=["EVID-9999"]))
    assert_fails(project.run("validate_done"), "DOD-001")


def test_done_on_an_unverified_requirement_fails(project):
    project.drop_edges(**{"from": "TC-AUTH-0031", "relation": "verifies", "to": "REQ-AUTH-0014"})
    project.drop_edges(**{"from": "AC-AUTH-0014-0003", "relation": "verifies",
                          "to": "REQ-AUTH-0014"})
    assert_fails(project.run("validate_done"), "DOD-002")


def test_a_done_test_task_whose_criterion_has_no_scenario_fails(project):
    """A test task closed over a criterion nothing exercises has verified nothing."""
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "AC-AUTH-0014-0005", "type": "acceptance-criterion",
        "title": "Expired certificates are rejected", "status": "APPROVED", "owner": "qa-team",
    }))
    project.node("WBS-1.2.3.4.1.1.3")(lambda n: n["acceptance"].append("AC-AUTH-0014-0005"))
    assert_fails(project.run("validate_done"), "DOD-003")


def test_a_done_mitigation_that_never_reassessed_its_risk_fails(project):
    """An iteration that changed no risk estimate usually means the reassessment was
    skipped, not that nothing was learned."""
    project.risk("RISK-0007")(lambda r: [r.pop("residual_probability"), r.pop("residual_impact"),
                                         r.pop("residual_exposure")])
    assert_fails(project.run("validate_done"), "DOD-004")


def test_a_done_mitigation_with_no_evidence_on_the_risk_fails(project):
    project.risk("RISK-0007")(lambda r: r.pop("evidence"))
    assert_fails(project.run("validate_done"), "DOD-004")


def test_a_broken_edge_on_a_done_node_fails(project):
    project.add_edge(**{"from": "WBS-1.2.3.4.1.1.1", "relation": "implements",
                        "to": "REQ-AUTH-9999", "provenance": "asserted", "status": "broken"})
    assert_fails(project.run("validate_done"), "DOD-005")


def test_a_done_test_task_with_no_acceptance_criteria_fails(project):
    project.node("WBS-1.2.3.4.1.1.3")(lambda n: n.pop("acceptance"))
    assert_fails(project.run("validate_done"), "DOD-006")


def test_the_construction_gate_fails_on_work_that_is_only_claimed_done(project):
    """The condition config and its implementation land together: a condition named in
    config but unimplemented already fails closed, so config alone would be a false gate."""
    project.config(lambda c: c["lifecycle"].update(phase="CONSTRUCTION"))
    project.node("WBS-1.2.3.4.1.1.1")(lambda n: n.pop("evidence"))
    verdict = project.gate("GATE-INITIAL_OPERATIONAL_CAPABILITY")
    assert verdict.status == "FAIL"
    assert "definition_of_done_met" in failing(verdict)


# --------------------------------------------------------------------------
# Generated views (specup.md s47, s65)
# --------------------------------------------------------------------------


def test_missing_views_are_reported(project):
    """The fixture ships no generated views, so a fresh project must be told to render."""
    assert_fails(project.run("render_views"), "VIEW-001")


def test_a_hand_edited_view_is_reported_and_write_repairs_it(project):
    project.render_views()
    assert project.run("render_views").status == "PASS"

    (project.root / ".specify" / "wbs" / "wbs.md").write_text("# I edited this by hand\n")
    assert_fails(project.run("render_views"), "VIEW-001")

    project.render_views()
    assert project.run("render_views").status == "PASS"


def test_a_view_goes_stale_when_its_source_changes(project):
    """This is the whole point of s47: the view cannot quietly disagree with the YAML."""
    project.render_views()
    project.risk("RISK-0012")(lambda r: r.update(title="Renamed after rendering"))
    assert_fails(project.run("render_views"), "VIEW-001")


def test_the_rendered_coverage_view_carries_the_provenance_mix(project):
    """speckit.openup.trace.md promises the mix on this page — a coverage number without it
    overstates what is known."""
    project.render_views()
    coverage = (project.root / ".specify" / "traceability" / "coverage.md").read_text()
    assert "Evidence quality" in coverage
    for label in ("derived, reproduced", "derived, unreproduced", "approved, stale", "asserted"):
        assert label in coverage, f"coverage.md does not report {label!r}"


def test_the_generated_governance_documents_match_the_code_that_enforces_them(project):
    """A Definition of Ready that disagrees with select_work.py is worse than none: people
    read the document and the machine applies the code."""
    import select_work
    import validate_done

    project.render_views()
    ready = (project.root / ".specify" / "governance" / "definition-of-ready.md").read_text()
    done = (project.root / ".specify" / "governance" / "definition-of-done.md").read_text()
    for rule in select_work.READINESS_RULES:
        assert rule in ready, f"{rule} is applied but not published"
    for rule in validate_done.DONE_RULES:
        assert rule in done, f"{rule} is applied but not published"


def test_every_configured_gate_condition_is_described_in_the_generated_view(project):
    import evaluate_gate

    project.render_views()
    gates = (project.root / ".specify" / "governance" / "quality-gates.md").read_text()
    for name in evaluate_gate.CONDITIONS:
        assert name in evaluate_gate.DESCRIPTIONS, f"{name} has no description to publish"
    assert "definition_of_done_met" in gates


# --------------------------------------------------------------------------
# Change impact (specup.md s22, s52)
# --------------------------------------------------------------------------


def test_impact_reaches_the_fan_out_s52_asks_for(project):
    report = project.impact("REQ-AUTH-0014")
    groups = report["groups"]
    assert report["reached"] > 0
    for expected in ("WBS nodes", "Risks", "Tests", "Source files", "Acceptance criteria",
                     "Scenarios", "Contracts", "Evidence"):
        assert expected in groups, f"impact of a requirement should reach {expected}"


def test_impact_answers_the_reverse_query_from_a_source_file(project):
    """s22: "what requirements does this file affect?" — the direction the graph is for."""
    report = project.impact("src/auth/authentication_service.ts")
    reached = {entry["id"] for entries in report["groups"].values() for entry in entries}
    assert "REQ-AUTH-0014" in reached
    assert "BUS-OBJ-0017" in reached


def test_impact_on_an_unknown_id_is_an_operator_error(project):
    """Exit 2, not 1: a report that cannot run is not a governance verdict."""
    assert project.impact_rc("REQ-NOPE-0001") == 2


def test_a_registered_test_connected_to_nothing_is_an_orphan(project):
    """s54's orphan tests. A test nobody connected to a requirement or a file proves nothing
    about the graph — the commonest way a suite grows while coverage stands still."""
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "UNIT-AUTH-0099", "type": "unit-test", "title": "Disconnected unit test",
        "status": "IMPLEMENTED", "owner": "qa-team",
    }))
    assert_fails(project.run("validate_trace"), "TRC-008")


def test_a_contract_nothing_conforms_to_is_an_orphan(project):
    project.drop_edges(**{"from": "src/security/certificate_validator.ts",
                          "relation": "conforms-to", "to": "CONTRACT-AUTH-0001"})
    assert_fails(project.run("validate_trace"), "TRC-008")


def test_an_adr_can_be_linked_into_the_chain(project):
    """s20 puts Design Decision in the chain and s57 wants the relevant ADR in an L7 task's
    context. Before this, no signature admitted an architecture-decision at either end, so an
    ADR could be registered and never reached."""
    verdict = project.run("validate_trace")
    assert verdict.status == "PASS"
    assert "ADR-0019" in {entry["id"] for entries in
                          project.impact("REQ-AUTH-0014")["groups"].values() for entry in entries}


def test_the_relation_vocabulary_and_the_signature_table_are_the_same_set(project):
    """The mismatch that let `modifies` and `decomposes-to` sit unused and unnoticed: the
    schema's enum and the domain/range table were two lists nobody compared."""
    import validate_trace
    from openup_model import Grammar

    assert set(Grammar().relations) == set(validate_trace.SIGNATURES), (
        "artifact.schema.json's relation enum and validate_trace.SIGNATURES disagree"
    )


def test_every_relation_has_a_declared_inverse(project):
    import validate_trace
    from openup_model import INVERSE

    assert set(validate_trace.SIGNATURES) == set(INVERSE), (
        "a relation with no inverse cannot be traversed backwards, which is the whole point"
    )


def test_the_id_patterns_and_the_artifact_type_enum_are_the_same_set(project):
    """The same defect as the relation table above, one column over.

    `E2E` was missing from the grammar for exactly this reason: `artifactType` and the
    `<name>Id` patterns are two lists in one file that nobody compared, so a type could be
    nameable but unregistrable, or registrable but unreachable. Grammar builds its pattern
    table from the `Id` keys, so this asserts the two halves of that file agree.
    """
    import json
    import pathlib

    from openup_model import SCHEMA_DIR, Grammar

    enum = set(json.loads(
        (pathlib.Path(SCHEMA_DIR) / "artifact.schema.json").read_text()
    )["$defs"]["artifactType"]["enum"])
    patterns = set(Grammar().patterns)

    # `source-artifact` is the one type with no id pattern: the path is the identity.
    assert enum - {"source-artifact"} <= patterns, (
        f"declared artifact type(s) nothing can name: {sorted(enum - {'source-artifact'} - patterns)}"
    )
    # `trace` is the one pattern with no artifact type: TRACE-* names a relation, not a thing
    # the graph stores. ID-GRAMMAR.md s1.2 lists it as reserved but unmodelled.
    assert patterns - enum == {"trace"}, (
        f"id pattern(s) with no artifact type: {sorted(patterns - enum - {'trace'})}"
    )


def test_an_e2e_test_verifies_a_requirement_like_any_other_test(project):
    """`E2E-*` is a peer of `UNIT-*` and `INTG-*`, not a reserved prefix.

    A grammar entry nothing admits at either end is a name, not a type — the state
    ID-GRAMMAR.md calls "reserved but unmodelled" and warns against reading as support.
    """
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "E2E-AUTH-0031", "type": "e2e-test", "title": "Enrolment journey, end to end",
        "status": "IMPLEMENTED", "owner": "qa-team",
    }))
    project.add_edge(**{"from": "E2E-AUTH-0031", "relation": "verifies",
                        "to": "REQ-AUTH-0014", "provenance": "asserted"})
    verdict = project.run("validate_trace")
    assert verdict.status == "PASS", f"failing: {sorted(failing(verdict))}"


def test_an_e2e_test_connected_to_nothing_is_an_orphan(project):
    """The other half: being modelled means being subject to the same orphan rule."""
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "E2E-AUTH-0099", "type": "e2e-test", "title": "Disconnected journey",
        "status": "IMPLEMENTED", "owner": "qa-team",
    }))
    assert_fails(project.run("validate_trace"), "TRC-008")


def test_the_mitigation_band_is_a_real_knob(project):
    """`require_mitigation_at_or_above` was declared in the config and read by nothing, so
    both checks used `high` whatever it said. A setting that cannot move a verdict is worse
    than an absent one, because a reader trusts it."""
    project.risk("RISK-0007")(lambda r: r.update(mitigation=[]))
    assert_fails(project.run("validate_risk"), "RISK-004")

    # RISK-0007 sits at 0.54: high, but below critical. Raising the band should excuse it.
    project.config(lambda c: c["risk"].update(require_mitigation_at_or_above="critical"))
    assert "RISK-004" not in failing(project.run("validate_risk"))


def test_the_verification_band_is_a_real_knob(project):
    project.risk("RISK-0007")(lambda r: r.update(verification=[]))
    assert_fails(project.run("validate_risk"), "RISK-005")

    project.config(lambda c: c["risk"].update(require_verification_at_or_above="critical"))
    assert "RISK-005" not in failing(project.run("validate_risk"))


def test_every_setting_in_the_shipped_config_is_read_by_something(project):
    """The defect this closes twice over: a config key nobody reads reads as a promise. Any
    key that survives unread must carry the NOT YET READ header, as `contracts:` does."""
    import pathlib
    import re

    import yaml

    extension = pathlib.Path(__file__).resolve().parent.parent / "extensions" / "openup"
    text = (extension / "openup-config.yml").read_text()
    config = yaml.safe_load(text)
    source = "\n".join(p.read_text() for p in (extension / "scripts" / "python").glob("*.py"))

    # Blocks that openly declare themselves inert are exempt — that header is the contract.
    exempt = {
        block for block in config
        if re.search(rf"^{re.escape(block)}:\n(  #[^\n]*\n)*?  # NOT YET READ BY ANY VALIDATOR",
                     text, re.MULTILINE)
        or f"{block}:\n  # NOT YET READ BY ANY VALIDATOR" in text
    }
    assert exempt, "the NOT YET READ marker is how an inert block declares itself; none found"

    unread = []
    for block, body in config.items():
        if block in exempt or not isinstance(body, dict):
            continue
        for key in body:
            if key.startswith("GATE-"):
                continue
            if f'"{key}"' not in source and f"'{key}'" not in source:
                unread.append(f"{block}.{key}")
    assert not unread, (
        f"declared in openup-config.yml but read by no validator: {unread}. Either implement "
        f"them, delete them, or move them under a NOT YET READ BY ANY VALIDATOR header."
    )


# --------------------------------------------------------------------------
# Progressive context (specup.md s7, s9, s56, s57)
# --------------------------------------------------------------------------


def test_the_good_fixture_has_a_complete_context_hierarchy(project):
    verdict = project.run("validate_context")
    assert verdict.status == "PASS", sorted(failing(verdict))
    assert "CTX-001" not in {c.id for c in verdict.checks if c.status == "WARN"}
    assert verdict.metrics["dangling_references"] == 0


def test_an_index_pointing_at_a_deleted_requirement_fails(project):
    """The check that earns its place. A context map naming an artifact that no longer exists
    does not merely fail to help — it sends an agent looking for something that is not there,
    and an agent willing to infer will fill the hole itself."""
    project.artifacts(lambda d: d.update(
        artifacts=[a for a in d["artifacts"] if a["id"] != "NON-FR-AUTH-0017"]))
    assert_fails(project.run("validate_context"), "CTX-002")


def test_a_missing_index_warns_rather_than_fails(project):
    """An existing project adopting SpecUP must not fail its first audit over absent
    documentation. A missing map is a gap; a misleading one is a defect."""
    (project.root / ".specify" / "wbs" / "index.md").unlink()
    verdict = project.run("validate_context")
    assert verdict.status == "PASS"
    assert any(c.id == "CTX-001" and c.status == "WARN" for c in verdict.checks)


def test_a_wbs_node_naming_a_skill_that_does_not_exist_fails(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(skills=["telepathy"]))
    assert_fails(project.run("validate_context"), "CTX-004")


def test_a_wbs_node_naming_a_shipped_skill_resolves(project):
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(skills=["traceability"]))
    assert project.run("validate_context").status == "PASS"


def test_governance_documents_are_never_inside_the_traceability_perimeter(project):
    """Seeding AGENTS.md into a source tree must not lower backward coverage — a check that
    punished the context hierarchy would set two parts of the design against each other."""
    (project.root / "src" / "security" / "AGENTS.md").write_text("# Scoped contract\n")
    (project.root / "src" / "security" / "index.md").write_text("# Map\n")
    assert project.run("validate_trace").status == "PASS"


def test_a_wbs_node_may_declare_the_skills_its_work_needs(project):
    """CTX-004 reads `skills`, so the schema has to admit it — a check that reads a field
    nothing may write is a check that can only ever pass."""
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(skills=["traceability", "risk"]))
    assert project.run("validate_wbs").status == "PASS"
    assert project.run("validate_context").status == "PASS"


def test_a_task_naming_a_missing_skill_is_not_ready(project):
    """s28's Definition of Ready lists "Applicable SKILL.md". Naming one that does not exist
    sends the agent looking for guidance that is not there."""
    project.config(lambda c: c["lifecycle"].update(iteration="ITER-E-02"))
    project.node("WBS-1.2.3.4.1.1.2")(lambda n: n.update(status="planned", skills=["telepathy"]))
    blockers = " ".join(
        reason for item in project.run("select_work").metrics["blockers"]
        for reason in item["reasons"]
    )
    assert "DOR-009" in blockers
