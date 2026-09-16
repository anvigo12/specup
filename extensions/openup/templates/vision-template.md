# Vision

> **Answers** — "Should we build this?" (specup.md s11). The Inception artifact the Lifecycle
> Objectives gate requires.
>
> **Does not answer** — how it will be built, or what it will cost. A vision that names a
> technology has taken a decision an ADR should take later, on evidence nobody has yet.
>
> **Filled in badly when** — "Explicitly out of scope" is empty or generic. Every other
> section here can be written from enthusiasm; that one cannot, and it is the only thing that
> will let anyone tell, months later, that the scope moved rather than that it was always
> this. The second symptom: business objectives with no measure, which cannot be missed and
> therefore cannot be met.
>
> **Checked by** — `vision_present` checks that this **file exists**. `requirements_have_owners`
> checks the `BUS-OBJ-*` and `REQ-*` you register in
> `.specify/traceability/requirements.yaml`. **Nothing reads this prose.** The objectives are
> governed because they are registered artifacts; the argument around them is not.
>
> **Authority** — the product owner named in `.specify/governance/approval-matrix.md`. Business
> scope is one of the decisions specup.md s59 reserves for a named human, and it enters at
> `DRAFT`: generated does not mean approved.

## Problem

What is wrong today, for whom, and what it costs.

## Proposed outcome

What is true once this exists. State it as an observable change, not a feature list.

## Scope

**In scope.**

**Explicitly out of scope.** The more honest this section, the more useful the gate.

## Business objectives

Each gets a `BUS-OBJ-nnnn` id in `.specify/traceability/requirements.yaml`; every
requirement must eventually `refines` one of them.

| Id | Objective | Measure of success |
|---|---|---|
| BUS-OBJ-0001 | | |

## Key assumptions

Assumptions that, if wrong, invalidate the case. Each should have a matching entry in the
risk register.

## Feasibility

Why this is achievable with the people, time, and technology available.
