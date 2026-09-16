# Vision — My Program

> **Answers** — "Should we build this?" The Inception artifact `vision_present` requires.
>
> **Does not answer** — how it will be built. No technology appears below, and that is
> deliberate: at Inception the evidence for that choice does not exist yet, and a vision that
> names a stack has taken an architecture decision without an ADR to argue it.
>
> **Filled in badly when** — "Explicitly out of scope" is empty. Every other section can be
> written from enthusiasm; that one cannot.
>
> **Checked by** — `vision_present` checks that this file **exists**. Nothing reads this
> prose. `BUS-OBJ-0001` is governed because it is a registered artifact.
>
> **Authority** — the product owner. Business scope is reserved for a named human (s59).

## Problem

A new customer who signs up waits up to four hours for a first response. Support handles the
greeting by hand, in working hours, in one time zone. The cost is measured twice: in the
support hours spent on a message that never varies, and in the customers who do not come back
after the first day.

## Proposed outcome

A new customer receives a personal greeting within five minutes of signing up, at any hour,
without a person composing it. Observable as a drop in median time-to-first-response, not as
"a greeting service exists".

## Scope

**In scope.** Generating and delivering the first greeting for a newly registered customer.
The greeting's content, its delivery, and the record that it was sent.

**Explicitly out of scope.**

- Every message after the first one. Ongoing customer communication is a different problem
  with different owners, and folding it in here is how this program grows a second scope
  nobody approved.
- Customer registration itself. This program consumes registration events; it does not own
  the account.
- Translation. The greeting ships in one language. If that turns out to be wrong it is a
  change-control event, which is exactly what this section exists to make visible.

## Business objectives

Registered in `.specify/traceability/requirements.yaml`. Every requirement `refines` one of
them, and `TRC-008` reports a requirement that refines nothing as an orphan.

| Id | Objective | Measure of success |
|---|---|---|
| `BUS-OBJ-0001` | Cut time-to-first-response for a new customer | median falls from 4 hours to under 5 minutes, measured over a calendar month |

## Key assumptions

Each of these, if wrong, invalidates the case. Each has an entry in the risk register — an
assumption with no matching risk is an assumption nobody is watching.

| Assumption | Risk |
|---|---|
| The platform can sustain the load a greeting per registration implies | `RISK-0001` |
| The greeting wording is acceptable to legal without redesign | `RISK-0002` |

## Feasibility

The capacity study measured 420 requests per second against a 200 ms target on the current
stack. The requirement is 500. That gap is not a reason to stop; it is the reason
`RISK-0001` is above the high threshold and `WBS-1.2.1.2` exists to close it before the
architecture is baselined.
