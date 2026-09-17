# Risks — SpecUP

> **Answers** — what is on the register, which side of the threshold each one falls, and what
> the model then requires of it.
>
> **Does not answer** — whether the register is complete. Nothing can: a risk nobody wrote
> down is invisible to every check in this project.
>
> **Filled in badly when** — a probability is chosen after looking at the threshold. Exposure
> is probability × impact, and 0.40 is where mitigation and verification become mandatory, so
> any number just under it buys silence.
>
> **Checked by** — `CTX-002` fails an id here that resolves to nothing.
>
> **Authority** — the maintainer, who owns every entry. That is `RISK-0001`.

## The register

| Id | Exposure | Status | What the model then requires |
|---|---|---|---|
| `RISK-0001` | 0.54 | accepted | nothing — an accepted risk is a decision, and the approval is what makes it one |
| `RISK-0002` | 0.30 | open | nothing; below the threshold, and carrying it untouched is allowed |
| `RISK-0003` | 0.42 | open | mitigation work **and** a verification reference; both are present |
| `RISK-0004` | 0.08 | open | nothing |
| `RISK-0005` | 0.32 | open | nothing; below the threshold, and the entry argues with its own impact estimate |
| `RISK-0006` | 0.105 | open | nothing, and no mitigation exists — the rights are already granted |

## What each one is, in a sentence

- **`RISK-0001`** — every approval SpecUP records is signed by the only person who could have
  recorded it. Accepted, by an approval that is itself unwitnessed. Reopen when a second
  person has commit rights; nothing before that event changes it.
- **`RISK-0002`** — nothing checks that the operating manual describes the code that shipped.
  Below the threshold because the manual is currently small enough for one person to re-read
  at release time. Raise the probability, not the threshold, when that stops being true.
- **`RISK-0003`** — an error in SpecUP's own traceability graph would not be detectable by
  SpecUP, because 83% of it is `asserted` and its own test-naming rule reproduces one edge.
  Mitigated by `WBS-1.1.3.1`; verified by `EVID-0006`, the regenerated coverage view, whose
  derived counts cannot be moved by relabelling.
- **`RISK-0004`** — the scaffold seeds an operating contract into `src/`, which not every
  project has. More a defect than a risk, and it is here because this repository has no issue
  tracker inside the graph.
- **`RISK-0005`** — BUSL-1.1 makes SpecUP ineligible for Spec Kit's community catalogs, whose
  publishing guide requires an open source licence file. Impact is held at 0.4 because those
  catalogs are discovery-only and every install goes through SpecUP's own catalog; the entry
  states that the arithmetic preceded the threshold, and names the argument for 0.5.
- **`RISK-0006`** — the engine being monetised is already published under MIT at `v0.1.1`, and
  that grant cannot be withdrawn. Probability is low only because the project is small, so it
  rises with every sign of success — a number to re-estimate on good news.

## The threshold is what makes this consequential

`high_exposure_threshold` is 0.40 and `critical_exposure_threshold` is 0.65, both in
`.specify/extensions/openup/openup-config.yml`. At or above the first, a risk must point at
real work and declare how the reduction will be proved, or the Elaboration gate fails. Nothing
here is above the second, which is why `no_open_critical_risks` passes at the Construction
gate.

Lowering either number would move risks out of scope without anything recording that it
happened. Lower one as a decision; never as a repair.

## Where to look

| Question | File |
|---|---|
| The register | `.specify/risks/risk-register.yaml` |
| Rendered | `.specify/risks/risk-register.md` — generated, never edit |
| Are the rules met | `python3 extensions/openup/scripts/python/validate_risk.py` |
| What does changing one reach | `python3 extensions/openup/scripts/python/impact.py --of RISK-0003` |
