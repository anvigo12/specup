# Risk Register Skill

> Capability contract (specup.md s8). `AGENTS.md` says **what rules must I obey**; this file
> says **how do I perform this activity**. Keep the two separate — merging them produces a
> document that is followed for neither purpose.
>
> **Done badly when** — the numbers are chosen to land under the threshold. The arithmetic is
> checked and the inputs are not, so `probability: 0.3` on something nobody measured passes
> every check here. The other symptom is a register that only ever shrinks, because risks get
> closed on the strength of a decision having been taken rather than on evidence exposure fell.
>
> **Checked by** — `RISK-000` through `RISK-007`. **Nothing checks whether a probability is
> true.** Reassess from what the iteration actually taught, and expect some numbers to go up.

## Purpose

Maintain a risk register that reaches into the plan as real work, rather than a list of worries nobody acts on.

## Inputs

- the architecture and its open questions
- requirements, especially non-functional ones
- what the last iteration actually learned
- `.specify/wbs/wbs.yaml`

## Rules

- **Exposure is computed:** `exposure = probability × impact`. Typing a different number fails `RISK-001`; the same for `residual_exposure`.
- A risk at or above the high threshold needs at least one mitigation WBS node **and** a verification reference, before the Elaboration gate.
- A mitigation node must be `kind: risk-mitigation` and reference the risk back. The link has to agree from both ends (`RISK-006`).
- Residual exposure must be strictly below current exposure — 'mitigated' with unchanged exposure is a no-op.
- Reassess from what was learned, not from optimism. An iteration that changed no estimate usually means the reassessment was skipped.
- **Accepting a risk is a human decision** and needs a recorded approval (`RISK-000`).

## Output

- `.specify/risks/risk-register.yaml` — canonical
- `.specify/risks/risk-register.md` — **generated**

## Validation

```bash
python3 .specify/extensions/openup/scripts/python/validate_risk.py --json
```
