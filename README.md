# SpecUP

**OpenUP lifecycle governance for GitHub Spec Kit — with gates that actually stop the run.**

SpecUP turns [`specup.md`](specup.md), a design document, into a working
[Spec Kit](https://github.com/github/spec-kit) bundle: an extension, a preset, and four
phase workflows that enforce an [Eclipse OpenUP](https://www.eclipse.org/epf/)-style
lifecycle with a seven-level WBS, an executable risk register, and bi-directional
traceability.

> **Status:** [0.1.0 released](https://github.com/anvigo12/specup/releases/tag/v0.1.0),
> verified against spec-kit **1.0.6**, and installed end to end from the published catalog
> into a clean project — see [Quick start](#quick-start). Spec Kit's `default` catalog carries
> only components vendored into its wheel, so a self-hosted catalog is the supported route for
> any third-party project, not a workaround.

---

## Documentation

| | |
|---|---|
| [Guide](docs/guide/README.md) | What SpecUP is, the data model, the lifecycle, the commands |
| [Using SpecUP](docs/guide/using-specup.md) | The operating manual — every command, every check id, every config key |
| [New project](docs/guide/new-project.md) | Greenfield adoption |
| [Existing project](docs/guide/existing-project.md) | Brownfield adoption, where intent has to be recovered |
| [Release notes 0.1.0](docs/runbooks/release-notes-0.1.0.md) | What ships, what is enforced, what is not |
| [Publishing runbook](docs/runbooks/publishing-to-spec-kit.md) | Cutting a release and keeping the catalog honest |
| [Taskfile](docs/dev/taskfile.md) | The task runner, and the boundary it must not cross |

---

## The problem this addresses

An AI agent can produce plausible, well-structured output whose only provenance is a chat
log. Most "AI governance" answers this with more prose — templates and instructions the
model is asked to follow, which it may follow, and which nothing checks.

SpecUP's position is that governance is only real if it is **machine-checkable and
consequential**. Concretely:

| Escape route | What closes it |
|---|---|
| State lives in the conversation | Every governed artifact is a version-controlled file |
| Action with no governing intent | A task must resolve to a WBS node, requirement and criteria — or the agent stops |
| Agent invents the missing link | `resolve, or stop — never infer`, plus validators that reject unresolvable ids |
| Agent declares itself done | Definition of Done is computed from the graph, not asserted |
| LLM opinion as a gate | Gates are Python predicates over the filesystem; a failing one **halts the workflow** |
| Coverage that means nothing | Every traceability edge declares provenance; coverage is reported next to it |

The last row is the one most governance tooling misses. A project can be 100% "traced" while
every edge is an unverified agent claim. SpecUP reports both numbers, always.

---

## How it maps onto Spec Kit

Spec Kit has four composition mechanisms. They differ in one way that decides the whole
design — **only one of them can actually stop anything**.

| Mechanism | Provides | Real enforcement? |
|---|---|---|
| **Preset** | Overrides/composes existing commands and templates (`replace`/`prepend`/`append`/`wrap`) | No — prompt-level |
| **Extension** | New namespaced commands, templates, scripts, config, hooks | No — hooks are LLM-interpreted |
| **Workflow** | Step sequence with `shell`, `gate`, `if`, `fan-out`, state and resume | **Yes** — a non-zero `shell` step halts the run |
| **Bundle** | Composes the above into one pinned, installable unit | Distribution only |

So SpecUP is three layers, each doing only what its mechanism can actually do:

```
workflows/                 ← ENFORCEMENT. shell steps run validators; the engine
  openup-{phase}/            branches on the real exit code and halts or pauses.

extensions/openup/         ← CAPABILITY. New /speckit.openup.* commands, the JSON
  schemas/ scripts/          schemas, and the validators everything else calls.
  commands/ templates/

presets/openup-governance/ ← DISCIPLINE. The only layer that can reach Spec Kit's own
  templates/ commands/       constitution, spec, plan, tasks and /implement.

bundles/specup/            ← COHESION. Not a fourth layer — the only place Spec Kit
  bundle.yml install.py      lets "these three, at these versions" be stated at all.
```

That last one is load-bearing rather than convenience packaging. The preset instructs an
agent to run validators the *extension* installs. It declares that dependency, so Spec Kit
warns when the extension is absent — but a warning is the whole of what Spec Kit offers here:
it installs nothing and refuses nothing. Installed alone, the preset still reads as fully
authoritative while every check it names silently does not run.

A useful consequence: **the path an agent runs and the path a workflow runs are the same
string.** Extension commands get no `{SCRIPT}` substitution, so they reference
`.specify/extensions/openup/scripts/python/<validator>.py` literally — exactly what the
workflow `shell` steps invoke. There is no second thing to keep in sync.

---

## Quick start

```bash
# 1. A Spec Kit project
specify init --here --integration claude

# 2. Register SpecUP's catalogs — genuinely one time, per machine.
#    `specify catalog add` cannot write here; it writes per project. These files
#    also keep Spec Kit's own catalogs, which the per-project route silently drops.
mkdir -p ~/.specify
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user
for f in extension preset workflow bundle; do
  curl -sSL -o ~/.specify/$f-catalogs.yml $BASE/$f-catalogs.yml
done

# 3. All three layers, in dependency order, each archive verified against its digest
specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt

# 4. Scaffold the governance tree
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "My Product"

# 5. See where you stand (it will FAIL — an empty plan is not a valid plan)
python3 .specify/extensions/openup/scripts/python/audit.py
```

Step 3 installs the extension, then the preset, then the four workflows. The order is not
cosmetic: the preset's guidance calls validators the extension installs.

**Do not skip the `pip install`.** Without `PyYAML` every validator exits 2; without the two
schema libraries, five of the nine do — `audit.py` among them. A workflow then halts on its
setup-fault branch rather than passing a gate it could not evaluate. That is the designed
behaviour, and a confusing way to discover a missing dependency.

Then drive a phase:

```bash
specify workflow run ./workflows/openup-inception/workflow.yml \
  --input idea="..." --input program="My Product"
```

To install this repository instead of a release — developing SpecUP, needing an unreleased
change, or working offline — use
[`bundles/specup/install.py`](bundles/specup/README.md#install-a-working-tree) in place of
steps 2 and 3.

---

## The data model

`specup.md` describes identifiers three mutually inconsistent ways. Everything here is frozen
in [`ID-GRAMMAR.md`](extensions/openup/schemas/ID-GRAMMAR.md) and enforced by four JSON
Schemas, because IDs are graph edges and retrofitting them is the one genuinely expensive
migration.

**Identifiers** — zero-padded, regex-enforced: `REQ-AUTH-0014`, `WBS-1.2.3.4.1.1.2`,
`RISK-0007`, `AC-AUTH-0014-0003`, `ITER-E-02`. Source files have no synthetic id: the
repo-relative path *is* the identity, so traceability survives a validator rebuild.

**Relations** — a closed set of 14, stored **once in active voice**. The inverse is derived
at load time and never written. Two hand-maintained directions are two things that can
disagree, and disagreement is what traceability exists to prevent.

**Provenance** — on every edge, and the honest part of the model:

| Value | Meaning | Trust |
|---|---|---|
| `derived` | Recomputed from the filesystem by a named rule — and the rule is **re-run to check** | Machine-checkable |
| `asserted` | Claimed by an agent or author | Claim only |
| `approved` | Asserted, then signed off by a named human | Governance-grade |

This exists because the agent writing the code otherwise also writes the proof it was traced
— auditor and audited collapse into one process. An `approved` edge is bound to its endpoints
by hash, so editing either one downgrades it rather than silently keeping the sign-off, and a
`derived` edge is only counted as evidence once the rule it names reproduces it
([below](#derived-has-to-survive-being-re-run)).

**Seven WBS levels** — L1 Program → L7 Executable Task, where the number of dotted segments
*is* the level. `specup.md` §18 demands every leaf be L7, which collides with its own §65
anti-bloat rule; the default `semantic` policy lets a leaf terminate early when it declares a
`terminal_reason`. `strict` mode implements §18 literally.

---

## Validators

Eleven CLIs. Each emits a JSON verdict on stdout and exits `0` pass / `1` fail / `2`
could-not-evaluate. That dual contract is what lets one script serve both an agent and a
workflow step.

| Script | Checks | Covers |
|---|---|---|
| `validate_wbs.py` | 12 | level/id agreement, parentage, single root, depth policy, reference resolution, dependency cycles |
| `validate_risk.py` | 8 | exposure arithmetic, residual reduction, mitigation and verification for high risks, both-ends agreement |
| `validate_trace.py` | 14 | endpoint resolution, relation type legality, duplicates, cycles, forward/backward coverage, orphans, provenance floor, **derivation reproducibility**, **approval binding**, scenario coverage |
| `validate_done.py` | 6 | the Definition of Done, computed from the graph rather than declared |
| `derive_edges.py` | 4 | what the derivation rules recover; `--write` regenerates the machine-owned store |
| `render_views.py` | 2 | the generated Markdown views are present and match their sources; `--write` regenerates them |
| `approve_edge.py` | — | records a human approval, bound by hash to the content approved |
| `impact.py` | — | what a change to one artifact reaches, in both directions (§52) |
| `select_work.py` | 3 | Definition of Ready, risk-first ordering |
| `evaluate_gate.py` | 22 conditions | every condition name declared in config |
| `audit.py` | — | the aggregate §33 report |

**Exit 2 is not exit 1.** A graph that fails to load is a setup fault, not a governance
failure. Collapsing them would tell someone their project failed its milestone when the truth
is a malformed YAML file.

### `derived` has to survive being re-run

`provenance: derived` claims a rule recovered an edge mechanically, and the audit counts it as
machine-checkable on that basis. The schema can only require `derived_by` to be *present* — so
until `TRC-010`, relabelling an assertion `derived` was free and moved the very ratio the audit
reports. An agent grading its own traceability had a one-word bypass.

[`derivers.py`](extensions/openup/scripts/python/derivers.py) implements the rules, and
`TRC-010` re-executes the one an edge names:

| Rule | Produces | |
|---|---|---|
| `gherkin-tag-scan` | `SCEN-*` → `executes` → `AC-*`, from `@` tags in `.feature` files | implemented |
| `test-file-naming-convention` | test artifact → `tests` → the file its `source` is named after | implemented |
| `wbs-iteration-field` | WBS node → `belongs-to` → iteration | implemented |
| `openapi-operation-scan`, `evidence-manifest-scan` | — | **not implemented** |

An edge an implemented rule does not reproduce fails (`TRC-010`). An edge a rule produces that
no store declares fails (`TRC-011`) and is fixed by `derive_edges.py --write`. An edge naming
one of the two unimplemented rules is counted as `derived_unverified` — reported, never
trusted.

### So does `approved`

The same defect sat one level up. `approved_endpoints_hash` was required by the schema and
read by nothing, so `approved` was a string anyone could type — and `traceability_final`
counted it as evidence. On the reference fixture, relabelling the eleven `asserted` edges
`approved` moved the verifiable share from 38% to 81%.

`TRC-013` now recomputes that hash from the endpoints as they stand. An approval binds the
*content* it was given for: edit either endpoint and the edge drops out of
`approved_verified`, which is the count the gate scores. Record one with
`approve_edge.py` — the hash cannot be produced by hand, and shipping the check without the
tool would have recreated the original mistake in a new place.

`traceability_final` scores reproduced derivations plus *verified* approvals, so a graph
cannot buy its way past by renaming its own claims at either level.

---

## Progressive context

§56–57 argue this approach scales because an agent navigates
`directory → AGENTS.md → index.md → the one artifact it needs`, instead of loading the
repository. `init_openup.py` scaffolds that hierarchy — an operating contract at the root,
`.specify/` and `src/`, a context map in every governed directory, and six capability
contracts under `skills/` — and `validate_context.py` checks it is true:

| Check | | |
|---|---|---|
| `CTX-001` | every governed directory has an `index.md` | WARN |
| `CTX-002` | every identifier an `index.md` names resolves in the graph | **FAIL** |
| `CTX-003` | an `AGENTS.md` is reachable at or above every governed directory | WARN |
| `CTX-004` | every skill a WBS node names exists | **FAIL** |

The split is deliberate. A missing map is a gap, and a project adopting SpecUP should not fail
its first audit over absent documentation. A map that *misleads* is a defect: an `index.md`
naming a deleted requirement sends an agent looking for something that is not there, and an
agent willing to infer will fill the hole itself — the exact failure the rest of the model
exists to prevent.

`AGENTS.md` and `SKILL.md` are kept apart on purpose (§7 vs §8): **what rules must I obey**
versus **how do I perform this activity**. Merged, you get a document followed for neither.
Two of §8's eight skills — `contracts` and `microcks` — are deliberately not shipped: nothing
here parses a contract document, and a capability contract for a capability that does not
exist teaches an agent to claim it.

---

## Generated documents

Nothing that can be computed is written by hand — including the documents. `render_views.py`
regenerates all six from their canonical source, and without `--write` it reports any that are
missing or stale (`VIEW-001`), so a workflow fails on a drifted view rather than shipping one:

| Document | Generated from |
|---|---|
| `.specify/wbs/wbs.md` | `wbs.yaml` |
| `.specify/risks/risk-register.md` | `risk-register.yaml` |
| `.specify/traceability/traceability.md` | the relation stores |
| `.specify/traceability/coverage.md` | `validate_trace.py` — coverage **and** the provenance mix |
| `.specify/governance/definition-of-ready.md` | `select_work.py` |
| `.specify/governance/definition-of-done.md` | `validate_done.py` |
| `.specify/governance/quality-gates.md` | `openup-config.yml` + `evaluate_gate.py` |

The last three matter most. A Definition of Ready that disagrees with `select_work.py`, or a
gate description that overstates what `evaluate_gate.py` checks, is worse than no document at
all: people follow the document while the machine applies the code. `approval-matrix.md` and
`change-control.md` are the exceptions — who may approve what is a decision about your
organisation, so those are authored from templates and never generated.

### Three standards ship as binding rules

`init_openup.py` seeds three more governance documents, and these are neither generated nor
organisational. They come from published specifications, and they bind the agent through the
root `AGENTS.md` and Principle VIII of the constitution addendum:

| Document | Binds | Standard |
|---|---|---|
| `.specify/governance/language-rules.md` | every governed document | ASD-STE100 Simplified Technical English |
| `.specify/governance/coding-rules.md` | every change to code | Railway Oriented Programming, RFC 9457 problem details, cloud-native data patterns |
| `.specify/governance/security-practices.md` | design, code, and the security gate evidence | the rules the security review applies |

The first two close a gap the structural checks cannot reach. A requirement written in a
40-word sentence with two readings still registers, still traces, and still passes every
check, while the implementation, the test and the gate each answer a different question. A
failure thrown as an exception carries no type and no id, so it cannot be bound to an
acceptance criterion or counted as evidence. Both are the same defect — meaning left in
someone's head — and neither is visible to a validator.

**None of the three is machine-checked.** They are enforced at review, each says so in its own
closing section, and an agent's claim to have followed them is `asserted`. Adding a checker
would be a real feature; pretending one exists would be the exact defect these documents are
about.

§65 says *"Do not manually maintain traceability documents."* Asking an agent to transcribe
YAML into Markdown is still manual maintenance, with an extra failure mode: it is
non-deterministic, every regeneration is a fresh diff, and nothing stops it from quietly
disagreeing with the canonical data.

---

## Gates

Four milestone gates, 23 condition declarations over 22 implementations, defined in
[`openup-config.yml`](extensions/openup/openup-config.yml):

| Gate | Phase | Asks |
|---|---|---|
| `GATE-LIFECYCLE_OBJECTIVES` | Inception | Is the scope, ownership and initial risk picture real? |
| `GATE-LIFECYCLE_ARCHITECTURE` | Elaboration | Is the architecture baselined and are the high risks handled? |
| `GATE-INITIAL_OPERATIONAL_CAPABILITY` | Construction | Is it built, covered, free of orphans, and actually done? |
| `GATE-PRODUCT_RELEASE` | Transition | Can it be released and operated? |

Two rules the implementation holds to:

- **Absence of evidence is not evidence.** A missing test report or review record *fails* its
  condition. A gate that passed because a file was never written would be worse than no gate.
- **Conditions fail closed.** A condition declared in config with no implementation, or one
  that raises, fails. It is never skipped.

---

## Enforcement

Every phase workflow ends with the same block:

```yaml
- id: evaluate-gate
  type: shell
  run: "python3 .specify/extensions/openup/scripts/python/evaluate_gate.py --gate <GATE> --json --out <evidence>"
  continue_on_error: true          # so the branches below are reachable

- id: halt-if-unevaluable          # exit 2 → setup fault, halt hard
  type: if
  condition: "{{ steps.evaluate-gate.output.exit_code == 2 }}"

- id: enforce-gate                 # exit 1 → governance failure, human decides
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

An `override` writes the failing verdict to `.specify/evidence/overrides/<run_id>.json`,
because an undocumented override is indistinguishable from a gate that never ran.

### Verified behavior

Run against spec-kit 1.0.6 with the real engine, using `tests/fixtures/good`:

| Graph state | Result |
|---|---|
| Healthy | `Status: completed` — runs to the final step |
| High-exposure risk stripped of its mitigation | `Status: paused` at `[gate-failed]` — **final step never reached** |
| `wbs.yaml` corrupted so the graph cannot load | `Status: failed`, `exited with code 2` |

And the bundle, into a clean `specify init` project — both routes:

| Step | Result |
|---|---|
| 4 × `catalog add` against the published catalog | all four registered; workflows resolve through `url`, the rest through `download_url` |
| `specify bundle install specup` | `✓ Installed 'specup' (6 added, 0 already present)` |
| `specify bundle list` after that | `specup v0.1.0 (6 components)` — a non-zero count is the proof the install was real |
| Published archive digests | `openup`, `openup-governance` and `specup` each hash identically as downloaded, as built locally, and as pinned in `catalog/` |
| `install.py --project <clean project>` | 6 components installed in manifest order, pins checked |
| `specify preset resolve spec-template` | `[append] openup-governance v0.1.0` composed onto core |
| 9 `speckit.openup.*` skills | registered under `.claude/skills/` |
| `audit.py` on the fresh scaffold | exit **1** — `initial_risks_registered`, `wbs_levels_1_to_3_valid` and `requirements_have_owners` all FAIL, correctly |
| `specify bundle build` | `specup-0.1.0.zip`, 3 files, fixed timestamps |
| A pin bumped to `0.2.0` in `bundle.yml` | install refuses before touching the project |

The three single-component routes, which the community-catalog submissions attest to, were
exercised separately against the published release:

| Step | Result |
|---|---|
| `specify extension add openup --from <release url>` | exit 0, 9 commands registered |
| `specify preset add --from <release url>` | exit 0, `spec-template` resolves to `[append] openup-governance v0.1.0` |
| `specify bundle install ./specup-0.1.0.zip` (downloaded artifact) | `6 added, 0 already present` |
| `specify bundle validate --path bundles/specup` | `✓ specup is well-formed and valid` |
| `preset add` into a project with no `openup` extension | warns `openup is not installed`, names `specify extension add openup`, installs anyway |

One gap in that record, stated rather than glossed: the verification host already had `PyYAML`
and `jsonschema` present, so the `pip install -r requirements.txt` step was not exercised from
a genuinely bare interpreter. The `exit 1` above is a real governance verdict rather than a
masked setup fault — the audit named `WBS-004`, `TRC-000` and three failing gate conditions —
but the missing-dependency path itself is covered only by the validators' own exit-2 contract.

The preset was likewise installed into a real `specify init` project: all four core templates
gained their `[append]` layer, the composed `speckit-tasks` skill had zero literal
`{CORE_TEMPLATE}` placeholders with pre/core/post in order, `{SCRIPT}` resolved identically to
an unwrapped command, and `specify preset remove` left nothing behind.

---

## Repository layout

```
specup.md                          the original design document (unchanged)
extensions/openup/
  extension.yml                    manifest: 9 commands, 15 templates, 15 scripts
  schemas/                         ID-GRAMMAR.md + 4 JSON Schemas
  scripts/python/                  the validators (~3,900 lines)
  templates/                       starter WBS, risk, traceability, vision, index,
                                   the three binding standards, 6 capability contracts
  openup-config.yml                thresholds, perimeter, gate definitions
presets/openup-governance/         4 append addenda + 2 wrap overlays
workflows/openup-{phase}/          the four phase workflows
bundles/specup/                    bundle.yml + the working-tree installer
catalog/                           the four published catalog documents (generated)
tools/                             archive + catalog generators
tests/                             248 tests + fixtures
```

---

## Corrections to `specup.md`

The design document is the source of intent, not of fact. Building against the real spec-kit
surfaced errors in it, recorded here because they are easy to repeat:

1. **§34's command names cannot exist.** `/speckit.wbs`, `/speckit.risk`, `/speckit.audit` are
   two-segment. Extension commands must match `^speckit\.[a-z0-9-]+\.[a-z0-9-]+$`. They are
   `/speckit.openup.*` here; two-segment names are core-only and reachable solely by a preset.
2. **§17's own WBS example is malformed.** It declares `id: "1.2.3.4.1.2"` with `level: 7`,
   but that id has six segments. Check `WBS-001` catches exactly this.
3. **§19's `TEST-PERF-022`** is outside the ID grammar the same document defines in §48.
4. **§48 defines eight prefixes it never uses**, while §21/§66/§67 use three overlapping
   relation vocabularies. Both are now closed sets.
5. **§18 contradicts §65** — "every leaf must be L7" versus "do not create seven levels of
   narrative". Resolved with the `semantic` depth policy.
6. **Exposure is never defined.** §19 shows `0.6 × 0.9 = 0.54` by example, and §19/§32/§63 all
   gate on "high" without saying what high is. Now a declared threshold.
7. **Hooks are not enforcement.** §30's gates cannot be built on `extension.yml` hooks: those
   render as instructions into a prompt and an agent can decline them.

Two things were added that the document does not have, because without them its central claim
is circular: **provenance** on every edge, and the **derived/asserted/approved ratio** in
every audit.

---

## Development

```bash
python3 -m pip install pyyaml jsonschema referencing pytest
python3 -m pytest tests/ -q          # 189 passed, 8 skipped
```

The 8 skips are the engine-validation tests. To run them, install spec-kit:

```bash
uv venv .venv && uv pip install --python .venv/bin/python specify-cli==1.0.6 pytest
uv pip install --python .venv/bin/python -r extensions/openup/requirements.txt
.venv/bin/python -m pytest tests/ -q  # 197 passed
```

Or with [Taskfile](docs/dev/taskfile.md), which wraps both suites and the release pipeline:

```bash
task test:both      # the pair is what proves the skips are honest
task release:check  # everything that must be green before tagging
```

`task` is a contributor convenience and never a runtime dependency — see
[the boundary](docs/dev/taskfile.md#the-boundary), which a test enforces.

They **skip rather than fake** when spec-kit is absent: a green test that did not run the
engine would be worse than an honest skip.

| Suite | Covers |
|---|---|
| `test_validators.py` | One deliberately-broken fixture per invariant |
| `test_derivers.py` | The derivation rules, and that `derived` cannot be claimed without them |
| `test_extension_manifest.py` | Spec Kit's documented manifest rules |
| `test_installed_layout.py` | The extension in its real `.specify/extensions/` layout |
| `test_workflows.py` | Structure, shell-injection rule, engine validation |
| `test_preset.py` | Preset schema, wrap contract, frontmatter preservation |
| `test_bundle.py` | Manifest schema, version-pin drift, the preset→extension pairing |
| `test_taskfile_boundary.py` | No workflow, command or manifest may reach the task runner |

Tests are mutation-checked. Neutering `WBS-001`, `RISK-001`, `TRC-010`, `TRC-011`,
`TRC-012`, the fail-closed path, the shell-injection rule, the wrap frontmatter rule, a
bundle version pin, and the bundle's extension entry each makes the corresponding tests
fail. Reverting `traceability_final` to scoring the `asserted` label instead of reproduced
evidence fails two.

---

## Limitations

- **`specify bundle install` cannot install an unreleased working tree.** Spec-kit resolves
  component ids only against assets shipped in its own wheel or a published catalog, and
  there is no `--dev` for bundles. That is fine for a release — the catalog route in the
  Quick start is exactly this — but it means an edit you have not released is unreachable
  through it. [`install.py`](bundles/specup/install.py) covers that case, and is also the
  only offline route. See
  [Why the two cannot be collapsed](bundles/specup/README.md#why-the-two-cannot-be-collapsed).
- **Nothing validates a contract document.** `MICROCKS-TEST-*` ids and the `validates`
  relation are reserved in the grammar so nothing has to be renamed later, but no contract
  checking runs at all: `contracts.microcks.enabled`, `openapi_glob` and `asyncapi_glob`
  are read by no code, and `critical_contracts_defined` only asserts that each registered
  `CONTRACT-*` artifact's declared `source` file exists on disk — the OpenAPI/AsyncAPI
  document itself is never parsed. Mocking and conformance is `specup.md`'s own Maturity
  Level 4; static schema validation is not built either.
- **Two of five derivation rules are unimplemented.**
  `openapi-operation-scan` and `evidence-manifest-scan` are named in
  [`speckit.openup.trace.md`](extensions/openup/commands/speckit.openup.trace.md) but have
  no code behind them, so an edge claiming one of them cannot be reproduced. `TRC-010`
  reports those edges as unverified rather than counting them as machine-checkable.
- **An approval binds content, not a human.** `approved_endpoints_hash` proves an edge still
  matches what was signed off (`TRC-013`), and that is all it proves. Nothing establishes that
  a person was involved: an agent can run `approve_edge.py --by product-owner` exactly as a
  human can. The only real anchor is `approval.commit` pointing at a signed commit, verified
  against git, which is not implemented. Read `approved` as "someone took accountability under
  this name", never as "a human checked this".
- **The three binding standards are unenforced by design, for now.** `language-rules.md`,
  `coding-rules.md` and `security-practices.md` are prompt-level rules: the root `AGENTS.md`
  and Principle VIII of the constitution bind an agent to them, and a human reviewer is the
  only thing that checks. Parts of all three are mechanically decidable — sentence length, the
  non-approved word table, `application/problem+json` on every failure response, the RFC 9457
  member set — and a validator over that subset is the obvious next increment. It is not
  written, so do not read a passing gate as evidence of conformance to any of them.
- **No CI enforcement yet.** The validators are CI-ready by construction — JSON out, exit
  codes — but no pipeline is authored (§62–63).
- **`python3` in shell steps.** Windows hosts normally have `python`; adjust the `run:` lines
  or provide a shim.
- **Governance overhead is unmeasured.** `specup.md` §65 warns that process can outgrow its
  value, and §57 implies ~10 artifact fetches per task against §33's example of 421 tasks.
  The context hierarchy is what the scalability argument rests on, and it now exists and is
  checked — but nothing measures the actual cost per unit of delivered work, and that is the
  thing most likely to sink the approach.

## License

MIT.
