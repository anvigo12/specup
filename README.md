# SpecUP

**OpenUP lifecycle governance for GitHub Spec Kit — with gates that actually stop the run.**

SpecUP turns [`specup.md`](specup.md), a design document, into a working
[Spec Kit](https://github.com/github/spec-kit) bundle: an extension, a preset, and four
phase workflows that enforce an [Eclipse OpenUP](https://www.eclipse.org/epf/)-style
lifecycle with a seven-level WBS, an executable risk register, and bi-directional
traceability.

> **Status:** Stages 0–4 complete and verified against spec-kit **1.0.6**. Stage 5 (the
> `specup` bundle that ships all three layers as one installable unit) is not built yet.
> Install the extension and preset separately until then.

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
```

A useful consequence: **the path an agent runs and the path a workflow runs are the same
string.** Extension commands get no `{SCRIPT}` substitution, so they reference
`.specify/extensions/openup/scripts/python/<validator>.py` literally — exactly what the
workflow `shell` steps invoke. There is no second thing to keep in sync.

---

## Quick start

```bash
# 1. A Spec Kit project
specify init --here --integration claude

# 2. The capability layer
cp -r extensions/openup .specify/extensions/openup
python3 -m pip install -r .specify/extensions/openup/requirements.txt

# 3. The discipline layer
specify preset add --dev ./presets/openup-governance

# 4. Scaffold the governance tree
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "My Product"

# 5. See where you stand (it will FAIL — an empty plan is not a valid plan)
python3 .specify/extensions/openup/scripts/python/audit.py
```

Then drive a phase:

```bash
specify workflow run ./workflows/openup-inception/workflow.yml \
  --input idea="..." --input program="My Product"
```

---

## The data model

`specup.md` describes identifiers three mutually inconsistent ways. Everything here is frozen
in [`ID-GRAMMAR.md`](extensions/openup/schemas/ID-GRAMMAR.md) and enforced by four JSON
Schemas, because IDs are graph edges and retrofitting them is the one genuinely expensive
migration.

**Identifiers** — zero-padded, regex-enforced: `REQ-AUTH-0014`, `WBS-1.2.3.4.1.1.2`,
`RISK-0007`, `AC-AUTH-0014-0003`, `ITER-E-02`. Source files have no synthetic id: the
repo-relative path *is* the identity, so traceability survives a validator rebuild.

**Relations** — a closed set of 16, stored **once in active voice**. The inverse is derived
at load time and never written. Two hand-maintained directions are two things that can
disagree, and disagreement is what traceability exists to prevent.

**Provenance** — on every edge, and the honest part of the model:

| Value | Meaning | Trust |
|---|---|---|
| `derived` | Recomputed from the filesystem by a named rule | Machine-checkable |
| `asserted` | Claimed by an agent or author | Claim only |
| `approved` | Asserted, then signed off by a named human | Governance-grade |

This exists because the agent writing the code otherwise also writes the proof it was traced
— auditor and audited collapse into one process. An `approved` edge is bound to its endpoints
by hash, so editing either one downgrades it rather than silently keeping the sign-off.

**Seven WBS levels** — L1 Program → L7 Executable Task, where the number of dotted segments
*is* the level. `specup.md` §18 demands every leaf be L7, which collides with its own §65
anti-bloat rule; the default `semantic` policy lets a leaf terminate early when it declares a
`terminal_reason`. `strict` mode implements §18 literally.

---

## Validators

Six CLIs. Each emits a JSON verdict on stdout and exits `0` pass / `1` fail / `2`
could-not-evaluate. That dual contract is what lets one script serve both an agent and a
workflow step.

| Script | Checks | Covers |
|---|---|---|
| `validate_wbs.py` | 12 | level/id agreement, parentage, single root, depth policy, reference resolution, dependency cycles |
| `validate_risk.py` | 8 | exposure arithmetic, residual reduction, mitigation and verification for high risks, both-ends agreement |
| `validate_trace.py` | 10 | endpoint resolution, relation type legality, duplicates, cycles, forward/backward coverage, orphans, provenance floor |
| `select_work.py` | 3 | Definition of Ready, risk-first ordering |
| `evaluate_gate.py` | 21 conditions | every condition name declared in config |
| `audit.py` | — | the aggregate §33 report |

**Exit 2 is not exit 1.** A graph that fails to load is a setup fault, not a governance
failure. Collapsing them would tell someone their project failed its milestone when the truth
is a malformed YAML file.

---

## Gates

Four milestone gates, 22 condition declarations over 21 implementations, defined in
[`openup-config.yml`](extensions/openup/openup-config.yml):

| Gate | Phase | Asks |
|---|---|---|
| `GATE-LIFECYCLE_OBJECTIVES` | Inception | Is the scope, ownership and initial risk picture real? |
| `GATE-LIFECYCLE_ARCHITECTURE` | Elaboration | Is the architecture baselined and are the high risks handled? |
| `GATE-INITIAL_OPERATIONAL_CAPABILITY` | Construction | Is it built, covered, and free of orphans? |
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

The preset was likewise installed into a real `specify init` project: all four core templates
gained their `[append]` layer, the composed `speckit-tasks` skill had zero literal
`{CORE_TEMPLATE}` placeholders with pre/core/post in order, `{SCRIPT}` resolved identically to
an unwrapped command, and `specify preset remove` left nothing behind.

---

## Repository layout

```
specup.md                          the original design document (unchanged)
extensions/openup/
  extension.yml                    manifest: 9 commands, 7 templates, 8 scripts
  schemas/                         ID-GRAMMAR.md + 4 JSON Schemas
  scripts/python/                  the validators (~2,000 lines)
  templates/                       starter WBS, risk, traceability, vision, index
  openup-config.yml                thresholds, perimeter, gate definitions
presets/openup-governance/         4 append addenda + 2 wrap overlays
workflows/openup-{phase}/          the four phase workflows
tests/                             130 tests (~1,260 lines) + fixtures
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
python3 -m pytest tests/ -q          # 126 passed, 4 skipped
```

The 4 skips are the engine-validation tests. To run them, install spec-kit:

```bash
uv venv .venv && uv pip install --python .venv/bin/python specify-cli==1.0.6 pytest
uv pip install --python .venv/bin/python -r extensions/openup/requirements.txt
.venv/bin/python -m pytest tests/ -q  # 130 passed
```

They **skip rather than fake** when spec-kit is absent: a green test that did not run the
engine would be worse than an honest skip.

| Suite | Covers |
|---|---|
| `test_validators.py` | One deliberately-broken fixture per invariant |
| `test_extension_manifest.py` | Spec Kit's documented manifest rules |
| `test_installed_layout.py` | The extension in its real `.specify/extensions/` layout |
| `test_workflows.py` | Structure, shell-injection rule, engine validation |
| `test_preset.py` | Preset schema, wrap contract, frontmatter preservation |

Tests are mutation-checked. Neutering `WBS-001`, `RISK-001`, the fail-closed path, the
shell-injection rule, and the wrap frontmatter rule each makes the corresponding tests fail.

---

## Limitations

- **Stage 5 is not built.** There is no `bundle.yml`, so the extension, preset and workflows
  install separately. Spec Kit has no preset→extension dependency mechanism, which means
  nothing currently prevents installing the preset without the extension — its guidance would
  reference validators that are not there.
- **Microcks is deferred.** v1 does static OpenAPI/AsyncAPI validation only. Contract
  mocking and conformance is `specup.md`'s own Maturity Level 4.
- **No CI enforcement yet.** The validators are CI-ready by construction — JSON out, exit
  codes — but no pipeline is authored (§62–63).
- **`python3` in shell steps.** Windows hosts normally have `python`; adjust the `run:` lines
  or provide a shim.
- **Governance overhead is unmeasured.** `specup.md` §65 warns that process can outgrow its
  value, and §57 implies ~10 artifact fetches per task against §33's example of 421 tasks.
  Nothing here measures that yet, and it is the thing most likely to sink the approach.

## License

MIT.
