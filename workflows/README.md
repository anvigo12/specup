# OpenUP Phase Workflows

Four workflows, one per OpenUP phase. **This is where SpecUP's gates actually bite.**

Presets and extension hooks are prompt-level — an agent reads them and may decline. A
workflow `shell` step is not: it runs a validator, and the engine branches on the real exit
code. These four files are the difference between governance that is described and governance
that is enforced.

| Workflow | Phase | Milestone gate |
|---|---|---|
| `openup-inception` | Inception | `GATE-LIFECYCLE_OBJECTIVES` |
| `openup-elaboration` | Elaboration | `GATE-LIFECYCLE_ARCHITECTURE` |
| `openup-construction` | Construction (one iteration) | `GATE-INITIAL_OPERATIONAL_CAPABILITY` |
| `openup-transition` | Transition | `GATE-PRODUCT_RELEASE` |

## Running

```bash
specify workflow run ./workflows/openup-inception/workflow.yml \
  --input idea="..." --input program="..."

specify workflow status
specify workflow resume <run_id>
```

`openup-construction` is **one iteration**. Run it again for the next one — a single pass
that implements everything is the "one large AI code-generation exercise" that specup.md s38
exists to prevent.

## The enforcement pattern

Every phase workflow ends with the same three-step block, and the shape is deliberate:

```yaml
- id: evaluate-gate
  type: shell
  run: "python3 .specify/extensions/openup/scripts/python/evaluate_gate.py --gate <GATE> --json --out <evidence path>"
  continue_on_error: true      # so the branches below are reachable

- id: halt-if-unevaluable
  type: if
  condition: "{{ steps.evaluate-gate.output.exit_code == 2 }}"
  then:
    - id: cannot-evaluate
      type: shell
      run: "echo '...' >&2; exit 2"     # no continue_on_error: this HALTS

- id: enforce-gate
  type: if
  condition: "{{ steps.evaluate-gate.output.exit_code == 1 }}"
  then:
    - id: gate-failed
      type: gate
      options: [reject, override]
      on_reject: abort
```

**Why `continue_on_error: true` on the check.** A non-zero shell step halts the whole run by
default. That would be enforcement, but it would also make the human branch unreachable and
give the operator no verdict to read. Letting the step record its exit code and branching
explicitly keeps the failure consequential *and* legible.

**Why exit 2 is handled separately.** Exit 2 means the graph could not be loaded — a setup
fault, not a governance failure. Collapsing the two would tell a human their project failed
its milestone when the truth is that a YAML file is malformed. Exit 2 halts hard; there is
no human choice to offer, because nothing was actually evaluated.

**Why the human gate exists at all.** A machine check establishes whether the evidence is
there. It does not decide whether to proceed — that is a human authority (s59). `reject`
stops; `override` proceeds and writes the failing verdict to
`.specify/evidence/overrides/<run_id>.json`, because an undocumented override is
indistinguishable from a gate that never ran.

## Security: never interpolate input into `run:`

A `run` field is executed by the system shell, and `{{ }}` expressions are substituted as
**raw text with no quoting or escaping**. A value the user supplies would be parsed as shell
syntax.

So in these workflows, no `{{ inputs.* }}` ever appears in a `run:` field. User input reaches
commands through `input.args`, which is the sanctioned path; shell steps use fixed strings
and engine-controlled values such as `{{ context.run_id }}`.
`tests/test_workflows.py::test_no_user_input_is_interpolated_into_a_shell_command` enforces this.

## Evidence

Two records accumulate, and neither depends on the agent choosing to write it:

- **Gate verdicts** — `.specify/evidence/gates/<gate>.json`, written by `--out` on the
  validator itself. (Capturing stdout with `tee` would destroy the exit code the branch
  depends on, so persisting the verdict is the validator's job, not the shell's.)
- **The engine's run log** — `.specify/workflows/runs/<run_id>/log.jsonl`, an append-only
  record of every step, its status, and where the run paused.

## Verified behavior

Against spec-kit 1.0.6, using the `tests/fixtures/good` project:

| Graph state | Result |
|---|---|
| healthy | `Status: completed` — runs through to the end |
| high-exposure risk stripped of its mitigation | `Status: paused` at `[gate-failed]`; the final step is never reached |
| `wbs.yaml` corrupted so the graph cannot load | `Status: failed`, `Shell command exited with code 2` |

## Portability note

Shell steps invoke `python3`. On Windows the interpreter is normally `python`; adjust the
`run:` lines, or install a `python3` shim, before running these on a Windows host.
