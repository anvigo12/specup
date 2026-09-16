# Governance Index — traceability

> The context map for this directory.

## Purpose

Identity in `requirements.yaml`, relationships in `traceability.yaml`. The separation is
deliberate: a rename is then one edit rather than a search.

## What the graph says today

| Figure | Value | Why |
|---|---|---|
| Forward coverage | 0% | nothing `implements` either requirement — there is no code in this root |
| Verification coverage | partial | `AC-GREET-0001-0001` verifies `REQ-GREET-0001`; nothing verifies `NON-FR-GREET-0001` |
| Backward coverage | vacuous | the perimeter is empty. See the note in `openup-config.yml` |
| Provenance mix | 10 `derived`, 4 `asserted`, 0 `approved` | `wbs-iteration-field` reads the WBS rather than the filesystem, so it fires here; the rules that need code produce nothing |

## Key identifiers

- `BUS-OBJ-0001`, `REQ-GREET-0001`, `NON-FR-GREET-0001`, `AC-GREET-0001-0001`

## `derived.yaml` is machine-owned

`derive_edges.py --write` owns that file and rewrites it wholesale. Never hand-edit it: every
edge in it names the rule that produced it, and `TRC-010` re-runs that rule and fails any edge
it cannot reproduce. Writing one in by hand does not make it true, it makes the graph fail.

To see what the rules can and cannot recover here:

```bash
python3 extensions/openup/scripts/python/derive_edges.py --root examples/my-program
```

Two things in that output are worth reading. `by_rule` shows `gherkin-tag-scan` and
`test-file-naming-convention` at zero, because neither has anything to read in this tree.
`DRV-004` reports `SKIP` for two declared rules nobody has implemented, and an edge claiming
one of them counts as unverified rather than as evidence — a rule that cannot run cannot
corroborate anything.
