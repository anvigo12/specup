## Task Execution Contract

A task is an execution contract for an agent, not a line item. Each one carries the
governance that bounds it, so the agent working on it needs the task and its linked artifacts
rather than the whole repository. The **WBS L7 node id is the task id** — s15 already defines
L7 as the Executable Task, so there is no separate `TASK-nnnn` to keep in step with it.

```text
[WBS-1.2.3.4.1.1.2]
[REQ-AUTH-0014]
[RISK-0007]
[AC-AUTH-0014-0003]

Implement certificate validation.

Preconditions:
- WBS-1.2.3.4.1.1.1 complete
- Certificate schema approved

Files:
- src/security/certificate_validator.ts
- tests/unit/certificate_validator.test.ts

Evidence:
- unit test result
- security test result

Exit criteria:
- invalid certificates rejected
- expiry checked
- issuer validated
- traceability updated
```

Every bracketed id must resolve to a registered artifact. An id that resolves to nothing is
the one failure mode this format exists to catch.

## Definition of Ready

A task is not executable merely because it exists. Before work starts, all of these hold:

| Condition | Meaning |
|---|---|
| Requirement linked | at least one `REQ-*` or `NON-FR-*`, registered and not `DRAFT` |
| Acceptance criteria | present for the requirement; mandatory on a `test` task |
| WBS node | L7, or terminal above L7 with a stated `terminal_reason` |
| Dependencies resolved | every dependency exists and is `done` |
| Risk analysis | a `risk-mitigation` task references the risk it reduces |
| Owner | a named person or standing group |
| Iteration | assigned to the open iteration |
| Files identified | the task names where the change lands |

Check it mechanically rather than by eye:

```bash
python3 .specify/extensions/openup/scripts/python/select_work.py --json
```

If nothing is ready, fix the blockers. Do not relax the bar to produce a work list — a task
that starts unready fails later, more expensively.

## Definition of Done

`status: done` is a computed state, not a declaration. A task is done when:

- implementation is complete
- unit and integration tests pass
- the bound Gherkin scenarios pass
- contract checks pass for any interface touched
- security checks pass
- the risk register is updated, with residual values from what was actually learned
- traceability is updated, with honest provenance
- evidence is recorded and referenced from the task
- no orphan artifacts and no broken references were introduced

A task marked done with no evidence is not done. Report it as incomplete rather than closing
it — carrying work into the next iteration is normal and honest; a green board that does not
match the repository is neither.

## Ordering

Order tasks by risk, then by dependency, then by cohesion. The highest-exposure work goes
first so uncertainty is retired while there is still time to respond to it. A plan that
schedules the easy work first optimizes for early progress and defers the questions that can
still change the design.
