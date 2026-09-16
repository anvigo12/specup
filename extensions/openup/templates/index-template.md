# Governance Index

> **Answers** — what is in this directory and which single artifact to open next. An agent
> navigates directory -> AGENTS.md -> index.md -> the one artifact it needs, instead of
> loading the repository (specup.md s9, s56, s57).
>
> **Does not answer** — what the rules are. That is the nearest `AGENTS.md`. A map that starts
> giving instructions is a second operating contract, and the two will disagree.
>
> **Filled in badly when** — it lists every id in the project instead of the ones that matter
> here, or it goes stale. A map is only worth reading if it is shorter than the thing it maps.
> The failure that actually hurts: an id that used to resolve and no longer does. It does not
> merely fail to help — it sends an agent looking for something that is not there, and an
> agent willing to infer will fill the hole itself.
>
> **Checked by** — `CTX-001` warns when a governed directory has no `index.md`, and `CTX-002`
> **fails** when an id-shaped token here does not resolve. That split is the project's rule in
> miniature: a missing thing warns, a misleading thing fails. **Nothing checks what this map
> leaves out.** `CTX-002` reads the ids that are here; an artifact the map never mentions is
> invisible to it, so a map can be entirely correct and still send an agent nowhere useful.
>
> **Authority** — whoever owns the directory. No approval needed; this is navigation, not a
> decision.

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
