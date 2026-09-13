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
| Governance | `openup-config.yml`, the validators | `definition-of-ready.md`, `definition-of-done.md`, `quality-gates.md` |
| Standards | `.specify/governance/language-rules.md`, `coding-rules.md`, `security-practices.md` | — |

Never edit a generated view. Regenerate them all:

```bash
python3 .specify/extensions/openup/scripts/python/render_views.py --write
```

## Key identifiers in this scope

Every id listed here must resolve: `CTX-002` fails on one that does not, because a map
pointing at something that is not there sends an agent looking for it.

- Business objectives:
- Requirements:
- WBS root:
- Open high risks:
- Contracts:

## Checking state

```bash
python .specify/extensions/openup/scripts/python/audit.py
```
