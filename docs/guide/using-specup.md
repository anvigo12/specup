# Using SpecUP

**Audience:** engineers and leads operating a SpecUP-governed repository day to day.

This is the operating manual. It assumes SpecUP is installed and you now have to live with
it: run the checks, read what they say, fix what they find, and get through a gate.

It is written to be read without the other pages. Where it overlaps with
[the guide](README.md), it goes further — every check id, every configuration key, every
field, and the reason each one exists.

One worked example runs through the whole document: **`REQ-AUTH-0014`, "Vehicle must
authenticate using a valid certificate"**, taken from `tests/fixtures/good` in this
repository. Every command output shown below is real output from running these scripts
against that fixture, not an illustration.

| | |
|---|---|
| 1 | [Before you start](#1-before-you-start) |
| 2 | [Install and scaffold](#2-install-and-scaffold) |
| 3 | [The daily loop](#3-the-daily-loop) |
| 4 | [The data model, store by store](#4-the-data-model-store-by-store) |
| 5 | [Provenance](#5-provenance-the-part-that-makes-the-rest-mean-anything) |
| 6 | [Check reference](#6-check-reference) |
| 7 | [Gates](#7-gates) |
| 8 | [Running a phase workflow](#8-running-a-phase-workflow) |
| 9 | [The nine agent commands](#9-the-nine-agent-commands) |
| 10 | [Changing a baselined artifact](#10-changing-a-baselined-artifact) |
| 11 | [Configuration reference](#11-configuration-reference) |
| 12 | [Troubleshooting](#12-troubleshooting) |
| 13 | [What SpecUP does not do](#13-what-specup-does-not-do) |
| 14 | [Where to go next](#14-where-to-go-next) |

---

## 1. Before you start

### Everything is a script you can run yourself

There are **15 command-line entry points** under
`.specify/extensions/openup/scripts/python/`. Nothing is agent-only. Whatever an agent or a
workflow tells you about the state of the project, you can reproduce by typing the same
command.

That is not a convenience feature. An agent reporting "traceability looks good" is an
assertion; a verdict you can re-run is evidence. The whole design leans on the second kind.

| Script | What it does | Exits |
|---|---|---|
| `init_openup.py` | Scaffolds the governance tree | `0` `2` |
| `validate_wbs.py` | 12 checks on the work breakdown structure | `0` `1` `2` |
| `validate_risk.py` | 8 checks on the risk register | `0` `1` `2` |
| `validate_trace.py` | 14 checks on the traceability graph | `0` `1` `2` |
| `validate_done.py` | 6 checks — the Definition of Done, computed | `0` `1` `2` |
| `validate_context.py` | 4 checks on the `AGENTS.md` / `index.md` / `SKILL.md` hierarchy | `0` `1` `2` |
| `validate_approvals.py` | 6 checks tying an approval to a person git can verify | `0` `1` `2` |
| `validate_docs.py` | 7 checks on docstrings as the working context for one unit | `0` `1` `2` |
| `derive_edges.py` | Reports (or with `--write`, regenerates) the mechanically-derivable edges | `0` `1` `2` |
| `render_views.py` | Reports (or with `--write`, regenerates) the seven generated documents | `0` `1` `2` |
| `select_work.py` | Applies the Definition of Ready; returns ready and blocked work | `0` `1` `2` |
| `evaluate_gate.py` | Evaluates one named milestone gate | `0` `1` `2` |
| `audit.py` | Aggregates every validator plus the current phase's gate | `0` `1` `2` |
| `impact.py` | What a change to one artifact reaches, in both directions | `0` `2` |
| `approve_edge.py` | Records a human approval on one edge | `0` `1` `2` |

Twelve of them emit the same verdict shape — `validator`, `status`, `checks[]`, `metrics`. Only
`audit.py`, `impact.py` and `approve_edge.py` emit their own, because they answer different
questions: an aggregate report, a traversal, and a write confirmation.

### Three exit codes, not two

| Code | Meaning | What you do |
|---|---|---|
| `0` | PASS | Nothing |
| `1` | FAIL | A governance invariant is violated. Fix the graph. |
| `2` | ERROR | The graph could not be loaded or parsed. Fix the setup. |

Keeping `2` separate from `1` is deliberate and worth understanding, because it changes what
a failing workflow means. A missing Python package, a malformed YAML file, an unreadable
schema, or a store declaring one id twice is an **operator error**, not a governance failure.
Collapsing the two would tell someone their project failed its architecture milestone when the
truth is that `risk-register.yaml` has a tab character in it. Every phase workflow branches on
`2` separately and says so.

In code this is one rule: a `GraphError` never becomes a `FAIL` verdict.

### Flags every script accepts

| Flag | Default | Why it exists |
|---|---|---|
| `--root PATH` | `.` | Run against a project other than the working directory |
| `--json` | off | Machine-readable verdict on stdout, for agents and pipelines |
| `--out PATH` | none | *Also* write the JSON verdict to a file |

`--out` looks redundant next to `--json` and is not. A workflow shell step cannot pipe
stdout through `tee` without destroying the exit code the branch below depends on, so
persisting the verdict has to be the validator's job. It is also how a gate verdict becomes
durable evidence rather than terminal scrollback.

Script-specific flags: `--write` (`derive_edges`, `render_views`), `--gate`
(`evaluate_gate`), `--of` (`impact`), `--iteration` and `--ids-only` (`select_work`),
`--program` (`init_openup`), and the `--from/--relation/--to/--by` set on `approve_edge`.

### One path, not two

Spec Kit substitutes `{SCRIPT}` into *core* command templates, but not into extension
commands. So every `/speckit.openup.*` command references
`.specify/extensions/openup/scripts/python/<name>.py` **literally** — exactly the string a
workflow `shell` step runs, and exactly the string you type.

There is no second path to keep in sync, and nothing that could drift between what the agent
runs and what the gate runs.

### Which layer can actually stop you

| Layer | Real enforcement? | Why |
|---|---|---|
| Preset (`openup-governance`) | No | Prompt-level. It changes what the model is told. |
| Extension (`openup`) | No | Its hooks render as instructions. A model can decline them. |
| **Workflow** (`openup-<phase>`) | **Yes** | A non-zero `shell` exit halts the run; `gate` with `on_reject: abort` terminates it. |
| Bundle (`specup`) | No | Distribution only. |

This single fact explains the shape of everything else. Governance living only in templates
is governance the model may simply not follow, and you would never know. So every hard check
lives in a workflow shell step, and the preset and extension exist to make those checks
reachable and legible — not to *be* the checks.

---

## 2. Install and scaffold

### Prerequisites

| Need | Why |
|---|---|
| Python 3.10+ | The validators |
| `specify` CLI ≥ 1.0.6 | Spec Kit itself |
| A git repository | Every governed artifact is a version-controlled file |

### Once per machine

Spec Kit resolves components through catalogs, and its `default` catalog holds only what is
vendored into the Spec Kit wheel. Every third-party project publishes its own catalog, so
registering SpecUP's is the supported route rather than a workaround. Each archive is pinned
by SHA-256 and the install aborts if the bytes do not match.

Register all four at user scope, once:

```bash
mkdir -p ~/.specify
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user
for f in extension preset workflow bundle; do
  curl -sSL -o ~/.specify/$f-catalogs.yml $BASE/$f-catalogs.yml
done
```

Read them before you run that — four short files deciding where your machine downloads code
from. [`catalog/user/README.md`](../../catalog/user/README.md) explains each one.

**There is no CLI equivalent.** `specify <primitive> catalog add` calls
`_require_specify_project()` and writes `<project>/.specify/<primitive>-catalogs.yml`; no
subcommand has a `--user` flag. Spec Kit *reads* `~/.specify/<primitive>-catalogs.yml` for all
four primitives, so the file route does once what the command route does per project.

### Once per project

```bash
specify init --here --integration claude          # if not already a Spec Kit project
specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt
```

The bundle installs the extension, then the preset, then the four workflows. **The order is
load-bearing.** The preset's guidance instructs agents to run validators the *extension*
ships. The preset declares that dependency, so installing it alone does warn — but the
warning is all it is: Spec Kit checks after the install has succeeded, installs nothing, and
refuses nothing. Installed alone, the preset reads as fully authoritative while every check
it names silently does not run.

To install a working tree instead of a release — developing SpecUP, needing an unreleased
change, or with no network — use the repository's own installer:

```bash
python3 /path/to/specup/bundles/specup/install.py --project .
```

Useful flags: `--dry-run` prints what would happen and checks the version pins without
touching anything; `--skip-record` omits the final provenance-recording call. After that
route `specify bundle list` shows 0 components, which is correct and explained in
[`bundles/specup/README.md`](../../bundles/specup/README.md#why-the-two-cannot-be-collapsed).

**The `pip install` line is not optional.** `bundle install` says so itself — it prints
`! Requires external tools: python3 >=3.10, pip: PyYAML>=6.0, jsonschema>=4.18,
referencing>=0.30` from the bundle manifest — but a warning you scrolled past and an exit
code you can see are different things, so check:

```bash
python3 .specify/extensions/openup/scripts/python/audit.py; echo "exit=$?"
```

Exit `1` is the correct result on a fresh project — an empty plan is not a valid plan. Exit
`2` means the dependencies are missing.

`audit.py` is the right probe because it is one of the validators that needs all three.
Missing `PyYAML` takes every validator to `2`; missing only the schema libraries is narrower,
and the split is worth knowing when you are diagnosing a partial install:

| Needs `jsonschema` + `referencing` | Runs on `PyYAML` alone |
|---|---|
| `validate_wbs`, `validate_risk`, `validate_trace`, `render_views`, `audit` | `validate_done`, `validate_context`, `select_work`, `derive_edges` |

Either way the failure is an honest `2` rather than a gate that passes without evaluating,
which is the property that matters.

### If you would rather scope the catalogs to one project

Run the four `catalog add` commands instead of copying the files, and know what they cost:

```bash
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog
specify extension catalog add $BASE/extensions.json --name specup --install-allowed --priority 0
specify preset    catalog add $BASE/presets.json    --name specup --install-allowed --priority 0
specify workflow  catalog add $BASE/workflows.json  --name specup --priority 0
specify bundle    catalog add $BASE/bundles.json    --id specup --policy install-allowed --priority 0
```

`--id specup` is not optional in spirit. Without it Spec Kit derives the source id from the
URL and you get `raw-githubusercontent-com-bundles` in your config.

**This removes Spec Kit's own catalogs from that project.** For extensions, presets and
workflows a config file *replaces* the stack below it rather than merging —
`get_active_catalogs` returns the first scope that loads and never consults the next. So a
project config naming only `specup` is the entire stack for that primitive. On a fresh
project `specify extension search` drops from **173 extensions to 1**.

The four core extensions still install, because they are vendored in the wheel rather than
fetched, and that is precisely what makes the loss hard to notice: nothing you try fails,
things simply stop being findable. If you take this route, restate `default` and `community`
in each file — [`catalog/user/*.yml`](../../catalog/user/) shows the shape, and those files
work unchanged at project scope.

Bundles are the exception both ways: their sources merge by id across built-in → user →
project, so `bundle-catalogs.yml` never needs the built-ins restated.

### Scaffold

```bash
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "My Product"
```

This creates seven directories and seeds seventeen authored files plus six capability
contracts and an `index.md` per governed directory:

```
.specify/
├── lifecycle/        vision.md, stakeholders.md, index.md
├── governance/       change-control.md, approval-matrix.md, allowed-signers, index.md,
│                     language-rules.md, coding-rules.md, security-practices.md
├── architecture/     architecture-template.md, adr-template.md, index.md
├── wbs/              wbs.yaml, index.md
├── risks/            risk-register.yaml, index.md
├── traceability/     requirements.yaml, traceability.yaml, index.md
└── evidence/         index.md
AGENTS.md                         the operating contract, repository-wide
.specify/AGENTS.md                narrowed to the governance tree
src/AGENTS.md                     narrowed to implementation code
skills/{wbs,risk,requirements,traceability,gherkin,architecture}/SKILL.md
```

**`init_openup.py` never overwrites an authored file.** Re-running it is safe, and is the
supported way to restore a store someone deleted. Authored content survives; that is the
converse of "generated does not mean approved".

**The two files under `architecture/` keep their `-template` names on purpose.** Copy
`architecture-template.md` to `architecture.md` when you write one, and `adr-template.md` to
`adr-0001-<slug>.md` per decision. `architecture_baselined` checks only that
`architecture.md` **exists**, so seeding a blank one would retire the gate's first condition
on day one while the document still said nothing. Left as templates, the gate keeps reporting
"no architecture document found" — which is the truth — and an author still has somewhere to
start.

### What that one command also generates

Three governance documents are **not seeded from templates**: `definition-of-ready.md`,
`definition-of-done.md` and `quality-gates.md`. They are generated from the code that
enforces them — `select_work.py`, `validate_done.py`, and `openup-config.yml` +
`evaluate_gate.py` respectively — and `init_openup.py` runs that generation for you.

The reason they are generated is the sharpest one in the whole system: **a governance
document that disagrees with the check is worse than no document at all**, because people
follow the document while the machine applies the code. Generating them makes disagreement
impossible.

That reason is about what *produces* them, not about when, which is why this is one command
rather than two. Generated documents are owned by the code, so unlike the authored files
above they *are* rewritten on a re-run — a stale one is a defect, and `VIEW-001` fails on it.

Two flags matter here:

| Flag | Effect |
|---|---|
| `--no-render` | Scaffold only. Rendering needs `jsonschema` and `referencing`; the scaffold needs neither, so this still works on a machine that has only PyYAML. |
| `--json` | Emits the validator verdict shape, with `INIT-003` carrying the render result. |

If rendering cannot run, `init_openup.py` **exits `2` and says so** rather than exiting `0`
with three documents quietly missing. The scaffold is still written, so the fix is to install
the dependencies and re-run. Exit `2` is the same could-not-evaluate code every validator
uses, so a workflow halts on its setup-fault branch instead of proceeding over a tree that
looks finished.

`approval-matrix.md` and `change-control.md` are the deliberate exceptions. Who may approve
what is a decision about your organisation, and no validator can recompute it — so those are
authored from templates and never generated.

### The three binding standards

`init_openup.py` also seeds three standards, and they are a different kind of document again.
They are not generated, because no code decides them; and they are not organisational
choices, because they come from published specifications.

| Document | Binds | Standard |
|---|---|---|
| `.specify/governance/language-rules.md` | every governed document | ASD-STE100 Simplified Technical English |
| `.specify/governance/coding-rules.md` | every change to code | Railway Oriented Programming, RFC 9457 problem details, cloud-native data patterns |
| `.specify/governance/security-practices.md` | design, code, and the security gate evidence | the rules the security review applies |

They are binding in the same sense as *"Resolve, or stop — never infer"*: the root
`AGENTS.md` names all three, and the constitution addendum carries them as Principle VIII, so
an agent reading its operating contract is told to obey them. **No validator checks any of
them.** Conformance is established at review, and an agent's report that it followed them is
`asserted` — the same label, carrying the same weight, as any other unverified claim.

Two of the three are worth reading before you write anything:

- `language-rules.md` exists because a requirement two people read differently still
  registers, still traces, and still passes every structural check, while the implementation,
  the test and the gate each answer a different question. Nothing downstream can detect that.
- `coding-rules.md` exists because an exception carrying a string has no type, no id, and no
  link to the requirement that anticipated it — so a failure mode raised that way cannot be
  covered by an acceptance criterion or counted as evidence at a gate. Give the failure an
  RFC 9457 `type` URI and it becomes an artifact the graph can see.

`security-practices.md` earns its place differently. Two gate conditions —
`security_review_complete` and `security_validation_passed` — read a JSON record and check
that it says `passed`. Neither knows what was reviewed, and the required shape of those two
records was documented nowhere else. That file is the standard the reviewer applies and the
schema the records must match.

A project may amend any of the three. It is a governance decision under
`change-control.md`, not an edit — which is the point of seeding them into the repository
rather than reading them out of the installed extension.

### Commit before writing anything into it

```bash
git add -A && git commit -m "Scaffold OpenUP governance"
```

The first diff of a governance file should be legible as a decision, not buried inside the
scaffold.

---

## 3. The daily loop

Most days you do not run a whole workflow. You run five commands.

```bash
cd <project root>
P=.specify/extensions/openup/scripts/python

# 1. What am I allowed to work on?
python3 $P/select_work.py

# ... do the work ...

# 2. Pick up what the filesystem changed under you
python3 $P/derive_edges.py --write

# 3. Is the graph still sound?
python3 $P/validate_wbs.py
python3 $P/validate_risk.py
python3 $P/validate_trace.py
python3 $P/validate_done.py

# 4. Keep the generated documents in step
python3 $P/render_views.py --write

# 5. Where do we stand overall?
python3 $P/audit.py
```

Why in that order:

- **`select_work.py` first** because the Definition of Ready is cheaper to satisfy before you
  start than to discover afterwards. It returns each blocked task *and the rule id that
  blocked it*, so a refusal is traceable to a published rule rather than a judgement call.
- **`derive_edges.py --write` before validating**, because writing a test file or tagging a
  scenario creates edges that the rules can now recover. Until you regenerate, `TRC-011`
  fails for edges the filesystem already supports.
- **`render_views.py --write` after the YAML settles**, because `VIEW-001` fails on a stale
  view, and a workflow will fail on it rather than ship a document that disagrees with its
  source.
- **`audit.py` last**, because it runs all of the above plus the gate for your current phase.

Run the phase workflow when you are crossing a phase boundary. That is when the gate matters.

Or, through the agent: `/speckit.openup.audit`, `/speckit.openup.gate`,
`/speckit.openup.trace`.

---

## 4. The data model, store by store

Everything is a version-controlled file under `.specify/`. There is no database and no hidden
state. Four JSON Schemas in `.specify/extensions/openup/schemas/` enforce the shapes;
[`ID-GRAMMAR.md`](../../extensions/openup/schemas/ID-GRAMMAR.md) beside them is the normative
statement of identifiers, relations and provenance.

### 4.0 Identifiers

Every governed artifact has exactly one id, zero-padded and regex-enforced.

| Kind | Pattern | Example |
|---|---|---|
| Business objective | `BUS-OBJ-<NNNN>` | `BUS-OBJ-0017` |
| Requirement | `REQ-<DOMAIN>-<NNNN>` | `REQ-AUTH-0014` |
| Non-functional requirement | `NON-FR-<DOMAIN>-<NNNN>` | `NON-FR-AUTH-0017` |
| Feature | `FEAT-<NNNN>` | `FEAT-0014` |
| User story | `USR-STR-<NNNN>` | `USR-STR-0014` |
| Acceptance criterion | `AC-<DOMAIN>-<NNNN>-<NNNN>` | `AC-AUTH-0014-0003` |
| Scenario | `SCEN-<DOMAIN>-<NNNN>` | `SCEN-AUTH-0031` |
| WBS node | `WBS-<dotted path>` | `WBS-1.2.3.4.1.1.2` |
| Risk | `RISK-<NNNN>` | `RISK-0007` |
| Architecture decision | `ADR-<NNNN>` | `ADR-0019` |
| Test case / unit / integration / e2e | `TC-`, `UNIT-`, `INTG-`, `E2E-` `<DOMAIN>-<NNNN>` | `TC-AUTH-0031` |
| Contract | `CONTRACT-<DOMAIN>-<NNNN>` | `CONTRACT-AUTH-0001` |
| Evidence | `EVID-<NNNN>` | `EVID-0001` |
| Iteration | `ITER-[IECT]-<NN>` | `ITER-E-02` |
| Gate | `GATE-<SCREAMING_SNAKE>` | `GATE-LIFECYCLE_ARCHITECTURE` |
| Source file | a repo-relative POSIX path | `src/security/certificate_validator.ts` |

`<DOMAIN>` is `[A-Z][A-Z0-9]{1,11}`. `<NNNN>` is four digits, zero-padded — padding is what
makes ids sort lexicographically, which the generated Markdown views depend on.

**Ids are stable for the life of the artifact.** They are the edges of the graph, so renaming
one breaks traceability. Supersede, never rename.

**There is deliberately no `TASK-*`.** WBS level 7 *is* the executable task. A parallel task
identity would be a second name for one thing, which is the drift this model exists to
prevent.

#### Where ids come from

**Nothing generates them.** There is no allocator in the codebase, and that is worth
understanding before your first requirement, because "stable" is not a property of how an id
is made — it is a property of how it is treated afterwards.

There are four cases, and only the last involves you choosing a number:

| Kind | How the id is decided |
|---|---|
| **WBS nodes** | **Positional.** `init_openup.py` seeds `WBS-1`; every child is its parent plus `.n`. The id *is* the coordinate in the tree |
| **Source files** | **No synthetic id at all.** The repo-relative path is the identity |
| **Scenarios** | **Authored once in the `.feature` file**, then read back by `gherkin-tag-scan` from the `@SCEN-` tag |
| **Everything else** | **You pick the next ordinal by hand.** The commands instruct an agent to "assign the next `RISK-nnnn`" — that is a prompt, not code |

Each has a reason:

- A WBS id is positional so there is **one** representation of the tree rather than two. That
  is precisely what lets `WBS-001` check the declared `level` against the segment count and
  `WBS-002` check `parent` against the id minus its last segment — neither check exists if the
  id is an arbitrary label sitting next to the structure. The cost is that re-parenting a node
  changes its id, which is right: it became a different piece of work.
- A source file has no id because an assigned id is a second name that can drift from the
  file, and a path cannot. Moving the file breaks its edges, which is correct — the edge was
  about that file in that place.
- A scenario's `@SCEN-` tag is required rather than inferred from the filename. An inferred id
  would make the edge depend on a guess, and a guess recorded as `derived` is an assertion
  wearing a better label. Exactly one tag per scenario; zero or two derive nothing and
  `DRV-003` says so.

#### Uniqueness is enforced at load time

An id names exactly one thing, and all three stores refuse a collision with `GraphError` —
**exit 2, not a failing check**:

```
specs/001-auth/artifacts.yaml: duplicate artifact REQ-AUTH-0014 — already declared in
.specify/traceability/requirements.yaml. An id names exactly one artifact for its whole
life; supersede it, never reuse it.
```

Exit 2 is the honest verdict rather than a governance failure. A store declaring one id twice
does not describe a graph that breaks a rule; it describes **no graph at all**, because the
loader would have to discard one of the two to build anything, and every check downstream
would then be computing over an arbitrary choice. The same refusal applies to an entry with no
id — usually a typo'd `id:` key — and the error names the entry by its title so you can find
it.

#### Allocating ids in a new repo

1. **Use the domain tag as your namespace.** `REQ-AUTH-0001` and `REQ-BILLING-0001` cannot
   collide, so teams allocate independently. This is the main thing `<DOMAIN>` is for, and it
   matters most once you use per-feature `specs/*/artifacts.yaml` registries — they all merge
   into one graph, so two features reaching for the same bare number is the natural collision.
2. **Allocate per `(type, domain)` from one place** — highest existing, plus one:
   `grep -rho 'REQ-AUTH-[0-9]\{4\}' .specify specs | sort -u | tail -1`
3. **Never reuse a number**, even after deleting an artifact. The old id may still be named in
   a commit message, an evidence file, or someone's notes.
4. **Always zero-pad to four.** Padding is what makes ids sort lexicographically, which the
   generated Markdown views depend on — it is not cosmetic.

### 4.1 `.specify/traceability/requirements.yaml` — the artifact registry

Everything an edge can point at, other than a WBS node, a risk, or a source path, is
registered here.

```yaml
schema_version: "1.0"

artifacts:
  - id: REQ-AUTH-0014
    type: requirement
    title: "Vehicle must authenticate using a valid certificate"
    status: APPROVED
    owner: product-owner
    priority: high
    phase: ELABORATION
    iteration: ITER-E-02
```

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Any governed id, including a source path |
| `type` | yes | One of 21: `requirement`, `acceptance-criterion`, `scenario`, `contract`, `evidence`, `architecture-decision`, … |
| `title` | yes | 1–200 characters |
| `status` | yes | A governance state, below |
| `owner` | — | Required at `BASELINED` and beyond; `requirements_have_owners` needs it on every requirement |
| `priority` | — | `critical` / `high` / `medium` / `low` |
| `phase`, `iteration` | — | Lifecycle position |
| `source` | — | The file the artifact is authored in. Load-bearing for tests and contracts — see below |
| `baseline.version` | — | Incremented on re-baseline |
| `approvals[]` | — | `{by, at, commit?, note?}`. **Required at `BASELINED`+** |
| `supersedes` | — | The id this replaces |
| `tags[]` | — | Free-form |

**Governance states** run forward only, one step at a time, except that any state may drop
back to `DRAFT` on amendment:

```
DRAFT → REVIEW → APPROVED → BASELINED → IMPLEMENTED → VERIFIED → ACCEPTED
```

`BASELINED` and beyond require at least one recorded approval *and* an owner — the schema
enforces that, not a convention. And **generated does not mean approved**: anything a command
creates enters at `DRAFT`.

`source` matters more than it looks. For a test artifact it is what
`test-file-naming-convention` reads to derive the `tests` edge; for a `CONTRACT-*` it is the
file `critical_contracts_defined` checks the existence of. An artifact with no `source` of its
own inherits the registry file it was declared in.

### 4.2 `.specify/wbs/wbs.yaml` — the work breakdown structure

```yaml
schema_version: "1.0"
program: "Autonomous Traffic Platform"
depth_policy: semantic

nodes:
  - id: WBS-1.2.3.4.1.1.2
    name: "Implement certificate validation"
    level: 7
    parent: WBS-1.2.3.4.1.1
    phase: ELABORATION
    iteration: ITER-E-02
    status: done
    kind: risk-mitigation
    owner: backend-team
    requirements: [REQ-AUTH-0014]
    risks: [RISK-0007]
    dependencies: [WBS-1.2.3.4.1.1.1]
    estimate: { unit: hours, value: 8 }
    evidence: [EVID-0001]
```

**The number of dotted segments *is* the level.** `WBS-1.2.3` is always L3. This is why an id
and its declared `level` can never quietly disagree — `WBS-001` compares them, and the id
wins.

| Level | Meaning | What it resolves |
|---|---|---|
| L1 | Program / Product | strategic context |
| L2 | OpenUP Phase | lifecycle objective |
| L3 | Iteration | near-term delivery goal |
| L4 | Capability / Feature | functional scope |
| L5 | Requirement / User Story | expected behaviour |
| L6 | Engineering Work Package | engineering slice |
| L7 | **Executable Task** | executable unit |

| Field | Notes |
|---|---|
| `id`, `name`, `level`, `status` | Required. `status` ∈ `planned` `ready` `in-progress` `blocked` `done` `cancelled` |
| `parent` | Required on everything except the L1 root, which must *not* declare one |
| `kind` | `structural` (default) `implementation` `test` `risk-mitigation` `spike` `release` |
| `owner`, `iteration`, `requirements` | **Required on every L7 node**, with ≥1 requirement |
| `risks` | **Required on `kind: risk-mitigation`**, ≥1 |
| `acceptance` | **Required on `kind: test`**, ≥1 |
| `dependencies` | Other WBS ids. Must exist and be acyclic |
| `terminal_reason` | 12–300 chars. Required for a leaf above L7 under `semantic` |
| `estimate` | `{unit: hours\|days\|points, value: >0}` |
| `evidence` | `EVID-*` ids |
| `skills` | Names `skills/<name>/SKILL.md`. `CTX-004` fails if one does not exist |

`kind` is the mechanism by which conditional invariants apply. It is not a label: setting
`kind: test` obliges the node to name acceptance criteria, and setting `kind: risk-mitigation`
obliges it to name a risk *and* obliges that risk to name it back (`RISK-006`). An edge that
agrees from only one end is not a link.

**Depth policy.** `semantic` (the default) keeps the level meanings fixed but lets a branch
terminate above L7 when it declares a `terminal_reason`:

```yaml
  - id: WBS-1.1.1.2
    name: "Legacy settlement engine"
    level: 4
    parent: WBS-1.1.1
    terminal_reason: "In maintenance; no planned work. Outside the traceability perimeter."
```

`strict` requires every leaf to be L7. Levels 1–3 are pure structure under either policy, so
a leaf there is always an error — an empty plan, not a concise one.

This setting exists because the design document contradicts itself: §18 demands every leaf be
L7 while §65 warns against creating seven levels of narrative. `semantic` resolves it by
making early termination a *declared, reviewable act* rather than an omission — and
`render_views.py` surfaces every `terminal_reason` in the generated `wbs.md`, so the exception
cannot hide in the YAML.

### 4.3 `.specify/risks/risk-register.yaml` — the risk register

```yaml
schema_version: "1.0"

risks:
  - id: RISK-0007
    title: "Certificate validation latency"
    category: technical
    probability: 0.6
    impact: 0.9
    exposure: 0.54                      # DERIVED: recomputed, must match
    phase_identified: ELABORATION
    iteration_identified: ITER-E-02
    status: mitigating
    owner: security-team
    mitigation:   [WBS-1.2.3.4.1.1.2]   # real WBS nodes, never prose
    verification: [TC-AUTH-0031]
    residual_probability: 0.2
    residual_impact: 0.5
    residual_exposure: 0.10
    evidence: [EVID-0001]
```

| Field | Required | Notes |
|---|---|---|
| `id`, `title`, `category`, `probability`, `impact`, `phase_identified`, `status`, `owner` | yes | |
| `category` | yes | `technical` `architectural` `security` `schedule` `resource` `external` `operational` `compliance` |
| `probability`, `impact` | yes | 0..1 inclusive |
| `exposure` | — | If present, recomputed as `probability × impact` and must match within 1e-9 |
| `status` | yes | `open` `mitigating` `mitigated` `accepted` `closed` `materialized` |
| `mitigation[]` | — | WBS ids. **Required at `mitigated`/`closed`** |
| `verification[]` | — | `TC-`/`UNIT-`/`INTG-`/`E2E-`/`MICROCKS-TEST-`/`EVID-` ids. **Required at `mitigated`/`closed`** |
| `residual_probability` / `_impact` / `_exposure` | — | The first two come as a pair or not at all |
| `acceptance_approval` | — | **Required at `status: accepted`** |
| `evidence[]`, `history[]` | — | |

Three design decisions worth the space:

**Exposure is arithmetic, not opinion.** `exposure = probability × impact`. The design
document states this only by example (`0.6 × 0.9 = 0.54`) and never defines "high", while
three separate sections gate on it — so the thresholds are declared in config
(`high_exposure_threshold: 0.40`, `critical_exposure_threshold: 0.65`) and `RISK-001` rejects
a stored `exposure` that disagrees with the multiplication. A hand-edited exposure is how
registers silently drift.

**Mitigation points at work, not at prose.** `mitigation` takes WBS ids. A mitigation nobody
scheduled is a wish, and this is the field that converts a worry into scheduled work or into
an explicit, approved acceptance.

**A mitigation that did not reduce exposure is a no-op.** `RISK-003` rejects a residual
exposure that is not strictly below the current one, unless the risk is explicitly `accepted`.
Marking something `mitigated` while the numbers stand still is the failure mode this check
exists for.

Accepting a live risk requires a named human:

```yaml
  status: accepted
  acceptance_approval:
    by: "Head of Engineering"
    at: "2026-09-12T10:00:00Z"
    note: "Rewrite scheduled Q2; interim manual verification in place."
```

### 4.4 `.specify/traceability/*.yaml` — the edges

```yaml
schema_version: "1.0"
scope: ".specify"

edges:
  - from: WBS-1.2.3.4.1.1.2
    relation: implements
    to: REQ-AUTH-0014
    provenance: asserted
```

| Field | Required | Notes |
|---|---|---|
| `from`, `relation`, `to`, `provenance` | yes | |
| `id` | — | `TRACE-nnnn`, if you want to name the edge |
| `status` | — | `proposed` `active` (default) `verified` `broken` `superseded` |
| `source_file` | — | Defaults to the store the edge was read from |
| `evidence[]` | — | `EVID-*` ids or paths |
| `derived_by` | conditionally | **Required when `provenance: derived`** |
| `approval`, `approved_endpoints_hash` | conditionally | **Both required when `provenance: approved`** |
| `note` | — | |

**The closed relation vocabulary — 14, each stored once in active voice:**

| Relation | Inverse (derived, never stored) | Domain → Range |
|---|---|---|
| `refines` | `refined-by` | Requirement → BusinessObjective; UserStory → Requirement; ADR → Requirement |
| `contains` | `contained-by` | WBSNode → WBSNode; Feature → Requirement |
| `implements` | `implemented-by` | WBSNode / SourceFile → Requirement / ADR |
| `verifies` | `verified-by` | AcceptanceCriterion / Test → Requirement |
| `executes` | `executed-by` | Scenario → AcceptanceCriterion |
| `tests` | `tested-by` | UnitTest / IntegrationTest → SourceFile |
| `conforms-to` | `conformed-by` | SourceFile → Contract |
| `validates` | `validated-by` | MicrocksTest → Contract |
| `mitigates` | `mitigated-by` | WBSNode → Risk |
| `evidences` | `evidenced-by` | Evidence → WBSNode / Gate / Risk |
| `depends-on` | `depended-on-by` | WBSNode → WBSNode |
| `belongs-to` | `owns` | WBSNode → Iteration |
| `approves` | `approved-by` | *any → any* |
| `supersedes` | `superseded-by` | *any → any* |

A relation outside this set is rejected. A relation used outside its domain and range fails
`TRC-003` — `implements` from a Risk to a Contract does not quietly land in the graph.

`approves` and `supersedes` accept anything at both ends on purpose: `approves` starts at a
human actor, which has no id form at all, and supersession is genuinely open — a contract
supersedes a contract, an ADR an ADR, and sometimes a decision supersedes the thing it was
made about.

**Why only one direction is stored.** Two hand-maintained directions are two things that can
disagree, and disagreement is exactly what traceability exists to prevent. The inverse is
computed at load time and never written to disk. The passive forms the design document uses
in places — `implemented-by`, `executed-by`, `satisfies` — are not storable.

**Cycles are an error** on `contains`, `refines`, `depends-on` and `supersedes`
(`TRC-004`).

**Stores merge into one graph.** `traceability.stores` lists three by default: the
hand-maintained `.specify/traceability/traceability.yaml`, per-feature
`specs/*/traceability/matrix.yaml`, and the machine-owned
`.specify/traceability/derived.yaml`. Every one is canonical for its own scope, and a
duplicate `(from, relation, to)` triple across stores is an error (`TRC-001`).

**`derived.yaml` is machine-owned.** `derive_edges.py --write` rewrites it in full. A file
rewritten wholesale has no room for a hand edit to survive in, which is the point: it keeps a
rule from competing with a human copy of the same edge.

### 4.5 The traceability perimeter

Backward coverage asks whether every source file is reachable from a requirement. Applied to
a whole repository that would demand an edge for every util, config and generated file — so
the *perimeter* scopes it:

```yaml
traceability:
  perimeter:
    include: ["src/**", "services/**", "apps/**"]
    exclude: ["**/*.generated.*", "**/node_modules/**", "**/*.test.*", …]
```

Two things about it that bite in practice.

**Keep the test exclusions in step with `testing.stem_suffixes`.** A test file that a
derivation rule recognises but the perimeter does not is counted twice over: it derives a
`tests` edge *and* reports as an untraced source file. Backward coverage then falls every time
someone adds a test.

**`AGENTS.md`, `index.md` and `SKILL.md` are always outside the perimeter**, and are not
listed in the exclude block. They are hard-coded in `openup_model.py` as `GOVERNANCE_FILES`,
because list-valued config **replaces rather than merges** — a project carrying its own
exclude list would otherwise start failing backward coverage the moment it adopted the context
hierarchy that another part of the design asks for. A check that punishes you for following
the design is a defect, so this one is not configurable.

---

## 5. Provenance: the part that makes the rest mean anything

### The problem

If the agent writing the code also writes the proof that the code was traced, the audited and
the auditor are one process, and the audit proves nothing. A project can report 100% coverage
where every edge is an unverified claim.

So every edge declares **how it is known**:

| Value | Meaning | Worth |
|---|---|---|
| `derived` | Recomputed from the filesystem by a named rule | Machine-checkable — *once the rule reproduces it* |
| `asserted` | Claimed by an agent or author | A claim |
| `approved` | Asserted, then signed off by a named human | Governance-grade — *while the signature still matches* |

Both of the strong labels have a way of being faked, and both are now checked.

### `derived` has to survive being re-run

The schema can only require `derived_by` to be *present*, never to be *true*. So relabelling
an assertion `derived` used to be free — and it moved the very ratio the audit reports. An
agent grading its own traceability had a one-word bypass.

`TRC-010` re-executes the rule an edge names and fails the edge when it does not come back.

| Rule | Produces | Status |
|---|---|---|
| `gherkin-tag-scan` | `SCEN-*` → `executes` → `AC-*`, from `@` tags in `.feature` files | implemented |
| `test-file-naming-convention` | test artifact → `tests` → the file its `source` is named after | implemented |
| `wbs-iteration-field` | WBS node → `belongs-to` → iteration, from the node's own field | implemented |
| `openapi-operation-scan` | source file → `conforms-to` → `CONTRACT-*` | **not implemented** |
| `evidence-manifest-scan` | `EVID-*` → `evidences` → WBS node / risk / gate | **not implemented** |

An edge naming one of the last two cannot be reproduced by anything, so it is counted as
`derived_unverified` — reported, never trusted, and never scored as evidence at a gate. Do not
add more of them. If a rule is not implemented, the honest label is `asserted`.

The rules are intentionally conservative. `test-file-naming-convention` requires the subject
file to match on stem *and* extension and to be unique inside the perimeter; two candidates
derive nothing and the reason is printed. `gherkin-tag-scan` requires exactly one
`@SCEN-<DOMAIN>-nnnn` tag per scenario rather than inferring an id from the file name. A guess
recorded as `derived` would be worse than no edge at all.

Regenerate, never hand-write:

```bash
python3 .specify/extensions/openup/scripts/python/derive_edges.py --write
```

Real output from the fixture, in report mode:

```
derive-edges: PASS
==================
  [SKIP] DRV-004  2 of 5 declared rules are not implemented; edges naming them cannot be reproduced
           - evidence-manifest-scan: EVID-* --evidences--> WBS node / risk / gate
           - openapi-operation-scan: source file --conforms-to--> CONTRACT-*

  rules_implemented: 3
  rules_declared: 5
  derivable_edges: 10
  missing_from_graph: 0
  by_rule: {'gherkin-tag-scan': 2, 'test-file-naming-convention': 1, 'wbs-iteration-field': 7}
```

### `approved` has to still match what was approved

The same defect sat one level up. `approved_endpoints_hash` was required by the schema and
read by nothing, so `approved` was a string anyone could type — and the release gate counted
it as evidence. On this fixture, relabelling the eleven `asserted` edges `approved` moved the
verifiable share from 38% to 81% without changing a single fact.

`TRC-013` recomputes that hash from the endpoints as they now stand:

```
SHA256( fingerprint(from) ␀ relation ␀ fingerprint(to) )
```

Two decisions inside that are worth knowing before you rely on it.

**`status`, `approvals` and `baseline` are excluded from the fingerprint.** An approval is
about *what* was approved, not where the artifact sits in the state machine. Advancing
`APPROVED → BASELINED` must not void a signature; editing the requirement's title or owner
must.

**A source path fingerprints as the path, not the file's bytes.** An approved edge to a file
records *which file was approved for this role*. Source churn is continuous and expected, and
hashing content would void every approval on every commit until nobody used approvals at all.
Whether the file is still *correct* is what tests and `TRC-010` derivation are for. These two
behaviours are indistinguishable from outside, which is why it is stated here and in
`ID-GRAMMAR.md`.

The relation is inside the hash deliberately, so re-pointing an approved edge at a different
relation voids the signature rather than inheriting it.

### Recording an approval

Nobody can compute that hash by hand, so there is a tool. Shipping the check without it would
have recreated the defect it closes — a required field nobody can write correctly.

```bash
python3 .specify/extensions/openup/scripts/python/approve_edge.py \
  --from REQ-AUTH-0014 --relation refines --to BUS-OBJ-0017 \
  --by product-owner --note "Scope confirmed at the Elaboration review"
```

It edits the store in place, one list item at a time, so the comments and ordering of a
hand-maintained file survive. Optional `--at` sets the timestamp; `--commit <sha>` records the
commit the approval was made in.

It refuses three things, each with a reason:

| Refusal | Why |
|---|---|
| An edge in `derived.yaml` | The store is rewritten wholesale, so the signature would be erased on the next regeneration — and it adds nothing a rule already proves |
| An edge with `provenance: derived` | Replacing reproducible evidence with a signature is strictly weaker |
| An edge with an endpoint that does not resolve | A signature on nothing |

**The honest limit.** This binds an approval to content. It does **not** prove a human was
involved — an agent can run the command and pass `--by product-owner` exactly as a person can.
The only real anchor available is `--commit` pointing at a signed commit, and verifying that
against git is not implemented. Read `approved` as *"someone took accountability under this
name"*, never as *"a human checked this"*.

### What the numbers actually say

```bash
python3 .specify/extensions/openup/scripts/python/validate_trace.py --json \
  | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)['metrics'], indent=2))"
```

Real output from the fixture:

```json
{
  "edges": 27,
  "requirements": 2,
  "forward_coverage": 1.0,
  "verification_coverage": 1.0,
  "backward_coverage": 1.0,
  "perimeter_files": 2,
  "orphans": 0,
  "provenance_mix": { "derived": 13, "asserted": 14, "approved": 0 },
  "asserted_share": 0.5185,
  "derived_verified": 10,
  "derived_unverified": 3,
  "approved_verified": 0,
  "approved_stale": 0,
  "acceptance_criteria": 2,
  "scenario_coverage": 1.0,
  "code_test_coverage": 0.5
}
```

Read it in this order:

1. **`derived_verified` + `approved_verified`** — 10 of 27, so **37% of this graph is
   independently verifiable**. That is the only figure a third party could check without
   taking anyone's word for it, and it is what the release gate scores.
2. **`derived_unverified`** — 3 edges naming a rule nobody implemented. These *look* like
   evidence in a coverage report and are not. On a healthy graph this number should not grow.
3. **`approved_stale`** — approvals given for content that has since changed. Not a crisis; a
   prompt to re-approve deliberately.
4. **`asserted_share`** — useful context, but the one number that can be moved by relabelling
   rather than by work. Do not manage to it.
5. **Coverage** last. `forward_coverage: 1.0` on a graph that is 52% asserted means every
   requirement has *a claim* attached, which is worth less than it reads.

On an empty graph the whole check short-circuits and reports only `{"edges": 0}` rather than
computing coverage over nothing.

---

## 6. Check reference

69 named checks across eleven validators, plus `GATE-000`. Every one is listed here with what
it checks, why it exists, and what to do when it fires.

Severity is not uniform, and where it varies it is deliberate. The governing principle:
**a missing thing warns; a misleading thing fails.** An absent context map is a gap in
ergonomics. A context map pointing at a deleted requirement sends an agent looking for
something that is not there — and an agent willing to infer will fill the hole itself, which
is the exact failure the whole model exists to prevent.

### `validate_wbs.py` — 12 checks

| Id | Sev | Checks | Why, and what to do |
|---|---|---|---|
| `WBS-000` | FAIL | `wbs.yaml` conforms to `wbs.schema.json` (or no WBS exists at all) | Field-level shape. Fix the reported path |
| `WBS-001` | FAIL | Declared `level` equals the id's segment count | The id encodes its position, so the two can never silently disagree. **The id is the truth — fix the `level` field** |
| `WBS-002` | FAIL | `parent` is the id minus its last segment, and exists; L1 declares none | A node with a hand-chosen parent is a second, disagreeing tree |
| `WBS-003` | FAIL | Exactly one L1 root | Two roots is two programs in one file |
| `WBS-004` | FAIL | Every leaf is L7, terminates with a `terminal_reason` (`semantic`), and is never at L1–L3 | Levels 1–3 are pure structure; a leaf there means the plan is empty, not concise |
| `WBS-005` | FAIL | Every id in `requirements` is a registered artifact | An unresolvable requirement is an invitation to invent one |
| `WBS-006` | FAIL | Every id in `risks` is a registered risk | " |
| `WBS-007` | FAIL | Every id in `acceptance` is a registered artifact | " |
| `WBS-008` | FAIL | Every `dependencies` target exists | |
| `WBS-009` | FAIL | The dependency graph is acyclic | A dependency cycle is work that can never start |
| `WBS-010` | FAIL | A node's `iteration` letter matches its `phase` | `ITER-E-02` on a `CONSTRUCTION` node means one of the two is wrong |
| `WBS-011` | **WARN** | No parent exceeds `max_children_warn` (default 25) | Usually a missing intermediate level, but sometimes correct — hence a warning |

Metrics: `levels` (a count per level), `total_nodes`, `leaves`, `early_terminations`,
`depth_policy`.

### `validate_risk.py` — 8 checks

| Id | Sev | Checks | Why, and what to do |
|---|---|---|---|
| `RISK-000` | FAIL / **WARN** | Conforms to `risk.schema.json`. **WARN** if there is no register at all | A project with no register has risk-driven planning switched off, which is a choice, not a violation |
| `RISK-001` | FAIL | `exposure` equals `probability × impact` within 1e-9 | A hand-edited exposure is how a register silently drifts. Delete the field or fix the factors |
| `RISK-002` | FAIL | `residual_exposure` equals `residual_probability × residual_impact` | " |
| `RISK-003` | FAIL | Residual exposure is strictly below current, unless `accepted` | A "mitigation" that moved no number is a no-op wearing the label of work |
| `RISK-004` | FAIL | Every open risk at or above the threshold has ≥1 **existing** mitigation WBS node | A mitigation nobody scheduled is a wish. Blocks the Elaboration gate |
| `RISK-005` | FAIL | Every open risk at or above the threshold has ≥1 verification reference | Mitigation you cannot check is an assertion |
| `RISK-006` | FAIL | Each mitigation node has `kind: risk-mitigation` **and** lists the risk back | An edge that agrees from one end only is not a link |
| `RISK-007` | FAIL | A `mitigated`/`closed` risk has evidence, on the risk or on its mitigation nodes | Closing a risk on a claim is the thing a register exists to prevent |

Which band `RISK-004`/`RISK-005` apply from is set by `require_mitigation_at_or_above` and
`require_verification_at_or_above` (`high` or `critical`).

Metrics: `total`, `open`, `open_critical`, `open_high`, `unmitigated_high`,
`mitigation_coverage`, `evidence_coverage`, and both thresholds. The two coverage ratios are
over *open* risks only — a closed or accepted risk with no mitigation is a decision, not a gap.
Booleans tell you whether you are compliant now; ratios tell you whether you are getting
better.

### `validate_trace.py` — 14 checks

| Id | Sev | Checks | Why, and what to do |
|---|---|---|---|
| `TRC-000` | FAIL | Every store, **as written**, conforms to `traceability.schema.json` | Validates the parsed documents, not a reconstruction of them. Every store is reported at once, so one fix-validate cycle does not become five |
| `TRC-001` | FAIL | No duplicate `(from, relation, to)` across merged stores | Two copies of an edge are two things that can diverge |
| `TRC-002` | FAIL | Both endpoints resolve (unless `status: broken`) | A dangling id or a deleted file. This is the check that catches a rename |
| `TRC-003` | FAIL | The relation is legal for its endpoint types | `implements` from a Risk to a Contract fails rather than landing quietly |
| `TRC-004` | FAIL | No cycles on `contains`, `refines`, `depends-on`, `supersedes` | |
| `TRC-005` | FAIL | Requirement→implementation coverage meets `coverage_thresholds.forward` | A requirement nothing implements is intent nobody acted on |
| `TRC-006` | FAIL | Requirement→verification coverage meets the same threshold | A requirement nothing verifies is a hope |
| `TRC-007` | FAIL | Backward coverage over the perimeter meets `coverage_thresholds.backward` | Reachability is **undirected** and capped at 6 hops — a file is traced if it is *connected* to intent, whichever way the arrows point |
| `TRC-008` | FAIL | No orphans, in six categories (below) | |
| `TRC-009` | FAIL | Edges touching a `BASELINED`+ **requirement** meet `baseline_min_provenance` | Scoped to requirements on purpose: a verified test case does not need an approved edge to exist. `derived` edges are exempt — reproducible evidence outranks a signature |
| `TRC-010` | FAIL | Every `derived` edge is reproduced by the rule it names | **Never fixable by relabelling.** Either the claim is wrong or the filesystem is. Edges naming an unimplemented rule are counted, not failed |
| `TRC-011` | FAIL | Every edge an implemented rule produces is present in some store | The one check here with a mechanical fix: `derive_edges.py --write` |
| `TRC-012` | FAIL / SKIP | Every acceptance criterion has ≥1 scenario executing it. **SKIP** if `require_scenario_per_ac: false` | A criterion nobody wrote a scenario for has not been specified, only asserted |
| `TRC-013` | **WARN** | Every `approved` edge still matches its `approved_endpoints_hash` | Warns rather than fails, and demotes the edge out of `approved_verified`. A stale hash after a legitimate edit is a normal event, and failing the whole validator would make people avoid `approved` entirely — which is how the feature dies a second time |

`TRC-008` orphan categories:

| Category | Condition |
|---|---|
| Orphan requirement | No edges at all, in either direction |
| Orphan WBS node | A non-structural leaf with no `requirements` and no outgoing edges |
| Orphan risk | No mitigation, not `closed`/`accepted`, **and** at or above the high threshold — accepting a low-exposure risk without work is legitimate |
| Orphan scenario | Executes no acceptance criterion |
| Orphan test | Neither verifies a requirement nor tests a file — the commonest way a suite grows without the coverage figure moving |
| Orphan contract | Nothing conforms to it or validates it — a published interface no code claims to honour |

### `validate_done.py` — 6 checks

This is the mirror of `select_work.py`, and exists because of an asymmetry: work was blocked
from *starting* on evidence while nothing stopped it being called *finished* on a claim. Of
the two, the claim a gate depends on is the second.

It only inspects nodes with `status: done` and a non-`structural` kind.

| Id | Sev | A task is done when… |
|---|---|---|
| `DOD-001` | FAIL | Evidence is recorded, and every evidence reference resolves |
| `DOD-002` | FAIL | Every linked requirement is both implemented and verified in the graph |
| `DOD-003` | FAIL | Every linked acceptance criterion has a scenario executing it |
| `DOD-004` | FAIL | A `risk-mitigation` task has reduced its risk, with evidence on the risk |
| `DOD-005` | FAIL | No edge touching the node is marked `broken` |
| `DOD-006` | FAIL | A `test` task names acceptance criteria, and each one is registered |

Metrics: `done_claimed`, `done_verified`, `incomplete[]`. The audit prints the first two
separately on purpose — printing one number would repeat the claim it is meant to check.

Two of the design document's Definition-of-Done clauses are **deliberately absent**: contract
tests and Microcks conformance have nothing behind them. A check that cannot fail is worse
than a missing one, because it reports compliance it never established.

### `validate_context.py` — 4 checks

| Id | Sev | Checks | Why |
|---|---|---|---|
| `CTX-001` | **WARN** | Every governed directory has an `index.md` | A missing map is a gap in ergonomics, and a project adopting SpecUP should not fail its first audit over absent documentation |
| `CTX-002` | **FAIL** | Every id-shaped token in every `index.md` resolves | A map pointing at a deleted requirement does not merely fail to help — it misleads the agent reading it |
| `CTX-003` | **WARN** | An `AGENTS.md` is reachable at or above every governed directory | As `CTX-001` |
| `CTX-004` | **FAIL** | Every skill a WBS node names exists at `skills/<name>/SKILL.md` | Naming guidance that is not there sends an agent looking for it, and one willing to infer will invent it |

`CTX-002` deliberately uses a loose pattern: anything that *looks* like a governed id in a
context map is something a reader will try to follow, so it is something that must resolve.
`GATE-*` and `TRACE-*` are exempt, being referenced in prose rather than registered.

Two consequences worth knowing before you write a context map.

**A check id is id-shaped.** `WBS-004` and `RISK-005` match the pattern for a WBS node and a
risk, resolve to nothing, and are reported. That is the check working, not a false positive —
it cannot tell a citation from a reference. Name those checks in prose inside an `index.md`.
`TRC-`, `DOC-`, `CTX-` and `APV-` share no prefix with an artifact type and are safe.

**A nested governed tree is skipped.** A directory with its own `.specify/` is a project root,
so its context maps describe a different graph and this run never loads it. Without that,
every repository shipping an example or a test fixture would report that tree's ids as
dangling — which is how SpecUP found it, on itself, with 28 violations from `examples/` and
`tests/fixtures/`. Skipping is a statement about scope: the nested tree is not validated here,
and needs its own run.

### `validate_approvals.py` — 6 checks

specup.md §59 reserves a class of decision for a named human. Until 0.1.2 nothing checked that
one had been involved: an agent could run `approve_edge.py --by product-owner` exactly as a
person could. These checks are what make that sentence mechanical.

An approval carries a provenance level, mirroring the one an edge carries:

| Level | Meaning |
|---|---|
| `witnessed` | `approval.commit` resolves **and** carries a signature that verifies against `approvals.allowed_signers` |
| `claimed` | a name and a date, and nothing tying them to a person |

| Id | Sev | Checks | Why, and what to do |
|---|---|---|---|
| `APV-000` | FAIL | `.specify/governance/approval-matrix.md` names at least one approver | Every other check is weaker without it. With the "who" column blank, anyone can approve anything and the matrix is decorative. **Fill in the column** |
| `APV-001` | FAIL | A declared `approval.commit` resolves to a real commit here | A sha that is not in this repository is a citation to nothing |
| `APV-002` | FAIL | That commit's signature verifies against the project's allowed signers | The trust root decides, not the presence of a signature — otherwise anyone who can commit can approve. A missing `allowed-signers` file fails here too, rather than passing silently |
| `APV-003` | FAIL | `approval.by` is a name the matrix records | An approval under a name nobody agreed to is not an approval |
| `APV-004` | **WARN** | Every approval declares a commit | A migration, not a defect: `commit` is optional in the schema and existing approvals predate the check. The warning makes the gap visible from day one |
| `APV-005` | FAIL | Every approval at or above `approvals.require_witness_at_or_above` is witnessed | The ratchet. `null` by default, so an upgrading project is told without being broken. Set it to `BASELINED` once your approvals carry commits, and **raise it as a decision — never lower it to make a run go green** |

Metrics: `approvals`, `witnessed`, `claimed`, `named_approvers[]`, `witness_floor`.

**Three places an approval is written, and all three are in scope.**

| Where | Key | Shape |
|---|---|---|
| An artifact | `approvals` | a list |
| A traceability edge | `approval` | one object, written by `approve_edge.py` |
| A risk | `acceptance_approval` | one object; required when `status` is `accepted` |

The risk shape was missed until 0.1.2's own self-governance accepted a risk. Accepting a live
risk is the §59 decision most likely to be taken quietly, the risk schema requires the approval
to be there, and every `APV-*` check looked straight past it. `APV-001` to `APV-004` now apply
to it. `APV-005` does not: its floor names governance states (`BASELINED` and its successors),
and `accepted` is a risk status, so a floor set for requirement baselines cannot quietly start
failing risk acceptances as well.

**A missing `git` binary is exit 2, not a FAIL.** So is a project that declares a commit while
sitting outside a git repository. Reporting either as a governance failure would send someone
looking for a defect in their data rather than in their environment.

The audit prints witnessed-versus-claimed next to the edge provenance mix, deliberately not
folded into it. The two "approved" numbers count different things: an edge is `approved` when
someone signed off on content that still matches, and an approval is `witnessed` when git can
verify a person made it. A project can be 100% approved and 0% witnessed.

### `validate_docs.py` — 7 checks

The last step of progressive disclosure. §56–57 argues an agent should navigate `directory →
AGENTS.md → index.md → the one artifact` rather than load the repository, and
`validate_context.py` checks that hierarchy down to the file. This checks the step below it,
inside the file: when an agent opens one function, its docstring is the whole context it gets
and nothing else will arrive. Four properties, none of them stylistic — **anchored**,
**bounded**, **honest**, **finite**.

| Id | Sev | Checks | Why, and what to do |
|---|---|---|---|
| `DOC-000` | PASS / SKIP | What was analysed, and what was not | Scope, reported rather than assumed. **SKIP whenever any perimeter file went unread** |
| `DOC-001` | **WARN\*** | Every exported symbol has a docstring | Opening it otherwise gives an agent the name and nothing else |
| `DOC-002` | **FAIL** | Every governing id a docstring names resolves | `CTX-002` one level down. A docstring naming a superseded requirement does not merely fail to help: it tells an agent the unit is governed by something, and the agent will not find it and will decide for itself |
| `DOC-003` | **WARN\*** | Each analysed file anchors to a `REQ-`, `NON-FR-`, `ADR-` or `SECURE-` id | Nothing the unit claims can be compared with what the project decided. **Per file, not per symbol** — the graph's unit of implementation is the source path, and demanding an id on every method teaches people to paste one everywhere |
| `DOC-004` | **WARN\*** | The docstring states a boundary — what the unit will not do, or when it refuses | The half that gets omitted, and the half that matters. An agent not told the edge will infer one |
| `DOC-005` | **FAIL** | A docstring claiming a cross-check names **two distinct sources** | The `cits-crypto` failure, generalised: a truth table was transcribed from a reading of a rule rather than from the page, and the predicate written to cross-check it came from the same misreading. They agreed, and both were wrong |
| `DOC-006` | **WARN** | The docstring fits `docs.max_docstring_lines` (default 40) | A docstring carrying an argument is an ADR in disguise. Move it and link the ADR, which `DOC-003` then anchors to |

Metrics: `perimeter_files`, `python_files`, `files_not_analysed`, `exported_symbols`,
`documented`, `anchored_files`, `enforced[]`.

**\* The ratchet.** The three starred checks warn by default and fail once listed in
`docs.enforce`, for the same reason `approvals.require_witness_at_or_above` is `null`: an
existing codebase has public symbols nobody documented against a requirement that did not exist
when they were written, and failing its first audit over them teaches only that this validator
should be switched off. The warnings are visible from day one; promoting a check is the
deliberate act that makes it consequential.

```yaml
docs:
  enforce: [DOC-001, DOC-003]    # these now FAIL; the rest warn
  max_docstring_lines: 40
```

`DOC-002` and `DOC-005` are **not listable and cannot be lowered** — the governing principle
puts them there, a missing thing warns and a misleading thing fails. `DOC-006` is refused
outright and the validator exits 2 saying why: failing on docstring length makes deleting the
reasoning the cheapest way to go green, and the reasoning is the part worth keeping. An id
`docs.enforce` does not recognise is also exit 2, because a control that is off while its
config says it is on is worse than one nobody configured.

**Python only, via `ast`.** There is no parser here for any other language. A perimeter file
this validator cannot read is counted by `DOC-000` as not analysed, never as passing — the
same honesty the `contracts:` block owes about what nothing globs. The audit prints "analysed"
and "in the perimeter" as two numbers for exactly this reason: a TypeScript project would
otherwise read a green docs line as a statement about code nothing opened.

`DOC-005` counts **names, not independence**. Two ids in one docstring may still be two
readings of one page, which is how the `cits-crypto` truth table went wrong. What the check
buys is that a claim of corroboration has to say what corroborated what; whether those two
things are genuinely independent is a human judgement, and an ADR is where it gets recorded.

### `select_work.py` — 3 checks and 9 readiness rules

| Id | Sev | Meaning |
|---|---|---|
| `SEL-000` | FAIL | No iteration is open — set `lifecycle.iteration`, or run `/speckit.openup.iteration open` |
| `SEL-001` | PASS / **WARN** | Whether anything in the iteration is ready |
| `SEL-002` | PASS / **WARN** | Whether anything is blocked, with the reason per task |

Candidates are non-`structural` nodes in the current iteration whose status is `planned` or
`ready`. Each is tested against the **Definition of Ready**, and every blocker is tagged with
the rule that produced it, so a refusal traces back to a published rule:

| Rule | A task is ready when… |
|---|---|
| `DOR-001` | Linked to at least one requirement |
| `DOR-002` | Has a named owner |
| `DOR-003` | Assigned to an iteration |
| `DOR-004` | Executable: an L7 task, or a higher leaf that declares a `terminal_reason` |
| `DOR-005` | Every declared dependency exists and is done |
| `DOR-006` | A `test` task names the acceptance criteria it covers |
| `DOR-007` | A `risk-mitigation` task names the risk it reduces |
| `DOR-008` | Every linked requirement is registered and past `DRAFT` |
| `DOR-009` | Every capability contract it names exists (`skills/<name>/SKILL.md`) |

The ready set is ordered **risk first** — highest mitigated exposure, then fewest
dependencies, then id for stability — so an iteration attacks uncertainty before convenience.

Real output from the fixture, where every task is already `done`:

```
select-work: PASS
=================
  [WARN] SEL-001  no task in ITER-E-02 is ready to execute
           - no non-structural task is assigned to ITER-E-02

  iteration: ITER-E-02
  ready: []
  blocked: []
```

`--ids-only` prints a bare JSON array and nothing else, because a workflow `fan-out` passes
stdout through `from_json` and needs a list rather than an object.

### `derive_edges.py` — 4 checks

| Id | Sev | Meaning |
|---|---|---|
| `DRV-001` | FAIL | Every derivable edge is present in the graph. Fix with `--write` |
| `DRV-002` | **WARN** | An edge a rule reproduces is recorded as `asserted` or `approved` — free coverage left on the floor. Understating evidence is the safe direction, so it warns |
| `DRV-003` | **WARN** | Inputs a rule scanned but could not use, with the reason for each |
| `DRV-004` | SKIP | How many declared rules are not implemented |

`DRV-003` is the most useful one in practice. It is where you learn that a scenario has two
`@SCEN-` tags, or that a test file's subject name is ambiguous inside the perimeter, or that a
registered test artifact's `source` does not exist.

### `render_views.py` — 2 checks

| Id | Sev | Meaning |
|---|---|---|
| `VIEW-001` | FAIL | Every generated view exists and matches what the sources would produce right now |
| `VIEW-002` | **WARN** | A file carrying the generated banner that no renderer owns — a stale view from an earlier layout, or a hand-written document in a generated place. Warns, because deleting someone's document is not this script's call |

The seven generated documents:

| Document | Generated from |
|---|---|
| `.specify/wbs/wbs.md` | `wbs.yaml` |
| `.specify/risks/risk-register.md` | `risk-register.yaml` |
| `.specify/traceability/traceability.md` | the relation stores |
| `.specify/traceability/coverage.md` | `validate_trace.py` — coverage **and** the provenance mix |
| `.specify/governance/definition-of-ready.md` | `select_work.py`'s rule table |
| `.specify/governance/definition-of-done.md` | `validate_done.py`'s rule table |
| `.specify/governance/quality-gates.md` | `openup-config.yml` + `evaluate_gate.py`'s descriptions |

**No view carries a timestamp.** A `generated_at` line would make every file differ from the
one on disk on every run, which would turn `VIEW-001` into noise and train people to ignore
it.

### `init_openup.py` — 3 checks

`INIT-001` lists what was created; `INIT-002` lists what was left untouched. Both always pass;
they are a report, not a gate.

`INIT-003` reports whether the generated views were rendered, and is the one that can carry a
non-PASS status. It exists because of the failure mode it covers: `render_views` exits 2 at
import time when PyYAML is absent, which would kill this process before the verdict was
written, so `--json` would exit 2 with empty stdout and a workflow step consuming the verdict
would read malformed output instead of a check. Converting that to an `INIT-003` ERROR keeps
the exit code and gives the caller something to parse.

### `evaluate_gate.py` — `GATE-000` plus one check per condition

`GATE-000` fires only when the gate name is not in config, and lists the configured gates.
Otherwise each condition becomes a check named after itself. See [§7](#7-gates).

---

## 7. Gates

Four milestone gates. **23 condition declarations over 22 implementations** (`wbs_valid`
appears in two gates), all declared in `openup-config.yml` and implemented in
`evaluate_gate.py`.

```bash
python3 .specify/extensions/openup/scripts/python/evaluate_gate.py \
  --gate GATE-LIFECYCLE_ARCHITECTURE --json
```

### Two rules the implementation holds to

**Absence of evidence is not evidence.** A missing test report, review record or architecture
baseline *fails* its condition. A gate that passed because a file was never written would be
worse than no gate at all.

**Conditions fail closed.** A condition declared in config with no implementation fails, and
says so. A condition that raises an exception fails, naming the exception. Neither is ever
skipped — a check that silently disappears is the one you will never notice is gone.

### `GATE-LIFECYCLE_OBJECTIVES` — Inception

*Is the scope, ownership and initial risk picture real?*

| Condition | Passes when |
|---|---|
| `vision_present` | A vision document exists at `.specify/lifecycle/vision.md` |
| `stakeholders_identified` | A stakeholder document exists, naming who approves what |
| `initial_risks_registered` | The risk register is not empty |
| `wbs_levels_1_to_3_valid` | L1, L2 and L3 nodes exist and `WBS-001..003` pass |
| `requirements_have_owners` | Every registered requirement names an owner, and there is at least one requirement |

### `GATE-LIFECYCLE_ARCHITECTURE` — Elaboration

*Is the architecture baselined and are the high risks handled?*

| Condition | Passes when |
|---|---|
| `architecture_baselined` | An architecture document exists **and** every registered ADR is `APPROVED` or beyond |
| `all_high_risks_have_mitigation` | `RISK-004` **and** `RISK-005` pass |
| `requirements_traceable` | `TRC-005` **and** `TRC-006` pass |
| `critical_contracts_defined` | ≥1 `CONTRACT-*` is registered and its declared `source` file exists. **The OpenAPI/AsyncAPI document itself is never parsed** |
| `security_review_complete` | `.specify/evidence/security-review.json` exists and its `status` is `passed` |
| `wbs_valid` | `validate_wbs.py` reports no FAIL |

### `GATE-INITIAL_OPERATIONAL_CAPABILITY` — Construction

*Is it built, covered, free of orphans, and actually done?*

| Condition | Passes when |
|---|---|
| `wbs_valid` | `validate_wbs.py` reports no FAIL |
| `forward_coverage_met` | `TRC-005` passes |
| `backward_coverage_met` | `TRC-007` passes |
| `acceptance_scenarios_passing` | `.specify/evidence/acceptance-results.json` exists, has ≥1 scenario and zero failures |
| `definition_of_done_met` | Every node claiming `done` survives `validate_done.py` |
| `no_open_critical_risks` | No risk at or above `critical_exposure_threshold` is still open |
| `no_orphans` | `TRC-008` passes |

### `GATE-PRODUCT_RELEASE` — Transition

*Can it be released and operated?*

| Condition | Passes when |
|---|---|
| `all_gates_passed` | Every non-`TRANSITION` gate in config passes (evaluated once, not recursively) |
| `release_evidence_complete` | All four of `release-readiness.md`, `deployment-plan.md`, `operations.md`, `acceptance-report.md` exist |
| `no_open_high_risks` | No risk at or above the high threshold is still open |
| `traceability_final` | `validate_trace.py` reports no FAIL **and** ≥50% of edges are independently verifiable |
| `security_validation_passed` | `.specify/evidence/security-validation.json` exists, passed, with zero critical findings |

### `traceability_final` deserves its own paragraph

It is the only condition that scores *evidence quality* rather than presence, and it is
computed as:

```
(derived_verified + approved_verified) / edges  ≥  0.50
```

Not the `asserted` share, and not `provenance_mix["approved"]`. Both of those can be moved by
typing a different word. `derived_verified` counts only edges a rule actually reproduced this
run; `approved_verified` counts only signatures that still match their endpoints. A graph
cannot buy its way past this condition by renaming its own claims at either level.

### A real gate result

```
Gate GATE-LIFECYCLE_ARCHITECTURE
  [PASS] architecture_baselined  1 ADR(s), 0 not yet approved
  [PASS] all_high_risks_have_mitigation  high-exposure risks are mitigated and verifiable
  [PASS] requirements_traceable  every requirement is implemented and verified
  [PASS] critical_contracts_defined  1 contract(s) registered
  [PASS] security_review_complete  security review status: passed
  [PASS] wbs_valid  WBS validation PASS
  Status: PASS
```

Note that *every* condition is reported, not only the failures. A gate report listing only
problems hides what was actually checked — and what was checked is half of what a reader needs.

### `audit.py` puts it together

`audit.py` runs all five validators plus the gate matching your current `lifecycle.phase`, and
fails on the conditions listed under `audit.fail_on`. Real output from the fixture:

```
OPENUP AI ENGINEERING AUDIT
===========================

Lifecycle
  Phase:        ELABORATION
  Iteration:    ITER-E-02
  Gate:         GATE-LIFECYCLE_ARCHITECTURE

WBS
  L1: 1
  L2: 1
  L3: 1
  L4: 1
  L5: 1
  L6: 1
  L7: 3
  Leaves: 3  (early terminations: 0)
  Policy: semantic
  Status: PASS

Requirements
  Total:        2
  Implemented:  100%
  Verified:     100%
  Status: PASS

Risks
  Total:         2
  Open critical: 0
  Open high:     1
  Unmitigated:   0
  Status: PASS

Traceability
  Edges:             27
  Forward coverage:  100%
  Backward coverage: 100%
  Orphans:           0
  Status: PASS

Definition of Done
  Claimed done:  3
  Verified done: 3
  Status: PASS

Evidence quality
  derived:     10  (37%)  reproduced by a rule
  unverified:   3  (11%)  claims a rule that is not implemented
  asserted:    14  (52%)  agent claim only
  approved:     0  (0%)  signed off, and still matching what was signed
  stale:        0  (0%)  approved for content that has since changed

Context hierarchy
  index.md files:  8 over 7 governed directory(s)
  Skills:          architecture, gherkin, requirements, risk, traceability, wbs
  Dangling refs:   0
  Status: PASS

Gate GATE-LIFECYCLE_ARCHITECTURE
  [PASS] architecture_baselined  1 ADR(s), 0 not yet approved
  ...
  Status: PASS

FINAL GATE: PASS
```

**Read the Evidence quality block, not the coverage block.** This project reports 100%
coverage everywhere and is 52% unverified claims. Both statements are true, and the second one
is the one that tells you what the first is worth. The provenance mix is always printed and is
deliberately **not** configurable — a flag to suppress it would be a switch for turning off
the honesty.

---

## 8. Running a phase workflow

```bash
specify workflow run openup-inception    --input idea="..." --input program="My Product"
specify workflow run openup-elaboration  --input focus="Vehicle authentication"
specify workflow run openup-construction --input iteration_goal="Certificate validation"
specify workflow run openup-transition   --input release="v1.0.0"
```

Each takes an optional `--input integration=` (default `auto`, which uses whatever the project
was initialised with).

| Workflow | Shape |
|---|---|
| `openup-inception` | scaffold → `speckit.constitution` → `speckit.specify` → **scope gate** → WBS skeleton → initial risks → trace → gate |
| `openup-elaboration` | open iteration → `speckit.plan` → ADRs and risks → contracts → behaviour → decompose → trace → five validator shell steps → repair branch → gate → **architect approval gate** |
| `openup-construction` | open iteration → `speckit.tasks` → `select_work --ids-only` → **scope gate** → **fan-out over ready work** → derive → verify → retrace → reassess risk → check done → render → gate → close iteration |
| `openup-transition` | final audit → close gaps → release artifacts → final trace → gate → **release approval gate** → record |

Construction is **one iteration per run**. Run it again for the next one. A single pass that
implements everything is precisely the "one large AI code-generation exercise" the iterative
model exists to prevent.

### The block every workflow ends with

```yaml
- id: evaluate-gate
  type: shell
  run: "python3 .specify/extensions/openup/scripts/python/evaluate_gate.py --gate <GATE> --json --out <evidence path>"
  continue_on_error: true          # so the branches below are reachable

- id: halt-if-unevaluable          # exit 2 -> setup fault, halt hard
  type: if
  condition: "{{ steps.evaluate-gate.output.exit_code == 2 }}"
  then:
    - id: cannot-evaluate
      type: shell
      run: "echo '... setup fault, not a governance failure ...' >&2; exit 2"

- id: enforce-gate                 # exit 1 -> governance failure, human decides
  type: if
  condition: "{{ steps.evaluate-gate.output.exit_code == 1 }}"
  then:
    - id: gate-failed
      type: gate
      options: [reject, override]
      on_reject: abort

    - id: record-override
      type: shell
      run: "... --out .specify/evidence/overrides/{{ context.run_id }}.json"
```

**`continue_on_error: true` looks like a weakening and is the opposite.** A non-zero shell step
halts the whole run by default — which enforces, but makes the human branch unreachable and
leaves the operator with no verdict to read. Recording the exit code and branching on it
explicitly keeps the failure consequential *and* legible.

An `override` is a legitimate, logged human act, not a bypass. It writes the failing verdict to
`.specify/evidence/overrides/<run_id>.json`, because an undocumented override is
indistinguishable from a gate that never ran. Two overrides in a row on the same condition
means the condition is wrong or the work is — decide which.

### One security rule these files obey

**No `{{ inputs.* }}` value appears inside any `run:` field, in any workflow.** Shell steps
interpolate expressions as raw text with no quoting or escaping, so a user-supplied value would
be parsed as shell syntax. User input reaches commands through `input.args`, which is the
sanctioned path; shell steps use only fixed strings and engine-controlled values such as
`{{ context.run_id }}`.

If you write your own workflow, keep to this. It is the difference between a prompt and a
command injection.

### Verified behaviour

Run against spec-kit 1.0.6 with the real engine:

| Graph state | Result |
|---|---|
| Healthy | `Status: completed` — runs to the final step |
| High-exposure risk stripped of its mitigation | `Status: paused` at `[gate-failed]` — **final step never reached** |
| `wbs.yaml` corrupted so the graph cannot load | `Status: failed`, `exited with code 2` |

---

## 9. The nine agent commands

All three-segment, because Spec Kit requires extension commands to match
`^speckit\.[a-z0-9-]+\.[a-z0-9-]+$`. Each is backed by a script you can run yourself.

| Command | What it does | Behind it |
|---|---|---|
| `/speckit.openup.init` | Scaffolds the tree, then walks you through the perimeter and risk threshold | `init_openup.py` |
| `/speckit.openup.phase` | Reports the lifecycle position, or advances it | `evaluate_gate.py`, `audit.py` |
| `/speckit.openup.iteration` | `open` / `review` / `close` an iteration | `validate_risk.py`, `audit.py` |
| `/speckit.openup.wbs` | Builds or extends the seven-level WBS | `validate_wbs.py`, `render_views.py` |
| `/speckit.openup.risk` | Records and updates risks, binding high ones to mitigation work | `validate_risk.py` |
| `/speckit.openup.trace` | Derives what is derivable, asserts the rest, reports coverage | `derive_edges.py`, `validate_trace.py` |
| `/speckit.openup.behavior` | Writes Gherkin bound by tag to acceptance criteria | `derive_edges.py` |
| `/speckit.openup.gate` | Evaluates a named gate and reports every condition | `evaluate_gate.py` |
| `/speckit.openup.audit` | The aggregate compliance report | `audit.py` |

The preset additionally wraps Spec Kit's own `/speckit.tasks` (generate tasks from the WBS in
the governed contract form) and `/speckit.implement` (resolve the governance chain *before*
writing code), and appends addenda to the constitution, spec, plan and tasks templates.

### `/speckit.openup.phase` — advancing is the consequential half

The rule that matters: you leave a phase by satisfying **its own** exit gate, not the gate of
the phase you are entering.

| Phase | Question | Exit gate |
|---|---|---|
| Inception | Should we build this? | `GATE-LIFECYCLE_OBJECTIVES` |
| Elaboration | Can we build it? | `GATE-LIFECYCLE_ARCHITECTURE` |
| Construction | Can we build it incrementally and verify each increment? | `GATE-INITIAL_OPERATIONAL_CAPABILITY` |
| Transition | Can it be released and operated safely? | `GATE-PRODUCT_RELEASE` |

A passing gate is a *precondition for asking*, not a substitute for the answer — a phase
transition is a human approval boundary. Moving backwards is allowed and needs no gate: it is
an admission that the previous milestone was not really met, and should be said plainly.

### What these commands are instructed not to do

`/speckit.openup.gate` carries the strictest list, because it is the command an agent is most
tempted to route around. All of the following are prohibited, and each defeats the gate rather
than passing it:

- **Do not declare a gate passed.** Report what the script returned. "Architecture looks good"
  is precisely the assertion a machine-checkable gate exists to replace.
- **Do not edit `openup-config.yml` to remove a failing condition** or lower a threshold. If a
  threshold is genuinely wrong, say so and let the user decide, as a separate visible change.
- **Do not write evidence files to satisfy a condition.** `security-review.json` means a
  security review happened. Creating it because a gate wants it is fabricating a record.
- **Do not mark artifacts `APPROVED` or `BASELINED` to clear a condition.** Approval is a human
  act.

The same discipline runs through the others: never hand-write a `derived` edge or an
`approved` hash, never edit a generated view, never edit `derived.yaml`, never invent a
requirement, a risk or an acceptance criterion, and never mark work `done` without evidence —
`validate_done.py` computes that, and disagreeing with it in prose does not change it.

The root `AGENTS.md` states these as repository rules, and the scoped `.specify/AGENTS.md` and
`src/AGENTS.md` narrow them. `AGENTS.md` answers *what rules must I obey*; `skills/*/SKILL.md`
answers *how do I perform this activity*. Merged, you get a document followed for neither.

---

## 10. Changing a baselined artifact

Below `BASELINED`, edit freely — that is what `DRAFT` and `REVIEW` are for. At `BASELINED` and
beyond, a change is a change-control event rather than an edit.

### 1. Compute the impact first

Never assess impact from memory or by reading around the code. Ask the graph:

```bash
python3 .specify/extensions/openup/scripts/python/impact.py --of REQ-AUTH-0014
```

Real output from the fixture, abbreviated:

```
Impact of changing REQ-AUTH-0014
================================

Business objectives (1)
  BUS-OBJ-0017  Enable authenticated vehicle communication
      1 hop(s), via REQ-AUTH-0014 →refines

Acceptance criteria (2)
  AC-AUTH-0014-0003  Invalid certificates must be rejected
      1 hop(s), via REQ-AUTH-0014 ←verifies
  AC-AUTH-0014-0004  Authentication p95 latency stays within budget
      3 hop(s), via NON-FR-AUTH-0017 ←verifies

WBS nodes (7)
  WBS-1.2.3.4.1.1.1  Define certificate contract
      1 hop(s), via REQ-AUTH-0014 ←implements
  ...

Risks (1)
  RISK-0007  Certificate validation latency
      2 hop(s), via WBS-1.2.3.4.1.1.2 →mitigates

Source files (2)
  src/auth/authentication_service.ts
      1 hop(s), via REQ-AUTH-0014 ←implements
  src/security/certificate_validator.ts
      1 hop(s), via REQ-AUTH-0014 ←implements

  23 artifact(s) reached within 6 hops.
  Traversal is undirected: impact does not follow the arrows.
```

Traversal is undirected and capped at 6 hops, because impact does not follow the arrows — a
requirement's blast radius includes both what refines it and what implements it. The same
command answers the reverse question from a file:

```bash
python3 .specify/extensions/openup/scripts/python/impact.py --of src/auth/authentication_service.ts
```

`impact.py` is a **report, not a gate**. It always exits 0 when the graph loads. A validator
that refused a change because it had consequences would refuse every change worth making.

**If the fan-out looks implausibly small, the missing edges are the finding.** An impact set
the graph cannot see is an impact set nobody will remember.

### 2. Record the change

Per `.specify/governance/change-control.md`:

| Field | |
|---|---|
| What changes | the artifact id, and what about it |
| Why | new information, defect, scope change, external requirement |
| Impact set | the `impact.py` output |
| Risk | new or changed `RISK-*` entries |
| Approval | who, per `approval-matrix.md` |

### 3. Expect the approvals to withdraw themselves

Editing the artifact voids the signatures on edges touching it. `TRC-013` recomputes the hash,
warns, and moves the edge out of `approved_verified` — the count the release gate scores.

That is the mechanism working, not a problem to route around. Re-approve deliberately:

```bash
python3 .specify/extensions/openup/scripts/python/approve_edge.py \
  --from REQ-AUTH-0014 --relation refines --to BUS-OBJ-0017 --by product-owner
```

### 4. Re-baseline, then re-gate

Increment `baseline.version` and collect a fresh approval. Do not delete the previous version
— use `supersedes` so the history stays in the graph. The change is absorbed when the gate that
covered the artifact passes again:

```bash
python3 .specify/extensions/openup/scripts/python/audit.py --json
```

### What this does not do

There is no commit-trailer validation and no pre-commit hook, so **nothing forces a change
through this process**. It is a procedure you follow, backed by checks that will notice
afterwards if you did not.

---

## 11. Configuration reference

`.specify/extensions/openup/openup-config.yml`. Machine-local overrides go in
`openup-config.local.yml`, which is gitignored. Layering is
defaults < `openup-config.yml` < `openup-config.local.yml`, merged deeply.

**List-valued keys replace rather than merge.** If you write your own
`perimeter.exclude`, you replace the shipped list entirely — you do not add to it. This is
the reason `GOVERNANCE_FILES` is hard-coded rather than being a config default.

Every setting below is read by something. Nothing in this file is decorative.

### `lifecycle`

| Key | Default | Read by |
|---|---|---|
| `phase` | `INCEPTION` | `audit.py` (chooses which gate to run), `select_work.py` |
| `iteration` | `null` | `select_work.py` — `SEL-000` fails without it |

### `wbs`

| Key | Default | Read by | Change it when |
|---|---|---|---|
| `depth_policy` | `semantic` | `WBS-004` | You want `strict` — every leaf must be L7, no exceptions |
| `never_terminal_above` | `3` | `WBS-004` | Almost never. L1–L3 are pure structure |
| `max_children_warn` | `25` | `WBS-011` | Your tree is legitimately wide |
| `store` | `.specify/wbs/wbs.yaml` | The loader | You relocate the WBS |

### `risk`

| Key | Default | Read by | Change it when |
|---|---|---|---|
| `high_exposure_threshold` | `0.40` | `RISK-004/005`, `TRC-008`, `no_open_high_risks` | Your appetite genuinely differs — as a recorded decision |
| `critical_exposure_threshold` | `0.65` | `no_open_critical_risks` | " |
| `require_mitigation_at_or_above` | `high` | `RISK-004` | You only want `critical` risks to block |
| `require_verification_at_or_above` | `high` | `RISK-005` | " |
| `require_residual_reduction` | `true` | `RISK-003` | Essentially never |
| `store` | `.specify/risks/risk-register.yaml` | The loader | |

### `artifacts`

| Key | Default | Notes |
|---|---|---|
| `stores[]` | `.specify/traceability/requirements.yaml`, `specs/*/artifacts.yaml` | Per-feature registries merge into the same graph. An artifact defined in one feature is visible to all — the graph is one graph |

### `traceability`

| Key | Default | Read by | Change it when |
|---|---|---|---|
| `stores[]` | the three above | The loader | You add per-feature matrices |
| `perimeter.include[]` | `src/**`, `services/**`, `apps/**` | `TRC-007`, `TRC-008`, derivation rules | **First thing to set in an existing repo** |
| `perimeter.exclude[]` | generated, snapshots, node_modules, test-file patterns | " | Keep in step with `testing.stem_*` |
| `coverage_thresholds.forward` | `1.00` | `TRC-005`, `TRC-006` | Rarely — an unimplemented requirement is a real gap |
| `coverage_thresholds.backward` | `0.95` | `TRC-007` | Brownfield adoption, **with a written ratchet and target date** |
| `baseline_min_provenance` | `approved` | `TRC-009` | You are not using approvals yet — set `asserted` deliberately |

### `gherkin`

| Key | Default | Read by |
|---|---|---|
| `features_glob` | `specs/*/acceptance/**/*.feature` | `gherkin-tag-scan` |
| `require_ac_tag` | `true` | `gherkin-tag-scan` (produces a `DRV-003` note) |
| `require_requirement_tag` | `true` | " |
| `require_scenario_per_ac` | `true` | `TRC-012` — set `false` and it reports SKIP |

### `testing`

| Key | Default | Read by |
|---|---|---|
| `stem_suffixes[]` | `.test` `.spec` `_test` `_spec` `-test` `Test` | `test-file-naming-convention` |
| `stem_prefixes[]` | `test_` `test-` | " |

The rule strips one marker from the file stem, then looks for that stem with the **same
extension** inside the perimeter. Zero or several matches derive nothing and say why, because
a guess here would be an asserted edge wearing a derived label.

### `contracts`

| Key | Default | Read by |
|---|---|---|
| `openapi_glob` | `specs/*/contracts/*.openapi.{yaml,yml,json}` | **Nothing** |
| `asyncapi_glob` | `specs/*/contracts/*.asyncapi.{yaml,yml,json}` | **Nothing** |
| `microcks.enabled` | `false` | **Nothing** |

This block is declared so the shape is settled. No code globs these and no code parses an
OpenAPI or AsyncAPI document. Do not read it as "contracts are validated".

### `gates`

A map of gate id → `{phase, conditions[]}`. Adding a condition name with no implementation in
`evaluate_gate.py` makes the gate fail with an explanatory message — never skip.

### `audit`

| Key | Default | Notes |
|---|---|---|
| `fail_on[]` | `broken_references`, `orphan_requirements`, `orphan_wbs_nodes`, `unmitigated_high_risk`, `coverage_below_threshold` | Each maps to a specific check (`TRC-002`, `TRC-008` ×2, `RISK-004`, `TRC-005`) |

The provenance mix is always emitted and is deliberately **not** configurable.

### The one habit that matters

> **Lower a threshold only as a decision, never to make a run go green.**

If you find yourself editing this file to make a workflow pass, stop — that is the exact
failure this project exists to prevent, and it is invisible six months later. The one
legitimate case is brownfield adoption, and it is legitimate only with the ratchet written
next to it:

```yaml
  coverage_thresholds:
    backward: 0.30    # ADOPTION: +0.10 per quarter; target 0.95 by 2027-06-30
```

---

## 12. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Every validator exits `2` | `PyYAML` / `jsonschema` / `referencing` missing | `pip install -r .specify/extensions/openup/requirements.txt` |
| A workflow halts immediately at exit `2` | The graph will not load — malformed YAML, or a duplicated id | Run the validator directly; the error names the file |
| `duplicate artifact/risk/WBS node <id>` at exit `2` | Two entries share an id — often two features reaching for the same number | Renumber one. Never reuse a retired id; the domain tag exists to keep teams out of each other's number space |
| `<kind> with no id ('<title>')` at exit `2` | A typo'd `id:` key | Fix the key. The entry was being dropped from the graph entirely |
| `WBS-000` fails with schema errors | A field is misspelled, missing, or of the wrong type | The error path points at the node and key |
| `WBS-001` fails | `level` disagrees with the id's segment count | **The id is the truth** — fix the `level` field |
| `WBS-002` fails | `parent` is hand-chosen rather than the id minus its last segment | Fix `parent`, or renumber the node |
| `WBS-004` fails on an L4–L6 leaf | The branch stops early with no explanation | Add a `terminal_reason`, or decompose to L7 |
| `WBS-004` fails on an L1–L3 leaf | The plan is empty at that branch | Decompose it. No `terminal_reason` will help |
| `WBS-010` fails | An `ITER-E-*` node declares `phase: CONSTRUCTION` (or similar) | One of the two is wrong; decide which |
| `RISK-001` fails | `exposure` was hand-edited | Delete the field or fix `probability`/`impact` |
| `RISK-003` fails | Residual exposure is not below current | Either the mitigation did nothing, or the reassessment was optimistic |
| `RISK-004` fails | A high risk points at prose, or at a node that does not exist | Create the `kind: risk-mitigation` WBS node and schedule it |
| `RISK-006` fails | The risk names the node but the node does not name the risk back | Add the `risks:` entry, and `kind: risk-mitigation` |
| `TRC-002` fails after a refactor | A file was renamed or deleted; its path was the identity | Update the edge, or mark it `status: broken` if the loss is real |
| `TRC-003` fails | The relation is not legal between those types | Check the domain/range table — usually the wrong relation, not the wrong endpoints |
| `TRC-007` fails for files that should not be governed | The perimeter is too wide | Narrow `perimeter.include`; never invent edges to silence it |
| Hundreds of orphans on a first audit | Perimeter is the whole repo | Narrow to one module and repeat |
| `TRC-010` fails | An edge claims a rule that does not reproduce it | **Fix the claim, not the label.** Usually the edge should be `asserted` |
| `TRC-011` fails | The derived store is behind the filesystem | `derive_edges.py --write` |
| `TRC-012` fails | An acceptance criterion has no scenario | Write the scenario, or set `require_scenario_per_ac: false` **with a target date beside it** |
| `TRC-013` warns | An approved edge's endpoints were edited | Re-approve with `approve_edge.py`, deliberately |
| `VIEW-001` fails | A generated document is missing or stale | `render_views.py --write` |
| `VIEW-002` warns | A `.md` carrying the generated banner that no renderer owns | A leftover from an older layout — delete it, or move it out of the generated directory |
| `SEL-000` fails | No iteration is open | Set `lifecycle.iteration`, or `/speckit.openup.iteration open` |
| `SEL-001` warns with an empty ready set | Everything is blocked, or nothing is assigned | Read `SEL-002` — each blocker names its `DOR-*` rule |
| `DOR-008` blocks a task | Its requirement is still `DRAFT` | Agree the requirement, then promote it. Do not implement a `DRAFT` |
| `DOR-009` / `CTX-004` fail | A WBS node names a skill that does not exist | Write `skills/<name>/SKILL.md`, or remove the reference |
| `CTX-002` fails | An `index.md` names an id that resolves to nothing | Update the map. A misleading map is worse than none |
| `DOD-001` fails | A node is `done` with no evidence | Record the evidence, or the node is not done |
| `DOD-004` fails | A mitigation is done but the risk was never reassessed | Update `residual_probability`/`residual_impact` from what the evidence showed |
| A condition is "declared but not implemented" | Config names a condition `evaluate_gate.py` does not define | Implement it, or remove it from config. It fails closed by design |
| `security_review_complete` fails with nothing to see | Absence of evidence is not evidence — the record is missing | Do the review, then record it |
| `traceability_final` fails on a clean graph | Fewer than 50% of edges are independently verifiable | Land derived edges and real approvals. Relabelling will not move it |
| The audit is ~100% `asserted` | The graph was generated rather than recovered | Treat it as unverified; re-derive what is derivable |

---

## 13. What SpecUP does not do

Being direct about this is part of the design. A tool that overstates its coverage is the
thing it was built to prevent.

- **Nothing validates a contract document.** `critical_contracts_defined` asserts that a
  registered `CONTRACT-*` artifact's declared `source` file *exists*. It never opens it.
  `contracts.openapi_glob`, `asyncapi_glob` and `microcks.enabled` are read by no code.
  `MICROCKS-TEST-*` ids and the `validates` relation are reserved in the grammar so nothing has
  to be renamed later. If you need API conformance today, that is a gap to fill yourself, not a
  feature to configure.
- **Gherkin binds but does not run.** `.feature` files are parsed, tags are read, and
  `executes` edges are derived. `acceptance_scenarios_passing` reads
  `.specify/evidence/acceptance-results.json` and trusts whatever produced it. Wire your own
  runner to write that file.
- **Two of five derivation rules are unimplemented.** `openapi-operation-scan` and
  `evidence-manifest-scan` are declared and reported as `derived_unverified`, never counted as
  evidence.
- **An approval binds content, not a human.** See [§5](#5-provenance-the-part-that-makes-the-rest-mean-anything).
  The only real anchor is a signed commit, and verifying one is not implemented.
- **The three binding standards are checked by people, not by code.** `language-rules.md`,
  `coding-rules.md` and `security-practices.md` bind an agent through the root `AGENTS.md` and
  Principle VIII of the constitution, and no validator reads a sentence or a source file.
  Useful parts of all three are mechanically decidable — sentence length, the non-approved
  word table, `application/problem+json` on every failure response, the RFC 9457 member set —
  and a checker over that subset is the obvious next increment. Until it exists, a green audit
  says nothing about conformance to any of them.
- **No CI enforcement.** The validators are CI-ready by construction — JSON out, exit codes —
  but no pipeline is authored.
- **No commit-trailer validation and no pre-commit hook.** Nothing forces a change through
  change control.
- **`python3` in shell steps.** Windows hosts normally have `python`; adjust the `run:` lines
  or provide a shim.
- **Governance overhead is unmeasured**, and it is the thing most likely to sink the approach.
  Track it from your first Construction iteration. If governed work is slower than ungoverned
  work without a corresponding drop in defects or audit effort, cut scope — reduce the
  perimeter, raise the depth policy, drop conditions — rather than continuing out of
  commitment.

### And when not to use it at all

**Do not use SpecUP for** prototypes and spikes you intend to throw away; small teams shipping
low-consequence software where code review is already sufficient; or projects where nobody will
own the risk register. An unmaintained register is worse than none — it looks like risk
management and is a stale snapshot.

**It earns its cost when** the work is audited, regulated or safety-relevant and you must
*demonstrate* traceability; AI agents write a meaningful share of the code and you need
provenance stronger than a chat log; or the project is long-lived enough that "why does this
exist?" is a question someone will actually ask about code nobody remembers writing.

---

## 14. Where to go next

| | |
|---|---|
| [The guide](README.md) | Concepts and architecture — why SpecUP is shaped this way |
| [New project](new-project.md) | Greenfield adoption, governed from the first commit |
| [Existing project](existing-project.md) | Brownfield adoption, where intent has to be recovered |
| [`ID-GRAMMAR.md`](../../extensions/openup/schemas/ID-GRAMMAR.md) | Normative identifiers, relations, provenance, governance states |
| [`workflows/README.md`](../../workflows/README.md) | The enforcement pattern in detail |
| [`presets/openup-governance/README.md`](../../presets/openup-governance/README.md) | The wrap and append contracts |
| [Publishing runbook](../runbooks/publishing-to-spec-kit.md) | Cutting a release |
| [`specup.md`](../../specup.md) | The original design document — the source of intent, not of fact |
