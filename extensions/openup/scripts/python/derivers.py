"""Recompute `derived` traceability edges from the filesystem.

A `provenance: derived` edge claims a named rule recovered it mechanically, and the audit
counts it as machine-checkable on that basis. Until this module existed nothing checked the
claim: traceability.schema.json requires `derived_by` to be *present*, never that it be
*true*, so any judgement call could be relabelled `derived` and the provenance mix — the one
signal separating evidence from assertion (ID-GRAMMAR.md s3) — would report it as evidence.
That is the exact circularity the provenance model exists to expose, reappearing one level up.

So the rules are implemented here and the graph is checked against them:

    TRC-010  every derived edge an implemented rule does not reproduce is a false claim
    TRC-011  every edge an implemented rule produces must be in the store
    TRC-012  every acceptance criterion has at least one scenario (specup.md s24)

Three of the six rules named in speckit.openup.trace.md are implemented. The other three are
listed in KNOWN_RULES and reported as *unverified* rather than quietly trusted — an
unimplemented rule is a gap in the evidence, and the audit says so instead of rounding it up.
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from openup_model import expand_paths

Triple = tuple[str, str, str]

# Test artifact types that may sit at the `from` end of a `tests` edge.
TEST_TYPES = {"test-case", "unit-test", "integration-test", "e2e-test"}


@dataclass
class Derivation:
    """What one rule recovered, and what it could not."""

    rule: str
    triples: set[Triple] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# gherkin-tag-scan
# --------------------------------------------------------------------------

_TAG = re.compile(r"@([A-Za-z0-9_.\-]+)")

# Gherkin keywords that open a scenario. `Examples`/`Scenarios` open the data table of a
# Scenario Outline and are deliberately absent — matching them would invent a scenario per
# outline. English only; a localised feature file derives nothing and says so.
_SCENARIO_KEYWORDS = {"Scenario", "Scenario Outline", "Scenario Template", "Example"}
_TAG_RESET_KEYWORDS = {"Background", "Examples", "Scenarios"}


def parse_feature(text: str) -> list[tuple[str, list[str], int]]:
    """Return [(scenario name, effective tags, line number)] for one feature file.

    Gherkin tag inheritance is positional: tags above `Feature:` apply to every scenario in
    the file, tags above `Rule:` to every scenario under that rule, and tags above a scenario
    to that scenario alone. Docstring bodies are skipped so a ``@`` inside prose cannot be
    read as a tag.
    """
    feature_tags: list[str] = []
    rule_tags: list[str] = []
    pending: list[str] = []
    scenarios: list[tuple[str, list[str], int]] = []
    delimiter = ""

    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()

        if delimiter:
            if line.startswith(delimiter):
                delimiter = ""
            continue
        if line.startswith('"""') or line.startswith("'''"):
            delimiter = line[:3]
            continue
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            pending.extend(_TAG.findall(line))
            continue

        if ":" not in line:
            continue
        keyword, remainder = (part.strip() for part in line.split(":", 1))

        if keyword == "Feature":
            feature_tags, rule_tags, pending = pending, [], []
        elif keyword == "Rule":
            rule_tags, pending = pending, []
        elif keyword in _SCENARIO_KEYWORDS:
            scenarios.append((remainder, feature_tags + rule_tags + pending, number))
            pending = []
        elif keyword in _TAG_RESET_KEYWORDS:
            pending = []

    return scenarios


def derive_gherkin_tags(graph: Any) -> Derivation:
    """`SCEN-*` --executes--> `AC-*`, from the @tags on each scenario.

    The scenario's own `@SCEN-<DOMAIN>-nnnn` tag is its identity in the graph. Requiring it
    explicitly rather than inferring one from the file name is what keeps this a derivation:
    an inferred id would make the edge depend on a guess, which is an assertion.
    """
    out = Derivation("gherkin-tag-scan")
    config = graph.config.get("gherkin", {})
    grammar = graph.grammar
    pattern = config.get("features_glob")
    if not pattern:
        out.notes.append("gherkin.features_glob is not set; no feature files were scanned")
        return out

    for path in expand_paths(graph.root, [pattern]):
        relative = str(path.relative_to(graph.root)).replace("\\", "/")
        try:
            scenarios = parse_feature(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            out.notes.append(f"{relative}: cannot read ({exc})")
            continue
        if not scenarios:
            out.notes.append(f"{relative}: no scenarios found")
            continue

        for name, tags, number in scenarios:
            where = f"{relative}:{number} ({name})"
            identities = [t for t in tags if grammar.type_of(t) == "scenario"]
            criteria = [t for t in tags if grammar.type_of(t) == "acceptance-criterion"]
            requirements = [t for t in tags if grammar.is_requirement(t)]

            if len(identities) != 1:
                out.notes.append(
                    f"{where}: expected exactly one @SCEN-<DOMAIN>-nnnn tag, found "
                    f"{len(identities)}; nothing derived for this scenario"
                )
                continue
            if config.get("require_ac_tag", True) and not criteria:
                out.notes.append(f"{where}: no @AC- tag — it executes no stated criterion")
            if config.get("require_requirement_tag", True) and not requirements:
                out.notes.append(f"{where}: no @REQ-/@NON-FR- tag — it serves no stated requirement")

            for criterion in criteria:
                out.triples.add((identities[0], "executes", criterion))

    return out


def scenarios_by_criterion(graph: Any) -> dict[str, list[str]]:
    """Acceptance criterion id -> the scenario ids that execute it, from the tag scan."""
    covered: dict[str, list[str]] = {}
    for scenario, _, criterion in derive_gherkin_tags(graph).triples:
        covered.setdefault(criterion, []).append(scenario)
    return covered


# --------------------------------------------------------------------------
# test-file-naming-convention
# --------------------------------------------------------------------------


def _subject_stem(stem: str, prefixes: list[str], suffixes: list[str]) -> str | None:
    """Strip one test marker from a file stem, or return None if it carries none."""
    for suffix in suffixes:
        if stem.endswith(suffix) and len(stem) > len(suffix):
            return stem[: -len(suffix)]
    for prefix in prefixes:
        if stem.startswith(prefix) and len(stem) > len(prefix):
            return stem[len(prefix):]
    return None


def derive_test_file_naming(graph: Any) -> Derivation:
    """`UNIT-*`/`TC-*`/`INTG-*`/`E2E-*` --tests--> the source file its `source` is named after.

    The subject must match on stem *and* extension, and must be unique inside the perimeter.
    An ambiguous name derives nothing: picking one of two candidates would be a guess, and a
    guess recorded as `derived` is worse than no edge at all.

    `E2E-*` is admitted here for symmetry, and usually derives nothing: `testing.stem_suffixes`
    carries no `.e2e` marker, and an end-to-end test is named after a journey rather than after
    one source file. That is reported as a note, not a failure — an `E2E-*` artifact's `tests`
    edge is normally `asserted`, and ID-GRAMMAR.md s2 says so rather than leaving a reader to
    infer it from a silent gap.
    """
    out = Derivation("test-file-naming-convention")
    config = graph.config.get("testing", {})
    prefixes = list(config.get("stem_prefixes", []))
    suffixes = list(config.get("stem_suffixes", []))

    by_name: dict[tuple[str, str], list[str]] = {}
    for relative in graph.perimeter_files():
        candidate = pathlib.PurePosixPath(relative)
        by_name.setdefault((candidate.stem, candidate.suffix), []).append(relative)

    for artifact_id, artifact in sorted(graph.artifacts.items()):
        if graph.grammar.type_of(artifact_id) not in TEST_TYPES:
            continue
        source = artifact.get("source")
        # An artifact with no `source` of its own inherits the registry it was declared in
        # (Graph._load_artifacts). A YAML registry is not a test file, so skip it silently
        # rather than reporting a missing counterpart for every store in the project.
        if not source or source.endswith((".yaml", ".yml")):
            continue
        if not (graph.root / source).is_file():
            out.notes.append(f"{artifact_id}: declared source '{source}' does not exist")
            continue

        test_path = pathlib.PurePosixPath(source)
        stem = _subject_stem(test_path.stem, prefixes, suffixes)
        if stem is None:
            out.notes.append(
                f"{artifact_id}: '{source}' carries no configured test marker "
                f"({', '.join(suffixes + prefixes)})"
            )
            continue

        matches = by_name.get((stem, test_path.suffix), [])
        if len(matches) == 1:
            out.triples.add((artifact_id, "tests", matches[0]))
        elif not matches:
            out.notes.append(
                f"{artifact_id}: no in-perimeter file named '{stem}{test_path.suffix}' "
                f"for test file '{source}'"
            )
        else:
            out.notes.append(
                f"{artifact_id}: '{stem}{test_path.suffix}' is ambiguous inside the perimeter "
                f"({', '.join(matches)}); nothing derived"
            )

    return out


# --------------------------------------------------------------------------
# wbs-iteration-field
# --------------------------------------------------------------------------


def derive_wbs_iteration(graph: Any) -> Derivation:
    """`WBS-*` --belongs-to--> `ITER-*`, from the node's own `iteration` field.

    Pure restatement of a field already in the WBS store, which is exactly why it belongs
    here: writing the same fact twice by hand is how the two copies start to disagree.
    """
    out = Derivation("wbs-iteration-field")
    for node_id, node in sorted(graph.wbs.items()):
        iteration = node.get("iteration")
        if iteration:
            out.triples.add((node_id, "belongs-to", iteration))
    return out


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

RULES: dict[str, Callable[[Any], Derivation]] = {
    "gherkin-tag-scan": derive_gherkin_tags,
    "test-file-naming-convention": derive_test_file_naming,
    "wbs-iteration-field": derive_wbs_iteration,
}

# Named in speckit.openup.trace.md but not implemented. An edge may still declare one of
# these; TRC-010 reports it as unverified instead of accepting it as machine-checkable.
UNIMPLEMENTED_RULES: dict[str, str] = {
    "openapi-operation-scan": "source file --conforms-to--> CONTRACT-*",
    "evidence-manifest-scan": "EVID-* --evidences--> WBS node / risk / gate",
}

KNOWN_RULES = frozenset(RULES) | frozenset(UNIMPLEMENTED_RULES)


def derive_all(graph: Any) -> dict[str, Derivation]:
    """Run every implemented rule against the graph."""
    return {name: rule(graph) for name, rule in RULES.items()}


def triples_by_rule(derivations: dict[str, Derivation]) -> dict[Triple, str]:
    """Flatten derivations to triple -> the rule that produced it."""
    return {triple: name for name, derivation in derivations.items() for triple in derivation.triples}
