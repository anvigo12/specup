"""End-to-end test of the extension in its INSTALLED layout.

The command files tell an agent to run, for example:

    python .specify/extensions/openup/scripts/python/audit.py --json

That path only resolves once the extension is installed under `.specify/extensions/openup/`,
which is a different layout from this repo. These tests install it the way Spec Kit does and
run the documented invocations verbatim, so a broken path is caught here rather than by a
user whose gate silently never ran.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXTENSION_SRC = REPO_ROOT / "extensions" / "openup"
GOOD_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "good"

SCRIPT_DIR = ".specify/extensions/openup/scripts/python"


def install(project_root: pathlib.Path) -> None:
    target = project_root / ".specify" / "extensions" / "openup"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(EXTENSION_SRC, target, ignore=shutil.ignore_patterns("__pycache__"))


def run(project_root: pathlib.Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", f"{SCRIPT_DIR}/{script}", *args],
        cwd=project_root, capture_output=True, text=True,
    )


@pytest.fixture
def empty_project(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "project"
    (root / ".specify").mkdir(parents=True)
    install(root)
    return root


@pytest.fixture
def governed_project(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "project"
    shutil.copytree(GOOD_FIXTURE, root)
    install(root)
    return root


def test_init_runs_from_the_installed_path(empty_project):
    result = run(empty_project, "init_openup.py", "--program", "Test Program", "--json")
    assert result.returncode == 0, result.stderr
    verdict = json.loads(result.stdout)
    assert verdict["status"] == "PASS"
    assert verdict["metrics"]["created"] > 0


def test_init_seeds_every_store_the_validators_read(empty_project):
    run(empty_project, "init_openup.py", "--program", "Test Program", "--json")
    for relative in (
        ".specify/wbs/wbs.yaml",
        ".specify/risks/risk-register.yaml",
        ".specify/traceability/requirements.yaml",
        ".specify/traceability/traceability.yaml",
        ".specify/extensions/openup/openup-config.yml",
    ):
        assert (empty_project / relative).is_file(), f"init did not seed {relative}"


def test_program_name_reaches_the_wbs_root(empty_project):
    run(empty_project, "init_openup.py", "--program", "Autonomous Traffic Platform", "--json")
    content = (empty_project / ".specify/wbs/wbs.yaml").read_text()
    assert "Autonomous Traffic Platform" in content
    assert "REPLACE-WITH-PROGRAM-NAME" not in content.split("nodes:")[0]


@pytest.mark.parametrize(
    "script",
    ["validate_wbs.py", "validate_risk.py", "validate_trace.py", "audit.py"],
)
def test_validators_pass_on_the_governed_project_from_the_installed_path(governed_project, script):
    result = run(governed_project, script, "--json")
    assert result.returncode == 0, f"{script} failed:\n{result.stdout}\n{result.stderr}"
    assert json.loads(result.stdout)["status"] == "PASS"


def test_gate_passes_from_the_installed_path(governed_project):
    result = run(governed_project, "evaluate_gate.py",
                 "--gate", "GATE-LIFECYCLE_ARCHITECTURE", "--json")
    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout)["status"] == "PASS"


def test_gate_aborts_with_exit_1_when_the_graph_is_broken(governed_project):
    """This is the contract Stage 3's workflow shell step depends on."""
    import yaml

    path = governed_project / ".specify/risks/risk-register.yaml"
    document = yaml.safe_load(path.read_text())
    document["risks"][0]["mitigation"] = []
    path.write_text(yaml.safe_dump(document, sort_keys=False))

    result = run(governed_project, "evaluate_gate.py",
                 "--gate", "GATE-LIFECYCLE_ARCHITECTURE", "--json")
    assert result.returncode == 1, "a failing gate must exit 1 so a shell step can branch on it"
    verdict = json.loads(result.stdout)
    assert verdict["status"] == "FAIL"
    assert any(c["id"] == "all_high_risks_have_mitigation" and c["status"] == "FAIL"
               for c in verdict["checks"])


def test_stdout_is_parseable_json_even_on_failure(governed_project):
    """A shell step pipes stdout through from_json; diagnostics must not pollute it."""
    (governed_project / ".specify/evidence/security-review.json").unlink()
    result = run(governed_project, "evaluate_gate.py",
                 "--gate", "GATE-LIFECYCLE_ARCHITECTURE", "--json")
    assert result.returncode == 1
    json.loads(result.stdout)  # raises if anything else was written to stdout


def test_missing_project_exits_2_not_1(governed_project):
    """Exit 2 distinguishes 'could not evaluate' from 'evaluated and failed'. A workflow
    must not treat a broken setup as a governance failure."""
    result = run(governed_project, "evaluate_gate.py",
                 "--root", "/nonexistent", "--gate", "GATE-LIFECYCLE_ARCHITECTURE", "--json")
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "ERROR"


def test_freshly_initialized_project_fails_its_gate(empty_project):
    """An empty plan is not a valid plan — init must not produce a passing gate."""
    run(empty_project, "init_openup.py", "--program", "Test Program", "--json")
    result = run(empty_project, "evaluate_gate.py",
                 "--gate", "GATE-LIFECYCLE_OBJECTIVES", "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "FAIL"
