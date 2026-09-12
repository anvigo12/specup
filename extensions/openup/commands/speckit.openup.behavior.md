---
description: "Write Gherkin scenarios bound by tag to acceptance criteria and requirements"
---

# Behavioral Specification

Write Gherkin that bridges business intent and executable verification (specup.md s23), and
bind it into the graph by tag so each scenario becomes a traceable node rather than prose in
a file.

## User Input

```text
$ARGUMENTS
```

A requirement id, acceptance criterion id, or feature to write scenarios for.

## Prerequisites

- The acceptance criteria exist in `.specify/traceability/requirements.yaml` as `AC-*` artifacts.
- If they do not, write them **first**. A scenario invented without a criterion behind it is
  the model deciding what "correct" means, which is the one thing this workflow exists to
  prevent (s51: resolve or stop, never infer).

## Tag binding

Every feature file carries the requirement it serves; every scenario carries the criterion it
executes and the test case it becomes:

```gherkin
@REQ-AUTH-0014
@WBS-1.2.3.4.1.1.3
Feature: Vehicle certificate authentication

  @AC-AUTH-0014-0003
  @TC-AUTH-0031
  Scenario: Invalid vehicle certificate
    Given a vehicle has an invalid certificate
    When the vehicle requests authentication
    Then the authentication request is rejected
```

Tags use the frozen ID grammar — zero-padded, four digits. `@REQ-AUTH-014` is not a valid id
and will not bind.

## Rules

- **Every acceptance criterion needs at least one scenario** (s24). Report any `AC-*` with none.
- **Every scenario needs a criterion and a requirement.** An untagged scenario is an orphan (`TRC-008`).
- **A scenario that exercises an API references its contract.** Add a `conforms-to` edge from the implementation to the `CONTRACT-*` id.
- **Write behavior, not implementation.** `Given a vehicle has an invalid certificate`, not `Given validateCertificate returns false`. A scenario coupled to the implementation stops being a specification.
- **Cover the negative paths.** The criterion in the example is about *rejection*; a suite that only proves the happy path has not verified it.

## Placement

`specs/<feature>/acceptance/<name>.feature`, matching `gherkin.features_glob` in the config.

## Steps

1. Read the requirement and every acceptance criterion bound to it.
2. Write one scenario per criterion, minimum. Add scenarios for the boundary and failure cases
   the criterion implies.
3. Register each scenario as a `SCEN-*` artifact in `requirements.yaml` with its `source` path.
4. Derive the edges:

   ```bash
   python .specify/extensions/openup/scripts/python/validate_trace.py --json
   ```

   `SCEN-* → executes → AC-*` is derived by `gherkin-tag-scan`; it should not be written by hand.
5. Ensure the WBS test node that owns this work has `kind: test` and lists these acceptance
   criteria — otherwise `WBS-007` fails.
6. Report which criteria now have scenarios and which still have none.

## Gherkin is not the contract layer

Gherkin answers *does the system behave as the business expects*. Whether the implementation
conforms to the agreed API interaction contract is a different question, answered by the
contract layer (`conforms-to`, and Microcks once enabled). Do not try to make scenarios carry
both — s25 separates them for a reason.
