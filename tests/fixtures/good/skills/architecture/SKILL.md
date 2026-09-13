# Architecture Decision Skill

> Capability contract (specup.md s8). `AGENTS.md` says **what rules must I obey**; this file
> says **how do I perform this activity**. Keep the two separate — merging them produces a
> document that is followed for neither purpose.

## Purpose

Record architecture decisions so they are reachable from the requirements they answer and the code that implements them.

## Inputs

- requirements, especially non-functional ones
- the open risks
- the existing architecture document and prior ADRs

## Rules

- An ADR is `ADR-nnnn` and registers like any other artifact.
- **Link it.** An ADR `refines` the requirement it answers; source code `implements` the ADR. An unlinked ADR is a document nobody navigating the graph will find.
- Record the decision, the alternatives, and what would make you revisit it. An ADR with no rejected alternative is a description, not a decision.
- Supersede, never rewrite: `supersedes` keeps the history in the graph.
- Only a human advances an ADR past `DRAFT` — `architecture_baselined` gates on it.
- A decision that changes a contract is a breaking change; see the approval matrix.

## Output

- `.specify/architecture/architecture.md`
- the ADR registry entry

## Validation

```bash
python3 .specify/extensions/openup/scripts/python/evaluate_gate.py --gate GATE-LIFECYCLE_ARCHITECTURE --json
```
