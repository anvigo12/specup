# WBS Generation Skill

> Capability contract (specup.md s8). `AGENTS.md` says **what rules must I obey**; this file
> says **how do I perform this activity**. Keep the two separate — merging them produces a
> document that is followed for neither purpose.
>
> **Done badly when** — the tree is deep and the leaves are narrative. Seven levels of heading
> with nothing executable at the bottom is a document, not a plan (s65). The opposite failure
> is a leaf at L1-L3, which means the plan is empty rather than concise.
>
> **Checked by** — `WBS-001` through `WBS-011`. What none of them check is whether this is the
> right work: every id can resolve, every level can agree, and the plan can still be for a
> system nobody asked for.

## Purpose

Generate and maintain the seven-level OpenUP Work Breakdown Structure.

## Inputs

- `.specify/extensions/openup/openup-config.yml` — phase, iteration, depth policy
- `.specify/traceability/requirements.yaml` — what the work must serve
- `.specify/risks/risk-register.yaml` — what the work must reduce
- the plan and architecture documents

## Rules

- **The id encodes the level.** `WBS-1.2.3` is L3 because it has three segments. Never declare a `level:` that disagrees with the id — that is the error specup.md's own s17 example makes.
- L1 Program · L2 Phase · L3 Iteration · L4 Capability · L5 Requirement · L6 Work Package · L7 Executable Task.
- **L7 is the task.** There is no separate `TASK-nnnn`.
- Every L7 node needs an owner, an iteration, and at least one requirement.
- A leaf may stop above L7 only if it declares a `terminal_reason` — and only under `depth_policy: semantic`. L1–L3 may never be leaves.
- A `risk-mitigation` node references its risk; a `test` node references its criteria.
- Do not create depth for its own sake (s65). Seven levels of narrative is not a plan.

## Output

- `.specify/wbs/wbs.yaml` — canonical
- `.specify/wbs/wbs.md` — **generated**, never hand-written

## Validation

```bash
python3 .specify/extensions/openup/scripts/python/validate_wbs.py --json
python3 .specify/extensions/openup/scripts/python/render_views.py --write
```
