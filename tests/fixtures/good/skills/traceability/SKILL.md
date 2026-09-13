# Traceability Skill

> Capability contract (specup.md s8). `AGENTS.md` says **what rules must I obey**; this file
> says **how do I perform this activity**. Keep the two separate — merging them produces a
> document that is followed for neither purpose.

## Purpose

Maintain the relation graph so that both 'what implements this requirement?' and 'what requirements does this file affect?' are answerable mechanically.

## Inputs

- the artifact registry
- the WBS and the risk register
- source files inside the configured perimeter
- `.feature` files and test artifacts

## Rules

- **Store each edge once, in active voice.** The inverse is derived at load time. Two hand-maintained directions are two things that can disagree.
- The relation vocabulary is closed and each relation has a legal domain and range.
- **Be honest about provenance.** `derived` means a rule recomputes it — and `TRC-010` re-runs that rule. `approved` means a human signed off — and `TRC-013` checks the signature still matches. `asserted` is the honest label for a judgment call, and it costs nothing. When in doubt, `asserted`.
- Never hand-write a `derived` edge: they live in `derived.yaml`, which is rewritten in full.
- Never hand-write an `approved` edge — use `approve_edge.py`.
- If backward coverage fails on files that should not be governed, fix the **perimeter**, not the graph.

## Output

- `.specify/traceability/traceability.yaml` — hand-maintained edges
- `.specify/traceability/derived.yaml` — **machine-owned**
- `traceability.md`, `coverage.md` — **generated**

## Validation

```bash
python3 .specify/extensions/openup/scripts/python/derive_edges.py --write
python3 .specify/extensions/openup/scripts/python/validate_trace.py --json
python3 .specify/extensions/openup/scripts/python/render_views.py --write
```
