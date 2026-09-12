# SpecUP — Implementation Plan

## Context

`specup.md` proposes SpecUP: an OpenUP-governed, filesystem-first extension of GitHub Spec Kit with a
7-level WBS, risk register, bi-directional traceability, Gherkin, Microcks, and machine-checkable
quality gates. It is a 3,382-line design document with **zero implementation** — 156 of its 170 code
fences are ASCII diagrams, and the four JSON schemas plus the `./tools/validate-wbs` binary it treats
as load-bearing are named but never written.

This plan turns that document into a working Spec Kit bundle. It is grounded in the **actual**
`github/spec-kit` repo as of v1.0.6 (135k stars, last pushed 2026-09-12), not in the document's
assumptions about it.

### What was verified about Spec Kit (and what it changes)

| Mechanism | Provides | Composition | Real enforcement? |
|---|---|---|---|
| **Preset** | overrides of existing commands/templates/scripts | `replace`/`prepend`/`append`/`wrap`, priority-stacked | No — prompt-level only |
| **Extension** | **new** namespaced commands, templates, scripts, config, hooks | `replace` only | No — hooks are LLM-interpreted |
| **Workflow** | step sequence: `command`/`shell`/`gate`/`if`/`switch`/`while`/`fan-out` | expression engine, state, resume, JSONL run log | **Yes** — `shell` exit code + `if` + `gate on_reject: abort` |
| **Bundle** | composes extensions + presets + workflows, pinned, with provenance | — | distribution only |

Four findings that shape everything below:

1. **Spec Kit already has a governance runtime.** The workflow engine ships `gate`, `shell`, `if`,
   `while`, and `fan-out` steps, a `from_json` expression filter, state persistence with resume, and
   an append-only run log at `.specify/workflows/runs/{run_id}/log.jsonl`. SpecUP does **not** need to
   build a gate engine, an evidence store, or an iteration driver. It needs to supply the *data model*,
   the *validators*, and the *workflow definitions that wire gates to validators*.
2. **Hooks are not enforcement.** `extension.yml` hooks are rendered as instructions into command
   markdown telling the agent to read `.specify/extensions.yml` and emit `EXECUTE_COMMAND:`. A model
   can ignore them. Per the decision taken, hard gates live in workflow `shell` steps.
3. **The document's command names are invalid.** Extension commands must match
   `^speckit\.[a-z0-9-]+\.[a-z0-9-]+$` — three dot-segments. So `/speckit.wbs`, `/speckit.risk`, and
   `/speckit.audit` (§34) cannot exist as extension commands; they must be `/speckit.openup.wbs` etc.
   Only a *preset* may override two-segment core command names.
4. **There is direct prior art.** `isaqb-architecture-governance` in the community catalog encodes a
   whole methodology (iSAQB/arc42) as a preset using `strategy: append` addenda on
   constitution/spec/plan/tasks plus standalone work-product templates. SpecUP should copy that idiom
   for its preset layer — and go beyond it, since that preset ships no validators at all, which is
   exactly the gap SpecUP exists to fill.

### Decisions taken

- **Ship the full bundle, staged** — each layer usable alone, but the target is the whole stack.
- **Enforcement via workflow `shell` steps.** CI enforcement (doc §62–63) is deferred, not built in v1.
- **Semantic 7-level WBS with early termination** — levels keep fixed meanings; a leaf may terminate
  above L7 if it declares `terminal_reason`. This resolves the §18-vs-§65 contradiction in the doc.
- **Microcks deferred** to a later phase (the doc's own Maturity Level 4). v1 does static
  OpenAPI/AsyncAPI schema validation only.
- **Validators in Python.** Spec Kit ships `scripts/python/` alongside bash/PowerShell and extensions
  declare `runtimes: [bash, powershell, python]`; Python gives one cross-platform implementation
  instead of maintaining bash+PowerShell parity, and `jsonschema` does the schema work directly.

---

## Target repository layout

```
specup/
├── specup.md                          # design doc — intent, unchanged
├── bundle.yml                         # composes the three layers below
│
├── extensions/openup/
│   ├── extension.yml
│   ├── commands/                      # speckit.openup.{init,phase,iteration,wbs,
│   │                                  #   risk,trace,behavior,gate,audit}.md
│   ├── schemas/                       # wbs|risk|traceability|artifact .schema.json
│   ├── templates/                     # lifecycle, wbs, risk, trace, index starters
│   ├── scripts/python/                # the validators — see below
│   └── openup-config.yml              # depth_policy, thresholds, perimeter
│
├── presets/openup-governance/
│   ├── preset.yml
│   ├── templates/                     # *-addendum.md, strategy: append
│   └── commands/                      # wrap speckit.tasks + speckit.implement
│
└── workflows/
    ├── openup-inception/workflow.yml
    ├── openup-elaboration/workflow.yml
    ├── openup-construction/workflow.yml
    └── openup-transition/workflow.yml
```

---

## Stage 0 — Freeze the data model

Nothing else can be built on a moving ID scheme, and retrofitting IDs is the one genuinely expensive
migration. `specup.md` contradicts itself here: §17–21 use `REQ-AUTH-014`/`TASK-042`, §48 mandates
4-digit `REQ-AUTH-0014`/`TASK-0042` plus eight prefixes used nowhere else, and WBS IDs appear both
bare (`1.2.3.4.1.2`) and prefixed (`WBS-1.2.3.4.1.2`).

**Deliverable: `extensions/openup/schemas/` + an `ID-GRAMMAR.md` next to it.**

1. **One ID grammar**, regex-enforced in `artifact.schema.json`. Adopt §48's zero-padded 4-digit form
   as canonical (`REQ-AUTH-0014`), WBS always prefixed (`WBS-1.2.3.4.1.2`). Every type prefix in §48
   is either used or deleted — no unused prefixes.
2. **One closed relation vocabulary with declared inverses.** §21, §66, and §67 currently use three
   overlapping sets (`implemented-by`/`implements`, `executed-by`, `decomposes-to`, `satisfies`). Pick
   the active-voice form as canonical, declare the inverse for each, and make the validator reject any
   relation outside the set. This is what makes "bi-directional" mechanical rather than aspirational.
3. **Four JSON Schemas**: `wbs`, `risk`, `traceability`, `artifact` — modelled on the YAML examples at
   `specup.md:887`, `:965`, `:1100`, and `:2331`.
4. **Provenance on every traceability edge** — `provenance: derived | asserted | approved`. This
   addresses the plan's biggest open risk: if the implementing agent authors its own traceability,
   the audited and the auditor are the same process. `derived` edges are recomputed by the validator
   from the filesystem and may be trusted; `asserted` edges are agent claims; `approved` requires a
   human. Gates can then require `approved` for baseline-level edges.
5. **Declare the traceability perimeter** in `openup-config.yml` — doc §54 flags every untraced source
   file as an orphan, which at file granularity means every util and config needs an edge. An explicit
   include/exclude perimeter makes orphan detection tractable.

## Stage 1 — Validators (the actual product)

**Deliverable: `extensions/openup/scripts/python/`.** Every validator is a standalone CLI that emits a
JSON verdict on stdout and sets a non-zero exit code on failure — that dual contract is what lets the
same script serve both the agent and a workflow `shell` step.

```
openup_model.py     # load + index the graph from YAML; the shared core
validate_wbs.py     # §18 invariants, under semantic-7 + terminal_reason
validate_risk.py    # §19: every high-exposure risk has mitigation + verification
validate_trace.py   # forward/backward coverage, orphans, broken refs, cycles
evaluate_gate.py    # named gate predicates → pass/fail with reasons
audit.py            # §33 aggregate report
```

Verdict shape — consumed directly by the workflow engine's `from_json` filter:

```json
{"status": "FAIL", "checks": [{"id": "TRC-001", "status": "FAIL",
  "message": "REQ-AUTH-0018 has no WBS mapping", "evidence": ["..."]}],
 "metrics": {"forward_coverage": 1.0, "backward_coverage": 0.97}}
```

Two things the doc leaves undefined and this stage must settle: **exposure** is `probability × impact`
(stated only by example at `specup.md:985`) and needs a declared `high` threshold in
`openup-config.yml`; and gate predicate names like `all_high_risks_have_mitigation` (`specup.md:1584`)
need actual implementations keyed by name in `evaluate_gate.py`.

Build these test-first against fixture graphs — a known-good graph and a deliberately-broken one per
invariant. The broken fixtures are the acceptance criteria for Stage 3.

## Stage 2 — The `openup` extension

**Deliverable: `extensions/openup/extension.yml` + `commands/`.**

Commands, all three-segment (correcting §34):

| Command | Purpose |
|---|---|
| `speckit.openup.init` | scaffold `.specify/lifecycle/`, `governance/`, `wbs/`, `risks/`, `traceability/` |
| `speckit.openup.phase` | set/evaluate current OpenUP phase |
| `speckit.openup.iteration` | create/manage an iteration |
| `speckit.openup.wbs` | create/update the WBS |
| `speckit.openup.risk` | create/update the risk register |
| `speckit.openup.trace` | build/validate traceability |
| `speckit.openup.behavior` | generate Gherkin bound to acceptance criteria |
| `speckit.openup.gate` | evaluate a named gate |
| `speckit.openup.audit` | the §33 compliance report |

Follow the core command anatomy (`templates/commands/plan.md`): frontmatter with `description` and a
`scripts:` block (`sh`/`ps`/`py`), `$ARGUMENTS` for user input, `{SCRIPT}` substitution, and the script
returning JSON the agent parses. Generated `.md` views (`wbs.md`, `risk-register.md`) are rendered from
canonical YAML per §47 — never hand-maintained.

Register hooks (`after_specify`, `after_plan`, `after_tasks`, `after_implement`) for **ergonomics** —
they prompt the agent to keep the graph current. They are explicitly not the enforcement path.

## Stage 3 — Workflows: where the gates actually bite

**Deliverable: four workflow definitions.** This is the stage that makes SpecUP's central claim true.
Pattern for every OpenUP milestone gate:

```yaml
- id: validate-architecture-gate
  type: shell
  run: "python .specify/extensions/openup/scripts/python/evaluate_gate.py --gate LIFECYCLE_ARCHITECTURE --json"
  timeout: 600

- id: enforce-architecture-gate
  type: if
  condition: "{{ steps.validate-architecture-gate.output.stdout | from_json | map('status') == 'FAIL' }}"
  then:
    - id: gate-failed
      type: gate
      message: "Lifecycle Architecture gate FAILED. Review the verdict before proceeding."
      options: [override, abort]
      on_reject: abort
```

The `shell` step is the machine check; the `if` makes failure consequential; the `gate` is §59's human
approval boundary. An override is a deliberate, logged human act — which is the correct reading of
§59, not a bypass. The engine's JSONL run log then *is* the evidence trail §70.5 asks for, for free.

`openup-construction/workflow.yml` uses `fan-out` over selected WBS nodes to drive the §38 iteration
loop (select work → generate tasks → implement → verify → trace → iteration gate), with `while` on the
validator exit code for the verify-fix cycle.

> Note the documented shell-injection caveat: `run:` fields interpolate `{{ }}` as raw text with no
> escaping. Keep interpolated values out of `run:`, or constrain them with an `enum` at the input.

## Stage 4 — The governance preset

**Deliverable: `presets/openup-governance/`.** Mirrors the `isaqb-architecture-governance` idiom:

- `strategy: append` addenda onto `constitution-template`, `spec-template`, `plan-template`,
  `tasks-template` — carrying OpenUP phase/iteration context, Definition of Ready (§28), and Definition
  of Done (§29).
- `strategy: wrap` on `speckit.tasks` so generated tasks carry the §27 execution-contract shape
  (`[TASK-…][WBS-…][REQ-…][RISK-…][AC-…]` with preconditions, files, evidence, exit criteria), and on
  `speckit.implement` to require the §51 resolve-or-STOP discipline.
- Standalone work-product templates: WBS, risk register, traceability matrix, index.md, Gherkin.

Preset last, not first: it is the ergonomic layer over a validator core that already works. Built first,
it would be indistinguishable from the prompt-only governance presets already in the catalog.

## Stage 5 — Bundle

**Deliverable: `bundle.yml`** composing extension + preset (with `priority`/`strategy`) + the four
workflows, pinned by version, installable with `specify bundle install ./bundle.yml`.

---

## Verification

Every stage is verified against a throwaway Spec Kit project in the scratchpad, not in this repo.

1. **Validators (Stage 1)** — unit tests over fixture graphs. Each invariant has a passing fixture and
   a deliberately-broken one; the broken fixture must produce a non-zero exit and a named failing check.
2. **Composition (Stages 2, 4)** — `specify init` a scratch project, install locally
   (`specify preset add --dev ./presets/openup-governance`, local-path install for the extension), then
   `specify preset resolve <name>` and `specify artifact list --json` to prove the addenda actually land
   in the composed stack and that `speckit.openup.*` commands registered into `.claude/commands/`.
3. **Enforcement (Stage 3) — the decisive test.** Run `specify workflow run openup-elaboration` against
   a project whose WBS is deliberately broken (an L7 task with no requirement, a high risk with no
   mitigation). The run **must abort at the gate**. Then repair the graph and confirm it proceeds. If
   the workflow completes on the broken graph, SpecUP does not work, regardless of how good the
   templates read.
4. **Evidence** — after a gated run, confirm `.specify/workflows/runs/{run_id}/log.jsonl` contains the
   validator verdicts and the gate decision, and that `speckit.openup.audit` reproduces them.
5. **Bundle (Stage 5)** — `specify bundle install ./bundle.yml` into a clean project reaches a working
   state in one command; `specify bundle remove` leaves no orphans.

## Explicitly out of scope for v1

- **Microcks** conformance (deferred — v1 does static OpenAPI/AsyncAPI validation only).
- **CI enforcement** (doc §62–63). The validators are CI-ready by construction — JSON out, exit codes —
  but no pipeline is authored in v1.
- **Publishing to the community catalog.** Local/`--dev` install only until the gate test above passes.
- **Git pre-commit traceability hook** (doc §44).

## Risks to watch

- **Process bloat** — the doc's own §65 warning. §57 implies ~10 artifact fetches per L7 task against
  §33's example of 421 tasks. Track governance overhead per unit of delivered code from Stage 3 onward;
  if the construction workflow is slower than ungoverned work, cut scope rather than ship it.
- **Spec Kit drift** — this targets v1.0.6 of a repo that pushed commits the day this plan was written.
  Pin `requires.speckit_version` and re-verify the manifest schemas before publishing, per `specup.md:3381`.
- **Evidence integrity** — the `provenance` field in Stage 0 is a mitigation, not a solution. If most
  edges end up `asserted`, the audit proves little. Measure the derived/asserted ratio in the audit report.
