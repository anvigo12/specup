# Acceptance Scenario Skill

> Capability contract (specup.md s8). `AGENTS.md` says **what rules must I obey**; this file
> says **how do I perform this activity**. Keep the two separate — merging them produces a
> document that is followed for neither purpose.
>
> **Done badly when** — the scenario is written from the implementation instead of from the
> acceptance criterion. It passes immediately, it will never fail, and it inverts the
> relationship the whole model rests on: the criterion is the specification, and the scenario
> is evidence about the system rather than a restatement of the code.
>
> **Checked by** — `TRC-012` fails an acceptance criterion no scenario executes, and `TRC-011`
> reports a rule-derivable tag edge that no store declares. **Nothing here runs a scenario** —
> `acceptance_scenarios_passing` reads `.specify/evidence/acceptance-results.json` and trusts
> the record, so a green gate is only as honest as whatever produced that file.

## Purpose

Write Gherkin scenarios bound by tag to acceptance criteria and requirements, so a scenario is evidence rather than prose.

## Inputs

- acceptance criteria (`AC-<DOMAIN>-nnnn-nnnn`)
- the requirements they verify
- `gherkin.features_glob` in the config

## Rules

- **Every scenario carries three tags:** its own `@SCEN-<DOMAIN>-nnnn` identity, the `@AC-...` it executes, and the `@REQ-...` behind it. Without the identity tag, `gherkin-tag-scan` has nothing to hang the `executes` edge on.
- Every acceptance criterion needs at least one scenario (`TRC-012`). A criterion nobody wrote a scenario for has been asserted, not specified.
- Write the scenario against the criterion, never against the implementation.
- Retagging a scenario moves its edge — re-run the deriver afterwards.

## Output

- `specs/<feature>/acceptance/*.feature`
- `executes` edges in `derived.yaml`, produced by `gherkin-tag-scan`

## Validation

```bash
python3 .specify/extensions/openup/scripts/python/derive_edges.py --write
python3 .specify/extensions/openup/scripts/python/validate_trace.py --json
```
