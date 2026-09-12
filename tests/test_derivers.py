"""The derivation rules, and the checks that keep `provenance: derived` honest.

The point of these is narrow and specific: before derivers.py existed, `derived` was a label
anyone could type. traceability.schema.json required `derived_by` to be *present*; nothing
required it to be *true*. An agent grading its own traceability could move an edge from
'asserted' to 'derived', improve the provenance mix it is measured on, and leave behind
something no reviewer could distinguish from a real derivation.

So the load-bearing test in this file is test_relabelling_an_assertion_as_derived_is_caught.
If that one passes while the rest fail, the property that matters still holds; if it fails,
the provenance model is decorative again no matter what else is green.
"""

from __future__ import annotations

import pytest
from conftest import assert_fails, failing

import derivers


FEATURE = "specs/001-auth/acceptance/vehicle-auth.feature"


def write_feature(project, body: str) -> None:
    (project.root / FEATURE).write_text(body)


def load(project):
    from openup_model import load_graph

    graph, _ = load_graph(str(project.root))
    return graph


def regenerate(project) -> None:
    """Rewrite the machine-owned store, the way `derive_edges.py --write` does."""
    import derive_edges

    class Args:
        root = str(project.root)
        json = False
        out = None
        write = True

    assert derive_edges.write_store(Args()) == 0


# --------------------------------------------------------------------------
# Gherkin parsing
# --------------------------------------------------------------------------


def test_feature_tags_are_inherited_by_every_scenario():
    scenarios = derivers.parse_feature(
        "@REQ-AUTH-0014\n"
        "Feature: F\n"
        "  @SCEN-AUTH-0031\n"
        "  Scenario: one\n"
        "  @SCEN-AUTH-0032\n"
        "  Scenario: two\n"
    )
    assert [name for name, _, _ in scenarios] == ["one", "two"]
    assert all("REQ-AUTH-0014" in tags for _, tags, _ in scenarios)


def test_a_scenarios_own_tags_do_not_leak_to_the_next_scenario():
    scenarios = derivers.parse_feature(
        "Feature: F\n"
        "  @SCEN-AUTH-0031\n  @AC-AUTH-0014-0003\n  Scenario: one\n"
        "  @SCEN-AUTH-0032\n  Scenario: two\n"
    )
    assert "AC-AUTH-0014-0003" not in scenarios[1][1]


def test_rule_tags_apply_only_within_their_rule():
    scenarios = derivers.parse_feature(
        "Feature: F\n"
        "  @NON-FR-AUTH-0017\n  Rule: latency\n"
        "    @SCEN-AUTH-0031\n    Scenario: inside\n"
        "  Rule: other\n"
        "    @SCEN-AUTH-0032\n    Scenario: outside\n"
    )
    assert "NON-FR-AUTH-0017" in scenarios[0][1]
    assert "NON-FR-AUTH-0017" not in scenarios[1][1]


def test_an_examples_table_does_not_count_as_a_scenario():
    scenarios = derivers.parse_feature(
        "Feature: F\n"
        "  @SCEN-AUTH-0031\n  Scenario Outline: parametrised\n"
        "    Given <x>\n"
        "  Examples:\n    | x |\n    | 1 |\n"
    )
    assert len(scenarios) == 1


def test_an_at_sign_inside_a_docstring_is_not_a_tag():
    scenarios = derivers.parse_feature(
        "Feature: F\n"
        "  @SCEN-AUTH-0031\n  Scenario: one\n"
        '    Given a payload\n      """\n      @AC-AUTH-0014-0009 is prose, not a tag\n      """\n'
        "  @SCEN-AUTH-0032\n  Scenario: two\n"
    )
    assert "AC-AUTH-0014-0009" not in scenarios[0][1]
    assert len(scenarios) == 2


# --------------------------------------------------------------------------
# The rules recover what the fixture declares
# --------------------------------------------------------------------------


def test_the_fixture_is_reproducible_end_to_end(project):
    """Every derived edge in the good fixture is either reproduced or openly unverified."""
    verdict = project.run("validate_trace")
    assert verdict.status == "PASS", sorted(failing(verdict))
    assert verdict.metrics["derived_verified"] == 10
    assert verdict.metrics["derived_unverified"] == 5


def test_gherkin_scan_binds_scenarios_to_their_criteria(project):
    triples = derivers.derive_gherkin_tags(load(project)).triples
    assert ("SCEN-AUTH-0031", "executes", "AC-AUTH-0014-0003") in triples
    assert ("SCEN-AUTH-0032", "executes", "AC-AUTH-0014-0004") in triples


def test_a_scenario_with_no_identity_tag_derives_nothing(project):
    write_feature(project, "@REQ-AUTH-0014\nFeature: F\n  @AC-AUTH-0014-0003\n  Scenario: untagged\n")
    result = derivers.derive_gherkin_tags(load(project))
    assert result.triples == set()
    assert any("exactly one @SCEN-" in note for note in result.notes)


def test_a_scenario_with_no_criterion_tag_is_reported(project):
    write_feature(project, "@REQ-AUTH-0014\nFeature: F\n  @SCEN-AUTH-0031\n  Scenario: floating\n")
    result = derivers.derive_gherkin_tags(load(project))
    assert result.triples == set()
    assert any("no @AC- tag" in note for note in result.notes)


def test_test_file_naming_finds_the_file_under_test(project):
    triples = derivers.derive_test_file_naming(load(project)).triples
    assert ("UNIT-AUTH-0031", "tests", "src/security/certificate_validator.ts") in triples


def test_an_ambiguous_test_name_derives_nothing(project):
    """Two candidates is a guess, and a guess recorded as 'derived' is worse than no edge."""
    (project.root / "src" / "auth" / "certificate_validator.ts").write_text("export const x = 1;\n")
    result = derivers.derive_test_file_naming(load(project))
    assert not any(t[0] == "UNIT-AUTH-0031" for t in result.triples)
    assert any("ambiguous" in note for note in result.notes)


def test_a_test_artifact_without_a_source_file_derives_nothing(project):
    project.artifact("UNIT-AUTH-0031")(lambda a: a.pop("source"))
    result = derivers.derive_test_file_naming(load(project))
    assert result.triples == set()


def test_wbs_iteration_edges_come_from_the_node_field(project):
    triples = derivers.derive_wbs_iteration(load(project)).triples
    assert ("WBS-1.2.3.4.1.1.2", "belongs-to", "ITER-E-02") in triples
    # WBS-1 and WBS-1.2 carry no iteration, so they must not appear.
    assert not any(t[0] in {"WBS-1", "WBS-1.2"} for t in triples)


# --------------------------------------------------------------------------
# TRC-010 — the claim has to survive being re-run
# --------------------------------------------------------------------------


def test_relabelling_an_assertion_as_derived_is_caught(project):
    """The bypass this whole module exists to close.

    An agent improves the provenance mix it is graded on by moving one of its own claims from
    'asserted' to 'derived' and naming a real rule. Re-running the rule is what makes that
    fail instead of pay.
    """
    project.drop_edges(**{"from": "WBS-1.2.3.4.1.1.1", "relation": "implements",
                          "to": "REQ-AUTH-0014"})
    project.add_edge(**{"from": "WBS-1.2.3.4.1.1.1", "relation": "implements",
                        "to": "REQ-AUTH-0014", "provenance": "derived",
                        "derived_by": "task-modifies-closure"})
    # An unimplemented rule cannot be checked, so it must not be counted as evidence either.
    assert project.run("validate_trace").metrics["derived_unverified"] == 6

    project.drop_edges(**{"from": "WBS-1.2.3.4.1.1.1", "relation": "implements",
                          "to": "REQ-AUTH-0014"})
    project.add_edge(**{"from": "WBS-1.2.3.4.1.1.1", "relation": "implements",
                        "to": "REQ-AUTH-0014", "provenance": "derived",
                        "derived_by": "test-file-naming-convention"})
    assert_fails(project.run("validate_trace"), "TRC-010")


def test_an_invented_rule_name_is_rejected(project):
    project.add_edge(**{"from": "UNIT-AUTH-0031", "relation": "tests",
                        "to": "src/auth/authentication_service.ts",
                        "provenance": "derived", "derived_by": "looks-official-enough"})
    assert_fails(project.run("validate_trace"), "TRC-010")


def test_editing_the_generated_store_by_hand_fails(project):
    """derived.yaml is machine-owned; a hand edit does not survive the rule being re-run."""
    project.edit_yaml(".specify/traceability/derived.yaml", lambda d: d["edges"].append({
        "from": "SCEN-AUTH-0031", "relation": "executes", "to": "AC-AUTH-0014-0004",
        "provenance": "derived", "derived_by": "gherkin-tag-scan",
    }))
    assert_fails(project.run("validate_trace"), "TRC-010")


def test_retagging_the_feature_file_moves_the_edge(project):
    """The filesystem is the authority: change the tag, and the derivation changes with it."""
    write_feature(project,
                  "@REQ-AUTH-0014\nFeature: F\n"
                  "  @SCEN-AUTH-0031\n  @AC-AUTH-0014-0003\n  Scenario: one\n"
                  "  @SCEN-AUTH-0032\n  @AC-AUTH-0014-0003\n  Scenario: two\n")
    # The stored SCEN-0032 --executes--> AC-0004 edge is no longer reproducible, and the new
    # SCEN-0032 --executes--> AC-0003 edge is not in any store yet.
    assert {"TRC-010", "TRC-011"} <= failing(project.run("validate_trace"))

    # Regenerating resolves both — and then surfaces what the retag actually cost: nothing
    # executes AC-0004 any more. The stale edge had been hiding that.
    regenerate(project)
    verdict = project.run("validate_trace")
    assert failing(verdict) == {"TRC-012"}, sorted(failing(verdict))


# --------------------------------------------------------------------------
# TRC-011 — the graph may not fall behind the filesystem
# --------------------------------------------------------------------------


def test_a_derivable_edge_missing_from_the_store_fails(project):
    project.edit_yaml(".specify/traceability/derived.yaml", lambda d: d.update(
        edges=[e for e in d["edges"] if e["derived_by"] != "test-file-naming-convention"]))
    assert_fails(project.run("validate_trace"), "TRC-011")


def test_a_new_scenario_must_be_recorded_before_the_graph_passes(project):
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "SCEN-AUTH-0033", "type": "scenario", "title": "Expired certificate",
        "status": "DRAFT", "owner": "qa-team", "source": FEATURE,
    }))
    with open(project.root / FEATURE, "a") as handle:
        handle.write("\n  @SCEN-AUTH-0033\n  @AC-AUTH-0014-0003\n  Scenario: expired\n")
    assert_fails(project.run("validate_trace"), "TRC-011")


def test_derive_edges_write_repairs_what_trc_011_reports(project):
    """The check has a fix, and the fix is one command."""
    project.edit_yaml(".specify/traceability/derived.yaml",
                      lambda d: d.update(edges=[]))
    assert_fails(project.run("validate_trace"), "TRC-011")

    regenerate(project)
    assert project.run("validate_trace").status == "PASS"


# --------------------------------------------------------------------------
# TRC-012 — specup.md s24
# --------------------------------------------------------------------------


def test_an_acceptance_criterion_with_no_scenario_fails(project):
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "AC-AUTH-0014-0009", "type": "acceptance-criterion",
        "title": "Revoked certificates are rejected", "status": "DRAFT", "owner": "qa-team",
    }))
    assert_fails(project.run("validate_trace"), "TRC-012")


def test_scenario_coverage_can_be_switched_off_deliberately(project):
    project.artifacts(lambda d: d["artifacts"].append({
        "id": "AC-AUTH-0014-0009", "type": "acceptance-criterion",
        "title": "Revoked certificates are rejected", "status": "DRAFT", "owner": "qa-team",
    }))
    project.config(lambda c: c["gherkin"].update(require_scenario_per_ac=False))
    verdict = project.run("validate_trace")
    assert "TRC-012" not in failing(verdict)
    assert verdict.metrics["scenario_coverage"] < 1.0


# --------------------------------------------------------------------------
# The release gate counts reproduced evidence, not labels
# --------------------------------------------------------------------------


def test_the_release_gate_does_not_reward_relabelling(project):
    """Turning every asserted edge into a 'derived' one must not buy a passing gate."""
    project.config(lambda c: c["lifecycle"].update(phase="TRANSITION"))
    before = project.gate("GATE-PRODUCT_RELEASE")
    assert "traceability_final" in failing(before)

    def relabel(document):
        for edge in document["edges"]:
            if edge.get("provenance") == "asserted":
                edge["provenance"] = "derived"
                edge["derived_by"] = "task-modifies-closure"
    project.edges(relabel)

    after = project.gate("GATE-PRODUCT_RELEASE")
    assert "traceability_final" in failing(after), (
        "relabelling assertions as 'derived' bought a passing gate — the provenance model "
        "is measuring the label instead of the evidence"
    )


def test_the_perimeter_excludes_every_test_marker_the_deriver_recognises():
    """A test file the deriver knows about but the perimeter does not is counted twice over.

    It derives a `tests` edge *and* reports as an untraced in-perimeter source file, so
    backward coverage falls every time someone adds a test — which teaches people to widen
    the exclude list until the perimeter stops meaning anything.
    """
    import yaml
    from conftest import REPO_ROOT

    config = yaml.safe_load(
        (REPO_ROOT / "extensions" / "openup" / "openup-config.yml").read_text())
    excludes = set(config["traceability"]["perimeter"]["exclude"])
    testing = config["testing"]

    expected = ({f"**/*{marker}.*" for marker in testing["stem_suffixes"]}
                | {f"**/{marker}*.*" for marker in testing["stem_prefixes"]})
    missing = sorted(expected - excludes)
    assert not missing, f"test markers with no matching perimeter exclude: {missing}"


@pytest.mark.parametrize("rule", sorted(derivers.UNIMPLEMENTED_RULES))
def test_every_unimplemented_rule_is_declared_not_silently_missing(rule):
    """An unimplemented rule must be a known gap, not an unknown one — TRC-010 tells them
    apart, and only the declared gap is tolerated."""
    assert rule in derivers.KNOWN_RULES
    assert rule not in derivers.RULES
