# Governance Index — risks

> The context map for this directory.

## Purpose

What could go wrong, sized, and pointed at work. `risk-register.md` is a generated view and
is absent here for the same reason as `wbs.md`.

## Key identifiers

| Id | Exposure | State | Why it is where it is |
|---|---|---|---|
| `RISK-0001` | 0.63 | open, mitigating work planned | above the 0.40 threshold, so `validate_risk.py` requires it to point at real work **and** to declare how the reduction will be proved. It does the first and not the second |
| `RISK-0002` | 0.18 | open | below the threshold, so it may sit open with neither, and `TRC-008` does not call it an orphan |

`RISK-0001` is why `all_high_risks_have_mitigation` fails. Adding a `verification:` entry
naming a test nobody has designed would turn the gate green and make the register false.
