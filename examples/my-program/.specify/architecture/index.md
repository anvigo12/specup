# Governance Index — architecture

> The context map for this directory.

## Purpose

Where the architecture document and the ADRs will live. **Both are absent, and that is the
state this program is in.**

`architecture_baselined` fails on two counts today: no `architecture.md` exists, and no
`ADR-nnnn` is registered in `.specify/traceability/requirements.yaml`. That is one of the
five conditions `GATE-LIFECYCLE_ARCHITECTURE` fails on, and it is correct — the capacity
question behind `RISK-0001` has not been answered, so there is no decision to record.

## Files here

| File | What it is |
|---|---|
| `architecture-template.md` | the template. Copy it to `architecture.md` when you write one |
| `adr-template.md` | the template, MADR-shaped. Copy it per decision, as `adr-0001-<slug>.md` |

Both keep their `-template` names on purpose. `architecture_baselined` checks only that
`architecture.md` **exists**, so a blank one seeded into place would retire the gate's first
condition while the document still said nothing.
