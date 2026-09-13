# SpecUP — the guide

**Audience:** engineers and leads deciding whether to adopt SpecUP, and then adopting it.

1. [What SpecUP is](#what-specup-is)
2. [The problem it addresses](#the-problem-it-addresses)
3. [How it works](#how-it-works)
4. [The data model](#the-data-model)
5. [The lifecycle](#the-lifecycle)
6. [The commands](#the-commands)
7. [Configuration](#configuration)
8. [Adoption](#adoption) → [new repo](new-project.md) · [existing repo](existing-project.md)
9. [When *not* to use SpecUP](#when-not-to-use-specup)

> Already installed and looking for the operating manual — what a check id means, what to
> type, what a config key does? That is **[Using SpecUP](using-specup.md)**. This page is the
> *why*; that one is the *how*.

---

## What SpecUP is

SpecUP adds the **Eclipse OpenUP lifecycle** to [GitHub Spec Kit](https://github.com/github/spec-kit) — phases,
iterations, a seven-level work breakdown structure, a risk register with arithmetic behind
it, bi-directional traceability, and milestone gates that are evaluated by Python predicates
over your filesystem.

The word doing the work in that sentence is **evaluated**. A failing gate does not produce a
warning an agent can talk its way past. It produces a non-zero exit code that halts the
workflow run.

It ships as three Spec Kit components plus a bundle that installs them together:

| Layer | What it is | What it can do |
|---|---|---|
| `openup` | extension | Adds `/speckit.openup.*` commands, JSON Schemas, and the validators |
| `openup-governance` | preset | Composes governance into Spec Kit's *own* constitution, spec, plan, tasks, `/tasks` and `/implement` |
| `openup-{phase}` | 4 workflows | **Enforcement.** Shell steps run the validators; the engine branches on the real exit code |
| `specup` | bundle | Installs all six as one pinned unit |

### The one architectural fact that explains the rest

Spec Kit has four composition mechanisms, and **only one of them can stop anything**:

| Mechanism | Real enforcement? | Why |
|---|---|---|
| Preset | No | Prompt-level. It changes what the model is told, not what happens. |
| Extension | No | Its hooks render as instructions into command markdown. A model can decline them. |
| **Workflow** | **Yes** | A non-zero `shell` step halts the run; `gate` with `on_reject: abort` terminates it. |
| Bundle | No | Distribution only. |

This is why SpecUP is shaped the way it is. Governance that lives only in templates is
governance the model may simply not follow, and you would never know. So every hard check
lives in a workflow shell step, and the preset and extension exist to make the checks
*reachable and legible* — not to be the checks.

---

## The problem it addresses

An AI agent produces plausible, well-structured output whose only provenance is a chat log.
Most answers to this are more prose: templates and instructions the model is *asked* to
follow, which it may follow, and which nothing verifies.

SpecUP's position is that governance is real only when it is **machine-checkable and
consequential**:

| Escape route | What closes it |
|---|---|
| State lives in the conversation | Every governed artifact is a version-controlled file |
| Action with no governing intent | A task must resolve to a WBS node, requirement and criteria — or the agent stops |
| Agent invents the missing link | *Resolve, or stop — never infer*, plus validators that reject unresolvable ids |
| Agent declares itself done | Definition of Done is computed from the graph, not asserted |
| LLM opinion as a gate | Gates are Python predicates over the filesystem; a failing one halts the run |
| Coverage that means nothing | Every traceability edge declares provenance; coverage is reported beside it |

That last row is the one most governance tooling misses. A project can be 100% "traced" while
every edge is an unverified agent claim. SpecUP reports both numbers, always.

### The circularity it had to close

If the agent writing the code also writes the proof that the code was traced, the audited and
the auditor are one process, and the audit proves nothing.

So every traceability edge carries **provenance**:

| Value | Meaning | Trust |
|---|---|---|
| `derived` | Recomputed from the filesystem by a named rule, and the rule is re-run to check | Machine-checkable |
| `asserted` | Claimed by an agent or author | Claim only |
| `approved` | Asserted, then signed off by a named human | Governance-grade |

An `approved` edge is bound to its endpoints by a SHA-256 hash, so editing either endpoint
downgrades the edge rather than silently keeping the sign-off. Every audit prints the
derived/asserted/approved mix next to the coverage figure, so a graph that is overwhelmingly
`asserted` cannot present itself as fully covered.

**And the label itself is checked.** The first version of this model closed the circularity
one level too high: a schema can require `derived_by` to be *present*, but not to be *true*, so
an agent could move its own claim from `asserted` to `derived`, type a plausible rule name, and
improve the exact ratio the audit reports. `TRC-010` re-executes the rule an edge names and
fails the edge when it does not come back. Three of the six declared rules are implemented; an
edge naming one of the other three is reported as `derived_unverified` and is not counted as
evidence at a gate. The rules live in
[`derivers.py`](../../extensions/openup/scripts/python/derivers.py) and regenerate into a
machine-owned store:

```bash
python3 .specify/extensions/openup/scripts/python/derive_edges.py --write
```

---

## How it works

```
┌─ you run a phase workflow ────────────────────────────────────────────┐
│                                                                       │
│  command steps  ─→  the agent does the work (specify, plan, tasks,    │
│                     implement, and the /speckit.openup.* commands)    │
│                                                                       │
│  shell steps    ─→  python3 …/evaluate_gate.py --gate GATE-X --json   │
│                     exit 0 = PASS   1 = FAIL   2 = CANNOT EVALUATE    │
│                                                                       │
│  if steps       ─→  branch on the real exit code                      │
│                                                                       │
│  gate step      ─→  a human decides: reject (abort) or override       │
│                     an override writes the failing verdict to         │
│                     .specify/evidence/overrides/<run_id>.json         │
└───────────────────────────────────────────────────────────────────────┘
```

Each phase workflow ends with the same block:

```yaml
- id: evaluate-gate
  type: shell
  run: "python3 .specify/extensions/openup/scripts/python/evaluate_gate.py --gate <GATE> --json --out <evidence>"
  continue_on_error: true          # so the branches below are reachable

- id: halt-if-unevaluable          # exit 2 -> setup fault, halt hard
  type: if
  condition: "{{ steps.evaluate-gate.output.exit_code == 2 }}"

- id: enforce-gate                 # exit 1 -> governance failure, human decides
  type: if
  condition: "{{ steps.evaluate-gate.output.exit_code == 1 }}"
  then:
    - id: gate-failed
      type: gate
      options: [reject, override]
      on_reject: abort
```

`continue_on_error: true` looks like a weakening and is the opposite. A non-zero shell step
halts the whole run *by default* — which enforces, but makes the human branch unreachable and
leaves the operator with no verdict to read. Recording the exit code and branching explicitly
keeps the failure consequential **and** legible.

### Three exit codes, not two

| Code | Meaning |
|---|---|
| `0` | PASS |
| `1` | FAIL — a governance failure. The project does not meet the gate. |
| `2` | ERROR — could not evaluate. Malformed YAML, missing dependency, unreadable graph. |

Collapsing `2` into `1` would tell someone their project failed its milestone when the truth
is a broken file. A `2` halts the run on a separate branch that says so.

### Verified behaviour

Run against spec-kit 1.0.6 with the real engine:

| Graph state | Result |
|---|---|
| Healthy | `Status: completed` — runs to the final step |
| High-exposure risk stripped of its mitigation | `Status: paused` at `[gate-failed]` — final step never reached |
| `wbs.yaml` corrupted so the graph cannot load | `Status: failed`, `exited with code 2` |

---

## The data model

Everything is a version-controlled file under `.specify/`. There is no database and no hidden
state.

```
.specify/
├── lifecycle/        vision.md, stakeholders.md, index.md
├── governance/       approvals and sign-off records
├── architecture/     ADRs and the architecture baseline
├── wbs/wbs.yaml                        the work breakdown structure
├── risks/risk-register.yaml            the risk register
├── traceability/
│   ├── requirements.yaml               requirements and acceptance criteria
│   └── traceability.yaml               the edges
└── evidence/         validator verdicts, test reports, gate records
```

### Identifiers

Zero-padded and regex-enforced. IDs are graph edges, and retrofitting them is the one
genuinely expensive migration — so they are frozen in
[`ID-GRAMMAR.md`](../../extensions/openup/schemas/ID-GRAMMAR.md) and validated by four JSON
Schemas.

| Kind | Form | Example |
|---|---|---|
| Requirement | `REQ-<DOMAIN>-<NNNN>` | `REQ-AUTH-0014` |
| WBS node | `WBS-<dotted path>` | `WBS-1.2.3.4.1.1.2` |
| Risk | `RISK-<NNNN>` | `RISK-0007` |
| Acceptance criterion | `AC-<DOMAIN>-<NNNN>-<NNNN>` | `AC-AUTH-0014-0003` |
| Iteration | `ITER-[IECT]-<NN>` | `ITER-E-02` |
| Gate | `GATE-<SCREAMING_SNAKE>` | `GATE-LIFECYCLE_ARCHITECTURE` |

**Source files have no synthetic id.** The repo-relative path *is* the identity, so
traceability survives a validator rebuild and never drifts from the filesystem.

### Relations

A closed set of fourteen, each stored **once, in active voice**. The inverse is derived at load
time and never written, because two hand-maintained directions are two things that can
disagree — and disagreement is what traceability exists to prevent.

`refines` · `contains` · `implements` · `verifies` ·
`executes` · `tests` · `conforms-to` · `validates` · `mitigates` · `evidences` ·
`depends-on` · `belongs-to` · `approves` · `supersedes`

A relation outside the set is rejected. Each has a declared domain and range, so
`implements` from a Risk to a Contract fails rather than quietly landing in the graph.

```yaml
edges:
  - from: WBS-1.2.3.4.1.1.1
    relation: implements
    to: REQ-AUTH-0014
    provenance: asserted
```

### The seven WBS levels

L1 Program → L2 Phase → L3 Iteration → L4 Capability → L5 Feature → L6 Component → L7
Executable Task. **The number of dotted segments *is* the level**, so an id and its declared
level can never disagree without a validator noticing.

An L7 node is the unit of execution and must carry an owner, an iteration and at least one
requirement:

```yaml
- id: WBS-1.2.3.4.1.1.1
  name: Define certificate contract
  level: 7
  parent: WBS-1.2.3.4.1.1
  phase: ELABORATION
  iteration: ITER-E-02
  status: done
  kind: implementation
  owner: backend-team
  requirements: [REQ-AUTH-0014]
  estimate: { unit: hours, value: 4 }
  evidence: [EVID-0001]
```

**Depth policy.** `semantic` (the default) keeps the level meanings fixed but lets a branch
terminate above L7 when it declares a `terminal_reason`. `strict` requires every leaf to be
L7. Levels 1–3 are pure structure, so a leaf there is always an error — an empty plan, not a
concise one.

### Risks with arithmetic

```yaml
- id: RISK-0007
  title: Certificate validation latency
  probability: 0.6
  impact: 0.9
  exposure: 0.54          # DERIVED: probability x impact, recomputed; a mismatch is an error
  status: mitigating
  owner: security-team
  mitigation:   [WBS-1.2.3.4.1.1.2]   # real WBS nodes, not prose
  verification: [TC-AUTH-0031]
  residual_probability: 0.2
  residual_impact: 0.5
  residual_exposure: 0.1
```

Exposure at or above `high_exposure_threshold` (default `0.40`) must have at least one
mitigation node and one verification reference before the Elaboration gate passes. A risk
marked `mitigated` whose residual exposure did not actually fall is rejected — that is a
no-op wearing the label of work.

### Governance states

```
DRAFT → REVIEW → APPROVED → BASELINED → IMPLEMENTED → VERIFIED → ACCEPTED
```

Forward only, one step at a time, except that any state may drop back to `DRAFT` on amendment.
`BASELINED` and beyond require a named approver.

**Generated does not mean approved.** Anything a command creates enters at `DRAFT`.

### Gherkin, and the contract layer that is not built

Gherkin is part of the model, and the part that is built is genuinely built. `.feature` files
under `gherkin.features_glob` are parsed; each scenario carries its own `@SCEN-<DOMAIN>-nnnn`
identity plus the `@AC-` criteria it executes, and `gherkin-tag-scan` turns those tags into
`executes` edges. Tag inheritance works the way Gherkin defines it — `Feature:` tags reach every
scenario, `Rule:` tags reach the scenarios under that rule. `TRC-012` then enforces `specup.md`
§24 directly: an acceptance criterion no scenario executes fails the graph.

What Gherkin here does **not** do is run. `acceptance_scenarios_passing` reads
`.specify/evidence/acceptance-results.json` and trusts whatever produced it; SpecUP binds
scenarios into the graph, it does not execute them. Wire your own runner to write that file.

The contract layer is a different story: **nothing validates a contract document at all.**
`MICROCKS-TEST-*` ids and the `validates` relation are reserved in the grammar so nothing has
to be renamed later, but `contracts.microcks.enabled`, `openapi_glob` and `asyncapi_glob` are
read by no code, and `critical_contracts_defined` only asserts that a registered `CONTRACT-*`
artifact's `source` file exists — it never opens it. If you need API conformance today, that is
a gap to fill yourself, not a feature to configure.

---

## The lifecycle

Four OpenUP phases, each ending at a milestone gate.

| Phase | Milestone | The question it asks |
|---|---|---|
| Inception | `GATE-LIFECYCLE_OBJECTIVES` | Is the scope, ownership and initial risk picture real? |
| Elaboration | `GATE-LIFECYCLE_ARCHITECTURE` | Is the architecture baselined and are the high risks handled? |
| Construction | `GATE-INITIAL_OPERATIONAL_CAPABILITY` | Is it built, covered, and free of orphans? |
| Transition | `GATE-PRODUCT_RELEASE` | Can it be released and operated? |

Twenty-two condition declarations over twenty-one implementations, all defined in
`openup-config.yml` and implemented in `evaluate_gate.py`.

Two rules the implementation holds to:

- **Absence of evidence is not evidence.** A missing test report or review record *fails* its
  condition. A gate that passed because a file was never written would be worse than no gate.
- **Conditions fail closed.** A condition declared in config with no implementation, or one
  that raises, fails. It is never skipped.

Construction is iterative: the workflow fans out over ready work, selected risk-first by
`select_work.py`, which applies the Definition of Ready and returns both the ready set and
each blocked task with its reason.

---

## The commands

Nine agent-facing commands, all three-segment (Spec Kit requires extension commands to match
`^speckit\.[a-z0-9-]+\.[a-z0-9-]+$`):

| Command | Purpose |
|---|---|
| `/speckit.openup.init` | Scaffold the governance tree |
| `/speckit.openup.phase` | Set or evaluate the current phase |
| `/speckit.openup.iteration` | Create and manage an iteration |
| `/speckit.openup.wbs` | Create and update the WBS |
| `/speckit.openup.risk` | Create and update the risk register |
| `/speckit.openup.trace` | Build and validate traceability |
| `/speckit.openup.behavior` | Generate Gherkin bound by tag to acceptance criteria |
| `/speckit.openup.gate` | Evaluate a named gate |
| `/speckit.openup.audit` | The aggregate compliance report |

Every one is backed by a validator you can run yourself. Nothing is agent-only:

| Script | Checks | Covers |
|---|---|---|
| `validate_wbs.py` | 12 | level/id agreement, parentage, single root, depth policy, reference resolution, dependency cycles |
| `validate_risk.py` | 8 | exposure arithmetic, residual reduction, mitigation and verification for high risks |
| `validate_trace.py` | 13 | endpoint resolution, relation legality, duplicates, cycles, coverage, orphans, provenance floor, derivation reproducibility, scenario coverage |
| `derive_edges.py` | 4 | what the derivation rules recover; `--write` regenerates the derived store |
| `select_work.py` | 3 | Definition of Ready, risk-first ordering |
| `evaluate_gate.py` | 21 conditions | every condition name declared in config |
| `audit.py` | — | the aggregate report |

They live at `.specify/extensions/openup/scripts/python/` and take `--json` and `--out`.
Because extension commands get no `{SCRIPT}` substitution, **the path an agent runs and the
path a workflow runs are the same string** — there is no second thing to keep in sync.

---

## Configuration

`.specify/extensions/openup/openup-config.yml`. Every threshold there is referenced by a
validator; nothing in it is decorative. Machine-local overrides go in
`openup-config.local.yml`, which is gitignored.

The settings you are most likely to change on adoption:

| Setting | Default | Why you would change it |
|---|---|---|
| `wbs.depth_policy` | `semantic` | `strict` forces every leaf to L7 |
| `risk.high_exposure_threshold` | `0.40` | What counts as a risk needing mitigation |
| `traceability.perimeter.include` | `src/**`, `services/**`, `apps/**` | **Set this first in an existing repo** |
| `traceability.coverage_thresholds.backward` | `0.95` | Share of in-perimeter files that must trace to intent |
| `traceability.stores` | `.specify/…` + `specs/*/…` | Where edges live; all stores merge into one graph |
| `traceability.baseline_min_provenance` | `approved` | Provenance floor for edges touching baselined artifacts |

The perimeter is the important one. Flagging *every* untraced source file as an orphan would
require an edge for every util and config file. The perimeter makes orphan detection
tractable, and getting it wrong is the most common reason a first audit is unusable.

> **Lower a threshold only as a decision, never to make a run go green.** The preset instructs
> agents to refuse that, and it is the one habit that turns this from governance into
> decoration.

---

## Adoption

- **[New project](new-project.md)** — greenfield, governed from the first commit.
- **[Existing project](existing-project.md)** — brownfield, where the code already exists and
  the intent behind it has to be recovered.
- **[Using SpecUP](using-specup.md)** — the operating manual, for once either of those is done.

They are genuinely different problems. In a new repo the graph grows with the code. In an
existing one you are reconstructing a graph for work already done, and the honest starting
position is that most of it is `asserted`.

---

## When *not* to use SpecUP

It is worth being direct about this, because adopting it where it does not fit is the fastest
way to make everyone hate governance.

**Do not use it for:**

- Prototypes, spikes, and anything you intend to throw away. The ceremony outweighs the work.
- Small teams shipping low-consequence software where a code review is already sufficient.
- Projects where nobody will own the risk register. An unmaintained register is worse than
  none: it looks like risk management and is a stale snapshot.

**It earns its cost when:**

- The work is audited, regulated, or safety-relevant and you must *demonstrate* traceability.
- AI agents write a meaningful share of the code and you need provenance stronger than a chat
  log.
- The project is long-lived enough that "why does this exist?" is a question someone will
  actually ask about code nobody remembers writing.

**The unmeasured risk.** Governance overhead per unit of delivered code is not measured
anywhere in SpecUP, and it is the thing most likely to sink the approach. Track it from your
first Construction iteration. If governed work is slower than ungoverned work without a
corresponding drop in defects or audit effort, cut scope — reduce the perimeter, raise the
depth policy, drop conditions — rather than continuing out of commitment.
