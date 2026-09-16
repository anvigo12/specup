"""The worked example is in the state it claims to be in.

`examples/my-program` passes the Inception gate and fails the Elaboration gate on five
conditions. Both halves are asserted here, and the second half is the one that matters: an
example that quietly drifted into passing would teach a reader that the gates are decorative,
and the first thing anyone copying it would learn is how to produce a project that reports
success.

So these tests pin the exact failing set rather than `status == "FAIL"`. If somebody fills in
the architecture document, the failure count moves and this suite says which lesson went with
it — which is the conversation worth having, rather than a green tick over a changed example.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRAM = REPO_ROOT / "examples" / "my-program"
PROJECT = REPO_ROOT / "examples" / "my-project"


class Args:
    """The argument shape every validator's `validate()` reads."""

    root = str(PROGRAM)
    json = False


@pytest.fixture(scope="module")
def gate():
    import evaluate_gate
    import validate_approvals
    import validate_done
    import validate_risk
    import validate_trace
    import validate_wbs
    from openup_model import load_graph

    graph, config = load_graph(str(PROGRAM))

    def evaluate(name: str):
        ctx = evaluate_gate.GateContext(
            root=graph.root, graph=graph, config=config,
            wbs=validate_wbs.validate(Args()),
            risk=validate_risk.validate(Args()),
            trace=validate_trace.validate(Args()),
            done=validate_done.validate(Args()),
            approvals=validate_approvals.validate(Args()),
        )
        return evaluate_gate.evaluate(name, ctx)

    return evaluate


def statuses(verdict) -> dict[str, str]:
    return {check.id: check.status for check in verdict.checks}


# -- the two gates ---------------------------------------------------------------------


def test_the_example_passes_the_inception_gate(gate):
    """Everything Inception asks for is genuinely there: a vision, named stakeholders, sized
    risks, a WBS skeleton, and requirements with owners."""
    verdict = gate("GATE-LIFECYCLE_OBJECTIVES")
    assert verdict.status == "PASS", statuses(verdict)
    assert len(verdict.checks) == 5


def test_the_example_fails_the_elaboration_gate_on_exactly_five_conditions(gate):
    """The list is the lesson, so the list is what is asserted.

    Each of these has a one-minute repair that turns the gate green and the record false —
    `examples/README.md` names every one of them. If a condition leaves this set, the example
    has been filled in for the reader and something they needed to see is gone.
    """
    verdict = gate("GATE-LIFECYCLE_ARCHITECTURE")
    by_id = statuses(verdict)
    assert {cid for cid, status in by_id.items() if status == "FAIL"} == {
        "architecture_baselined",
        "all_high_risks_have_mitigation",
        "requirements_traceable",
        "critical_contracts_defined",
        "security_review_complete",
    }, by_id


def test_the_two_conditions_it_passes_are_the_ones_it_has_earned(gate):
    """`human_approvals_witnessed` passes only because this copy of the approval matrix is
    filled in. The shipped template leaves the "who" column blank and `APV-000` fails on it,
    which is the difference between a template and an example."""
    by_id = statuses(gate("GATE-LIFECYCLE_ARCHITECTURE"))
    assert by_id["wbs_valid"] == "PASS"
    assert by_id["human_approvals_witnessed"] == "PASS"


# -- what the example does hold up ------------------------------------------------------


@pytest.mark.parametrize("module_name", ["validate_wbs", "validate_approvals",
                                         "validate_context", "validate_docs", "validate_done"])
def test_the_validators_the_example_should_satisfy_do_pass(module_name):
    """Failing Elaboration is the point; failing a structural check would just be a broken
    example. The WBS is valid, the matrix names people, every id in every context map
    resolves, and nothing claims to be done."""
    import importlib

    verdict = importlib.import_module(module_name).validate(Args())
    assert verdict.status == "PASS", {c.id: c.status for c in verdict.checks if c.status == "FAIL"}


def test_the_failing_validators_fail_only_where_the_example_says_they_do():
    import validate_risk
    import validate_trace

    risk = {c.id for c in validate_risk.validate(Args()).checks if c.status == "FAIL"}
    assert risk == {"RISK-005"}, risk

    trace = {c.id for c in validate_trace.validate(Args()).checks if c.status == "FAIL"}
    assert trace == {"TRC-005", "TRC-006", "TRC-012"}, trace


def test_the_audit_is_a_governance_failure_not_a_setup_fault():
    """Exit 1, never exit 2. A workflow branches on the difference, and an example that
    exited 2 would be teaching people to debug their environment."""
    import audit

    report, code = audit.audit(Args())
    assert code == 1
    assert report["sections"]["gate"]["status"] == "PASS"  # the Inception gate is current


def test_the_derived_edges_are_reproduced_rather_than_declared():
    """Ten of the fourteen edges are machine-derived, and `TRC-010` re-runs the rule behind
    each one. A worked example whose provenance was 100% `asserted` would never show a reader
    what the distinction buys."""
    import validate_trace

    metrics = validate_trace.validate(Args()).metrics
    assert metrics["provenance_mix"]["derived"] == 10
    assert metrics["derived_verified"] == 10
    assert metrics["derived_unverified"] == 0


def test_backward_coverage_over_this_tree_is_vacuous_and_the_example_says_so():
    """The perimeter is empty because the deliverable is in a different root. A reader who
    takes `backward_coverage: 1.0` at face value has been misled by a ratio with nothing in
    the denominator, so both the config and the context map name it."""
    import validate_trace

    assert validate_trace.validate(Args()).metrics["perimeter_files"] == 0
    for path in (PROGRAM / ".specify/extensions/openup/openup-config.yml",
                 PROGRAM / ".specify/traceability/index.md"):
        assert "vacuous" in path.read_text() or "nothing in the denominator" in path.read_text()


# -- the deliverable --------------------------------------------------------------------


def test_the_deliverable_carries_no_second_governance_tree():
    """One program, one graph. A `.specify/` here would be a second one, and two graphs over
    the same work is the drift the whole model exists to prevent."""
    assert PROJECT.is_dir()
    assert not (PROJECT / ".specify").exists()


def test_the_example_source_satisfies_the_docstring_contract():
    """`my-project` is outside every perimeter, so no validator will ever read it. Its
    docstrings are written to pass `DOC-*` anyway — an example that taught the contract and
    then broke it would be teaching the wrong half.

    Scoped to `src/`, which is what the contract covers. `tests/` is excluded from every
    perimeter the shipped config defines (`**/test_*.*`), so holding the example's tests to a
    rule the validator would never apply to them would be inventing a stricter standard than
    the one being taught.
    """
    import validate_docs

    for path in sorted((PROJECT / "src").rglob("*.py")):
        units = validate_docs.exported_units(str(path), path.read_text())
        assert units, path
        for unit in units:
            doc = (unit.doc or "").strip()
            assert doc, f"{path}:{unit.lineno} {unit.name} has no docstring"
            assert len(doc.splitlines()) <= 40, unit.where
            if validate_docs.CROSS_CHECK_CLAIM.search(doc):
                assert len(validate_docs.named_sources(doc)) >= 2, unit.where
        module = units[0]
        assert validate_docs.BOUNDARY.search(module.doc or ""), f"{path} states no boundary"
