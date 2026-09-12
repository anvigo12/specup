---
description: "Open, review, or close an iteration within the current phase"
---

# OpenUP Iteration

Manage the iteration — the unit that keeps Construction genuinely iterative rather than one
large generation run (specup.md s38).

## User Input

```text
$ARGUMENTS
```

- `open` — start a new iteration in the current phase
- `review` — report progress and risk movement for the current iteration
- `close` — evaluate the iteration gate and close it
- empty — `review`

## Iteration ids

`ITER-<phase letter>-<NN>`, where the letter is `I`, `E`, `C`, or `T`. An iteration's letter
must match the phase of every WBS node assigned to it; `validate_wbs.py` check `WBS-010`
enforces that.

## Open

1. Read `lifecycle.phase` from `.specify/extensions/openup/openup-config.yml`.
2. Compute the next id for that phase.
3. Register it in `.specify/traceability/requirements.yaml` as an `iteration` artifact at
   status `DRAFT`, with an owner.
4. **Select the work, risk first.** Run:

   ```bash
   python .specify/extensions/openup/scripts/python/validate_risk.py --json
   ```

   Order candidate WBS nodes so that architectural validation and high-exposure risk
   mitigation come before lower-risk feature work (s39). Present the ordering and the reason
   for it; let the user adjust.
5. Assign the selected L7 nodes to the iteration by setting their `iteration` field, then
   set `lifecycle.iteration` in the config.
6. Check each selected task against the Definition of Ready in
   `.specify/governance/definition-of-ready.md`. Report any task that is not ready and why.
   A task that is not ready should not be in the iteration.

## Review

Run the audit and report, for this iteration only:

- WBS nodes assigned, and their status breakdown
- requirements touched, and their coverage
- risks whose exposure changed since the iteration opened
- evidence produced

Report movement, not just totals. "Three tasks done" says less than "RISK-0007 exposure fell
from 0.54 to 0.10, evidenced by EVID-0001".

## Close

1. Evaluate the iteration's work:

   ```bash
   python .specify/extensions/openup/scripts/python/audit.py --json
   ```

2. Every L7 node in the iteration must satisfy the Definition of Done
   (`.specify/governance/definition-of-done.md`): implementation, tests, traceability
   updated, evidence recorded. `status: done` without evidence is not done — say so rather
   than accepting it.
3. **Reassess risk.** For each risk touched, update `residual_probability` and
   `residual_impact` from what was actually learned. An iteration that changed no risk
   estimate usually means the reassessment was skipped, not that nothing was learned.
4. Carry unfinished work forward explicitly: move it to the next iteration rather than
   leaving it assigned to a closed one.
5. Set the iteration artifact's status to `ACCEPTED` and report what closed, what carried,
   and how risk moved.
