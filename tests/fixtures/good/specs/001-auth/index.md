# Feature Index — Vehicle Authentication

> The context map for this feature (specup.md s9). An agent navigates
> `directory -> AGENTS.md -> index.md -> the one artifact it needs`, instead of loading the
> repository. Every identifier below must resolve: `CTX-002` fails if one does not, because a
> map pointing at something that is not there is worse than no map.

## Purpose

Certificate-based authentication for vehicles joining the platform.

## Artifacts

- **Business objective** — BUS-OBJ-0017
- **Requirements** — REQ-AUTH-0014, NON-FR-AUTH-0017
- **User story** — USR-STR-0014
- **Acceptance criteria** — AC-AUTH-0014-0003, AC-AUTH-0014-0004
- **Architecture decision** — ADR-0019
- **WBS root** — WBS-1.2.3.4
- **Risks** — RISK-0007 (open, high), RISK-0012
- **Tests** — TC-AUTH-0031, UNIT-AUTH-0031
- **Evidence** — EVID-0001

## Files

| | |
|---|---|
| `acceptance/vehicle-auth.feature` | SCEN-AUTH-0031, SCEN-AUTH-0032 |
| `contracts/authentication.openapi.yaml` | CONTRACT-AUTH-0001 |

## Checking state

```bash
python3 .specify/extensions/openup/scripts/python/impact.py --of REQ-AUTH-0014
python3 .specify/extensions/openup/scripts/python/audit.py
```
