# Stakeholders

> Inception artifact (specup.md s11). Required by the Lifecycle Objectives gate.
>
> Accountability does not transfer to an agent (s58): an AI performs bounded work, a named
> human owns the decision. Every role below must resolve to a person or a standing group.

## Roles

| Role | Who | Accountable for | Approves |
|---|---|---|---|
| Product owner | | scope, requirement baseline | `BUS-OBJ-*`, `REQ-*` |
| Architect | | architecture baseline | `ADR-*`, architecture gate |
| Iteration owner | | iteration scope and closure | iteration gate |
| QA / test lead | | acceptance criteria, verification | `AC-*`, `TC-*` |
| Security owner | | threat model, security exceptions | `SECURE-*`, security evidence |
| Release owner | | release readiness | product release gate |

## Human approval boundaries

Per s59, these may not be decided by an agent:

- business scope approval
- architecture baseline approval
- requirement baseline
- high-risk acceptance
- breaking API changes
- security exceptions
- release approval

## Interested parties

Those affected by the outcome who do not approve artifacts.
