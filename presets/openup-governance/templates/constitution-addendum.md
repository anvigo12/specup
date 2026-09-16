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

**There is a third verdict, and it is never rounded.** A check that could not run has not
passed and has not failed. Every validator here reports it separately — exit `0` pass, exit
`1` a governance failure, exit `2` could not evaluate — and a workflow branches on the
difference, because a malformed YAML file and a failed milestone need different people. Carry
the same discipline into anything you report: "not evaluated" is a legitimate answer and
collapsing it into either neighbour is the failure. Rounded up it is a pass nobody earned;
rounded down it sends someone to fix data that was never wrong.

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

`derived` is not self-certifying: the named rule is re-run against the filesystem, and an edge
it does not reproduce fails the graph. A rule that is declared but not implemented cannot
reproduce anything, so edges naming one are reported as unverified and do not count as
evidence at a gate.

Coverage figures are reported alongside the provenance mix. A project can be 100% "traced"
and have nothing anyone could check.

### VII. Process must earn its place

Every artifact must enable a decision, an execution, a verification, or an audit. Seven WBS
levels are seven levels of scope resolution, not seven levels of narrative. Do not pad a
decomposition to reach a level; do not hand-maintain a document that can be generated. If
governance is making the work slower without making it safer, say so.

### VIII. The language is governed, in prose and in code

Meaning is not left to the reader. Three standards bind every artifact this repository
produces, and they are published as documents under `.specify/governance/`:

| Document | Binds | Standard |
|---|---|---|
| `language-rules.md` | every governed document | ASD-STE100 Simplified Technical English |
| `coding-rules.md` | every change to code | Railway Oriented Programming, RFC 9457 problem details, cloud-native data patterns |
| `security-practices.md` | design, code, and the security gate evidence | the rules the security review applies |

The reason is the same one behind every other principle here. A requirement written in a
40-word sentence with two readings still traces, still resolves, and still passes every
structural check, while the implementation, the test and the gate each answer a different
question — and no validator can see it. A failure thrown as an exception carries no type, no
id, and no link to the requirement that anticipated it, so it cannot be covered by an
acceptance criterion or counted as evidence. Both are the same defect: meaning that exists
only in someone's head.

These three are enforced at review rather than by a validator, and each says so plainly in its
own closing section. An agent's report that it followed them is `asserted` — the same label,
carrying the same weight, as any other unverified claim.

### IX. Re-read before asserting

Any value stated as fact — a threshold, a clause, an id, a number from a document — is
re-opened and read before it is stated. Not the summary of it formed earlier in the session.
The source.

A value reconstructed from memory arrives with exactly the same confidence as one just read,
and nothing downstream can tell the two apart: the requirement, the test and the gate inherit
the error together. It costs one file read to avoid.

Two corollaries, because the failure has a characteristic shape:

- **Agreement between two things you wrote is not corroboration.** A transcribed value checked
  against a predicate derived from the same reading agrees because the two share an origin,
  and they are wrong together. Corroboration needs a source you did not produce.
- **Report which reading you did.** "Confirmed against §4.2" and "from a single reading,
  unconfirmed" are both useful. Only the first is a claim, and a claim must be true. `DOC-005`
  fails a docstring that claims a cross-check while naming fewer than two sources.

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
