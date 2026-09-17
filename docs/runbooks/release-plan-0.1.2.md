# SpecUP 0.1.2 — release plan *(written before the split; now the 0.1.3 plan)*

**Audience:** whoever implements this release, and whoever reviews whether it was worth doing.

> **This document describes an unsplit release that was then split, and the filename is kept
> so existing links resolve.** The runtime work below — the capability broker, the container,
> the Open SWE integration — moved to **0.1.3** and is still the live plan for it. The
> governance work moved to **0.1.2** and has shipped; what it actually became is
> [`release-notes-0.1.2.md`](release-notes-0.1.2.md), which is the record, while this is the
> intent. The §8 table carries the per-item split.
>
> Splitting was deliberate: the broker and the container are the two items that could
> invalidate a release, and nine independently useful workstreams should not wait behind them.
>
> Two things below were overtaken by later decisions and are annotated in place rather than
> deleted — §1's licensing conclusion, and the assumption throughout that SpecUP is MIT.

0.1.1 shipped a governance layer for Spec Kit: an extension, a preset, four workflows, and
gates that halt a run. It governs an agent it does not own — whichever agent the user happens
to be running.

This release closes that gap. SpecUP acquires a runtime:
[Open SWE](https://github.com/langchain-ai/open-swe), LangChain's asynchronous coding agent,
running inside a container that starts with no capabilities and acquires them only as the
governance graph grants them.

The sentence the release has to make true:

> **The governance decides what the agent may do; the factory decides how it does it; the
> container decides where. A capability is granted because the governance graph resolved a
> claim to it — never because the agent asked.**

---

## 1. The finding that shapes everything: licensing

This has to come first, because it constrains the architecture rather than the schedule.

| Component | Licence | Consequence |
|---|---|---|
| `langgraph`, `langchain-core`, model integrations | MIT | usable, no constraint |
| Open SWE itself | open source, on GitHub | usable |
| **`langgraph-api` — the standalone Agent Server binary** | **Elastic License 2.0** | **production self-hosting needs a commercial key** |
| **[Aegra](https://github.com/aegra/aegra) — Agent Protocol server, FastAPI + PostgreSQL** | **Apache-2.0** | **a drop-in replacement for the row above, with no ELv2 in its dependency tree** |

> **Superseded in part, 2026-09-17.** SpecUP is no longer MIT — 0.1.2 relicensed it to
> BUSL-1.1 ([`docs/dev/licensing.md`](../dev/licensing.md)). The conclusion below survives
> unchanged and the reasoning for it does not, which is worth reading rather than skipping:
> becoming source-available grants no rights to anyone else's source-available software, so
> Elastic's licence binds SpecUP exactly as it did before. What changed is who pays. The
> constraint used to protect SpecUP's *users* from an unannounced commercial dependency; it now
> also protects SpecUP's *customers* from a second vendor's agreement on top of the one they
> already have. Read "MIT" below as "the licence SpecUP was under when this was written."

SpecUP was MIT when this was written. A release that made SpecUP depend on an ELv2 server would
quietly convert a permissively licensed governance tool into one that cannot be run in
production without a LangChain Enterprise agreement — and it would do so without saying so,
which is precisely the class of defect this project exists to reject.

**Two decisions follow, and they are not negotiable in this release:**

1. **SpecUP core stays Open-SWE-free.** The `specup` bundle of 0.1.1 gains nothing and
   loses nothing. A user who wants governance over their own agent keeps exactly what they have.
   *(As written this said "stays MIT and Open-SWE-free". The MIT half is spent; the
   Open-SWE-free half is the part that was actually load-bearing, and it holds.)*
2. **Open SWE adoption ships as a separate, optional bundle: `specup-openswe`.** It declares the
   licence position in its manifest, and the installer surfaces it before writing a file.

> **Amended 2026-09-17.** The table above gained an Aegra row and it dissolves the dilemma this
> section was written around: durable execution, a task queue and resumable runs are available
> under Apache-2.0, so "in-process only" becomes one of two supported modes rather than the only
> licence-clean one. What it buys instead is a PostgreSQL dependency, which is an argument with
> `NON-FR-CORE-0001` rather than with a licence — see
> [`docs/dev/licensing.md`](../dev/licensing.md).

Within that bundle, prefer running graphs **in-process against the MIT `langgraph` library**
over the ELv2 Agent Server. The server buys durable execution, a task queue and a hosted UI;
for a single-workspace agent under a governance gate, a supervisor process and the filesystem
already provide the durability that matters, and the filesystem is the auditable state machine
SpecUP is built on. Where the Agent Server genuinely is the right answer — multi-tenant, many
concurrent runs — that is an operator's decision to license, taken knowingly.

ADR-0001 of this release records that, with the rejected alternatives.

---

## 2. The three layers

```
┌─────────────────────────────────────────────────────────────┐
│  AUTHORITY — the openup extension                           │
│  Python validators over the filesystem. Decides.            │
│  Never executes agent work. Cannot be modified by the       │
│  agent it governs.                                          │
└────────────────────────────┬────────────────────────────────┘
                             │  capability-profile.yaml
                             │  (generated, machine-owned)
┌────────────────────────────▼────────────────────────────────┐
│  CONTAINMENT — the sandbox                                  │
│  --cap-drop=ALL, non-root, read-only root filesystem,       │
│  explicit bind mounts, seccomp, egress proxy.               │
│  Enforces. Knows nothing about OpenUP.                      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  FACTORY — Open SWE                                         │
│  Plans, edits, runs tests, opens pull requests.             │
│  Executes. Has no opinion on whether it is allowed to.      │
└─────────────────────────────────────────────────────────────┘
```

The separation is the design. The layer that decides is not the layer that executes, and
neither is the layer that enforces. An agent that could edit the validators that govern it
would be governing itself, which is the circularity the provenance model already exists to
expose one level down.

**Concretely:** `extensions/openup/` is mounted read-only into the sandbox. The agent can run
the validators and cannot change them. A change to a validator is a change to the repository,
made on a branch, reviewed by a human.

---

## 3. The capability model

### 3.1 What `--cap-drop=ALL` actually buys, stated honestly

Linux capabilities govern privileged kernel operations: binding low ports, changing file
ownership, loading modules, tracing other processes. **A coding agent needs none of them.**
So dropping all of them is necessary, cheap, and — on its own — close to irrelevant to the
threats that matter here.

The interesting failures are not privileged operations. They are:

- writing to `src/` during Inception, when no architecture exists yet;
- `git push --force` to `main`;
- exfiltrating a repository to an arbitrary host;
- editing the risk register to lower an exposure below the gate threshold;
- writing an `approvals:` entry.

None of those needs a Linux capability. Every one of them is an *ordinary* file write, network
call or subprocess. A plan that presented `--cap-drop=ALL` as the mechanism would be
security theatre, and would fail its own audit.

**So "capability" in this design means four enforcement surfaces, of which Linux capabilities
are the smallest:**

| Surface | Mechanism | What it stops |
|---|---|---|
| Linux capabilities | `--cap-drop=ALL`, add back per profile | privilege escalation inside the container |
| Filesystem | read-only root, explicit `rw` bind mounts per path glob | writing outside the paths the phase permits |
| Network | default-deny egress proxy, per-profile allowlist | exfiltration; unreviewed dependency pulls |
| Process | seccomp profile; `git` wrapped, not raw | force-push, history rewrite, remote changes |

The container runs as a non-root user with `no-new-privileges`. `CAP_NET_BIND_SERVICE` is the
only capability any profile adds, and only for a Construction step that needs a local test
server on a low port — which the templates avoid by using a high port, so in practice every
profile is `cap-drop=ALL` with nothing added.

Saying that plainly is better than claiming a capability model that does more work than it does.

### 3.2 Lazily granted by progressive disclosure

This is the part that is new, and it is the reason the release is interesting.

In a conventional sandbox an operator configures permissions up front, and the agent inherits
whatever the configuration allows for the whole session. Here, the grant is **derived at
runtime from the governance graph**, and the derivation is the same progressive-disclosure walk
the agent already performs:

```
  directory  →  AGENTS.md  →  index.md  →  the one artifact
       │            │             │              │
       │            │             │              └─ the WBS node, requirement, gate state
       │            │             └──────────────── the scope this work belongs to
       │            └────────────────────────────── the rules binding that scope
       └─────────────────────────────────────────── where the work is
```

Each step resolves part of a claim. When the walk terminates in a resolved L7 WBS node with an
owner, an iteration and at least one requirement, the governance can answer: *what does this
work item need, and is the project in a state where that is permitted?* That answer is the
capability grant.

**Reading the governance is the act that earns the permission.** An agent that has not
disclosed the context has not established a claim, and holds nothing.

Three properties fall out of this, and each is worth the implementation cost:

- **The grant is narrow.** It is scoped to one work item, not one session. Finishing the item
  drops it.
- **The grant is auditable.** It is a file, written before the work, naming the artifacts that
  justified it. "Why was the agent able to do that?" is answerable afterwards, from the
  repository, by someone who was not there.
- **The grant fails closed.** Same three-way contract as every other SpecUP check — `0` granted,
  `1` denied by governance, `2` could not evaluate. **`2` denies.** This mirrors `ctx.check()`,
  which already returns `False, ["<id> was not evaluated"]` rather than passing on absence of
  evidence.

### 3.3 The profile, as a file

Filesystem-first, like everything else. A new CLI, peer to `evaluate_gate.py`:

```bash
python3 .specify/extensions/openup/scripts/python/resolve_capabilities.py \
    --wbs-node WBS-1.3.1.2.4.1.1 --json --out .specify/runtime/capability-profile.yaml
```

```yaml
# GENERATED — machine-owned, like derived.yaml. Never hand-edit.
schema_version: "1.0"
resolved_at: "2026-09-16T09:14:00Z"
granted_for:
  wbs_node: WBS-1.3.1.2.4.1.1
  iteration: ITER-C-01
  phase: CONSTRUCTION
  requirements: [REQ-AUTH-0014]
justified_by:                    # the disclosure walk that established the claim
  - src/auth/AGENTS.md
  - src/auth/index.md
  - .specify/wbs/wbs.yaml
  - .specify/traceability/requirements.yaml
gate_state:
  GATE-LIFECYCLE_ARCHITECTURE: PASS      # required to write src/ at all
capabilities:
  linux: []                              # cap-drop=ALL, nothing added
  filesystem:
    read: [".specify/**", "src/**", "tests/**", "docs/**"]
    write: ["src/auth/**", "tests/auth/**", ".specify/evidence/checks/**"]
  network:
    egress: ["registry.npmjs.org", "repo1.maven.org"]   # from the project's declared toolchain
  process:
    git: [status, diff, add, commit, branch, checkout]   # no push, no rebase, no reset --hard
denied:
  - reason: "publish requires GATE-PRODUCT_RELEASE and an explicit human approval"
    capabilities: [git.push, git.tag, release.publish]
```

The docker invocation, the seccomp profile and the proxy allowlist are **rendered** from this
file. Nothing is configured twice.

### 3.4 Phase profiles

| Phase | Writable | Egress | Git | Notes |
|---|---|---|---|---|
| Inception | `.specify/lifecycle/`, `.specify/risks/` | none | local commits | cannot touch `src/` — there is no architecture yet |
| Elaboration | + `.specify/architecture/`, `wbs/`, `traceability/`; spike branches | package registries | + branch | `src/` opens only for nodes marked `kind: spike` |
| Construction | + `src/`, `tests/` | package registries | + branch, commit | requires `GATE-LIFECYCLE_ARCHITECTURE` PASS |
| Transition | + `docs/`, release notes | registries | + tag *(human-approved)* | publish is never agent-granted |

A profile is the intersection of the phase, the WBS node's own scope, and the gate state. The
phase sets the ceiling; the node narrows it.

---

## 4. Human approval is the only final authority

0.1.1 states this in prose. 0.1.2 makes it structural, because prose is what this project
refuses to accept as governance anywhere else.

**The invariant:** *no agent action can produce an approval, and no agent action can be taken
whose only justification is an approval the agent produced.*

Four changes:

1. **`APV-001` — an agent may not write an `approvals:` entry.** A new check compares the
   approvals in the working tree against those in `HEAD`; an added entry in a commit whose
   author is the agent identity fails. Approvals are added by a human, in a commit a human
   authored.
2. **`approvals[].by` must resolve to a named human** in `.specify/governance/approval-matrix.md`.
   Today the matrix ships with the "who" column blank, which means anyone can override anything
   and the gate is decorative — the file says so itself. `APV-002` fails a blank cell that is
   being relied on.
3. **Gate override records identity.** A workflow `override` is already a logged human act; the
   override record gains the approver and the remediation commitment, and `APV-003` fails an
   override record with neither.
4. **The capability broker has no "approved" tier it can reach.** `git.push`, `git.tag` and
   `release.publish` are grantable only when an approval artifact exists that the agent could
   not have written. The broker verifies this by construction, not by asking.

This is also what the worked example already demonstrated, in the only way that counts: the
vision for `cits-crypto` was wrong — it scoped one document out of seven — and a human caught
it. No validator did, and none could have.

---

## 5. Meta-cognitive templates

The request is for templates that are *self-explanatory* and *meta-cognitive*: a template that
explains its own purpose, and that teaches the reader how to tell when they have filled it in
badly.

Every generic template in 0.1.2 carries the same five-part frame:

```markdown
<!-- WHAT QUESTION THIS ANSWERS
     ... and, explicitly, what it does not answer. A template that does not draw its own
     boundary gets filled with whatever the author had nearby. -->

<!-- HOW YOU CAN TELL THIS IS WRONG
     The failure mode, named. Not "be thorough" — the specific way this artifact goes wrong. -->

<!-- WHAT CHECKS IT
     The check id, and what it does and does not verify. If nothing checks it, say so. -->

<!-- WORKED EXAMPLE
     A real excerpt from workspace/cits-crypto, with the reasoning intact. -->

<!-- WHERE AUTHORITY SITS
     Who decides this is done. For anything past DRAFT, that is a named human. -->
```

The "how you can tell this is wrong" section is the meta-cognitive one, and it is the section
that has to be written from experience rather than from imagination. Which is what the worked
example is for.

### 5.1 What `cits-crypto` actually taught, and where each lesson lands

The worked example is not decoration. It ran a real normative corpus — seven standards
documents — through Inception and into Elaboration, and it produced findings that no amount of
designing in the abstract would have produced.

| What happened | What it teaches | Where it lands in 0.1.2 |
|---|---|---|
| The SSP truth table was transcribed from a *reading of the rule* rather than from the page, and the predicate written to cross-check it was derived from the same misreading. **They agreed, and both were wrong.** | Two statements only cross-check each other if they come from genuinely independent sources. A "duplicate" that shares an origin verifies nothing. | ADR template gains the *independent-oracle* pattern and names this failure. New check `DOC-004`: a claimed cross-check must cite two distinct sources. |
| `NOT_EVALUATED` as a third verdict, never rounded to pass or fail | SpecUP's own three-way exit contract is a general pattern, not a CLI convention | Preset guidance; the code template ships a three-valued verdict type; the capability broker uses it (`2` denies) |
| Every normative value carried document + edition + clause, via a **custom `cites:` key** that the schema tolerated | Citation at the value level is what made review possible at all | Promote `cites:` to a first-class, documented field in `artifact.schema.json` |
| Closing a risk failed: the schema required a mitigation WBS node, and none existed yet. Status became `mitigating` with the evidence recorded. | The honest intermediate state is a feature. A gate that blocks a premature closure is working. | Risk template documents `mitigating` as the correct state when evidence exists but the governed link does not |
| ADR-0001 recorded a normative conflict and **RISK-0010 stayed open** | An ADR records a decision taken under uncertainty; it does not remove the uncertainty | ADR template: mandatory *Revisit when*, and an explicit note that deciding ≠ closing the risk |
| Twice, a value was reconstructed from memory instead of re-read from the source — and was wrong both times | Re-read before asserting. This is the single highest-yield agent operating rule the example produced. | `AGENTS.md` template gains it as a rule; the preset repeats it at the point of use |
| The human corrected the scope; no validator could have | Final authority is human, structurally | §4 |

### 5.2 `workspace/` as the home, and the My Program / My Project split

```
workspace/
├── my-program/            ← the GOVERNANCE. "My Program". WBS-1 is a program.
│   └── .specify/          ← lifecycle, wbs, risks, traceability, architecture
│       └── ...
├── my-project/            ← the APPLICATION. What gets built.
│   └── src/ tests/ docs/
└── cits-crypto/           ← the worked example, kept as a reference, not a template
```

The generic example ships as `workspace/my-program/` + `workspace/my-project/`, fully populated
and self-describing: every file explains what it is for, what would make it wrong, and what
checks it. It passes `GATE-LIFECYCLE_OBJECTIVES` out of the box and fails
`GATE-LIFECYCLE_ARCHITECTURE` with the same five conditions a real project fails at that
point — because a template that shipped in a passing state would teach that the gates are
decorative.

`cits-crypto` stays where it is, as the worked example the templates cite. It is not a
template: it is a real project with a real corpus, and the difference is the point.

---

## 6. The docstring contract

> *"All internal and external API docstrings must be descriptive and focused enough to form its
> current working context only."*

This is a precise and checkable rule, and it is the code-level form of progressive disclosure.
A docstring is **the complete working context for the unit it documents, and nothing more**.
An agent that reads only that docstring can use or change that unit correctly. Anything beyond
that is context the reader is paying for and does not need.

The contract, as five checks in a new `validate_docs.py`:

| Check | Rule | Why |
|---|---|---|
| `DOC-001` | Every exported symbol has a docstring | Undocumented is unusable at bounded context |
| `DOC-002` | The docstring names what governs it — a `REQ-`, `ADR-` or `NON-FR-` id that resolves | An unanchored docstring cannot be checked against intent |
| `DOC-003` | The docstring states at least one thing the unit must **not** do, or the condition under which it refuses | The boundary is the half that gets omitted, and it is the half that matters |
| `DOC-004` | A docstring claiming a cross-check names two distinct sources | The `cits-crypto` failure, generalised |
| `DOC-005` | Length is bounded (warn past ~40 lines) | A docstring carrying an argument is an ADR wearing a disguise. Link the ADR. |

`DOC-005` warns rather than fails, deliberately: the cost of a long docstring is real but
small, and a hard failure would push people to delete reasoning rather than move it.

The worked example already satisfies this. From `core/src/main/kotlin/.../Verdict.kt`:

```kotlin
/**
 * The outcome of applying one normative rule to one configuration.
 *
 * Three values, not two. ADR-0009: a rule that could not be evaluated is never rounded up to
 * [CONFORMS] and never down to [DOES_NOT_CONFORM]. A report that silently omits the rules it
 * could not check states a conformance the guidelines do not give, and it does so exactly
 * where a reader most needs to know that nothing was verified.
 *
 * Implements REQ-POL-0003.
 */
```

Names what it is, what governs it (`ADR-0009`, `REQ-POL-0003`), and what it must never do. A
reader needs nothing else to use it correctly, and is given nothing else.

---

## 7. SpecUP governs itself

`.specify/` in this repository currently holds three cache directories and nothing else. The
governance tool is not governed. For a release whose claim is "production grade", that is the
first thing a reviewer will check.

0.1.2 scaffolds SpecUP's own lifecycle: vision, stakeholders, a WBS to L7 for this release, a
risk register, and traceability from the 273 existing tests to the requirements they verify.

This is not ceremony. It is the only way to find out what adopting SpecUP actually costs on a
codebase that already exists, which is the question `docs/guide/existing-project.md` currently
answers from reasoning rather than from having done it.

Expect it to be uncomfortable. Backward coverage over `extensions/`, `tools/` and `tests/`
will fail at first, and the honest response is to record the real figure rather than to widen
the perimeter until it passes.

---

## 8. What gets built, in order

Risk-first, as OpenUP requires — the two items that could invalidate the release come first.

| # | Item | Retires | Landed |
|---|---|---|---|
| 1 | **ADR-0001: the licence position.** Prove a graph runs in-process on MIT `langgraph`, with no Agent Server. | The risk that adopting Open SWE forces every SpecUP operator into a LangChain Enterprise agreement | **0.1.3** — and reshaped: Aegra (Apache-2.0) removes the constraint the ADR was to work around |
| 2 | **Spike: the capability broker.** `resolve_capabilities.py` + rendered docker/seccomp/proxy config. One end-to-end denial and one grant. | The risk that the central idea does not survive contact with a real sandbox | **0.1.3** |
| 3 | `specup-openswe` bundle skeleton; licence surfaced at install | — | **0.1.3** |
| 4 | Sandbox image: `cap-drop=ALL`, non-root, read-only root, egress proxy | — | **0.1.3** |
| 5 | Open SWE integration: graphs loaded with a profile; every tool call brokered | — | **0.1.3** |
| 6 | `validate_docs.py` (`DOC-001`–`005`) and the approval checks (`APV-001`–`003`) | — | **0.1.2** — shipped as `DOC-000`–`006` and `APV-000`–`005`, 13 checks rather than 8 |
| 7 | Meta-cognitive templates, with the `cits-crypto` harvest of §5.1 | — | **0.1.2** |
| 8 | `workspace/my-program` + `workspace/my-project` generic example | — | **0.1.2** — as `examples/`, because `workspace/` ships as an empty folder |
| 9 | SpecUP governs itself (§7) | — | **0.1.2** — gate FAIL, recorded rather than repaired |
| 10 | `cites:` promoted to first-class in `artifact.schema.json` | — | **not done** — kept a convention, since the artifact registry is never schema-validated and a schema edit would buy nothing |
| 11 | Docs: architecture page, capability reference, the licence position | — | **split** — the licence position shipped as `docs/dev/licensing.md` in 0.1.2; the other two are 0.1.3 |
| — | **Relicense MIT → BUSL-1.1** | Not planned here at all. Added during 0.1.2 to make the agent stack monetisable. | **0.1.2** |

Items 1 and 2 are gates on the rest. If the broker cannot be made to work without either
becoming trivially bypassable or making the agent unusable, the release becomes "SpecUP
governs Open SWE at the workflow level only" — a smaller, still honest claim. Deciding that
early is the point of doing them first.

---

## 9. What 0.1.2 will not do

The more honest this section, the more useful the release.

- **Not a security boundary against a hostile model.** The broker constrains an agent that is
  trying to do the right thing and may be wrong. An agent actively seeking to escape a
  container is a different threat model, and the container is not hardened for it. Saying
  otherwise would be the "LLM opinion as a gate" row of the README, one level down.
- **No multi-tenancy.** One workspace, one agent, one run.
- **The ELv2 Agent Server stays optional and unsupported here.** Running it is an operator's
  licensed decision.
- **No Microcks.** Still deferred; still inert.
- **The two unimplemented derivation rules stay unimplemented** — `openapi-operation-scan` and
  `evidence-manifest-scan` — and stay reported as unverified rather than trusted.
- **No claim that governance overhead is measured.** §7 will produce the first real number for
  one codebase. One is not a measurement.

---

## 10. Verification

1. `python3 -m pytest tests/ -q` — 273 passing today; no regression.
2. **Every check id in the docs exists in the code, in both directions.** Already the rule; now
   covers `DOC-*` and `APV-*`.
3. **The broker denies by default.** A test asserts that a profile request naming an
   unresolvable WBS node exits `2` and grants nothing — the fail-closed property, tested rather
   than asserted.
4. **The generic example fails the Elaboration gate on exactly the expected conditions.** If it
   ever passes, the template has been filled in for it, and the lesson is gone.
5. **The licence claim is tested**: a run of the example graph with no `LANGGRAPH_*` licence
   variable present, asserting it completes.
6. `task build && task validate` — the catalog stays honest, per the publishing runbook.

---

## Sources

- [langchain-ai/open-swe](https://github.com/langchain-ai/open-swe)
- [Self-host standalone servers — LangChain docs](https://docs.langchain.com/langsmith/deploy-standalone-server)
- [LangGraph is MIT-Licensed, but Your Production Deployment Might Not Be](http://rvernica.github.io/2026/03/langchain-license)
- [Open SWE system architecture — DeepWiki](https://deepwiki.com/langchain-ai/open-swe/1.1-system-architecture)
