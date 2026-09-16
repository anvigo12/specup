# Governance Index — wbs

> The context map for this directory.

## Purpose

The plan. `wbs.yaml` is canonical; `wbs.md` is a generated view and is absent here because
nothing has run `render_views.py --write` against this example.

## Shape of this plan

| Level | In this program |
|---|---|
| L1 | `WBS-1` — My Program |
| L2 | `WBS-1.1` Inception, `WBS-1.2` Elaboration |
| L3 | `WBS-1.1.1` ITER-I-01, `WBS-1.2.1` ITER-E-01 |
| L4–L7 | decomposed under Inception only |

Elaboration stops at L4 with a `terminal_reason`, which `depth_policy: semantic` allows and
`validate_wbs.py`'s leaf-depth check enforces. Decomposing it now would record guesses as a
plan.

> Check ids are named in prose here rather than written out, and that is not style. `CTX-002`
> reads any id-shaped token in a context map as an artifact reference; the leaf-depth check's
> id is shaped exactly like a WBS node id, so writing it here would report as a dangling
> reference — correctly, because a reader would try to follow it.

## Key identifiers

- Root: `WBS-1`
- Risk mitigation: `WBS-1.2.1.2` → `RISK-0001`
- Test work: `WBS-1.1.1.1.1.1.3` → `AC-GREET-0001-0001`
