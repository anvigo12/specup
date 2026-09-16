#!/usr/bin/env python3
"""Validate the progressive-context hierarchy: AGENTS.md, index.md, SKILL.md.

specup.md s56-s57 argues this approach scales because an agent navigates
`directory -> AGENTS.md -> index.md -> the one artifact it needs` instead of loading the
repository. That argument is only as good as the hierarchy being there and being true, and
neither was checked.

The check that earns its place is CTX-002. A stale `index.md` pointing at a requirement that
no longer exists is worse than a missing one: it is a context map that actively misleads the
agent reading it, which is the failure mode the whole progressive-disclosure design is meant
to avoid.

    validate_context.py --json

Exit 0 if the hierarchy is present and its references resolve, 1 if not, 2 if the graph will
not load.
"""

from __future__ import annotations

import re
import sys
from typing import Any

from openup_model import Verdict, base_parser, load_graph, record, record_warning, run

# Directories that must carry an index.md: the governance tree, plus each feature spec.
GOVERNED_DIRECTORIES = (
    ".specify/lifecycle", ".specify/wbs", ".specify/risks",
    ".specify/traceability", ".specify/governance", ".specify/evidence",
)

# An id-shaped token in prose. Deliberately loose: anything that LOOKS like a governed id in a
# context map is something a reader will try to follow, so it is something that must resolve.
ID_TOKEN = re.compile(
    r"\b(?:BUS-OBJ|REQ|NON-FR|FEAT|USR-STR|FLOW|AC|SCEN|WBS|RISK|TRACE|ADR|SECURE|TC|UNIT|"
    r"INTG|CONTRACT|MICROCKS-TEST|EVID|ITER|GATE)-[A-Z0-9.\-]+\b"
)

# Referenced in prose but not resolvable as artifacts, and not meant to be.
NOT_ARTIFACTS = re.compile(r"^(?:GATE-|TRACE-)")

# Why the severities split the way they do: a missing map is a gap in ergonomics; a map that
# misleads is a defect.
#
# CTX-001 and CTX-003 warn. An existing project adopting SpecUP should not fail its first audit
# over absent documentation, and no claim about evidence depends on either.
#
# CTX-002 and CTX-004 fail. A reference that does not resolve is not a gap — it sends an agent
# looking for something that is not there, and an agent willing to infer will fill the hole
# itself. That is the s51 failure the whole model exists to prevent.


def _feature_directories(graph) -> list[str]:
    return sorted(
        graph._rel(path) for path in (graph.root / "specs").glob("*")
        if path.is_dir()
    ) if (graph.root / "specs").is_dir() else []


def validate(args: Any) -> Verdict:
    graph, _ = load_graph(args.root)
    verdict = Verdict("validate-context")

    # CTX-001 — every governed directory has a context map
    expected = [d for d in GOVERNED_DIRECTORIES if (graph.root / d).is_dir()]
    expected += _feature_directories(graph)
    missing = [f"{directory}/index.md is missing — an agent navigating here has no map"
               for directory in expected if not (graph.root / directory / "index.md").is_file()]
    record_warning(verdict, "CTX-001", missing,
                   f"all {len(expected)} governed directory(s) carry an index.md")

    # CTX-002 — every id an index.md names actually resolves
    #
    # The one with real value. A map pointing at a deleted requirement does not merely fail to
    # help; it sends the agent looking for something that is not there, and an agent that is
    # willing to infer will fill the gap itself.
    dangling: list[str] = []
    indexes = sorted(graph.root.glob("**/index.md"))
    for path in indexes:
        rel = graph._rel(path)
        if rel.startswith(".git/"):
            continue
        for identifier in sorted(set(ID_TOKEN.findall(path.read_text()))):
            if NOT_ARTIFACTS.match(identifier):
                continue
            if not graph.exists(identifier):
                dangling.append(f"{rel}: names {identifier}, which resolves to nothing")
    record(verdict, "CTX-002", dangling,
           f"every identifier in {len(indexes)} index.md file(s) resolves in the graph")

    # CTX-003 — an AGENTS.md is reachable above every governed directory
    #
    # "Reachable" means at that directory or any ancestor up to the root, which is how an agent
    # is told to look for the nearest one (s7).
    unreachable = []
    for directory in expected:
        parts = directory.split("/")
        if not any((graph.root.joinpath(*parts[:depth]) / "AGENTS.md").is_file()
                   for depth in range(len(parts), -1, -1)):
            unreachable.append(f"{directory}/ has no AGENTS.md at or above it")
    record_warning(verdict, "CTX-003", unreachable,
                   "every governed directory has an operating contract above it")

    # CTX-004 — a skill a WBS node names must exist
    missing_skills = []
    for node_id, node in sorted(graph.wbs.items()):
        for skill in node.get("skills", []) or []:
            if not (graph.root / "skills" / skill / "SKILL.md").is_file():
                missing_skills.append(f"{node_id}: names skill '{skill}', "
                                      f"but skills/{skill}/SKILL.md does not exist")
    record(verdict, "CTX-004", missing_skills, "every skill a WBS node names exists")

    skills = sorted(p.parent.name for p in graph.root.glob("skills/*/SKILL.md"))
    verdict.metrics = {
        "governed_directories": len(expected),
        "index_files": len(indexes),
        "skills": skills,
        "dangling_references": len(dangling),
    }
    return verdict


if __name__ == "__main__":
    sys.exit(run(validate, base_parser(__doc__.splitlines()[0])))
