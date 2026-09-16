# Stakeholders

> **Answers** — who is accountable for what, and which decisions may not be taken without one
> of them. The Inception artifact the Lifecycle Objectives gate requires (specup.md s11).
>
> **Does not answer** — who may approve a specific artifact in practice. That is
> `.specify/governance/approval-matrix.md`, and `APV-003` reads the names out of it, not out
> of this file. Keep the two in step; they are separate because one describes people and the
> other describes decisions.
>
> **Filled in badly when** — the "Who" column holds role names rather than people. "Architect"
> approving the architecture is a tautology. A standing group is fine; a job title standing in
> for a person is the thing that looks filled in and is not.
>
> **Checked by** — `stakeholders_identified` checks that this **file exists** and nothing more.
> The names that are actually enforced live in the approval matrix, where `APV-000` fails if
> nobody is named and `APV-003` fails an approval under a name that is not there.
>
> **Authority** — the product owner. Changing who approves what is itself a decision, not an
> edit.
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
