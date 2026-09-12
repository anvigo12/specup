---
description: "Create or update the seven-level Work Breakdown Structure and regenerate wbs.md"
---

# Work Breakdown Structure

Build or extend the seven-level WBS in `.specify/wbs/wbs.yaml`, then validate it.

## User Input

```text
$ARGUMENTS
```

A feature, capability, or WBS id to decompose. Empty means: report the current WBS and
propose the next decomposition.

## The seven levels

The id encodes the level — the number of dotted segments **is** the level, so `WBS-1.2.3` is
always L3. These are levels of scope resolution, not seven levels of prose (s15, s65).

| Level | Meaning | Reasoning boundary |
|---|---|---|
| L1 | Program / Product | strategic context |
| L2 | OpenUP Phase | lifecycle objective |
| L3 | Iteration | near-term delivery goal |
| L4 | Capability / Feature | functional scope |
| L5 | Requirement / User Story | expected behavior |
| L6 | Engineering Work Package | engineering slice |
| L7 | Executable Task | executable unit |

## Prerequisites

Read, in this order — stop and say so if any is missing:

1. `.specify/extensions/openup/openup-config.yml` — phase, iteration, `depth_policy`
2. `.specify/traceability/requirements.yaml` — the requirements to decompose
3. `.specify/risks/risk-register.yaml` — high-exposure risks that need mitigation nodes
4. `.specify/wbs/wbs.yaml` — what already exists
5. The feature's `plan.md` and `spec.md` if this follows `/speckit.plan`

## Rules

- **Every L7 node needs `owner`, `iteration`, and at least one requirement.** Not conventions — the schema rejects the node otherwise.
- **`kind` drives the rules.** `risk-mitigation` requires `risks`; `test` requires `acceptance`. Set it deliberately.
- **A risk-mitigation node must be listed by its risk, and list that risk back.** The link is checked from both ends.
- **Depth.** Under `depth_policy: semantic` a leaf may stop above L7 if it declares a `terminal_reason` saying why further decomposition adds nothing. Under `strict`, every leaf must be L7. L1–L3 may never be leaves under either policy.
- **Decompose by risk first.** High-exposure risk mitigation and architectural validation come before lower-risk feature work (s39).
- **Do not pad.** If a work package genuinely has one task, say so in `terminal_reason` rather than inventing three. Seven levels of narrative is the failure mode s65 warns about.

## Execution

After every edit:

```bash
python .specify/extensions/openup/scripts/python/validate_wbs.py --json
```

Fix every `FAIL` before reporting success. The common ones:

| Check | Cause |
|---|---|
| `WBS-001` | `level` disagrees with the id's segment count |
| `WBS-002` | `parent` is not the id minus its last segment, or does not exist |
| `WBS-004` | a leaf above L7 with no `terminal_reason`, or a structural leaf |
| `WBS-005/6/7` | a referenced requirement, risk, or acceptance criterion is not registered |
| `WBS-009` | a dependency cycle |
| `WBS-010` | an iteration letter that disagrees with the node's phase |

## Generated view

`wbs.md` is a **generated** view of `wbs.yaml` (s47). Regenerate it from the YAML; never
hand-edit it, and never let the two drift. Render the tree with id, name, owner, iteration,
status, and linked requirement and risk ids.

## Then

Add the new edges to the traceability graph with `/speckit.openup.trace`. A WBS node that
implements a requirement is not traced until that edge exists.
