"""Validate the OpenUP phase workflows.

Two layers:

1. Structural rules we impose on ourselves — most importantly that no user-supplied input
   ever reaches a `run:` field, since shell steps interpolate expressions as raw text with
   no quoting or escaping.
2. The real Spec Kit engine's own validator, when `specify-cli` is importable. That layer
   is skipped rather than faked when it is absent: a green test that did not actually run
   the engine would be worse than an honest skip.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW_DIR = REPO_ROOT / "workflows"
SCRIPT_DIR = REPO_ROOT / "extensions" / "openup" / "scripts" / "python"

WORKFLOW_PATHS = sorted(WORKFLOW_DIR.glob("*/workflow.yml"))

EXPECTED_GATES = {
    "openup-inception": "GATE-LIFECYCLE_OBJECTIVES",
    "openup-elaboration": "GATE-LIFECYCLE_ARCHITECTURE",
    "openup-construction": "GATE-INITIAL_OPERATIONAL_CAPABILITY",
    "openup-transition": "GATE-PRODUCT_RELEASE",
}

try:
    from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False


def load(path: pathlib.Path) -> dict:
    return yaml.safe_load(path.read_text())


def walk_steps(steps):
    """Yield every step, including those nested in if/then, else, switch cases, loops, fan-out."""
    for step in steps or []:
        yield step
        for key in ("then", "else", "steps"):
            yield from walk_steps(step.get(key))
        for branch in (step.get("cases") or {}).values():
            yield from walk_steps(branch)
        yield from walk_steps(step.get("default"))
        if isinstance(step.get("step"), dict):
            yield from walk_steps([step["step"]])


def all_steps(path: pathlib.Path):
    return list(walk_steps(load(path).get("steps")))


def test_all_four_phase_workflows_exist():
    assert {p.parent.name for p in WORKFLOW_PATHS} == set(EXPECTED_GATES)


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_workflow_has_required_metadata(path):
    document = load(path)
    assert document["schema_version"] == "1.0"
    block = document["workflow"]
    for field in ("id", "name", "version", "author", "description"):
        assert block.get(field), f"workflow.{field} is required"
    assert block["id"] == path.parent.name, "directory name must match the workflow id"
    assert document["requires"]["speckit_version"].startswith(">=")


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_step_ids_are_unique(path):
    ids = [s["id"] for s in all_steps(path)]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"duplicate step ids: {sorted(duplicates)}"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_no_user_input_is_interpolated_into_a_shell_command(path):
    """The security rule. A `run` field is executed by the system shell and `{{ }}` values
    are substituted as raw text with no escaping, so an inputs value would be parsed as
    shell syntax. Only engine-controlled values may appear."""
    allowed = {"context.run_id"}
    for step in all_steps(path):
        run = step.get("run")
        if not run:
            continue
        for expression in re.findall(r"\{\{(.*?)\}\}", run):
            token = expression.strip()
            assert token in allowed, (
                f"{path.parent.name}/{step['id']}: `run` interpolates {token!r}, which is not "
                f"an engine-controlled value. Allowed: {sorted(allowed)}"
            )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_referenced_scripts_exist_at_their_installed_path(path):
    for step in all_steps(path):
        run = step.get("run", "")
        for script in re.findall(r"\.specify/extensions/openup/scripts/python/([a-z_]+\.py)", run):
            assert (SCRIPT_DIR / script).is_file(), (
                f"{path.parent.name}/{step['id']} runs {script}, which does not exist"
            )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_gates_that_abort_on_reject_offer_reject(path):
    for step in all_steps(path):
        if step.get("type") != "gate":
            continue
        options = step.get("options", [])
        assert options, f"{step['id']} is a gate with no options"
        if step.get("on_reject") == "abort":
            assert "reject" in options, (
                f"{step['id']} declares on_reject: abort but offers no 'reject' option, "
                f"so the abort path is unreachable"
            )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_workflow_evaluates_its_own_phase_gate(path):
    expected = EXPECTED_GATES[path.parent.name]
    runs = " ".join(s.get("run", "") for s in all_steps(path))
    assert expected in runs, f"{path.parent.name} never evaluates {expected}"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_gate_evaluation_is_branchable_and_writes_evidence(path):
    """The enforcement contract: the gate step must not halt the run itself (or the human
    branch is unreachable), and it must persist its verdict as evidence."""
    for step in all_steps(path):
        run = step.get("run", "")
        if "evaluate_gate.py" not in run or "overrides" in run:
            continue
        assert step.get("continue_on_error") is True, (
            f"{step['id']}: the gate check must set continue_on_error so the `if` below can "
            f"branch on its exit code"
        )
        assert "--out" in run, f"{step['id']}: the gate verdict must be written as evidence"
        assert "--json" in run, f"{step['id']}: the gate verdict must be JSON"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_every_workflow_distinguishes_setup_faults_from_governance_failures(path):
    """Exit 2 means the graph could not be loaded. Treating that as a governance failure
    would present a broken setup to a human as if the project had failed its milestone."""
    conditions = [s.get("condition", "") for s in all_steps(path) if s.get("type") == "if"]
    joined = " ".join(conditions)
    assert "exit_code == 2" in joined, f"{path.parent.name} does not handle the exit-2 setup fault"
    assert "exit_code == 1" in joined, f"{path.parent.name} does not branch on the exit-1 gate failure"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_if_conditions_reference_steps_that_exist(path):
    known = {s["id"] for s in all_steps(path)}
    for step in all_steps(path):
        for referenced in re.findall(r"steps\.([a-z0-9-]+)\.", step.get("condition", "") or ""):
            assert referenced in known, f"{step['id']} references unknown step {referenced!r}"
        for referenced in re.findall(r"steps\.([a-z0-9-]+)\.", str(step.get("items", "")) or ""):
            assert referenced in known, f"{step['id']} fans out over unknown step {referenced!r}"


def test_construction_fans_out_over_deterministically_selected_work():
    """The iteration set must come from the graph, not from model output, or the scope of an
    iteration is not reproducible."""
    steps = all_steps(WORKFLOW_DIR / "openup-construction" / "workflow.yml")
    fan_out = next(s for s in steps if s.get("type") == "fan-out")
    assert "select-work" in fan_out["items"], "fan-out must consume select_work.py output"
    assert "from_json" in fan_out["items"], "items must be parsed from the JSON array"

    selector = next(s for s in steps if "select_work.py" in s.get("run", ""))
    assert "--ids-only" in selector["run"], (
        "the selector must emit a bare JSON array; a verdict object would not be a valid "
        "fan-out collection"
    )


@pytest.mark.skipif(not ENGINE_AVAILABLE, reason="specify-cli is not installed")
@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_engine_accepts_the_workflow(path):
    definition = WorkflowDefinition.from_yaml(path)
    errors = validate_workflow(definition)
    assert not errors, f"{path.parent.name} rejected by the engine: {errors}"
