---
description: Execute the implementation plan by processing tasks from tasks.md, resolving each task's governance chain before acting and producing verification evidence after.
strategy: wrap
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
  py: scripts/python/check_prerequisites.py --json --require-tasks --include-tasks
---

## OpenUP Pre-Execution: Resolve the Chain, or Stop

For each task you are about to implement, resolve its full chain **before writing any code**:

```text
TASK -> WBS node -> iteration -> phase -> requirements -> risks
                              -> acceptance criteria -> architecture -> contracts -> tests
```

Read only what the chain names. That is the point of the structure: an L7 task should be
executable from its own metadata, its linked requirement and acceptance criteria, the
relevant architecture decision and contract, and nothing else. Loading the repository defeats
it.

**If any required relationship cannot be resolved, STOP and report it. Do not infer.**

This is the single most important rule in this preset. An agent that invents the missing
requirement, guesses which acceptance criterion applies, or proceeds without an architecture
decision produces work that looks governed and is not — and the fabricated link is
indistinguishable from a real one on inspection.

Concretely, stop rather than proceed when:

- the task references a requirement, risk or criterion that is not registered
- the task has no WBS node, or its node is not in the open iteration
- an interface is touched but no contract is registered for it
- a dependency task is not `done`
- the requirement is still `DRAFT` — it has not been agreed

Confirm the task is genuinely ready:

```bash
python3 .specify/extensions/openup/scripts/python/select_work.py --json
```

{CORE_TEMPLATE}

## OpenUP Post-Execution: Produce Evidence, Then Update the Graph

Implementation is half of the task. A change that works but leaves no trace is not done.

### 1. Verify

Run the checks the task's exit criteria name — unit, integration, the bound Gherkin scenarios,
and contract checks for any interface touched. Record the results under `.specify/evidence/`
and register each as an `EVID-nnnn` artifact.

Report failures as failures. Do not adjust a test, widen an assertion, or narrow a scenario so
that a suite goes green: the acceptance criterion is the specification, and changing the test
to match the implementation inverts the relationship this whole workflow rests on.

### 2. Update traceability

```bash
python3 .specify/extensions/openup/scripts/python/derive_edges.py --write
python3 .specify/extensions/openup/scripts/python/validate_trace.py --json
```

The first command regenerates every mechanically-recoverable edge. Write the judgment links by
hand, as `asserted`, into the hand-maintained store — never a `derived` one.

**Do not label an asserted link `derived` to improve the audit.** Provenance is the only thing
separating evidence from claim; falsifying it removes the one signal a reviewer has. `TRC-010`
re-runs the rule you name and fails the edge when it does not come back, so this is now a
failing graph rather than a better score.

### 3. Reassess risk

If the task mitigated a risk, update `residual_probability` and `residual_impact` from what
the evidence actually showed, and attach it. Leaving the original estimate in place after
mitigation means the register no longer describes the project.

### 4. Close honestly

Mark a task `done` only when the Definition of Done holds in full: implementation, tests,
traceability, evidence, no orphans, no broken references. Verify rather than assume:

```bash
python3 .specify/extensions/openup/scripts/python/audit.py --json
```

If the audit fails, fix the graph. Do not lower a threshold, widen the traceability perimeter,
fabricate an evidence file, or mark artifacts approved to clear it.

A task left open with a clear reason is a useful signal. A task marked done that the
repository does not support is the failure this entire preset exists to prevent.
