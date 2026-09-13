---
description: "Build, derive, and validate the bi-directional traceability graph"
---

# Traceability

Maintain `.specify/traceability/traceability.yaml` — the relation store that makes both
"what implements this requirement?" and "what requirements does this file affect?" answerable
(specup.md s20–s22).

## User Input

```text
$ARGUMENTS
```

An artifact id to trace, a scope to rebuild, or empty to derive what can be derived and
report coverage.

## Two rules that carry the whole design

**1. Store each edge once, in active voice.** The inverse is derived at load time. Never write
both directions: two hand-maintained directions are two things that can disagree, and
disagreement is what traceability exists to prevent.

**2. Be honest about provenance.** Every edge declares how it is known:

| provenance | Meaning | When to use it |
|---|---|---|
| `derived` | Recomputed from the filesystem by a stated rule. Requires `derived_by`, and the rule is re-run to check it. | Anything mechanically recoverable: test-file naming, codegen output, Gherkin tags |
| `asserted` | Claimed by you or the author. Not reproducible. | Judgment links: which requirement a WBS node implements |
| `approved` | Asserted, then signed off by a named human. Never hand-written — see below. | Baseline-level edges on `BASELINED`+ requirements |

To record an approval, run the tool; the required `approved_endpoints_hash` cannot be produced
by hand, and a wrong one downgrades the edge on the next run:

```bash
python3 .specify/extensions/openup/scripts/python/approve_edge.py \
  --from REQ-AUTH-0014 --relation refines --to BUS-OBJ-0017 --by product-owner
```

`TRC-013` recomputes that hash from the endpoints as they now stand. If either endpoint has been
edited since, the edge is WARNed and drops out of `approved_verified` — the count
`traceability_final` actually scores — until someone approves it again. An approval binds the
*content* it was given for; it does not prove a human ran the command.

This exists because you are writing both the code and the proof that it was traced. Marking a
judgment call `derived` to make the audit look better defeats the only mechanism that
distinguishes evidence from assertion — and `TRC-010` now re-runs the named rule and fails the
edge when it disagrees, so the relabelling costs a failing graph rather than buying a better
score. **When in doubt, mark it `asserted`.**

## Closed vocabulary

A relation outside this set is rejected (`TRC-000`), and each has a legal domain and range
(`TRC-003`):

`refines` · `contains` · `implements` · `verifies` ·
`executes` · `tests` · `conforms-to` · `validates` · `mitigates` · `evidences` ·
`depends-on` · `belongs-to` · `approves` · `supersedes`

The passive forms the design document used in places — `implemented-by`, `executed-by`,
`satisfies` — are **not** stored. Use the active form; the inverse is free.

## Deriving

**Never hand-write a `derived` edge.** Derived edges live in `.specify/traceability/derived.yaml`,
which `derive_edges.py --write` rewrites in full from the rules below:

```bash
python .specify/extensions/openup/scripts/python/derive_edges.py --write
```

| Rule | Produces | |
|---|---|---|
| `gherkin-tag-scan` | `SCEN-*` → `executes` → `AC-*`, from `@` tags in `.feature` files | implemented |
| `test-file-naming-convention` | `UNIT-*`/`TC-*`/`INTG-*` → `tests` → the file its `source` is named after | implemented |
| `wbs-iteration-field` | WBS node → `belongs-to` → iteration, from the node's `iteration` field | implemented |
| `openapi-operation-scan` | source file → `conforms-to` → `CONTRACT-*` | **not implemented** |
| `evidence-manifest-scan` | `EVID-*` → `evidences` → WBS node / risk / gate | **not implemented** |

An implemented rule is re-run by `TRC-010`, so a `derived` edge it does not reproduce fails.
An edge naming one of the two unimplemented rules cannot be reproduced at all: it is reported
as **unverified** and does not count as evidence at the release gate. Do not add more of them —
if a rule is not implemented, the honest label is `asserted`.

Leave `asserted` and `approved` edges alone; those live in the hand-maintained stores.

## Execution

```bash
python .specify/extensions/openup/scripts/python/validate_trace.py --json
```

| Check | Meaning |
|---|---|
| `TRC-002` | an endpoint does not resolve — a dangling id or a deleted file |
| `TRC-003` | the relation is illegal for those endpoint types |
| `TRC-005/006` | a requirement has nothing implementing or verifying it |
| `TRC-007` | an in-perimeter source file is not reachable from any requirement |
| `TRC-008` | orphans (s54) |
| `TRC-009` | an edge on a baselined requirement is below the required provenance |
| `TRC-010` | an edge claims a rule that does not reproduce it, or a rule that does not exist |
| `TRC-011` | a rule produces an edge no store declares — run `derive_edges.py --write` |
| `TRC-012` | an acceptance criterion has no scenario executing it (s24) |
| `TRC-013` | an approved edge no longer matches what was approved — WARN, and it stops counting as evidence until re-approved |

`TRC-011` is the only one of these with a mechanical fix: regenerate. `TRC-010` never is —
it means a claim was wrong, so correct the claim or the filesystem, never the label.

If `TRC-007` fails for files that should not be governed, fix the **perimeter** in
`openup-config.yml` rather than inventing edges to silence it.

## Generated views

`traceability.md` and `coverage.md` are generated from the YAML. Do not write either by hand:

```bash
python3 .specify/extensions/openup/scripts/python/render_views.py --write
```

`coverage.md` carries the provenance mix alongside the coverage figures, because a coverage
number without it overstates what is actually known.

## Reporting

Report forward coverage, backward coverage, orphans, and the derived/asserted/approved split.
If most edges are `asserted`, say so directly: coverage is high but largely unverified.
