# Requirements Skill

> Capability contract (specup.md s8). `AGENTS.md` says **what rules must I obey**; this file
> says **how do I perform this activity**. Keep the two separate — merging them produces a
> document that is followed for neither purpose.

## Purpose

Register governed requirements with stable ids, owners, and a path to a business objective.

## Inputs

- the vision and business objectives
- stakeholder input
- the specification documents

## Rules

- Ids are stable for the life of the artifact — they are graph edges. **Supersede, never rename.**
- `REQ-<DOMAIN>-nnnn` for functional, `NON-FR-<DOMAIN>-nnnn` for non-functional. Zero-padded to four digits.
- Every requirement needs an `owner` and a `refines` edge toward a business objective.
- Every requirement enters at `DRAFT`. Only a human advances it (s31).
- A requirement with nothing implementing or verifying it fails `TRC-005`/`TRC-006`. Register the requirement and the work together, or the graph records intent with no means of achieving it.
- Write a requirement that can be verified. If you cannot state how it would be checked, it is a wish.
- Write it in Simplified Technical English, per `.specify/governance/language-rules.md`. One statement per requirement, at most 25 words, "must" for an obligation and "can" for a possibility. Never "should", never "and/or", never "etc." A requirement two people read differently still registers and still traces — nothing downstream can detect the disagreement.
- If the requirement anticipates a failure, that failure gets an RFC 9457 `type` URI, and the same URI names it in the acceptance criterion, the scenario and the contract (`.specify/governance/coding-rules.md`).

## Output

- `.specify/traceability/requirements.yaml`, or `specs/<feature>/artifacts.yaml`

## Validation

```bash
python3 .specify/extensions/openup/scripts/python/validate_trace.py --json
```
