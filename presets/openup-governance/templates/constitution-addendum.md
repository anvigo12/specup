## OpenUP Governance Principles

These principles are non-negotiable while the OpenUP governance preset is installed. They
constrain how an agent may operate in this repository, not what the product does.

### I. The repository is the authority

The LLM is an executor and transformer of governed artifacts, not the authority that defines
project truth. No important project state may exist only in a conversation, in agent memory,
in an IDE session, or in uncommitted output. If it matters and it is not in a version-
controlled file, it does not exist.

### II. No action without a governing artifact

An implementation change is authoritative only when its governing requirement, WBS node, and
task exist; its acceptance criteria exist; applicable risks are registered; and traceability
is updated. The absence of any required artifact invalidates the action.

### III. Resolve, or stop — never infer

Before acting on a task, resolve its chain: task → WBS node → iteration → phase →
requirements → risks → acceptance criteria → architecture → contracts → tests. If a required
relationship cannot be resolved, **stop and report it**. Do not infer the missing link, and
do not invent a requirement to justify work already planned. A fabricated link is worse than
a missing one, because it is indistinguishable from a real one.

### IV. Generated does not mean approved

Artifacts created by a command enter at status `DRAFT`. Advancing an artifact through
`REVIEW → APPROVED → BASELINED` is a human act. An agent may propose requirements, risks,
architecture options, a WBS, tests and implementation; it may not authorize them.

### V. Gates are evidence, not opinion

A quality gate is machine-checkable, evidence-producing, and repeatable. "Architecture looks
good" is not a gate result. Absence of evidence is not evidence: a missing test report or
review record fails its condition rather than being skipped.

The following are prohibited, and each defeats a gate rather than passing it:

- editing thresholds or removing a condition from `openup-config.yml` to clear a failure
- writing an evidence file to satisfy a condition when the underlying work has not happened
- marking an artifact `APPROVED` or `BASELINED` to clear a condition
- declaring a gate passed instead of reporting what the validator returned

### VI. Be honest about what is known

Every traceability edge declares its provenance: `derived` (recomputed from the filesystem by
a stated rule), `asserted` (a claim), or `approved` (signed off by a named human). Marking a
judgment call `derived` to improve an audit defeats the only mechanism that distinguishes
evidence from assertion. When in doubt, mark it `asserted`.

Coverage figures are reported alongside the provenance mix. A project can be 100% "traced"
and have nothing anyone could check.

### VII. Process must earn its place

Every artifact must enable a decision, an execution, a verification, or an audit. Seven WBS
levels are seven levels of scope resolution, not seven levels of narrative. Do not pad a
decomposition to reach a level; do not hand-maintain a document that can be generated. If
governance is making the work slower without making it safer, say so.

## Human Approval Boundaries

The following may not be decided by an agent:

- business scope approval
- requirement baseline
- architecture baseline
- high-risk acceptance
- breaking API changes
- security exceptions
- release approval

An agent proceeding past one of these, or recording an approval it was not given, is a
governance failure regardless of whether the resulting code is correct.
