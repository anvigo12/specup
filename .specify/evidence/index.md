# Evidence — SpecUP

> **Answers** — what a gate looks for in this directory, and what is actually in it.
>
> **Does not answer** — whether the evidence is good. Every check here resolves a reference
> or reads a status field; none of them evaluates the thing being pointed at.
>
> **Filled in badly when** — a JSON record is written by hand to satisfy a gate. The three
> evidence-backed conditions read a file and trust its `status` field, so an
> `acceptance-results.json` typed by a person is indistinguishable from one a test run
> produced. That is the loosest surface in the whole model.
>
> **Checked by** — `CTX-002` fails an id here that resolves to nothing. `DOD-001` fails a
> `done` node whose `evidence` reference does not resolve — it checks the reference, never the
> file.
>
> **Authority** — the maintainer.

## What is here

**Nothing.** This directory holds no evidence records, and three gate conditions fail because
of it:

| Condition | Looks for | Gate |
|---|---|---|
| `acceptance_scenarios_passing` | `.specify/evidence/acceptance-results.json` | Construction — **the one SpecUP currently fails** |
| `security_review_complete` | `.specify/evidence/security-review.json` | Elaboration |
| `security_validation_passed` | `.specify/evidence/security-validation.json` | Transition |

None of the three is being repaired, and the reason is the same each time: the file would be
written by hand. `acceptance_scenarios_passing` asks for executed Gherkin scenarios; SpecUP
has no `.feature` files, and its acceptance is a pytest suite the model expresses as `UNIT-*`
artifacts verifying requirements. Producing the JSON from a pytest run would satisfy the
condition with a document that describes a different kind of evidence.

`absence of evidence is not evidence` is the constitutional principle at issue, and it cuts
both ways: a missing record fails, and a fabricated one passes.

## Evidence that does exist, registered elsewhere

Six `EVID-*` artifacts are registered in `.specify/traceability/requirements.yaml` and pointed
at by the WBS nodes claiming `done`. Each one is a path to something a reviewer can open:

| Id | Points at |
|---|---|
| `EVID-0001` | the 0.1.1 release notes |
| `EVID-0002` | the approval validator |
| `EVID-0003` | the docstring validator |
| `EVID-0004` | the template suite |
| `EVID-0005` | the worked-example suite |
| `EVID-0006` | the generated coverage view — the verification reference for `RISK-0003` |

`DOD-001` resolves each of those references and stops there. Nothing opens the file, so
"evidence" here means a pointer a person can follow, not a fact a machine has established.
