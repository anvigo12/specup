# Work Breakdown — SpecUP

> **Answers** — what work exists, which iteration it sits in, and where to look for the one
> node you need.
>
> **Does not answer** — whether a node is done. That is computed by `validate_done.py` from
> the graph, not read from the `status` field. A node says `done`; the validator decides.
>
> **Filled in badly when** — it duplicates `wbs.yaml`. This is a map; the store is the store.
>
> **Checked by** — `CTX-002` fails an id here that resolves to nothing. **Nothing checks what
> this map omits.**
>
> **Authority** — the maintainer. Structure at levels 1 to 3 goes through `change-control.md`.

## Purpose

SpecUP's own plan. Thirteen nodes, one phase, three iterations, every leaf terminating at
level 4 with a recorded reason.

## Shape

```
WBS-1                 SpecUP                                   L1  in-progress
└── WBS-1.1           Construction                             L2  in-progress
    ├── WBS-1.1.1     ITER-C-01 — 0.1.1                        L3  done
    │   └── WBS-1.1.1.1   released                             L4  done
    ├── WBS-1.1.2     ITER-C-02 — 0.1.2                        L3  in-progress
    │   ├── WBS-1.1.2.1   human approval, made mechanical      L4  done
    │   ├── WBS-1.1.2.2   the docstring contract               L4  done
    │   ├── WBS-1.1.2.3   templates that explain themselves    L4  done
    │   ├── WBS-1.1.2.4   the worked example                   L4  done
    │   ├── WBS-1.1.2.5   SpecUP governs itself                L4  in-progress
    │   └── WBS-1.1.2.6   documentation sweep and release      L4  planned
    └── WBS-1.1.3     ITER-C-03 — 0.1.3                        L3  planned
        └── WBS-1.1.3.1   make the test suite derivable        L4  planned
```

## Two things a reader should not have to discover

**No node reaches level 7, and that is declared rather than omitted.** `depth_policy` is
`semantic`, so a leaf above level 7 must carry a `terminal_reason`, and all eight do.
`specup.md` §18 read literally wants every leaf at level 7; §65 says not to write seven levels
of narrative. Decomposing "write one validator" into a task tree would produce six levels of
restatement, and the reason is on the node rather than in a commit message.

**0.1.3 is deliberately almost empty.** Its main content is a runtime whose intent is in a
plan file and in no registered requirement. A node for work whose requirement does not exist
puts the plan ahead of the decision, which is the order `specup.md` §39 exists to prevent. The
one node there mitigates `RISK-0003`, which is live now.

## Where to look

| Question | File |
|---|---|
| What is the plan | `.specify/wbs/wbs.yaml` |
| What does it look like | `.specify/wbs/wbs.md` — generated, never edit |
| Is a `done` claim true | `python3 extensions/openup/scripts/python/validate_done.py` |
| What is ready to start | `python3 extensions/openup/scripts/python/select_work.py` |
