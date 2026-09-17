# SpecUP v0.1.2 — implementation plan

## Context

SpecUP 0.1.1 enforces an OpenUP lifecycle over an agent it does not own. Its central claim is
that governance is only real when it is machine-checkable and consequential. Two of its own
claims do not meet that bar:

- **`README.md:548-553`** — *"An approval binds content, not a human... an agent can run
  `approve_edge.py --by product-owner` exactly as a human can. The only real anchor is
  `approval.commit` pointing at a signed commit, verified against git, **which is not
  implemented**."* So "final authority rests with explicit human approval" is prose.
- The three binding standards and every template are prompt-level. Nothing checks that a
  docstring carries the context an agent needs to act correctly on a unit of code.

v0.1.2 closes both, ships the templates that teach the model, and makes SpecUP govern itself.
It **adds no runtime dependency**, so it is releasable independently of the Open SWE work.

*Amended 2026-09-17.* This originally read *"MIT throughout, adds no runtime dependency, and
touches no bundle or workflow"*. Two thirds of that is now wrong: a **workstream 0** was added
ahead of §6 relicensing SpecUP from MIT to **BUSL-1.1**, which rewrites the `license:` field in
the bundle manifest and all four workflow manifests. The surviving claim — no new runtime
dependency — is the one the "releasable independently" conclusion actually rested on, so the
conclusion holds. See [`docs/dev/licensing.md`](../../docs/dev/licensing.md).

**The Open SWE runtime moves to 0.1.3.** Its research is complete and recorded in §7 below so
it is not re-derived. Splitting was a deliberate call: the broker and container are the two
items that could invalidate a release, and nine independently useful workstreams should not
wait behind them.

### Two decisions taken during planning

1. **The permission artifact is a *grant*, not a *capability*.** "Capability" is already taken:
   `SKILL.md` files are *capability contracts* (`specup.md:494`, `README.md:442`,
   `DOR-009`). A permissions file called `capability-profile` would sit beside six shipped
   capability contracts meaning procedures. 0.1.3 uses `resolve_grant.py` →
   `.specify/evidence/grants/<run-id>.json`.
2. **Approvals get a signature, and therefore a provenance level** — mirroring the
   `derived`/`asserted`/`approved` model the project already applies to edges.

---

## Scope

| # | Workstream | Closes |
|---|---|---|
| 1 | `validate_approvals.py` — `APV-001..004`, signed-commit verification | `README.md:548-553` |
| 2 | `validate_docs.py` — `DOC-001..005`, the docstring contract | new |
| 3 | Meta-cognitive rewrite of the shipped templates, with the `cits-crypto` harvest | new |
| 4 | `examples/` generic program + project, materialised into `workspace/` | new |
| 5 | SpecUP governs itself | `.specify/` holds only caches today |
| 6 | Documentation sweep + release mechanics | four live drifts |
| 0 | **Relicense MIT → BUSL-1.1** *(added 2026-09-17, ahead of 6)* | monetising the `open-swe` agent stack |

---

## 1. `validate_approvals.py` — make human approval mechanical

**The model.** An approval acquires a provenance level, exactly as an edge has one:

| Level | Meaning |
|---|---|
| `witnessed` | `approval.commit` resolves **and** carries a signature that verifies against the project's allowed signers |
| `claimed` | a name and a date, and nothing that ties them to a person |

The trust root is a version-controlled project artifact: **`.specify/governance/allowed-signers`**
(the `gpg.ssh.allowedSignersFile` format). Reviewable, diffable, and a governance change when
it changes — the same property that makes `extensions/openup/` trustworthy per
`docs/dev/taskfile.md:139-151`.

**Checks.** Follow the `Id | Sev | Checks | Why, and what to do` table form of
`docs/guide/using-specup.md:979-997`.

| Id | Sev | Checks |
|---|---|---|
| `APV-000` | FAIL | The approvals in scope parse; git is a repository *(a missing git binary is exit 2, not FAIL — a setup fault)* |
| `APV-001` | FAIL | A declared `approval.commit` resolves to a real commit (`git cat-file -e`) |
| `APV-002` | FAIL | That commit's signature verifies (`git verify-commit --raw`) against `allowed-signers` |
| `APV-003` | FAIL | `approval.by` resolves to a named human in `.specify/governance/approval-matrix.md` |
| `APV-004` | **WARN** | An approval with no `commit` is `claimed`, not `witnessed` |

`APV-004` warns rather than fails **because it is a data migration, not a defect** — existing
approvals predate the field. It ratchets via a new config key, which is the documented habit at
`using-specup.md:1714-1726` ("Lower a threshold only as a decision, never to make a run go
green"):

```yaml
approvals:
  require_witness_at_or_above: BASELINED   # default; null disables
  allowed_signers: .specify/governance/allowed-signers
```

`APV-003` is the check that forces `approval-matrix.md` to be filled in. It ships with a blank
"who" column today and says so itself: *"If nobody is named here, anyone can override anything
and the gate is decorative"* (`extensions/openup/templates/approval-matrix-template.md:67`).

**Files**

- new `extensions/openup/scripts/python/validate_approvals.py`
- **`extensions/openup/extension.yml`** — declare the script, or
  `tests/test_extension_manifest.py:139` fails on set-equality (`on_disk == declared`)
- `extensions/openup/openup-config.yml` — the `approvals:` block
- new `extensions/openup/templates/allowed-signers-template` + declare it (`:148` same rule)
- `evaluate_gate.py` — a `human_approvals_witnessed` condition on
  `GATE-LIFECYCLE_ARCHITECTURE` and `GATE-PRODUCT_RELEASE`

**Reuse.** `base_parser()`, `Verdict`, `run()`, `emit()`, `write_out()` from
`openup_model.py:144,72,153,136,123`. `graph.artifacts` for `approvals[]`, and the edge stores
for edge approvals. Note `_record` is copy-pasted in four validators
(`validate_wbs.py:168`, `validate_risk.py:175`, `validate_trace.py:308`,
`validate_context.py:115`) — **promote it into `openup_model.py` and update the four**, rather
than adding a fifth copy.

**Honesty constraint.** `README.md:548-553` must be rewritten, not deleted. The new statement:
a *witnessed* approval is a human act, bounded by the trust root; a *claimed* one is still only
a name. Overstating this would be the exact defect the bullet exists to prevent.

---

## 2. `validate_docs.py` — the docstring contract

> *"All internal and external API docstrings must be descriptive and focused enough to form its
> current working context only."*

The code-level form of progressive disclosure (`specup.md` §56-57): a docstring is the
**complete working context for the unit it documents, and nothing more**.

| Id | Sev | Checks | Why |
|---|---|---|---|
| `DOC-001` | FAIL | Every exported symbol in the perimeter has a docstring | Undocumented is unusable at bounded context |
| `DOC-002` | FAIL | It names a governing artifact — a `REQ-`, `NON-FR-` or `ADR-` id that resolves | An unanchored docstring cannot be checked against intent |
| `DOC-003` | FAIL | It states something the unit must **not** do, or when it refuses | The boundary is the half that gets omitted, and the half that matters |
| `DOC-004` | FAIL | A docstring claiming a cross-check names **two distinct sources** | The `cits-crypto` failure, generalised — see §3 |
| `DOC-005` | **WARN** | Bounded length (~40 lines) | A docstring carrying an argument is an ADR in disguise; link the ADR |

`DOC-005` warns because `using-specup.md:973-977` sets the principle — *"a missing thing warns;
a misleading thing fails"* — and a long docstring is neither. It is a smell, and a hard failure
would push people to delete reasoning rather than move it.

**Scope, stated plainly.** Python only, via `ast`. Non-Python perimeter files are counted and
reported `SKIP`, never passed. This follows the `contracts:` precedent at
`using-specup.md:1690-1699`, whose "Read by" column literally says `Nothing` and then says so.

**Reuse.** `graph.perimeter_files()` (`openup_model.py:573`) and `graph.exists()` (`:533`) for
`DOC-002` resolution — note the artifact registry is **never schema-validated** (verified:
`schema_errors()` is called with only `wbs`, `risk`, `traceability`), so `graph.exists()` is the
resolution primitive, not a schema hook.

**Files.** New script + `extension.yml` declaration + a `docs:` config block + `audit.py`
(`:28-34`, `:74-75`, `:80-81`, and `render()` all hard-code five section keys).

---

## 3. Meta-cognitive templates, and the `cits-crypto` harvest

Every shipped template gains a five-part frame:

```markdown
<!-- WHAT QUESTION THIS ANSWERS — and what it does not. A template that does not draw
     its own boundary gets filled with whatever the author had nearby. -->
<!-- HOW YOU CAN TELL THIS IS WRONG — the failure mode, named specifically. -->
<!-- WHAT CHECKS IT — the check id, and what it does and does not verify. If nothing
     checks it, say so. -->
<!-- WORKED EXAMPLE — a real excerpt from the cits-crypto project, reasoning intact. -->
<!-- WHERE AUTHORITY SITS — who decides this is done. Past DRAFT, a named human. -->
```

"How you can tell this is wrong" has to be written from experience. That is what the worked
example is for.

| What happened in `cits-crypto` | Where it lands |
|---|---|
| The SSP truth table was transcribed from a *reading of the rule* rather than the page, and the predicate written to cross-check it came from the same misreading. **They agreed, and both were wrong.** | ADR template gains the *independent-oracle* pattern; `DOC-004` checks it |
| `NOT_EVALUATED` as a third verdict, never rounded | Preset guidance; already SpecUP's own exit contract |
| Every value carried document + edition + clause via a custom `cites:` key | `cites:` documented as a convention — **not** a schema change; the registry is unvalidated, so a convention is all a schema edit would buy |
| Closing a risk failed: the schema wanted a mitigation node that did not exist yet; status became `mitigating` | Risk template documents the honest intermediate state |
| ADR-0001 decided a normative conflict and **RISK-0010 stayed open** | ADR template: mandatory *Revisit when*; deciding ≠ closing |
| Twice a value was reconstructed from memory instead of re-read, and was wrong both times | `AGENTS.md` template rule: **re-read before asserting** |
| A human caught a scope error no validator could have | §1 |

**Files.** Edit the existing templates under `extensions/openup/templates/` — editing avoids the
set-equality manifest test entirely. Four phrases are test-locked by
`tests/test_preset.py:246-256` and must survive: *"do not lower a threshold"*, *"absence of
evidence is not evidence"*, *"stop and report"*, *"generated does not mean approved"*.

---

## 4. `examples/` — the generic program and project

`workspace/` is committed as an **empty folder** (`143346d`) and its contents are ignored, so the
example cannot live there. It ships tracked in `examples/` and is *materialised into*
`workspace/`:

```
examples/my-program/     the GOVERNANCE — "My Program". WBS-1 is a program.
examples/my-project/     the APPLICATION — what gets built.
```

Self-describing throughout: every file states what it is for, what would make it wrong, and what
checks it. It **passes `GATE-LIFECYCLE_OBJECTIVES` and fails `GATE-LIFECYCLE_ARCHITECTURE` on
the same five conditions a real project fails at that point** — a template that shipped green
would teach that the gates are decorative.

`cits-crypto` stays as the worked example the templates cite. It is not a template: it is a real
project with a real normative corpus, and that difference is the point.

---

## 5. SpecUP governs itself

`.specify/` holds three cache directories and nothing else. For a release claiming "production
grade", that is the first thing a reviewer checks.

Follow `docs/guide/existing-project.md` as written — it is the brownfield journey, and this is
its first real execution. Its Phase 6 rule, *"turn on enforcement, last"*, is the ordering
constraint.

Expect discomfort. Backward coverage over `extensions/`, `tools/` and `tests/` will fail at
first. The honest response is to **record the real figure**, per
`existing-project.md:10-13`: *"An existing project that reports 100% coverage on day one has not
been governed; it has been decorated."*

This also produces the first real number for `README.md:566-569` — governance overhead,
currently unmeasured. One project is not a measurement, and the release should say so.

---

## 6. Documentation sweep and release mechanics

**Four live drifts, all verified this session:**

| Drift | Truth |
|---|---|
| Test counts: `README.md:451` "248", `:484` "189 passed, 8 skipped", `:492` "197 passed", `docs/dev/taskfile.md:34-35` | **273 passed / 8 skipped** without spec-kit; **281 passed** with it |
| `INIT-003` documented at `using-specup.md:293` but absent from the §6 check reference (`:1167-1170` says "2 checks") | three |
| Check count: `using-specup.md:970` "55 named checks" vs `release-notes-0.1.0.md:60` "62" | reconcile, then extend for `DOC-*`/`APV-*` |
| ~~`docs/runbooks/release-plan-0.1.2.md` describes the **unsplit** release~~ | **Closed.** Filename kept so links resolve; a header records the split and the §8 table carries a *Landed* column per item. The §2–§5 design is still the live 0.1.3 plan, so it was annotated rather than duplicated into a new file. |

**Release mechanics** (`docs/runbooks/publishing-to-spec-kit.md`):

- `docs/runbooks/release-notes-0.1.2.md` is a **hard requirement** — `gh release create
  --notes-file` consumes it. Follow the 0.1.1 form: what did *not* change, then Upgrading, then
  a per-component version table.
- Bump `extensions/openup/extension.yml:6` (still `0.1.1` — the only version string outside git
  tags), `bundles/specup/bundle.yml`, `presets/openup-governance/preset.yml`.
- `task release:check` → `task release:catalog`. `tests/test_catalog.py:150` rebuilds every
  component and compares digests, so content drift under an unchanged version fails.
- ~~Workflows are untouched, so they rebuild to identical digests — state that, as 0.1.1 did.~~
  **No longer true, and this is the one release-mechanics consequence of the relicence.** All
  four `workflow.yml` manifests carry a `license:` field, so all four changed and all four now
  rebuild to different digests. `tests/test_catalog.py` already fails on exactly that. **The
  four workflows must be version-bumped off `0.1.0` at release**, which 0.1.1 did not have to
  do, and the release notes state a digest change rather than the "identical" line 0.1.1 used.
- **Do not route anything through `task`** — `tests/test_taskfile_boundary.py` forbids a
  workflow, command or manifest reaching the task runner.

---

## 7. Carried forward to 0.1.3 — research already done

Recorded so it is not re-derived. Every item verified this session.

**Licensing.** `deepagents` 0.7.14 MIT · `langchain-core` 1.6.3 MIT · `langgraph` 1.2.11 MIT ·
**`langgraph-api` 0.14.1 Elastic-2.0** · Open SWE itself **MIT**. SpecUP can adopt Open SWE
provided graphs run **in-process** and it never depends on `langgraph-api`. *(Amended
2026-09-17: this said "and stay MIT". SpecUP is BUSL-1.1 from 0.1.2, which changes nothing
here — Open SWE's MIT imposes no obligation on an incorporating work beyond keeping the
notice, and being source-available yourself grants no rights to Elastic's software. The
in-process rule stands, now to keep SpecUP's own customers out of a second vendor's
agreement.)*
`deepagents` needs Python **≥3.11**; SpecUP declares `>=3.10` at `bundle.yml:26` and
`extension.yml:23`.

**Amended 2026-09-17 — the ELv2 problem has an Apache-2.0 answer, and 0.1.3 adopts it.**
[Aegra](https://github.com/aegra/aegra) (`aegra.dev`) is an **Apache-2.0** Agent Protocol
server on FastAPI + PostgreSQL, calling itself a drop-in replacement for LangSmith Deployments
— same LangGraph SDK, same APIs, self-hosted. Its `libs/aegra-api/pyproject.toml` was read:
depends on `langgraph>=1.0.3`, `langgraph-sdk>=0.3.5`, `langgraph-checkpoint-postgres>=2.0.23`,
and **none of `langgraph-api` / `langgraph-runtime` / `langgraph-cli`**. So the durable
execution, task queue and resumable runs the Agent Server was wanted for are available without
the Elastic licence, and the "in-process only" constraint stops being a limitation and becomes
one deployment mode of two.

Three consequences, none of them licensing:

1. **`requires-python` becomes `>=3.12`, not `>=3.11`.** Aegra's floor is higher than
   `deepagents`'. The bundle declares the highest floor, so the line above is superseded.
2. **PostgreSQL and Redis become runtime dependencies.** This is the item that needs an ADR
   before any code: `NON-FR-CORE-0001` is filesystem authority, and a checkpoint database is a
   second state store that is not diffable, not reviewable and not in git. The defensible split
   is agent-execution state in Postgres, governance state on the filesystem, always — but it
   must be decided rather than absorbed.
3. **Apache-2.0 under BUSL-1.1 is fine and needs a `NOTICE` file.** Permissive, no copyleft,
   attribution and patent-grant terms propagate. Note it is *not* eligible as this project's
   BUSL Change License — covenant 1 requires GPL-2.0 compatibility — which is a different
   question from depending on it.

**Maturity is the open risk.** Aegra publishes no production-readiness or stability statement,
and "Agent Protocol v2 streaming" is flagged as new. Adopting it makes SpecUP's agent runtime
depend on a young project, which is a trade against depending on a licensed one. Record it as
a risk when 0.1.3 acquires requirements; it has none today, and a risk with no requirement to
threaten is a note, not an entry.

**Open SWE is Python**, with three documented extension points — `get_agent()` in
`agent/server.py` is the single assembly point:

| Point | Mechanism | Use |
|---|---|---|
| Middleware | `awrap_tool_call` hook, appended in `get_agent()` | the grant broker |
| Sandbox backend | implement `SandboxBackendProtocol`; register in `agent/sandboxes/providers/registry.py` | the container |
| Prompts | `AGENTS.md` at repo root is already read into the system prompt | the disclosure entry point |

**The finding that shapes enforcement.** Per the deepagents docs, *"the only method a provider
must implement is `execute()`"* — `read`, `write`, `edit`, `ls`, `glob`, `grep` are all built on
it by `BaseSandbox`. **Every file and shell operation funnels through one method.** That splits
the tool inventory:

- **Container enforces** (routes through `execute()`): `read_file`, `write_file`, `edit_file`,
  `ls`, `glob`, `execute`
- **Broker brokers** (does not): `http_request`, `fetch_url`, `web_search`,
  `commit_and_open_pr`, `request_pr_review`, `task`

`agent/sandboxes/providers/` has `daytona/e2b/langsmith/local/modal/runloop` and **no
`docker.py`** — so a SpecUP docker backend is genuinely additive and plausibly upstreamable.

**Four constraints 0.1.3 inherits:**

1. **`specup.md` has *nothing* on execution.** Verified keyword counts over 3,382 lines:
   `docker` 0, `container` 0, `sandbox` 0, `isolat*` 0, `permission` 0, `privileg*` 0,
   `runtime` 0, `subprocess` 0. The five `capabilit*` hits all mean a skill or a WBS level. The
   authority layer traces to §51/§56-57/§59-60; **the containment layer has no textual basis at
   all.** `README.md:454-477` has a "Corrections to `specup.md`" section — 0.1.3 needs its
   mirror, an *Additions* section, or two-thirds of it reads as unsourced.
2. **A bundle cannot enforce** (`using-specup.md:1112-1124` — "Bundle | No | Distribution
   only"). The broker's authority must come from a workflow shell step or the container.
3. **No `{{ inputs.* }}` in any `run:` field** — hard-enforced by
   `tests/test_workflows.py:84-99` with `allowed = {"context.run_id"}`. A rendered docker
   invocation is a `run:` field.
4. **Exit code 2 inverts at the broker.** Everywhere else `2` means "not a governance failure"
   (`using-specup.md:68-83`). At the broker, `2` **denies**. Defensible, and it must be said in
   exactly those words because the manual teaches the opposite.

**Blockers for a second bundle or fifth workflow** (all currently red the moment either
appears): `tests/test_bundle.py:166`, `tests/test_workflows.py:62` and `:126` (`EXPECTED_GATES`
KeyError), `tests/test_catalog.py:81` and `:106`, plus hardcoded `bundles/specup` paths in
`Taskfile.yml:69,76,83,90,106,119`, `tools/build_archives.py:39`, `tools/build_catalog.py:53`.

**Loose end.** `openswe/` is untracked scaffolding — six empty dirs plus two zero-byte files
(`docker-compose.yml`, `bbpe/bbpe-codec.toon`), never committed, never mentioned in any commit
message. `langfuse`, `db/neo4j`, `db/clickhouse` and `bbpe` appear in **no design document**.
Either record their intent or remove them before 0.1.3; leaving undocumented scaffolding in a
release whose §9 is the honesty section is the wrong trade.

---

## Verification

1. **Both suites, both ways** — the pair is the check (`docs/dev/taskfile.md:38-42`):
   ```bash
   task test        # expect 273 passed, 8 skipped
   task test:engine # expect 281 passed
   ```
2. **New checks have tests in the existing form** — mutate `tests/fixtures/good/` and assert the
   failure, via `conftest.py`'s `Project` mutators and `assert_fails()`. There is no `bad`
   fixture by design.
3. **Signature verification is tested end to end** — a temp repo, a real signed commit, and an
   unsigned one; assert `APV-002` passes on the first and fails on the second. A mocked
   signature would test nothing.
4. **Every check id in the docs exists in the code, in both directions.** Grep the `DOC-*` and
   `APV-*` sets out of `scripts/python/` and diff against `using-specup.md` §6. A documented
   check that does not exist is the defect the guide itself warns about.
5. **The generic example fails the Elaboration gate on exactly the expected conditions:**
   ```bash
   python3 .specify/extensions/openup/scripts/python/evaluate_gate.py \
       --gate GATE-LIFECYCLE_ARCHITECTURE --root examples/my-program
   ```
   If it ever passes, the template has been filled in for the reader and the lesson is gone.
6. **SpecUP's own audit runs and its real numbers are recorded**, not tuned:
   ```bash
   python3 extensions/openup/scripts/python/audit.py --json
   ```
7. **Release gate:** `task release:check`, then the six steps of
   `docs/runbooks/publishing-to-spec-kit.md`, including the clean-project install in §5 — which
   must report **six** components, not zero.

---
---

# ADDENDUM — `docs/research/specup-agent-stack.md`

*Added 2026-09-17, after the 0.1.2 doc sweep. This is a separate deliverable from everything
above: a research report, not an implementation. It feeds §7 and does not change it.*

## Context

`open-swe/` is nine components expressed as **17 filesystem paths containing zero bytes**. Every
file is empty; the directory layout is the entire specification. Nothing in the repository
explains it — `grep` finds `valkey`, `plane.so`, `bm25s` and `docker-sandbox` in **no document at
all**, and the one place the folder is mentioned is this plan's §7 *Loose end*, which is
**already stale**: it describes `openswe/`, "six empty dirs", and a `bbpe/bbpe-codec.toon` that
no longer exists.

§7 *Loose end* set the condition: *"Either record their intent or remove them before 0.1.3."*
This report is the first half of that. It exists so the 0.1.3 stack is argued from sources
before any of it is built, and so that the two licence problems below are found now rather than
after the compose file has content.

**The governing constraint is `AGENTS.md` — "Resolve, or stop — never infer".** An empty
directory named `neo4j` states that Neo4j is wanted. It does not state what for. The report
therefore marks every claim as **Verified** (read from an upstream source, cited) or
**Inferred** (read off the folder layout), and never blurs the two. A report that asserted a
role for each directory would be the invented governing artifact that rule exists to forbid.

## What the research already established

Recorded so it is not re-derived. Every item below was fetched this session.

**The layout, exactly as it stands:**

```
agent/  db/{clickhouse,neo4j,valkey}/  docker-compose.yml  docker-sandbox/
langfuse/  langgraph/{aegra/,langgraph.json}  plane.so/  rag/{bbpe/tokenizer.json,bm25s/corpus.jsonl}
```

**The two findings that make the stack cohere:**

1. **Open SWE's `langgraph.json` declares exactly five graphs** — `agent`, `reviewer`,
   `analyzer`, `chat`, `scheduler` — and every entrypoint is a `traced_*` wrapper
   (`agent.graphs.agent:traced_agent`). That is the seam `langfuse/` plugs into, and it makes
   the `langgraph/langgraph.json` placement correct rather than arbitrary.
2. **Aegra's config is `aegra.json`, not `langgraph.json`** — same `graphs`/`dependencies`/
   `http`/`store` shape, different filename. The layout assumes one file; the two projects want
   two. Small, real, and worth stating.

**Licences, each read from source:**

| Component | Licence | Note |
|---|---|---|
| Open SWE | MIT | now *"an open-source software factory built on Deep Agents"* — the README has moved on from §7's reading |
| Aegra | Apache-2.0 | compose uses `pgvector/pgvector:pg18` + `redis:7-alpine` |
| LangGraph / deepagents | MIT | |
| Langfuse | **MIT core**, `/ee` dirs commercial | EE = RBAC, audit logs, SCIM, retention, masking |
| ClickHouse | Apache-2.0 | |
| Valkey | BSD-3-Clause | Linux Foundation fork of Redis 7.2.4, wire-compatible |
| bm25s | MIT *(re-verify)* | Numpy/Scipy only; eager sparse scoring |
| **Neo4j Community** | **GPL-3.0** | Enterprise is commercial-only |
| **Plane Community** | **AGPL-3.0** | §13 network clause |

**deepagents still ships no Docker sandbox backend** — providers are LangSmith, Daytona, E2B,
Modal, Runloop, Vercel, AgentCore, NVIDIA OpenShell. `SandboxBackendProtocol` requires one
method, `execute()`; `read`/`write`/`edit`/`delete`/`ls`/`glob`/`grep` are all built on it by
`BaseSandbox`. So `docker-sandbox/` is genuinely additive and plausibly upstreamable, and §7's
"every file and shell operation funnels through one method" finding survives.

**Three services each require PostgreSQL** (Aegra, Plane, Langfuse) and **three each require
Redis** (same three). `db/` has `valkey` but **no `postgres`**, and Langfuse v3 additionally
requires an S3/blob store that the layout has nowhere to put.

## The report

**One new file: `docs/research/specup-agent-stack.md`.** Prose in the house voice — the
`docs/dev/licensing.md` register: audience line, tables over paragraphs, the cost stated rather
than omitted, and a closing *"What checks any of this"*. ASD-STE100 per `language-rules.md`.

| § | Content |
|---|---|
| 1 | **What `open-swe/` is today** — the inventory table, 17 paths / 0 bytes, and the Verified-vs-Inferred contract stated up front |
| 2 | **Correcting the record** — §7 *Loose end* describes a folder that no longer exists; name the drift rather than silently supersede it |
| 3 | **The nine components** — one subsection each: what it is, licence, what it requires, upstream citation, and its role marked Verified or Inferred |
| 4 | **How they compose** — the request lifecycle, end to end: Plane work item → webhook → Aegra run → Open SWE `agent` graph → retrieval (`bm25s` lexical + Neo4j structural, tokenised by `bbpe`) → `docker-sandbox` `execute()` → PR → `reviewer` graph → `traced_*` spans to Langfuse → ClickHouse → status back to Plane |
| 5 | **The shared substrate** — one Valkey and one Postgres serving three consumers each; which are genuinely separable and which are not |
| 6 | **Licences** — the table above, then the two copyleft components in detail |
| 7 | **Permissive alternatives** — see below |
| 8 | **What the layout does not have** — no `postgres/`, no blob store, no vector store, no secrets, no ingress; `docker-compose.yml` is empty |
| 9 | **Where this argues with SpecUP** — `NON-FR-CORE-0001` filesystem authority vs. five stateful services; `requires-python` `>=3.10` → `>=3.12`; no `{{ inputs.* }}` in a `run:` field (`tests/test_workflows.py:84-99`); exit code `2` inverting at the broker; a bundle cannot enforce |
| 10 | **Open questions** — named as ADR candidates, decided nowhere in this document |
| 11 | **Sources** — every URL, with what was read from it |

### §6–§7, the licence sections

Neo4j CE is **GPL-3.0** and Plane CE is **AGPL-3.0**, under a product licensed BUSL-1.1 and
intended for sale. The report separates the two questions that get conflated:

- **Running them** as separate processes over Bolt and REST. On the common reading this is not a
  derivative work, and `docker-compose.yml` references images rather than redistributing them.
- **Shipping them** — vendoring, forking, or publishing a derived image — which is where GPL-3.0
  reciprocity and AGPL §13 actually bite.

Then the substitutes, with what each costs:

- **The graph.** The strongest candidate is not another graph database but **Apache AGE**
  (Apache-2.0) or recursive CTEs **in the PostgreSQL the stack already mandates** — removing a
  service and the GPL exposure together. Memgraph (BSL) and ArangoDB (BUSL-1.1) are the same
  licence class as SpecUP itself, which is worth saying plainly.
- **The tracker.** Open SWE's native surface is already **GitHub issues and PR comments**, so
  Plane is an additional surface rather than a required one. Most self-hostable trackers are
  copyleft, so the honest conclusion is likely *integrate with the tracker the customer already
  runs* rather than *self-host a different one*.

**Every licence in §7 is re-read from the project's own `LICENSE` at write time.** The candidate
list above came from a single reading and several of these projects have relicensed before —
Redis, ArangoDB and Neo4j Enterprise all did. Per `AGENTS.md`, a licence stated from memory is
exactly the class of value that arrives with false confidence.

## Governance registration — evidence only

Per your decision: an evidence artifact and one edge. **No new requirement and no new WBS node** —
`wbs.yaml:269-275` refuses to decompose 0.1.3 because its requirements do not exist yet, and
inventing one to hang research on is the ordering `specup.md` §39 prevents.

- `.specify/traceability/requirements.yaml` — `EVID-0008`, `type: evidence`, `status: REVIEW`,
  `source: docs/research/specup-agent-stack.md`, with a comment saying why it is a document and
  not a test: what a reviewer must check is whether the licence and dependency claims are true,
  and none of that is machine-checkable.
- `.specify/traceability/traceability.yaml` — `EVID-0008 evidences WBS-1.1.3`, `provenance:
  asserted`. `EVID-0006 → RISK-0003` is the precedent for evidence attaching to a non-leaf.
- `.specify/wbs/wbs.yaml` — add `evidence: [EVID-0008]` to `WBS-1.1.3`. The schema permits it on
  any node (`wbs.schema.json:82-86`) and `WBS-1.1.3` is `planned`, so no `DOD-*` check fires.

### The count ripple — do not hand-compute it

This adds one artifact and one edge: **78 → 79**, and `evidences` 7 → 8. That number is quoted
in six places, two of them generated:

```
render_views.py --write   regenerates  coverage.md, traceability.md
hand-edited                            .specify/traceability/index.md:35,42,47,126
                                       .specify/risks/index.md:37
                                       docs/runbooks/release-notes-0.1.2.md:111,115
```

Run `derive_edges.py --write` then `render_views.py --write`, **read the regenerated
percentages, and propagate those**. Do not arithmetic them by hand — `asserted_share` crosses a
rounding boundary, and a reconstructed figure is the defect `AGENTS.md:57-66` is about.
`derived.yaml` should not change: no WBS node is added, so `wbs-iteration-field` derives nothing
new and TRC-011 stays green.

The release notes are editable because **0.1.2 is not tagged yet**. Had it shipped, the correct
move would be to leave them alone as a record.

## Files

| File | Change |
|---|---|
| `docs/research/specup-agent-stack.md` | **new** — the report |
| `docs/README.md` | +1 row, new `**Research**` group after Dev |
| `.specify/traceability/requirements.yaml` | `EVID-0008` |
| `.specify/traceability/traceability.yaml` | one `evidences` edge |
| `.specify/wbs/wbs.yaml` | `evidence:` on `WBS-1.1.3` |
| `.specify/traceability/{coverage,traceability}.md` | regenerated |
| `.specify/traceability/index.md`, `.specify/risks/index.md`, `docs/runbooks/release-notes-0.1.2.md` | counts |

`README.md`'s table is left alone — it lists what a user of SpecUP needs, and this is internal
research. Say so rather than leaving it as an oversight.

## Verification

1. **The inventory is reproducible.** `find open-swe -mindepth 1 | sort` and
   `find open-swe -type f -size +0c` — the second must stay empty, or the report's premise has
   changed and §1 is wrong.
2. **Every licence claim is re-read at write time** from the project's own `LICENSE`, not from
   this plan. Say which reading was done, per `AGENTS.md:74-75`.
3. **Every URL in §11 resolves and says what it is cited for.** A citation that does not support
   its claim is worse than none.
4. `python3 extensions/openup/scripts/python/audit.py` — the gate must still report exactly
   `TRC-006` at 95% and `acceptance_scenarios_passing`. **A third failure means this change
   broke something**; a repaired one means a number was tuned.
5. `task test` and `task test:engine` — the pair, unchanged. No code is touched, so any movement
   is a signal.
6. `git diff --stat` — `.specify/traceability/derived.yaml` must be **absent** from it.

## Not in scope

- Writing anything into `open-swe/`, or committing it. The folder stays untracked and empty;
  the report records intent, and whether the placeholders are kept or deleted is the second half
  of §7's *Loose end* and a separate decision.
- Any ADR. §10 names the candidates and decides none of them.
- Any dependency, `requires-python` bump, or manifest change.
- The 0.1.2 release — still `release:catalog`, the tag, and the GitHub release, still yours to
  trigger.
