# Probe scripts

**Audience:** whoever runs a probe from
[`../test-specup-agent-shape-assumptions.md`](../test-specup-agent-shape-assumptions.md).

This directory holds the **tracked** half of the campaign. The campaign document states what each
probe asks and what would falsify it; these scripts are how a second person repeats the reading.

| What | Where | Tracked |
|---|---|---|
| The falsifiers, the steps, the results | `../test-specup-agent-shape-assumptions.md` | **yes** |
| Scripts a second person re-runs | here | **yes** |
| Clones, compose files, volumes, model caches, logs | `workspace/spike-0.1.3/<probe>/` | **no** |

`workspace/.gitignore` is `*` with one exception for itself, so nothing built inside a probe
environment can reach the repository by accident. **Nothing goes into `open-swe/`** — a pre-commit
hook fails any commit that gives a file there bytes, and that premise is what
[the stack report's §1](../../research/specup-agent-stack.md#1-what-open-swe-is-today) rests on.

## What is here now, and what is not

| File | What it is | Has it been run? |
|---|---|---|
| `record.py` | the harness. The only thing that should edit a `RESULT` block | yes, including all three refusals |
| `p1.sh` | P1 end to end: clone, resolve, boot, assert, tear down | **yes — exit 0 answered, and exit 1 on a deliberately dirtied `open-swe`** |
| `p1_stub_anthropic.py` | a stub Anthropic Messages API, so P1 needs no provider key | yes, both JSON and SSE |
| `p1b_open_swe_suite.sh` | Open SWE's own suite, twice: with and without `langgraph-api` | yes |
| `p2.sh` … `p8.sh` | **absent, deliberately** | — |

**`p1b` is evidence, not a probe.** It has no pre-registered falsifier, so `record.py` will not
take its output and no `RESULT` block belongs to it. It exists because P1's one stubbed run said
almost nothing about Open SWE, and Open SWE ships 3434 tests that say a great deal for free.
A script whose numbers are checked against constants is not a probe; it is a regression guard, and
when its numbers move the campaign document changes rather than the constants.

**The remaining seven are missing on purpose.** Writing `p2.sh` today would mean inventing
OpenShell's CLI flags from memory — the failure `AGENTS.md` names in as many words: *"Resolve, or
stop — never infer."* Each probe's script is written **when that probe is prepared**, against the
upstream documentation open beside it.

A directory holding a harness and the scripts that have actually run is honest. A directory
holding eight scripts that were never executed against the software they name is not.

**On ordering, precisely.** The rule that binds is that the *falsifier* is committed before the
run, and P1's was — commit `afb6b75`, before any of this. `p1.sh` was written **during** P1's
first run rather than before it, and committed with the result. It is a reproduction script, not
the pre-registration; saying otherwise would be the small lie this whole directory exists to make
expensive.

## Using `record.py`

```bash
python3 docs/implement/probes/record.py --list
```

Prints every probe, its current outcome, and whether it has a pre-registered falsifier.

```bash
python3 docs/implement/probes/record.py \
    --probe P1 --outcome answered \
    --by "Aniket Gore" \
    --evidence "workspace/spike-0.1.3/P1/2026-09-20-run.log" \
    --found "All five graphs loaded; chat completed one thread. No Open SWE source changed."
```

`--dry-run` prints the block without writing it.

**Three outcomes, and there is no fourth:** `answered`, `falsified`, `blocked`. A probe that could
not be run is `blocked` and never a pass — which matters most for P2, because OpenShell is alpha
and installs on the host rather than in a container.

## What it refuses, and why each rule exists

| Refusal | Because |
|---|---|
| An outcome outside the three | "Mostly works" is how a falsified probe becomes a passing one |
| A result against a probe with no `**Falsified when:**` line | A success criterion written after the run can always be read as a pass |
| Overwriting an outcome without `--supersede` | A result that quietly changes is not a record. With the flag, the old outcome is kept in the new block |

Exit `0` recorded, `1` refused, `2` the document could not be read — the same three-code contract
the validators use, where `2` is an operator error rather than a governance failure.

## What checks this

**Nothing checks the scripts.** `record.py` is outside the traceability perimeter — the perimeter
is `src/**`, `services/**` and `apps/**` — so `DOC-*` does not read its docstring and backward
coverage does not count it. It has no unit tests, and the suite must stay hermetic, so it should
not acquire any that need a probe environment.

What it does have is the property the campaign actually needs: **every refusal above was made to
fire on purpose before the harness was trusted.** A check nobody has seen fail is not a check.
