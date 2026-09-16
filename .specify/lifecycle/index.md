# Lifecycle — SpecUP

> **Answers** — where SpecUP is in the OpenUP lifecycle, which gate that makes current, and
> where the documents behind it live.
>
> **Does not answer** — what the gate conditions mean. That is the generated
> `.specify/governance/quality-gates.md`, produced from the code that evaluates them.
>
> **Filled in badly when** — the phase is set to the one whose gate the project can pass.
> `docs/guide/existing-project.md` names that as a failure mode in as many words: you will
> hold the wrong gate and learn nothing.
>
> **Checked by** — `CTX-002` fails an id here that resolves to nothing. Nothing checks that
> the phase is honest — it is a string in a config file, and choosing it is a governance act.
>
> **Authority** — the maintainer.

## Position

| | |
|---|---|
| Phase | `CONSTRUCTION` |
| Iteration | `ITER-C-02` — SpecUP 0.1.2 |
| Gate held | `GATE-INITIAL_OPERATIONAL_CAPABILITY` |
| Gate verdict | **FAIL**, on `acceptance_scenarios_passing` |

Two earlier iterations exist in the graph: `ITER-C-01` (0.1.1, released) and `ITER-C-03`
(0.1.3, planned and almost entirely undecomposed). Inception and Elaboration are absent
because they happened before this tree existed, and reconstructing them now would be
archaeology.

Setting `CONSTRUCTION` had an immediate cost, which is the point of setting it honestly: the
gate became the strictest one before release. `INCEPTION` would have passed on day one over a
tool that has shipped twice.

## Documents here

| File | Answers |
|---|---|
| `vision.md` | what SpecUP is for, and what would make it not worth having |
| `stakeholders.md` | who is affected, what they need, and who decides |

Both are authored. Both are checked by conditions that verify the **file exists** and open
nothing — `vision_present` and `stakeholders_identified` pass over an unfilled template, which
is worth knowing before treating either condition as meaningful.

## Changing the phase

```bash
# .specify/extensions/openup/openup-config.yml
lifecycle:
  phase: CONSTRUCTION
  iteration: ITER-C-02
```

Moving forward means the next gate becomes current and is held immediately. Moving backward
means a gate that was passed is no longer being checked. Neither is an edit: both go through
`.specify/governance/change-control.md`.
