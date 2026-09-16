"""Keep the task runner above the enforcement boundary.

The Taskfile is for developing, testing, packaging and publishing SpecUP. Nothing
SpecUP *runs* may go through it, and this file is what makes that a rule rather
than an intention.

The reason is governance, not tooling preference. Validators live under
`.specify/extensions/openup/`, a directory `specify extension add` owns and
reinstalls, so tampering with one is visible and gets reverted on update. A
Taskfile sits at a project root, where editing it is an unremarkable act
that leaves no trace anywhere Spec Kit looks. If a gate were evaluated through
`task gate`, redefining that task as `exit 0` would be a clean, reviewable-looking
way to turn a failing gate green — precisely what `speckit.openup.gate.md`
forbids, and the bypass would be indistinguishable from ordinary project
maintenance.

It also preserves a property the README states plainly: the path an agent runs and
the path a workflow runs are the same string. An indirection layer reintroduces
the second thing to keep in sync.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# go-task accepts four spellings and this repository has used two of them. Pinning one meant a
# rename turned these tests into skips rather than failures — the boundary stopped being
# checked and the suite still reported green, which is the failure mode this file exists to
# prevent one level up.
TASKFILE = next(
    (REPO_ROOT / name for name in ("Taskfile.yml", "Taskfile.yaml", "taskfile.yml",
                                   "taskfile.yaml")
     if (REPO_ROOT / name).is_file()),
    REPO_ROOT / "Taskfile.yml",
)
WORKFLOW_PATHS = sorted((REPO_ROOT / "workflows").glob("*/workflow.yml"))
COMMAND_PATHS = sorted((REPO_ROOT / "extensions" / "openup" / "commands").glob("*.md"))
PRESET_PATHS = sorted((REPO_ROOT / "presets").glob("*/**/*.md"))

# `task`/`go-task` as a command word: at the start, or after a pipe, &&, ||, ; or (.
TASK_INVOCATION = re.compile(r"(?:^|[|;&(]|&&|\|\|)\s*(?:go-)?task\s", re.MULTILINE)


def walk_steps(steps):
    for step in steps or []:
        yield step
        for key in ("then", "else", "steps"):
            yield from walk_steps(step.get(key))
        for case in (step.get("cases") or []):
            yield from walk_steps(case.get("steps"))


@pytest.mark.skipif(not TASKFILE.is_file(), reason="no Taskfile at the repo root")
def test_taskfile_is_valid_yaml_and_declares_version_3():
    data = yaml.safe_load(TASKFILE.read_text())
    assert str(data.get("version")) == "3"
    assert data.get("tasks"), "a Taskfile with no tasks is dead weight"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda p: p.parent.name)
def test_no_workflow_step_invokes_the_task_runner(path):
    """The one that matters. A gate must not be reachable through a project-editable alias."""
    for step in walk_steps((yaml.safe_load(path.read_text()) or {}).get("steps")):
        run = step.get("run")
        if not run:
            continue
        assert not TASK_INVOCATION.search(run), (
            f"{path.parent.name}/{step.get('id')}: `run:` invokes the task runner.\n"
            f"  {run.strip()[:160]}\n"
            f"Gates must call the validator directly, at a path the extension owns."
        )


@pytest.mark.parametrize("path", COMMAND_PATHS, ids=lambda p: p.name)
def test_no_extension_command_tells_the_agent_to_run_task(path):
    """Same rule for the agent-facing path: a command that says `task audit` instead of
    the validator moves the check somewhere the project can redefine it."""
    for block in re.findall(r"```(?:bash|sh|shell)\n(.*?)```", path.read_text(), re.DOTALL):
        assert not TASK_INVOCATION.search(block), (
            f"{path.name} instructs the agent to run the task runner; "
            f"it should call the validator at its installed path"
        )


@pytest.mark.parametrize("path", PRESET_PATHS, ids=lambda p: p.name)
def test_no_preset_guidance_tells_the_agent_to_run_task(path):
    for block in re.findall(r"```(?:bash|sh|shell)\n(.*?)```", path.read_text(), re.DOTALL):
        assert not TASK_INVOCATION.search(block), (
            f"{path.name} instructs the agent to run the task runner; "
            f"it should call the validator at its installed path"
        )


@pytest.mark.skipif(not TASKFILE.is_file(), reason="no Taskfile at the repo root")
def test_the_task_runner_is_never_a_shipped_dependency():
    """`task` must not appear in any manifest's `requires.tools`.

    A consumer needs python3 and three pip packages. Adding a Go binary to that set
    would make a missing `task` a failure at gate time — spec-kit surfaces
    `requires.tools` as an install-time warning, not a check.
    """
    manifests = [
        REPO_ROOT / "extensions" / "openup" / "extension.yml",
        REPO_ROOT / "presets" / "openup-governance" / "preset.yml",
        REPO_ROOT / "bundles" / "specup" / "bundle.yml",
        *WORKFLOW_PATHS,
    ]
    for path in manifests:
        if not path.is_file():
            continue
        data = yaml.safe_load(path.read_text()) or {}
        tools = (data.get("requires") or {}).get("tools") or []
        for tool in tools:
            name = tool.get("name", "") if isinstance(tool, dict) else str(tool)
            assert not re.match(r"^(go-)?task\b", name.strip()), (
                f"{path.relative_to(REPO_ROOT)} declares the task runner as a "
                f"runtime dependency; it is a development tool only"
            )
