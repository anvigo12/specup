# Architecture — SpecUP

> **Answers** — what is in this directory, and why the one document a gate looks for is not
> here.
>
> **Does not answer** — SpecUP's design. That is `specup.md` for the model and
> `docs/guide/using-specup.md` for the implementation.
>
> **Filled in badly when** — an `architecture.md` is created from the template to make a gate
> pass. `architecture_baselined` checks only that the file **exists**; it never opens it, so a
> blank one retires the condition permanently on the day it is written.
>
> **Checked by** — `CTX-002` fails an id here that resolves to nothing.
>
> **Authority** — the maintainer. An architecture baseline is a named-human decision.

## This directory is deliberately not finished

It holds two templates and no decisions:

| File | State |
|---|---|
| `architecture-template.md` | a template, seeded with its template name intact |
| `adr-template.md` | a template, copied per decision; MADR section order |

There is **no `architecture.md`** and there are **no ADRs**. `architecture_baselined` fails,
which is correct, and it is not a condition of the gate SpecUP is currently held to
(`GATE-INITIAL_OPERATIONAL_CAPABILITY`) — so this is a real gap rather than a blocked release.

Seeding the architecture document under its template name is the reason the gate keeps
reporting the truth. A seeded `architecture.md` would pass the condition on day one while the
document still said nothing, which is the one outcome the check cannot recover from.

## The decision that should be written first

`WBS-1.1.3.1` — how to make SpecUP's own test suite derivable — has two candidate
implementations that are not equivalent:

- rename `tests/test_docs.py` to `tests/test_validate_docs.py` and so on, which makes the
  shipped rule work and costs one churn commit; or
- add a derivation rule mapping a test module to the module it imports, which is more general
  and more likely to be wrong.

The ADR is the deliverable before the code is. `RISK-0003` is why it matters.

## When an ADR is written here

Copy `adr-template.md`, and do not skip its **Confirmation** section. It carries the
independent-oracle rule: a transcription checked against a predicate derived from the same
reading has not been checked at all — the two agree because they share an origin, and they are
wrong together.
