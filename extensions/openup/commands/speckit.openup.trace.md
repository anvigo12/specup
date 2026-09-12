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
| `derived` | Recomputed from the filesystem by a stated rule. Requires `derived_by`. | Anything mechanically recoverable: test-file naming, imports, codegen output, Gherkin tags |
| `asserted` | Claimed by you or the author. Not reproducible. | Judgment links: which requirement a WBS node implements |
| `approved` | Asserted, then signed off by a named human. Requires `approval` and `approved_endpoints_hash`. | Baseline-level edges on `BASELINED`+ requirements |

This exists because you are writing both the code and the proof that it was traced. Marking a
judgment call `derived` to make the audit look better defeats the only mechanism that
distinguishes evidence from assertion. **When in doubt, mark it `asserted`.**

## Closed vocabulary

A relation outside this set is rejected (`TRC-000`), and each has a legal domain and range
(`TRC-003`):

`refines` · `contains` · `decomposes-to` · `implements` · `modifies` · `verifies` ·
`executes` · `tests` · `conforms-to` · `validates` · `mitigates` · `evidences` ·
`depends-on` · `belongs-to` · `approves` · `supersedes`

The passive forms the design document used in places — `implemented-by`, `executed-by`,
`satisfies` — are **not** stored. Use the active form; the inverse is free.

## Deriving

Recompute `derived` edges rather than hand-writing them. Each needs a `derived_by` naming its
rule, so it can be reproduced or invalidated:

| Rule | Produces |
|---|---|
| `gherkin-tag-scan` | `SCEN-*` → `executes` → `AC-*`, from `@` tags in `.feature` files |
| `test-file-naming-convention` | `UNIT-*` → `tests` → source file |
| `openapi-operation-scan` | source file → `conforms-to` → `CONTRACT-*` |
| `task-modifies-closure` | source file → `implements` → requirement, via the task that modifies it |
| `wbs-iteration-field` | WBS node → `belongs-to` → iteration |
| `evidence-manifest-scan` | `EVID-*` → `evidences` → task / risk / gate |

Regenerate derived edges on every run; leave `asserted` and `approved` edges alone.

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

If `TRC-007` fails for files that should not be governed, fix the **perimeter** in
`openup-config.yml` rather than inventing edges to silence it.

## Generated views

`traceability.md` and `coverage.md` are generated from the YAML. Include the provenance mix
in `coverage.md` — a coverage number without it overstates what is actually known.

## Reporting

Report forward coverage, backward coverage, orphans, and the derived/asserted/approved split.
If most edges are `asserted`, say so directly: coverage is high but largely unverified.
