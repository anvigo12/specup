# SpecUP — Current Gaps: Reasons and Fixes

**Status: all ten closed.** 231 tests passing (was 197), `task bundle:validate` clean.
**Baseline the audit was taken against:** `b32c902`, 197 tests passing.
**Method:** every normative claim in `specup.md` (§1–§73) checked against the code on disk.
Each gap below was reproduced, not inferred; the reproduction is kept so the defect stays
legible after the fix, and so a regression is recognisable.

Read the priority column as "what breaks if we ship without this", not as effort.

---

## Summary

| # | Gap | §  | Priority | Outcome |
|---|---|---|---|---|
| [G1](#g1--approved-provenance-is-unreachable) | `provenance: approved` cannot be used at all — two checks contradict | 31, 59 | **Blocker** | ✅ `TRC-000` validates the stores as written |
| [G2](#g2--approved_endpoints_hash-is-never-verified) | The approval hash is required but never computed or checked | 31, 55 | **Blocker** | ✅ `TRC-013` + `approve_edge.py` |
| [G3](#g3--the-task-layer-does-not-exist) | `TASK-*`, `task`, `modifies`, `decomposes-to` are declared and unused | 21, 26, 27, 44, 67 | High | ✅ Option A — WBS L7 *is* the task |
| [G4](#g4--generated-views-have-no-generator) | `wbs.md` / `risk-register.md` / `traceability.md` / `coverage.md` are hand-written by the agent | 47, 65 | High | ✅ `render_views.py` |
| [G5](#g5--definition-of-done-is-not-computed) | DoR is machine-checked, DoD is a prompt bullet list | 29 | High | ✅ `validate_done.py` + `definition_of_done_met` |
| [G6](#g6--governance-documents-are-referenced-but-never-created) | A shipped command reads two files nothing creates | 5 | Medium | ✅ 3 generated, 2 templated and seeded |
| [G7](#g7--agentsmd-skillmd-and-indexmd-are-absent) | Three whole sections of the document have no artifact | 7, 8, 9, 33, 56, 57 | Medium | ✅ Scaffolded + `validate_context.py` |
| [G8](#g8--change-impact-analysis-is-not-exposed) | The graph supports it; nothing surfaces it | 52 | Medium | ✅ `impact.py` |
| [G9](#g9--coverage-metrics-and-orphan-classes-are-partial) | 3 of 9 metrics, 6 of 10 orphan classes | 53, 54 | Low | ✅ 3 ratios added, 2 orphan classes added |
| [G10](#g10--smaller-inconsistencies) | Six small defects and false-ish claims | various | Low | ✅ All six |

### What shipped

| New script | Does |
|---|---|
| `approve_edge.py` | Records an approval, bound by hash to the content approved |
| `render_views.py` | Generates all seven Markdown views; reports stale ones (`VIEW-001`) |
| `validate_done.py` | The Definition of Done, computed (`DOD-001`…`DOD-006`) |
| `validate_context.py` | The `AGENTS.md` / `index.md` / `SKILL.md` hierarchy (`CTX-001`…`CTX-004`) |
| `impact.py` | §52 change impact, both directions |

New checks: `TRC-013`, `DOD-001`–`006`, `CTX-001`–`004`, `VIEW-001`–`002`, `DOR-009`.
New gate condition: `definition_of_done_met`. New metrics: `approved_verified`,
`approved_stale`, `code_test_coverage`, `mitigation_coverage`, `evidence_coverage`.

### Two things found while implementing, not in the original audit

1. **The audit reported the raw `approved` label too.** `audit.py` printed
   `provenance_mix['approved']` beside the *split* `derived` figures — the same defect G2
   closes, in the report rather than the gate. It now shows `approved` and `stale` separately.
2. **Seeding `src/AGENTS.md` broke backward coverage.** G7's scaffold puts a governance
   document inside the traceability perimeter, so `TRC-007` counted it as an untraced source
   file: adopting the context hierarchy would have *lowered* coverage, setting two parts of
   the design against each other. `AGENTS.md`, `index.md` and `SKILL.md` are now excluded
   structurally in `Graph.in_perimeter`, not via config — an exclude list replaces rather than
   merges, so a project carrying its own list would have broken on upgrade.

### Deliberately still open

The README's Limitations are unchanged except where noted: Microcks and contract parsing
(§25, §41), the two remaining unimplemented derivation rules, CI enforcement (§61–§63), PR
review surface (§42), commit-trailer validation (§43–§44), bundle publishing. One was added:
**an approval binds content, not a human** — `approve_edge.py --by product-owner` is available
to an agent exactly as it is to a person, and the only real anchor would be `approval.commit`
verified against a signed commit.

Governance overhead per unit of delivered work (§65) remains unmeasured.

---

## G1 — `approved` provenance is unreachable

**Priority: blocker. Size: S. Fix first — G2 depends on it.**

### Symptom

`TRC-009` demands `provenance: approved` on every edge touching a `BASELINED`+ requirement.
Complying makes `TRC-000` fail. There is no state that satisfies both, so a requirement can
never be baselined.

### Reproduction

On a clean copy of `tests/fixtures/good`:

```bash
# 1. Baseline a requirement, exactly as s31 intends.
#    REQ-AUTH-0014.status = BASELINED, with an approvals: entry.
python3 .../validate_trace.py --root . --json
#    -> TRC-009 FAIL, 7 violation(s)
#       "AC-AUTH-0014-0003 --verifies--> REQ-AUTH-0014: touches baselined
#        REQ-AUTH-0014 with provenance 'asserted' (minimum 'approved')"

# 2. Do exactly what it asks: set those 7 edges to provenance: approved,
#    with a real approval block and a real sha256 in approved_endpoints_hash.
python3 .../validate_trace.py --root . --json
#    -> TRC-000 FAIL, 14 error(s)
#       "edges/0: 'approval' is a required property"
#       "edges/0: 'approved_endpoints_hash' is a required property"
```

Both fields are present on disk. Validating the same file directly with
`schema_errors(doc, "traceability.schema.json")` returns **zero** errors.

### Root cause

[`validate_trace.py:60-77`](../../extensions/openup/scripts/python/validate_trace.py)
does not schema-check the stores. It rebuilds a synthetic document out of the in-memory
`Edge` objects and validates that:

```python
for path in set(e.source_file for e in graph.edges if e.source_file):
    document = {
        "schema_version": "1.0",
        "edges": [
            {k: v for k, v in {
                "from": e.from_id, "relation": e.relation, "to": e.to_id,
                "provenance": e.provenance, "status": e.status,
                "derived_by": e.derived_by, "evidence": e.evidence or None,
            }.items() if v is not None}
            for e in graph.edges if e.source_file == path
        ],
    }
    errors = schema_errors(document, "traceability.schema.json")
```

The [`Edge`](../../extensions/openup/scripts/python/openup_model.py) dataclass
carries seven fields. The schema's `edge` definition has twelve. `approval`,
`approved_endpoints_hash`, `id` and `note` are dropped at load time by
[`_load_edges`](../../extensions/openup/scripts/python/openup_model.py) — so the
schema then demands the exact fields the projection just discarded.

### Why it matters beyond the dead end

1. **`additionalProperties: false` is inert.** A junk or misspelled key in a store cannot
   survive into a dict the loader builds by hand, so `TRC-000` structurally cannot detect
   one. The check reads as "the stores conform to the schema" and is not that.
2. **§31's state machine is truncated.** `BASELINED` is the mandatory stop before
   `IMPLEMENTED → VERIFIED → ACCEPTED`. `traceability_final` requires `validate_trace` not
   to FAIL, so a project that baselines anything can never pass `GATE-PRODUCT_RELEASE`.
   The upper half of the governance lifecycle is unreachable.
3. **The fixture silently documents the bug.** `tests/fixtures/good` has `approved: 0`
   edges. That is not a design choice — it is the only configuration that validates.
4. **The test suite tests the demand, not the satisfaction.**
   `test_baselined_requirement_needs_approved_provenance` asserts TRC-009 fires. Nothing
   asserts that doing what TRC-009 asks then works. Negative path covered, positive path
   broken — which is exactly how this survived to a green suite.

### Fix

**Validate the documents as parsed from disk.** Retain the raw store documents at load time
and check those.

In `openup_model.py`, `Graph.__init__`:

```python
self.raw_stores: dict[str, dict] = {}
```

In `Graph._load_edges`, keep the parsed document:

```python
for path in expand_paths(self.root, self.config["traceability"]["stores"]):
    rel = self._rel(path)
    self.loaded_files.append(rel)
    doc = _load_yaml(path)
    self.raw_stores[rel] = doc          # NEW — the document as written
    for raw in doc.get("edges", []) or []:
        ...
```

Complete the `Edge` dataclass while you are here — G2 needs these fields anyway, and a
lossy loader is what caused this:

```python
@dataclass
class Edge:
    from_id: str
    relation: str
    to_id: str
    provenance: str
    status: str = "active"
    source_file: str | None = None
    evidence: list[str] = field(default_factory=list)
    derived_by: str | None = None
    edge_id: str | None = None                    # NEW — the optional TRACE-nnnn
    approval: dict[str, Any] | None = None        # NEW
    approved_endpoints_hash: str | None = None    # NEW
    note: str | None = None                       # NEW
```

Replace the `TRC-000` block in `validate_trace.py`:

```python
schema_failures: list[str] = []
for rel, doc in sorted(graph.raw_stores.items()):
    schema_failures += [f"{rel}: {err}" for err in schema_errors(doc, "traceability.schema.json")]
_record(verdict, "TRC-000", schema_failures,
        f"all {len(graph.raw_stores)} traceability store(s) conform to traceability.schema.json")
```

Note this also drops the `break` on the first failing store. Reporting one store at a time
turns a single fix-validate cycle into several for no benefit.

### Verification

Three new tests in `tests/test_validators.py`:

- `test_an_approved_edge_validates` — the missing positive path. One edge with
  `provenance: approved`, a well-formed `approval` and a syntactically valid hash;
  `TRC-000` must pass.
- `test_a_baselined_requirement_can_actually_be_approved` — the full G1 sequence:
  baseline the requirement, approve its edges, assert the verdict is **PASS**. This is the
  regression test for the dead end and should be named so its purpose survives.
- `test_an_unknown_key_in_a_store_is_rejected` — add `provenence: asserted` (typo) to an
  edge and assert `TRC-000` fails. Proves `additionalProperties: false` now bites, which it
  never has.

Mutation check: revert `TRC-000` to the reconstruction and confirm exactly these three fail.

---

## G2 — `approved_endpoints_hash` is never verified

**Priority: blocker. Size: M. Do immediately after G1 — same file, same tests.**

### Symptom

The schema requires `approved_endpoints_hash` to be **present** on an approved edge. No code
computes it, compares it, or reacts to it. `grep -rn approved_endpoints_hash
extensions/openup/scripts/` returns nothing.

[`traceability-template.yaml:23`](../../extensions/openup/templates/traceability-template.yaml)
tells the reader: *"editing an endpoint downgrades the edge."* That does not happen.
Same claim in [`speckit.openup.trace.md:32`](../../extensions/openup/commands/speckit.openup.trace.md).

### Why it matters

This is the identical defect that `TRC-010` was written to close, one level over — and it is
now load-bearing on the gate that was re-based to close the first one.
[`evaluate_gate.py:275`](../../extensions/openup/scripts/python/evaluate_gate.py):

```python
verifiable = (reproduced + approved) / edges if edges else 0.0
```

`reproduced` is re-executed by a rule and fails the edge if it disagrees. `approved` is a
string anyone can type. Measured on the good fixture — relabel the 11 `asserted` edges
`approved`, `approval: {by: release-owner, at: ...}`, hash `"0" * 64`:

```
before   verifiable = 10/26 = 38%   ->  traceability_final FAILS
after    verifiable = 21/26 = 81%   ->  traceability_final PASSES
```

Once G1 lands and `approved` becomes usable, that is a live bypass on the release gate.
**G1 without G2 is worse than shipping neither**, because G1 unlocks the label.

### Fix

Bind the approval to the content it approved. Add to `openup_model.py`:

```python
# Lifecycle bookkeeping, excluded from the fingerprint. An approval is about WHAT was
# approved, not where the artifact currently sits in s31's state machine: advancing
# APPROVED -> BASELINED must not void a signature, but editing the requirement must.
LIFECYCLE_KEYS = {"status", "approvals", "baseline"}


def endpoint_fingerprint(graph: Graph, identifier: str) -> str:
    """Canonical text for one endpoint of an approved edge."""
    for store in (graph.artifacts, graph.wbs, graph.risks):
        if identifier in store:
            body = {k: v for k, v in store[identifier].items() if k not in LIFECYCLE_KEYS}
            return json.dumps(body, sort_keys=True, separators=(",", ":"))
    return identifier          # a source path: the path IS the identity


def approval_hash(graph: Graph, edge: Edge) -> str:
    payload = "\x00".join((
        endpoint_fingerprint(graph, edge.from_id),
        edge.relation,
        endpoint_fingerprint(graph, edge.to_id),
    ))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

The relation is inside the hash deliberately: re-pointing an approved edge at a different
relation must void the approval, not inherit it.

New check `TRC-013` in `validate_trace.py`, placed after `TRC-012`:

```python
stale: list[str] = []
for edge in graph.edges:
    if edge.provenance != "approved":
        continue
    expected = approval_hash(graph, edge)
    if edge.approved_endpoints_hash != expected:
        stale.append(
            f"{edge}: approved_endpoints_hash does not match its endpoints — the approval "
            f"was given for different content and no longer applies "
            f"(stored {str(edge.approved_endpoints_hash)[:12]}…, computed {expected[:12]}…)"
        )

if stale:
    verdict.warn("TRC-013", f"{len(stale)} approved edge(s) no longer match what was approved", stale)
else:
    verdict.ok("TRC-013", "every approved edge still matches the content it was approved for")
```

`openup_model.py` already imports `json`; `hashlib` is new.

**Report as WARN, and downgrade in the metrics.** Not FAIL. Reason: a stale hash after a
legitimate edit is a normal event in a live project, not a governance violation — the
correct response is that the edge stops counting as approved until someone re-approves it,
which is precisely what the template already promises. Failing the whole validator would
make people avoid `approved` entirely, which is how the feature dies a second time.

Metrics must reflect the downgrade, or the gate still reads the label:

```python
"approved_verified": mix["approved"] - len(stale),
"approved_stale": len(stale),
```

and `evaluate_gate._trace_final` counts `approved_verified`, never `mix["approved"]`.

### The tool is part of the fix, not an extra

A human cannot compute this hash by hand. Shipping the check without the tool recreates the
original mistake — a required field nobody can produce correctly. Add
`scripts/python/approve_edge.py`:

```
approve_edge.py --from REQ-AUTH-0014 --relation refines --to BUS-OBJ-0017 \
                --by product-owner [--commit <sha>] [--note "..."]
```

It locates the edge in a hand-maintained store, stamps `provenance: approved`, the
`approval` block and the freshly computed hash, and rewrites the file. Register it in
`extension.yml` (`test_every_script_on_disk_is_declared` will fail otherwise) and add
`approve_edge` to the allowlist in `test_python_dependencies_are_declared`.

### Decision to make: source-path endpoints

Recommended above: for a source path, fingerprint **the path string**, not the file bytes.

Reason: an approved edge to a file records *which file was approved for this role*, and
source churn is continuous and expected — hashing bytes would void every approval on every
commit, and people would stop using approvals within a week. File *content* correctness is
what tests and `TRC-010` derivation are for.

The alternative (hash the bytes) is defensible for a regulated context where an approval
really is content-bound. If you take it, say so in `ID-GRAMMAR.md §3`, because the two
behaviours are not distinguishable from the outside.

### Honest limit — record it in the README

The hash binds an approval to **content**. It does **not** prove a human was involved: an
agent can run `approve_edge.py` and write `--by product-owner`. The only real anchor is
`approval.commit` pointing at a signed commit, verified against git. That is out of scope
here; do not let the hash be described as human-verification. Add a Limitations bullet in
the same PR, or G2 ships a second overstated claim while fixing the first.

---

## G3 — The task layer does not exist

**Priority: high. Size: M.**

### Symptom

`TASK-*` is in the ID grammar, `task` is in `artifactType`, `modifies` and `decomposes-to`
are in the relation vocabulary and have signatures in
[`validate_trace.py:28-46`](../../extensions/openup/scripts/python/validate_trace.py).

```bash
grep -rn 'TASK-' tests/fixtures/           # nothing
# relations used in the reference fixture:
#   belongs-to 7, implements 6, verifies 3, refines 3, executes 2,
#   evidences 2, tests 1, mitigates 1, conforms-to 1
#   -> modifies 0, decomposes-to 0, contains 0, validates 0, depends-on 0
```

The preset's `speckit.tasks` wrap mints `[TASK-nnnn]` into `tasks.md` prose
([`speckit.tasks.md:59`](../../presets/openup-governance/commands/speckit.tasks.md)).
Nothing parses `tasks.md`. Those ids never reach the graph, and
`Graph.exists()` would reject an edge pointing at one.

### Why it matters

This is the document's own central chain. §21, §26, §44 and §67 all route through
`REQ → WBS → TASK → modifies → file`. What is implemented is `file --implements--> REQ`
directly (which is why `implements` accepts `source-artifact` as a domain). Consequences:

- `task-modifies-closure` — one of the three unimplemented derivers — is not merely unwritten,
  it is **unwritable**, because it would close over task artifacts that cannot exist.
- §54's "orphan tasks" cannot be detected.
- §67's reverse query cannot run as the document writes it.
- [`ID-GRAMMAR.md:61`](../../extensions/openup/schemas/ID-GRAMMAR.md) states *"Every
  prefix listed in §48 is used above. None is defined and left unused."* True of the table.
  Misleading about the model.

### Two options — pick one, do not leave it ambiguous

**Option A (recommended): collapse the task layer into WBS L7.**

§15 already defines L7 as "Executable Task". The WBS node *is* the task; a parallel `TASK-*`
identity is a second name for one thing, which is the drift the whole model exists to
prevent. Delete rather than decorate.

Sweep — all of it, or the grammar stays inconsistent:

| File | Change |
|---|---|
| `schemas/artifact.schema.json` | drop `taskId`, `"task"` from `artifactType`, the `taskId` branch of `anyId`; drop `modifies` and `decomposes-to` from the `relation` enum |
| `openup_model.py` | drop both from `INVERSE`; drop `decomposes-to` from `ACYCLIC` |
| `validate_trace.py` | drop both `SIGNATURES` entries; drop `"task"` from `WORK_TYPES`, from the `evidences` range and the `depends-on` / `belongs-to` domains |
| `derivers.py` | drop `task-modifies-closure` from `UNIMPLEMENTED_RULES` |
| `schemas/ID-GRAMMAR.md` | drop the Task row and the two relation rows; **rewrite line 61** to say which prefixes are reserved-but-unmodelled (see G10) |
| `presets/.../speckit.tasks.md` | task contract header becomes `[WBS-1.2.3.4.1.2]`; `TASK-nnnn` disappears |
| `commands/speckit.openup.trace.md` | deriver table loses the row |
| `README.md` | Limitations: three derivation rules → two |
| `tests/test_derivers.py` | `test_every_unimplemented_rule_is_declared_not_silently_missing` is parametrised over the rule set and will need the new count |

Add one test asserting the relation vocabulary in the schema and the `SIGNATURES` keys are
the same set. That mismatch is what let two relations sit unused and unnoticed.

**Option B: make the task layer real.**

`artifacts.stores` already includes `specs/*/artifacts.yaml` — a registry exists and is
loaded. Instruct the `speckit.tasks` wrap to write task artifacts there alongside
`tasks.md`, then implement `task-modifies-closure`.

Cost: the agent maintains a second registry whose entries nothing can verify (tasks are
inherently `asserted`), and `tasks.md` becomes a generated view of it or the two drift.
Take B only if §67's reverse query through tasks is something you actually want to
demonstrate. Otherwise A is cheaper and more honest.

---

## G4 — Generated views have no generator

**Priority: high. Size: M.**

### Symptom

There is no renderer. `wbs.md`, `risk-register.md`, `traceability.md` and `coverage.md` are
named as generated views in the schemas, templates and three commands, and the commands
instruct **the agent** to produce them:

- [`speckit.openup.wbs.md:73`](../../extensions/openup/commands/speckit.openup.wbs.md) — "Regenerate it from the YAML; never..."
- [`speckit.openup.risk.md:71`](../../extensions/openup/commands/speckit.openup.risk.md) — "Regenerate it; never hand-edit it."
- [`speckit.openup.trace.md:103`](../../extensions/openup/commands/speckit.openup.trace.md) — "generated from the YAML"

### Why it matters

§47 exists to stop humans maintaining duplicated artifacts. §65 says *"Do not manually
maintain traceability documents. Generate traceability views from structured relationships."*
An LLM hand-transcribing YAML into Markdown is manual maintenance with an extra failure
mode: it is non-deterministic, it is unreviewable (every regeneration is a fresh diff), and
it can quietly disagree with the canonical data — which is the precise failure the whole
design is built to prevent. This is the one place the system currently asks an agent to do
what it forbids everywhere else.

### Fix

`scripts/python/render_views.py`, following the `derive_edges.py` idiom exactly — that
precedent is already established and tested, so reuse it rather than inventing a second one:

- `--write` regenerates all views from the canonical YAML.
- no flag: renders in memory, diffs against what is on disk, emits a verdict.
  `VIEW-001` FAIL for a view that is missing or stale, `VIEW-002` WARN for a view file with
  no canonical source.
- Every output carries the same banner: `<!-- GENERATED by render_views.py — do not edit -->`.

Views to emit:

| Output | Source | Content |
|---|---|---|
| `.specify/wbs/wbs.md` | `wbs.yaml` | indented tree, level names, owner, iteration, status, terminal_reason |
| `.specify/risks/risk-register.md` | `risk-register.yaml` | table sorted by exposure desc, mitigation + verification refs, residual |
| `.specify/traceability/traceability.md` | all stores | edges grouped by relation, with provenance |
| `.specify/traceability/coverage.md` | `validate_trace` metrics | forward/backward/verification/scenario coverage **and the provenance mix** — `speckit.openup.trace.md:104` already requires the mix here, so the renderer must include it or it contradicts a shipped instruction |

Wire `render_views.py --write` as a `shell` step into the elaboration and construction
workflows, next to the existing `derive-edges` step. Then replace the "regenerate it"
prose in all three commands with the command to run. Add the script to `extension.yml` and
the dependency allowlist.

Test: `test_a_hand_edited_view_is_reported` — edit `wbs.md`, assert `VIEW-001` fails,
run `--write`, assert it passes. Same shape as
`test_derive_edges_write_repairs_what_trc_011_reports`.

---

## G5 — Definition of Done is not computed

**Priority: high. Size: M.**

### Symptom

Definition of Ready is machine-checked:
[`select_work.py:26-60`](../../extensions/openup/scripts/python/select_work.py)
returns per-node blockers. Definition of Done is a bullet list in
`tasks-addendum.md:62-74` and a paragraph in `speckit.implement.md:84`. No code reads
`status: done` and checks anything; the only use of the value is
`select_work.DONE_STATUSES` for dependency ordering.

### Why it matters

§29 is explicit about the standard it is asking for:

> `TASK-042.status = DONE` **is a computed governance state rather than a casual AI declaration.**

Right now it is exactly a casual declaration — an agent writes `status: done` and nothing
disagrees. The asymmetry is the tell: DoR blocks work from starting on evidence, DoD lets
work be called finished on a claim. Of the two, DoD is the one a gate depends on.

### Fix

`scripts/python/validate_done.py`, mirroring `select_work.py` so the pair is symmetric. For
every WBS node with `status: done`:

| Check | Condition | §  |
|---|---|---|
| `DOD-001` | has at least one `evidence` reference, and each resolves | 29, 19 |
| `DOD-002` | each linked requirement is reached by both an `implements` and a `verifies` edge | 29, 32 |
| `DOD-003` | each linked acceptance criterion has ≥1 `executes` edge from a scenario | 24, 29 |
| `DOD-004` | if `kind: risk-mitigation`, the risk has evidence and residual exposure strictly below current | 19, 29 |
| `DOD-005` | no edge touching the node has `status: broken` | 29 |
| `DOD-006` | if `kind: test`, the referenced acceptance criteria exist and are covered | 18, 29 |

Then add a gate condition `definition_of_done_met` to
`GATE-INITIAL_OPERATIONAL_CAPABILITY` in `openup-config.yml` and implement it in
`evaluate_gate.py` — a condition named in config but not implemented already fails closed,
so config and code must land together.

Wire the validator into `openup-construction/workflow.yml` before `evaluate-gate`.

Test: take the good fixture, mark an L7 node `done` after stripping its evidence, assert
`DOD-001`. One test per check, plus a gate-level test.

---

## G6 — Governance documents are referenced but never created

**Priority: medium. Size: S.**

### Symptom

[`speckit.openup.iteration.md:45`](../../extensions/openup/commands/speckit.openup.iteration.md)
tells the agent to check tasks against `.specify/governance/definition-of-ready.md`, and
[line 69](../../extensions/openup/commands/speckit.openup.iteration.md) against
`.specify/governance/definition-of-done.md`.

[`init_openup.py:22-30`](../../extensions/openup/scripts/python/init_openup.py)
creates `.specify/governance/` **empty**. There is no template for either file, and §5 also
names `quality-gates.md`, `change-control.md` and `approval-matrix.md`, none of which exist.

So a shipped command instructs the agent to read two files that will never be there. The
agent will either skip the step or invent the content — and inventing governance criteria is
the §51 failure the preset exists to forbid.

### Fix

Two of these should be **generated**, not authored, so the prose cannot drift from the code
that enforces it:

- `definition-of-ready.md` ← rendered from `select_work._readiness`'s check list
- `definition-of-done.md` ← rendered from `validate_done`'s check table (needs G5)
- `quality-gates.md` ← rendered from the `gates:` block of `openup-config.yml`

Fold all three into `render_views.py` from G4; they are the same mechanism. A hand-written
Definition of Ready that disagrees with `select_work.py` is worse than none, because people
will read the document and the machine will apply the code.

The remaining two are genuinely authored decisions, so ship templates and seed them:

- `templates/change-control-template.md` → `.specify/governance/change-control.md`
- `templates/approval-matrix-template.md` → `.specify/governance/approval-matrix.md`,
  seeded from §59's seven human approval boundaries and the roles already in
  `stakeholders-template.md`

Add both to `init_openup.SEEDS` and `extension.yml`. Then the command references resolve.

---

## G7 — `AGENTS.md`, `SKILL.md` and `index.md` are absent

**Priority: medium. Size: L. Lowest enforcement value of the set — schedule last.**

### Symptom

```bash
grep -rln 'SKILL\.md' --exclude=specup.md .     # nothing
grep -rn  'AGENTS\.md' --exclude=specup.md .    # one passing mention in index-template.md
```

§7 (AGENTS.md operating contract), §8 (SKILL.md capability contract, eight named skills) and
§9 (index.md per governed directory) have no template, no scaffold entry and no validator.
`index-template.md` exists but is seeded only to `.specify/lifecycle/index.md`.

Three further places assume they exist:

- §33 says the audit inspects "AGENTS.md hierarchy → index.md hierarchy". `audit.py` does neither.
- §28's Definition of Ready lists `Applicable SKILL.md ✓`. `select_work._readiness` has no such check.
- §56/§57's progressive-context argument — the scalability claim in the README — is built on
  `AGENTS.md → index.md → artifact` navigation that does not exist to navigate.

### Why it matters, and why it is still not urgent

These are the ergonomic layer, not the enforcement layer: nothing silently passes because
they are missing, and no claim about evidence quality depends on them. But §56/§57 is the
argument for why this approach scales, and it is currently unbacked. Do it before making any
public claim about context efficiency.

### Fix

1. **Templates** — `agents-root-template.md` (from §7's contract verbatim: mandatory startup,
   filesystem-first rule, prohibited, required, boundaries), `agents-specify-template.md`,
   `agents-src-template.md`, and eight `skills/<name>/SKILL.md` templates matching §8's list
   (requirements, architecture, wbs, risk, traceability, gherkin, contracts, microcks — drop
   the last two, or seed them as stubs pointing at the Limitations entry, so we are not
   shipping a skill for a capability that does not exist).
2. **Scaffold** — `init_openup.py` seeds root `AGENTS.md`, `.specify/AGENTS.md`,
   `skills/*/SKILL.md`, and an `index.md` in each directory it creates.
3. **Validator** — `validate_context.py`: `CTX-001` every governed directory has an
   `index.md`; `CTX-002` every artifact reference inside an `index.md` resolves in the graph;
   `CTX-003` every directory named in the perimeter has a reachable `AGENTS.md` above it;
   `CTX-004` every `SKILL.md` referenced by a WBS node exists. Fold `CTX-001`/`CTX-002` into
   `audit.py` so §33's claim becomes true.

`CTX-002` is the one with real value — a stale `index.md` pointing at a deleted requirement
is a context map that actively misleads an agent.

---

## G8 — Change impact analysis is not exposed

**Priority: medium. Size: S. Best value-per-hour on this list.**

### Symptom

§52 asks for a computed impact set from a changed artifact. Nothing exposes it. The
capability is entirely present — `Graph.reaches(start, relations, reverse=True)` already
does transitive closure in both directions, cycle-safe.

### Fix

`scripts/python/impact.py --of REQ-AUTH-0014 [--json]`, emitting the §52 fan-out grouped by
artifact type: user stories, WBS nodes, risks, ADRs, contracts, scenarios, tests, source
files. Reverse mode `--of src/security/certificate_validator.ts` gives §22's reverse query.

Exit `0` always — this is a report, not a gate.

Then reference it from `speckit.implement.md` so the agent presents an impact report before
touching a requirement, which is what §52 actually asks for. Small, self-contained, and it
makes the knowledge-graph claim demonstrable in one command.

---

## G9 — Coverage metrics and orphan classes are partial

**Priority: low. Size: M.**

### §53 — 3 of 9 metrics exist as ratios

Implemented: requirement→implementation (`forward_coverage`), requirement→verification
(`verification_coverage`), source→requirement (`backward_coverage`), plus AC→scenario
(`scenario_coverage`, added with TRC-012).

Missing: WBS→task (moot under G3 Option A), task→code (same), code→test, API→Microcks
(blocked on contracts, already a declared limitation), risk→mitigation and risk→evidence
(both exist as boolean checks `RISK-004`/`RISK-007` but are never reported as ratios).

Cheapest real additions: `code_test_coverage` — the share of in-perimeter source files with
an incoming `tests` edge, which `test-file-naming-convention` already derives — and
`risk_mitigation_coverage` / `risk_evidence_coverage`, which are three lines each over data
`validate_risk` already computes. A boolean check tells you whether you are compliant; a
ratio tells you whether you are getting better, which is what §53 is for.

### §54 — 6 of 10 orphan classes exist

Implemented in `TRC-008`: orphan requirements, orphan WBS nodes, orphan risks (high-exposure
only, deliberately), orphan scenarios; plus orphan source files via `TRC-007` and broken
references via `TRC-002`.

Missing: orphan tasks (moot under G3 Option A), orphan tests, orphan APIs, orphan contracts.

Add to `TRC-008`: a registered test artifact (`TC-*`, `UNIT-*`, `INTG-*`) with no outgoing
`tests` and no outgoing `verifies` edge, and a registered `CONTRACT-*` with no incoming
`conforms-to` and no incoming `validates`. Both are a few lines and both catch a real thing —
a test nobody connected to a requirement is a test that proves nothing about the graph.

---

## G10 — Smaller inconsistencies

**Priority: low. Size: S in total.** Each is a few lines; grouped because they share no theme
beyond "a claim that is not quite true".

1. **No `artifacts:` block in the shipped config.** `openup-config.yml` has nine top-level
   blocks and `artifacts` is not among them, so `.specify/traceability/requirements.yaml` —
   the most-edited store in the system — has its location only in
   [`DEFAULT_CONFIG`](../../extensions/openup/scripts/python/openup_model.py). A user
   reading the config file cannot discover where requirements live or that
   `specs/*/artifacts.yaml` is also loaded. **Fix:** add the block with the same
   commented-rationale style as the rest of the file.

2. **`ADR-*` can never be linked.** `ADR-0019` is registered in the good fixture and no
   `SIGNATURES` entry accepts `architecture-decision` at either end, so no edge can reach it.
   §20 puts Design Decision in the chain; §57 requires "relevant architecture decision" in an
   L7 task's context; neither is expressible. **Fix:** give `refines` an
   `architecture-decision` domain (ADR refines a requirement) and add
   `implements: source-artifact → architecture-decision`, or state plainly in `ID-GRAMMAR.md`
   that ADRs are referenced by path and not modelled as graph nodes. Either is fine; silence
   is not.

3. **`supersedes` is documented with a signature it does not have.**
   [`ID-GRAMMAR.md:92`](../../extensions/openup/schemas/ID-GRAMMAR.md) says
   `ADR → ADR; Requirement → Requirement`. `SIGNATURES["supersedes"]` is `(None, None)` —
   any type to any type. **Fix:** implement the documented signature, or relax the doc. Same
   question for `approves`, where `(None, None)` is correct and should say why.

4. **`FLOW-*`, `TRACE-*`, `SECURE-*` participate in no relation.** Like `TASK-*` in G3, they
   are grammar-only. **Fix:** with G3, rewrite `ID-GRAMMAR.md:61` from "None is defined and
   left unused" to an explicit two-list statement — prefixes the model uses, and prefixes
   reserved for later with the reason. The current sentence is true of the table and reads as
   a claim about the model.

5. **`TRC-000` reports one store at a time.** Folded into G1's fix; listed here so it is not
   lost if G1 is split.

6. **The `contracts:` block warning is good; make it the pattern.** The
   `NOT YET READ BY ANY VALIDATOR` header on `openup-config.yml:109` is the right treatment.
   Apply the same header to anything else that survives this plan unimplemented, rather than
   leaving readers to grep for whether a setting does anything.

---

## Sequencing — as executed

Order was chosen so that no step shipped a claim the next step invalidated. It was followed
exactly; every step below landed.

| Step | Work | Why here |
|---|---|---|
| 1 | **G1 + G2 together, one PR** | G1 unlocks `approved`; G2 makes it mean something. Landing G1 alone opens a live bypass on the release gate — strictly worse than the current dead end. Do not split. |
| 2 | **G4 + G6** | Same mechanism (`render_views.py`). G6's two generated documents fall out of G4 for free. Removes the "agent hand-maintains derived documents" contradiction. |
| 3 | **G5** | Needs G6's generated DoD document to point at; completes the DoR/DoD symmetry and adds the gate condition. |
| 4 | **G3** | A wide mechanical sweep. Do it when the semantics above are settled, so the sweep happens once. |
| 5 | **G8 + G10** | Small, independent, no dependencies. Good filler. |
| 6 | **G9** | Metrics and orphan classes, once G3 has settled which of them are still meaningful. |
| 7 | **G7** | Largest, lowest enforcement value. Required before making any public claim about §56/§57 context efficiency. |

### Standing rules for every step

- Every new invariant gets a **mutation check**: break it deliberately, confirm exactly the
  tests written for it fail, and nothing else does. This is what caught the
  perimeter/marker mismatch in the last change.
- Every new CLI keeps the **three-way exit contract**: `0` PASS, `1` FAIL, `2` ERROR.
- Every new script is registered in `extension.yml` and added to the allowlist in
  `test_python_dependencies_are_declared`, or the manifest tests fail.
- `task` never appears in a workflow `run:`, an extension command bash block, a preset bash
  block, or any `requires.tools` — enforced by `tests/test_taskfile_boundary.py`.
- No `{{ inputs.* }}` in any workflow `run:` field.
- When a fix makes a README or command claim false, correct it **in the same commit**. Two of
  the gaps above exist because documentation described intended behaviour rather than shipped
  behaviour.

### Versioning

Components are at `0.1.0` and nothing is published. G1 and G2 change the meaning of
`provenance: approved` and of `traceability_final`. If anything has been published by the
time these land, that is a breaking change to the evidence model and needs a minor bump plus
a migration note — an existing graph with `approved` edges will have no valid hashes and every
one of them will downgrade on first run.
