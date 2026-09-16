"""Shared core for the SpecUP validators.

Loads the governed graph from the filesystem, indexes it, and provides the verdict
types every validator emits. ID patterns and the relation vocabulary are read out of
the JSON Schemas rather than restated here, so ID-GRAMMAR.md and the schemas stay the
single source of truth (specup.md s4: the filesystem is the authority).

Every validator built on this module obeys the same CLI contract:

    stdout   a JSON verdict (with --json) or a human-readable report
    exit 0   PASS
    exit 1   FAIL - a governance invariant was violated
    exit 2   ERROR - the graph could not be loaded or parsed

The dual contract is what lets one script serve both an AI agent (which reads the
JSON) and a workflow ``shell`` step (which branches on the exit code).
"""

from __future__ import annotations

import argparse
import fnmatch
import glob
import hashlib
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

SCHEMA_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "schemas"

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"

# $defs keys whose derived name does not match the artifactType enum.
_TYPE_OVERRIDES = {"wbs": "wbs-node", "adr": "architecture-decision"}


class GraphError(Exception):
    """The graph could not be loaded. Maps to exit code 2, never to a FAIL verdict —
    a missing file is an operator error, not a governance violation."""


# --------------------------------------------------------------------------
# Verdicts
# --------------------------------------------------------------------------


@dataclass
class Check:
    id: str
    status: str
    message: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "message": self.message,
            "evidence": self.evidence,
        }


@dataclass
class Verdict:
    validator: str
    checks: list[Check] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def add(self, check_id: str, status: str, message: str, evidence: Iterable[str] = ()) -> None:
        self.checks.append(Check(check_id, status, message, sorted(set(evidence))))

    def ok(self, check_id: str, message: str) -> None:
        self.add(check_id, PASS, message)

    def fail(self, check_id: str, message: str, evidence: Iterable[str] = ()) -> None:
        self.add(check_id, FAIL, message, evidence)

    def warn(self, check_id: str, message: str, evidence: Iterable[str] = ()) -> None:
        self.add(check_id, WARN, message, evidence)

    @property
    def status(self) -> str:
        return FAIL if any(c.status == FAIL for c in self.checks) else PASS

    @property
    def exit_code(self) -> int:
        return 1 if self.status == FAIL else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator": self.validator,
            "status": self.status,
            "checks": [c.to_dict() for c in self.checks],
            "metrics": self.metrics,
        }

    def render(self) -> str:
        lines = [f"{self.validator}: {self.status}", "=" * (len(self.validator) + len(self.status) + 2)]
        for check in self.checks:
            if check.status == PASS:
                continue
            lines.append(f"  [{check.status}] {check.id}  {check.message}")
            lines.extend(f"           - {item}" for item in check.evidence[:10])
            if len(check.evidence) > 10:
                lines.append(f"           ... {len(check.evidence) - 10} more")
        if self.metrics:
            lines.append("")
            lines.extend(f"  {k}: {v}" for k, v in self.metrics.items())
        passed = sum(1 for c in self.checks if c.status == PASS)
        lines.append(f"\n  {passed}/{len(self.checks)} checks passed")
        return "\n".join(lines)


def record(verdict: Verdict, check_id: str, failures: list[str], ok_message: str) -> None:
    """Record one check: FAIL listing every violation, or PASS with the reason it held.

    The shape every validator wants. It lived as an identical private copy in four of them
    until a fifth was needed; a helper duplicated once is a convenience, duplicated five times
    it is four places for the failure message to drift apart.

    Does NOT decide severity. A check that should warn rather than fail calls `record_warning`,
    and the choice between them is a governance decision made per check id, never a default.
    """
    if failures:
        verdict.fail(check_id, f"{len(failures)} violation(s)", failures)
    else:
        verdict.ok(check_id, ok_message)


def record_warning(verdict: Verdict, check_id: str, problems: list[str], ok_message: str) -> None:
    """Record one check as a WARN rather than a FAIL, so it never changes the exit code.

    The governing principle, from the operating manual: **a missing thing warns; a misleading
    thing fails.** A gap someone has not filled in yet should not stop an existing project's
    first audit; a statement that actively misleads an agent must.

    Use this only where that argument holds and is written down next to the check. A warning
    chosen to keep a run green is the defect the gates exist to reject.
    """
    if problems:
        verdict.warn(check_id, f"{len(problems)} gap(s)", problems)
    else:
        verdict.ok(check_id, ok_message)


def write_out(path: str | None, payload: dict[str, Any]) -> None:
    """Persist a verdict to disk as durable evidence.

    A workflow cannot capture stdout with `tee` without destroying the exit code the
    pipeline depends on, so writing the file is the validator's job, not the shell's.
    """
    if not path:
        return
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n")


def emit(verdict: Verdict, as_json: bool, out: str | None = None) -> int:
    """Print a verdict in the requested form and return the process exit code."""
    payload = verdict.to_dict()
    write_out(out, payload)
    print(json.dumps(payload, indent=2) if as_json else verdict.render())
    return verdict.exit_code


def base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--root", default=".", help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit a JSON verdict on stdout")
    parser.add_argument("--out", default=None, metavar="PATH",
                        help="also write the JSON verdict here, as durable evidence")
    return parser


def run(main_fn, parser: argparse.ArgumentParser) -> int:
    """Wrap a validator main so load failures become exit 2, not a misleading FAIL."""
    args = parser.parse_args()
    try:
        verdict = main_fn(args)
    except GraphError as exc:
        payload = {"validator": parser.prog, "status": "ERROR", "error": str(exc)}
        write_out(getattr(args, "out", None), payload)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return emit(verdict, args.json, getattr(args, "out", None))


# --------------------------------------------------------------------------
# Grammar, loaded from the schemas
# --------------------------------------------------------------------------


def _camel_to_kebab(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


class Grammar:
    """ID patterns and the relation vocabulary, read from artifact.schema.json."""

    def __init__(self, schema_dir: pathlib.Path = SCHEMA_DIR):
        try:
            schema = json.loads((schema_dir / "artifact.schema.json").read_text())
        except OSError as exc:
            raise GraphError(f"cannot read artifact.schema.json: {exc}") from exc
        defs = schema["$defs"]

        self.patterns: dict[str, re.Pattern[str]] = {}
        for key, body in defs.items():
            if not key.endswith("Id") or "pattern" not in body:
                continue
            stem = _camel_to_kebab(key[:-2])
            self.patterns[_TYPE_OVERRIDES.get(stem, stem)] = re.compile(body["pattern"])

        self.relations: list[str] = defs["relation"]["enum"]
        self.states: list[str] = defs["governanceState"]["enum"]
        self.provenance: list[str] = defs["provenance"]["enum"]
        self.phases: list[str] = defs["phase"]["enum"]
        self._source_path = re.compile(defs["sourcePath"]["pattern"])

    def type_of(self, identifier: str) -> str | None:
        """Return the artifact type for an id, or 'source-artifact' for a path."""
        for artifact_type, pattern in self.patterns.items():
            if pattern.match(identifier):
                return artifact_type
        if "/" in identifier or "." in identifier:
            if self._source_path.match(identifier):
                return "source-artifact"
        return None

    def is_requirement(self, identifier: str) -> bool:
        return self.type_of(identifier) in {"requirement", "non-functional-requirement"}


# Inverse relations. Stored edges are active voice; inverses are derived at load time
# and never written to disk (ID-GRAMMAR.md s2).
INVERSE = {
    "refines": "refined-by",
    "contains": "contained-by",
    "implements": "implemented-by",
    "verifies": "verified-by",
    "executes": "executed-by",
    "tests": "tested-by",
    "conforms-to": "conformed-by",
    "validates": "validated-by",
    "mitigates": "mitigated-by",
    "evidences": "evidenced-by",
    "depends-on": "depended-on-by",
    "belongs-to": "owns",
    "approves": "approved-by",
    "supersedes": "superseded-by",
}

# Relations that must not contain a cycle.
ACYCLIC = ("contains", "refines", "depends-on", "supersedes")


# --------------------------------------------------------------------------
# WBS id helpers
# --------------------------------------------------------------------------


def wbs_segments(wbs_id: str) -> list[str]:
    return wbs_id[len("WBS-"):].split(".")


def wbs_level(wbs_id: str) -> int:
    """The level IS the segment count — the id encodes its own position (s15)."""
    return len(wbs_segments(wbs_id))


def wbs_parent_id(wbs_id: str) -> str | None:
    segments = wbs_segments(wbs_id)
    return f"WBS-{'.'.join(segments[:-1])}" if len(segments) > 1 else None


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

# Never inside the traceability perimeter, whatever the config says. These are the governance
# layer (s7, s9), not implementation: an AGENTS.md seeded into a source tree is not a file that
# needs an edge to a requirement. This is hard-coded rather than a config default because an
# exclude list REPLACES rather than merges, so a project carrying its own list would start
# failing backward coverage the moment it adopted the context hierarchy — a check punishing
# the very thing another part of the design asks for.
GOVERNANCE_FILES = ("AGENTS.md", "index.md", "SKILL.md")

DEFAULT_CONFIG: dict[str, Any] = {
    "lifecycle": {"phase": "INCEPTION", "iteration": None},
    "wbs": {"depth_policy": "semantic", "never_terminal_above": 3, "max_children_warn": 25,
            "store": ".specify/wbs/wbs.yaml"},
    "risk": {"high_exposure_threshold": 0.40, "critical_exposure_threshold": 0.65,
             "require_residual_reduction": True, "store": ".specify/risks/risk-register.yaml"},
    "artifacts": {"stores": [".specify/traceability/requirements.yaml", "specs/*/artifacts.yaml"]},
    "traceability": {
        "stores": [".specify/traceability/traceability.yaml", "specs/*/traceability/matrix.yaml",
                   ".specify/traceability/derived.yaml"],
        "perimeter": {"include": ["src/**"], "exclude": []},
        "coverage_thresholds": {"forward": 1.00, "backward": 0.95},
        "baseline_min_provenance": "approved",
    },
    "gherkin": {"features_glob": "specs/*/acceptance/**/*.feature",
                "require_ac_tag": True, "require_requirement_tag": True,
                "require_scenario_per_ac": True},
    "testing": {"stem_suffixes": [".test", ".spec", "_test", "_spec", "-test", "Test"],
                "stem_prefixes": ["test_", "test-"]},
    "gates": {},
    "audit": {"fail_on": []},
}


def _deep_merge(base: dict, overlay: dict) -> dict:
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(root: pathlib.Path) -> dict[str, Any]:
    """Merge defaults < openup-config.yml < openup-config.local.yml."""
    config = DEFAULT_CONFIG
    for name in ("openup-config.yml", "openup-config.local.yml"):
        for candidate in (
            root / ".specify" / "extensions" / "openup" / name,
            root / "extensions" / "openup" / name,
        ):
            if candidate.is_file():
                loaded = yaml.safe_load(candidate.read_text()) or {}
                config = _deep_merge(config, loaded)
                break
    return config


# --------------------------------------------------------------------------
# Graph
# --------------------------------------------------------------------------


@dataclass
class Edge:
    """One stored relation.

    Every field the schema allows is carried here. That is not tidiness: a loader that
    drops fields is a projection, and validating a projection against the schema checks
    a document nobody wrote (which is exactly how `approved` became unusable — the schema
    demanded the fields the loader had just discarded).
    """

    from_id: str
    relation: str
    to_id: str
    provenance: str
    status: str = "active"
    source_file: str | None = None
    evidence: list[str] = field(default_factory=list)
    derived_by: str | None = None
    edge_id: str | None = None
    approval: dict[str, Any] | None = None
    approved_endpoints_hash: str | None = None
    note: str | None = None

    @property
    def triple(self) -> tuple[str, str, str]:
        return (self.from_id, self.relation, self.to_id)

    def __str__(self) -> str:
        return f"{self.from_id} --{self.relation}--> {self.to_id}"


def _load_yaml(path: pathlib.Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise GraphError(f"{path}: invalid YAML: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise GraphError(f"{path}: expected a mapping at the top level")
    return data


def expand_paths(root: pathlib.Path, patterns: Iterable[str]) -> Iterator[pathlib.Path]:
    for pattern in patterns:
        if any(ch in pattern for ch in "*?["):
            for match in sorted(glob.glob(str(root / pattern), recursive=True)):
                path = pathlib.Path(match)
                if path.is_file():
                    yield path
        else:
            path = root / pattern
            if path.is_file():
                yield path


class Graph:
    """The governed graph, loaded from the filesystem and indexed for traversal."""

    def __init__(self, root: pathlib.Path, config: dict[str, Any], grammar: Grammar):
        self.root = root
        self.config = config
        self.grammar = grammar

        self.wbs: dict[str, dict] = {}
        self.risks: dict[str, dict] = {}
        self.artifacts: dict[str, dict] = {}
        self.edges: list[Edge] = []
        self.duplicate_edges: list[Edge] = []
        self.wbs_doc: dict[str, Any] = {}
        self.loaded_files: list[str] = []
        # Relative path -> the traceability document exactly as parsed. Schema checks run
        # against these, never against anything rebuilt from the Edge objects.
        self.raw_stores: dict[str, dict] = {}

        self._load_wbs()
        self._load_risks()
        self._load_artifacts()
        self._load_edges()
        self._index()

    # -- loading ----------------------------------------------------------

    def _rel(self, path: pathlib.Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def _register(self, store: dict[str, dict], declared_in: dict[str, str],
                  identifier: str | None, item: dict, kind: str, rel: str) -> None:
        """Add one item to a store, refusing a missing or duplicated id.

        Both refusals are GraphError — exit 2, "cannot evaluate" — rather than a FAIL check,
        and deliberately so. A store declaring `REQ-AUTH-0014` twice does not describe a graph
        that violates a policy; it describes no graph at all, because every downstream check
        would be computing over whichever of the two happened to load last. Reporting that as
        a governance failure would claim the graph was read and found wanting, when the truth
        is that the loader silently discarded half of what was written.

        An id is a name, and two things cannot share one. This is the single place that holds
        for all three stores: the WBS enforced it from the start while artifacts and risks
        overwrote in silence, which meant the most-edited store in the system was the one
        where a collision cost you a requirement and said nothing.
        """
        if not identifier:
            # Name the entry by whatever it does carry. The commonest cause is a typo'd `id:`
            # key, and "one of your 200 artifacts has no id" is not a finding anyone can act on.
            hint = item.get("title") or item.get("name")
            raise GraphError(f"{rel}: {kind} with no id" + (f" ({hint!r})" if hint else ""))
        if identifier in store:
            first = declared_in[identifier]
            where = f"already declared in {first}" if first != rel else "declared twice here"
            raise GraphError(
                f"{rel}: duplicate {kind} {identifier} — {where}. An id names exactly one "
                f"artifact for its whole life; supersede it, never reuse it."
            )
        declared_in[identifier] = rel
        store[identifier] = item

    def _load_wbs(self) -> None:
        path = self.root / self.config["wbs"].get("store", ".specify/wbs/wbs.yaml")
        if not path.is_file():
            return
        self.wbs_doc = _load_yaml(path)
        rel = self._rel(path)
        self.loaded_files.append(rel)
        declared_in: dict[str, str] = {}
        for node in self.wbs_doc.get("nodes", []) or []:
            self._register(self.wbs, declared_in, node.get("id"), node, "WBS node", rel)

    def _load_risks(self) -> None:
        path = self.root / self.config["risk"].get("store", ".specify/risks/risk-register.yaml")
        if not path.is_file():
            return
        rel = self._rel(path)
        self.loaded_files.append(rel)
        declared_in: dict[str, str] = {}
        for risk in _load_yaml(path).get("risks", []) or []:
            self._register(self.risks, declared_in, risk.get("id"), risk, "risk", rel)

    def _load_artifacts(self) -> None:
        # Artifacts are the only store that spans several files — specs/*/artifacts.yaml all
        # merge into the same graph — so this map lives outside the loop. Two features
        # independently reaching for REQ-AUTH-0001 is the natural collision here, not an
        # exotic one, and an error naming only the second file leaves the reader hunting for
        # the first.
        declared_in: dict[str, str] = {}
        for path in expand_paths(self.root, self.config["artifacts"]["stores"]):
            rel = self._rel(path)
            self.loaded_files.append(rel)
            doc = _load_yaml(path)
            for artifact in doc.get("artifacts", []) or []:
                artifact.setdefault("source", rel)
                self._register(self.artifacts, declared_in, artifact.get("id"), artifact,
                               "artifact", rel)

    def _load_edges(self) -> None:
        seen: dict[tuple[str, str, str], Edge] = {}
        for path in expand_paths(self.root, self.config["traceability"]["stores"]):
            rel = self._rel(path)
            self.loaded_files.append(rel)
            doc = _load_yaml(path)
            self.raw_stores[rel] = doc
            for raw in doc.get("edges", []) or []:
                edge = Edge(
                    from_id=raw.get("from", ""),
                    relation=raw.get("relation", ""),
                    to_id=raw.get("to", ""),
                    provenance=raw.get("provenance", "asserted"),
                    status=raw.get("status", "active"),
                    source_file=raw.get("source_file") or rel,
                    evidence=list(raw.get("evidence", []) or []),
                    derived_by=raw.get("derived_by"),
                    edge_id=raw.get("id"),
                    approval=raw.get("approval"),
                    approved_endpoints_hash=raw.get("approved_endpoints_hash"),
                    note=raw.get("note"),
                )
                if edge.triple in seen:
                    self.duplicate_edges.append(edge)
                    continue
                seen[edge.triple] = edge
                self.edges.append(edge)

    def _index(self) -> None:
        self.out: dict[str, list[Edge]] = {}
        self.inc: dict[str, list[Edge]] = {}
        for edge in self.edges:
            self.out.setdefault(edge.from_id, []).append(edge)
            self.inc.setdefault(edge.to_id, []).append(edge)

        self.children: dict[str, list[str]] = {}
        for node_id in self.wbs:
            parent = wbs_parent_id(node_id)
            if parent:
                self.children.setdefault(parent, []).append(node_id)

    # -- queries ----------------------------------------------------------

    def is_leaf(self, wbs_id: str) -> bool:
        return not self.children.get(wbs_id)

    def requirements(self) -> dict[str, dict]:
        return {
            aid: art
            for aid, art in self.artifacts.items()
            if self.grammar.is_requirement(aid)
        }

    def exists(self, identifier: str) -> bool:
        """An id resolves if it is a known artifact, WBS node, risk, or an on-disk file."""
        if identifier in self.artifacts or identifier in self.wbs or identifier in self.risks:
            return True
        if self.grammar.type_of(identifier) == "source-artifact":
            return (self.root / identifier).exists()
        return False

    def follow(self, start: str, relation: str, reverse: bool = False) -> list[str]:
        index = self.inc if reverse else self.out
        return [
            (e.from_id if reverse else e.to_id)
            for e in index.get(start, [])
            if e.relation == relation and e.status != "broken"
        ]

    def reaches(self, start: str, relations: tuple[str, ...], reverse: bool = False) -> set[str]:
        """Transitive closure over the given relations, cycle-safe."""
        seen: set[str] = set()
        stack = [start]
        index = self.inc if reverse else self.out
        while stack:
            current = stack.pop()
            for edge in index.get(current, []):
                if edge.relation not in relations or edge.status == "broken":
                    continue
                nxt = edge.from_id if reverse else edge.to_id
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    def in_perimeter(self, path: str) -> bool:
        if path.rsplit("/", 1)[-1] in GOVERNANCE_FILES:
            return False
        perimeter = self.config["traceability"]["perimeter"]
        included = any(fnmatch.fnmatch(path, pat) for pat in perimeter.get("include", []))
        excluded = any(fnmatch.fnmatch(path, pat) for pat in perimeter.get("exclude", []))
        return included and not excluded

    def perimeter_files(self) -> list[str]:
        """Every tracked file inside the traceability perimeter (s54, scoped by config)."""
        found: list[str] = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            rel = self._rel(path).replace("\\", "/")
            if rel.startswith(".git/"):
                continue
            if self.in_perimeter(rel):
                found.append(rel)
        return sorted(found)

    def find_cycle(self, relation: str) -> list[str] | None:
        """Return one cycle over `relation`, or None. Iterative, so deep graphs are safe."""
        colour: dict[str, int] = {}
        for start in list(self.out):
            if colour.get(start):
                continue
            stack: list[tuple[str, list[str]]] = [(start, [start])]
            while stack:
                node, path = stack.pop()
                state = colour.get(node, 0)
                if state == 2:
                    continue
                if state == 0:
                    colour[node] = 1
                    stack.append((node, path))  # revisit to mark black
                    for nxt in self.follow(node, relation):
                        if colour.get(nxt) == 1:
                            return path[path.index(nxt):] + [nxt] if nxt in path else [nxt, node, nxt]
                        if colour.get(nxt, 0) == 0:
                            stack.append((nxt, path + [nxt]))
                else:
                    colour[node] = 2
        return None


# --------------------------------------------------------------------------
# Approval binding
# --------------------------------------------------------------------------

# Lifecycle bookkeeping, excluded from the fingerprint. An approval is about WHAT was
# approved, not where the artifact currently sits in s31's state machine: advancing
# APPROVED -> BASELINED must not void a signature, but editing the requirement must.
LIFECYCLE_KEYS = {"status", "approvals", "baseline"}


def endpoint_fingerprint(graph: "Graph", identifier: str) -> str:
    """Canonical text for one endpoint of an approved edge.

    A source path fingerprints as the path itself, not as the bytes at that path. An
    approved edge to a file records *which file was approved for this role*; source churn
    is continuous and expected, and hashing content would void every approval on every
    commit until nobody used approvals at all. Whether the file is still correct is what
    tests and TRC-010 derivation are for. (ID-GRAMMAR.md s3 states this externally, because
    the two behaviours are indistinguishable from outside.)
    """
    for store in (graph.artifacts, graph.wbs, graph.risks):
        if identifier in store:
            body = {k: v for k, v in store[identifier].items() if k not in LIFECYCLE_KEYS}
            return json.dumps(body, sort_keys=True, separators=(",", ":"))
    return identifier


def approval_hash(graph: "Graph", edge: Edge) -> str:
    """SHA256 binding an approval to the exact content it was given for.

    The relation is inside the hash deliberately: re-pointing an approved edge at a
    different relation must void the approval, not inherit it.
    """
    payload = "\x00".join((
        endpoint_fingerprint(graph, edge.from_id),
        edge.relation,
        endpoint_fingerprint(graph, edge.to_id),
    ))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def schema_errors(instance: Any, schema_name: str, schema_dir: pathlib.Path = SCHEMA_DIR) -> list[str]:
    """Validate an instance against one of the SpecUP schemas.

    Cross-file ``$ref``s are resolved by registering every schema in the directory under
    both its ``$id`` and its bare filename, which is the form the relative refs use.
    """
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError as exc:  # pragma: no cover
        raise GraphError(f"jsonschema and referencing are required: {exc}") from exc

    resources = {}
    for path in schema_dir.glob("*.json"):
        doc = json.loads(path.read_text())
        resource = Resource.from_contents(doc)
        resources[doc["$id"]] = resource
        resources[path.name] = resource

    registry = Registry().with_resources(resources.items())
    schema = json.loads((schema_dir / schema_name).read_text())
    validator = Draft202012Validator(schema, registry=registry)

    messages = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        location = "/".join(str(p) for p in error.path) or "<root>"
        messages.append(f"{location}: {error.message}")
    return messages


def load_graph(root_arg: str) -> tuple[Graph, dict[str, Any]]:
    root = pathlib.Path(root_arg).resolve()
    if not root.is_dir():
        raise GraphError(f"project root does not exist: {root}")
    config = load_config(root)
    graph = Graph(root, config, Grammar())
    return graph, config
