# Governance Index

> The context map for this directory (specup.md s9). An agent navigates
> directory -> AGENTS.md -> index.md -> the one artifact it needs, instead of loading the
> repository. This is what keeps per-task context bounded (s56, s57).

## Purpose

One sentence on what this scope covers.

## Lifecycle position

- Phase: see `.specify/extensions/openup/openup-config.yml` -> `lifecycle.phase`
- Iteration: see `lifecycle.iteration`

## Canonical stores

| Artifact | File | Generated view |
|---|---|---|
| WBS | `.specify/wbs/wbs.yaml` | `wbs.md` |
| Risks | `.specify/risks/risk-register.yaml` | `risk-register.md` |
| Artifacts | `.specify/traceability/requirements.yaml` | — |
| Traceability | `.specify/traceability/traceability.yaml` | `traceability.md`, `coverage.md` |
| Evidence | `.specify/evidence/` | — |

Never edit a generated view; regenerate it with `/speckit.openup.wbs`,
`/speckit.openup.risk`, or `/speckit.openup.trace`.

## Key identifiers in this scope

- Business objectives:
- Requirements:
- WBS root:
- Open high risks:
- Contracts:

## Checking state

```bash
python .specify/extensions/openup/scripts/python/audit.py
```
