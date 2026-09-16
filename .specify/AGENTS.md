# Agent Operating Contract — `.specify/`

> **Answers** — what an agent may and may not edit inside the governance tree, and which
> files are owned by a machine rather than by anyone (specup.md s7).
>
> **Does not answer** — the general operating rules. The repository-root `AGENTS.md` still
> applies; this narrows it for the files that *are* the governance.
>
> **Filled in badly when** — the "Editable by an agent?" column drifts from what the scripts
> actually rewrite. A file listed as authored that `render_views.py --write` overwrites will
> lose someone's work exactly once, and they will not trust the tree afterwards.
>
> **Checked by** — `VIEW-001` fails when a generated view does not match what its sources
> would produce right now, and `VIEW-002` warns about a file carrying the generated banner
> that no renderer owns. `TRC-010` and `TRC-013` catch a hand-written `derived` or `approved`
> edge. **Nothing stops an agent editing a machine-owned file** — the checks notice
> afterwards, which is the whole reason this table is written down.
>
> **Authority** — the repository owner. Moving a row from machine-owned to editable is a
> governance change.

## What lives here

| Path | Authority | Editable by an agent? |
|---|---|---|
| `wbs/wbs.yaml` | canonical | yes, through `/speckit.openup.wbs` |
| `risks/risk-register.yaml` | canonical | yes, through `/speckit.openup.risk` |
| `traceability/requirements.yaml` | canonical | yes — the artifact registry |
| `traceability/traceability.yaml` | canonical | yes — `asserted` edges only |
| `traceability/derived.yaml` | **machine-owned** | **no** — `derive_edges.py --write` rewrites it in full |
| `governance/definition-of-*.md`, `quality-gates.md` | **generated** | **no** — `render_views.py --write` |
| `governance/approval-matrix.md`, `change-control.md` | authored | yes, with a human |
| `governance/language-rules.md`, `coding-rules.md`, `security-practices.md` | binding standards | amend only with a human, under change control |
| `evidence/` | append-only in practice | add, never rewrite history |
| `*.md` views | **generated** | **no** |

## Rules specific to this tree

1. **Every artifact enters at `DRAFT`.** Generated does not mean approved (s31). Only a human
   advances an artifact to `APPROVED` or `BASELINED`.
2. **Exposure is computed, never typed.** `exposure = probability × impact`; a hand-edited
   `exposure:` fails `RISK-001`. The same holds for `residual_exposure`.
3. **Edges are stored once, in active voice.** The inverse is derived at load time. Writing
   both directions creates two things that can disagree.
4. **Mark judgment calls `asserted`.** It is the honest label and it costs nothing. Marking one
   `derived` to improve the mix fails `TRC-010`; marking one `approved` without the tool fails
   `TRC-013`.
5. **Evidence is a file, not a sentence.** Record it under `evidence/`, register it as
   `EVID-nnnn`, and reference it from the node that produced it.
6. **Re-read the source before you write a value into a canonical store.** A threshold, a
   clause reference, an id, a number taken from a document: open it and read it, rather than
   writing what you remember reading earlier in this session. A value reconstructed from
   memory arrives with the same confidence as one just read, and every artifact downstream
   inherits the error together with it.
7. **Every word written here follows `governance/language-rules.md`.** That covers a
   requirement, an acceptance criterion, a risk title, a `terminal_reason`, and any
   `description` field in the canonical YAML. A requirement two people read differently still
   traces, still resolves, and still passes every check — which is exactly why the prose is
   governed rather than left to taste.

## Before you touch anything baselined

```bash
python3 .specify/extensions/openup/scripts/python/impact.py --of REQ-AUTH-0014
```

Then follow `governance/change-control.md`.
