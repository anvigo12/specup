## Governed Requirement Identity

Every requirement in this specification is a node in the traceability graph, so each needs an
identity that survives editing and an owner who is accountable for it.

Register each one in `.specify/traceability/requirements.yaml`. Requirements written only in
prose here are invisible to the validators and will surface as gaps at the next gate.

| Field | Rule |
|---|---|
| `id` | `REQ-<DOMAIN>-nnnn` for functional, `NON-FR-<DOMAIN>-nnnn` for quality attributes. Four digits, zero-padded. |
| `owner` | A named person or standing group. Not "the team". |
| `priority` | `critical` \| `high` \| `medium` \| `low` |
| `status` | Enters at `DRAFT`. Only a human advances it. |
| refines | The `BUS-OBJ-nnnn` this requirement serves |

A requirement that refines no business objective is either unnecessary or evidence of an
undocumented objective. Say which; do not quietly leave it unlinked.

## Acceptance Criteria

Each requirement needs at least one acceptance criterion, registered as
`AC-<DOMAIN>-nnnn-nnnn`. A criterion is a single checkable condition, written so that two
people would agree on whether it holds.

- Prefer the negative and boundary cases. A criterion set that only describes the happy path
  has not specified the requirement.
- A quality attribute needs a measurable target and the conditions it holds under —
  "fast" is not a criterion; "p95 under 200ms at 500 rps" is.
- Every criterion becomes at least one Gherkin scenario (`/speckit.openup.behavior`). One
  with no scenario is an unverified requirement wearing a checkmark.

## Interfaces

If this feature exposes or consumes an API, register the contract as
`CONTRACT-<DOMAIN>-nnnn` with the path to its OpenAPI or AsyncAPI file. Behavior and contract
are separate questions: Gherkin asks whether the system does what the business expects, the
contract asks whether the implementation conforms to the agreed interaction.

## What This Specification Must Not Do

- Do not invent requirements to fill a template section. An empty section that says "none
  identified" is information; a fabricated requirement is noise that will be traced,
  decomposed and implemented.
- Do not assign an owner who has not agreed to own it. An unowned requirement failing the
  Inception gate is the correct outcome; a fabricated owner hides the problem.
- Do not record a requirement as `APPROVED`. Approval is a human act.

## Before This Spec Is Considered Complete

```bash
python3 .specify/extensions/openup/scripts/python/validate_trace.py --json
```

Every requirement should reach an implementing WBS node and a verifying acceptance criterion.
At specification time the implementation side will legitimately be empty — the point is to
see which requirements are already orphaned, not to force the number green.
