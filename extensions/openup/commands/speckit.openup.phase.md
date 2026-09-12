---
description: "Show or advance the OpenUP phase; advancing requires the phase gate to pass"
---

# OpenUP Phase

Report the current lifecycle position, or advance it. Advancing is the consequential half:
a phase transition is a milestone, and a milestone that can be declared without evidence is
decoration (specup.md s55).

## User Input

```text
$ARGUMENTS
```

Empty means **report**. A phase name (`INCEPTION`, `ELABORATION`, `CONSTRUCTION`, `TRANSITION`)
means **advance to it**.

## Phases and their questions

| Phase | Question | Exit gate |
|---|---|---|
| Inception | Should we build this? | `GATE-LIFECYCLE_OBJECTIVES` |
| Elaboration | Can we build it? | `GATE-LIFECYCLE_ARCHITECTURE` |
| Construction | Can we build it incrementally and verify each increment? | `GATE-INITIAL_OPERATIONAL_CAPABILITY` |
| Transition | Can it be released and operated safely? | `GATE-PRODUCT_RELEASE` |

## Reporting

Read `lifecycle.phase` and `lifecycle.iteration` from
`.specify/extensions/openup/openup-config.yml`, then run the audit:

```bash
python .specify/extensions/openup/scripts/python/audit.py --json
```

Report the phase, the iteration, the gate for that phase, and its current status.

## Advancing

1. Identify the **exit gate of the current phase** from the table above — not the gate of the
   phase being entered. You leave a phase by satisfying its own milestone.
2. Evaluate it:

   ```bash
   python .specify/extensions/openup/scripts/python/evaluate_gate.py --gate <CURRENT_PHASE_GATE> --json
   ```

3. If the gate **fails**, do not change the phase. Report each failing condition and what
   would satisfy it. Offer to fix them. Never edit `lifecycle.phase` to make a gate
   irrelevant — that is the one move this command exists to prevent.
4. If the gate **passes**, confirm with the user before writing. A phase transition is a
   human approval boundary (s59); the gate passing is a precondition for asking, not a
   substitute for the answer.
5. On confirmation, set `lifecycle.phase` in the config and reset `lifecycle.iteration` to
   the first iteration of the new phase (`ITER-<letter>-01`), or `null` if none exists yet.
6. Record the transition in `.specify/evidence/` with the gate verdict JSON, so the decision
   and the evidence it rested on stay together.

## Skipping backwards

Moving to an earlier phase is allowed and needs no gate — it is an admission that the
previous milestone was not really met. Say so plainly in the report and note which gate
conditions have since regressed.
