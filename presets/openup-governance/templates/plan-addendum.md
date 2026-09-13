## Lifecycle Position

State where this plan sits before describing what it does. The phase determines which
milestone this work is accountable to.

| Field | Source |
|---|---|
| Phase | `.specify/extensions/openup/openup-config.yml` → `lifecycle.phase` |
| Iteration | `lifecycle.iteration` |
| Exit gate | The gate whose `phase` matches — this plan's work must satisfy it |

## Architecture Decisions

Record every architecturally significant choice as `ADR-nnnn` in
`.specify/traceability/requirements.yaml`, with the architecture document under
`.specify/architecture/`. Significant means: expensive to reverse, constrains other work, or
a reviewer would want to know why.

For each decision, capture the alternatives considered and why they were rejected. An ADR
that records only the choice is a note, not a decision record — it cannot be re-evaluated
when the constraints change.

The Lifecycle Architecture gate requires an architecture document and every ADR at `APPROVED`
or beyond. An ADR left at `DRAFT` fails the gate, which is the correct signal that the
decision has not actually been taken.

## Uncertainty Becomes Risk

Major technical uncertainty must be resolved before high-volume implementation. Every
unresolved `NEEDS CLARIFICATION` in this plan is either resolved here or registered as a risk
with `probability`, `impact` and an owner.

A risk at or above the configured high-exposure threshold needs, in this same change:

- a WBS node with `kind: risk-mitigation` that references the risk id
- the risk's `mitigation` listing that node
- a verification reference showing how the reduction will be proved

Both ends are checked. Registering the risk without creating the work is how a risk register
becomes decoration.

Order the plan so that high-risk architectural validation and risk-reducing implementation
come before lower-risk feature work. Scaling implementation before the architecture is
established is the failure this phase exists to prevent.

## Contracts

For each interface this plan introduces or changes, produce the OpenAPI or AsyncAPI contract
and register it as `CONTRACT-<DOMAIN>-nnnn` with its file path. A contract lets consumer and
provider work in parallel; it also makes "does the implementation conform?" a question a
machine can answer.

A contract change without a corresponding requirement change is a silent interface break.
State which requirement drove it.

Every operation declares its failure responses, and each one is
`application/problem+json` carrying `type`, `title` and `status`, per
`.specify/governance/coding-rules.md`. An operation with only a 2xx response has not been
specified — it has been sketched. A `type` URI is part of the published interface, so changing
one is a breaking API change and needs the approval named in `approval-matrix.md`.

## Security

Plan against `.specify/governance/security-practices.md` rather than reviewing for security at
the end. Two gate conditions depend on it: `security_review_complete` closes this phase's
milestone, and `security_validation_passed` closes the release.

For this plan, state:

- which boundaries authenticate, and where authorization is checked against the resource
- what untrusted input is parsed into typed domain values, and where
- which limits are bounded — body size, page size, upload size, request rate
- what personal data is collected, and how long it is kept
- which third-party dependency touches authentication, cryptography, serialization or process
  execution, and therefore needs its own ADR

Every security finding is registered as a risk, with mitigation bound to WBS nodes. Accepting
one is a human decision, never an agent's.

## Decomposition

This plan is decomposed by `/speckit.openup.wbs` into L4–L7 nodes. Every L7 task carries an
owner, an iteration, and at least one requirement — not as convention but as a schema
constraint. Plan the work so that is achievable: a task that serves no requirement is either
undocumented scope or unnecessary work.

## Checks

```bash
python3 .specify/extensions/openup/scripts/python/validate_wbs.py --json
python3 .specify/extensions/openup/scripts/python/validate_risk.py --json
python3 .specify/extensions/openup/scripts/python/evaluate_gate.py --gate <phase gate> --json
```

Fix the graph when these fail. Do not lower a threshold, widen the traceability perimeter, or
create an evidence file to make a check pass.
