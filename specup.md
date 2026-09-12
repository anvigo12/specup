# SpecUP: GitHub Spec Kit + Eclipse OpenUP Governed AI-Native SDLC

> **SpecUP** is a proposed extension of GitHub Spec Kit that combines Spec Kit's AI-native specification-driven development workflow with the Eclipse OpenUP iterative software development lifecycle. It adds a machine-checkable governance layer based on a seven-level Work Breakdown Structure (WBS), Risk Register, bi-directional traceability, Gherkin, Microcks, `AGENTS.md`, `SKILL.md`, filesystem-first rules, and lifecycle quality gates.

---

## 1. Executive Summary

The strongest way to extend GitHub Spec Kit with OpenUP is **not to replace Spec Kit's Spec → Plan → Tasks → Implement flow**, but to turn it into the **AI execution engine inside an OpenUP-governed lifecycle**.

The resulting model is:

> **OpenUP governs why, when, who, risk, lifecycle, milestones, and acceptance; Spec Kit governs how an AI agent progressively transforms those governed artifacts into implementation; the filesystem becomes the auditable state machine.**

Conceptually:

```text
┌──────────────────────────────────────────────────────────────┐
│                    GOVERNANCE / CONSTITUTION                 │
│  Principles • Definition of Done • Quality Gates • Policies  │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                         OPENUP LIFECYCLE                     │
│ Inception → Elaboration → Construction → Transition          │
│ Milestones • Iterations • Roles • Work Products              │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                    SPECIFICATION SYSTEM                      │
│ Spec • User Stories • Acceptance Criteria • Gherkin          │
│ Architecture • Data Model • Contracts                        │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                      PLANNING SYSTEM                         │
│ 7-Level WBS • Tasks • Dependencies • Estimates • Iteration   │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                     ENGINEERING SYSTEM                       │
│ Code • Tests • OpenAPI • AsyncAPI • Microcks • CI/CD         │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                 TRACEABILITY / ASSURANCE                     │
│ Requirement ↔ WBS ↔ Risk ↔ Design ↔ Code ↔ Test ↔ Contract   │
└──────────────────────────────────────────────────────────────┘
```

The result should be understood as an **AI-native, filesystem-governed, evidence-producing implementation of OpenUP**, rather than simply an OpenUP-flavored Spec Kit template.

---

# 2. Why Combine Spec Kit and OpenUP?

GitHub Spec Kit provides the AI-oriented portion of the development workflow:

```text
Constitution
    ↓
Specify
    ↓
Clarify / Checklist
    ↓
Plan
    ↓
Tasks
    ↓
Implement
    ↓
Analyze / Converge
```

OpenUP contributes the project and engineering governance layer:

```text
Lifecycle
Iterations
Milestones
Roles
Risk management
Architecture governance
Work breakdown
Stakeholder visibility
Quality gates
```

This creates a useful separation of concerns:

| Concern | Spec Kit | OpenUP / SpecUP |
|---|---|---|
| What are we building? | Strong | Strong |
| AI-assisted specification | Strong | Preserved |
| Technical planning | Strong | Governed |
| Task generation | Strong | WBS-constrained |
| AI implementation | Strong | Governed |
| Lifecycle governance | Limited | Strong |
| Risk governance | Limited | Strong |
| Iteration management | Limited | Strong |
| Phase milestones | Limited | Strong |
| Stakeholder governance | Limited | Strong |
| WBS | Task-oriented | Seven-level governed |
| Traceability | Extensible | First-class |
| Executable API contracts | Extensible | First-class |
| Agent instructions | External convention | `AGENTS.md` hierarchy |
| Agent skills | External convention | `SKILL.md` hierarchy |

Therefore:

```text
OpenUP       = governance and lifecycle
Spec Kit     = AI-native transformation engine
SpecUP       = governed integration of both
```

---

# 3. Core Design Principle

The most important principle is:

> **The LLM is an executor and transformer of governed project artifacts, not the authority that defines project truth.**

The repository is the authority.

A valid development action follows:

```text
Human Intent
    ↓
Filesystem Artifact
    ↓
Validated Artifact
    ↓
Next Artifact
    ↓
Validated Artifact
    ↓
Implementation
    ↓
Verification Evidence
    ↓
Traceability
```

The AI is never the only place where project state exists.

This gives:

- reproducibility
- auditability
- reviewability
- deterministic context retrieval
- rollback
- branch comparison
- agent interoperability
- explicit human approval points

---

# 4. Filesystem-First Compliance

The core SpecUP governance principle should be:

> **No AI action is valid unless its governing artifact exists in the filesystem and its resulting state can be reconstructed from version-controlled files.**

A complete development chain looks like:

```text
Requirement
    ↓
spec.md
    ↓
Acceptance Criteria
    ↓
Gherkin
    ↓
WBS
    ↓
Task
    ↓
Code
    ↓
Tests
    ↓
OpenAPI / AsyncAPI
    ↓
Microcks
    ↓
Evidence
    ↓
Traceability
```

## 4.1 FS-001: Filesystem Authority

Every governed development action MUST correspond to a version-controlled artifact.

No implementation may be considered authoritative unless:

1. its governing requirement exists;
2. its WBS node exists;
3. its task exists;
4. required acceptance criteria exist;
5. applicable risks are registered;
6. implementation evidence exists;
7. verification evidence exists;
8. traceability is updated.

The absence of any required artifact invalidates the action.

## 4.2 FS-002: No Invisible State

No important project state may exist only:

- in an LLM conversation;
- in agent memory;
- in an IDE session;
- in temporary generated output;
- in an uncommitted local artifact.

The repository is the durable state store.

---

# 5. Repository Architecture

A proposed repository structure:

```text
project/
│
├── AGENTS.md
├── README.md
├── CHANGELOG.md
│
├── .specify/
│   ├── AGENTS.md
│   │
│   ├── memory/
│   │   └── constitution.md
│   │
│   ├── lifecycle/
│   │   ├── lifecycle.yaml
│   │   ├── phases.md
│   │   ├── milestones.md
│   │   └── iterations.md
│   │
│   ├── governance/
│   │   ├── definition-of-ready.md
│   │   ├── definition-of-done.md
│   │   ├── quality-gates.md
│   │   ├── change-control.md
│   │   └── approval-matrix.md
│   │
│   ├── wbs/
│   │   ├── wbs.yaml
│   │   ├── wbs.md
│   │   └── schemas/
│   │
│   ├── risks/
│   │   ├── risk-register.yaml
│   │   ├── risk-register.md
│   │   └── history/
│   │
│   ├── traceability/
│   │   ├── requirements.yaml
│   │   ├── traceability.yaml
│   │   ├── traceability.md
│   │   └── coverage.md
│   │
│   ├── templates/
│   │   ├── openup/
│   │   ├── wbs/
│   │   ├── risk/
│   │   └── traceability/
│   │
│   └── schemas/
│       ├── wbs.schema.json
│       ├── risk.schema.json
│       ├── traceability.schema.json
│       └── artifact.schema.json
│
├── specs/
│   ├── 001-feature-a/
│   │   ├── AGENTS.md
│   │   ├── index.md
│   │   ├── spec.md
│   │   ├── clarify.md
│   │   ├── plan.md
│   │   ├── research.md
│   │   ├── data-model.md
│   │   ├── quickstart.md
│   │   │
│   │   ├── wbs/
│   │   │   ├── wbs.md
│   │   │   └── wbs.yaml
│   │   │
│   │   ├── risks/
│   │   │   └── risk-register.yaml
│   │   │
│   │   ├── traceability/
│   │   │   ├── matrix.yaml
│   │   │   └── matrix.md
│   │   │
│   │   ├── acceptance/
│   │   │   ├── feature-001.feature
│   │   │   └── ...
│   │   │
│   │   ├── contracts/
│   │   │   ├── openapi.yaml
│   │   │   └── asyncapi.yaml
│   │   │
│   │   └── tasks.md
│   │
│   └── ...
│
├── skills/
│   ├── requirements/
│   │   └── SKILL.md
│   ├── architecture/
│   │   └── SKILL.md
│   ├── wbs/
│   │   └── SKILL.md
│   ├── risk/
│   │   └── SKILL.md
│   ├── traceability/
│   │   └── SKILL.md
│   ├── gherkin/
│   │   └── SKILL.md
│   ├── contracts/
│   │   └── SKILL.md
│   └── microcks/
│       └── SKILL.md
│
├── src/
│   └── ...
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── acceptance/
│   └── contract/
│
└── infra/
    └── ...
```

The architecture deliberately distinguishes:

```text
Human-readable artifacts
    ↓
Markdown
```

from:

```text
Machine-readable artifacts
    ↓
YAML / JSON
```

and uses Git for historical state.

---

# 6. Do Not Turn `constitution.md` Into a Monolith

A common failure mode is putting all governance into one enormous:

```text
constitution.md
```

That eventually becomes a context and maintenance bottleneck.

Instead use layered governance:

```text
AGENTS.md
   │
   ├── global agent operating rules
   │
   └── project-level context
             │
             ▼
.specify/
   │
   ├── constitution.md
   ├── lifecycle/
   ├── governance/
   ├── schemas/
   └── templates/
```

Then localize rules:

```text
AGENTS.md

src/AGENTS.md

src/api/AGENTS.md

tests/AGENTS.md

specs/AGENTS.md

.specify/AGENTS.md
```

This gives **instruction locality**.

The agent should not need to consume project-wide policy when working on a small localized task.

---

# 7. `AGENTS.md` as the Agent Operating Contract

`AGENTS.md` should answer:

> **How is an agent allowed to operate in this repository?**

Example:

```markdown
# Agent Operating Contract

## Mandatory Startup

Before changing anything:

1. Read the nearest applicable AGENTS.md.
2. Read the corresponding index.md.
3. Resolve all referenced artifacts.
4. Determine current OpenUP phase.
5. Determine current iteration.
6. Determine applicable WBS node.
7. Determine applicable risks.
8. Determine affected requirements.
9. Determine applicable SKILL.md files.

## Filesystem-First Rule

Never create implementation changes without:

- a governing requirement;
- a WBS item;
- an applicable task;
- applicable acceptance criteria;
- traceability entries.

## Prohibited

- bypassing quality gates;
- creating undocumented APIs;
- modifying contracts without updating requirements;
- marking tasks complete without evidence;
- inventing missing requirements;
- silently modifying architecture decisions.

## Required

Every implementation change must produce:

Requirement
→ WBS
→ Task
→ Code
→ Test
→ Evidence
→ Traceability update

## Boundaries and Hard Rules
1. ALWAYS DO
- Follow best practices and project guidelines
2. ASK HUMAN
- Human approval mandatory for destructive actions
3. NEVER DO
- Commit PII or secrets into version control system
```

The key separation is:

```text
AGENTS.md = governance / operating rules
```

---

# 8. `SKILL.md` as the Agent Capability Contract

`SKILL.md` should answer:

> **How do I perform this particular engineering activity?**

This should be different from `AGENTS.md`.

Example:

```text
skills/
└── wbs/
    └── SKILL.md
```

Example content:

```markdown
# WBS Generation Skill

## Purpose

Generate and maintain a seven-level OpenUP-compatible
Work Breakdown Structure.

## Inputs

- lifecycle.yaml
- iteration definition
- requirements
- risks
- architecture
- constraints

## Rules

- maximum depth = 7
- every leaf must be executable
- every leaf must have an owner
- every leaf must belong to an iteration
- every leaf must reference at least one requirement
- risk mitigation tasks must reference risk IDs
- test tasks must reference acceptance criteria

## Output

.specify/wbs/wbs.yaml
.specify/wbs/wbs.md

## Validation

Run:

./tools/validate-wbs
```

The resulting separation is:

```text
AGENTS.md = WHAT RULES MUST I OBEY?
SKILL.md  = HOW DO I PERFORM THIS ACTIVITY?
```

This is a strong foundation for multi-agent operation.

---

# 9. The `index.md` Context Map

Each governed directory should contain an `index.md`.

Example:

```text
specs/001-auth/
├── AGENTS.md
├── index.md
├── spec.md
├── plan.md
├── wbs/
├── risks/
├── traceability/
├── acceptance/
└── contracts/
```

Example `index.md`:

```markdown
# Feature Index

## Purpose

Vehicle certificate authentication.

## Artifacts

- `spec.md`
  - Requirements:
    - REQ-AUTH-014
    - REQ-AUTH-015

- `wbs/wbs.md`
  - Root:
    - WBS-1.2.3.4

- `risks/risk-register.yaml`
  - RISK-007

- `acceptance/vehicle-auth.feature`
  - AC-AUTH-014-03

- `contracts/authentication.openapi.yaml`
  - POST /v1/authenticate

## Traceability

- `traceability/matrix.yaml`
```

The agent can then navigate:

```text
directory
    ↓
AGENTS.md
    ↓
index.md
    ↓
relevant artifact
```

instead of dumping the entire repository into context.

This is a **progressive disclosure** strategy.

---

# 10. OpenUP Lifecycle Mapping

OpenUP divides development into:

```text
Inception
    ↓
Elaboration
    ↓
Construction
    ↓
Transition
```

with iterations within phases.

SpecUP should explicitly map Spec Kit activities to these phases.

---

# 11. Inception

## Primary question

> **Should we build this?**

Typical artifacts:

```text
vision.md
business-case.md
stakeholders.md
initial-risk-register.yaml
initial-wbs.yaml
initial-requirements.md
```

Spec Kit contribution:

```text
constitution
specify
clarify
```

Gate:

```text
Lifecycle Objectives Milestone
```

The purpose is to establish business intent, initial scope, stakeholders, feasibility and the highest-level risks before major investment.

---

# 12. Elaboration

## Primary question

> **Can we build it?**

This should be the most architecture-heavy phase.

Artifacts:

```text
architecture.md
architecture-decisions/
data-model.md
contracts/
threat-model.md
risk-register.yaml
wbs.yaml
traceability.yaml
```

Spec Kit contribution:

```text
plan
research
data-model
contracts
```

Gate:

```text
Lifecycle Architecture Milestone
```

The central objective is to establish an executable architecture and address the highest-value risks before scaling implementation.

---

# 13. Construction

## Primary question

> **Can we build the product incrementally and verify each increment?**

Each iteration becomes:

```text
Iteration
    ↓
Select WBS nodes
    ↓
Generate tasks
    ↓
Implement
    ↓
Unit tests
    ↓
Integration tests
    ↓
Gherkin acceptance tests
    ↓
Microcks contract tests
    ↓
Traceability update
    ↓
Iteration review
```

This is where Spec Kit becomes the AI execution engine within OpenUP's iterative governance.

---

# 14. Transition

## Primary question

> **Can the system be safely released and operated?**

Artifacts:

```text
release-readiness.md
deployment-plan.md
operations.md
security-validation.md
known-issues.md
acceptance-report.md
traceability-final.md
```

Gate:

```text
Product Release Milestone
```

Transition should validate deployment, operations, acceptance and release readiness rather than treating "code complete" as equivalent to "ready to release".

---

# 15. Seven-Level Work Breakdown Structure

SpecUP should enforce exactly seven semantic WBS levels.

Recommended model:

```text
L1  Program / Product
L2  OpenUP Phase
L3  Iteration
L4  Capability / Feature
L5  Requirement / User Story
L6  Engineering Work Package
L7  Executable Task
```

Example:

```text
1       Autonomous Traffic Platform
│
└── 1.2     Elaboration
     │
     └── 1.2.3     Iteration E2
          │
          └── 1.2.3.4     Vehicle Authentication
               │
               └── 1.2.3.4.1     Secure vehicle onboarding
                    │
                    ├── 1.2.3.4.1.1   Define certificate contract
                    │
                    ├── 1.2.3.4.1.2   Implement certificate validation
                    │
                    └── 1.2.3.4.1.3   Add negative-path tests
```

The seven levels are not intended to create seven levels of prose.

They create **seven levels of scope and execution resolution**.

---

# 16. Why Seven WBS Levels Matter for AI

The hierarchy provides natural reasoning boundaries.

```text
L1  Product
    → strategic context

L2  Phase
    → lifecycle objective

L3  Iteration
    → near-term delivery goal

L4  Capability
    → functional scope

L5  Requirement
    → expected behavior

L6  Work Package
    → engineering slice

L7  Task
    → executable unit
```

Thus:

```text
Strategic Context
       ↓
Lifecycle Context
       ↓
Iteration Context
       ↓
Feature Context
       ↓
Requirement Context
       ↓
Engineering Context
       ↓
Execution Context
```

This effectively becomes **hierarchical context engineering for software agents**.

---

# 17. Machine-Readable WBS

The authoritative representation should be YAML or JSON.

Example:

```yaml
id: "1.2.3.4.1.2"
name: "Implement certificate validation"

level: 7

phase: "ELABORATION"

iteration: "E2"

parent: "1.2.3.4.1"

requirements:
  - "REQ-AUTH-014"

risks:
  - "RISK-007"

acceptance:
  - "AC-AUTH-014-03"

dependencies:
  - "1.2.3.4.1.1"

owner: "backend-team"

status: "planned"

estimate:
  unit: "hours"
  value: 8
```

`wbs.md` should be a generated human-readable view.

---

# 18. WBS Invariants

Machine-checkable invariants should include:

```text
Every L7 task:
    → maps to an iteration
    → maps to a requirement
    → has executable scope
    → has an owner
```

Further:

```text
Every child node:
    → has exactly one parent

Every leaf:
    → must be L7

Maximum depth:
    → exactly 7

Every risk mitigation task:
    → references a risk ID

Every test task:
    → references acceptance criteria
```

---

# 19. Risk Register

The Risk Register should not be passive documentation.

It must influence the WBS.

Example:

```yaml
id: RISK-007

title: Certificate validation latency

category: technical

probability: 0.6
impact: 0.9

exposure: 0.54

phase_identified: ELABORATION

status: open

owner: security-team

mitigation:
  - WBS-1.2.3.4.1.2
  - WBS-1.2.3.4.1.3

verification:
  - TEST-PERF-022

residual_probability: 0.2
residual_impact: 0.5

residual_exposure: 0.10
```

Recommended invariant:

```text
Every high-exposure risk
must have at least one mitigation WBS item.
```

And:

```text
Every mitigation WBS item
must produce evidence.
```

Therefore:

```text
Risk
 ↓
Mitigation
 ↓
Implementation
 ↓
Verification
 ↓
Evidence
 ↓
Residual Risk
```

This turns risk management into executable engineering work.

---

# 20. Bi-Directional Traceability

Traditional traceability often stops at:

```text
Requirement → Test
```

SpecUP should build a richer relationship graph:

```text
Business Objective
       ↕
Requirement
       ↕
User Story
       ↕
Acceptance Criterion
       ↕
Gherkin Scenario
       ↕
WBS
       ↕
Task
       ↕
Design Decision
       ↕
Source Code
       ↕
Unit/Integration Test
       ↕
API Contract
       ↕
Microcks Test
       ↕
Evidence
```

The traceability system must work in both directions.

Examples:

```text
Requirement → implementation
```

and:

```text
Implementation → requirement
```

and:

```text
Risk → mitigation → implementation → verification
```

and:

```text
API Contract → implementation → test → requirement
```

---

# 21. Machine-Readable Traceability Model

Recommended relation schema:

```yaml
from_id: "REQ-AUTH-014"
from_type: "requirement"
relation: "implemented-by"
to_id: "WBS-1.2.3.4.1.2"
to_type: "wbs"
source_file: "specs/001-auth/traceability/matrix.yaml"
evidence:
  - "src/security/certificate_validator.ts"
status: "verified"
```

Example complete chain:

```yaml
- from: "REQ-AUTH-014"
  relation: "implemented-by"
  to: "WBS-1.2.3.4.1.2"

- from: "WBS-1.2.3.4.1.2"
  relation: "implemented-by"
  to: "TASK-042"

- from: "TASK-042"
  relation: "modifies"
  to: "src/security/certificate_validator.ts"

- from: "REQ-AUTH-014"
  relation: "verified-by"
  to: "AC-AUTH-014-03"

- from: "AC-AUTH-014-03"
  relation: "executed-by"
  to: "features/auth/certificate.feature"

- from: "certificate.feature"
  relation: "validated-by"
  to: "MICROCKS-TEST-91"
```

---

# 22. Why Bi-Directional Traceability Matters

The system should support questions such as:

> Which requirements are affected by this source-code change?

and:

> Which files, tests and contracts implement this requirement?

For example:

```text
REQ-AUTH-014
      ↓
WBS-1.2.3.4.1.2
      ↓
TASK-042
      ↓
certificate_validator.ts
      ↓
unit tests
      ↓
OpenAPI
      ↓
Microcks
```

The reverse query must also be possible:

```text
certificate_validator.ts
      ↓
TASK-042
      ↓
WBS-1.2.3.4.1.2
      ↓
REQ-AUTH-014
      ↓
BO-17
```

This creates explainability rather than merely documentation.

---

# 23. Gherkin as the Behavioral Bridge

Gherkin should bridge:

```text
Business Requirement
        ↓
Acceptance Criteria
        ↓
Executable Behavioral Test
```

Example:

```gherkin
Feature: Vehicle certificate authentication

  Scenario: Valid vehicle certificate
    Given a vehicle has a valid certificate
    And the certificate is within its validity period
    When the vehicle requests authentication
    Then the authentication request is accepted
    And the vehicle identity is established
```

For traceability, add explicit IDs:

```gherkin
@REQ-AUTH-014
@AC-AUTH-014-03
@WBS-1.2.3.4.1.3
Feature: Vehicle certificate authentication

  @TC-AUTH-031
  Scenario: Valid vehicle certificate
    Given a vehicle has a valid certificate
    When the vehicle requests authentication
    Then the request is accepted
```

The scenario itself becomes a graph node.

---

# 24. Gherkin Invariants

Recommended invariants:

```text
Every acceptance criterion
    → has at least one Gherkin scenario
```

And:

```text
Every Gherkin scenario
    → maps to an acceptance criterion
    → maps to a requirement
```

Further:

```text
Every scenario that exercises an API
    → references the relevant API contract
```

---

# 25. Microcks as the Contract Execution Layer

Microcks should serve as the API contract and conformance layer.

The useful architectural split is:

### Behavioral verification

```text
Gherkin
```

answers:

> Does the system behave as the user/business expects?

### Contract verification

```text
Microcks
```

answers:

> Does the implementation conform to the agreed API interaction contract?

This gives:

```text
Gherkin
   │
   │ business behavior
   ▼
Acceptance Criteria
   │
   ▼
OpenAPI / AsyncAPI
   │
   ▼
Microcks
   │
   ├── mock provider
   ├── consumer testing
   └── provider conformance
```

This separation is extremely useful for distributed systems and API-centric architectures.

---

# 26. Example End-to-End Requirement Chain

Consider:

```text
Business Objective

BO-17:
Enable authenticated vehicle communication.
```

Requirement:

```text
REQ-AUTH-014

Vehicle must authenticate using a valid certificate.
```

User story:

```text
US-014

As a vehicle,
I want certificate-based authentication,
so that unauthorized vehicles are rejected.
```

Acceptance criterion:

```text
AC-AUTH-014-03

Invalid certificates must be rejected.
```

Gherkin:

```gherkin
@REQ-AUTH-014
@AC-AUTH-014-03
Scenario: Invalid vehicle certificate
  Given a vehicle has an invalid certificate
  When the vehicle requests authentication
  Then the authentication request is rejected
```

WBS:

```text
WBS-1.2.3.4.1
Secure vehicle authentication
```

Tasks:

```text
TASK-041
Implement certificate parser

TASK-042
Implement certificate validator

TASK-043
Implement authentication endpoint

TASK-044
Implement negative-path tests
```

Implementation:

```text
src/security/certificate_validator.*
```

Tests:

```text
tests/unit/certificate_validator.*
tests/acceptance/vehicle_auth.*
```

Contract:

```text
contracts/authentication.openapi.yaml
```

Microcks:

```text
MICROCKS-TEST-91
```

Traceability:

```text
BO-17
  ↕
REQ-AUTH-014
  ↕
US-014
  ↕
AC-AUTH-014-03
  ↕
Gherkin
  ↕
WBS-1.2.3.4.1
  ↕
TASK-042
  ↕
certificate_validator
  ↕
unit tests
  ↕
OpenAPI
  ↕
Microcks
```

---

# 27. Transforming `/speckit.tasks`

A normal task-generation process can be strengthened significantly.

Instead of generating tasks from only:

```text
requirements
+
plan
```

SpecUP should generate tasks from:

```text
requirements
+
WBS
+
risk register
+
architecture
+
contracts
+
Gherkin
+
current iteration
```

Example task:

```text
[TASK-042]
[WBS-1.2.3.4.1.2]
[REQ-AUTH-014]
[RISK-007]
[AC-AUTH-014-03]

Implement certificate validation.

Preconditions:
- TASK-041 completed.
- Certificate schema approved.

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

The task is now a controlled execution contract for the agent.

---

# 28. Definition of Ready

A task should not be considered executable merely because it exists.

Suggested Definition of Ready:

```text
REQ linked              ✓
Acceptance criteria     ✓
WBS level 7             ✓
Dependencies resolved   ✓
Risk analysis           ✓
Design decision         ✓
Required contract       ✓
Applicable SKILL.md     ✓
Files identified        ✓
```

Therefore:

```text
READY = true
```

only when all mandatory conditions pass.

---

# 29. Definition of Done

A task is done only when:

```text
Implementation complete
Tests complete
Gherkin passing
Contract tests passing
Microcks conformance passing
Security checks passing
Risk updated
Traceability updated
Documentation updated
No orphan artifacts
No broken references
```

Thus:

```text
TASK-042.status = DONE
```

is a computed governance state rather than a casual AI declaration.

---

# 30. Lifecycle and Quality Gates

The OpenUP milestones should become machine-checkable AI gates.

Suggested mapping:

```text
Inception
    ↓
Lifecycle Objectives Gate

Elaboration
    ↓
Lifecycle Architecture Gate

Construction
    ↓
Initial Operational Capability Gate

Transition
    ↓
Product Release Gate
```

Each gate should have machine-readable conditions.

Example:

```yaml
gate: LIFECYCLE_ARCHITECTURE

conditions:
  - all_high_risks_have_mitigation
  - architecture_baselined
  - requirements_traceable
  - critical_contracts_defined
  - security_review_complete
  - WBS_level_1_to_7_valid
```

An LLM must not be allowed to declare:

```text
Architecture looks good.
```

The gate must be supported by evidence.

---

# 31. Governance States

Every important governed artifact should have an explicit state.

Recommended lifecycle:

```text
DRAFT
  ↓
REVIEW
  ↓
APPROVED
  ↓
BASELINED
  ↓
IMPLEMENTED
  ↓
VERIFIED
  ↓
ACCEPTED
```

Example:

```yaml
id: REQ-AUTH-014

status: APPROVED

baseline:
  version: 2

approved_by:
  - product-owner
  - architect

approved_at: 2026-09-10
```

Important principle:

> **Generated does not mean approved.**

---

# 32. Governance Invariants

The system should provide machine-checkable invariants.

## Requirement invariant

```text
Every requirement:
    → has an owner
    → has a priority
    → has acceptance criteria
    → maps to WBS
```

## WBS invariant

```text
Every L7 task:
    → maps to a requirement
    → maps to an iteration
    → has executable scope
```

## Risk invariant

```text
Every high risk:
    → has mitigation
    → has verification
```

## Gherkin invariant

```text
Every acceptance criterion:
    → has >= 1 Gherkin scenario
```

## Contract invariant

```text
Every API requirement:
    → has API contract
    → has contract test
```

## Traceability invariant

```text
Every implementation task:
    → has a forward trace
    → has a backward trace
```

---

# 33. `/speckit.audit`

A first-class audit command should evaluate filesystem-first compliance.

Suggested command:

```text
/speckit.audit
```

It should inspect:

```text
AGENTS.md hierarchy
        ↓
index.md hierarchy
        ↓
constitution
        ↓
OpenUP phase
        ↓
iteration
        ↓
WBS
        ↓
requirements
        ↓
risks
        ↓
tasks
        ↓
source
        ↓
tests
        ↓
contracts
        ↓
Microcks evidence
        ↓
traceability
```

Example output:

```text
OPENUP AI ENGINEERING AUDIT
===========================

Lifecycle
  Phase:        Construction
  Iteration:    C-04
  Status:       PASS

Requirements
  Total:        48
  Covered:      47
  Uncovered:     1
  Status:       FAIL

WBS
  L1: 1
  L2: 4
  L3: 11
  L4: 32
  L5: 74
  L6: 183
  L7: 421
  Orphans: 0
  Status: PASS

Risks
  Open critical: 0
  Open high:     2
  Unmitigated:   0
  Status: PASS

Traceability
  Forward coverage: 100%
  Backward coverage: 97%
  Status: FAIL

Gherkin
  Acceptance scenarios: 116
  Passing: 113
  Failing: 3
  Status: FAIL

Microcks
  Contracts: 22
  Conformance: 98.7%
  Breaking changes: 0
  Status: PASS

FINAL GATE: FAIL

Reasons:
  TRC-001 uncovered requirement
  TEST-042 failing scenario
```

This makes the governance state observable.

---

# 34. Proposed SpecUP Commands

A governed command vocabulary can extend Spec Kit.

## `/speckit.openup-init`

Initializes OpenUP lifecycle and governance artifacts.

## `/speckit.openup-phase`

Sets or evaluates the current OpenUP phase.

## `/speckit.openup-iteration`

Creates or manages an iteration.

## `/speckit.specify`

Creates or updates requirements.

## `/speckit.wbs`

Creates or updates the seven-level WBS.

## `/speckit.risk`

Creates or updates the risk register.

## `/speckit.trace`

Builds or validates bi-directional traceability.

## `/speckit.behavior`

Creates Gherkin acceptance scenarios.

## `/speckit.contract`

Creates or updates OpenAPI / AsyncAPI contracts.

## `/speckit.microcks`

Runs contract/conformance validation against Microcks.

## `/speckit.gate`

Evaluates lifecycle and iteration quality gates.

## `/speckit.implement`

Performs governed implementation.

## `/speckit.audit`

Evaluates filesystem-first compliance and evidence coverage.

---

# 35. Spec Kit Preset Architecture

The recommended implementation is a custom Spec Kit preset rather than a deep fork of Spec Kit.

Conceptually:

```text
GitHub Spec Kit
       │
       ├── core
       │
       ├── SpecUP preset
       │
       ├── optional extensions
       │
       └── project-specific preset
```

Therefore:

```text
Spec Kit Core
      +
OpenUP Governance Preset
      +
Project Domain Preset
      =
Project AI Development System
```

The preset should customize commands, templates and workflows while preserving the underlying Spec Kit engine.

This provides a cleaner upgrade path as Spec Kit evolves.

---

# 36. Preset Responsibilities

The SpecUP preset should own:

```text
OpenUP lifecycle templates
WBS templates
Risk Register templates
Traceability schemas
Governance gates
Definition of Ready
Definition of Done
Gherkin templates
Contract templates
Microcks integration
AGENTS.md templates
SKILL.md templates
index.md conventions
Audit workflows
```

The project repository should own:

```text
business requirements
domain architecture
source code
tests
project-specific policies
project-specific skills
```

---

# 37. OpenUP Phase-to-Spec-Kit Mapping

| OpenUP | SpecUP activities | Major artifacts |
|---|---|---|
| Inception | Constitution, Specify, Clarify | Vision, scope, initial risks, initial WBS |
| Elaboration | Plan, Research, Architecture, Contracts | Architecture, data model, contract, risk mitigation |
| Construction | Tasks, Implement, Test, Trace | Code, tests, Gherkin, Microcks, evidence |
| Transition | Release validation, Audit, Acceptance | Release readiness, operations, acceptance |

---

# 38. OpenUP + AI Iteration Loop

For every iteration:

```text
Iteration Goal
      ↓
Review Risks
      ↓
Select WBS Work
      ↓
Generate Tasks
      ↓
Validate Definition of Ready
      ↓
AI Implementation
      ↓
Automated Verification
      ↓
Traceability
      ↓
Evidence
      ↓
Iteration Review
      ↓
Risk Reassessment
      ↓
Iteration Gate
```

This ensures that iterative development remains genuinely iterative rather than becoming a single large AI code-generation exercise.

---

# 39. Risk-Driven Planning

Risk should affect scheduling.

For example:

```text
RISK-001 Critical
RISK-002 High
RISK-003 Medium
```

The WBS should prioritize:

```text
high-risk architectural validation
        ↓
high-risk prototype
        ↓
risk-reducing implementation
        ↓
lower-risk feature implementation
```

This aligns the AI workflow with the risk-driven nature of OpenUP.

---

# 40. Architecture Must Be Established Early

A major design rule should be:

> **Major technical uncertainty must be resolved before high-volume implementation.**

Therefore Elaboration should contain:

```text
architecture
architecture decisions
interfaces
data model
security model
deployment assumptions
performance assumptions
integration strategy
```

and corresponding risks.

Only then should Construction scale.

---

# 41. Contract-First Development

For service-based systems, a useful pattern is:

```text
Requirement
      ↓
Acceptance Criteria
      ↓
Gherkin
      ↓
API Contract
      ↓
Mock / Stub
      ↓
Consumer Development
      ↓
Provider Development
      ↓
Microcks Conformance
```

This makes parallel development practical.

The consumer can implement against the contract before the final provider is complete.

---

# 42. Pull Requests as Lifecycle Reviews

A SpecUP pull request should review more than a code diff.

A useful PR review surface is:

```text
Requirements diff
+
WBS diff
+
Risk diff
+
Architecture diff
+
Code diff
+
Test diff
+
Contract diff
+
Traceability diff
```

For example:

```text
Requirement changed:
REQ-AUTH-014

Affected WBS:
1.2.3.4.1

Affected risks:
RISK-007

Affected API:
POST /v1/authenticate

Affected tests:
TC-AUTH-031
TC-AUTH-032

Affected implementation:
certificate_validator.ts
authentication_service.ts
```

This makes change impact visible before merge.

---

# 43. Git as Historical Governance

Git becomes more than the code version-control system.

It becomes the history of engineering decisions.

A change can encompass:

```text
Requirement change
WBS change
Risk change
Architecture change
Code change
Test change
Traceability change
```

A useful commit convention is:

```text
feat(auth):

REQ-AUTH-014
WBS-1.2.3.4.1.2
TASK-042
```

This creates an additional audit layer.

---

# 44. Code Changes Must Carry Traceability

A recommended policy:

```text
Every code-changing task
    ↓
must have:
    requirement ID
    WBS ID
    task ID
    test IDs
    traceability update
```

This should be validated in CI.

---

# 45. The Repository as an Engineering Knowledge Graph

At full maturity, the repository is no longer just a source-code repository.

It becomes an engineering knowledge graph:

```text
                 ┌──────────────┐
                 │   Business   │
                 │   Objective  │
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
                 │ Requirement  │
                 └──────┬───────┘
                        │
              ┌─────────▼──────────┐
              │ Acceptance Criteria│
              └─────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │      Gherkin        │
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │       WBS L1-L7     │
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │       Task          │
             └──────────┬──────────┘
                        │
          ┌─────────────▼─────────────┐
          │       Implementation      │
          └─────────────┬─────────────┘
                        │
              ┌─────────▼─────────┐
              │       Tests       │
              └─────────┬─────────┘
                        │
                ┌───────▼────────┐
                │    Microcks    │
                └───────┬────────┘
                        │
                 ┌──────▼───────┐
                 │   Evidence   │
                 └──────┬───────┘
                        │
                ┌───────▼────────┐
                │ Traceability   │
                └────────────────┘
```

Every important node can be traversed forward and backward.

---

# 46. Markdown vs YAML / JSON

SpecUP should deliberately use two layers.

## Human-readable layer

```text
*.md
```

Best for:

- requirements
- design rationale
- architecture explanations
- decision records
- reviews
- reports
- plans

## Machine-readable layer

```text
*.yaml
*.json
```

Best for:

- IDs
- relations
- states
- dependencies
- WBS
- risks
- traceability
- schemas
- validation

Therefore:

```text
Markdown = human interface
YAML/JSON = machine interface
Git = historical database
Filesystem = current state
```

---

# 47. Generated Views

Avoid duplicate manual maintenance.

Canonical data:

```text
wbs.yaml
risk-register.yaml
traceability.yaml
```

Generated views:

```text
wbs.md
risk-register.md
traceability.md
coverage.md
```

This reduces synchronization errors.

---

# 48. Artifact References Should Use Stable IDs

Stable identifiers should be used consistently. Maintain a glossary of these.

Examples:

```text
BUS-OBJ-0017
NON-FR-0017
REQ-AUTH-0014
USR-STR-0014
FEAT-0014
FLOW-AUTH-0014-0003
AC-AUTH-0014-0003
WBS-1.2.3.4.1.2
TASK-0042
RISK-0007
TRACE-0007
ADR-0019
SECURE-0019
TC-AUTH-0031
UNIT-AUTH-0031
INTG-AUTH-0031
CONTRACT-AUTH-0001
MICROCKS-TEST-0091
```

The IDs become edges in the knowledge graph.

---

# 49. Suggested Artifact Metadata

A governed artifact could use:

```yaml
id: REQ-AUTH-014
type: requirement
title: Certificate-based authentication

status: approved

owner: product-owner

priority: high

phase: elaboration
iteration: E2

source: specs/001-auth/spec.md

relations:
  parent:
    - BO-017

  acceptance:
    - AC-AUTH-014-03

  wbs:
    - WBS-1.2.3.4.1

  risks:
    - RISK-007

  contracts:
    - CONTRACT-AUTH-01
```

This allows the graph to be reconstructed automatically.

---

# 50. Auditability Model

A mature SpecUP implementation should be able to answer:

### What?

```text
What requirement is this code implementing?
```

### Why?

```text
What business objective drove the requirement?
```

### Who?

```text
Who owns the requirement, risk and WBS?
```

### When?

```text
Which OpenUP phase and iteration?
```

### How?

```text
Which design and engineering tasks?
```

### Verified how?

```text
Which unit, integration, acceptance and contract tests?
```

### Released how?

```text
Which release gate and evidence?
```

This is complete engineering transparency.

---

# 51. AI Agent Execution Policy

The agent should never "discover" governance through hallucination.

For any task:

```text
TASK-042
```

the agent must resolve:

```text
TASK-042
   ↓
WBS parent
   ↓
Iteration
   ↓
Phase
   ↓
Requirements
   ↓
Risks
   ↓
Acceptance Criteria
   ↓
Architecture
   ↓
Contracts
   ↓
Tests
```

If a required relationship cannot be resolved:

```text
STOP
```

rather than:

```text
INFER
```

This is an important AI safety and correctness mechanism.

---

# 52. Change Impact Analysis

Because relationships are explicit, change analysis becomes computable.

Suppose:

```text
REQ-AUTH-014
```

changes.

The system can calculate:

```text
Affected User Stories
        ↓
Affected WBS nodes
        ↓
Affected Tasks
        ↓
Affected Risks
        ↓
Affected Architecture Decisions
        ↓
Affected APIs
        ↓
Affected Gherkin scenarios
        ↓
Affected Tests
        ↓
Affected Source Files
```

This enables an agent to present a concrete change-impact report before implementation.

---

# 53. Traceability Coverage Metrics

SpecUP should compute coverage.

Examples:

```text
Requirement-to-WBS coverage
Requirement-to-Test coverage
Requirement-to-Gherkin coverage
WBS-to-Task coverage
Task-to-Code coverage
Code-to-Test coverage
API-to-Microcks coverage
Risk-to-Mitigation coverage
Risk-to-Evidence coverage
```

Example:

```text
Requirement coverage       100%
WBS coverage               100%
Risk mitigation coverage   100%
Gherkin coverage            97%
Contract coverage          100%
Backward traceability       95%
```

These become governance metrics.

---

# 54. Orphan Detection

The audit engine should detect:

```text
orphan requirements
orphan WBS nodes
orphan tasks
orphan risks
orphan Gherkin scenarios
orphan tests
orphan APIs
orphan contracts
orphan source files
broken references
```

Examples:

```text
REQ-AUTH-018
  → no WBS mapping
```

or:

```text
WBS-1.2.3.6.4.2
  → no requirement
```

or:

```text
src/auth/session_manager.ts
  → no traceability entry
```

The gate should fail accordingly.

---

# 55. Quality Gate Philosophy

Every quality gate should be:

```text
machine-checkable
evidence-producing
repeatable
version-controlled
```

Avoid:

```text
"Architecture reviewed"
```

Prefer:

```yaml
architecture_baselined: true
security_review: passed
critical_risks_mitigated: true
contract_validation: passed
traceability_coverage: 100
```

This makes governance objective.

---

# 56. Progressive Context Architecture

The filesystem layout also provides a context-optimization strategy.

The agent does not need:

```text
entire repository
```

for every task.

Instead:

```text
Root AGENTS.md
      ↓
Nearest AGENTS.md
      ↓
Nearest index.md
      ↓
Task metadata
      ↓
Direct relations
      ↓
Required artifacts only
```

This reduces context consumption and makes the agent's reasoning more deterministic.

---

# 57. Minimal Context for an L7 Task

A level-seven task should ideally be executable with:

```text
global governance summary
+
nearest AGENTS.md
+
feature index.md
+
task metadata
+
linked requirement
+
linked acceptance criteria
+
linked risk
+
relevant architecture decision
+
relevant contract
+
relevant SKILL.md
```

Not:

```text
entire repository
```

This is a key scalability property.

---

# 58. OpenUP Roles + AI Agents

An enterprise implementation can map OpenUP roles to AI agents.

Possible mapping:

```text
Stakeholder / Product Owner
      ↓
Requirements Agent

Analyst
      ↓
Specification Agent

Architect
      ↓
Architecture Agent

Developer
      ↓
Implementation Agent

Tester
      ↓
Verification Agent

Project Manager
      ↓
Planning / WBS Agent

Configuration / Quality Role
      ↓
Audit / Traceability Agent
```

The AI does not replace accountability.

Instead:

```text
Human role owns decisions.
AI agent performs bounded work.
Filesystem stores decisions/evidence.
```

---

# 59. Human Approval Boundaries

Not every activity should be autonomous.

Recommended human gates:

```text
Business scope approval
Architecture baseline approval
High-risk acceptance
Requirement baseline
Release approval
Security exceptions
Breaking API changes
```

AI can propose:

```text
requirements
risks
architecture options
WBS
tests
implementation
```

but should not silently authorize governance decisions.

---

# 60. Example Gate Matrix

| Gate | Required evidence | Human approval |
|---|---|---|
| Inception | scope, vision, initial risks, WBS | Product / project owner |
| Elaboration | architecture, critical risks, contracts | Architect |
| Iteration Ready | tasks, dependencies, acceptance criteria | Iteration owner |
| Iteration Complete | tests, Gherkin, traceability | Team / reviewer |
| Release Ready | final audit, security, deployment, acceptance | Release owner |

---

# 61. Continuous Compliance

The governance engine should not run only at release time.

Run audit checks:

```text
on commit
on pull request
on task completion
on contract change
on requirement change
on WBS change
on iteration boundary
on release
```

This creates continuous compliance.

---

# 62. CI/CD Integration

A typical pipeline can become:

```text
lint
  ↓
schema validation
  ↓
AGENTS / index validation
  ↓
WBS validation
  ↓
risk validation
  ↓
traceability validation
  ↓
unit tests
  ↓
integration tests
  ↓
Gherkin
  ↓
API contract validation
  ↓
Microcks
  ↓
security scans
  ↓
audit
  ↓
quality gate
```

A failed governance check should be capable of failing the pipeline.

---

# 63. Example CI Gate Rules

```text
FAIL if:
    requirement coverage < 100%

FAIL if:
    high risk without mitigation

FAIL if:
    L7 WBS task has no requirement

FAIL if:
    code change has no traceability

FAIL if:
    Gherkin scenario references nonexistent requirement

FAIL if:
    contract changed without contract verification

FAIL if:
    Microcks conformance fails

FAIL if:
    release gate evidence is incomplete
```

---

# 64. SpecUP Maturity Levels

A practical rollout could use:

## Level 1 — Spec Driven

```text
Spec Kit
+
AGENTS.md
```

## Level 2 — Governed

```text
+
OpenUP lifecycle
+
WBS
+
Risk
```

## Level 3 — Traceable

```text
+
Bi-directional traceability
+
Gherkin
```

## Level 4 — Contract Verified

```text
+
OpenAPI / AsyncAPI
+
Microcks
```

## Level 5 — Continuous Governance

```text
+
automated gates
+
CI enforcement
+
change impact analysis
+
audit evidence
```

---

# 65. Avoiding Process Bloat

There is an important danger:

> **It is possible to create such a large governance process that AI development becomes slower than traditional development.**

OpenUP emphasizes that process should remain useful and not become an end in itself.

Therefore:

```text
Governance must be machine-checkable.
Documentation must have a purpose.
Every artifact must enable:
    a decision,
    execution,
    verification,
    or audit.
```

Do not create seven levels of narrative.

Create seven levels of scope decomposition.

Do not manually maintain traceability documents.

Generate traceability views from structured relationships.

Do not force humans to edit duplicated artifacts.

Maintain canonical data and generate views.

---

# 66. Recommended Canonical Data Model

The minimum structured graph should include:

```text
BusinessObjective
Requirement
UserStory
AcceptanceCriterion
WBSNode
Task
Risk
ArchitectureDecision
Contract
Scenario
TestCase
SourceArtifact
Evidence
Iteration
Phase
Gate
```

Relations:

```text
contains
refines
implements
verifies
mitigates
depends-on
tested-by
validated-by
modifies
belongs-to
approved-by
supersedes
```

This is effectively a lightweight project knowledge graph backed by the filesystem.

---

# 67. Example Traceability Graph Query

A tool should be able to answer:

```text
Show all code affected by REQ-AUTH-014.
```

Conceptually:

```text
REQ-AUTH-014
    ↓ implemented-by
WBS-1.2.3.4.1.2
    ↓ decomposes-to
TASK-042
    ↓ modifies
certificate_validator.ts
    ↓ tested-by
certificate_validator.test.ts
```

Another query:

```text
Show all requirements potentially affected by certificate_validator.ts.
```

Reverse traversal:

```text
certificate_validator.ts
    ↓ modifies
TASK-042
    ↓ implements
WBS-1.2.3.4.1.2
    ↓ satisfies
REQ-AUTH-014
```

---

# 68. Proposed Final SpecUP Architecture

```text
              OPENUP × SPEC KIT
           AI-NATIVE GOVERNED SDLC

OpenUP
│
├── Phases
├── Iterations
├── Milestones
├── Roles
├── Risk management
└── WBS
        │
        ▼
Spec Kit
│
├── Constitution
├── Specify
├── Clarify
├── Plan
├── Tasks
├── Implement
└── Analyze / Converge
        │
        ▼
Governance extensions
│
├── 7-level WBS
├── Risk Register
├── Bi-directional Traceability
├── Definition of Ready
├── Definition of Done
└── Quality Gates
        │
        ▼
Executable specification
│
├── Gherkin
├── OpenAPI
├── AsyncAPI
└── Microcks
        │
        ▼
Agent operating system
│
├── AGENTS.md
├── SKILL.md
├── index.md
└── filesystem-first rules
        │
        ▼
Evidence
│
├── Code
├── Tests
├── Contract results
├── Risk evidence
├── Traceability
└── Git history
```

---

# 69. Complete End-to-End Development Flow

The complete system becomes:

```text
                         HUMAN INTENT
                              │
                              ▼
                     /speckit.openup-init
                              │
                              ▼
                     OPENUP INCEPTION
                              │
                              ▼
                    /speckit.constitution
                              │
                              ▼
                       /speckit.specify
                              │
                              ▼
                          REQUIREMENTS
                              │
                              ▼
                          RISK REGISTER
                              │
                              ▼
                            WBS L1-L7
                              │
                              ▼
                     INCEPTION GATE
                              │
                              ▼
                        ELABORATION
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
               ARCHITECTURE         CONTRACTS
                    │                   │
                    └─────────┬─────────┘
                              ▼
                        TRACEABILITY
                              │
                              ▼
                    ARCHITECTURE GATE
                              │
                              ▼
                       CONSTRUCTION
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                   PLAN               TASKS
                    │                   │
                    └─────────┬─────────┘
                              ▼
                         IMPLEMENT
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                  UNIT      GHERKIN   MICROCKS
                  TEST       TEST     CONTRACT
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                       TRACEABILITY
                              │
                              ▼
                      ITERATION GATE
                              │
                              ▼
                         TRANSITION
                              │
                              ▼
                     RELEASE EVIDENCE
                              │
                              ▼
                     RELEASE MILESTONE
```

---

# 70. What the Resulting System Provides

The combined architecture creates five major control planes.

## 70.1 Intent Control

```text
Constitution
Specification
Requirements
```

Controls:

> **What should be built?**

## 70.2 Lifecycle Control

```text
OpenUP Phases
Iterations
Milestones
Gates
```

Controls:

> **When and under what governance conditions may it be built?**

## 70.3 Work Control

```text
7-level WBS
Tasks
Dependencies
Owners
```

Controls:

> **How is the work decomposed and assigned?**

## 70.4 Verification Control

```text
Gherkin
Unit Tests
Integration Tests
OpenAPI
AsyncAPI
Microcks
```

Controls:

> **Does the implementation satisfy expected behavior and contracts?**

## 70.5 Evidence Control

```text
Traceability
Git history
Audit reports
Risk register
Approval states
```

Controls:

> **Can we prove what happened, why it happened, and whether it was verified?**

---

# 71. Architectural Thesis

The deeper architecture can be summarized as:

```text
OpenUP
    = Lifecycle Governance

Spec Kit
    = AI-Native Development Transformation

7-Level WBS
    = Controlled Work Decomposition

Risk Register
    = Uncertainty Management

Gherkin
    = Executable Behavioral Specification

OpenAPI / AsyncAPI
    = Executable Interaction Contracts

Microcks
    = Contract Mocking and Conformance

AGENTS.md
    = Agent Operating Governance

SKILL.md
    = Agent Procedural Capability

index.md
    = Local Context Navigation

Traceability
    = Engineering Knowledge Graph

Git
    = Historical Evidence Store

Filesystem
    = Current Authoritative Project State
```

Together:

```text
                    SPECUP

        ┌───────────────────────────┐
        │     OpenUP Governance     │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │     Spec Kit AI Flow      │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │   Structured Artifacts    │
        │ WBS • Risk • Traceability │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │ Executable Specifications │
        │ Gherkin • Contracts       │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │     AI Execution          │
        │ AGENTS • SKILL • Tasks    │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │ Verification + Evidence   │
        │ Tests • Microcks • Git    │
        └───────────────────────────┘
```

---

# 72. Final Design Principle

The central idea of SpecUP is:

> **The AI should not be trusted because the prompt was good. The AI should be trusted because its work is constrained by governed artifacts and every meaningful action produces independently inspectable evidence.**

In this model:

```text
LLM
  ↓
interprets governed artifacts
  ↓
executes bounded tasks
  ↓
produces implementation
  ↓
produces tests
  ↓
produces verification evidence
  ↓
updates traceability
  ↓
passes machine-checkable gates
```

Therefore the repository itself becomes the control plane.

The final system can be described as:

> **An AI-native, filesystem-first, OpenUP-governed software engineering framework built as a Spec Kit preset, where requirements, seven-level WBS, risks, acceptance behavior, executable contracts, implementation tasks, code, tests, and evidence are connected through a bi-directional traceability graph.**

This is substantially more rigorous than using Spec Kit as a prompt/template framework alone. It turns the repository into a **living, auditable engineering model** in which AI agents operate within explicit lifecycle, scope, risk, verification, and evidence boundaries.

---

# 73. Reference Notes

The architecture is based on the following established ideas and extension mechanisms:

1. GitHub Spec Kit supports specification-driven development, structured artifacts, custom templates/scripts/workflows, and extension/preset mechanisms.
2. OpenUP provides an iterative, incremental, risk-focused lifecycle with Inception, Elaboration, Construction, and Transition phases and milestone-oriented governance.
3. `AGENTS.md` provides a conventional mechanism for repository-scoped coding-agent instructions.
4. Microcks provides API mocking and contract/conformance testing around supported API specifications including OpenAPI and AsyncAPI.
5. Gherkin provides a human-readable executable specification format for behavior-driven acceptance tests.

These should be re-checked against the current versions of the respective projects when implementing the actual preset, because command names, extension interfaces, configuration formats, and integrations can evolve.

