# Traceability — SpecUP's own graph

> **Answers** — what is in this directory, what the graph currently reports, and which of
> those numbers can be trusted without taking anyone's word for it.
>
> **Does not answer** — what the rules are. That is `.specify/AGENTS.md`.
>
> **Filled in badly when** — the figures below are updated without re-running the commands
> that produce them. Every number here came from a run on 2026-09-16 and is reproducible in
> one command; a hand-edited figure in a document about honesty would be the whole problem in
> one line. Re-run on 2026-09-17 after the BUSL-1.1 relicence, which added a requirement, a
> node, two risks and four edges.
>
> **Checked by** — `CTX-002` fails an id here that resolves to nothing. **Nothing checks what
> this map leaves out**, and nothing checks that the commentary matches the run.
>
> **Authority** — the maintainer.

## Purpose

SpecUP governs itself with SpecUP. This directory holds the graph that does it, and this file
records what governing itself actually produced — including the parts that do not flatter it.

## What the graph reports

Reproduce with:

```bash
python3 extensions/openup/scripts/python/validate_trace.py --json
python3 extensions/openup/scripts/python/audit.py
```

| Metric | Value | What it means here |
|---|---|---|
| `edges` | 78 | 18 `refines`, 21 `implements`, 18 `verifies`, 1 `mitigates`, 7 `evidences`, 1 `tests`, 12 `belongs-to` |
| `perimeter_files` | 17 | the Python modules under `extensions/openup/scripts/python/` |
| `forward_coverage` | 100% | every requirement reaches an implementer |
| `backward_coverage` | 100% | every in-perimeter file reaches a requirement |
| `verification_coverage` | **95%** | 18 of 19 — `NON-FR-DOCS-0001` has no verifier |
| `orphans` | 0 | |
| `derived_verified` | 13 | reproduced from the filesystem this run |
| `asserted_share` | **83%** | one person's judgement, unchecked |
| `approved_verified` | 0 | nothing is signed; see `RISK-0001` |

## The number that matters, and it is not the coverage

**83% of this graph is `asserted`, and 17% is machine-reproducible.** Backward coverage of
100% over 17 files is a true statement about a perimeter chosen by the same person who wrote
the edges. `existing-project.md` says an existing project reporting 100% on day one "has not
been governed; it has been decorated" — the defence against that reading is not a lower
number, it is this one printed beside it.

Thirteen derived edges come from two rules:

- `wbs-iteration-field` — 12 `belongs-to` edges, one per WBS node carrying an `iteration:`.
  A restatement of a field, which is exactly why it is derivable.
- `test-file-naming-convention` — **1** edge, `UNIT-DRV-0001 --tests--> derivers.py`, and it
  exists by coincidence: `tests/test_derivers.py` is the only test file in this repository
  whose name matches the module it exercises. The rule reports the other five by name:

  ```
  UNIT-APV-0001:  no in-perimeter file named 'approvals.py'  for tests/test_approvals.py
  UNIT-CORE-0001: no in-perimeter file named 'validators.py' for tests/test_validators.py
  UNIT-DOC-0001:  no in-perimeter file named 'docs.py'       for tests/test_docs.py
  UNIT-INIT-0001: no in-perimeter file named 'init.py'       for tests/test_init.py
  UNIT-LIC-0001:  no in-perimeter file named 'license.py'    for tests/test_license.py
  ```

  The fifth arrived with the relicence. `tests/test_license.py` checks manifests and licence
  files, none of which is a module, so no naming convention could have earned that edge — a
  reminder that the rule's reach is bounded by more than this repository's naming habit.

SpecUP names its test files after the behaviour under test rather than after the module. That
is a defensible naming choice and it costs the project its own machine-checkable provenance.
`RISK-0003` records it; `WBS-1.1.3.1` is the work; the ADR has not been written, and the two
candidate fixes are not equivalent.

## The one requirement nothing verifies

`NON-FR-DOCS-0001` — every check named in the manual exists in the code, and the reverse.
It is implemented by `WBS-1.1.2.6`, which is a person reading both sides at release time, and
verified by nothing. `TRC-006` fails on it and the audit's final gate fails with it.

Deleting it would report 100% verification over a project whose documentation drifted four
times in two releases. The obligation exists either way; registering it is what turns a
memory into a number. `RISK-0002` is the same fact.

## What the Construction gate fails on

`GATE-INITIAL_OPERATIONAL_CAPABILITY`, evaluated because `lifecycle.phase` is `CONSTRUCTION`:

| Condition | Verdict | |
|---|---|---|
| `wbs_valid` | PASS | |
| `forward_coverage_met` | PASS | |
| `backward_coverage_met` | PASS | |
| `definition_of_done_met` | PASS | 6 of 6 nodes claiming `done` survive `DOD-001`..`006` |
| `no_open_critical_risks` | PASS | nothing at or above 0.65 |
| `no_orphans` | PASS | |
| `acceptance_scenarios_passing` | **FAIL** | there is no `.specify/evidence/acceptance-results.json` |

The failure is correct and is not being repaired. That condition asks for executed Gherkin
scenarios; SpecUP has no `.feature` files, and its acceptance is a pytest suite that the model
expresses as `UNIT-*` artifacts verifying requirements. Writing an `acceptance-results.json`
by hand from a pytest run would satisfy the condition with a document nothing produced.

## What governing itself found

Eight things, none of which were visible before the tree existed. All are fixed or
registered. Seven came from the self-governance exercise; the eighth came from the relicence
that followed it, and is listed here because it is the same kind of hole.

| Finding | Where it landed |
|---|---|
| Three docstrings carried an example requirement id that resolves to nothing — `DOC-002` caught all three on the first run | fixed in `approve_edge.py`, `impact.py`, `validate_docs.py` |
| `approve_edge.py` still said the signed-commit binding "is not implemented" after 0.1.2 implemented it | fixed; the README bullet had been rewritten in the same release and the docstring had not |
| `CTX-002` globbed every `index.md` under the root, so `examples/` and `tests/fixtures/` reported 28 dangling ids from graphs this run never loads | `in_a_nested_project()` in `validate_context.py`, with a test |
| A risk accepted by a human is an approval under `acceptance_approval`, and no `APV-*` check collected it — the one approval in this repository was the one nothing verified | `approvals_in_scope()` now reads all three shapes, with a test |
| `perimeter_files()` walks the working tree, so every `.pyc` under `__pycache__/` was an in-perimeter source file | `**/__pycache__/**` added to the shipped default exclude list |
| Both YAML examples in `docs/guide/existing-project.md` were invalid — wrong top-level key, `state` for `status`, and an `acceptance_approval` shape the risk schema rejects outright | both corrected |
| `init_openup.py` seeds `src/AGENTS.md` into a repository whose code is not in `src/` | `RISK-0004`, deferred |
| Nothing read the `license:` field in any of the seven published manifests — `build_catalog.py` republishes it verbatim as display-only, so a stale one would have restated withdrawn terms in a public catalog with every test green | `NON-FR-DIST-0001` and `tests/test_license.py`, which reads `LICENSE` rather than hardcoding a licence name |

The first four were found by running the tool, not by reading the code. That is the argument
for doing this at all, and it is worth being precise about what it cost: one sitting, and an
output of 78 edges, 19 requirements, 14 WBS nodes and 6 risks — of which 65 edges are
assertions no check can confirm. `README.md` quotes that as the one measurement of governance
overhead SpecUP has, and says plainly that one project measured by its own author is not a
measurement.

## Key identifiers in this scope

- Business objective: `BUS-OBJ-0001`
- Requirements: `REQ-WBS-0001`, `REQ-RISK-0001`, `REQ-TRACE-0001`, `REQ-TRACE-0002`,
  `REQ-TRACE-0003`, `REQ-DONE-0001`, `REQ-READY-0001`, `REQ-GATE-0001`, `REQ-AUDIT-0001`,
  `REQ-VIEW-0001`, `REQ-CTX-0001`, `REQ-APV-0001`, `REQ-IMPACT-0001`, `REQ-INIT-0001`,
  `REQ-DOC-0001`
- Quality attributes: `NON-FR-CORE-0001`, `NON-FR-CORE-0002`, `NON-FR-DOCS-0001`,
  `NON-FR-DIST-0001`
- Test artifacts: `UNIT-CORE-0001`, `UNIT-DRV-0001`, `UNIT-APV-0001`, `UNIT-DOC-0001`,
  `UNIT-INIT-0001`, `UNIT-LIC-0001`
- Evidence: `EVID-0001` to `EVID-0007`
- Iterations: `ITER-C-01`, `ITER-C-02`, `ITER-C-03`

## Canonical stores

| Artifact | File | Generated view |
|---|---|---|
| Artifacts | `.specify/traceability/requirements.yaml` | — |
| Relations, asserted | `.specify/traceability/traceability.yaml` | `traceability.md`, `coverage.md` |
| Relations, derived | `.specify/traceability/derived.yaml` | machine-owned; never hand-edit |

```bash
python3 extensions/openup/scripts/python/derive_edges.py --write
python3 extensions/openup/scripts/python/render_views.py --write
```
