---
description: Generate an actionable, dependency-ordered tasks.md for the feature, derived from the WBS, risk register and acceptance criteria, in the governed task contract form.
strategy: wrap
handoffs:
  - label: Analyze For Consistency
    agent: speckit.analyze
    prompt: Run a project analysis for consistency
    send: true
  - label: Implement Project
    agent: speckit.implement
    prompt: Start the implementation in phases
    send: true
scripts:
  sh: scripts/bash/setup-tasks.sh --json
  ps: scripts/powershell/setup-tasks.ps1 -Json
  py: scripts/python/setup_tasks.py --json
---

## OpenUP Pre-Execution: Derive Tasks From the Governed Plan

Tasks are **derived from the WBS**, not invented from the plan text. The WBS is where scope,
ownership, iteration assignment and risk linkage already live; generating tasks independently
of it produces a second, competing plan.

Before generating anything, read:

1. `.specify/extensions/openup/openup-config.yml` — the current `lifecycle.phase` and
   `lifecycle.iteration`. Tasks belong to the open iteration, not to the whole backlog.
2. `.specify/wbs/wbs.yaml` — the L7 nodes assigned to that iteration. These are the tasks.
3. `.specify/risks/risk-register.yaml` — every risk at or above the high-exposure threshold
   needs mitigation work scheduled ahead of lower-risk features.
4. `.specify/traceability/requirements.yaml` — the requirements and acceptance criteria each
   node is bound to.

Then establish what is genuinely executable:

```bash
python3 .specify/extensions/openup/scripts/python/select_work.py --json
```

This applies the Definition of Ready and returns the ready set, ordered highest-risk-first,
plus each blocked task and the reason it is blocked.

**If a task you were about to generate is not in the ready set, do not generate it.** Report
the blocker instead. Generating a task that cannot be executed moves the problem to
implementation time, where it is more expensive and less visible.

**If the WBS has no L7 node for work the plan clearly requires,** that is a gap in the WBS,
not a reason to invent a free-floating task. Say so, and hand back to `/speckit.openup.wbs`.

{CORE_TEMPLATE}

## OpenUP Post-Execution: Bind Each Task to Its Governance

Rewrite every generated task into the governed contract form, with its ids drawn from the
artifacts you read — never minted here:

```text
[WBS-<node>]
[REQ-<DOMAIN>-nnnn]
[RISK-nnnn]            (only when the task mitigates one)
[AC-<DOMAIN>-nnnn-nnnn] (only when the task verifies one)

<what the task does>

Preconditions:   <dependency tasks that must be complete>
Files:           <where the change lands>
Evidence:        <what will prove it worked>
Exit criteria:   <the conditions that make it done>
```

Rules:

- **The WBS node id is the task id.** There is no separate `TASK-nnnn`: s15 defines WBS L7 as
  the Executable Task, so the node *is* the task. Minting a second identity for one thing is
  the drift this whole model exists to prevent, and an id nothing registers cannot be checked.
- **Every bracketed id must resolve.** If you cannot resolve one, stop and report it rather
  than writing a plausible id. An unresolvable id is worse than a missing task because it
  looks traced.
- **Do not create requirement, risk or acceptance ids here.** `/speckit.tasks` consumes the
  graph; it does not extend it. New requirements go through `/speckit.specify`, new risks
  through `/speckit.openup.risk`.
- **Order by risk, then dependency.** Preserve the ordering `select_work.py` returned unless
  a dependency forces otherwise; say so when you deviate.
- **Preserve the Definition of Done.** A task's exit criteria must include updating
  traceability and recording evidence — a task whose exit criteria are only "code written"
  cannot ever be legitimately marked done.

Then record the new edges and re-check:

```bash
python3 .specify/extensions/openup/scripts/python/validate_wbs.py --json
python3 .specify/extensions/openup/scripts/python/validate_trace.py --json
```

Report which tasks were generated, which WBS nodes they came from, which were skipped as not
ready and why. If the ready set was empty, say that plainly — an empty iteration is a real
result and usually means the blockers are the actual next work.
