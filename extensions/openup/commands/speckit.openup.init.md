---
description: "Scaffold the OpenUP governance tree: lifecycle, WBS, risks, traceability, evidence"
---

# Initialize OpenUP Governance

Create the directories and canonical stores that every other OpenUP command reads and writes.

## User Input

```text
$ARGUMENTS
```

Treat the input as the **program name** for the WBS root if it looks like one. Otherwise ask for it.

## Prerequisites

- The project is already a Spec Kit project (`.specify/` exists). If not, tell the user to run `specify init` first and stop.
- Python 3.10+ is available.

## Execution

```bash
python .specify/extensions/openup/scripts/python/init_openup.py --program "<program name>" --json
```

The script never overwrites an **authored** file. Re-running it is safe and is the supported way to restore a deleted store.

It then generates `definition-of-ready.md`, `definition-of-done.md` and `quality-gates.md` from the code that enforces them, so the document and the check cannot disagree. Those three are owned by the code and *are* rewritten on a re-run.

Exit codes follow the usual contract: `0` scaffolded and generated, `2` the scaffold was written but generation could not run — report that to the user as a missing dependency (`pip install -r .specify/extensions/openup/requirements.txt`) and do not treat it as success. Pass `--no-render` only if the user explicitly wants the scaffold without the generated documents.

## What it creates

| Path | Role |
|---|---|
| `.specify/lifecycle/` | vision, stakeholders, index — Inception artifacts |
| `.specify/governance/` | definition-of-ready, definition-of-done, approval matrix |
| `.specify/architecture/` | architecture.md and decision records |
| `.specify/wbs/wbs.yaml` | canonical seven-level WBS |
| `.specify/risks/risk-register.yaml` | canonical risk register |
| `.specify/traceability/requirements.yaml` | governed artifacts (requirements, ACs, contracts, ADRs) |
| `.specify/traceability/traceability.yaml` | the relation store |
| `.specify/evidence/` | verification evidence consumed by gates |
| `.specify/extensions/openup/openup-config.yml` | thresholds, perimeter, gate definitions |

## Steps

1. Run the script and report what was created versus preserved.
2. Read `.specify/extensions/openup/openup-config.yml` and confirm two things with the user, because both change what the gates enforce:
   - **`traceability.perimeter`** — which source paths must be traced. The default (`src/**`) is a guess; a wrong perimeter makes backward coverage either meaningless or impossible.
   - **`risk.high_exposure_threshold`** — the exposure at or above which a risk must have mitigation work and verification. Default `0.40`.
3. Set `lifecycle.phase` to `INCEPTION` unless the project is demonstrably further along.
4. Fill `.specify/lifecycle/vision.md` and `stakeholders.md` from what the user tells you. Do **not** invent business objectives, owners, or approvers — an unowned requirement fails the Inception gate, and inventing an owner hides that rather than fixing it.
5. Report the next step: `/speckit.openup.wbs` to build the L1–L3 skeleton.

## Notes

- Everything seeded here enters at status `DRAFT`. Generated does not mean approved.
- A freshly scaffolded project **fails** `/speckit.openup.gate` on purpose: an empty plan is not a valid plan. Use the failures as the to-do list.
