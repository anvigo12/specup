# Governance — SpecUP

> **Answers** — which documents in this directory bind behaviour, which are generated from
> the code, and which decisions are reserved for a person.
>
> **Does not answer** — the rules themselves. Each document states its own.
>
> **Filled in badly when** — a generated document is edited. Three of the files here are
> produced from the checks that enforce them, and an edit survives exactly until the next
> `render_views.py --write`, having meanwhile told somebody something untrue.
>
> **Checked by** — `CTX-002` fails an id here that resolves to nothing. `APV-000` fails when
> the approval matrix names no approver.
>
> **Authority** — the maintainer. Amending a standard is a change-control decision, not an
> edit.

## Authored — a person decides what is in these

| File | What it binds |
|---|---|
| `approval-matrix.md` | which decisions need a named human, and who. Every row names the same person; see `RISK-0001` |
| `change-control.md` | how a baselined artifact changes |
| `language-rules.md` | how a requirement is written so it can be contradicted |
| `coding-rules.md` | how failure is represented in code |
| `security-practices.md` | what must be true of a change that touches a trust boundary |
| `allowed-signers` | whose signature `APV-002` will accept. **Currently holds no key** — see below |

## Generated — the code decides what is in these

| File | Produced from |
|---|---|
| `definition-of-ready.md` | the Definition-of-Ready checks in `select_work.py` |
| `definition-of-done.md` | the `DOD` checks in `validate_done.py` |
| `quality-gates.md` | the gate conditions registered in `evaluate_gate.py` |

```bash
python3 extensions/openup/scripts/python/render_views.py --write
```

A governance document that disagrees with its check is worse than no document: people follow
the document while the machine applies the code. That is why these three are not seeded.

## The trust root is empty, and that is the accurate state

`allowed-signers` holds reasoning and no keys. `APV-002` therefore verifies nothing here, and
`approvals.require_witness_at_or_above` is `null` — a witness floor that one person satisfies
by signing their own approval is a ceremony, not a control. `APV-004` warns on every claimed
approval regardless, so the gap is visible on every run rather than only in this paragraph.

There is exactly one approval in this repository: the acceptance of `RISK-0001`, by
`maintainer`, with no commit. It is reported as `claimed`.

## The three standards apply forward only

They arrived with the scaffold. Nothing in this codebase became non-conformant by installing
them, and rewriting existing prose to match is a rewrite wearing adoption's clothes. Apply
them to what you touch — `docs/guide/existing-project.md` says the same at more length, and
amending a standard to match what the project actually does is a legitimate decision rather
than a failure.
