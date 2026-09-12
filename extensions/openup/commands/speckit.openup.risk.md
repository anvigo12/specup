---
description: "Create or update the risk register and bind high-exposure risks to mitigation work"
---

# Risk Register

Maintain `.specify/risks/risk-register.yaml` so that risk drives work rather than describing it.

## User Input

```text
$ARGUMENTS
```

A risk to record, a risk id to update, or empty to review the register and report exposure.

## The rule that makes this real

```
Risk -> Mitigation (WBS) -> Implementation -> Verification -> Evidence -> Residual Risk
```

A risk at or above `risk.high_exposure_threshold` (default `0.40`) **must** have at least one
mitigation WBS node and at least one verification reference, or `GATE-LIFECYCLE_ARCHITECTURE`
fails. A register whose entries point nowhere is the passive documentation s19 rejects.

## Recording a risk

1. Assign the next `RISK-nnnn`.
2. Estimate `probability` and `impact` in 0..1. State the basis for each — an unexplained 0.6 is a guess wearing a number.
3. Compute `exposure = probability x impact`. Never hand-adjust it; `RISK-001` rejects a stored value that disagrees.
4. Set `category`, `phase_identified`, `owner`. The owner is a named human or standing group.
5. If exposure is at or above the threshold, create the mitigation work **now**, in the same
   change:
   - add a WBS node with `kind: risk-mitigation` that lists this risk id
   - list that node under the risk's `mitigation`
   - add a verification reference (`TC-*`, `UNIT-*`, `INTG-*`, `MICROCKS-TEST-*`, or `EVID-*`)

   Both ends are checked (`RISK-006`). One end alone is not a link.

## Updating exposure

- Update `probability`/`impact` when evidence changes what you know, and record the change
  and its reason in `history`.
- Set `residual_probability`/`residual_impact` only from evidence that mitigation worked.
  Residual exposure must be strictly below current exposure (`RISK-003`) — otherwise the
  mitigation did nothing and saying otherwise is worse than leaving it open.
- `status: mitigated` or `closed` requires mitigation, verification, residual values, and
  evidence (`RISK-007`).
- `status: accepted` requires `acceptance_approval` with a named human and a timestamp.
  Accepting a live risk is a human decision (s59). If the user has not actually approved it,
  do not write the field — ask.

## Execution

```bash
python .specify/extensions/openup/scripts/python/validate_risk.py --json
```

## Reporting

Report by exposure, highest first, showing for each: id, title, exposure, status, owner,
mitigation nodes, and whether verification exists. Call out separately:

- risks above the threshold with no mitigation — these block the architecture gate
- risks whose exposure has not been reassessed in more than one iteration
- risks marked `mitigated` with no evidence

## Generated view

`risk-register.md` is a generated view. Regenerate it; never hand-edit it.
