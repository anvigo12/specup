---
description: "Evaluate a lifecycle gate against evidence and report which conditions fail"
---

# Lifecycle Gate

Evaluate a milestone gate. Every condition is a real check against the filesystem, so the
verdict is reproducible by anyone who runs the same command (specup.md s55).

## User Input

```text
$ARGUMENTS
```

A gate id. Empty means the gate for the current `lifecycle.phase`.

## Gates

| Gate | Phase | Asks |
|---|---|---|
| `GATE-LIFECYCLE_OBJECTIVES` | Inception | is the scope, ownership, and initial risk picture real? |
| `GATE-LIFECYCLE_ARCHITECTURE` | Elaboration | is the architecture baselined and are the high risks handled? |
| `GATE-INITIAL_OPERATIONAL_CAPABILITY` | Construction | is it built, covered, and free of orphans? |
| `GATE-PRODUCT_RELEASE` | Transition | can it be released and operated? |

Conditions are declared per gate in `.specify/extensions/openup/openup-config.yml` and
implemented in `evaluate_gate.py`. A condition named in config with no implementation
**fails** — it is never skipped.

## Execution

```bash
python .specify/extensions/openup/scripts/python/evaluate_gate.py --gate <GATE-ID> --json
```

Exit codes: `0` pass, `1` fail, `2` the graph could not be loaded.

## Reporting

Report **every** condition with its status and message, not just the failures — a gate report
that lists only problems hides what was actually checked. For each failure, state what would
satisfy it, in terms of a file to write or a link to add.

## What you must not do

This is the command an agent is most tempted to route around. All of the following are
prohibited, and each defeats the purpose of the gate rather than passing it:

- **Do not declare a gate passed.** Report what the script returned. "Architecture looks good" is precisely the assertion s30 forbids.
- **Do not edit `openup-config.yml` to remove a failing condition,** or lower a threshold, to make a gate pass. If a threshold is genuinely wrong, say so, explain why, and let the user decide — as a separate, visible change.
- **Do not write evidence files to satisfy a condition.** `security-review.json` means a security review happened. Creating it because a gate wants it is fabricating a record. If the review has not happened, the correct output is "this gate fails because no security review has been done".
- **Do not mark artifacts `APPROVED` or `BASELINED` to clear a condition.** Approval is a human act (s59).

Absence of evidence is not evidence. A failing gate is useful information; a gate made to pass is not.

## Overriding

A human may proceed past a failing gate — that is their authority, not yours. When it
happens, record it: write the gate verdict JSON to `.specify/evidence/` alongside who
decided and why. An undocumented override is indistinguishable from a gate that never ran.

## After a pass

Report it plainly and hand off to `/speckit.openup.phase` to advance, which will re-evaluate
before writing.
