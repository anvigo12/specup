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
| `p2.sh` | P2: builds the governed tree into an image, boots it under two policies, and tries `truncate(2)` | **yes, against two builds — exit 1 on `v0.0.116`, exit 0 on `0.0.117-dev.204`. Both are correct runs** |
| `p5.sh` | P5: starts **one** Infinity process with both models and measures it | **yes — exit 0 answered, and exit 1 on the reranker the stack had decided** |
| `p5_measure.py` | the judgement half of P5: process count from `/proc`, resident memory, and whether the two models actually retrieve and rank | yes, including both failures |
| `p3.sh`, `p4.sh`, `p6.sh` … `p8.sh` | **absent, deliberately** | — |

**`p1b` is evidence, not a probe.** It has no pre-registered falsifier, so `record.py` will not
take its output and no `RESULT` block belongs to it. It exists because P1's one stubbed run said
almost nothing about Open SWE, and Open SWE ships 3434 tests that say a great deal for free.
A script whose numbers are checked against constants is not a probe; it is a regression guard, and
when its numbers move the campaign document changes rather than the constants.

**The remaining five are missing on purpose.** Writing `p3.sh` today would mean inventing Agent
Inbox's connection flags from memory — the failure `AGENTS.md` names in as many words: *"Resolve, or
stop — never infer."* Each probe's script is written **when that probe is prepared**, against the
upstream documentation open beside it. `p2.sh` is what that looks like in practice: every flag in it
was read from `openshell <command> --help` or from NVIDIA's own source during the run, and the two
guesses made beforehand — `openshell version` and a positional argument to `sandbox exec` — were
both wrong. `p5.sh` is the same: the decision to use Infinity rather than TEI came from reading
TEI's own usage line, which takes one `--model-id` and settles the assumption negatively for that
runtime before a single byte is downloaded.

**A probe must check that the thing worked, not that it replied.** `p5_measure.py` exists because
the obvious version of P5 — start a server, `POST /rerank`, assert `200` — would have recorded
`answered` against a model server returning meaningless numbers. So it reranks two queries over a
shared corpus and requires each to place its own answer first, and it does the same to the
embedder by cosine, because wrong pooling produces vectors of the right width that retrieve
badly. Both checks earned their place: the reranker check is what caught the falsifier, and the
embedder check is what proved the embedder was fine while its neighbour was not.

**Smoke-test the harness before the probe, and say which is which.** `p5.sh` takes `EMBED_ID` and
`RERANK_ID` so the script can be exercised end to end on two tiny models in a minute rather than
after an hour of downloading. That run is not a result and no `RESULT` block may cite it — it
tells you the script works, not what the software does. The defaults are the decided pair, and a
recorded run uses them.

**`p2.sh` does not install OpenShell, and that is deliberate.** The installer needs root. A probe
script that silently acquires root to answer a question about containment would be a worse problem
than the unanswered question. The script checks for `openshell` on `PATH`, exits `2` if it is
missing, and prints the command for a human to run.

**It also turned out not to need root at all.** OpenShell's gateway is a systemd **user** service,
so the published tarballs can be `sha256`-verified, extracted into the spike directory and run
unprivileged against a `--db-url` inside `workspace/`. That is how P2 was re-run against a build
that has no release artifacts. `OPENSHELL=/path/to/openshell` points the script at it; the header
comment carries the five commands. The general rule holds — **when a probe seems to need root,
check whether the software actually does before asking anyone to grant it.**

**`p2.sh` has exited both 1 and 0, on the same day, from the same code.** `v0.0.116` builds the
Landlock ruleset at `ABI::V2` and `truncate(2)` empties the trust root: exit 1, `FALSIFIED`, and
that is the true result rather than a broken script. `0.0.117-dev.204+ge38d7254e` builds at
`ABI::V3` and the same call returns `EACCES`: exit 0. **Neither run is the one to keep.** The
record holds both, because the gap between them is the deployment constraint. When the fix
reaches a stable release, the response is `record.py --supersede` — never an edit to the script's
expectations.

**Step 5c truncates twice on purpose.** A `DENIED` on the protected path proves nothing on its
own: `perl` could be missing, the file could be absent, the exec wrapper could be failing. The
second truncation, on a path the same policy permits in the same sandbox, is what makes the first
one evidence. An earlier run of this probe reported a `read: DENIED` that turned out to be a
redirect to an unlisted `/dev/null`, and this is the shape of the fix.

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
