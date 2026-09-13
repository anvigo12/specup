# Agent Operating Contract — `.specify/`

> Scoped rules for the governance tree (specup.md s7). The repository-root `AGENTS.md` still
> applies; this narrows it for the files that *are* the governance.

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
6. **Every word written here follows `governance/language-rules.md`.** That covers a
   requirement, an acceptance criterion, a risk title, a `terminal_reason`, and any
   `description` field in the canonical YAML. A requirement two people read differently still
   traces, still resolves, and still passes every check — which is exactly why the prose is
   governed rather than left to taste.

## Before you touch anything baselined

```bash
python3 .specify/extensions/openup/scripts/python/impact.py --of REQ-AUTH-0014
```

Then follow `governance/change-control.md`.
