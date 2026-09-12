"""Shared test helpers.

Every broken fixture is the good fixture plus one deliberate mutation. Keeping a single
good fixture and mutating a copy means a change to the data model updates one file, not
twenty, and each test states exactly which invariant it is breaking.
"""

from __future__ import annotations

import pathlib
import shutil
import sys
from typing import Any, Callable

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "extensions" / "openup" / "scripts" / "python"
GOOD_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "good"

sys.path.insert(0, str(SCRIPTS))


class Project:
    """A mutable copy of the good fixture."""

    def __init__(self, root: pathlib.Path):
        self.root = root

    # -- mutation helpers -------------------------------------------------

    def edit_yaml(self, relative: str, mutate: Callable[[dict], None]) -> None:
        path = self.root / relative
        document = yaml.safe_load(path.read_text())
        mutate(document)
        path.write_text(yaml.safe_dump(document, sort_keys=False))

    def wbs(self, mutate: Callable[[dict], None]) -> None:
        self.edit_yaml(".specify/wbs/wbs.yaml", mutate)

    def risks(self, mutate: Callable[[dict], None]) -> None:
        self.edit_yaml(".specify/risks/risk-register.yaml", mutate)

    def edges(self, mutate: Callable[[dict], None]) -> None:
        self.edit_yaml(".specify/traceability/traceability.yaml", mutate)

    def artifacts(self, mutate: Callable[[dict], None]) -> None:
        self.edit_yaml(".specify/traceability/requirements.yaml", mutate)

    def config(self, mutate: Callable[[dict], None]) -> None:
        self.edit_yaml(".specify/extensions/openup/openup-config.yml", mutate)

    def node(self, node_id: str) -> Callable:
        """Return a mutator factory targeting one WBS node."""
        def apply(change: Callable[[dict], None]) -> None:
            def mutate(document: dict) -> None:
                for node in document["nodes"]:
                    if node["id"] == node_id:
                        change(node)
                        return
                raise AssertionError(f"fixture has no node {node_id}")
            self.wbs(mutate)
        return apply

    def risk(self, risk_id: str) -> Callable:
        def apply(change: Callable[[dict], None]) -> None:
            def mutate(document: dict) -> None:
                for risk in document["risks"]:
                    if risk["id"] == risk_id:
                        change(risk)
                        return
                raise AssertionError(f"fixture has no risk {risk_id}")
            self.risks(mutate)
        return apply

    def artifact(self, artifact_id: str) -> Callable:
        def apply(change: Callable[[dict], None]) -> None:
            def mutate(document: dict) -> None:
                for artifact in document["artifacts"]:
                    if artifact["id"] == artifact_id:
                        change(artifact)
                        return
                raise AssertionError(f"fixture has no artifact {artifact_id}")
            self.artifacts(mutate)
        return apply

    def drop_edges(self, **match: str) -> None:
        def mutate(document: dict) -> None:
            document["edges"] = [
                edge for edge in document["edges"]
                if not all(edge.get(k) == v for k, v in match.items())
            ]
        self.edges(mutate)

    def add_edge(self, **edge: Any) -> None:
        self.edges(lambda document: document["edges"].append(edge))

    # -- running ----------------------------------------------------------

    def run(self, module_name: str, **kwargs: Any):
        """Run a validator in-process and return its Verdict."""
        import importlib

        module = importlib.import_module(module_name)

        class Args:
            root = str(self.root)
            json = False
        for key, value in kwargs.items():
            setattr(Args, key, value)
        return module.validate(Args())

    def gate(self, gate_name: str):
        import evaluate_gate
        import validate_risk
        import validate_trace
        import validate_wbs
        from openup_model import load_graph

        class Args:
            root = str(self.root)
            json = False

        graph, config = load_graph(str(self.root))
        ctx = evaluate_gate.GateContext(
            root=graph.root, graph=graph, config=config,
            wbs=validate_wbs.validate(Args()),
            risk=validate_risk.validate(Args()),
            trace=validate_trace.validate(Args()),
        )
        return evaluate_gate.evaluate(gate_name, ctx)


@pytest.fixture
def project(tmp_path: pathlib.Path) -> Project:
    root = tmp_path / "project"
    shutil.copytree(GOOD_FIXTURE, root)
    return Project(root)


def failing(verdict) -> set[str]:
    """The ids of every FAILing check in a verdict."""
    return {check.id for check in verdict.checks if check.status == "FAIL"}


def assert_fails(verdict, check_id: str) -> None:
    ids = failing(verdict)
    assert verdict.status == "FAIL", f"expected FAIL, got {verdict.status}"
    assert check_id in ids, f"expected {check_id} to fail; failing checks were {sorted(ids) or 'none'}"
