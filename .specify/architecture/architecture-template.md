# Architecture

> **Answers** — what the system is made of, where its boundaries are, and which decisions are
> already taken. It is the document the Elaboration gate's `architecture_baselined` condition
> looks for at `.specify/architecture/architecture.md`.
>
> **Does not answer** — *why* any single decision went the way it did. That is an ADR, one per
> decision, registered as `ADR-nnnn`. A section here that argues a case is an ADR in the wrong
> file, and it will be edited by whoever touches the diagram next.
>
> **Filled in badly when** — it describes the system as intended rather than as built, and
> nothing in the repository disagrees with it, because nothing here is machine-checked. The
> specific symptom: components with no owning requirement, and boundaries that no contract
> under `specs/*/contracts/` corresponds to. If you cannot name the `REQ-` behind a component,
> the component is either unnecessary or the requirement was never written.
>
> **Checked by** — `architecture_baselined` checks that this file **exists** and that every
> registered ADR is `APPROVED` or beyond. It does not read it. `CTX-002` checks that every id
> named in this directory's `index.md` resolves. **Nothing checks the content of this
> document** — say so to anyone who treats a passing gate as a review.
>
> **Authority** — the architect named in `.specify/governance/approval-matrix.md`. Baselining
> the architecture is one of the decisions specup.md §59 reserves for a named human.
>
> Copy this file to `architecture.md` in this directory and fill it in. The gate does not
> accept the template: while only `architecture-template.md` exists, `architecture_baselined`
> reports "no architecture document found", and that is the correct report.

## Scope

What this architecture covers, and what it deliberately does not. A boundary omitted here is
one that gets crossed by accident later.

## Context

The system in its environment: who uses it, what it depends on, what depends on it.

## Components

Every component names the requirement it exists to serve. A component with no `REQ-` is the
finding.

| Component | Responsibility | Serves | Owner |
|---|---|---|---|
| | | `REQ-…` | |

## Boundaries and contracts

Each boundary someone else calls across has a contract under `specs/*/contracts/`, registered
as `CONTRACT-…`. The Elaboration gate's `critical_contracts_defined` checks that a registered
contract's `source` file exists — it does **not** open it, so a contract file that exists and
says nothing passes.

| Boundary | Contract | Registered as |
|---|---|---|
| | | `CONTRACT-…` |

## Quality attributes

The non-functional requirements this architecture is shaped by, with the measurable target
each one carries. An attribute with no number is a preference.

| Attribute | Target | Id |
|---|---|---|
| | | `NON-FR-…` |

## Decisions

One row per registered ADR. This is an index, not a summary: a summary here and an ADR there
are two documents that will disagree.

| Id | Decision | Status |
|---|---|---|
| `ADR-0001` | | DRAFT |

## Known weaknesses

What this architecture is bad at, and what it would cost to fix. The section people skip, and
the one a reviewer reads first. If it is empty, the architecture has not been reviewed — it
has been described.
