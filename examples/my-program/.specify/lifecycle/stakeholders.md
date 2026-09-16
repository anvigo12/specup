# Stakeholders — My Program

> **Answers** — who is accountable for what. The Inception artifact
> `stakeholders_identified` requires.
>
> **Does not answer** — who may approve a specific artifact. That is
> `.specify/governance/approval-matrix.md`, and `APV-003` reads the names out of that file,
> not this one.
>
> **Filled in badly when** — the "Who" column holds role names rather than people. The names
> below are placeholders in an example; in a real program they are people, and a job title
> standing in for a person is the thing that looks filled in and is not.
>
> **Checked by** — `stakeholders_identified` checks that this file **exists** and nothing
> more. The names that are enforced live in the approval matrix.
>
> **Authority** — the product owner.

Accountability does not transfer to an agent (s58). An AI performs bounded work; a named
human owns the decision.

## Roles

| Role | Who | Accountable for | Approves |
|---|---|---|---|
| Program owner | Dana Okonkwo | the program existing at all | the program plan |
| Product owner | Dana Okonkwo | scope, requirement baseline | `BUS-OBJ-*`, `REQ-*` |
| Architect | Sam Reyes | architecture baseline | `ADR-*`, architecture gate |
| Iteration owner | Priya Raman | iteration scope and closure | iteration gate |
| QA lead | Priya Raman | acceptance criteria, verification | `AC-*`, `TC-*` |
| Security owner | Jo Lindqvist | threat model, security exceptions | `SECURE-*`, security evidence |
| Release owner | Jo Lindqvist | release readiness | product release gate |

One person holds two roles in three rows above. That is normal in a small program and it is
better written down than pretended away — what matters to `APV-003` is that an approval names
somebody this table records, not that the table has seven different people in it.

## Human approval boundaries

Per s59, an agent may propose each of these and may authorize none:

- business scope approval
- requirement baseline
- architecture baseline
- high-risk acceptance
- breaking API changes
- security exceptions
- release approval

## Interested parties

Support team leads, who lose the manual greeting work and gain the escalations it currently
absorbs. They approve nothing and they should be in the room for `RISK-0002`.
