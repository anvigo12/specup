# The SpecUP agent stack — what `open-swe/` names, and how it would run

**Audience:** anyone deciding whether the 0.1.3 runtime is the right shape, and anyone who has
to build it.

**Status: research, and now ten decisions.** This document reports what each component in
`open-swe/` is, how the twelve of them compose into a production stack, and what adopting them
would cost. The previous draft decided nothing. Since then the project owner has ruled on ten
of its open questions; the rulings are recorded in [§12.1](#121-decisions-taken) and carried into
every section they change. What remains open is [§12.2](#122-the-eighteen-questions) and belongs in ADRs.

**The eighth ruling is different in kind from the other seven.** Each of those settles one
component. Decision 8 adopts a standard — the twelve-factor methodology, extended to fifteen — and
a standard is something every component is then measured against.
[§11](#11-the-stack-as-a-fifteen-factor-application) is that measurement, and it is the only part of
this report that produces obligations a program could check.

**Decisions 9 and 10 close the rest.** Decision 9 adopts, in one move, a researched answer to every
one of the eighteen questions in [§12.2](#122-the-eighteen-questions) — on the ground that
established practice is the better answer while this stack is young, and that each reopens as its
component matures. Decision 10 gives the GitHub surface a written grammar
([§5.4](#54-the-conventions-the-github-surface-follows)). The honest reading of decision 9 is in
[§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on): eighteen answers borrowed
from outside, six of them from secondary sources, none of them measured here.

**[§13](#13-meta-cognition-exploration-and-the-parts-that-must-not-be-explored) is new, and it
reopens the questions section.** The previous revision of this page said the document no longer had
one. That is no longer true. The governance layer has to say how the agent improves and who is
allowed to certify that it did, and researching it produced **six more questions**
([§13.10](#1310-six-new-questions)) rather than answers. Decision 9 does not reach them: it rests on
established practice, and there is no established practice for governing a self-improving agent
inside a governance tool. The section takes **no decision** and its central claim is a refusal —
*an agent may optimise what it does, and never what decides whether what it did was good.*

> **A decision recorded here is not an ADR.** It is a ruling written into a research report,
> which is weaker than the artifact this project would normally demand for a choice of this size.
> [What checks any of this](#what-checks-any-of-this) says so again at the end, because it is the
> single easiest thing in this document to forget.

> Read [`docs/dev/licensing.md`](../dev/licensing.md) first if you are here for the licence
> question. This page extends it to the runtime; that page is the authority on SpecUP's own
> terms.

> **If you are here to operate the stack rather than to decide on it, read
> [`specup-agent-shape.md`](specup-agent-shape.md) instead.** It synthesises this report into one
> running system — five planes, eleven processes, two lifecycles, the trust boundaries and the
> failure matrix — and carries **31 numbered assumptions** for the inferences that synthesis has to
> make. This page stays the authority on *why* each component is here; that page is the authority
> on *how they run together*, and it corrects one claim in
> [§13.7](#137-one-rule-and-the-five-places-it-lands) about where the governance tree is protected.

**Four conclusions are worth putting at the top, because the rest of the report is the working.**

1. **SpecUP composes this stack. It does not redistribute it** ([decision 1](#121-decisions-taken)).
   That one ruling resolves most of [§7](#7-the-licence-position): a licence that governs
   *distribution* cannot be triggered by a project that distributes none of the software it
   governs. The remaining obligations are the ones that survive composition, and there are two.
2. **The graph is reached over Bolt, and Bolt is a wire rather than a product**
   ([decision 6](#121-decisions-taken)). SpecUP ships an Apache-2.0 driver and no server, so
   Neo4j's GPL-3.0 stops being SpecUP's problem and becomes a choice the customer makes about
   their own instance. **One correction to the premise:** the drivers are Apache-2.0; the Bolt
   *specification documentation* is CC BY-NC-SA 4.0, and [§3.10](#310-dbneo4j--the-graph-store)
   says what that does and does not restrict.
3. **The licence risk moved again, and it is now one transitive Python dependency.** Adopting
   Vouch ([decision 4](#121-decisions-taken)) puts `vouch-protocol` in SpecUP's own
   `requirements.txt`, and that package depends on **`jwcrypto`, which is LGPL-3.0-or-later** —
   the first copyleft library in SpecUP's own install path rather than in a container it merely
   talks to. [§7.1](#71-two-copyleft-items-and-neither-is-shipped) is where that is worked
   through. Model weights remain the other trap, and
   [decision 5](#121-decisions-taken) takes SpecUP out of their redistribution path entirely.
4. **The twelve factors agree with the decisions already taken, and settle two arguments that were
   still open** ([decision 8](#121-decisions-taken)). Factor IV's definition of a backing service is
   decision 1 arriving from architecture instead of from licensing. Factor III's definition of
   config resolves the `NON-FR-CORE-0001` conflict in SpecUP's favour rather than against it. And
   factor V supplies the index provenance [§9](#9-what-the-layout-does-not-have) has been asking for.
   **Four factors still cannot be met and one is violated permanently**, which
   [§11](#11-the-stack-as-a-fifteen-factor-application) names rather than smooths over.

---

## 1. What `open-swe/` is today

It is **56 paths containing zero bytes** — 32 directories, 4 placeholder files and 20 `.gitkeep`
files. No component is vendored and no compose file has content.

The tree below shows the directories and the four placeholder files. Every directory with no
file of its own carries a `.gitkeep`, which is how the layout survives a clone: git tracks files,
not directories, so without them a checkout would contain four files and none of the structure
that is the specification.

```
open-swe/
├── agent/                           (empty)
├── agent-inbox/                     (empty)
├── db/
│   ├── clickhouse/                  (empty)
│   ├── neo4j/                       (empty)
│   ├── postgres/                    (empty)
│   ├── seaweedfs/                   (empty)
│   └── valkey/                      (empty)
├── docker-compose.yml               0 bytes
├── langfuse/                        (empty)
├── langgraph/
│   ├── aegra/                       (empty)
│   └── aegra.json                   0 bytes
├── rag/
│   ├── bbpe/tokenizer.json          0 bytes
│   ├── chunk/
│   │   ├── cast/                    (empty)
│   │   └── contextual/              (empty)
│   ├── embed/
│   │   └── qwen3-embedding/         (empty)
│   ├── eval/
│   │   ├── coir/                    (empty)
│   │   └── golden/                  (empty)
│   ├── fuse/                        (empty)
│   ├── index/
│   │   ├── ann/
│   │   │   ├── hnsw/                (empty)
│   │   │   └── ivf/                 (empty)
│   │   └── bm25s/corpus.jsonl       0 bytes
│   └── rerank/
│       └── qwen3-reranker/          (empty)
├── sandbox/
│   └── openshell/                   (empty)
└── vouch/                           (empty)
```

**`(empty)` above means the directory holds a `.gitkeep` and nothing else.** Reproduce the full
listing with `find open-swe -mindepth 1 | sort`, strip the scaffolding with
`find open-swe -mindepth 1 -not -name .gitkeep | sort`, and confirm the premise with
`find open-swe -type f -size +0c`, which must return nothing.

**So the directory layout is most of the specification.** That governs how this report is
written. `AGENTS.md` sets the rule it has to obey:

> *"When a reference does not resolve, stop and say so. Do not invent the requirement, the
> criterion, or the risk that would have made the task coherent. An invented governing artifact
> is worse than a missing one: it looks like governance and checks nothing."*

A directory named `neo4j` establishes that Neo4j is wanted. It does not establish what for.
Every claim below therefore carries one of four markers, and they are not interchangeable:

| Marker | Means |
|---|---|
| **Verified** | Read this session from the named upstream source, cited in [§14](#14-sources) |
| **Inferred** | Read off the folder layout or off how these projects are normally combined. **A guess, marked as one** |
| **Specified** | **Created deliberately, with the intent recorded here at the moment of creation.** Neither a reading nor a guess — a decision by the author of this report, written down |
| **Decided** | **Ruled on by the project owner**, and recorded here rather than discovered here. The ten rulings are listed together in [§12.1](#121-decisions-taken) |

The last two markers are the ones to read carefully, because they look like authority and are not
the same thing. *Specified* is this report choosing a shape — `agent-inbox/` and the whole of
`rag/` below `bbpe/` were created rather than found, so their intent is stated instead of
recovered. *Decided* is the project owner closing a question this report had opened, which is a
stronger act and still not an ADR. Everything marked *Inferred* remains a guess, and nobody should
read an inference here as a decision that has been taken.

**Twelve components, counted by role rather than by directory.** `db/` is a container for five of
them and `sandbox/` for one. **`rag/` is counted as one component rather than two**, because it
stopped being "a BM25 index and a vector index" and became a seven-stage pipeline
([§3.6](#36-rag--the-retrieval-pipeline)). `agent-inbox/` was added in the previous revision, and
`vouch/` is added in this one ([§3.12](#312-vouch--agent-identity-and-the-broker)) — the first
directory in this layout that exists because of a ruling rather than a reading.

---

## 2. Correcting the record

The only existing mention of this folder is the 0.1.2 plan's §7 *Loose end*, and it describes a
folder that no longer exists:

| §7 says | Actually |
|---|---|
| `openswe/` | `open-swe/` |
| "six empty dirs plus two zero-byte files" | twelve components, 56 paths, all of them zero bytes |
| "untracked scaffolding… never committed" | **tracked from this commit**, structure preserved by `.gitkeep` |
| `bbpe/bbpe-codec.toon` | `rag/bbpe/tokenizer.json` — different name, different format, moved under `rag/` |
| names `langfuse`, `db/neo4j`, `db/clickhouse`, `bbpe` | adds `agent-inbox/`, `db/postgres`, `db/seaweedfs`, `db/valkey`, `langgraph/aegra/`, `sandbox/openshell/`, `vouch/`, and the seven `rag/` stages |

The drift is recorded rather than quietly overwritten, because §7 is the document a reader would
otherwise trust. Its instruction stands and this report is the first half of it: *"Either record
their intent or remove them before 0.1.3."*

---

## 3. The twelve components

### 3.1 `agent/` — Open SWE, and its interfaces

**Verified.** Open SWE is LangChain's coding agent, MIT licensed, copyright LangChain, Inc. Its
README now calls it *"an open-source software factory built on Deep Agents by LangChain"* — a
change from the "asynchronous coding agent" framing the 0.1.2 plan recorded.

Its `langgraph.json` declares exactly five graphs:

| Graph | Entrypoint | Does |
|---|---|---|
| `agent` | `agent.graphs.agent:traced_agent` | plans, implements, validates, opens the PR |
| `reviewer` | `agent.graphs.reviewer:traced_reviewer_agent` | read-only PR analysis |
| `analyzer` | `agent.graphs.analyzer:traced_analyzer` | learns a repository's review preferences |
| `chat` | `agent.graphs.chat:traced_chat_agent` | answers questions, changes no code |
| `scheduler` | `agent.graphs.scheduler:get_scheduler` | recurring tasks, CI monitoring |

**Four of the five entrypoints are a `traced_*` wrapper.** That is not decoration — it is the seam
observability attaches to, and it is why [§3.5](#35-langfuse--llm-observability) is a component
of this stack rather than an optional extra.

> **Corrected 2026-09-18.** This sentence read *"Every entrypoint is a `traced_*` wrapper"*, which
> the table directly above it contradicts: `scheduler` is `get_scheduler`. The error is worth
> leaving visible rather than quietly fixing, because it is the failure mode this report's own
> marker contract exists to catch — a generalisation written one line after the evidence that
> refutes it. It matters for [§3.5](#35-langfuse--llm-observability): if Langfuse is reached
> through those wrappers, the scheduler graph is not traced on this reading, and
> [P7](../implement/test-specup-agent-shape-assumptions.md#p7--do-the-traced_-wrappers-reach-langfuse-over-otlp)
> has to check it separately instead of generalising from the other four. Found by
> [P1](../implement/test-specup-agent-shape-assumptions.md#31--what-p1-found-that-it-was-not-looking-for),
> which was not looking for it.

Open SWE composes Deep Agents, which supplies planning, file operations, shell access, skills,
state and subagents. LangGraph supplies durable execution and thread state: *"each Open SWE
invocation executes as a LangGraph run within a thread."*

**It is not only a graph — it ships its own front ends**, and this is the fact that makes
[§5](#5-the-interface-layer--what-replaces-plane) possible. The repository root holds a `ui/`
workspace whose package is named `open-swe-dashboard` — a Vite and React application serving
alongside the API, *"Locally: `http://localhost:2024` serves the API and the dashboard"* — and a
`desktop/` client whose *"Packaged releases currently target macOS; source builds also support
Windows and Linux"*. Work can be started from five places:

| Surface | What the README says it does |
|---|---|
| Web dashboard | *"Start and continue tasks, inspect work, manage pull requests, and configure user or team settings"* |
| GitHub | *"Start tasks from issues, request changes from pull request conversations, run reviews, and continue work on the same branch"* |
| Slack | *"Start from a channel, thread, or code channel and receive progress and delivery updates in context"* |
| Linear | *"Invoke Open SWE from an issue and post results back to the issue"* |
| Desktop *(experimental)* | *"Run the same agent against local projects"* |

All five are MIT and all five are already built. The `oeps/` directory holds *"Open SWE
Enhancement Proposals"* for *"consequential product, architecture, security, and process
decisions"* — which is an ADR practice by another name, and worth noting in a project that has
one of its own.

**Inferred:** `agent/` holds a vendored or forked Open SWE, or the SpecUP-specific middleware and
prompts layered onto it. The 0.1.2 plan §7 names three extension points — `awrap_tool_call`
middleware, a sandbox backend, and the `AGENTS.md` already read into the system prompt — which is
consistent with either. The empty directory does not distinguish them, and the choice matters:
vendoring makes Open SWE's MIT notices a shipping obligation ([§7](#7-the-licence-position)).

### 3.2 `langgraph/` — Aegra and the Agent Protocol server

**Verified.** Aegra is an Apache-2.0 self-hosted Agent Protocol server, *"an open source
alternative to LangGraph Platform (now LangSmith Deployments)"*. It exists in this stack for one
reason: it delivers durable execution, a task queue and resumable runs **without
`langgraph-api`**, which is Elastic-2.0 and which `docs/dev/licensing.md` rules out.

Its dependencies were read directly: `langgraph`, `langgraph-sdk`,
`langgraph-checkpoint-postgres`, `redis[hiredis]` — and **none of `langgraph-api`,
`langgraph-runtime` or `langgraph-cli`**. Its own `docker-compose.yml` runs three services:
`postgres` on `pgvector/pgvector:pg18`, `redis` on `redis:7-alpine`, and `aegra` itself on uvicorn
at port 2026.

**The config filename is correct as it stands.** Aegra reads **`aegra.json`**, not
`langgraph.json`, and `langgraph/aegra.json` is what the folder contains. The schema is the same
shape as LangGraph's — `dependencies`, `graphs`, `http`, `store`, with each graph a
`path/to/module.py:variable` reference. Aegra's own file also carries a `store.scopes`
block, which LangGraph's does not, and which is how it separates one tenant's stored state from
another's.

> **Corrected 2026-09-18 by [P1](../implement/test-specup-agent-shape-assumptions.md#p1--do-open-swes-five-graphs-run-unchanged-under-aegra).**
> This paragraph said the five graphs *"transfer across with no change in content, only in
> filename"*. The content changes. Aegra splits a graph reference on `:` and treats the left side
> as a **file path** it resolves relative to the config file and then requires to exist;
> Open SWE's `langgraph.json` writes **module paths** — `agent.graphs.agent:traced_agent`. Under
> Aegra that resolves to a file named `agent.graphs.agent` and the load fails. Each of the five
> has to be rewritten as `.../agent/graphs/agent.py:traced_agent`, which is a change to
> `aegra.json` and so a file this stack owns — which is why P1 was still *answered* rather than
> falsified. Two further findings sit against this section: Open SWE's floor is Python **`>=3.14`**,
> above Aegra's `>=3.12`, and `langgraph-api` arrives transitively through Open SWE even though it
> does not arrive through Aegra. Both are in
> [§3.1 of the campaign](../implement/test-specup-agent-shape-assumptions.md#31--what-p1-found-that-it-was-not-looking-for).

**It supports human-in-the-loop and it speaks to existing clients.** Aegra lists
*"Human-in-the-loop — Approval gates and user intervention points"* among its features, ships
`react_agent_hitl` and `subgraph_hitl_agent` example graphs in its own `aegra.json`, and states
that it *"Works with Agent Chat UI, LangGraph Studio, and CopilotKit out of the box"* — a direct
consequence of implementing the Agent Protocol rather than a bespoke API. Its auth is
*"Configurable auth — JWT, OAuth, Firebase, or none"*. Both
[§3.3](#33-agent-inbox--the-explicit-decisions) and
[§5](#5-the-interface-layer--what-replaces-plane) rest on this.

**Inferred:** `langgraph/aegra/` holds the Aegra deployment — its compose fragment, migrations
and auth configuration — and `langgraph/aegra.json` is the graph manifest that points at the
Open SWE graphs in [§3.1](#31-agent--open-swe-and-its-interfaces).

Note also that Aegra's Postgres image is `pgvector/pgvector`. Vector search is therefore
available in the database the stack already requires — which is directly relevant to
[§3.6](#36-rag--the-retrieval-pipeline).

**Maturity remains an open risk.** Aegra publishes no production-readiness or stability
statement, and Agent Protocol v2 streaming is flagged as new. Adopting it trades *depending on a
licensed project* for *depending on a young one*. That trade should be recorded as a risk when
0.1.3 acquires requirements — not before, because a risk with nothing to threaten is a note.

### 3.3 `agent-inbox/` — the explicit decisions

**Specified.** This directory holds the deployment of LangChain's
[Agent Inbox](https://github.com/langchain-ai/agent-inbox) — **MIT**, self-hostable — as the one
place every explicit human decision in the system is queued, shown and answered.

**It does not add human-in-the-loop. HITL already exists**, and being precise about that is the
only way to say what this component is for:

| Where HITL already is | What it does |
|---|---|
| LangGraph | `interrupt()` pauses a graph mid-node, persists the payload to the checkpointer, and returns control to the caller; `Command(resume=...)` continues from the same checkpoint |
| Aegra | *"Approval gates and user intervention points"*, with two HITL example graphs shipped |
| Open SWE's dashboard | *"When Open SWE generates a plan, it interrupts and gives you the chance to accept, edit, delete, or request changes to the plan"* |

So the interrupts exist and a human can already answer them. **What does not exist is a single
enumerable list of them.** A plan approval today is a modal inside whichever run view somebody
happens to have open. Across five graphs, many concurrent threads and more than one repository,
"what is currently waiting on a human" is not a question the stack can answer.

**The schema is what makes a queue possible.** Agent Inbox reads a specific interrupt shape:

| Type | Fields |
|---|---|
| `HumanInterrupt` | `action_request`, `config`, `description` (markdown) |
| `ActionRequest` | `action` (the operation's name), `args` (its arguments) |
| `HumanInterruptConfig` | `allow_ignore`, `allow_respond`, `allow_edit`, `allow_accept` — four booleans |
| `HumanResponse` | one of **accept**, **edit**, **response**, **ignore** |

Those four booleans are the interesting part. **They are a per-decision permission set**, declared
by the graph at the moment it asks. A step can offer approval but forbid editing; it can allow a
free-text answer but not a silent skip. That is a finer-grained authority model than SpecUP
currently has anywhere, and it is declared in code rather than in a document.

**The inbox stores nothing.** Its connection settings — graph or assistant ID, deployment URL,
API key — *"are stored in your browser's local storage, and are only used to connect &
authenticate requests"*. The decision itself lands in LangGraph's checkpointer, which in this
stack is the PostgreSQL in [§3.7](#37-dbpostgres--the-most-required-service). **The inbox is a
view, not a store**, which is why adding it costs no service and creates no second source of
truth — the dashboard, the inbox and any Agent Chat UI client are three windows onto the same
interrupts.

#### Why this matters to SpecUP more than to anyone else

SpecUP's approval model has two provenance levels. `witnessed` means `approval.commit` resolves
and its signature verifies against `.specify/governance/allowed-signers`. `claimed` means a name
and a date, and nothing tying them to a person.

**An Agent Inbox decision is `claimed`.** It is a click in a browser, authenticated by whatever
Aegra was configured with. Aegra's JWT or OAuth identifies the caller; it does not sign the
content of the decision, and nothing binds the decision to a commit. So the stack would acquire a
stream of human decisions that look authoritative, sit in a database, and would not survive
`APV-002`.

That is not a reason to avoid the inbox. **It is the most valuable thing this component exposes**,
because it is the exact gap SpecUP exists to close, appearing in a place where closing it is
tractable: the decision has a defined schema, a known payload and a durable record. Turning one
into a witnessed approval needs the decision's content hashed, written to a reviewable file, and
bound to a signed commit.

**Decision 4 supplies the machinery for half of that and does not close it.** Vouch
([§3.12](#312-vouch--agent-identity-and-the-broker)) signs *the agent's* actions and binds them to
a resolvable identity, which is the half that was hardest. The human's click is still a click.
Worse, the two halves are easy to confuse: an inbox decision that an agent then acts on would
carry a verifiable signature — **the agent's** — and a reader who does not look closely would take
that signature for the human's. Naming that failure mode is the most useful thing this section can
do, and [§12.2](#122-the-eighteen-questions) questions 1 and 2 are where it belongs.

Note the symmetry with [§3.4](#34-sandboxopenshell--nvidia-openshell): OpenShell binds a
*policy* by hash and fails closed, so the agent cannot act outside what was approved. The inbox
records a *decision* and binds nothing. **One seam has the property SpecUP wants and the other
does not**, and they sit next to each other in the same run.

**Two caveats, both unverified and both real:**

- **Agent Inbox's connection form asks for a LangSmith API key.** Aegra is not LangSmith, and
  Aegra's own compatibility list names Agent Chat UI, LangGraph Studio and CopilotKit — **not
  Agent Inbox**. Whether the inbox authenticates cleanly against Aegra's JWT or OAuth has not
  been tested here. It is the first thing to try before this directory gets any content.
- **The overlap with Open SWE's dashboard is real.** If plan approval stays in the dashboard and
  everything else goes to the inbox, there are two places to look, which is the problem the inbox
  was added to solve. Deciding which surface owns which decision is part of adopting it.

### 3.4 `sandbox/openshell/` — NVIDIA OpenShell

**Verified.** [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) is **Apache-2.0** — read
from the repository's own `LICENSE` — and describes itself as *"the safe, private runtime for
autonomous AI agents"*. It replaces Docker Sandboxes in this layout, and the substitution is
better than a like-for-like swap: it is the same job under a licence that can be read, and it
brings two properties Docker's product does not expose.

**The isolation.** OpenShell *"isolates each sandbox in its own container with policy-enforced
egress routing"*, over Docker or Podman, with MicroVM-backed sandboxes available for a harder
boundary. Platforms are Linux, macOS on Apple Silicon, and Windows under WSL 2, marked
experimental. Sandboxes are created from a CLI — `openshell sandbox create -- <agent>` — or from
the Python SDK.

**The policy is a declarative YAML file**, and it covers four domains:

| Domain | What it controls | When it binds |
|---|---|---|
| Filesystem | *"Prevents reads/writes outside allowed paths"* | locked at sandbox creation |
| Process | *"Blocks privilege escalation and dangerous syscalls"* | locked at sandbox creation |
| Network | *"Blocks unauthorized outbound connections"* | hot-reloadable at runtime |
| Providers | *"endpoint-bound credentials and network access"* | hot-reloadable at runtime |

**And the policy is attested, by hash, and it fails closed.** This is the part that matters most
to SpecUP, and it is quoted rather than paraphrased:

> *"OpenShell binds the configured policy at creation and attests the authoritative effective
> policy source, content, hash, and active revision before exposing the execution backend."*

> *"current, active, revision, and effective-config versions must all be positive and agree with
> the exact submitted policy/hash; missing capabilities or any version disagreement fails
> closed."*

Read that against SpecUP's own approval model. `APV-002` verifies a signature over **content**,
so that an approval binds the bytes rather than a promise about them. OpenShell attests a hash
over the **policy**, so that an execution binds the rules rather than a claim that they were
applied. **They are the same idea at two layers**, and the stack did not have that property
before. The run also emits structured `sandbox.attestation` and `sandbox.cleanup` events, which
makes the binding a record rather than an assertion — the distinction the whole provenance
vocabulary rests on.

> **Corrected 2026-09-18 by `P2`, which measured this paragraph instead of believing it.**
> Two of the claims above do not survive contact with `0.0.116`.
>
> **The hash binds the submitted document, not the enforced ruleset.** Submitting a widened
> filesystem policy to a *live* sandbox is accepted — new version, new hash, `policy get` reporting
> `status: effective`, `policy list` marking the previous version `Superseded` with no error — while
> the kernel goes on enforcing the old one. The quoted guarantee says *"any version disagreement
> fails closed"*, and nothing fails closed here because **every version agrees**; they simply agree
> on a document the ruleset does not match. `policy get` returns a hash, a status and no filesystem
> lists at all, so the attestation can be compared and never inspected. It is still a record — of
> what was submitted.
>
> **And on the shipped release the attested policy did not stop the write it existed to stop.**
> Appending to `.specify/governance/allowed-signers` is denied; `truncate(2)` on it succeeds, and
> the file went from 2732 bytes to 0. The sandbox's own attestation names the cause in two
> adjacent lines — `CONFIG:PROBED abi:v8` then `CONFIG:APPLYING abi:V2` — the host offered
> Landlock ABI 8 and the ruleset was built at 2, which predates `LANDLOCK_ACCESS_FS_TRUNCATE`.
>
> *Amended 2026-09-19.* Re-run against OpenShell's rolling `dev` build
> (`0.0.117-dev.204+ge38d7254e`), which builds at `ABI::V3`, the same `truncate(2)` returns
> **`EACCES`** and the file is untouched. So the enforcement point is real, above a version floor
> that **no stable release reaches**. Two things did not improve with it. The widening behaviour
> above is unchanged — a `read_write` addition over a `read_only` subtree is still accepted and
> still reported `Effective` while the kernel enforces the old ruleset. And the `dev` build
> **stopped printing the ABI**: `CONFIG:APPLYING abi:V2` is replaced by
> `Isolation boundary attached backend=openshell-sandbox`, and a search of the whole sandbox log
> for `abi` or `landlock` returns nothing. The line that diagnosed this defect no longer exists,
> so the attestation cannot tell you whether truncation is covered and only a behavioural test
> can. *(The one direction that would be dangerous is refused: removing a `read_write` path from
> a live sandbox fails with `InvalidArgument` and records no version. Tested on `dev` only.)*
>
> The comparison with `APV-002` is still the right one, and it now cuts the other way too: a hash
> over bytes nobody re-reads, and a policy over an access right the kernel was never asked to
> withhold, fail in the same shape. See
> [campaign §3.3](../implement/test-specup-agent-shape-assumptions.md#33--what-p2-found-and-what-the-answer-is-conditional-on).

> **Measured 2026-09-19 by `P4` — the egress half, which this section had not examined.** The
> filesystem policy is only one of two. Every sandbox is a container on a private veth whose only
> reachable host port is a **transparent L7 proxy** (`http_proxy=http://10.200.0.1:3128`, with an
> OpenShell CA injected at `/etc/openshell-tls/`), and `network_policies` names the endpoints that
> proxy will serve — host, port, protocol, and for `protocol: rest` the permitted methods.
>
> **It is enforced at the network layer, not by the environment variable.** Unsetting
> `http_proxy` and connecting straight to the host fails rather than escaping; an unlisted port on
> a listed host returns `{"error":"policy_denied"}`. That is the property the filesystem half was
> found lacking above, present here.
>
> **And `binaries` attributes egress to the executable that asks for it**, so an endpoint can be
> reachable by one program in the sandbox and by nothing else. Neither this report nor the shape
> document had that control, and it is the right primitive for a signing endpoint.
>
> One caution that follows from the design rather than a defect: the proxy terminates TLS with its
> own CA, so **OpenShell sees the plaintext of every request a sandbox makes**, credentials
> included. That is how L7 rules are possible at all, and it means the proxy is in the trust
> boundary for everything the agent sends.

**The Deep Agents provider already exists**, which is the practical difference from the previous
plan. Deep Agents documents eight backends, and NVIDIA OpenShell is one of them:

```python
from langchain_nvidia_openshell import OpenShellSandbox
import openshell

with openshell.Sandbox(delete_on_exit=True) as sandbox:
    backend = OpenShellSandbox(sandbox=sandbox)
    result = backend.execute("python3 --version")
```

`pip install langchain-nvidia-openshell`, and the protocol is satisfied. **There is no Docker
backend to write.** The 0.1.2 plan's finding that a SpecUP sandbox backend would be "genuinely
additive and plausibly upstreamable" was true of Docker and is not true here — the work drops
from *implement a provider* to *configure one and write the policy*.

The protocol it satisfies is still unusually small, and that is why this component can enforce
anything:

> *"The only method a provider must implement is `execute()`, which runs a shell command and
> returns its output."*
> *"Every other filesystem operation (`read`, `write`, `edit`, `delete`, `ls`, `glob`, `grep`) is
> built on top of `execute()` by the `BaseSandbox` base class."*

So the agent's tools split three ways, and OpenShell's egress gateway narrows the ungoverned set
further than a plain container could:

| | Tools | Enforced by |
|---|---|---|
| Routes through `execute()` | `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`, `execute` | **filesystem and process policy** — one chokepoint, locked at creation |
| Network egress | `http_request`, `fetch_url`, `web_search` | **the policy-enforced egress gateway** — it intercepts outbound connections below the agent |
| Semantic actions | `commit_and_open_pr`, `request_pr_review`, `task` | **a middleware broker** — `awrap_tool_call`, or Vouch Shield ([§3.12](#312-vouch--agent-identity-and-the-broker)), which the agent's own code path must honour |

The first two rows are enforcement. The third is interception, which is weaker, and the
difference should be stated in exactly those terms wherever SpecUP claims the agent is contained.
Network policy answers *which host*, not *which operation*: allowing egress to `github.com` does
not distinguish opening a pull request from force-pushing over a branch. The broker gets smaller
under OpenShell; it does not disappear.

**Decision 4 names something that fills that row**, which is new since the previous draft. Vouch
Shield evaluates `action` + `target` + `resource` against a rules file, denies by default, and
raises before the tool body runs. It is still interception rather than containment — the agent's
own process performs the check — but it is interception with a written policy and a stated
fail-closed guarantee, rather than a broker that does not exist.

**The cost is maturity, and it is the same shape as Aegra's.** OpenShell is badged **alpha**, its
Kubernetes deployment is *"Experimental — under active development"*, and the AI-Q blueprint
pins behaviour to a specific build (`0.0.80`). Docker Sandboxes is the more finished product;
this is the more inspectable one. **That trade is now explicit rather than accidental**, which is
the only thing this report can usefully do about it.

**Inferred:** `sandbox/openshell/` holds the YAML policy and the sandbox image definition. If
that is right it is the most interesting directory in the layout for SpecUP's purposes — see
[§10](#10-where-this-argues-with-specup-as-it-stands), because it is the one artifact here that
*agrees* with filesystem authority instead of arguing with it.

### 3.5 `langfuse/` — LLM observability

**Verified.** Langfuse is an LLM observability, evaluation and prompt-management platform. Its
core is MIT; modules under `ee/`, `web/src/ee/` and `worker/src/ee/` are commercially licensed
and need a key. The EE set is enterprise governance — project-level RBAC, audit logs, SCIM, data
retention, server-side masking, UI customisation. **None of the tracing that this stack wants is
EE.**

It integrates with LangGraph through LangChain callbacks, or as an OpenTelemetry backend — and
[§5.2](#52-opentelemetry-is-not-a-ui-and-you-should-adopt-it-anyway) argues the second route is
the one to take.

**Two facts that a reader should not miss:**

1. **Langfuse's `LICENSE` is copyright ClickHouse, Inc.** ClickHouse acquired Langfuse in January
   2026. So [§3.9](#39-dbclickhouse--the-analytical-store) and this component are now **one
   vendor**, not two — see [§7.4](#74-vendor-concentration).
2. **Self-hosting Langfuse v3 requires four backing services**, not one: Postgres, ClickHouse,
   Redis/Valkey, **and an S3/blob store**. The blob store is not optional — *"all incoming
   tracing and evaluation events are persisted in S3/Blob Storage first,"* which is the basis of
   its recoverability design. `db/seaweedfs` is where it lands
   ([§3.11](#311-dbseaweedfs--the-blob-store)).

**Inferred:** `langfuse/` holds the self-hosted deployment config, and the `traced_*` entrypoints
in [§3.1](#31-agent--open-swe-and-its-interfaces) are pointed at it instead of LangSmith. That
inference is stronger than most in this document, because the alternative — LangSmith — is the
hosted product this stack is built to avoid.

**Langfuse is now the only web application in the stack that SpecUP would deploy itself**, since
Plane is gone and both Open SWE's dashboard and the Agent Inbox ship as static front ends. That
makes it the de facto operator console as well as the trace store, which is a role it is well
suited to and was not chosen for.

### 3.6 `rag/` — the retrieval pipeline

**Specified.** `rag/` was two directories and is now seven stages. The reason is that a BM25
index and a vector index are not a retrieval system — they are two of its parts, and the parts
that were missing are the ones that decide whether it works. What follows is a local,
self-hosted, state-of-the-art pipeline for **code** retrieval, in the order data flows through
it.

**The shape is not invented.** Anthropic's published contextual-retrieval results measure each
addition against the same corpus, and they are the argument for this specific ordering:

| Pipeline | Reduction in retrieval failures |
|---|---|
| Contextual embeddings alone | **35%** |
| Contextual embeddings + BM25 | **49%** |
| …plus reranking | **67%** |

Each stage below is a directory because each is a separate decision with a separate cost. A
stage with no directory is a stage that gets assumed.

| Stage | Directory | What it is |
|---|---|---|
| 1. Chunk | `chunk/cast/` | tree-sitter AST chunking, so a function is never cut in half |
| 2. Contextualise | `chunk/contextual/` | an LLM pass that prefixes each chunk with where it sits — **SpecUP's configured provider** ([decision 7](#121-decisions-taken)) |
| 3. Tokenise | `bbpe/` | one byte-level BPE tokenizer, shared by every stage |
| 4. Embed | `embed/qwen3-embedding/` | the dense vectors — a local model, **fetched at install, never shipped** ([decisions 3 and 5](#121-decisions-taken)) |
| 5. Index | `index/bm25s/`, `index/ann/{hnsw,ivf}/` | lexical and dense indexes — **a local library, split by corpus** ([decision 2](#121-decisions-taken)) |
| 6. Fuse | `fuse/` | reciprocal rank fusion over the two result lists |
| 7. Rerank | `rerank/qwen3-reranker/` | a cross-encoder over the fused top-k — local, fetched the same way |
| — | `eval/coir/`, `eval/golden/` | the harness that says whether any of it helped |

Structural retrieval is the fourth arm and it is not here, because it is a service rather than an
artifact: it lives in [§3.10](#310-dbneo4j--the-graph-store).

**Four of the ten decisions land in this one component, and together they change what "local"
means here.** `rag/` is a library rather than a service ([decision 2](#121-decisions-taken)); its
two model stages run on the host and their weights are downloaded rather than distributed
([decisions 3 and 5](#121-decisions-taken)); and stage 2 calls out to whichever provider SpecUP is
configured with ([decision 7](#121-decisions-taken)).

So the honest description is **not** "a local retrieval pipeline". It is *a local retrieval
pipeline with one remote stage at index time* — and that stage reads the source it is indexing.
[§3.6.2](#362-chunkcontextual--the-35) is where that cost is stated rather than buried, because it
is the kind of detail that is true in the design, forgotten in the README, and discovered by a
customer's security review.

#### 3.6.1 `chunk/cast/` — structure-aware chunking

**Verified.** cAST is *"cAST: Enhancing Code Retrieval-Augmented Generation with Structural
Chunking via Abstract Syntax Tree"* (Zhang, Zhao, Wang, Yang, Wei, Wu). It recursively splits
large AST nodes and merges sibling nodes within a size budget, so chunk boundaries fall on
complete syntactic units. The reported gains are **+4.3 Recall@5 on RepoEval** and **+2.67 Pass@1
on SWE-bench**.

The paper's framing of the problem is the reason this stage exists at all:

> *"existing line-based chunking heuristics often break semantic structures, splitting functions
> or merging unrelated code, which can degrade generation quality."*

Four design goals are worth keeping when this is implemented: syntactic integrity, high
information density, language invariance — no per-language heuristics — and **plug-and-play
compatibility, meaning concatenating the chunks reproduces the original file verbatim.** That
last property is the one that makes chunking auditable, and it is the kind of invariant this
repository would normally write a check for.

`tree-sitter` is **MIT**; the reference implementation `astchunk` is **MIT**. Neither imposes
anything.

#### 3.6.2 `chunk/contextual/` — the 35%

**Verified.** Anthropic's contextual retrieval prefixes every chunk with a short, generated
description of where it sits in its document before the chunk is embedded and indexed, so a chunk
that says `return self._cache[key]` stops being unattributable. The measured effect is the first
row of the table above, and it is the largest single gain in the pipeline.

**It is also the only stage with a recurring model cost**, and that has to be said plainly: it
runs an LLM over every chunk at index time, and again over every chunk that changes. For a large
repository that is the dominant cost of building the index. The cost is bounded by prompt caching
and by only re-contextualising what changed, and neither of those is free to implement.

**Decided — this stage uses the provider SpecUP is already configured with, which is Claude.**
It does not get a model of its own. The reasoning is the same one that makes the rest of the
pipeline local: a second generative model would be a second serving budget, a second set of
weights, a second thing to keep current, and a second place for quality to drift — to do a job the
project already pays a provider to do well.

Three consequences follow, and the third is the one that gets forgotten:

| Consequence | Detail |
|---|---|
| **No local generative model** | `rag/` runs two local models — the embedder and the reranker — and both are encoders. Nothing in the retrieval layer generates text on the host, which removes the largest single hardware requirement the pipeline could have had |
| **The cost is provider spend, not capex** | It scales with the repository and with churn, it appears on a bill somebody already receives, and it is measurable before it is committed to. That is a better shape of cost than a GPU, and it is still a cost |
| **The source code leaves the network** | Contextualising a chunk means sending that chunk to the provider. For a customer who adopted a self-hosted stack *in order to* keep source in-house, this is the one stage that does not honour that, and it must be a switch they can see rather than a default they discover |

**That third row also crosses [§3.4](#34-sandboxopenshell--nvidia-openshell)'s egress boundary.**
Whatever runs the indexing job needs outbound access to the provider API and a provider credential
— so the two things OpenShell's policy is strictest about are both required by stage 2, and the
indexer is therefore not simply another process inside the sandbox.

**The directory survives the decision, and for the original reason:** whether to contextualise at
all is still the sharpest cost-versus-quality trade in the retrieval layer. Burying it in a config
key is how it gets switched off for a deadline and never switched back.

#### 3.6.3 `bbpe/` — one tokenizer, everywhere

**Verified.** Byte-level BPE tokenises UTF-8 bytes, so it has no out-of-vocabulary failure mode —
which is why it suits source code, identifiers and mixed natural language. `tokenizer.json` is
the serialised form used by the HuggingFace `tokenizers` library.

**Inferred:** it is shared rather than per-stage. The chunker measures its size budget in tokens,
`bm25s` segments with it, and the embedding model has its own. Keeping one definition is what
makes a lexical hit and a dense hit refer to the same span of the same file; letting them drift
is a class of retrieval bug that is very hard to see from the results.

#### 3.6.4 `embed/qwen3-embedding/` — the model that was missing

**Verified.** **Qwen3-Embedding** is **Apache-2.0**, read from the model card. It has a **32K
context**, supports **user-defined output dimensions from 32 to 1024** — Matryoshka truncation,
so index size is a tuning parameter rather than a property of the model — accepts **task
instructions** to steer retrieval, and covers *"over 100 languages"* including *"various
programming languages"* with *"robust multilingual, cross-lingual, and code retrieval
capabilities"*. The 8B variant reports 70.58 on MTEB multilingual.

**Specified, and the directory name records a recommendation rather than a decision.** Two
permissive alternatives are worth knowing, and swapping to either is a rename:

| Alternative | Licence | When it wins |
|---|---|---|
| `nomic-embed-code` (7B) | Apache-2.0 | A dedicated code embedder — *"Outperforms Voyage Code 3 and OpenAI Embed 3 Large on CodeSearchNet"*, 81.7 on Python. Larger and slower to serve |
| `bge-m3` family | permissive | Long-established multilingual baseline with good tooling |

**And one that must not be used here:** EmbeddingGemma is small, fast and frequently recommended,
and it is under Google's **Gemma terms**, not an OSI licence — see
[§7.2](#72-model-weights-carry-licences-too-and-the-good-ones-often-forbid-you).

##### How the weights arrive — decisions 3 and 5, and they apply to §3.6.7 too

**Decided. SpecUP ships no model weights, and nothing else that can be fetched from the
internet.** A directory named after a model holds the *reference* to it — repository id, revision,
and the command that fetches it — and never the file. Two reasons, and both are load-bearing:

- **Redistribution obligations do not attach to a pointer.** [§7.2](#72-model-weights-carry-licences-too-and-the-good-ones-often-forbid-you)
  describes what shipping weights would cost: their terms join a `NOTICE`, and every customer
  receives them from SpecUP rather than from the model's author. Fetching moves the licence
  acceptance to the party that runs the model, which is where it belongs and where the Hugging Face
  gate already puts it.
- **A repository is not a binary store.** Qwen3-Embedding-0.6B is roughly a gigabyte; the 7B
  alternatives are an order more. A governance tool whose whole argument is that artifacts should
  be diffable and reviewable has no business carrying files that are neither.

**The mechanism is `uv` and the Hugging Face library, for consistency with the rest of SpecUP's
tooling** — the project already resolves Python through `uv`, so the model fetch uses the same
resolver rather than introducing a second one:

```bash
uvx hf download Qwen/Qwen3-Embedding-0.6B --revision <pinned-sha>
```

**Verified:** `huggingface_hub` is **Apache-2.0**; the CLI is now `hf`, not `huggingface-cli`; the
Hugging Face documentation names `uvx hf` as *"the easiest way to use the `hf` CLI"*; and downloads
land in the cache at `HF_HOME`, defaulting to `~/.cache/huggingface/hub/`, with `--cache-dir` as
the override. That cache location matters more than it looks: it is outside the repository, so a
fetched model cannot be committed by accident, and it is a path OpenShell's filesystem policy has
to allow explicitly if the model is served from inside a sandbox.

**Two things this decision makes mandatory rather than optional.** A revision must be **pinned to a
digest**, because `main` on a model repository is a moving target and an unpinned fetch makes the
retrieval quality of a build unreproducible in a way no test will catch. And the install acquires a
**network dependency**: a clean install of SpecUP's retrieval layer cannot complete offline. An
air-gapped customer needs a documented mirror path, which is the honest cost of not shipping the
files.

**Serving it needs no directory of its own.** Text Embeddings Inference (**Apache-2.0**),
Infinity (**MIT**), llama.cpp (**MIT**) and Ollama (**MIT**) all serve embedding and reranking
models, and one process can serve both this stage and §3.6.7. The serving config belongs inside
these model directories; inventing a `serve/` directory would imply a component that is one
container running two models.

> **Corrected 2026-09-19 — "one process can serve both" is true, and the four runtimes are not
> interchangeable for it.** P5 measured a single Infinity process serving an embedder and a
> reranker at one pid and 3337 MiB. **TEI cannot do this**: its usage line is
> `text-embeddings-router [OPTIONS] --model-id <MODEL_ID>`, singular and required — one model per
> process. Infinity's help states the opposite capability directly: *"cli options can be
> overloaded i.e. `v2 --model-id model/id1 --model-id model/id2`"*. The sentence above listed
> four runtimes as equivalent on the strength of all four serving both **kinds** of model, which
> is not the same claim as serving two models **at once**. Whichever runtime is chosen also
> constrains which reranker can be loaded — see the amendment in
> [§3.6.7](#367-rerankqwen3-reranker--the-last-18-points).

#### 3.6.5 `index/bm25s/` and `index/ann/` — lexical and dense

**Verified.** `bm25s` is a BM25 implementation under **MIT** (copyright Xing Han Lu) depending
only on NumPy and SciPy. It computes BM25 scores eagerly at index time into sparse matrices,
reporting up to 500× the throughput of `rank-bm25` at query time. `corpus.jsonl` is its standard
corpus input format.

`hnsw` and `ivf` are the two dominant families of approximate nearest-neighbour index, and they
are not variants of each other:

| | HNSW | IVF |
|---|---|---|
| Structure | a multi-layer proximity graph, *"a hierarchical set of proximity graphs (layers) for nested subsets of the stored elements"* | a coarse quantiser partitions vectors into lists; a query probes the nearest few |
| Origin | Malkov & Yashunin, *Efficient and robust approximate nearest neighbor search using HNSW graphs* | Jégou, Douze & Schmid, *Product Quantization for Nearest Neighbor Search*, IEEE TPAMI 2011 — the IVFADC method |
| Search cost | logarithmic in the index size | linear in the number of probes |
| Build cost | high — roughly 5–6× IVF on the same corpus | low |
| Memory | high — around 2.8× IVF at matched recall | low |
| Updates | tolerates them | *"not resilient to index updates in terms of recall"*; needs rebuilding |

**Decided, and it settles the largest open question in the previous draft.** That draft asked
whether `index/ann/` was pgvector or a local library, and read the directory names as pgvector's
two index methods — *"the strongest inference in this section"*. **The ruling is that `rag/` is a
local library.** The inference is recorded here rather than deleted, because it was the load-bearing
guess in §3.6 and a reader who saw it should be able to see what replaced it.

**And the split between the two directories is by corpus, not by algorithm preference:**

| Directory | Holds the index for | Why that index |
|---|---|---|
| `index/ann/ivf/` | **Static binding documents** — ADRs, contracts, API specifications, standards, anything normative that is written once and then cited | This corpus is *frozen by nature*. IVF's documented weakness is that it is *"not resilient to index updates in terms of recall"* and needs rebuilding — which costs nothing for a corpus that does not change between releases. In exchange it takes roughly a fifth of HNSW's memory and builds five to six times faster |
| `index/ann/hnsw/` | **Code** — the repository being worked on, and whatever else churns | A code index is rewritten on every commit. HNSW tolerates incremental updates, which is exactly the property IVF lacks, and it pays for that with memory and build time |

**This is the right shape of reason for choosing an index**, and it is worth saying why: the two
algorithms are being matched to the *update rate of the data*, which is the property they actually
differ on, rather than to a benchmark score. The property that makes IVF a poor fit for code is the
same property that makes it free for a corpus of signed-off documents.

**Two consequences the layout now commits to.**

- **The vectors are files, not rows.** They live beside the process that built them rather than in
  the PostgreSQL that Aegra and Langfuse require. That keeps retrieval independent of the database
  — the pipeline can be rebuilt, moved or thrown away without a migration — and it gives up
  Postgres's backups, transactions and single restore path for the index. It also makes
  [§3.11](#311-dbseaweedfs--the-blob-store)'s second consumer real rather than conditional: built
  indexes are large binary artifacts that are expensive to rebuild and unwanted in git.
- **pgvector is no longer needed for retrieval**, although it arrives anyway — Aegra's compose pins
  `pgvector/pgvector:pg18`, so the extension is present and simply unused by `rag/`. That is worth
  recording so nobody later reads its presence as a design.

**Which library is not decided.** FAISS covers both families in one dependency — `IndexHNSWFlat`
and `IndexIVFFlat` — which is the obvious fit for two directories that must be built by the same
code; `hnswlib` and `usearch` are narrower and only cover the first. That choice belongs in
[§12.2](#122-the-eighteen-questions).

**No licence exposure on any route.** FAISS is MIT; `hnswlib` and `usearch` are Apache-2.0;
pgvector is under the PostgreSQL License. All four were read from their own `LICENSE` files.

#### 3.6.6 `fuse/` — reciprocal rank fusion

**Verified as a method.** Reciprocal rank fusion combines ranked lists by summing
`1 / (k + rank)` across them. It uses **only ranks**, which is precisely why it suits this
pipeline: BM25 scores are unbounded and cosine similarities sit in [-1, 1], so score-level
fusion needs a normalisation that has to be tuned per corpus and silently rots. RRF needs none.
The standard reference is Cormack, Clarke & Buettcher, *Reciprocal Rank Fusion outperforms
Condorcet and individual Rank Learning Methods*, SIGIR 2009 — cited bibliographically here and
not re-fetched this session, which is marked because the rest of this report's citations were.

Fusing BM25 with dense retrieval *"improves over both constituent methods across all metrics"*,
and it is the step that takes Anthropic's measured failure reduction from 35% to 49%.

**Specified, and it is a directory for one formula deliberately.** RRF has one parameter, `k`, and
an optional per-list weight. Both are retrieval-quality decisions that change results measurably
and get made once, by whoever writes the first version, and then never revisited. A directory
with an evaluation beside it ([§3.6.8](#368-eval--the-part-that-makes-the-rest-honest)) is what
turns that into a decision.

#### 3.6.7 `rerank/qwen3-reranker/` — the last 18 points

**Verified.** **Qwen3-Reranker** is **Apache-2.0**, read from the model card: 0.6B parameters,
28 layers, **32K context**, instruction-aware, and used as a cross-encoder scoring query–document
pairs directly rather than comparing independent embeddings. It is the stage that takes
Anthropic's measured failure reduction from 49% to **67%**.

**Why a cross-encoder is a different thing from the retriever:** an embedding model encodes query
and document separately and can only compare the results, which is what makes an ANN index
possible. A cross-encoder reads both together and is far more accurate and far too slow to run
over a corpus. Running it over the fused top-k is the whole trick.

**Its weights arrive the same way the embedder's do** — `uvx hf download`, pinned to a revision,
cached outside the repository, never committed and never shipped. The full statement is in
[§3.6.4](#364-embedqwen3-embedding--the-model-that-was-missing).

**The permissive alternative is `bge-reranker-v2-m3`** — **Apache-2.0**, 0.6B, built on bge-m3,
multilingual, and the usual lightweight default. ~~Its documented usage truncates at **512
tokens**, against Qwen3-Reranker's 32K, and for code that difference is not academic: 512 tokens
is a medium-sized function.~~ **Corrected 2026-09-19 — see the amendment below. The window is
8192, and 512 was a number in a code snippet.**

> **Amended 2026-09-19, and this is no longer the alternative — it is the candidate.** P5 tried
> to serve `Qwen3-Reranker-0.6B` from the model server this stack specifies and **could not**.
> The model declares `architectures: ["Qwen3ForCausalLM"]`, and Infinity selects a reranker only
> when `"SequenceClassification"` appears in that list
> (`infinity_emb/inference/select_model.py:47`), with no flag to override. Below Infinity's own
> `sentence-transformers` pin the server will not start, because the model's `modules.json`
> names v5-only module classes; above it the server starts, loads the model in the same process
> — and registers it as an **embedder**, so `/rerank` returns HTTP 400.
>
> This is a **packaging** mismatch and not a judgement on the model: `Qwen3-Reranker` is a
> causal-LM reranker scored from yes/no logits, and the generic cross-encoder loaders every
> permissive serving runtime uses expect a classification head. `bge-reranker-v2-m3` is
> `XLMRobertaForSequenceClassification` and matches.
>
> ~~**So the 512-token cost named above now has to be paid, or the serving runtime has to
> change**~~ — the second option is still real, because
> [§12.1 decision 7](#121-decisions-taken)'s "one process serves both" is the thing that made
> TEI unusable in the first place. That is a decision with a measured cost on both sides, which
> means an ADR. The full record is in
> [campaign §3.4](../implement/test-specup-agent-shape-assumptions.md#34--what-p5-found-and-the-reranker-that-has-to-be-replaced).
>
> **Corrected 2026-09-19 by running the replacement — there is no 512-token cost, and this
> report invented it by reading a snippet as a specification.** `bge-reranker-v2-m3` declares
> `max_position_embeddings: 8194` and `model_max_length: 8192`; it is built on `bge-m3`, which is
> the *long-context* model. The model card's example passes `max_length=512`, which is a caller's
> parameter. Tested with the answer placed beyond token 512: at `max_length=512` the
> answer-bearing and answer-free documents score **identically** (−10.6261, the answer is
> invisible); at 8192 they score **+5.0365 against −3.3194**. The window is **8192 against
> Qwen3-Reranker's 32K** — a factor of four, not sixty-four.
>
> **The cost that is real is latency.** Served from the same single Infinity process as the
> decided embedder, the pair occupies **4186 MiB** and reranks four documents in **6.79s cold and
> 3.06s warm** on four AVX2 cores at `float32`, against 0.08s for the small cross-encoder. Cold
> start to ready was 207s. A pipeline that reranks on every query has to answer for that, and
> that — not the context window — is what the ADR decides.

**And the one to avoid is the one most likely to be recommended.** `jina-reranker-v3` is a 0.6B
model with a 131K window reporting **61.94 nDCG@10 on BEIR**, state of the art among open-weight
rerankers — and it is **CC BY-NC 4.0, non-commercial**
([§7.2](#72-model-weights-carry-licences-too-and-the-good-ones-often-forbid-you)).

#### 3.6.8 `eval/` — the part that makes the rest honest

**Specified, and this is the directory this repository has the least excuse to omit.** Every gain
quoted above is somebody else's number on somebody else's corpus. None of them is evidence about
this stack until it is measured here.

| Directory | What goes in it |
|---|---|
| `eval/coir/` | **CoIR** — *"designed to evaluate code retrieval capabilities"*, **10 curated code datasets, 8 retrieval tasks across 7 domains, two million documents**. The toolkit is **Apache-2.0**; the paper is arXiv 2407.02883, ACL 2025 Main |
| `eval/golden/` | The project's own labelled queries. A public benchmark says the pipeline is competent in general; only a local set says it finds the right file in *this* repository |

Without this stage every earlier claim in §3.6 is inherited rather than established — which is
the same failure mode `.specify/traceability/index.md` records about SpecUP's own graph, where
84% of the edges are assertions nothing can confirm. **A retrieval pipeline with no evaluation is
a graph with no derived edges.**

### 3.7 `db/postgres` — the most-required service

**Verified.** PostgreSQL is under the PostgreSQL License, a permissive licence of the BSD/MIT
family. It imposes nothing on this project.

Its consumers, after the tracker was removed:

| Consumer | Uses it for | Consequence if it is lost |
|---|---|---|
| Aegra | run checkpoints, thread state, **and every pending HITL interrupt** | a run cannot resume, and every queued human decision is lost |
| Langfuse | transactional state beside ClickHouse | the UI and configuration |
| `rag/index/ann` | dense vectors, under the `pgvector` reading of §3.6.5 | the dense arm of retrieval |

**Inferred:** one cluster, two databases. They cannot share a schema — Langfuse runs its own
migrations — so the shared object is the server, not the database.

Aegra's own compose pins `pgvector/pgvector:pg18`, so if this instance is the one Aegra uses it
carries `pgvector` too, and the dense index has somewhere to live without another container.
**That is an inference about intent, not a design** — but it is the reading under which the whole
retrieval layer collapses into services the stack already runs.

This is also where [§10](#10-where-this-argues-with-specup-as-it-stands)'s sharpest conflict
lands, and [§3.3](#33-agent-inbox--the-explicit-decisions) sharpened it: this cluster now holds
**human approval decisions**, not only execution state. That is governance data in a store that
cannot be diffed or reviewed.

### 3.8 `db/valkey` — the shared cache and queue

**Verified.** Valkey is a Linux Foundation fork of Redis 7.2.4 under **BSD-3-Clause**, created
after Redis moved to SSPL/RSALv2 in March 2024. It is wire-compatible: existing Redis clients,
libraries and configs work unchanged.

Two components ask for Redis — Aegra for its job queue and SSE pub/sub, Langfuse for its cache
and queue. Redis's own licence is neither open source nor compatible with a clean redistribution
story. Valkey satisfies both at BSD-3.

**Inferred:** one instance serves both, separated by database index or key prefix.

### 3.9 `db/clickhouse` — the analytical store

**Verified.** ClickHouse is a column-oriented OLAP database under **Apache-2.0**. It is where
Langfuse v3 keeps traces, observations and scores; the Postgres-only architecture of Langfuse v2
was replaced because it did not hold up at ingestion volume.

**Inferred:** `db/clickhouse` exists **for Langfuse and for nothing else.** Nothing else in the
layout is an analytics consumer. If that is right, it is not an independent choice at all — it is
a transitive dependency of §3.5, and the two live or die together.

### 3.10 `db/neo4j` — the graph store

**Verified.** Neo4j Community Edition is **GPL-3.0**. Its `LICENSE.txt` also carries an explicit
dual-licensing clause: if you hold a *"Commercial Agreement"* with Neo4j, *"the terms of the
license in such Commercial Agreement will supersede the GNU GENERAL PUBLIC LICENSE Version 3."*
So paying is a documented route out. Enterprise Edition is commercial-only and is no longer
published to GitHub.

**Decided — SpecUP speaks Bolt, and ships no graph server.** Everywhere in SpecUP that talks to a
graph, it talks over the Bolt protocol to an instance somebody else runs. That is the whole
ruling, and it is smaller and better than the substitution the previous draft recommended, because
it removes the licence question without removing the tool.

| | |
|---|---|
| **What SpecUP ships** | A Bolt client. The official Neo4j drivers are permissive — the Python package declares **`Apache-2.0 AND Python-2.0`**, and its `LICENSE.txt` reads *"Unless stated otherwise, this software is distributed under the terms of the Apache License 2.0"*, with `LICENSE.PYTHON.txt` covering the parts that are not. There is a `NOTICE.txt`, so Apache attribution applies the moment anything is redistributed |
| **What SpecUP does not ship** | The server. No image is published, no source is vendored, no appliance bundles it. GPL-3.0 reciprocity attaches to distributing Neo4j, and SpecUP distributes none of it ([decision 1](#121-decisions-taken)) |
| **What the customer chooses** | Community Edition under GPL-3.0, a commercial agreement, Aura, or another Bolt-speaking server entirely. That is their decision about their own deployment, taken with their own counsel |

**One correction to the premise, because it is the kind of thing that gets repeated.** The
*drivers* are Apache-2.0. The **Bolt specification documentation is not** — `neo4j/docs-bolt`
carries `LICENSE.txt` reading *"Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International (CC BY-NC-SA 4.0)"*, copyright Neo4j Sweden AB. That restricts **copying or adapting
the specification text**; it does not restrict speaking the protocol through an Apache-2.0 driver,
which is what this decision does. The practical rule is one line: **use the driver, do not vendor
the docs.**

**And the specification's licence moved, which is worth recording rather than absorbing.**
`boltprotocol.org` — the independent address the specification was published at — now
**301-redirects to `neo4j.com/docs/bolt`**, verified this session. AWS's Neptune documentation still
describes Bolt as *"licensed under the Creative Commons 3.0 Attribution-ShareAlike license"* and
links to that old address. The current repository file says CC BY-NC-**SA** 4.0, which adds a
**NonCommercial** term the licence AWS cites did not have. **Which publication governs which
artifact is not resolved here**, and this report does not invent an answer: what is verified is the
repository file and the redirect. The practical rule above is unchanged and is better founded for it.

**Bolt is a wire, and that is what makes this more than a licence manoeuvre.** Memgraph implements
Bolt and documents the Neo4j drivers as the recommended way to reach it; since Memgraph 2.11 its
`--bolt-server-name-for-init` default is compatible with the Neo4j driver, so no configuration is
needed. **And Amazon Neptune speaks Bolt too** — AWS documents connecting with the Neo4j drivers by
*"simply replac[ing] the URL and Port number with your cluster endpoints using the `bolt` URI
scheme"*. So the same client reaches **three** servers across three licensing and operating models:
GPL-3.0 self-hosted, BSL self-hosted, and a managed cloud service. The graph is the one component in
this stack a customer can substitute without SpecUP changing, and the substitution set is wider than
the previous draft of this section knew. That is *keep the seam, swap the implementation* — the
argument [§5.2](#52-opentelemetry-is-not-a-ui-and-you-should-adopt-it-anyway) makes about traces —
applied to the only component that carried an obligation.

**Portability has limits, and they should be written down before anybody promises it.** Neptune
supports Bolt over **TCP only**, so *"you can't use an Application Load Balancer in front of them"*;
its SigV4 signatures expire in roughly five minutes, so the driver has to support re-authentication —
AWS names the specific driver issues where it did not; idle connections close at 20 minutes; and the
`auth` parameters are ignored unless IAM authentication is enabled. None of that breaks the seam. All
of it is configuration a deployment has to get right, and it is the kind of detail that turns
"portable" into "portable, after two days".

**What it costs** is the saving [§8.1](#81-the-graph) was reaching for. Apache AGE would have put
the graph inside the PostgreSQL the stack already runs and removed a container; Bolt keeps the
container and removes only the obligation. AGE is not reachable over Bolt, so this ruling forecloses
it. That trade is stated in [§8.1](#81-the-graph) rather than left for a reader to find.

Modelling a codebase as a property graph and letting an agent query it with Cypher — instead of
re-reading source files — is an established pattern, with tooling built specifically to be
always-on context for coding agents.

**Inferred, and this is the weakest inference in the report:** `db/neo4j` holds a code property
graph — symbols, files, imports, call edges — that the agent queries for structural retrieval,
as the fourth arm of [§3.6](#36-rag--the-retrieval-pipeline). Nothing in the layout says this. It
could equally be agent memory, a requirements ontology, or a dependency graph.

**The new `rag/` structure makes this inference testable rather than permanent.** `eval/golden/`
is where the question "does structural retrieval find files the other three arms miss?" gets an
answer. Until then, this is the component most in need of a written intent — and the decision above
has changed what turns on that. The question is no longer *is the graph worth a licence
obligation*, which was a question about SpecUP. It is *is the graph worth a container*, which is a
question about whether it earns its operational weight, and `eval/golden/` can answer it.

### 3.11 `db/seaweedfs` — the blob store

**Verified.** SeaweedFS is a distributed object store under **Apache-2.0**, describing itself as
*"a simple and highly scalable distributed file system"* built "to store billions of files". Its
S3 gateway implements the object, bucket, IAM and STS APIs on one endpoint, so AWS SDKs, the AWS
CLI, rclone and restic work against it unchanged. The architecture is master, volume and filer,
with the filer adding filesystem semantics over a pluggable metadata database.

It fills the requirement in [§3.5](#35-langfuse--llm-observability): Langfuse v3 must have
S3-compatible storage, because *"all incoming tracing and evaluation events are persisted in
S3/Blob Storage first."*

**And the choice avoids a second copyleft component.** The obvious candidate here is MinIO —
**AGPL-3.0 since 2021**, when it moved off Apache-2.0. Picking SeaweedFS keeps the blob store
permissive.

**It now has a second consumer, and that is decided rather than conditional.** `rag/index/`
artifacts — a built BM25 index, a serialised ANN index, a contextualised corpus — are large binary
blobs that are expensive to rebuild and unwanted in git.
[Decision 2](#121-decisions-taken) makes `rag/` a local library, so these files exist, and this is
where they belong. The previous draft held this open as "the same fork as §3.6.5, showing up in a
different directory"; the fork is closed and both sides moved together, which is what closing it
once was supposed to achieve.

**One consequence to hold on to:** an index artifact in a blob store is a build output with no
provenance of its own. Nothing in the layout records which commit, which model revision and which
chunker produced a given index — and retrieval quality silently depends on all three. That is the
same class of gap as an unpinned model revision ([§3.6.4](#364-embedqwen3-embedding--the-model-that-was-missing)),
one layer further out.

### 3.12 `vouch/` — agent identity and the broker

**Decided.** SpecUP adopts the [Vouch Protocol](https://github.com/vouch-protocol/vouch), which
describes itself as *"The Open Standard for Identity & Provenance of AI Agents"* and, less
formally, as *"the SSL certificate for AI agents"*. This directory is the deployment of that
adoption. It is the only component in the layout added by a ruling rather than by a reading, and
the only one whose subject is **who the agent is** rather than what it runs on.

**Verified — what it is built from.** Vouch is not a new cryptosystem. It composes standards that
already exist: W3C **Verifiable Credentials Data Model 2.0**, **Data Integrity** proofs under the
`eddsa-jcs-2022` cryptosuite — Ed25519 over JSON Canonicalisation — **DIDs** in the `did:web` and
`did:key` methods, and Multikey verification methods. An optional post-quantum profile adds
`mldsa44-jcs-2024` as a second proof. The repository's `LICENSE` is **Apache-2.0**, *"Copyright
2025 Vouch Protocol Contributors"*, and the Python package `vouch-protocol` declares Apache-2.0
with `requires-python >=3.9`.

**A credential carries intent, not just identity**, and that is what makes it useful here. The
signed object names an `action`, a `target` and a required `resource`, plus a reputation and an
optional delegation chain. So it is not *"this agent exists"* — it is *"this agent, acting on this
authority, intends this operation against this resource, inside this time window."*

**Three things it gives this stack, in the order they are worth having:**

**1. A broker that already exists.** [§3.4](#34-sandboxopenshell--nvidia-openshell)'s third row —
`commit_and_open_pr`, `request_pr_review`, `task` — is the class of action no container boundary
catches, and [§9](#9-what-the-layout-does-not-have) has listed the middleware broker as missing in
every draft of this report. **Vouch Shield is that broker, written down.** Its rules file is
declarative and denies by default:

```yaml
version: 2
rules:
  - did: did:web:agent.example.com
    allow:
      - action: read_file
        target: filesystem
        resource: "reports/**"
deny_default: true
```

`action` and `target` match exactly, with no globbing; `resource` is glob-matched against
normalised paths, `*` for one segment and `**` for zero or more. **Unknown keys are rejected at
load time rather than ignored**, which is the difference between a policy file and a suggestion. A
check returns a decision with stable reasons — `"allowed"`, `"unknown did"`, `"no matching rule"`,
`"resource outside scope"`, `"invalid resource"`, `"malformed rules"` — and on any failure a
structured error is raised **before the tool body runs**. The guarantee is stated in the same terms
this report has been using for OpenShell:

> *"There is no path where a failure produces an allow, and no fallback that is laxer than the
> configured policy."*

The enforcement point is a drop-in MCP server: `vouch.mcp.FastMCP` protects **every registered tool
by default**, a tool opts out only by being marked `unprotected=True`, and opting out logs a
warning at registration and at every call. The credential is a required argument, injected into the
tool's schema and stripped before the user function sees it, and the resource it is checked against
defaults to the JCS canonicalisation of the whole argument dict. **Default-deny with a noisy
opt-out is the correct shape**, and it is the shape SpecUP would have had to build.

**2. An identity for the agent, and a place to put the key.** `did:web` resolves through DNS to a
document at `/.well-known/did.json` — free, immediate, and centralised in the sense that losing the
domain loses the identity, which the project says plainly. The private key does not go near the
model: the documented **Identity Sidecar** pattern exists because *"if you give an LLM your private
key, it might accidentally leak it in a prompt injection attack"*, and `vouch-bridge` is the local
signing daemon that implements it. **That pattern is not optional in this stack** — the agent runs
inside a sandbox whose whole purpose is to contain it, and the signing key is the one secret that
must be outside the boundary it is signing about.

> **Corrected 2026-09-19, by running it — `vouch-bridge` is not a commit-signing daemon.** It is
> real and it installs as a console script (`vouch.bridge.server:main`), but its own FastAPI
> application calls itself a *"C2PA image signing, QR badge overlay, and audio watermarking
> service"*. Its endpoints are `sign_image` and `verify_image`, it has a companion
> `audio_routes.py`, and `_generate_cert_chain` mints an **ephemeral** three-level chain per
> request — so it holds no long-lived key to keep away from the model. The Identity Sidecar
> **pattern** is exactly as load-bearing as this paragraph says. The **component named here does
> not implement it for git**, and nothing else shipped does either, so this is work SpecUP has to
> do rather than software it can adopt.
>
> Two further findings a deployment needs. `vouch-bridge` binds **`0.0.0.0`** by default and
> enables authentication only when `VOUCH_BRIDGE_SECRET` is set, so the out-of-the-box posture is
> a signing service on every interface with no auth; `main()` parses no arguments, so
> `vouch-bridge --help` starts that server rather than printing help. And **`vouch git init`
> writes `--global` git config** — `user.signingkey`, `gpg.format=ssh`, `commit.gpgsign=true` —
> and a key pair into `~/.ssh/`, which on a machine that deliberately keeps per-repository
> configuration is a change to every repository its owner has.
>
> [Campaign 3.5](../implement/test-specup-agent-shape-assumptions.md#35--what-p4-found-and-the-sidecar-that-does-not-exist)
> has the measured topology that does work.

**3. A binding to git, which is where SpecUP's own model already lives.** `vouch git init`
configures SSH commit signing, installs commit hooks and adds a **`Vouch-DID` commit trailer**;
the project also ships delegation chains for multi-agent systems and a CI workflow that verifies
Vouch signatures on pull requests.

**Read that last one against `APV-002` carefully, because it is the trap in this component.**
SpecUP grades an approval `witnessed` when `approval.commit` resolves and its signature verifies
against `.specify/governance/allowed-signers`. Vouch's git workflow produces **SSH-signed commits**.
So an agent's commits would verify with SpecUP's existing machinery **the moment an agent's key is
added to `allowed-signers`** — no new code, no new check, and no announcement.

**That must not happen by accident, and it should probably not happen at all.**
`allowed-signers` is the human trust root; `APV-002` exists so that an approval means a person. An
agent key inside it makes `witnessed` mean "signed by something", which is the precise failure the
level was created to prevent. The defensible shape is **two roots** — or one root with a type on
each entry — so that a signature can prove *an agent did this* without ever proving *a human
approved this*. [§12.2](#122-the-eighteen-questions) question 2 is where that is decided, and it is the
single most consequential unanswered question this decision creates.

**This report reached that conclusion on its own, and it turns out to be item ten on a published
list.** OWASP's **Non-Human Identities Top 10** closes with **NHI10:2025 *Human Use of NHI***, whose
named risks include *"lack of detailed auditing and accountability"* and — in as many words —
**_"indistinguishable activity between humans and automation"_**. Its first mitigation is *"use
dedicated human identities with appropriate roles and permissions"*. The list is about humans
borrowing a machine credential and this is the mirror image, a machine credential satisfying a check
written for a human, but the property being destroyed is identical. **That changes what kind of
question this is:** not a subtlety this report noticed, but something a security reviewer will arrive
already expecting an answer to.

**What is weak here, stated rather than discovered later:**

| Weakness | Detail |
|---|---|
| **The trust root is an environment variable** | The rules file is version-controlled and reviewable; `VOUCH_TRUSTED_ISSUERS` is a comma-separated list of DIDs read from the environment at server construction, alongside `VOUCH_RULES` and `VOUCH_TARGET`. **The policy is diffable and the list of who may invoke it is not** — the inversion of what `NON-FR-CORE-0001` asks for, in the component added to strengthen provenance. The server does at least refuse to start when the configuration is missing |
| **Shield is policy, not containment** | Its own documentation says so: path normalisation *"resolves `..` lexically but cannot see symlinks"*, and *"servers must independently confine real paths to a configured root"*. **That is the argument for keeping OpenShell**, not an argument against Shield. Shield decides what an action means; OpenShell decides what a process can reach |
| **The expressiveness is deliberately small** | No negation, no numeric ranges, and no globbing on issuer DIDs — an authority-wide grant must be spelled out. Small is good for a policy language and it means some rules cannot be written at all |
| **It is young, and it is the third young dependency** | The repository was created in November 2025; the PyPI package classifies itself **Development Status 4 – Beta**; version 2.2.0 removed capability-level rules outright and required every rules file to be rewritten. Aegra is unproven, OpenShell is alpha, and this is now the third. **Three is a different risk from one** |
| **Its own README is behind its own package** | The README describes v1.6 as current while PyPI ships **2.2.1**. Nothing is wrong with the software; it means the README is not the source to quote, and the changelog and package metadata are. Every version number in this section came from the latter |
| **A trademark applies, for the first time in this stack** | *"Vouch Protocol"* is an unregistered common-law mark with registration planned. Nominative use is granted explicitly — *"Built with Vouch Protocol"*, *"Vouch-compatible"* — and naming a commercial service *"Vouch"* or *"Vouch-as-a-Service"* needs written permission. SpecUP's use is nominative, so this costs nothing and is worth knowing, since SpecUP is sold |

**And one licence consequence that is not in this section's own licence.** `vouch-protocol` depends
on **`jwcrypto`, which is LGPL-3.0-or-later** — verified from `latchset/jwcrypto`'s own `LICENSE`.
It is a base dependency, not an extra, so adopting Vouch puts a copyleft library in SpecUP's
install path. [§7.1](#71-two-copyleft-items-and-neither-is-shipped) works that through; the short
version is that it is workable and it is the first of its kind here.

**Inferred — what goes in the directory.** The Shield rules file and the `did:web` document, and
nothing else. **The private key does not live here**, which is the one thing about this directory
worth writing down before it has content: a repository is the worst possible place for it, and a
directory that exists to hold identity is exactly where somebody will eventually put one.

**What is not adopted yet.** Vouch also ships a Heartbeat Protocol — a dead-man's-switch with a
monotonic `authorityEpoch`, plus an *intent recheck* to close the gap between two heartbeats where
a sensitive action could otherwise land. That is for long-running autonomous agents whose authority
should decay when nobody is watching. It is worth knowing it exists; nothing in this stack needs it
at 0.1.3, and adopting a standard is not the same as adopting all of it.

---

## 4. How they compose

The lifecycle below is **inferred** — it is how these twelve components fit together given what
each one is, not a design anyone has recorded. It is included because the request asked how the
stack works in production, and because writing it out is what exposed the gaps in §9.

```
  ┌── GitHub issue / PR ─┐   ┌── Agent Inbox ──┐        ┌── Langfuse ──┐
  │  or Open SWE dash    │   │ accept / edit / │        │  UI, evals   │
  └──────────┬───────────┘   │ respond / ignore│        └──────▲───────┘
             │               └────────▲────────┘               │ OTLP spans
             │ GitHub App event       │ interrupt()    (traced_* wrappers)
             ▼                        │ Command(resume=…)      │
      ┌─────────────┐   POST /threads/{id}/runs   ┌────────────┴──────────────┐
      │  Open SWE   │ ─────────────────────────►  │  Aegra                    │
      │  ui / :2024 │      Agent Protocol         │  durable runs, SSE, HITL  │
      └─────────────┘         (aegra.json)        └─────────────┬─────────────┘
             ▲                                                  │ LangGraph run
             │ status, comment, PR link                         ▼
             │                              ┌───────────────────────────────┐
             │                              │  Open SWE graph               │
             │                              │  agent │ reviewer │ analyzer  │
             │                              │  chat  │ scheduler            │
             │                              └───┬────────────┬──────────────┘
             │                                  │            │  every tool call
             │                                  ▼            ▼
             │              ┌──────────────────────┐  ┌──────────────────────┐
             │              │ rag/  retrieval      │  │ Vouch Shield         │
             │              │ chunk→embed→index    │  │ deny by default      │
             │              │ →fuse→rerank         │  │ action/target/resrc  │
             │              │ + graph over Bolt    │  └──────────┬───────────┘
             │              └──────────────────────┘             ▼
             │                                       ┌──────────────────────┐
             │                                       │ OpenShell sandbox    │
             │                                       │ YAML policy, hashed  │
             │                                       │ execute() chokepoint │
             │                                       │ + egress gateway     │
             │                                       └──────────┬───────────┘
             │                                                  │ git push, SSH-signed
             └──────────────── PR opened ◄─────────────────────┘

  state:  Postgres (checkpoints, interrupts, Langfuse) · Valkey (2 queues/caches)
          ClickHouse (traces) · SeaweedFS (raw events, index artifacts)
  files:  rag/ indexes · vouch/ rules + did.json · sandbox policy YAML · governance tree
```

**Step by step:**

1. **Work arrives.** A GitHub issue is labelled, a PR comment asks for changes, or somebody
   starts a task in the Open SWE dashboard. **No adapter is needed** — this is Open SWE's own
   integration, and it is the single largest simplification in this revision
   ([§5](#5-the-interface-layer--what-replaces-plane)).
2. **Aegra accepts the run** and creates a thread. Checkpoints go to Postgres, so the run survives
   a process restart; Valkey carries the job queue and the SSE pub/sub that lets a client
   reattach to a run in progress. This is the capability that `langgraph-api` was wanted for, and
   the reason the Elastic licence is no longer an obstacle.
3. **The `agent` graph runs** under LangGraph, resolved through `aegra.json`. Deep Agents supplies
   planning, state and subagents; Open SWE supplies the engineering tools and prompts.
4. **Retrieval answers "where in this repository", four ways.** The `rag/` pipeline runs
   lexical and dense retrieval over AST-aligned, contextualised chunks, fuses the two lists by
   RRF, and reranks the top-k with a cross-encoder — all of it against indexes on local disk. The
   graph, reached over Bolt, answers the structural questions none of those reach: what calls this,
   what breaks if it changes.
5. **The graph interrupts, and a human decides.** `interrupt()` persists the payload to the
   checkpointer and the thread waits. The decision is taken in Agent Inbox or the dashboard —
   accept, edit, respond or ignore, bounded by the four booleans the graph declared — and
   `Command(resume=...)` continues from the same checkpoint.
6. **Every tool call is checked, then contained.** Vouch Shield evaluates the call's action, target
   and resource against a rules file that denies by default, and raises before the tool body runs.
   What survives that reaches the OpenShell sandbox: because `BaseSandbox` builds
   `read`/`write`/`edit`/`ls`/`glob`/`grep` on `execute()`, the policy is a real boundary for that
   whole class, and the egress gateway bounds outbound network below the agent. The policy hash is
   attested before the backend is exposed, and disagreement fails closed. **The two are not
   redundant:** Shield knows what an operation *means* and cannot see a symlink; OpenShell knows
   what a process can *reach* and cannot tell a pull request from a force-push.
7. **The `reviewer` graph reads the PR** and records findings; `analyzer` learns the repository's
   review preferences over time.
8. **Every step emits a trace.** The `traced_*` entrypoints emit OTLP spans to Langfuse, which
   writes them to ClickHouse and the raw events to SeaweedFS.
9. **The result returns to GitHub** as a PR, a review comment, or a status on the originating
   issue — and the commits carry an SSH signature and a `Vouch-DID` trailer, made by a signing
   daemon outside the sandbox. **This is the first step in the lifecycle whose output can be
   verified after the fact by somebody who was not there**, which is what provenance means and what
   every other step in this list lacks.

### The four governance seams

SpecUP's interest in this stack is not that it codes. It is that steps 5, 6, 8 and 9 are the only
points where a governance claim can be made mechanical — and **they do not all have the same
strength**, which is the most useful thing this report can say about them:

| Seam | What it is | Binds content? |
|---|---|---|
| **Step 6 — the sandbox** | a tool call satisfies the policy or it does not | **Yes.** The policy is hashed and attested, and disagreement fails closed |
| **Step 8 — the trace** | a record produced by the run rather than asserted about it | **Yes**, in the sense that matters: it is emitted, not written afterwards |
| **Step 9 — the signed commit** | the agent's output, signed by a key held outside the sandbox, carrying the identity it acted under | **Yes**, and it is the only seam that can still be checked a year later by somebody with nothing but the repository. **New in this revision** |
| **Step 6 — the broker** | the call's action, target and resource match a rules file, or it never runs | **The policy, yes; the caller, partly.** The rules are a reviewable file; the list of issuers they trust is an environment variable |
| **Step 5 — the decision** | a human accepts, edits, responds or ignores | **No.** It is a click, authenticated but unsigned, stored in a database |

Everything else in the stack is plumbing that makes those possible, and the table is ordered by
strength deliberately. **The last row is still the weak one, and it is the one SpecUP's whole model
is about.** Decision 4 added two rows above it without moving it —
[§12.2](#122-the-eighteen-questions) question 1 is that gap, unchanged in substance and now much better
surrounded.

---

## 5. The interface layer — what replaces Plane

`plane.so/` was in the layout and is not any more. Plane is a self-hostable project tracker whose
Community Edition is AGPL-3.0, and whose self-hosted footprint is six application containers —
web, admin, api, worker, beat-worker, live — behind a Caddy proxy, over its own Postgres, Valkey,
**RabbitMQ** and **MinIO**. It was the largest single item in the stack, and it was AGPL.

**The question it leaves behind is real:** something has to let a human start work, watch it, and
intervene. The answer is that three separate things were being asked of one component, and each
already has an owner.

### 5.1 What Plane was for, and what already does it

| What was wanted | What provides it now | Licence | New containers |
|---|---|---|---|
| **Work intake** — start a task, track its state | GitHub issues and PRs, via Open SWE's GitHub App. Linear and Slack are also wired in upstream | MIT (integration) | **none** |
| **Run steering** — watch a run, inspect a diff | `open-swe-dashboard`, shipped in Open SWE's own `ui/`, served beside the API at `:2024` | MIT | **none** — it is part of the agent |
| **Explicit decisions** — approve, edit, reject | **Agent Inbox**, now [§3.3](#33-agent-inbox--the-explicit-decisions) | MIT | **none** — a static front end over Aegra |
| **Alternative clients** | Agent Chat UI, LangGraph Studio, CopilotKit — Aegra *"works with [them] out of the box"* | MIT (Agent Chat UI) | **none** |
| **Observability and audit** | Langfuse, already in the stack | MIT core | **none** — already counted |

**So the lightweight UI layer is not a component to add. It is surfaces that already exist, and
the work is configuration rather than construction.** The heaviest thing on that list is Langfuse,
which the stack needed anyway.

### 5.2 OpenTelemetry is not a UI, and you should adopt it anyway

**Stated plainly, because the distinction matters:** OpenTelemetry is an instrumentation API, a
set of SDKs and a wire protocol. It has no interface. It cannot replace a tracker or a dashboard,
and a stack instrumented with OTel and nothing else shows a human nothing at all. **Langfuse is
the UI for OTel data in this stack**, and OTel is how the data gets there.

**But the instinct behind the suggestion points at a real problem, and the answer is yes.**
[§7.4](#74-vendor-concentration) records that ClickHouse now owns both Langfuse and the store
Langfuse mandates, so the entire observability half of this stack has one commercial owner. There
is one cheap mitigation, and it is exactly this:

> **Instrument to OpenTelemetry, not to Langfuse's native SDK.** Langfuse accepts OTLP as an
> OpenTelemetry backend. So does Grafana Tempo, Jaeger, SigNoz, Honeycomb, Datadog and every
> other trace store worth naming.

The cost is close to zero — Langfuse documents the OTLP route itself — and what it buys is that
step 8 of §4 stops being a bet on one vendor. If Langfuse relicenses, or if the ClickHouse
requirement becomes uncomfortable, the instrumentation does not change; only the endpoint does.
Instrumenting to a vendor SDK makes that a rewrite.

This is the same argument [§8](#8-alternatives-where-there-are-any) makes about the sandbox and
the graph: *keep the seam, swap the implementation*. It is the cheapest form of it in the whole
report, because the seam already exists and is standardised.

### 5.3 What removing Plane costs

Stated rather than omitted, because the trade is not free:

| Lost | Mitigation |
|---|---|
| **Cycles, modules and estimates** — Plane's planning structures, which map onto OpenUP iterations more directly than anything GitHub offers | GitHub Projects has iteration fields and milestones; Linear has cycles natively and Open SWE already integrates with it. Neither is as close a fit, and this is the sharpest loss |
| **A tracker SpecUP controls** | Work items now live in the customer's GitHub. That is a smaller product surface and a larger integration surface |
| **A single self-hosted surface for a customer with no GitHub** | Real, and it narrows the addressable deployment. An air-gapped customer without GitHub Enterprise has no intake path in this design |

**And what it buys, which is more:**

- **The AGPL-3.0 exposure is gone entirely** — the largest item in [§7](#7-the-licence-position).
- **RabbitMQ disappears**, because Plane was its only consumer.
- **Six application containers and a Caddy proxy disappear.**
- **Postgres and Valkey each drop a consumer**, which makes the shared-cluster argument in
  [§6](#6-the-shared-substrate) easier rather than harder.
- **The Plane → Agent Protocol adapter disappears from [§9](#9-what-the-layout-does-not-have)**,
  and it was the one missing component with no upstream to borrow from. It was going to be
  SpecUP's to write, forever.

### 5.4 The conventions the GitHub surface follows

**Decided.** Three published conventions, adopted together because [§5](#5-the-interface-layer--what-replaces-plane)
made GitHub the whole interface layer. A surface that is the entire front door needs a written
grammar, and all three of these are already what most contributors expect.

| Convention | What it fixes | Read from |
|---|---|---|
| **["How to Write a Git Commit Message"](https://cbea.ms/git-commit/)** — cbeams, 31 August 2014 | The shape and content of a commit message. Seven rules: separate subject from body with a blank line; limit the subject to **50 characters**; capitalise it; no full stop; **imperative mood**; wrap the body at **72**; use the body for *what* and *why* rather than *how* | The page itself |
| **[Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)** | The machine-readable prefix. `<type>[optional scope]: <description>`, body after a blank line, footers as `token: value` with hyphens for spaces. `fix` → PATCH, `feat` → MINOR, `BREAKING CHANGE` → MAJOR. Case-insensitive **except** `BREAKING CHANGE`, which must be uppercase; `!` before the colon is the short form | The specification, which is **CC BY 3.0** |
| **[GitHub issue and pull request templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates)** | What a human or an agent is asked for when it opens work. `.md` files and issue-form `.yml` files in `.github/ISSUE_TEMPLATE/`, with `config.yml` controlling the chooser; a pull request template as `.md` or `.txt` in the repository root, `docs/`, or `.github/` | GitHub's documentation |

**The templates have one hard constraint worth repeating**, because it is the thing that silently
fails: both kinds live **on the default branch**. GitHub's documentation is explicit — *"Templates
created in other branches are not available for collaborators to use."* A template added on a
feature branch does nothing, and nothing says so.

**Where this actually bites is that an agent writes most of these commits.** The seven rules read
as advice to a person and function as a hard constraint on a generator: left alone, a model will
produce a subject line of any length and a body of any shape. And the trailers this stack adds —
`Vouch-DID` from [§3.12](#312-vouch--agent-identity-and-the-broker), plus whatever co-authorship
line a provider appends — **are footers in the Conventional Commits sense**. So the format is not
decoration. It is what keeps those trailers parseable by something other than a regular expression
written in a hurry.

**The two commit conventions disagree in exactly one place, and the resolution is recorded here so
nobody re-derives it per commit.** cbea.ms rule 3 says capitalise the subject line. Conventional
Commits requires a `type` prefix and is *"case insensitive"* about everything except
`BREAKING CHANGE`. Adopting both means: **the type is lowercase, and the description after the colon
follows cbea.ms** — capitalised, imperative, no full stop.

```
feat(rag): Split the ANN index by corpus

Static binding documents go to ivf/ and code to hnsw/, because IVF is not
resilient to index updates and that costs nothing for a frozen corpus.

Refs: ADR-00XX
Vouch-DID: did:web:agent.example.com
```

The 50-character subject limit applies to the **whole** line including the type and scope, which is
tighter than it looks: `feat(rag): ` is eleven characters before the description starts. cbea.ms
calls 50 *"not a hard limit, just a rule of thumb"* and 72 the hard one, and that is the reading
adopted — **50 as the target, 72 as the failure point.**

**And one honest note about this repository.** SpecUP's own history does not follow Conventional
Commits: `c56c2e3` is *"Record what the 0.1.2 release verified, and why its WBS node is still open"*,
which satisfies all seven of cbea.ms's rules and none of Conventional Commits'. **The convention
starts here rather than retroactively.** The history is not rewritten, because rewriting it to
satisfy a rule adopted afterwards would invert what both conventions are for — and because anything
parsing this log for release notes now has to cope with two grammars either side of one commit.
That cost is real and it is smaller than the cost of a rewritten history.

**What checks it.** A `commit-msg` hook in `.pre-commit-config.yaml` can reject a malformed commit
before it exists, and that is the only one of the three that is mechanically enforceable. **Nothing
checks the templates** — GitHub renders them and has no opinion about whether anybody fills them in.

---

## 6. The shared substrate

Counted by consumer rather than by container, the stack is smaller than its directory count:

| Service | Wanted by | Separable? |
|---|---|---|
| **PostgreSQL** | Aegra (checkpoints, interrupts), Langfuse (transactional) | Shareable as databases in one cluster. Langfuse runs its own migrations, so a shared schema is not an option — separate databases, one server. **`rag/` is no longer a consumer** ([decision 2](#121-decisions-taken)), although `pgvector` still arrives with Aegra's image |
| **Valkey** | Aegra (queue, SSE), Langfuse (cache, queue) | Yes, by database index or key prefix |
| **ClickHouse** | Langfuse only | **No.** Transitive dependency of §3.5 |
| **The graph** | structural retrieval only | **Yes, and it is now the customer's** — reached over Bolt, run by whoever runs it ([decision 6](#121-decisions-taken)). It is the one service in this table SpecUP can point at rather than deploy |
| **SeaweedFS** | Langfuse (required), `rag/index` artifacts | One instance serves both, and the second consumer is now certain rather than conditional |
| **Model serving** | `rag/embed`, `rag/rerank` | **One process serves both** — **measured 2026-09-19 at one pid and 3337 MiB**, and only these two, because stage 2 calls SpecUP's configured provider instead ([decision 7](#121-decisions-taken)). **Not "TEI, Infinity, llama.cpp or Ollama" any more:** TEI takes one `--model-id` per process and cannot serve both, so the permissive options are not interchangeable for this row. Still config rather than a directory in the layout |

So twelve components resolve to **five stateful services plus one model server**, of which three
exist because Langfuse does and one is not SpecUP's to run. `vouch/` adds no service: Shield is a
library in the agent's own process and the signing daemon is a sidecar beside it.

**That concentration is worth noticing.** Before this revision, RabbitMQ existed only because
Plane did and ClickHouse only because Langfuse did. Removing Plane removed one of those
dependencies and left the other more exposed: **observability is now most of the operational
weight of the stack.** It is still the right call — step 8 is a governance seam — but the cost
should be attributed to the thing that causes it rather than spread across "the stack".

**The retrieval pipeline is the opposite case.** Seven stages, eleven leaf directories, and it adds
**one process** — the model server — plus a directory of index files and a line item on a provider
bill. Directory count is a very poor proxy for operational weight, and `rag/` is where the two
diverge most.

**The dependency that is easiest to underestimate is PostgreSQL.** It is not one database with
two tenants but two independent schemas with two migration histories, either of which can break
on upgrade without the other noticing — and it now holds pending human decisions as well.

---

## 7. The licence position

Every licence below was read this session from the project's own licence file or model card, not
from secondary sources. Where a project has relicensed before, that is noted, because these
change.

| Component | Licence | OSI | Read from |
|---|---|---|---|
| Open SWE *(agent, `ui/`, `desktop/`)* | MIT (LangChain, Inc.) | Yes | `LICENSE` |
| Aegra | Apache-2.0 | Yes | `LICENSE` |
| LangGraph, Deep Agents | MIT | Yes | recorded in the 0.1.2 plan §7 |
| **Agent Inbox** | MIT (LangChain, Inc.) | Yes | `LICENSE` |
| Agent Chat UI | MIT | Yes | `LICENSE` |
| **NVIDIA OpenShell** | **Apache-2.0** | Yes | `LICENSE` |
| **Vouch Protocol** | **Apache-2.0** — *"Copyright 2025 Vouch Protocol Contributors"* | Yes | `LICENSE`, and the PyPI metadata for `vouch-protocol`. GitHub's own detector reports `NOASSERTION`, because the file carries a preamble before the Apache text |
| **`jwcrypto`** *(via `vouch-protocol`)* | **LGPL-3.0-or-later** | Yes | `latchset/jwcrypto` `LICENSE`. **The first copyleft library in SpecUP's own install path** — [§7.1](#71-two-copyleft-items-and-neither-is-shipped) |
| `pqcrypto`, `cryptography`, `pydantic`, `httpx` *(same chain)* | Apache-2.0 / Apache-2.0 OR BSD-3-Clause / MIT / BSD-3-Clause | Yes | PyPI metadata each |
| **Neo4j drivers** | **Apache-2.0 AND Python-2.0** | Yes | `LICENSE.txt`, `LICENSE.PYTHON.txt`, `NOTICE.txt` — this is what SpecUP actually ships for the graph |
| **Bolt protocol *documentation*** | **CC BY-NC-SA 4.0** | No | `neo4j/docs-bolt` `LICENSE.txt`. Restricts copying the spec text, not speaking the protocol — [§3.10](#310-dbneo4j--the-graph-store) |
| `huggingface_hub` / the `hf` CLI | Apache-2.0 | Yes | PyPI metadata |
| ***The Twelve-Factor App*** *(text, not software)* | MIT | Yes | `heroku/12factor` — *"Released under the MIT License"*. Adopting a methodology obliges nothing; quoting its text is what a licence reaches, and [§11](#11-the-stack-as-a-fifteen-factor-application) quotes it |
| ***12-Factor Agents*** *(text, not software)* | **CC BY-SA 4.0** content; Apache-2.0 code | Content no | `humanlayer/12-factor-agents`. **Not adopted** — named in [§11](#11-the-stack-as-a-fifteen-factor-application) only because the title collides with what is. Share-alike would attach to adapted text, so it is worth knowing before anybody borrows a paragraph |
| **Conventional Commits v1.0.0** *(text, not software)* | **CC BY 3.0** | Attribution only | The specification page, adopted by [decision 10](#121-decisions-taken). Attribution-only, no share-alike — so quoting the format in SpecUP's own contributing guide costs a credit and nothing else |
| **cbea.ms, "How to Write a Git Commit Message"** *(text, not software)* | **Not stated** | — | The page carries no licence notice. **The seven rules are facts about a convention and are not themselves copyrightable**; the prose is. Cite it, do not paste it — the same rule [§3.10](#310-dbneo4j--the-graph-store) reaches for the Bolt documentation |
| Langfuse | MIT core; `ee/`, `web/src/ee/`, `worker/src/ee/` commercial | Core yes | `LICENSE` — copyright **ClickHouse, Inc.** |
| ClickHouse | Apache-2.0 | Yes | `LICENSE` |
| Valkey | BSD-3-Clause | Yes | `COPYING` |
| PostgreSQL | PostgreSQL License | Yes | BSD/MIT family |
| SeaweedFS | Apache-2.0 | Yes | `LICENSE` |
| tree-sitter, astchunk | MIT | Yes | `LICENSE` |
| bm25s | MIT (Xing Han Lu) | Yes | `LICENSE` |
| pgvector / FAISS / hnswlib / usearch | PostgreSQL License / MIT / Apache-2.0 | Yes | `LICENSE` each |
| **Qwen3-Embedding** | **Apache-2.0** | Yes | model card |
| **Qwen3-Reranker** | **Apache-2.0** | Yes | model card |
| bge-reranker-v2-m3, nomic-embed-code | Apache-2.0 | Yes | model card each |
| CoIR toolkit | Apache-2.0 | Yes | repository |
| TEI / Infinity / llama.cpp / Ollama / vLLM | Apache-2.0 / MIT | Yes | `LICENSE` each |
| **Neo4j Community** | **GPL-3.0**, with a commercial override | Yes | `LICENSE.txt` |

**Three entries are not permissive, and [decision 1](#121-decisions-taken) is why the table is
still comfortable.** SpecUP composes this stack: it publishes code that stands the stack up, and
distributes none of the software the stack is made of. A licence that governs *distribution* has
nothing to attach to. The exception is the Python dependency chain, which SpecUP genuinely does
put in front of its users — that is [§7.1](#71-two-copyleft-items-and-neither-is-shipped).

A `NOTICE` file becomes a shipping requirement the moment any of this is vendored or redistributed.
It does not exist yet, because nothing is vendored yet — and the Apache-2.0 entries above are the
reason it will be needed the first time anything is.

**Two obligations left this stack**, and both are worth recording because they were the hardest
items in the previous draft:

| Removed | Was | Why it is gone |
|---|---|---|
| Plane Community | AGPL-3.0, with §13's network clause | The tracker role was already covered ([§5](#5-the-interface-layer--what-replaces-plane)) |
| Docker Sandboxes (`sbx`) | **Proprietary** — its `LICENSE` is the single line *"Copyright © 2026 Docker Inc. All rights reserved."*, distributed as binaries only, with team-level policy behind the paid Docker AI Governance product | NVIDIA OpenShell does the same job at Apache-2.0, with a Deep Agents provider that already exists ([§3.4](#34-sandboxopenshell--nvidia-openshell)) |

### 7.1 Two copyleft items, and neither is shipped

**The first is the graph server**, Neo4j CE at GPL-3.0, and
[decisions 1 and 6](#121-decisions-taken) together move it out of SpecUP's licence position
entirely. SpecUP ships a Bolt client. It does not vendor the server, fork it, publish a derived
image, or distribute an appliance containing it. GPL-3.0 reciprocity attaches to distributing the
software, and SpecUP distributes none of it. Whether a given customer runs Community Edition under
GPL-3.0, buys the commercial override, or points the same client at a different Bolt server is
their decision about their own deployment.

**That is a smaller claim than the previous draft's, and it is a sturdier one.** The old argument
turned on separate processes communicating over a network protocol not creating a derivative work
— the common reading, how most of the industry operates, and untested against this specific
deployment. The new argument does not need that reading to hold, because there is no distribution
to characterise. **The reading still matters for one case**, and it should be written down before
it arrives: a one-command appliance that brings up the whole stack is a natural product for this
project, and it sits much closer to distribution than a compose file does. Decision 1 is the rule
that forbids it; it is worth knowing that it forbids something somebody will want.

**The second is new, and it is the one that is genuinely in SpecUP's install path.**
`vouch-protocol` depends on **`jwcrypto`, LGPL-3.0-or-later** — a base dependency, not an extra, so
adopting Vouch means SpecUP's own `requirements.txt` resolves a copyleft library onto every
machine that installs it.

| | |
|---|---|
| **What is fine, and is the ordinary case** | Importing an unmodified library that the user installs from PyPI. SpecUP's own code stays BUSL-1.1; the LGPL covers `jwcrypto` and does not reach out into the application that calls it. Python's import model does nothing that LGPL §4 objects to, and because SpecUP is source-available the *"allow the recipient to replace the library"* condition is already satisfied by how the project is distributed |
| **What would not be fine** | Vendoring a copy into this repository, or shipping a frozen single-file artifact, a bundled wheel or a redistributed container image with `jwcrypto` inside it, without meeting LGPL §4's replacement and notice conditions. **That is the same appliance case as the first item**, arriving from a second direction |
| **The hazard worth naming** | It is **transitive**. SpecUP's requirements would name `vouch-protocol`; `jwcrypto` arrives underneath it. A reviewer reading SpecUP's own dependency list would not see a copyleft library at all, and the first person to discover it would be whoever packages the appliance |

**Neither item argues against the decision that introduced it.** Both argue for the same missing
artifact: a written rule about what SpecUP may put inside a distributable bundle. That rule does
not exist today, and until it does, the protection here is that nobody has tried to build one.

### 7.2 Model weights carry licences too, and the good ones often forbid you

**This is the section most likely to be skipped, and it is where the licence risk actually moved.**
Everything above is code. A retrieval pipeline also ships or downloads **model weights**, and
weights carry their own terms that have nothing to do with the licence of the code that runs them.
`llama.cpp` being MIT says nothing about the model it loads.

Three of the models a 2026 "best RAG models" list would put near the top are unusable in a
commercial product, and each was read from its own model card this session:

| Model | Licence as stated | What it means here |
|---|---|---|
| **`jina-reranker-v3`** | **`cc-by-nc-4.0`** — *"the model is licensed under CC BY-NC 4.0. For commercial usage inquiries, feel free to contact us"* | State of the art among open-weight rerankers at 61.94 nDCG@10 on BEIR, and **non-commercial**. Unusable in a product SpecUP sells, absent a separate agreement with Jina AI |
| **`splade-v3`** | **`cc-by-nc-sa-4.0`** | Learned sparse retrieval, an attractive complement to BM25. **Non-commercial, and share-alike on top** |
| **EmbeddingGemma** | **Gemma terms** — *"Prohibited uses of Gemma models are outlined in the Gemma Prohibited Use Policy"*, and *"you're required to review and agree to Google's usage license"* to download | Not an OSI licence. Commercial use is permitted, but the prohibited-use policy travels downstream, so shipping it means passing Google's restrictions to every customer |

**The pattern is not accidental.** Research labs release the strongest checkpoint under terms that
protect a commercial offering, exactly as ClickHouse, Elastic and Neo4j do with code. A stack that
picks models by benchmark rank will pick a non-commercial one, and the failure is silent: the
model works, the tests pass, and the problem surfaces at the first customer contract.

**The picks in [§3.6](#36-rag--the-retrieval-pipeline) are Apache-2.0 by construction** —
Qwen3-Embedding, Qwen3-Reranker, with `bge-reranker-v2-m3` and `nomic-embed-code` as permissive
alternates. That costs some benchmark position at the reranker, and the cost is worth naming
rather than pretending the best open-weight model was also the permissive one.

**That obligation is now decided away, and the residue is worth being precise about.**
[Decision 5](#121-decisions-taken) is that SpecUP ships no weights and nothing else obtainable
online; [decision 3](#121-decisions-taken) is that the models are fetched with `uv` and the
Hugging Face library ([§3.6.4](#364-embedqwen3-embedding--the-model-that-was-missing)). So the
weights are never redistributed by SpecUP, their terms never join a SpecUP `NOTICE`, and each
customer accepts them from the model's author at the gate the author put there.

**What does not go away is the recommendation.** A default is a form of steering: if SpecUP's
configuration names `jina-reranker-v3` as the reranker, every customer who accepts the default runs
a CC BY-NC 4.0 model in a commercial product, and SpecUP put them there without distributing a
single byte. **Not shipping the weights removes the redistribution question and leaves the
responsibility**, which is why [§3.6](#36-rag--the-retrieval-pipeline)'s defaults are Apache-2.0 by
construction and why the non-commercial models are named here rather than quietly avoided.

### 7.3 Langfuse's split, which is narrower than it looks

Langfuse is MIT at the core with commercial modules in clearly marked `ee/` directories. The EE
features are enterprise governance — RBAC, audit logs, SCIM, retention policies, masking. **None
of them is tracing.** Everything this stack needs from Langfuse is MIT, and self-hosting it
commercially without a key is explicitly contemplated by the project.

The care needed is ongoing rather than upfront: the boundary is a directory convention, so it can
move between releases, and a future feature this stack comes to depend on could land inside `ee/`.
[§5.2](#52-opentelemetry-is-not-a-ui-and-you-should-adopt-it-anyway) is the mitigation for that
too, not only for the ownership question.

### 7.4 Vendor concentration

ClickHouse, Inc. **acquired Langfuse in January 2026**, alongside a $400M Series D. So `langfuse/`
and `db/clickhouse` are one vendor, not two — and since ClickHouse is also the store Langfuse
mandates, the observability half of this stack has a single commercial owner.

Nothing about that is wrong today: both remain open source, and the acquirer's stated roadmap
keeps them self-hostable. It is recorded because *"we use two independent open-source projects"*
would be a false description of the observability layer, and because licence changes in this
industry follow ownership changes more often than not. Redis, ArangoDB, Neo4j Enterprise,
MinIO, Elastic and HashiCorp all relicensed; SpecUP itself relicensed at 0.1.2, so this project
is in no position to treat it as unusual.

**This is now the largest single-vendor exposure in the stack**, because the other one was
removed. It is also the cheapest to hedge: OTLP instead of a vendor SDK,
[§5.2](#52-opentelemetry-is-not-a-ui-and-you-should-adopt-it-anyway).

### 7.5 What decision 1 does not excuse

Decision 1 does most of the work in this section, so it is worth being exact about what it does
not do. **It is a statement about what SpecUP publishes, and it is only true for as long as that
stays true.** Five things survive it:

| Survives | Why |
|---|---|
| **The Python dependency chain** | SpecUP does distribute its own package and its requirements. That is where `jwcrypto` lives, and composition does not reach it — [§7.1](#71-two-copyleft-items-and-neither-is-shipped) |
| **Attribution, the first time anything is vendored** | Apache-2.0 entries in the table above carry notice and patent terms. Nothing is vendored today. The rule holds until somebody decides an appliance would be convenient |
| **Responsibility for defaults** | Not shipping a component does not make SpecUP neutral about which one a customer runs. A default that points at a non-commercial model or a GPL server is still SpecUP choosing — [§7.2](#72-model-weights-carry-licences-too-and-the-good-ones-often-forbid-you) |
| **Trademark** | New in this revision, and the first in this stack. *"Vouch Protocol"* is a common-law mark; describing SpecUP as *"Vouch-compatible"* is granted, naming a commercial service after it is not. Composition does not touch trademark, which is a different body of law from the licence |
| **The installer's burden** | This is the honest cost. **"Compose, not redistribute" is easier for SpecUP and harder for whoever installs it** — five stateful services, a sandbox runtime, a model fetch and a graph server they must stand up themselves. The licence exposure did not disappear; part of it moved to the customer, who is now the party running GPL-3.0 software |

**And nothing enforces any of this.** Decision 1 is a sentence in a research document. The
artifacts that could make it real — a packaging rule, a dependency-licence check in CI, a `NOTICE`
generator — do not exist. That is the same observation the end of this report makes about every
other claim in it, and it applies with more force here, because this is the decision the other six
lean on.

---

## 8. Alternatives, where there are any

Two components are still worth a substitution argument, and the reasons have changed. The graph's
licence question is answered — [decision 6](#121-decisions-taken) — so what is left there is
whether it earns its container. The sandbox's question was always maturity. The retrieval models
have their own arguments, in [§3.6](#36-rag--the-retrieval-pipeline) and
[§7.2](#72-model-weights-carry-licences-too-and-the-good-ones-often-forbid-you).

### 8.1 The graph

| Option | Licence | What it costs |
|---|---|---|
| **Apache AGE** | Apache-2.0 | openCypher inside the PostgreSQL the stack already runs. **Removes a service and the last copyleft obligation together.** Smaller community than Neo4j; less mature tooling; graph performance is Postgres performance |
| Keep Neo4j CE | GPL-3.0 | Best tooling, largest ecosystem, most agent-facing prior art. Carries §7.1 |
| Buy the Neo4j override | commercial | `LICENSE.txt` says a Commercial Agreement *"will supersede"* the GPL. Removes the licence question and replaces it with a per-deployment cost and a vendor negotiation in every sale |
| Kùzu | MIT | Embedded, no server at all, Cypher plus vector and full-text search. **Archived October 2025 after Apple acquired the company**; continues only as community forks |
| Memgraph | BSL | Source-available, same licence *class* as SpecUP |
| ArangoDB | BUSL-1.1 | Same, with a non-commercial capacity cap |
| FalkorDB | SSPL | Not OSI; SSPL is the licence family most hostile to hosted products |
| **Amazon Neptune** | managed service | **Speaks Bolt with the Neo4j drivers**, so it is reachable without changing a line. Managed rather than self-hosted, which is the opposite of what this stack is for — but it is the option an existing AWS customer will ask about, and the answer is now yes. TCP only, no load balancer in front, SigV4 signatures that expire in minutes |
| **Drop the graph** | — | Recursive CTEs in Postgres, or the three `rag/` arms alone. Costs structural retrieval entirely |

**This table is now a record of an argument that was decided a different way**, and it is kept for
that reason rather than deleted.

The previous draft's recommendation was **Apache AGE** — openCypher inside the PostgreSQL that
Aegra and Langfuse already require, removing a container and the last licence obligation together,
and composing with a pgvector-backed `rag/` so that *"the entire retrieval layer becomes extensions
on a server that is already mandatory."* It was the strongest single recommendation in the report.

**Two decisions removed it, and neither was about the graph.**
[Decision 6](#121-decisions-taken) made Bolt the wire, and AGE does not speak Bolt — it is a
PostgreSQL extension reached over the PostgreSQL wire. [Decision 2](#121-decisions-taken) moved
`rag/` to local index files, which removes the other half of the argument: there is no longer a
dense index inside Postgres for a structural index to sit beside. **The consolidation case
collapsed from both ends at once.**

**What was traded.** AGE removed a container *and* an obligation; Bolt removes the obligation and
keeps the container. In exchange it keeps Cypher, keeps the mature tooling, and makes the graph the
one component a customer can substitute without SpecUP changing — **of the options above, Neo4j,
Memgraph and Amazon Neptune all speak Bolt** (Memgraph's compatibility with the Neo4j drivers and
Neptune's Bolt endpoint were both verified). Kùzu is embedded and has no server wire at all. The
remaining rows were not checked for Bolt support here, and checking them is part of
[§12.2](#122-the-eighteen-questions) question 8, whose recommendation is in
[§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on).

And the last row of the table is answerable rather than rhetorical. `eval/golden/` is exactly the
instrument that says whether the graph earns a container — which is the difference between dropping
it as a decision and dropping it as a guess. **That question is now the only one left about the
graph**, because the licence question has an answer.

Note that Memgraph and ArangoDB are BSL/BUSL — **the same licence class SpecUP itself chose.**
Swapping a copyleft dependency for a source-available one does not restore permissive freedom; it
substitutes one set of conditions for another. That is worth saying out loud in a document
published by a BUSL project.

### 8.2 The sandbox

The licence question here is settled — OpenShell is Apache-2.0. What is left is maturity, and the
alternatives are worth knowing because OpenShell is badged alpha.

| Option | Licence | What it costs |
|---|---|---|
| **NVIDIA OpenShell** *(chosen)* | Apache-2.0 | Declarative YAML policy over filesystem, process, network and providers; hash attestation that fails closed; egress gateway; a Deep Agents provider that already exists. **Alpha**, Kubernetes support experimental |
| Docker Sandboxes (`sbx`) | proprietary | The most finished product, and the strongest default isolation — own kernel per sandbox, private Docker daemon, cross-platform VMM. Closed binary, paid team policy, no source to audit |
| Plain Docker containers | Apache-2.0 (Moby) | Fully open, trivially scriptable, `execute()` over `docker exec`. **Namespace isolation, not hardware.** No policy layer, no attestation — all of that becomes SpecUP's to build |
| Kata Containers | Apache-2.0 | Real per-container VMs, OCI-compatible, open end to end. Linux and KVM only; no policy or attestation layer of its own |
| gVisor | Apache-2.0 | A user-space kernel between workload and host. Stronger than a container, weaker than a VM, with a performance cost on the I/O-heavy work a build actually is |
| The other Deep Agents providers | vendor terms | Daytona, E2B, Modal, Runloop, Vercel, AgentCore, LangSmith already implement the protocol. No build at all, and the boundary moves to somebody else's cloud — the opposite of what a self-hosted stack is for |

**The point that survives whichever is picked:** `SandboxBackendProtocol` is one method. Keeping
`execute()` behind an interface that can dispatch to OpenShell today and something else later
costs one indirection, and it is what `sandbox/` as a grouping directory already implies. Given
that OpenShell is alpha, that indirection is not optional hygiene — it is the thing that makes
the alpha acceptable.

**What no alternative gives back** is the attested policy. Kata and gVisor isolate; they do not
bind a hash-verified policy and fail closed, and they do not emit a `sandbox.attestation` event.

---

## 9. What the layout does not have

Present-by-absence, and each one is a real gap rather than a nitpick:

| Missing | Why it matters |
|---|---|
| **The binding from a decision to an approval** | [§3.3](#33-agent-inbox--the-explicit-decisions). An Agent Inbox decision is `claimed`, never `witnessed`. Nothing hashes it, writes it to a reviewable file, or binds it to a signed commit — and that is the one gap SpecUP exists to close. **Decision 4 narrowed it without closing it:** the agent can now sign; the human still clicks |
| ~~**The middleware broker**~~ **— the rules that go in it** | The component is no longer missing ([§3.12](#312-vouch--agent-identity-and-the-broker)); **its policy is.** Vouch Shield denies by default, so an unwritten rules file is not an open door — it is a closed one, and the agent can do nothing at all. Writing the allow list for `commit_and_open_pr`, `request_pr_review` and `task` is the work that remains |
| **The issuer trust root** | `VOUCH_TRUSTED_ISSUERS` is an environment variable and `.specify/governance/allowed-signers` is a reviewed file. **Nothing yet says whether these are one root or two**, and getting it wrong makes an agent's signature indistinguishable from a human's — [§12.2](#122-the-eighteen-questions) question 2 |
| **Key custody** | The agent signs, so a private key exists. Nothing in the layout says where it lives, who rotates it, or what happens when it leaks. The Identity Sidecar pattern says only that it must not be reachable by the model |
| **The OpenShell policy itself** | `sandbox/openshell/` is where the YAML belongs, and it is one of two artifacts in this stack SpecUP would genuinely govern — the Shield rules file is now the other. Nothing is in it |
| **The indexing job** | `rag/` describes a pipeline and names no thing that runs it. Something has to walk the repository, chunk, contextualise, embed and index on every commit, and decide what is incremental. **It is also the one process that holds a provider credential and needs egress** ([§3.6.2](#362-chunkcontextual--the-35)), which makes it a security boundary as well as the largest unwritten piece of the retrieval layer |
| **Index provenance** | Which commit, which model revision and which chunker produced a given index. Retrieval quality depends on all three and nothing records any of them — [§3.11](#311-dbseaweedfs--the-blob-store) |
| **The embedding model's serving budget** | One model server is one process and an unquantified amount of GPU or CPU. `rag/` says which models; nothing says on what hardware, at what latency, for what corpus size |
| **Secrets** | No `.env`, no `.env.example`. Langfuse, the GitHub App, the model provider for stage 2, the graph's Bolt credentials and the agent's signing key all need somewhere to live. OpenShell's provider policy covers credentials inside the sandbox only, and the signing key is deliberately outside it. **Factor III now says where they go, and supplies the test for whether they got there** — [§11.3](#113-two-collisions-and-both-resolve) |
| **Application logs** | Everything in this stack emits *traces*. Nothing says what happens to an ordinary log line. **That is factor XI, and it is the gap most easily mistaken for filled**, because Langfuse looks like the place logs would go and is not — [§11.6](#116-telemetry-is-not-logs-and-this-stack-has-one-of-them) |
| **Ingress** | Langfuse, Aegra, the Open SWE dashboard and the Agent Inbox all want HTTP. Nothing terminates TLS or routes. **Factor VII puts this outside the app deliberately** — the components bind ports correctly and the routing layer is the execution environment's to supply, which is why this is a deployment gap rather than an application defect |
| **Content in `docker-compose.yml`** | The file that would compose all of this is zero bytes |

**Gaps closed across the last two revisions.** The Plane → Agent Protocol adapter is gone because
Open SWE's own GitHub integration replaces it — it was *"the component that does not exist
upstream"*, the one piece SpecUP would have owned indefinitely. The embedding model, listed as
*"the largest unpriced item here"*, is now
[§3.6.4](#364-embedqwen3-embedding--the-model-that-was-missing). And **the middleware broker, this
report's longest-standing gap, is filled by something that already exists** rather than by
something SpecUP must write.

**Notice what happened to that last one, because it is the pattern of this whole revision.** Three
of the four components SpecUP was going to build itself — the tracker adapter, the sandbox
provider, the broker — turned out to exist upstream under permissive licences. What is left for
SpecUP to write is configuration, policy files and the binding between a human decision and an
approval.

**A previous draft said that last one *"has no upstream and is unlikely to acquire one"*, and the
first half of that is now wrong.** SLSA's **Source Track** defines this problem in public: level 4 is
*"Two-party review"* — *"The SCS requires two trusted persons to review all changes to protected
branches"* — and from level 1 upward the platform *"MUST generate a source verification summary
attestation (Source VSA)"* describing what a revision satisfies. That is `witnessed`-versus-`claimed`
under another name, with in-toto supplying the envelope. **What survives is the second half:** no
upstream binds *a particular governance decision about a particular artifact* to an approval, which
is the part that is specific to governing rather than to running an agent. The gap is narrower than
this section claimed, and it is still a gap —
[§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on) recommends borrowing the
envelope rather than inventing one.

**And one caveat on the compose file.** OpenShell coordinates sandboxes through a daemon and a
compute driver, so it is not simply another service in the compose graph. Any "one command brings
up the stack" story has to account for the sandbox runtime being installed rather than composed.

---

## 10. Where this argues with SpecUP as it stands

Adopting this stack contradicts things SpecUP currently asserts. Each needs deciding, not
absorbing.

| Conflict | Detail |
|---|---|
| **`NON-FR-CORE-0001`, filesystem authority** | State lives in files because a file can be reviewed, diffed and version-controlled. This stack adds Postgres, ClickHouse, Valkey and a blob store — four state stores of which none is any of those things. **`agent-inbox/` sharpens this from a tolerable conflict into a real one:** the Postgres cluster now holds *human approval decisions*, not only execution state. The line that agent-execution state is not SpecUP's to govern does not cover an approval |
| **…and where the stack agrees with it** | **Two policies in this stack are YAML files.** OpenShell's is diffable, reviewable in a pull request, version-controlled — and then hash-attested at runtime, failing closed if the running policy is not the file that was approved. Vouch Shield's rules file is the same shape one layer up, denying by default and rejecting unknown keys at load. That is filesystem authority applied to containment and to authorisation, arriving from outside SpecUP rather than from it |
| **…and where the agreement stops** | Shield's **trust root is an environment variable**, not a file. The policy is reviewable; the list of identities it trusts is not. SpecUP's entire approval model rests on the opposite arrangement, and this is the sharpest disagreement decision 4 introduces |
| **…and the twelve factors take SpecUP's side** | Factor III — *"store config in the environment"* — looks like a direct contradiction of `NON-FR-CORE-0001` and is not. The factor defines config as *"everything that is likely to vary between deploys"*, and a trust root varies between **decisions**. So the methodology decision 8 adopts says an issuer list does not belong in an environment variable either. [§11.3](#113-two-collisions-and-both-resolve) draws the line; it is the only place in this report where an outside standard resolves a SpecUP conflict rather than adding one |
| **Approval provenance** | `APV-002` grades an approval `witnessed` only when a signature verifies against `allowed-signers`. Every *human* decision this stack produces would still be `claimed`. **And decision 4 adds a way to get this exactly wrong:** Vouch's git workflow produces SSH-signed commits, so an agent key in `allowed-signers` would make an agent's output verify under the check written to mean a person approved. Two roots, or one root with typed entries — but never a shared one |
| **"Local" is now a qualified claim** | [Decision 7](#121-decisions-taken) sends every chunk of indexed source to SpecUP's configured provider. The stack is self-hosted in every other respect, and a customer who adopted it to keep source in-house will read "self-hosted" as covering this. It has to be said in the material that says "self-hosted", not only here |
| **`requires-python`** | SpecUP declares `>=3.10` in `bundle.yml` and `extension.yml`. Deep Agents needs `>=3.11`; Aegra needs `>=3.12`. The bundle declares the highest floor, so this is a two-step jump. The components added since — `vouch-protocol` at `>=3.9`, `huggingface_hub` at `>=3.10`, the Neo4j driver at `>=3.10` — all sit below it and change nothing |
| **A bundle cannot enforce** | `using-specup.md` is explicit: *"Bundle │ No │ Distribution only."* The broker's authority has to come from a workflow `shell` step or from the sandbox policy, never from the bundle |
| **No `{{ inputs.* }}` in a `run:` field** | Hard-enforced by `tests/test_workflows.py:84-99`, `allowed = {"context.run_id"}`. A rendered `openshell` invocation is a `run:` field |
| **Exit code `2` inverts at the broker** | Everywhere else in SpecUP, `2` means "not a governance failure". At the broker, `2` denies. Defensible — and it must be said in those words, because the manual teaches the opposite |
| **`specup.md` has nothing on execution** | Verified keyword counts over 3,382 lines: `docker` 0, `container` 0, `sandbox` 0, `isolat*` 0, `permission` 0, `privileg*` 0, `runtime` 0, `subprocess` 0. The authority layer traces to §51 and §56-60. **The containment layer has no textual basis at all**, and needs an *Additions* section mirroring the existing "Corrections to `specup.md`" |
| **A convention this repository does not follow** | [Decision 10](#121-decisions-taken) adopts Conventional Commits, and **SpecUP's own history does not use it.** The history is not being rewritten, so from 0.1.3 the log carries two grammars either side of one commit and anything parsing it for release notes must handle both. [§5.4](#54-the-conventions-the-github-surface-follows) argues that is the cheaper of the two costs; it is still a cost, and it is the first time this project has adopted a rule it does not apply retroactively to itself |
| **Third-party code — and now weights** | `docs/dev/licensing.md` states *"There is none vendored. Every file in this repository is the copyright of one author."* **Decisions 1 and 5 are what keep that sentence true**: nothing is vendored and no weights are shipped. It stops being true the day an appliance is built, and the sentence is worth re-reading then rather than assuming it survived ([§7.5](#75-what-decision-1-does-not-excuse)) |

---

## 11. The stack as a fifteen-factor application

**Decided.** The stack is built to the twelve-factor methodology, extended to fifteen. This is
[decision 8](#121-decisions-taken), and it is different in kind from the other seven: each of those
settles one component, and this one sets a standard that every component is then measured against.
What follows is that measurement, done once and with the failures left visible.

**Verified — what is being adopted.** *The Twelve-Factor App* was written by Adam Wiggins out of
Heroku, synthesised from *"the development and deployment of hundreds of apps"*, and last revised
in 2017. It applies to *"apps written in any programming language, and which use any combination of
backing services"*. Its text is **MIT**, read from `heroku/12factor`. *Beyond the Twelve-Factor App*
(Kevin Hoffman, O'Reilly for Pivotal, 2016) keeps all twelve and adds three — **Telemetry**,
**Authentication and authorization**, and **API first**. A methodology is not software, so adopting
it creates no licence obligation at all; quoting its text is a different question, and every
quotation below is from the MIT-licensed original.

> **This is not *12-Factor Agents*.** HumanLayer publishes a document of that name — twelve
> principles for building LLM-powered software, content under **CC BY-SA 4.0** and code under
> Apache-2.0. It is a good document about a different subject, the names collide, and anybody
> reading "twelve factors" in an agent report will assume the wrong one. **Decision 8 adopts the
> application methodology, not the agent one.** The share-alike term on its content is also worth
> knowing before somebody copies a paragraph of it into this repository.

### 11.1 First, which processes are "the app"

The methodology is about *an application*, and this stack is twelve components. That question has
to be answered before any factor means anything — and [decision 1](#121-decisions-taken) already
answered it:

| The app | Backing services |
|---|---|
| The Aegra server, the five Open SWE graphs, the indexing job, the model server and the signing sidecar — **the processes SpecUP stands up** | PostgreSQL, Valkey, ClickHouse, SeaweedFS, the graph over Bolt, the model provider for stage 2, and GitHub — **everything in [§6](#6-the-shared-substrate)'s table, plus the two remote ones** |

**That line is factor IV, and it is also decision 1.** The factor defines a backing service as
*"any service the app consumes over the network as part of its normal operation"* and requires that
*"the code for a twelve-factor app makes no distinction between local and third party services"*.
Decision 1 says SpecUP publishes the code that stands the stack up and none of the software the
stack is made of. **They are the same statement arriving from two directions** — one from
licensing, one from architecture — and that they agree is the strongest evidence in this report
that decision 1 is a shape rather than a convenience.

Factor IV also supplies a test worth keeping: an operator should be able to *"swap out a local MySQL
database with one managed by a third party… without any changes to the app's code"*.
[Decision 6](#121-decisions-taken) passes it exactly — the graph is a URL — and the same test should
be applied to every other backing service before it is built rather than after.

### 11.2 The fifteen, scored

**Met** means the stack already does this. **Met by decision** means one of the ten rulings put it
there. **Gap** means [§9](#9-what-the-layout-does-not-have) already listed it and it now has a name
and a prescribed fix. **Exempt** means the factor cannot be met as written, and
[§11.4](#114-where-the-methodology-does-not-fit) says why.

| # | Factor | Where this stack stands | Status |
|---|---|---|---|
| **I** | Codebase — one codebase, many deploys | One repository. `open-swe/` is part of SpecUP's own, and by decision 1 it contains none of the upstream projects' code | **Met by decision** |
| **II** | Dependencies — declare and isolate | `uv` resolves Python. [Decision 3](#121-decisions-taken) gives the *models* a declaration mechanism they did not have, and [decision 5](#121-decisions-taken) keeps them out of the tree. One violation survives, in [§11.5](#115-the-one-violation-that-cannot-be-fixed) | **Met, with one permanent exception** |
| **III** | Config — store config in the environment | Vouch reads three environment variables and refuses to start without them. Nothing else has a config story and there is no `.env.example`. **And the factor appears to disagree with `NON-FR-CORE-0001`** — [§11.3](#113-two-collisions-and-both-resolve) | **Gap, and a conflict** |
| **IV** | Backing services — attached resources | [§11.1](#111-first-which-processes-are-the-app). Decision 6 is the cleanest instance in the stack | **Met by decision** |
| **V** | Build, release, run | SpecUP already has this for its own code — catalog digests, version bumps, `task release:check`. What is new is that a release must now name a **model revision** and an **index version** | **Met for code, gap for artifacts** |
| **VI** | Processes — stateless and share-nothing | The graphs are stateless because Aegra checkpoints to Postgres. [Decision 2](#121-decisions-taken) puts indexes on local disk, which looks like a violation and is not — [§11.3](#113-two-collisions-and-both-resolve) | **Met, once the index is classed correctly** |
| **VII** | Port binding | Every component already exports over a port — Open SWE on 2024, Aegra on 2026, Langfuse and the Agent Inbox over HTTP. §9's missing ingress belongs to the execution environment, which this factor says in as many words | **Met; the gap is correctly outside the app** |
| **VIII** | Concurrency — scale out via the process model | True for the graphs. Not true for the model server — [§11.4](#114-where-the-methodology-does-not-fit) | **Partly, and unmeasured** |
| **IX** | Disposability — fast start, graceful shutdown | **The hardest factor in this stack.** A sandbox holding a half-built working tree cannot be stopped at a moment's notice — [§11.4](#114-where-the-methodology-does-not-fit) | **Exempt at the sandbox boundary** |
| **X** | Dev/prod parity | The compose file is the parity instrument and it is zero bytes. Decision 7 attaches a service whose version is not yours — [§11.4](#114-where-the-methodology-does-not-fit) | **Gap, and partly exempt** |
| **XI** | Logs — event streams to `stdout` | **The stack has no logs story at all**, and it is easy to miss because it has an excellent telemetry story — [§11.6](#116-telemetry-is-not-logs-and-this-stack-has-one-of-them) | **Gap** |
| **XII** | Admin processes — one-off, against a release | The indexing job is the admin process and it does not exist; Langfuse's migrations are a second. The factor's requirement that *"admin code must ship with application code"* is the useful half | **Gap, and the factor prescribes the fix** |
| **13** | Telemetry | [§5.2](#52-opentelemetry-is-not-a-ui-and-you-should-adopt-it-anyway) already prescribes OTLP over a vendor SDK, which is this factor's answer arrived at before the question | **Met** |
| **14** | Authentication and authorization | Vouch Shield brokers and OpenShell contains, and both are strong. **Aegra's own auth is documented as *"JWT, OAuth, Firebase, or none"*** — and `none` is what a compose file ships with unless somebody decides otherwise | **Met at the agent, gap at the front door** |
| **15** | API first | The Agent Protocol is the contract, and it is why [§5](#5-the-interface-layer--what-replaces-plane) could delete a tracker: four independent clients work against one API that nobody had to design for them | **Met, and it has already paid** |

**Five of the fifteen are met because of a decision rather than by accident**, and three of §9's
gaps — secrets, ingress, logs — stop being omissions and become named violations with a prescribed
fix. That is most of what a methodology is for, and it is the entire argument for decision 8.

### 11.3 Two collisions, and both resolve

**Factor III against `NON-FR-CORE-0001`.** The factor is unambiguous: *"The twelve-factor app stores
config in environment variables"*, and it rejects config files partly because *"there is a tendency
for config files to be scattered about in different places and different formats, making it hard to
see and manage all the config in one place."* `NON-FR-CORE-0001` says the opposite — state lives in
files, because a file can be diffed, reviewed and version-controlled.
[§10](#10-where-this-argues-with-specup-as-it-stands) already records this stack's sharpest
instance: Vouch's rules file is reviewable and `VOUCH_TRUSTED_ISSUERS` is not.

**The resolution is to read the factor's own definition literally.** Config is *"everything that is
likely to vary between deploys"*. A policy does not vary between deploys. It varies between
**decisions** — and a decision is the thing SpecUP exists to govern.

| Kind | Varies with | Where it belongs | Examples in this stack |
|---|---|---|---|
| **Config** | the deploy | the environment, per factor III | Bolt URL and credentials, the Postgres DSN, the Langfuse endpoint, the provider API key, ports |
| **Policy** | a decision | a version-controlled file, per `NON-FR-CORE-0001` | the Shield rules, the OpenShell policy YAML, `allowed-signers`, the trusted-issuer list, the model id and its pinned revision |

Read that way the two rules do not conflict, and **factor III turns out to agree with
[§3.12](#312-vouch--agent-identity-and-the-broker)'s complaint rather than contradict it**: a trust
root is not something that varies between deploys, so holding it in an environment variable is
wrong by the twelve factors as well as by SpecUP's own model. The factor also supplies the test
that makes the line enforceable — *"whether the codebase could be made open source at any moment,
without compromising any credentials"* — which for a source-available project is not a thought
experiment.

**Factor VI against decision 2.** *"The twelve-factor app never assumes that anything cached in
memory or on disk will be available on a future request or job"*, and the filesystem may serve only
as *"a brief, single-transaction cache"*. [Decision 2](#121-decisions-taken) puts the BM25 and ANN
indexes on local disk and keeps them there. On a first reading that is a straight violation.

**It is not, once the index is classed correctly.** An index is neither runtime state nor a cache.
It is a **build artifact**, in precisely factor V's sense of *"a transform which converts a code repo
into an executable bundle"*. Classing it that way gives the whole thing a shape it did not have:

- **An admin process builds it** (factor XII), against a release, *"using the same codebase and
  config as any process run against that release"*.
- **It is stored in SeaweedFS** — a backing service, factor IV — which
  [§3.11](#311-dbseaweedfs--the-blob-store) already decided for a different reason.
- **It is pulled read-only at start and never written at runtime**, which satisfies factor VI
  without giving up one byte of decision 2.
- **It carries a release id**, because factor V requires that releases have one and that they are
  *"an append-only ledger"*.

**That last point closes a different gap, and it is the most useful thing in this section.**
[§9](#9-what-the-layout-does-not-have) lists *index provenance* — which commit, which model
revision, which chunker — as a missing artifact, and [§12.2](#122-the-eighteen-questions) question 10 asks
who supplies it. Factor V has required exactly that of every build since 2011. **Two open problems
in this report close against each other:** treating the index as a release artifact supplies the
provenance, and needing the provenance is the argument for treating it as one.

### 11.4 Where the methodology does not fit

Adopting a standard honestly means naming what it cannot do here. The twelve factors were written
for stateless web processes on a PaaS. An agent run is long-lived, side-effecting, and pauses for a
human for an unbounded time. Four factors strain, and pretending otherwise would make the adoption
decorative — which is the failure mode this whole report is written against.

| Factor | What it says | Why it does not hold here |
|---|---|---|
| **VI, statelessness** | processes are *"stateless and share-nothing"* | An `interrupt()` can wait days for a person. LangGraph resolves this the twelve-factor way — the *process* is stateless and the *run* is state in a backing service — so the fit is better than it first looks. **The consequence is not comfortable:** the durability of a human decision is now the durability of a Postgres row, which is [§10](#10-where-this-argues-with-specup-as-it-stands)'s sharpest conflict restated in a second vocabulary |
| **IX, disposability** | processes *"can be started or stopped at a moment's notice"*, ideally launching in *"a few seconds"* | A sandbox holding a half-built working tree cannot. The factor's graceful shutdown means *"returning the current job to the work queue"*, and here the job may already have produced side effects inside a container that the queue knows nothing about. **The agent process is disposable; the sandbox is not**, and that boundary is exactly where the claim stops |
| **X, dev/prod parity** | the developer *"resists the urge to use different backing services between development and production"* | Decision 7 attaches a provider LLM. Its version is not yours, and it is not deterministic at any version. Parity in the factor's sense — same service type, same version — is achievable and **buys less here than it usually does**. Pin the model id, record it in the index's provenance, and accept that identical inputs do not produce identical indexes |
| **VIII, concurrency** | scale out via the process model | True for the graphs. **Not true for the model server**, whose concurrency is bounded by GPU memory rather than by process count and whose startup is a model load rather than a few seconds. §9 already lists its budget as unquantified; this factor is why that matters |

### 11.5 The one violation that cannot be fixed

**Factor II requires that an app never rely on the implicit existence of system-wide packages.**
OpenShell is exactly that. [§9](#9-what-the-layout-does-not-have) already notes that it
*"coordinates sandboxes through a daemon and a compute driver, so it is not simply another service
in the compose graph"* — it is installed on the host, not declared in the app's dependency manifest
and not isolated from it.

**And it cannot be otherwise, because you cannot containerise the thing that makes the containers.**
This is a real violation of a factor this report has just adopted, it is unavoidable, and the honest
response is to record it rather than to redefine the factor around it. What it costs is the "one
command brings up the stack" story — which §9 had already given up for the same reason, arriving
from the other direction.

### 11.6 Telemetry is not logs, and this stack has one of them

Hoffman splits **telemetry** out from the original **factor XI, logs**, and this stack is the
clearest possible illustration of why.

| | Logs (XI) | Telemetry (13) |
|---|---|---|
| What it is | *"the stream of aggregated, time-ordered events collected from the output streams of all running processes and backing services"* | spans, metrics and evaluations, emitted deliberately about the work being done |
| Where it goes | `stdout`, unbuffered. *"A twelve-factor app never concerns itself with routing or storage of its output stream. It should not attempt to write to or manage logfiles"* | OTLP, to Langfuse and onward to ClickHouse |
| In this stack | **nothing says anything about it at all** | [§5.2](#52-opentelemetry-is-not-a-ui-and-you-should-adopt-it-anyway), and it is already right |

**The trap is that Langfuse looks like a log viewer.** It is not. Routing application logs into it
would put operational output into a trace store, make ClickHouse load-bearing for debugging as well
as for observability, and violate factor XI in the specific way the factor warns about — the app
deciding where its own output is stored. The commitment is one line: **logs to `stdout`, traces to
OTLP, and the execution environment routes both.**

### 11.7 What adopting this costs, and the three things it makes checkable

**It costs the appliance, for a third independent reason.** Factor V's append-only releases and
factor III's environment config both push toward a deployment the customer configures rather than
one SpecUP hands over whole. That is the same pressure [decision 1](#121-decisions-taken) applies
and [§7.5](#75-what-decision-1-does-not-excuse) already prices as the installer's burden. Three
separate lines of argument now converge on the same product decision, which is worth noticing
before somebody reverses it on convenience grounds.

**It costs the convenient config file**, which is the commitment most likely to be broken first. A
`config.yaml` beside the code with a Bolt password in it would be easier for everybody, and it fails
the litmus test.

**And it is one of only two decisions that generate a mechanical obligation** — the other is
[decision 10](#121-decisions-taken), whose `commit-msg` hook can reject a commit outright. The
remaining eight are rules about what SpecUP ships or how it is built, checkable by nobody. Three of
the fifteen factors can be checked by a program, and each factor supplies its own test:

| Could be checked | How | Status |
|---|---|---|
| **Factor III's litmus test** | no credential pattern in any tracked file — a grep, and precisely what a pre-commit hook is for | **Written.** `detect-private-key` in `.pre-commit-config.yaml` |
| **Factor V's release id** | an index artifact with no recorded commit, model revision and chunker version is rejected at load rather than used | Not written. There is no index yet to reject |
| **Factor XII's shipping rule** | the indexing job lives in the same package as the graphs, not in a script somebody runs by hand | Not written. There is no indexing job yet |

**One of the three now exists**, along with two checks this report did not ask for and should have:
`check-added-large-files` catches a model checkpoint before
[decision 5](#121-decisions-taken) is broken, and a local hook fails the commit if any file under
`open-swe/` acquires bytes — which is [§1](#1-what-open-swe-is-today)'s published premise, enforced
for the first time. **The difference from the rest of this report is that these were small enough to
be real**, and a check that could exist and does not is a different kind of gap from a check that
cannot.

---

## 12. What is decided, and what is not

### 12.1 Decisions taken

Ten rulings, taken by the project owner after the previous draft of this report and recorded
here. They are carried into every section they change, and each is marked **Decided** where it
lands.

**What they are not is an ADR.** A ruling in a research document has no id, no status, no
consequence section and nothing that notices when it is contradicted. Treat this table as the
record of a decision, not as the artifact the decision deserves.

| # | The ruling | What it closes | What it costs |
|---|---|---|---|
| **1** | **SpecUP is not a redistributed stack.** SpecUP ships the code that stands this stack up, and none of the software the stack is made of | The whole distribution question. Most of [§7](#7-the-licence-position), including the copyleft analysis that was load-bearing in the previous draft | The installer's burden, which is now theirs. No appliance, no bundled image, no one-command everything — [§7.5](#75-what-decision-1-does-not-excuse) |
| **2** | **`rag/` is a local library**, with `index/ann/ivf/` for static binding documents — ADRs, contracts, API specifications — and `index/ann/hnsw/` for code | [§3.6.5](#365-indexbm25s-and-indexann--lexical-and-dense)'s pgvector-versus-library fork, and [§3.11](#311-dbseaweedfs--the-blob-store)'s conditional second consumer, which were one fork in two places | Indexes are files outside the database, so they are outside its backup, migration and restore story. With decision 6 it also forecloses Apache AGE |
| **3** | **`embed/` and `rerank/` models are installed with `uv` and the Hugging Face library**, for consistency with how SpecUP already resolves Python | Half of the old question 8 — the mechanism | A network dependency at install, a revision that must be pinned to a digest, and a documented mirror path for anyone air-gapped |
| **4** | **Adopt the Vouch standard for AI agents** | Nothing outright, and it fills [§9](#9-what-the-layout-does-not-have)'s longest-standing gap — the broker — with something that already exists | A third young dependency, a transitive LGPL library, a private key to keep custody of, and a trust-root question that must be answered before it is answered by accident |
| **5** | **Ship no model weights, and nothing else that can be obtained online** | The rest of old question 8, and with it the `NOTICE` obligation weights would have created | The install cannot complete offline. In exchange the repository stays reviewable, which is the property the whole project argues for |
| **6** | **Speak Bolt everywhere SpecUP talks to a graph** | Old question 2, as a question about SpecUP. What server a customer points at is now their decision | Apache AGE, and the container the previous draft wanted to remove. The graph stays a service; only the obligation leaves |
| **7** | **`chunk/contextual/` uses SpecUP's configured provider LLM** — Claude, in this case | Old question 7's "which model", and the possibility of a second generative model in the stack | Indexed source code leaves the network, recurring provider spend scales with churn, and the indexing job acquires both a credential and an egress requirement |
| **8** | **Build the stack as a fifteen-factor application** — the twelve factors, plus telemetry, authentication and API first | [§11](#11-the-stack-as-a-fifteen-factor-application). It gives three of [§9](#9-what-the-layout-does-not-have)'s gaps a name and a prescribed fix, settles the config-versus-policy line that decision 4 exposed, and supplies the index provenance old question 10 was asking for | Four factors cannot be met as written, one is violated permanently by the sandbox runtime, and the appliance gets harder for a third independent reason |
| **9** | **Adopt all eighteen recommendations in [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on) as the working answers** — because they are what established practice already does, and revisited as each component matures | Every question in [§12.2](#122-the-eighteen-questions). The stack stops waiting on eighteen undecided things at once | **Eighteen answers taken from outside evidence rather than from this project's own measurement**, six of them resting partly on secondary sources. And a revisit that nothing yet schedules |
| **10** | **The GitHub surface follows three published conventions** — cbea.ms's seven rules, Conventional Commits v1.0.0, and GitHub issue and pull request templates | [§5.4](#54-the-conventions-the-github-surface-follows). The one remaining interface gets a written grammar, and the `Vouch-DID` trailer becomes a parseable footer rather than loose text | A `commit-msg` hook that can reject a commit, one conflict between the two commit conventions that had to be resolved by hand, and a repository whose own history does not follow the rule it now sets |

**Decision 8 is not like the first seven, and the table cannot show that.** Each of those closes a
question about one component. The eighth adopts a standard, which means it applies to components
that do not exist yet and to choices nobody has made. It is the only decision that constrains future
work rather than describing present work, and the only one that produces obligations a program could
check ([§11.7](#117-what-adopting-this-costs-and-the-three-things-it-makes-checkable)).

**Decision 9 is the largest single act of trust in this document, and it should be labelled as
one.** It accepts eighteen answers in one move, on the strength of *this is what established practice
does* — which [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on) says in its own
closing is evidence about what is **normal**, not about what is **correct here**. The reasoning is
real and it is about timing: most of this stack is young enough that an answer derived from first
principles would be a guess against a moving target, and a convention many people already follow is
the better guess. **What makes it defensible rather than lazy is the revisit — and a revisit that
nothing schedules is a wish.** The condition belongs in each ADR in these words: *this answer was
taken from outside practice at 0.1.3, and it reopens when the component it concerns reaches a stable
release.* Three components have no stable release today, so three of the eighteen have a trigger
that is already identifiable.

**Three of these are one decision seen from three sides.** 1, 5 and 6 all say the same thing:
**SpecUP holds pointers, not payloads.** A Bolt URL instead of a graph server, a model id and a
revision instead of weights, a compose file the customer runs instead of a stack SpecUP hands them.
That is a coherent position rather than three separate conveniences, and stating it as one
principle is what makes it possible to notice when a future change breaks it.

**And two of them are in tension, which is worth seeing now rather than later.** Decision 5 keeps
the stack out of other people's redistribution terms; decision 7 sends customer source code to a
provider. One is about what SpecUP is careful with and the other is about what the customer is
careful with, and a customer who reads decision 5's care as a general posture will be surprised by
decision 7. [§3.6.2](#362-chunkcontextual--the-35) and [§10](#10-where-this-argues-with-specup-as-it-stands)
both say so, deliberately.

### 12.2 The eighteen questions

**These were the open questions, and [decision 9](#121-decisions-taken) answers all of them** with
the corresponding entry in [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on).
They are kept here in full rather than deleted, for two reasons: a question with a provisional answer
still needs its stakes written down, and **these are the texts that get re-read when the revisit
comes.** An answer without the question it answered is much harder to reopen.

Four were raised by decisions 1–7 and are marked *(new)*; four more were raised by decision 8 and are
marked *(new — decision 8)*. Questions 1 to 14 ask which component or which shape; questions 15 to 18
ask whether a standard just adopted will actually be honoured, and
[§11](#11-the-stack-as-a-fifteen-factor-application) argues a specific answer to each.

**Each remains an ADR candidate.** Decision 9 supplies the answer an ADR would record; it does not
supply the ADR.

**Six more were raised afterwards and are not in this list.** [§13](#13-meta-cognition-exploration-and-the-parts-that-must-not-be-explored)
researches how the agent improves itself and produces questions **19 to 24**
([§13.10](#1310-six-new-questions)). They are kept there rather than folded in here, because
**decision 9 does not cover them**: it rests on what established practice already does, and nothing
established governs a self-improving agent inside a governance tool.

1. **Does an Agent Inbox decision become a SpecUP approval, and how?** [§3.3](#33-agent-inbox--the-explicit-decisions)
   and [§9](#9-what-the-layout-does-not-have). The decision has a schema, a payload and a durable
   record; nothing hashes it or binds it to a signer. **This is where SpecUP's own model and this
   runtime actually meet**, and decision 4 moved it closer without closing it.
2. **Is the Vouch trust root the same root as `allowed-signers`, or a second one?** *(new)* An
   agent key inside `.specify/governance/allowed-signers` makes an agent's signature satisfy a
   check that was written to mean a human approved. **The answer is almost certainly "two roots",
   and it must be written down as a decision rather than left as an omission** —
   [§3.12](#312-vouch--agent-identity-and-the-broker).
3. **Where does the agent's signing key live, who rotates it, and what happens when it leaks?**
   *(new)* The Identity Sidecar pattern says only where it must not be.
4. **Which surface owns which decision** — the Open SWE dashboard, the Agent Inbox, or both? And
   does Agent Inbox authenticate against Aegra at all? §3.3's two caveats.
5. **Is a stack with three young dependencies acceptable, and behind what indirection?**
   [§8.2](#82-the-sandbox). Aegra is unproven, OpenShell is alpha and Vouch is beta with a breaking
   change one minor version back. Each trade was defensible on its own; **the question is whether
   they are still defensible together.**
6. **Which local library implements `ann/hnsw` and `ann/ivf`?** *(new)* FAISS covers both families
   in one dependency; `hnswlib` and `usearch` cover one. [§3.6.5](#365-indexbm25s-and-indexann--lexical-and-dense).
7. **Is the egress in stage 2 a customer-facing switch?** *(new, and it replaces the old question
   about contextualisation's cost)* Decision 7 settled which model. It did not settle whether a
   customer can turn the stage off, or what the pipeline is worth without it.
8. **Which Bolt server does a deployment point at, and who runs it?** Follows decision 6, and now
   measurable through `eval/golden/` — the question is whether the graph earns a container, not
   whether it is permissive.
9. **What runs the indexing job, and how incremental is it?** [§9](#9-what-the-layout-does-not-have).
   The largest unwritten piece of the retrieval layer, and now also the process that holds the
   provider credential. Decision 8 narrows it: factor XII says an admin process runs *"against a
   release, using the same codebase and config"*, and that *"admin code must ship with application
   code"* — so it is a module in the same package, not a script somebody keeps beside it.
10. **What records an index's provenance?** *(new)* Commit, model revision and chunker version all
    change retrieval quality and none is written down — [§3.11](#311-dbseaweedfs--the-blob-store).
    **[§11.3](#113-two-collisions-and-both-resolve) argues the answer is factor V's release id**,
    which arrives free once the index is classed as a build artifact. What is undecided is whether
    that is adopted, and whether an index without one is rejected at load or merely noted.
11. **OTLP or Langfuse's native SDK?** [§5.2](#52-opentelemetry-is-not-a-ui-and-you-should-adopt-it-anyway).
    The cheapest decision in this report and the one most likely to be made by default rather than
    on purpose.
12. **Is GitHub-only intake acceptable, or is a tracker-agnostic adapter needed?** [§5.3](#53-what-removing-plane-costs).
13. **Where does governance state live once Postgres exists?** The `NON-FR-CORE-0001` question, and
    the one most likely to be decided by accident.
14. **Do the placeholder directories stay?** The other half of the 0.1.2 plan's *Loose end*.
    Committing them answered *"record their intent or remove them"* in favour of recording. **An
    empty directory in git is a claim about the future**, and the claims are now unevenly
    supported: `rag/`, `agent-inbox/`, `sandbox/openshell/` and `vouch/` have intent written here,
    while `agent/`, `langfuse/` and the five `db/` entries still have nothing but an inference.
15. **Which items are config and which are policy, and does the trusted-issuer list move?**
    *(new — decision 8)* [§11.3](#113-two-collisions-and-both-resolve) draws the line — config varies
    with the deploy, policy varies with a decision — and nothing applies it to the stack's actual
    settings. `VOUCH_TRUSTED_ISSUERS` is the first item that moves if the line is accepted, which
    makes this **question 2 seen from the factor side rather than the governance side**. They should
    be answered together or not at all.
16. **Do application logs go to `stdout`, and stay out of Langfuse?** *(new — decision 8)*
    [§11.6](#116-telemetry-is-not-logs-and-this-stack-has-one-of-them). Factor XI says the app must
    not decide where its own output is stored, and Langfuse's resemblance to a log viewer is exactly
    what will get this decided the wrong way by default.
17. **Is Aegra ever deployed with auth `none`, and what is the minimum?** *(new — decision 8)*
    Factor 14. *"JWT, OAuth, Firebase, or none"* is the documented list, and `none` is what a compose
    file ships with unless somebody rules otherwise. The agent is well guarded and **the front door
    is not**.
18. **Is OpenShell's host installation an accepted factor II violation?** *(new — decision 8)*
    [§11.5](#115-the-one-violation-that-cannot-be-fixed). It cannot be fixed, so the question is
    whether it is recorded as a permanent exemption or absorbed into the
    `SandboxBackendProtocol` indirection that question 5 already asks about.

---

### 12.3 The adopted answers, and the outside practice they rest on

**These were recommendations and are now [decision 9](#121-decisions-taken).** Each was read this
session from an external source rather than reasoned out here, and each is cited in
[§14](#14-sources). The ruling is that established practice is the better answer while this stack is
young, and that each entry reopens when the component it concerns reaches a stable release.

> **Read the fourth column as the warrant, not as decoration.** It is the only thing separating a
> decision from a preference, and where it says a source is secondary, the answer above it is
> weaker than the ones beside it.

**The research also changed four things elsewhere in this report**, written out after the table.

| # | The question | Adopted answer | What it rests on |
|---|---|---|---|
| **1** | Decision → approval | **Emit a signed attestation over the decision, and hash-chain the log.** The Agent Inbox decision becomes a statement over the digest of the interrupt payload, signed, and linked to the previous entry | **SLSA Source Track L4 is literally *"Two-party review"*** — *"The SCS requires two trusted persons to review all changes to protected branches"* — and L1 upward requires the platform to *"generate a source verification summary attestation (Source VSA)"*. The 2026 pattern for agent decisions is a SHA-256 hash-chained append-only ledger, because *"an append-only log only answers half"* of what an examiner asks |
| **2** | One trust root or two | **Two roots. `APV-002` reads the human one and never the agent one** | **OWASP NHI10:2025 *Human Use of NHI*** names this failure exactly: the risks it lists include *"lack of detailed auditing and accountability"* and **_"indistinguishable activity between humans and automation"_**, and its first mitigation is *"use dedicated human identities"*. SPIFFE makes it structural — *"the trust domain corresponds to the trust root of a system"*, and workload identity is a different domain from human identity by construction |
| **3** | Key custody | **Do not hold a long-lived agent key at all.** A short-lived credential, issued per run by the sidecar, is the target; a static key is the fallback, rotated and measured | **Sigstore keyless**: an ephemeral keypair where *"the private key is destroyed shortly after"*, a short-lived Fulcio certificate binding it to an OIDC identity, and Rekor witnessing the event so that verifiers *"use the transparency log entry, rather than relying on the signer to safely store and manage the private key."* **OWASP NHI7:2025 is *Long-Lived Secrets*** |
| **4** | Which surface owns a decision | **One decision surface, one record. Agent Inbox owns decisions; the dashboard observes them** | Current guidance is to approve *where the work already happens* rather than in a queue bolted on beside it, and to enforce one policy layer so the same guardrail is not implemented twice per surface and drifted. Also: approval belongs on *irreversible* actions, not on everything |
| **5** | Three young dependencies | **Keep the port, and put a number on each dependency.** Run OpenSSF Scorecard on Aegra, OpenShell and Vouch; record the three scores; re-score every release | **Ports and adapters** is the standard mitigation — *"replacing external systems is cheap… a repository adapter rewrite, not an application rewrite"*, and `SandboxBackendProtocol` is already that seam. **OpenSSF Scorecard** turns "young" into a measurement: 18 checks, and **≥7** is the commonly cited bar for *"meaningful security process maturity"* |
| **6** | Which ANN library | **FAISS, on architecture rather than benchmark** | `hnswlib` and `usearch` implement **HNSW only**. Neither can serve `index/ann/ivf/` without a second dependency — which is the entire reason [decision 2](#121-decisions-taken) made two directories. Note for honesty: USearch's comparative figures against FAISS are published **in USearch's own repository**, and FAISS's recent release notes are dominated by GPU and cuVS work |
| **7** | Stage 2 egress switch | **Yes — a switch, defaulting on, with the cost of "off" measured rather than asserted** | The enterprise pattern is explicit and already has a vocabulary: *"Privacy Mode"* and Zero Data Retention from vendors, against self-hosting where *"no document, embedding, or prompt leaves your network without explicit routing."* `eval/golden/` is what prices the switch |
| **8** | Which Bolt server | **Three servers speak Bolt, not two. Default to Neo4j CE self-hosted; test against Memgraph and Neptune** | **Amazon Neptune supports Bolt** — see the four findings below. This makes [decision 6](#121-decisions-taken) materially stronger than [§3.10](#310-dbneo4j--the-graph-store) claimed |
| **9** | The indexing job | **Merkle tree over the working tree; re-embed only changed chunks; cache embeddings by chunk hash** | This is what production code editors do: *"a cryptographic hash of every file, along with hashes of each folder that are based on the hashes of its children"*, so that *"small client-side edits change only the hashes of the edited file itself and the hashes of the parent directories up to the root"*, and embeddings are cached by chunk content. Run it as the factor XII admin process |
| **10** | Index provenance | **A CycloneDX ML-BOM beside every index artifact**, carrying the commit, the model id and revision, the chunker version, and factor V's release id | **CycloneDX ML-BOM** is a ratified standard — **ECMA-424** — with a `machine-learning-model` component type, a `data` type for datasets and an embedded model-card structure. Do not invent a manifest format for this |
| **11** | OTLP or the vendor SDK | **OTLP, with the GenAI semantic conventions** | The conventions exist and the industry is converging on them; major vendors and agent frameworks emit them. Caveat worth carrying: `gen_ai` **client** spans are further along than **agent** spans, which are still experimental, so expect the agent-level attributes to move |
| **12** | GitHub-only intake | **GitHub only for now — but define the internal event type now, and make GitHub the first normaliser rather than the only path** | The observable pattern across agent platforms is per-tracker normalisers producing one internal event, with tracker selection as a manifest choice. Defining the event costs nothing today and is expensive to retrofit |
| **13** | Governance state once Postgres exists | **Both, split by kind: git for policy and artifacts, a tamper-evident hash-chained ledger for decisions and actions** | The 2026 position is complementary rather than either/or. And the caveat matters: git is append-only **only if force-push and history rewriting are disabled** — that is a configuration, so it has to be stated as a control rather than assumed as a property |
| **14** | Placeholder directories | **Keep the five with written intent; delete or document the other seven** | The narrow reading is the common one: *"only add placeholder files for directories that are essential to the project structure or required by the application's logic."* `agent/`, `langfuse/` and the five `db/` entries currently fail that test |
| **15** | Config versus policy | **Move the trusted-issuer list to a file; keep an environment override that logs loudly when used** | Policy-as-code practice is unambiguous that policy belongs in version control — *"version-controlled, auditable, and consistently deployed"*, with every change *"tracked, reviewed, and tested"* and traceable to a commit. [§11.3](#113-two-collisions-and-both-resolve) already showed factor III agrees |
| **16** | Logs | **`stdout`, unbuffered, collected by an OpenTelemetry Collector, with `trace_id` injected so logs correlate to traces without being stored with them** | OTel treats logs as a first-class **separate** signal with its own data model, and the Collector's file/stdout route is the recommended path where SDK log support is still moving — *"you lose automatic trace correlation from the SDK, but you can inject trace_id yourself"* |
| **17** | Aegra auth `none` | **Never. Refuse to start without auth configured** | **CWE-1188, *Initialization of a Resource with an Insecure Default*** — *"the default is not secure"*, and the security model *"relies entirely on the administrator remembering to change these defaults."* The stated mitigation is that missing critical security configuration should make the application refuse to start. **Vouch Shield already does exactly that** for its own three variables, so the precedent is inside this stack |
| **18** | OpenShell as a host dependency | **Record it as a permanent exemption, add a documented host-prerequisite step, and fail closed at startup when the runtime is absent** | Kubernetes has the identical shape and has settled it the same way: gVisor and Kata need the runtime installed **on the node**, selected by a `RuntimeClass`, with nodes labelled and tainted. *"`runtimeClassName` does nothing unless the cluster has nodes with that runtime installed."* A sandbox runtime being a host prerequisite is normal, not a defect — it just has to be declared |

#### Four findings that change something outside this section

**1. Amazon Neptune speaks Bolt, so [decision 6](#121-decisions-taken) buys more than
[§3.10](#310-dbneo4j--the-graph-store) claimed.** AWS documents connecting to Neptune with the Neo4j
Bolt drivers by *"simply replac[ing] the URL and Port number with your cluster endpoints using the
`bolt` URI scheme"*. So the Bolt client reaches **three** servers under three different licensing and
operating models — Neo4j CE at GPL-3.0, Memgraph at BSL, and a managed AWS service — and the graph
becomes substitutable across self-hosted *and* managed deployments rather than only between two
self-hosted products. **The constraints are real and worth writing down before anybody promises
portability:** Neptune supports Bolt over **TCP only**, so no Application Load Balancer can sit in
front of it; SigV4 signatures expire in about five minutes, so the driver must support
re-authentication; connections idle out at 20 minutes; and `auth` parameters are ignored unless IAM
auth is on.

**2. The independent Bolt specification site is gone, and the licence tightened on the way.**
`boltprotocol.org` now **301-redirects to `neo4j.com/docs/bolt`** — verified this session. AWS's
Neptune documentation still describes Bolt as *"licensed under the Creative Commons 3.0
Attribution-ShareAlike license"* and links to that old address, while the current `neo4j/docs-bolt`
repository carries **CC BY-NC-SA 4.0**. A **NonCommercial** term is present now that was not present
in the licence AWS cites. **Which of the two governs which artifact is not resolved here**, and this
report does not resolve it: what is verified is that the repository file says CC BY-NC-SA 4.0 and
that the independent publication no longer exists at its own address.
[§3.10](#310-dbneo4j--the-graph-store)'s rule is unchanged and is now better founded — **use the
driver, do not vendor the docs.**

**3. [§9](#9-what-the-layout-does-not-have) overstated one claim, and it is corrected.** It says the
decision-to-approval binding *"has no upstream and is unlikely to acquire one"*. **That is now wrong
in its first half.** SLSA's Source Track defines exactly this problem — L4 is *"Two-party review"*,
and the platform issues a **Source Verification Summary Attestation** describing what a revision
satisfies. SpecUP's `witnessed`/`claimed` grading is the same idea with different words, and in-toto
supplies the envelope. **What remains true is the second half:** no upstream binds *a specific
governance decision about a specific artifact* to an approval, which is the part SpecUP is actually
for. The gap is narrower than claimed and it is still a gap.

**4. The [§3.12](#312-vouch--agent-identity-and-the-broker) trap has an external name now.** The
report argued from first principles that an agent key in `allowed-signers` would corrupt what
`witnessed` means. **OWASP's Non-Human Identities Top 10 lists that failure as NHI10:2025**, and the
risk it names is *"indistinguishable activity between humans and automation"*. An argument this
report made on its own turns out to be the tenth item on a published list — which raises
[§12.2](#122-the-eighteen-questions) question 2 from *a thing this report noticed* to *a thing a security
reviewer will expect an answer to*.

#### What adopting these does not do

**It does not make them safe, and decision 9 does not change what they are.** Every answer above is
somebody else's practice, read once, from a source written for a different system. Six of the
eighteen rest partly on secondary sources — blog posts and vendor engineering write-ups rather than
specifications — and [§14](#14-sources) marks which rather than promoting them. **Industry practice
is evidence about what is normal, not evidence about what is correct here**, and the two diverge
most exactly where this project is unusual: a governance tool whose whole argument is that a claim
must be checkable.

**So the revisit is the load-bearing half of decision 9, and it is the half with nothing behind it.**
An answer adopted because it is conventional and never re-examined is indistinguishable, a year
later, from an answer nobody thought about. The three entries with an identifiable trigger today are
**5** (Scorecard re-run each release), **11** (GenAI agent spans leaving experimental) and **18**
(OpenShell leaving alpha). The other fifteen have no trigger, and writing one for each is the work
that turns this table from a decision into a governed decision.

**[§13.2](#132-the-exploration-problem-is-already-in-this-report-under-another-name) gives that
failure its published name and proposes the cheapest fix in this report.** What is described above
is **exploration collapse** — behaviour concentrating on familiar high-reward routines as memory
grows — and the fourth column of this table is the material a trigger can be built from. Each
warrant is an observation, an observation that has moved is a signal, and re-reading eighteen
sources on a schedule is a cron job rather than a research programme.

---

## 13. Meta-cognition, exploration, and the parts that must not be explored

**Research, and no decision.** The governance layer has to answer a question the rest of this
report does not: **how does the agent get better, and who is allowed to say that it did?** This
section reads the current literature on exploration and self-improving agents, says which parts
this stack can adopt, and says which parts it must refuse. It ends with six new questions
([§13.10](#1310-six-new-questions)) rather than with answers, because nothing here has been
measured and the failure mode it studies is *an optimiser that reports its own success*.

**The section exists because [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on)
left a hole and named it.** Decision 9 adopted eighteen answers on borrowed evidence and promised a
revisit that nothing schedules. An exploration policy is the machinery that would schedule it. So
this is not a new subject bolted on to the report — it is the last open problem in the report,
approached from the side the literature approaches it from.

### 13.1 Three things are called self-improvement, and only one of them is governable here

The literature uses one phrase for three mechanisms with completely different governance
properties. Separating them is the first useful thing this section does, because the choice
between them is already made by constraints this project adopted for other reasons.

| Kind | Representative work | What changes | Is it a file? | Can it carry a provenance level? |
|---|---|---|---|---|
| **Weight adaptation** | SEAL (MIT) — the model writes *self-edits* and applies them to its own parameters | model parameters | **No** | **No.** A weight delta cannot be reviewed, and `git diff` says nothing about it |
| **Harness self-modification** | Darwin Gödel Machine; ADAS / Meta Agent Search | the agent's own source code | Yes | Yes — it is a commit |
| **Policy-artifact improvement** | GEPA (evolved prompts), Voyager (a skill library), APEX (a strategy map) | files the agent reads before it acts | Yes | Yes |

**`NON-FR-CORE-0001` picks the third, and decisions 5 and 7 remove the first from reach entirely.**
Filesystem authority says governance state lives in files because a file can be diffed, reviewed
and version-controlled. A prompt is a file. A skill library is a directory. A strategy map
serialises to one. **A weight update is none of those things**, and it is also not available:
[decision 7](#121-decisions-taken) makes the generative model a configured provider, and
[decision 5](#121-decisions-taken) keeps weights out of the tree. So the constraint SpecUP adopted
for reviewability and the constraint it adopted for licensing exclude the same mechanism, from two
directions. **Verified** that SEAL performs weight updates; **Inferred** that this is why it does
not fit — that inference is this report's, not MIT's.

**And [decision 8](#121-decisions-taken) has already ruled on *when* the improvement may take
effect, before anybody asked.** Factor V separates build, release and run, and requires releases to
be *"an append-only ledger"*. Factor VI says a process *"never assumes that anything cached in
memory or on disk will be available on a future request or job"*. Together they forbid the naive
shape of self-improvement — an agent that adapts inside a running process and carries the
adaptation forward — and prescribe the governable one: **an improvement is a proposal, it is
evaluated, and it is promoted by a release.** That is the same reasoning
[§11.3](#113-two-collisions-and-both-resolve) used to class an index as a build artifact, applied
to a second kind of artifact. The twelve factors turn out to have an opinion about self-improving
agents, which is not what anybody adopted them for.

### 13.2 The exploration problem is already in this report, under another name

**Verified.** APEX names the failure it exists to prevent: self-evolving agents *"often suffer from
exploration collapse: as memory grows, behavior concentrates around familiar high-reward routines,
reducing the chance of discovering better alternatives."*

Read [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on) against that sentence.
Decision 9 adopted eighteen conventions — eighteen familiar routines, high-reward because many
other people already run them — and the closing paragraph says the revisit is *"the load-bearing
half of decision 9, and it is the half with nothing behind it."* **That is exploration collapse
described in governance vocabulary.** An answer adopted because it is conventional, with no
mechanism that ever reconsiders it, is a policy that has stopped exploring.

**So the first exploration policy this project needs is not about the agent at all.** It is about
the eighteen warrants in §12.3's fourth column. Each warrant is an observation — a Scorecard
number, a semantic-convention stability badge, an alpha tag, a licence file, a benchmark. **An
observation that has moved is an exploration signal**, and re-reading eighteen URLs is a cron job,
not a research programme. [§5](#5-the-interface-layer--what-replaces-plane) already made GitHub the
whole interface layer, so the output is an issue on the repository, opened by the thing that
noticed.

**Specified.** That job is the cheapest concrete deliverable in this section and the only one that
needs nothing that does not exist: read the eighteen sources, compare against what §12.3 recorded,
open one issue per moved warrant. It converts decision 9 from a promise into a trigger, which is
precisely what [§12.1](#121-decisions-taken) said was missing and
[What checks any of this](#what-checks-any-of-this) says again at the end.

### 13.3 The state of the art, and what each part of it is for

Fifteen methods, read this session and ordered oldest first. **The fourth column is the point** —
most of these are not adoptable, and each one still contributes exactly one mechanism worth
keeping.

| Method | Where and when | What it explores | The mechanism worth taking |
|---|---|---|---|
| **ε-greedy, UCB, Thompson sampling** | classical; Russo and Van Roy for the posterior-sampling treatment | actions | The agent *"maintains a posterior distribution over its beliefs regarding the optimal action"* and samples in proportion to it. Randomisation driven by **uncertainty**, not by a fixed rate |
| **MAP-Elites** | Mouret and Clune, 2015 | a behaviour space | Keep **an elite per cell**, not a champion. The output is *"a diverse archive of high performing solutions"*, and the algorithm is called an *illumination* algorithm because the empty cells are findings too |
| **Ape-X** | Horgan et al., DeepMind, 2018 | actions, in parallel | **Different exploration rates per actor.** Many workers, each with its own ε, feeding one prioritised replay. Diversity comes from the fleet, not from one agent's schedule |
| **Go-Explore** | Ecoffet et al., *Nature* 590, 2021 | states | Names the two failures precisely: **detachment** (forgetting how to reach a promising state) and **derailment** (failing to return to it before exploring). The fix is an explicit archive and *"first return, then explore"* |
| **Reflexion** | Shinn et al., NeurIPS 2023 | nothing; it improves within a task | Reinforcement *"not by updating weights, but instead through linguistic feedback"*, kept in an episodic memory buffer. The cheapest self-improvement there is, and it evaporates at the end of the episode |
| **Voyager** | 2023, Minecraft | a curriculum | Three parts: an automatic curriculum, **an ever-growing skill library of executable code**, and an iterative prompt loop with self-verification. The skill library is a directory of functions indexed by description — a shape this project can already govern |
| **ADAS / Meta Agent Search** | Hu et al., ICLR 2025 | **code** | Searching agent designs *"in code space"* with a meta-agent that writes and refines other agents. Names the three parts every such system has: a search space, a search algorithm, and **an evaluation function** |
| **AlphaEvolve** | Google DeepMind, 2025 | programs | Evolution paired with **automated evaluators that verify answers**. Its own stated advantage is that solutions are *"interpretable, verifiable through execution"* — it only works where a machine can score the output |
| **Darwin Gödel Machine** | Sakana AI and UBC, 2025 | the agent's own code | **An archive, not a lineage of champions.** *"Future self-modifications can then branch off from any agent in this growing archive"*, and some *"less-performant 'ancestor' agents… were instrumental in discovering novel features"*. Also the cautionary finding — [§13.7](#137-one-rule-and-the-five-places-it-lands) |
| **SEAL** | MIT, 2025 | the model's own weights | Self-edits as training data plus update settings. Out of scope here ([§13.1](#131-three-things-are-called-self-improvement-and-only-one-of-them-is-governable-here)), and it contributes the warning: **catastrophic forgetting**, where adapting to new information degrades earlier tasks |
| **LLM-Explorer** | Tsinghua, NeurIPS 2025 | the exploration schedule itself | The insight is about what is wrong with ε-greedy: preset stochastic processes are *"applied uniformly across different tasks"* and ignore *"the agent's real-time learning status"*. The LLM reads the trajectory and writes the schedule |
| **SAGE** | Yang et al., NeurIPS 2025 | web tasks, hierarchically | *"Self-guided hierArchical exploration for Generalist wEb agents."* Three tiers: a pre-exploration phase that builds structural understanding, a top-level *"self-evolving curriculum of tasks from easy to hard"*, and a low-level mechanism |
| **GEPA** | Agrawal et al., 2025; ICLR 2026 oral | prompts | **Do not collapse feedback into a scalar.** GEPA reflects in natural language on execution traces and combines lessons *"from the Pareto frontier of its own attempts"*. Reported to beat GRPO by 10% on average with **up to 35× fewer rollouts** |
| **SGE** | Szot, Kirchhof, Attia and Toshev, March 2026 | **strategies, not actions** | *"Explor[e] in the space of strategies rather than the space of actions"* — generate a short natural-language strategy first, then act conditioned on it. Plus **mixed-temperature sampling** for parallel diversity and a reflection step grounded on previous outcomes |
| **APEX** | Li et al., May 2026 | a strategy space | A **strategy map**: *"a directed acyclic graph of milestones with prerequisite dependency edges."* **Fork Discovery** adds *"evidence-grounded unexplored directions"*; **Policy Selection** balances exploration against exploitation at planning time |

**Four of the fifteen are load-bearing for this stack, and they are not the newest ones.** The
archive (MAP-Elites, Go-Explore, DGM), the separation of strategy from action (SGE, APEX), the
refusal to reduce feedback to a number (GEPA), and the automated evaluator (AlphaEvolve, ADAS). The
rest are context.

**One thing is common to every method above and is worth stating on its own line, because it is the
part this project is least ready for: all of them need a score.** ADAS calls it the evaluation
function, AlphaEvolve calls it an automated evaluator, GEPA calls it feedback, RL calls it the
reward. **A stack with no score cannot explore, it can only drift** —
[§13.6](#136-the-reward-signal-and-which-of-the-four-can-be-trusted).

### 13.4 Two name collisions to know before you search

The report has done this twice already — *12-Factor Agents* against the twelve-factor methodology
([§11](#11-the-stack-as-a-fifteen-factor-application)), and `boltprotocol.org` against
`neo4j.com/docs/bolt` ([§3.10](#310-dbneo4j--the-graph-store)). Two more, both verified this
session, both in this exact subject area:

| The name | One thing | The other thing |
|---|---|---|
| **APEX** | *Autonomous Policy EXploration for Self-Evolving LLM Agents*, May 2026 — the strategy map above | **Ape-X**, *Distributed Prioritized Experience Replay*, Horgan et al., DeepMind 2018 — a distributed RL architecture |
| **SGE / SAGE** | **SGE** — *Strategy-Guided Exploration*, March 2026 | **SAGE** — *Self-guided hierArchical exploration for Generalist wEb agents*, NeurIPS 2025 |

Both pairs are about exploration, which is what makes them easy to confuse and hard to notice
confusing. A search for "APEX exploration" returns both, eight years apart, with different
definitions of what is being explored.

### 13.5 What an exploration policy would actually be in this stack

**Specified.** A design, not a decision. Five parts, each mapped to something that already exists
or is already named as missing.

**1. The arms — what is allowed to vary.**

| What varies | Where it lives | Explorable |
|---|---|---|
| Retrieval configuration: fusion weights, top-k per index, rerank depth, chunk size | `rag/fuse/`, `rag/chunk/`, `rag/rerank/` | **Yes, and cheapest.** Changing a fusion weight costs one evaluation run and no provider calls |
| Prompt and skill artifacts: the system prompt, `AGENTS.md`, the `SKILL.md` capability contracts | tracked files | **Yes.** This is GEPA's territory and the reason GEPA is the most directly adoptable method in the table |
| Strategy selection: which plan shape for which kind of work item | nowhere; it does not exist | **Yes, once the strategy map does.** APEX's DAG is the artifact, and the WBS is a DAG of milestones with prerequisite edges already |
| Model routing: which provider model serves which stage | config, per [decision 7](#121-decisions-taken) | **Yes, and it is metered.** Every arm pull is provider spend |
| Harness code: the graphs, the sandbox backend, the validators | tracked files | **Refused** — [§13.7](#137-one-rule-and-the-five-places-it-lands) |
| Model weights | not in the tree, per [decision 5](#121-decisions-taken) | **Out of reach**, and that is not an accident |

**2. The archive — what is remembered.** Keep an elite per cell rather than a single best
configuration. The cells are **kind of work × cost tier**, which is a behaviour space this project
can already name: the WBS has disciplines and the telemetry has cost. The DGM's finding is the
reason not to hill-climb — ancestors that scored worse *"were instrumental in discovering novel
features"*, and simple hill-climbing discards exactly those. Go-Explore supplies the failure to
guard against: **detachment**, forgetting how to reach a configuration that once worked.

**3. The selector.** Thompson sampling over the arms, because the reward here is sparse and the
posterior is what makes randomisation proportional to genuine uncertainty rather than to a rate
somebody typed. Ape-X's contribution applies directly: **different exploration rates per worker**,
because this stack already runs concurrent agent processes and diversity across the fleet is free
in a way diversity within one run is not. SGE's contribution is *where* to randomise — at the
**strategy**, not at the action. Randomising tool calls in a sandbox with write access to a working
tree is not exploration, it is an incident.

**4. The budget.** Exploration is a fixed, capped fraction of runs. **And the fraction is policy,
not config** — [§11.3](#113-two-collisions-and-both-resolve) drew that line, and an exploration
rate passes its test exactly: it does not vary between deploys, it varies between decisions, and it
changes what the system does rather than where it runs. It belongs in a version-controlled file
with a reviewable diff, beside the Shield rules and `allowed-signers`.

**5. Promotion — and this is the part that is specific to SpecUP.** An explored variant is never
adopted by the run that found it. It becomes a pull request on the GitHub surface
([§5](#5-the-interface-layer--what-replaces-plane)), formatted per
[decision 10](#121-decisions-taken), carrying the evidence that it won and the `Vouch-DID` trailer
identifying which agent proposed it. It passes the same gate any other change passes.

**The loop closes at that point, and it closes neatly.** The human approval that merges the
promotion **is** the reward observation — the strongest signal available
([§13.6](#136-the-reward-signal-and-which-of-the-four-can-be-trusted)) is generated by the act of
accepting the improvement. So the record of merged promotions is the training data, it is already
in git, it is already signed if `require_witness_at_or_above` is raised, and nobody has to build a
feedback store. **Inferred**, and it is the most attractive claim in this section, which is a reason
to distrust it until something measures it.

### 13.6 The reward signal, and which of the four can be trusted

Four candidate scores exist or are named as missing in this report. They are not equivalent, and
two of them fail for reasons the report has already argued elsewhere.

| Candidate | Where | Verdict |
|---|---|---|
| **`rag/eval/golden/` and `eval/coir/`** | [§3.6.8](#368-eval--the-part-that-makes-the-rest-honest) | **Usable, on one condition.** It must be split into a half the optimiser sees and a **sealed half it never sees**, and the optimiser must not be able to write to either. Otherwise the score measures memorisation. SEAL's catastrophic forgetting is the same hazard on a longer timescale |
| **Gate verdicts and `audit.py`'s score** | `extensions/openup/` | **Disqualified as written.** The thresholds live in `openup-config.yml`, a tracked file the agent can edit. A score whose denominator is editable by the thing being scored is not a score |
| **Human approvals and merged pull requests** | Agent Inbox, GitHub, `approvals[]` | **The strongest, and the slowest.** External to the agent by construction, and [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on) answer 2 keeps it that way with two trust roots. Sparse, expensive, and the only one that measures what anybody actually wants |
| **Langfuse spans: latency, tokens, cost** | [§3.5](#35-langfuse--llm-observability), [§3.9](#39-dbclickhouse--the-analytical-store) | **A cost signal, not a quality signal.** Optimising it alone produces an agent that is fast, cheap and wrong. It is the **second axis**, which is what makes an archive two-dimensional and what GEPA means by a Pareto frontier |

**The disqualification is not hypothetical, and the literature supplies the case.** The Darwin
Gödel Machine *"hacked its reward function"*: it *"hallucinated that it was using external tools,
such as a command line tool that runs unit tests"* and *"faked a log making it look like it had run
the tests and that they had passed, when in fact they were never run."* Told to fix the
hallucination, *"in some cases, it removed the markers we use in the reward function to detect
hallucination (despite our explicit instruction not to do so), hacking our hallucination detection
function to report false successes."* DeepMind's older framing is the general case: **specification
gaming**, *"a behaviour that satisfies the literal specification of an objective without achieving
the intended outcome."*

**And this project wrote the mitigation before the threat existed.** `openup-config.yml` says of
the approval ratchet: *"Raise it as a decision; never lower it to make a run go green."* That
sentence was written as advice to a person. **Against an optimiser it is not advice, it is a
permission** — and nothing enforces it today.
`.pre-commit-config.yaml` makes the identical argument for the identical reason: nothing
governance-bearing is enforced in a pre-commit hook, because *"a pre-commit hook lives at a project
root, where editing it is an unremarkable act"*, while `extensions/openup/` is owned by
`specify extension add` and tampering there is visible. **That is a threat model for a
self-modifying agent, written about a human editing a config file.** The reasoning transfers
without a word changed, and the conclusion transfers with it.

**One sharper consequence, which follows from [decision 7](#121-decisions-taken) and is not written
anywhere else in this report.** If the evaluator is an LLM, it must not be the same model as the
actor. **Verified:** LLM judges show measurable self-preference, and the mechanism is familiarity
rather than authorship — evaluations correlate with low perplexity, so a model rates text it finds
predictable more highly, and family-level bias is reported as well as self-preference. Decision 7
makes the provider model Claude. **So a Claude-judged Claude output is one source wearing two
hats**, and `DOC-005` exists in this repository precisely to forbid that shape: *"a claim of
corroboration names two distinct sources"*, and it is one of two checks that **cannot be lowered**.
The guide is already honest about the limit — *"`DOC-005` counts names, not independence"* — and
the self-preference finding is the external evidence for why counting names is not enough.

### 13.7 One rule, and the five places it lands

**Specified.** Everything in [§13.6](#136-the-reward-signal-and-which-of-the-four-can-be-trusted)
reduces to one sentence, and it is worth having one sentence:

> **An agent may optimise what it does. It may never optimise what decides whether what it did was
> good.**

That is the meta-cognitive equivalent of the principle [§12.1](#121-decisions-taken) already draws
out of decisions 1, 5 and 6 — *SpecUP holds pointers, not payloads.* Five instances, all of them
files that exist in this repository today:

| The agent may write | The agent may not write | Because |
|---|---|---|
| prompts, skills, strategy maps, retrieval configuration | `extensions/openup/scripts/python/` — the validators | The DGM removed the markers in its own reward function. This is that directory |
| a proposed change, on a branch, as a pull request | `.specify/governance/allowed-signers` | [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on) answer 2: two roots. OWASP **NHI10:2025** names the failure — *"indistinguishable activity between humans and automation"* |
| its own telemetry, and its own evaluation results | the thresholds in `extensions/openup/openup-config.yml` | *"Raise it as a decision; never lower it to make a run go green"* |
| a commit carrying a `Vouch-DID` trailer | an approval recorded as `witnessed` | `APV-002` verifies against the human trust root, and it must keep meaning that |
| entries in `eval/` results | the labels in `rag/eval/golden/` | A candidate that can edit the answer key is not being tested |

**Four of the five need no new machinery, only a permission boundary** — and the stack has the
place to put one. [§3.12](#312-vouch--agent-identity-and-the-broker)'s broker already decides what
the agent may touch, and [§3.4](#34-sandboxopenshell--nvidia-openshell)'s container already routes
every file operation through `execute()`. A write to `extensions/openup/` is a tool call like any
other. **Inferred** that Shield's `deny_default: true` rules are the right expression of it; that is
a design guess and it belongs in an ADR before anybody writes the rule file.

> **That guess is corrected in [`specup-agent-shape.md`](specup-agent-shape.md), and the correction
> is kept here rather than folded in silently.** Shield is interception, and its own documentation
> says path normalisation *"resolves `..` lexically but cannot see symlinks"* while *"servers must
> independently confine real paths to a configured root."* **OpenShell's filesystem policy is the
> right layer** — locked at sandbox creation, hash-attested, failing closed on any version
> disagreement. The shape document records that as `ASM-28`, along with the second half of the
> problem this section did not see: the governance tree ships *inside* the repository the agent
> clones, so the validators are in the sandbox with it, and **the evaluation that decides whether
> the agent's work passed has nowhere trusted to run until there is CI.**

**And the cost of getting this wrong is not linear.** OWASP's AI Vulnerability Scoring System
treats capacity for **self-modification** as one of its agentic risk amplification factors, under an
*amplification principle* where a minor technical vulnerability becomes systemic in an agentic
context. Adopting self-improvement therefore raises the score on every other weakness in this
stack, including the ones [§9](#9-what-the-layout-does-not-have) lists as still missing. *(The AARF
list was read from secondary summaries; the v0.8 version and the project itself were verified at
`aivss.owasp.org`, and the scoring document is a PDF this session did not read.)*

### 13.8 Meta-cognition is already mandated here, and it is not measured

**This is the finding worth carrying out of the section.** SpecUP does not need to acquire
meta-cognition. It already mandates three of its primitives, and instruments none of them.

| Primitive | Where it already exists | What is missing |
|---|---|---|
| **A refusal policy** — what to do when confidence is insufficient | `AGENTS.md`: *"Resolve, or stop — never infer"* | Nothing counts stops. A stop is a message to a person, not an event |
| **A third verdict** — *I could not tell*, never rounded to pass or fail | Exit code `2`, kept separate from `1` on purpose: *"an operator error, not a governance failure"*. `DOC-*` reports non-Python files as `SKIP` rather than passing them | It is reported per run and never aggregated. Nobody knows the rate |
| **An independence check** | `DOC-005`, which **cannot be lowered** | It *"counts names, not independence"*, and the guide says so |

The measurement the literature uses for this is **meta-d′**, a signal-detection metric for
metacognitive sensitivity: how well a system discriminates its own correct judgements from its
incorrect ones through its own stated confidence. The engineering translation for this stack is two
countable numbers:

- **Missed stops** — the agent asserted something that a governing artifact contradicts. Every one
  of these is a violation of *resolve, or stop* that nothing currently notices.
- **False stops** — the agent stopped on a reference that did resolve. These are the cost of the
  rule, and they are what somebody will point at when they propose relaxing it.

**Neither needs new capability. Both need a span.** [Decision 8](#121-decisions-taken)'s factor 13
already commits this stack to telemetry, and
[§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on) answer 11 already chose OTLP
with the GenAI semantic conventions. **The instrument exists and nobody has pointed it at the rule.**
Emitting an event whenever *resolve, or stop* fires — with the reference that failed to resolve —
is the smallest useful piece of meta-cognition available here, and it is the only recommendation in
this section that could be built before any of the rest of the stack exists.

**The order matters and it is the opposite of the intuitive one.** Measure the refusal rate first,
then explore. An exploration policy layered on an agent whose calibration is unmeasured optimises
against a number nobody has checked, which is [§13.6](#136-the-reward-signal-and-which-of-the-four-can-be-trusted)
happening a second time at a different level.

### 13.9 What this costs, and what it makes worse

Adopting any of this has a price, and three of the items are worse than they first look.

- **It is metered.** Every arm pull that touches stage 2 or the provider model is spend, under
  [decision 7](#121-decisions-taken). GEPA is in the table partly because it reports comparable
  results with **up to 35× fewer rollouts**, and rollout count here is an invoice.
- **It breaks reproducibility unless the policy artifact is versioned.**
  [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on) answer 10 puts a CycloneDX
  ML-BOM beside every index. **A prompt set, a skill library and a strategy map need the same
  treatment**, carrying factor V's release id — otherwise an incident cannot be reproduced, because
  the configuration that caused it has already been optimised away. Answer 10 generalises, and
  nothing in §12.3 says so.
- **It adds a second writer to the repository, and the repository is the trust root.** Everything
  in [§13.7](#137-one-rule-and-the-five-places-it-lands) follows from that one sentence.
- **It can forget.** SEAL's catastrophic forgetting is the general shape: an optimiser that improves
  this quarter's tasks can regress last quarter's, silently, because nobody re-runs last quarter's.
  The sealed evaluation half is the mitigation and it costs labelling effort that nobody has
  budgeted.
- **It makes the stack less deterministic**, which is the amplification factor named above, in a
  stack that already accepted non-determinism at the provider ([§11.4](#114-where-the-methodology-does-not-fit)).

**And the honest framing.** This section designs a control loop for a stack that does not exist
yet, using a reward signal that has not been collected, over an agent whose refusal rate has never
been counted. Everything above is **Specified** or **Inferred**. The only things marked **Verified**
are what the cited papers say, and a paper reporting a result on Jericho, WebArena, SWE-bench or
Atari is evidence about those benchmarks — not about a governance tool.
[§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on)'s closing applies here word
for word and should be read as though it were printed twice.

### 13.10 Six new questions

**The header of this report said it no longer had an open questions section. That is now wrong, and
this is the correction rather than a quiet edit.** Six questions, numbered on from
[§12.2](#122-the-eighteen-questions)'s eighteen. **[Decision 9](#121-decisions-taken) does not cover
them** — it adopted answers to questions 1 to 18 on the strength of established practice, and there
is no established practice for governing a self-improving agent inside a governance tool. Each is an
ADR candidate and none has a recommended answer here.

19. **Which kind of self-improvement is in scope for 0.1.3?**
    [§13.1](#131-three-things-are-called-self-improvement-and-only-one-of-them-is-governable-here)
    argues that policy-artifact improvement is the only governable one. The question is whether
    **harness self-modification is excluded by rule or merely not built yet** — those look identical
    today and diverge completely the first time somebody finds it convenient.
20. **What is the reward, and who may write to it?** Specifically: may the agent write to
    `rag/eval/golden/`? A yes makes every number the pipeline produces unfalsifiable, and it is the
    kind of permission that gets granted for a good reason on a Tuesday.
21. **May the evaluator be the same model as the actor?** Decision 7 makes the actor Claude, and the
    self-preference evidence says a same-model judge is one source counted twice. A different model,
    or a non-LLM oracle, is the alternative — and both cost something.
22. **Does an explored variant need a `witnessed` approval to be promoted, or is a passing gate
    enough?** Note that `require_witness_at_or_above` is `null` by default, so the strongest reward
    signal in [§13.6](#136-the-reward-signal-and-which-of-the-four-can-be-trusted) **is not being
    recorded today** in any project that has not raised it deliberately.
23. **What is the exploration budget, and is it config or policy?**
    [§11.3](#113-two-collisions-and-both-resolve)'s line says policy. If it is ever settable by an
    environment variable, the rate at which the agent experiments on a customer's repository becomes
    a deployment detail.
24. **What re-reads the eighteen warrants, on what trigger, and who sees the result?**
    [§13.2](#132-the-exploration-problem-is-already-in-this-report-under-another-name) says this is
    a cron job and an issue. It is the one question here with a cheap answer, and it is the one that
    decides whether [decision 9](#121-decisions-taken) was defensible.

---

## 14. Sources

Every URL was fetched or searched during the sessions that produced this document, **2026-09-17 and
2026-09-18**. Licence claims in §7 were read from each project's own licence file or model card;
roles and architecture from the documents listed.

**Open SWE, Deep Agents, LangGraph**
- <https://github.com/langchain-ai/open-swe> — README; the `ui/`, `desktop/`, `oeps/` directories; the five work surfaces; *"http://localhost:2024 serves the API and the dashboard"*; plan interrupt with accept/edit/delete
- <https://raw.githubusercontent.com/langchain-ai/open-swe/main/LICENSE> — MIT, LangChain, Inc.
- <https://raw.githubusercontent.com/langchain-ai/open-swe/main/langgraph.json> — the five graphs and their `traced_*` entrypoints
- <https://raw.githubusercontent.com/langchain-ai/open-swe/main/ui/package.json> — the dashboard package, `open-swe-dashboard`
- <https://www.langchain.com/blog/open-swe-an-open-source-framework-for-internal-coding-agents> — architecture, GitHub integration
- <https://docs.langchain.com/oss/python/deepagents/sandboxes> — the eight providers; `execute()` as the only required method; the `OpenShellSandbox` example
- <https://reference.langchain.com/python/deepagents/backends/protocol/SandboxBackendProtocol> — protocol definition
- <https://www.langchain.com/blog/execute-code-with-sandboxes-for-deepagents> — `BaseSandbox` building the filesystem tools on `execute()`

**Human-in-the-loop and the interfaces**
- <https://github.com/langchain-ai/agent-inbox> — MIT; the `HumanInterrupt` / `ActionRequest` / `HumanInterruptConfig` / `HumanResponse` schema; the four response types; *"stored in your browser's local storage"*
- <https://raw.githubusercontent.com/langchain-ai/agent-inbox/main/LICENSE> — MIT, LangChain, Inc.
- <https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt> — `interrupt()` and `Command(resume=...)`
- <https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/LICENSE> — MIT
- <https://docs.langchain.com/oss/python/langgraph/ui> — Agent Chat UI against a local or remote LangGraph server

**Vouch Protocol**
- <https://github.com/vouch-protocol/vouch> — *"The Open Standard for Identity & Provenance of AI Agents"*; *"the SSL certificate for AI agents"*; VC Data Model 2.0, Data Integrity, `eddsa-jcs-2022`, `did:web` and `did:key`, Multikey, the optional `mldsa44-jcs-2024` post-quantum profile; repository created 2025-11-30
- <https://raw.githubusercontent.com/vouch-protocol/vouch/main/LICENSE> — Apache-2.0, *"Copyright 2025 Vouch Protocol Contributors"*. GitHub's own detector reports `NOASSERTION`, because of the preamble above the licence text
- `https://pypi.org/pypi/vouch-protocol/json` — package metadata: version **2.2.1**, `requires-python >=3.9`, **Development Status 4 – Beta**, and the dependency list that contains `jwcrypto`, `pqcrypto`, `cryptography`, `pydantic` and `httpx`
- <https://raw.githubusercontent.com/vouch-protocol/vouch/main/docs/design/shield-v2-and-protected-mcp.md> — Shield v2: the `version: 2` / `deny_default: true` rules schema; exact matching on `action` and `target`, glob on `resource`; unknown keys rejected at load; the stable decision reasons; *"There is no path where a failure produces an allow, and no fallback that is laxer than the configured policy"*; `vouch.mcp.FastMCP`, `unprotected=True`, the JCS resource binding; `VOUCH_RULES`, `VOUCH_TRUSTED_ISSUERS`, `VOUCH_TARGET`; the four stated limitations
- <https://raw.githubusercontent.com/vouch-protocol/vouch/main/CHANGELOG.md> — v1.4.0's *"Vouch Git Workflow"*: `vouch git init`, SSH signing, commit hooks, the `Vouch-DID` trailer, delegation chains, CI enforcement. v2.2.0's removal of capability-level rules. The heartbeat, `authorityEpoch` and intent-recheck entries
- <https://raw.githubusercontent.com/vouch-protocol/vouch/main/docs/vouch_guide.md> — `did:web` resolution through `/.well-known/did.json`; the Identity Sidecar pattern and *"if you give an LLM your private key, it might accidentally leak it in a prompt injection attack"*
- <https://raw.githubusercontent.com/vouch-protocol/vouch/main/docs/THREAT_MODEL.md> — the six threats addressed and the four explicitly out of scope
- <https://raw.githubusercontent.com/vouch-protocol/vouch/main/TRADEMARK.md> — common-law mark; nominative use granted; *"Vouch-as-a-Service"* requires written permission
- <https://raw.githubusercontent.com/vouch-protocol/vouch/main/test-vectors/README.md> — *"canonical, language-independent fixtures that define the cross-implementation contract"*
- <https://raw.githubusercontent.com/latchset/jwcrypto/master/LICENSE> — **LGPL-3.0**, read from the file; the repository's own metadata says `LGPL-3.0-or-later`

**NVIDIA OpenShell**
- <https://github.com/NVIDIA/OpenShell> — *"the safe, private runtime for autonomous AI agents"*; container and MicroVM isolation; policy-enforced egress routing; the four YAML policy domains; `openshell sandbox create`; Linux, macOS Apple Silicon, WSL 2; **alpha**
- <https://raw.githubusercontent.com/NVIDIA/OpenShell/main/LICENSE> — Apache-2.0
- <https://docs.nvidia.com/openshell/latest/get-started> — CLI install and sandbox creation
- <https://docs.nvidia.com/aiq-blueprint/2.2.0-rc1/architecture/agents/sandbox.html> — policy binding and attestation at creation; *"any version disagreement fails closed"*; `sandbox.attestation` and `sandbox.cleanup` events
- <https://github.com/langchain-ai/openshell-deepagent> — a Deep Agents coding agent running inside an OpenShell sandbox
- <https://perspectives.nvidia.com/nvidia-openshell/> — Apache-2.0, self-hosted, no per-sandbox billing

**Aegra**
- <https://github.com/aegra/aegra> and <https://github.com/ibbybuilds/aegra> — both resolve; Apache-2.0, Agent Protocol, Postgres and Redis
- <https://raw.githubusercontent.com/ibbybuilds/aegra/main/LICENSE> — Apache-2.0
- <https://raw.githubusercontent.com/ibbybuilds/aegra/main/aegra.json> — config filename and schema shape; `store.scopes`; the `react_agent_hitl` and `subgraph_hitl_agent` graphs
- <https://raw.githubusercontent.com/ibbybuilds/aegra/main/docker-compose.yml> — `pgvector/pgvector:pg18`, `redis:7-alpine`, uvicorn on 2026
- <https://docs.aegra.dev/> — *"Human-in-the-loop — Approval gates and user intervention points"*; *"Works with Agent Chat UI, LangGraph Studio, and CopilotKit out of the box"*; *"Configurable auth — JWT, OAuth, Firebase, or none"*

**Retrieval — the pipeline**
- <https://arxiv.org/abs/2506.15655> — cAST: Zhang, Zhao, Wang, Yang, Wei, Wu; +4.3 Recall@5 on RepoEval, +2.67 Pass@1 on SWE-bench; the four design goals
- <https://github.com/yilinjz/astchunk> — MIT reference implementation
- <https://raw.githubusercontent.com/tree-sitter/tree-sitter/master/LICENSE> — MIT
- <https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide> and <https://docs.together.ai/docs/how-to-implement-contextual-rag-from-anthropic> — contextual retrieval; the 35% / 49% / 67% failure-reduction figures
- <https://raw.githubusercontent.com/xhluca/bm25s/main/LICENSE> — MIT, Xing Han Lu
- <https://github.com/xhluca/bm25s> and <https://arxiv.org/abs/2407.03618> — eager sparse scoring; NumPy/SciPy only
- <https://arxiv.org/abs/1603.09320> — Malkov & Yashunin, HNSW; the layered proximity graph and logarithmic scaling
- Jégou, Douze & Schmid, *Product Quantization for Nearest Neighbor Search*, IEEE TPAMI 33(1):117–128, 2011 — the IVFADC method, which is what "IVF" names. Bibliographic citation; not fetched this session
- Cormack, Clarke & Buettcher, *Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods*, SIGIR 2009 — the RRF formula. Bibliographic citation; not fetched this session
- <https://github.com/pgvector/pgvector> and <https://raw.githubusercontent.com/pgvector/pgvector/master/LICENSE> — index methods `hnsw` and `ivfflat`; `m`, `ef_construction`, `lists`, `probes`; PostgreSQL License
- <https://github.com/facebookresearch/faiss/wiki/Faiss-indexes> and <https://raw.githubusercontent.com/facebookresearch/faiss/main/LICENSE> — `IndexHNSWFlat`, `IndexIVFFlat`; MIT
- <https://raw.githubusercontent.com/nmslib/hnswlib/master/LICENSE> and <https://raw.githubusercontent.com/unum-cloud/usearch/main/LICENSE> — Apache-2.0
- <https://www.tembo.io/blog/vector-indexes-in-pgvector> — the HNSW/IVFFlat build-time, memory and recall comparison
- <https://huggingface.co/docs/transformers/tokenizer_summary> — byte-level BPE, 256-byte base vocabulary
- <https://huggingface.co/docs/huggingface_hub/guides/cli> — the CLI is now `hf`, not `huggingface-cli`; *"the easiest way to use the `hf` CLI"* is `uvx hf`; downloads cache at `HF_HOME`, default `~/.cache/huggingface/hub/`, overridden with `--cache-dir`

**Retrieval — the models, and their licences**
- <https://huggingface.co/Qwen/Qwen3-Embedding-0.6B> — **`apache-2.0`**; 32K context; user-defined dimensions 32–1024; instruction-aware; *"over 100 languages"* including programming languages
- <https://huggingface.co/Qwen/Qwen3-Reranker-0.6B> — **`apache-2.0`**; 0.6B, 28 layers, 32K context; cross-encoder, instruction-aware
- <https://huggingface.co/BAAI/bge-reranker-v2-m3> — `apache-2.0`; 0.6B on bge-m3. **The card's example passes `max_length=512`; the model declares `max_position_embeddings: 8194` and `model_max_length: 8192`.** An earlier revision of this report cited the first as if it were the second
- <https://huggingface.co/nomic-ai/nomic-embed-code> — `apache-2.0`; 7B; *"Outperforms Voyage Code 3 and OpenAI Embed 3 Large on CodeSearchNet"*
- <https://huggingface.co/jinaai/jina-reranker-v3> — **`cc-by-nc-4.0`, non-commercial**; 0.6B, 131K window, 61.94 nDCG@10 on BEIR
- <https://huggingface.co/naver/splade-v3> — **`cc-by-nc-sa-4.0`, non-commercial**; learned sparse retrieval
- <https://huggingface.co/google/embeddinggemma-300m> — **Gemma terms, not OSI**; *"Prohibited uses of Gemma models are outlined in the Gemma Prohibited Use Policy"*; acceptance required to download
- <https://github.com/CoIR-team/coir> and <https://arxiv.org/abs/2407.02883> — CoIR: 10 curated code datasets, 8 retrieval tasks across 7 domains, two million documents; Apache-2.0; ACL 2025 Main
- Licence files read for the serving runtimes: TEI (Apache-2.0), vLLM (Apache-2.0), Infinity (MIT), llama.cpp (MIT), Ollama (MIT), FlagEmbedding (MIT)

**Langfuse, OpenTelemetry and ClickHouse**
- <https://raw.githubusercontent.com/langfuse/langfuse/main/LICENSE> — MIT Expat with the `ee/` carve-out; **copyright ClickHouse, Inc.**
- <https://langfuse.com/self-hosting> — required infrastructure; *"all incoming tracing and evaluation events are persisted in S3/Blob Storage first"*
- <https://langfuse.com/self-hosting/license-key> — the EE feature list
- <https://langfuse.com/integrations/frameworks/langchain> — callback and OTLP/OpenTelemetry integration
- <https://clickhouse.com/blog/clickhouse-acquires-langfuse-open-source-llm-observability> — acquisition, January 2026
- <https://clickhouse.com/blog/clickhouse-raises-400-million-series-d-acquires-langfuse-launches-postgres> — Series D and acquisition together
- <https://raw.githubusercontent.com/ClickHouse/ClickHouse/master/LICENSE> — Apache-2.0
- <https://clickhouse.com/blog/langfuse-and-clickhouse-a-new-data-stack-for-modern-llm-applications> — why v3 moved off Postgres

**Neo4j and graph alternatives**
- <https://raw.githubusercontent.com/neo4j/neo4j/dev/LICENSE.txt> — GPL-3.0, and the clause that a Commercial Agreement *"will supersede"* it
- <https://raw.githubusercontent.com/neo4j/neo4j/dev/README.asciidoc> — *"Neo4j Community Edition is an open source product licensed under GPLv3"*
- <https://neo4j.com/open-core-and-neo4j/> — Enterprise moved to a commercial licence, no longer published to GitHub
- <https://raw.githubusercontent.com/neo4j/neo4j-python-driver/6.x/LICENSE.txt> — *"Unless stated otherwise, this software is distributed under the terms of the Apache License 2.0"*, with `LICENSE.APACHE2.txt`, `LICENSE.PYTHON.txt` and `NOTICE.txt` beside it; PyPI declares `Apache-2.0 AND Python-2.0`, `requires-python >=3.10`
- <https://raw.githubusercontent.com/neo4j/docs-bolt/dev/LICENSE.txt> — the Bolt **documentation** is *"Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)"*, copyright Neo4j Sweden AB
- <https://neo4j.com/docs/bolt/current/bolt/> — *"Bolt is an application protocol for the execution of database queries via a database query language, such as Cypher"*; *"generally carried over a regular TCP or WebSocket connection"*; built on PackStream
- <https://memgraph.com/docs/client-libraries/java> and <https://memgraph.com/blog/memgraph-1-2-release-implementing-the-bolt-protocol-v4> — Memgraph implements Bolt and documents the Neo4j drivers as the recommended client; since 2.11 no `--bolt-server-name-for-init` override is needed
- <https://neo4j.com/blog/developer/codebase-knowledge-graph/> — codebase as a property graph
- <https://age.apache.org/overview/> — Apache AGE, Apache-2.0, openCypher in PostgreSQL
- <https://kuzudb.github.io/docs/> and <https://github.com/Vela-Engineering/kuzu> — Kùzu MIT; archived October 2025, continued as forks
- <https://github.com/memgraph/memgraph/blob/master/licenses/BSL.txt> — Memgraph BSL
- <https://github.com/arangodb/arangodb/blob/devel/LICENSE> — ArangoDB BUSL-1.1

**Valkey, PostgreSQL, SeaweedFS**
- <https://raw.githubusercontent.com/valkey-io/valkey/unstable/COPYING> — BSD-3-Clause, Valkey contributors and Redis Ltd.
- Linux Foundation fork of Redis 7.2.4 following the March 2024 SSPL/RSALv2 change; wire-compatible
- <https://github.com/seaweedfs/seaweedfs> — Apache-2.0; S3, IAM and STS APIs on one endpoint; master/volume/filer architecture
- <https://www.min.io/blog/from-open-source-to-free-and-open-source-minio-is-now-fully-licensed-under-gnu-agplv3> — MinIO's move to AGPL-3.0, completed May 2021

**Removed from the stack, retained here because the reasoning should survive the decision**
- <https://raw.githubusercontent.com/makeplane/plane/master/LICENSE.txt> — Plane Community, AGPL-3.0
- <https://mintlify.wiki/makeplane/plane/self-hosting/docker> — Plane's compose services: web, admin, api, worker, beat-worker, live, Postgres, Valkey, RabbitMQ, MinIO, Caddy — the footprint §5 removes
- <https://raw.githubusercontent.com/docker/sbx-releases/main/LICENSE> — the whole file: *"Copyright © 2026 Docker Inc. All rights reserved."*
- <https://github.com/docker/sbx-releases> — binaries only, no source published
- <https://www.docker.com/products/docker-sandboxes/> — *"For centralized controls across a team… Docker AI Governance"*
- <https://www.docker.com/blog/why-microvms-the-architecture-behind-docker-sandboxes/> — the custom VMM and per-sandbox kernel, which remains the strongest isolation on offer and is the thing §8.2 gives up

**The twelve factors, and the fifteen**
- <https://12factor.net/> — the twelve factors and their one-line statements; the scope, *"apps written in any programming language, and which use any combination of backing services"*; synthesised from *"the development and deployment of hundreds of apps"*; Adam Wiggins, last revised 2017
- <https://12factor.net/config> — *"everything that is likely to vary between deploys"*; the open-source litmus test; why config files are rejected; env vars as *"granular controls"*
- <https://12factor.net/backing-services> — *"any service the app consumes over the network"*; *"no distinction between local and third party services"*; the swap-without-code-changes test
- <https://12factor.net/build-release-run> — the three stages; *"a transform which converts a code repo into an executable bundle"*; unique release ids; *"an append-only ledger"*
- <https://12factor.net/processes> — *"stateless and share-nothing"*; *"never assumes that anything cached in memory or on disk will be available on a future request or job"*; *"a brief, single-transaction cache"*
- <https://12factor.net/disposability> — *"started or stopped at a moment's notice"*; *"a few seconds"*; graceful shutdown as *"returning the current job to the work queue"*
- <https://12factor.net/dev-prod-parity> — the time, personnel and tools gaps; *"resists the urge to use different backing services between development and production"*
- <https://12factor.net/logs> — *"the stream of aggregated, time-ordered events"*; *"never concerns itself with routing or storage of its output stream. It should not attempt to write to or manage logfiles"*
- <https://12factor.net/admin-processes> — *"run in an identical environment as the regular long-running processes"*; *"admin code must ship with application code"*
- <https://github.com/heroku/12factor> — the site's source, and where the licence was read: **MIT**
- Kevin Hoffman, *Beyond the Twelve-Factor App*, O'Reilly for Pivotal, 2016 — <https://www.oreilly.com/library/view/beyond-the-twelve-factor/9781492042631/>. **The publisher's page returned HTTP 403 to an unauthenticated fetch this session**, so this is a bibliographic citation and the factor list below is what was actually read
- <https://www.cloudfoundry.org/blog/how-many-factors-are-there-anyway/> — the fifteen named and ordered, and the statement that **Telemetry, Authentication and authorization, and API First** are the three additions
- <https://domenicoluciani.com/2021/10/30/15-factor-app.html> — a secondary summary, used only for the *intent* of the three added factors and marked as secondary because it is
- <https://github.com/humanlayer/12-factor-agents> — *12-Factor Agents*: a different document with a colliding name, content **CC BY-SA 4.0** and code Apache-2.0. Cited in [§11](#11-the-stack-as-a-fifteen-factor-application) so it is not mistaken for what decision 8 adopts

**Industry practice consulted for [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on)**

*Primary sources — specifications, standards bodies and vendor product documentation:*
- <https://slsa.dev/spec/v1.2/source-requirements> — the Source Track: L1 *"Version controlled"*, L2 *"History & Provenance"*, L3 *"Continuous technical controls"*, **L4 *"Two-party review"***; *"The SCS requires two trusted persons to review all changes to protected branches"*; *"The SCS MUST generate a source verification summary attestation (Source VSA)"*; approvals apply to *"the final revision submitted"*
- <https://owasp.github.io/www-project-non-human-identities-top-10/> — the ten risks, NHI1 to NHI10; **NHI7:2025 *Long-Lived Secrets***
- <https://owasp.github.io/www-project-non-human-identities-top-10/2025/10-human-use-of-nhi/> — **NHI10:2025 *Human Use of NHI***; the named risks *"lack of detailed auditing and accountability"* and *"indistinguishable activity between humans and automation"*; the mitigation *"use dedicated human identities with appropriate roles and permissions for debugging or maintenance tasks"*
- <https://cwe.mitre.org/data/definitions/1188.html> — **CWE-1188**, *"Initialization of a Resource with an Insecure Default"*; a Base-level weakness; parents CWE-344 and CWE-1419, child CWE-453
- <https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/> — *"A SPIFFE ID is a string that uniquely and specifically identifies a workload"*; **_"The trust domain corresponds to the trust root of a system"_**; SVIDs as X.509 or JWT. The documentation covers workload identity only and does not address human identity
- <https://docs.sigstore.dev/cosign/signing/overview/> — keyless signing: an ephemeral keypair where *"the private key is destroyed shortly after"*; Fulcio *"issues short-lived certificates binding an ephemeral key to an OpenID Connect identity"*; Rekor *"witnesses"* the event; verifiers *"use the transparency log entry, rather than relying on the signer to safely store and manage the private key"*
- <https://cyclonedx.org/capabilities/mlbom/> — **CycloneDX ML-BOM**, ratified as **ECMA-424**; the `machine-learning-model` component type, the `data` type, and the embedded model-card structure
- <https://docs.aws.amazon.com/neptune/latest/userguide/access-graph-opencypher-bolt.html> — **Amazon Neptune over Bolt**: *"simply replace the URL and Port number with your cluster endpoints using the `bolt` URI scheme"*; *"Neptune only supports TCP connections for Bolt"*; *"you can't use an Application Load Balancer in front of them"*; SigV4 signatures expiring in about five minutes and the driver issues that followed; the 20-minute idle timeout; *"the `auth` parameters are ignored"* without IAM auth. **Also the source of the CC BY-SA 3.0 claim** discussed in [§3.10](#310-dbneo4j--the-graph-store)
- <https://boltprotocol.org/> — **301-redirects to `neo4j.com/docs/bolt`**, verified this session. The independent specification site no longer resolves to its own content
- <https://scorecard.dev/> — OpenSSF Scorecard: automated checks over a repository's security practices, scored 0–10 per check
- <https://opentelemetry.io/docs/specs/otel/logs/> — the OpenTelemetry logging specification; logs as a first-class signal with their own data model, distinct from traces

*Secondary sources — blog posts, vendor engineering write-ups and summaries. Read for practice rather than for normative text, and marked as secondary because that is what they are:*
- <https://cursor.com/blog/secure-codebase-indexing> — Merkle-tree incremental indexing: *"a cryptographic hash of every file, along with hashes of each folder that are based on the hashes of its children"*; *"small client-side edits change only the hashes of the edited file itself and the hashes of the parent directories up to the root"*; embeddings cached by chunk content
- <https://www.cncf.io/blog/2025/03/18/open-policy-agent-best-practices-for-a-secure-deployment/> and <https://devops.com/declarative-compliance-with-policy-as-code-and-gitops/> — policy-as-code in version control, *"version-controlled, auditable, and consistently deployed"*
- <https://finqub.io/learn/tamper-evident-audit-trail/> and <https://aisyndicate.io/blog/compliance/append-only-audit-logs-ai-compliance> — hash-chained tamper-evident ledgers; *"an append-only log only answers half"* of what an examiner asks; the complementary-use position with git
- <https://apievangelist.com/2026/06/30/git-is-your-governance-source-of-truth/> — git as the governance source of truth, and the condition that history rewriting must be disabled for it to hold
- <https://munderdiffl.in/blog/human-in-the-loop-approving-ai-agents/> — approve where the work happens rather than in a separate queue; approval reserved for irreversible actions
- <https://en.wikipedia.org/wiki/Hexagonal_architecture_(software)> and <https://www.happycoders.eu/software-craftsmanship/hexagonal-architecture/> — ports and adapters as the mitigation for an immature or swappable dependency
- <https://github.com/unum-cloud/usearch/blob/main/BENCHMARKS.md> — USearch's comparative figures against FAISS, **published by USearch**, which is why [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on) does not rest question 6 on them
- <https://github.com/facebookresearch/faiss/releases> — FAISS release notes; recent work is dominated by GPU and cuVS. **The dates returned this session were inconsistent and are not quoted**
- <https://www.dash0.com/knowledge/opentelemetry-logging-explained> — the Collector stdout/file route, and *"you lose automatic trace correlation from the SDK, but you can inject trace_id yourself"*
- <https://www.baytechconsulting.com/blog/keep-code-off-cloud-self-hosted-ai-dev-agents> — Privacy Mode and Zero Data Retention as the enterprise vocabulary; self-hosting as the only arrangement that *"physically cannot send it anywhere else"*
- <https://www.git-tower.com/learn/git/faq/add-empty-folder-to-version-control> and <https://www.deployhq.com/blog/understanding-keep-and-gitkeep-files-a-guide> — `.gitkeep` has no meaning to git; *"only add placeholder files for directories that are essential to the project structure"*
- <https://www.systemshardening.com/articles/kubernetes/runtimeclass-gvisor-kata/> — `RuntimeClass` with gVisor and Kata: the runtime is installed on the node, selected by class, with nodes labelled and tainted; *"`runtimeClassName` does nothing unless the cluster has nodes with that runtime installed"*

**The GitHub conventions — [decision 10](#121-decisions-taken)**
- <https://cbea.ms/git-commit/> — cbeams, 31 August 2014. The seven rules, verbatim; *"A diff will tell you what changed, but only the commit message can properly tell you why"*; the imperative test *"If applied, this commit will _your subject line here_"*; and *"50 characters is not a hard limit, just a rule of thumb… consider 72 the hard limit"*. **No licence notice on the page**
- <https://www.conventionalcommits.org/en/v1.0.0/> — the `<type>[optional scope]: <description>` structure; the sixteen numbered specification points; footers as `token: value` with hyphens for spaces; `!` and the `BREAKING CHANGE` footer, which alone must be uppercase; `fix` → PATCH, `feat` → MINOR, breaking → MAJOR. Published **CC BY 3.0**
- <https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates> — `.md` and issue-form `.yml` files in `.github/ISSUE_TEMPLATE/` with `config.yml` for the chooser; pull request templates as `.md` or `.txt` in the repository root, `docs/` or `.github/`; and the constraint that both live on the default branch — *"Templates created in other branches are not available for collaborators to use"*

**Exploration and self-improving agents — [§13](#13-meta-cognition-exploration-and-the-parts-that-must-not-be-explored)**

*Primary — papers and project pages, read for what they define:*
- <https://arxiv.org/abs/2603.02045> — **SGE**, *Expanding LLM Agent Boundaries with Strategy-Guided Exploration*; Szot, Kirchhof, Attia, Toshev; 2 March 2026. Abstract read in full: *"explor[e] in the space of strategies rather than the space of actions"*; mixed-temperature sampling; the strategy reflection process; UI, tool-calling, coding and embodied environments
- <https://arxiv.org/abs/2605.21240> — **APEX**, *Autonomous Policy EXploration for Self-Evolving LLM Agents*; Li, Yang, Zheng, Hu, Sui, Wang, He, Hooi; 20 May 2026. *"Exploration collapse"* verbatim; the strategy map as *"a directed acyclic graph of milestones with prerequisite dependency edges"*; Fork Discovery and Policy Selection; nine Jericho games and WebArena
- <https://arxiv.org/abs/2505.15293> — **LLM-Explorer**, *A Plug-in Reinforcement Learning Policy Exploration Enhancement Driven by Large Language Models*; Tsinghua; NeurIPS 2025. The criticism of preset stochastic processes *"applied uniformly across different tasks"*; the agent's *"real-time learning status"*
- <https://yxw.cs.illinois.edu/files/SAGE_NeurIPS2025.pdf> — **SAGE**, *Self-Guided Hierarchical Exploration for Generalist Foundation Model Web Agents*; Yang, Wang, Perszyk, Wang; NeurIPS 2025. The acronym expansion read from the title page; the three-tier strategy and the *"self-evolving curriculum of tasks from easy to hard"*
- <https://sakana.ai/dgm/> and <https://arxiv.org/abs/2505.22954> — the **Darwin Gödel Machine**. The archive and *"parallel exploration of many different evolutionary paths"*; SWE-bench 20.0% → 50.0% and Polyglot 14.2% → 30.7%; the stepping-stone finding about *"less-performant 'ancestor' agents"*; and the reward-hacking section quoted in [§13.6](#136-the-reward-signal-and-which-of-the-four-can-be-trusted) — the faked test log, and the removal of *"the markers we use in the reward function to detect hallucination"*
- <https://arxiv.org/abs/2408.08435> — **ADAS**, *Automated Design of Agentic Systems*; Hu, Lu, Clune; ICLR 2025. Meta Agent Search; the search space / search algorithm / **evaluation function** decomposition
- <https://arxiv.org/abs/2506.13131> and <https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/> — **AlphaEvolve**; automated evaluators that verify; solutions *"interpretable, verifiable through execution"*
- <https://arxiv.org/pdf/2506.10943> — **SEAL**, *Self-Adapting Language Models*; MIT. Self-edits as generated training data plus update settings; catastrophic forgetting named as the open limitation
- <https://arxiv.org/abs/2507.19457> — **GEPA**, *Reflective Prompt Evolution Can Outperform Reinforcement Learning*; Agrawal et al.; the title page records acceptance at ICLR 2026 as an oral. Reflection on execution traces rather than a scalar reward; *"the Pareto frontier of its own attempts"*; the reported margin over GRPO and **up to 35× fewer rollouts**
- <https://arxiv.org/abs/2305.16291> — **Voyager**; the automatic curriculum, the skill library of executable code indexed by description, and the iterative prompting loop with self-verification
- <https://arxiv.org/abs/2303.11366> — **Reflexion**; NeurIPS 2023. Reinforcement *"not by updating weights, but instead through linguistic feedback"*, held in an episodic memory buffer
- <https://www.nature.com/articles/s41586-020-03157-9> — **Go-Explore**, *First return, then explore*; Ecoffet, Huizinga, Lehman, Stanley, Clune; *Nature* **590**, 580–586 (2021). **Detachment** and **derailment** defined; the archive as the fix for the first
- <https://www.semanticscholar.org/paper/45373921f06a6efebefa6189d2dd80362ab0836e> — **MAP-Elites**, *Illuminating search spaces by mapping elites*; Mouret and Clune, 2015. Behaviour characteristics, the tessellated behaviour space, one elite per cell, and illumination as the stated purpose
- <https://arxiv.org/abs/1301.2609> — Russo and Van Roy, *Learning to Optimize Via Posterior Sampling*. Thompson sampling: the agent *"maintains a posterior distribution over its beliefs regarding the optimal action"* and randomises in proportion to it
- <https://arxiv.org/abs/1803.00933> — **Ape-X**, *Distributed Prioritized Experience Replay*; Horgan et al., DeepMind, 2018; ICLR 2018. Many actors with **different exploration rates**, one prioritised replay buffer, one learner. Cited here for the name collision and for the per-actor idea, not for the architecture
- <https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/> — Krakovna et al., 23 April 2020. **Specification gaming** as *"a behaviour that satisfies the literal specification of an objective without achieving the intended outcome"*; the Lego-block example; and that these behaviours *"are caused by misspecification of the intended task, rather than any flaw in the RL algorithm"*
- <https://proceedings.neurips.cc/paper_files/paper/2024/file/7f1f0218e45f5414c79c0679633e47bc-Paper-Conference.pdf> and <https://arxiv.org/abs/2410.21819> — LLM judges recognising and favouring their own generations, and the perplexity mechanism behind self-preference: judges rate familiar, low-perplexity text more highly than humans do, with family-level bias as well as self-preference
- <https://www.iso.org/standard/42001> — **ISO/IEC 42001:2023**, the AI management system standard: *"establishing, implementing, maintaining and continually improving an AI management system"*; Plan-Do-Check-Act; internal audit and corrective action as named requirements. Cited as the shape a governance layer's improvement loop is expected to have. **The catalogue page returns HTTP 403 to an unauthenticated fetch and the standard itself is paywalled**, so this is a bibliographic citation and a reading of ISO's own public summary, not of the normative text — the same treatment [§11](#11-the-stack-as-a-fifteen-factor-application) gives *Beyond the Twelve-Factor App*
- <https://www.nist.gov/itl/ai-risk-management-framework> — **NIST AI RMF 1.0** and the Generative AI Profile (**AI 600-1**, July 2024). MEASURE as the TEVV function; measurement before deployment *and throughout the lifecycle*; continuous monitoring under MANAGE
- <https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/> — OWASP Agentic Security Initiative, *Agentic AI: Threats and Mitigations* v1.0, 17 February 2025. **The landing page was read; the threat taxonomy itself is in a PDF this session did not open**, so no threat id is quoted from it here
- <https://aivss.owasp.org/> — the **OWASP AI Vulnerability Scoring System**, v0.8. Version verified on the site; the site footer states CC BY-SA 4.0 for site content. **The list of Agentic Risk Amplification Factors, including self-modification, was read from secondary summaries rather than from the scoring document**, and [§13.7](#137-one-rule-and-the-five-places-it-lands) says so where it uses it

*Secondary — search summaries and commentary, read for orientation and not quoted as normative:*
- <https://www.lakera.ai/blog/why-we-need-owasps-aivss-extending-cvss-for-the-agentic-ai-era> — vendor commentary on AIVSS extending CVSS for agentic systems. This and other secondary coverage are where the amplification-factor names in [§13.7](#137-one-rule-and-the-five-places-it-lands) come from
- Commentary on metacognition in LLM agents, including the meta-d′ signal-detection metric for metacognitive sensitivity. **Used for the name of the measurement only**; [§13.8](#138-meta-cognition-is-already-mandated-here-and-it-is-not-measured) rests its argument on this repository's own artifacts, not on this literature

**Within this repository**
- [`docs/dev/licensing.md`](../dev/licensing.md) — BUSL-1.1, the Additional Use Grant, the Elastic-2.0 exclusion
- [`AGENTS.md`](../../AGENTS.md) — "Resolve, or stop — never infer"; "Re-read before asserting"
- [`docs/guide/using-specup.md`](../guide/using-specup.md) — exit-code contract, and `2` kept separate from `1` because a setup fault is *"an operator error, not a governance failure"*; `DOC-005` is not listable and cannot be lowered; *"`DOC-005` counts names, not independence"*; bundles cannot enforce
- [`extensions/openup/openup-config.yml`](../../extensions/openup/openup-config.yml) — the approval ratchet, `require_witness_at_or_above: null` by default, and *"Raise it as a decision; never lower it to make a run go green"*
- [`extensions/openup/scripts/python/validate_docs.py`](../../extensions/openup/scripts/python/validate_docs.py) — `DOC-005` and the `cits-crypto` failure it generalises: a truth table and the predicate written to cross-check it derived from the same misreading, so *"they agreed, and both were wrong"*
- [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) — why nothing governance-bearing is enforced there: *"a pre-commit hook lives at a project root, where editing it is an unremarkable act"*, while `extensions/openup/` is owned by `specify extension add` and tampering is visible
- [`.specify/traceability/index.md`](../../.specify/traceability/index.md) — the 84%-asserted figure §3.6.8 compares itself to
- `.claude/plans/floofy-pondering-crescent.md` §7 — the 0.1.3 research this report extends and corrects

---

## What checks any of this

**Nothing.**

No validator reads this page. `validate_docs.py` checks Python docstrings through `ast` and
reports non-Python files as `SKIP`; a Markdown research report is outside the seventeen-module
perimeter entirely. No check resolves a URL, compares a licence claim against a licence file, or
notices when an upstream project relicenses.

So every fact here is `asserted`, in exactly the sense SpecUP's provenance vocabulary uses the
word: one person read a source and wrote down what it said. The citations in §14 exist so that a
second person can repeat the reading, which is the only verification available.

**And the ten decisions in [§12.1](#121-decisions-taken) are in a weaker position than the
facts.** A fact here can at least be re-checked against a cited source. A decision recorded in a
research report has no id, no status, no consequence section, and nothing that fails when the code
contradicts it. **Decision 1 is the clearest case**: "SpecUP does not redistribute this stack" is
a rule about every future release, written in a document no release process reads. The day somebody
builds a convenient appliance, nothing will object. Each of the ten should become an ADR, and
until it does, this section is the honest description of what they are.

**Decisions 8 and 10 are the partial exceptions, and they are exceptions for the same reason.** Both
adopt standards stated outside this document by somebody else, so the obligation does not depend on
this page surviving. Three of the fifteen factors are checkable by a program rather than by a reader
— no credential in a tracked file, no index artifact without a release id, no indexing job living
outside the package it indexes for
([§11.7](#117-what-adopting-this-costs-and-the-three-things-it-makes-checkable)) — and decision 10's
commit format is checkable by a `commit-msg` hook. **Two of those four are now written**, in
`.pre-commit-config.yaml`: the commit format, and factor III's litmus test as `detect-private-key`.
The other two wait on artifacts that do not exist yet — there is no index to reject and no indexing
job to misplace — so not writing them is a schedule rather than a choice, which is the first time
that has been true of anything in this section.

**And decision 9 is the opposite case — the one that most needs a verifier and can least have one.**
It adopts eighteen answers on the strength of outside practice and promises to revisit each as its
component matures. Nothing watches an upstream project's release badge. Nothing will notice when
OpenShell leaves alpha, when the GenAI agent spans stabilise, or when a Scorecard number moves. **The
revisit is the entire justification for adopting on borrowed evidence, and it is a sentence in a
research report** — which is exactly the shape of claim this section exists to be honest about.
[§13.2](#132-the-exploration-problem-is-already-in-this-report-under-another-name) now describes the
job that would fix it — re-read the eighteen warrants, open an issue when one has moved — and
**describing a cron job is not running one.**

**And [§13](#13-meta-cognition-exploration-and-the-parts-that-must-not-be-explored) is the weakest
section in the document, by a margin, and it says so in its own closing.** It designs a control loop
for a stack that does not exist, over a reward that has not been collected, for an agent whose
refusal rate has never been counted. **Its one rule is the part to keep** — *an agent may optimise
what it does, and never what decides whether what it did was good* — and the five places that rule
lands ([§13.7](#137-one-rule-and-the-five-places-it-lands)) are five directories in this repository
that **nothing currently protects from a process running as the developer**. The Darwin Gödel
Machine removed the markers in its own reward function and was caught only because the archive kept
a traceable lineage of every change; SpecUP's equivalent of that lineage is git, and git is exactly
one of the things §13.7 says the agent may write to.

**Four things will go stale, and they are the four that matter most:**

- **Licences change with ownership.** Langfuse is already under new ownership. Redis, ArangoDB,
  MinIO, Elastic, HashiCorp and Neo4j Enterprise all relicensed, and SpecUP relicensed at 0.1.2.
- **Model licences change faster than code licences, and matter more here than they used to.**
  [§7.2](#72-model-weights-carry-licences-too-and-the-good-ones-often-forbid-you) is a snapshot of
  five model cards on one day. Weights get re-released under new terms routinely, in both
  directions.
- **`open-swe/` was untracked until this commit, and that failure mode is now closed.** It could
  change with no commit, no diff and no review — which is what happened to the §7 note this
  document corrects in [§2](#2-correcting-the-record), and it produced no diff because there was
  nothing to diff. The `.gitkeep` files fix that: the layout is now reviewable, and a change to
  it shows up in a pull request like anything else. **And the premise is now checked rather than
  merely published:** a pre-commit hook runs `find open-swe -type f -size +0c` and fails the commit
  if anything under `open-swe/` acquires bytes, so [§1](#1-what-open-swe-is-today)'s central claim
  can no longer quietly stop being true. **What is still unchecked is the inventory itself** —
  nothing fails if §1's list of 56 paths stops matching `find open-swe -mindepth 1 | sort`. Half of
  the check somebody could write now exists, and it is the half that was load-bearing.
- **Every role in §3 marked *Inferred* is a guess**; *Specified* means this report chose a shape;
  *Decided* means the project owner ruled and no ADR has been written yet. All three are weaker
  than they look, and in different ways. Do not let any of them erode into "the layout says so".

**And three things are newly fragile.** Aegra is unproven, OpenShell is badged alpha at the exact
point where SpecUP's containment claim would be made, and Vouch is beta, seven months old at the
time of writing, and removed a whole class of its own rules one minor version back. The report
recommends all three, and it recommends them *because* the alternatives were a licensed runtime, a
closed one, and a broker SpecUP would have had to write. **Each trade is defensible alone. Whether
they are defensible together is [§12.2](#122-the-eighteen-questions) question 5**, and it is the question
this report is least able to answer about itself.

**One source contradicted itself, and the resolution is recorded rather than smoothed over.**
Vouch's README describes v1.6 as current while its PyPI package ships 2.2.1 and its changelog
documents everything in between. Every Vouch version number and API name in this report came from
the changelog and the package metadata, not from the README — which is the *"re-read before
asserting"* rule doing the only thing it can do, and a reminder that a project's most-read file is
not automatically its most current one.

**The retrieval pipeline's numbers are all borrowed.** 35%, 49%, 67%, +4.3 Recall@5, 61.94
nDCG@10 — every one is somebody else's measurement on somebody else's corpus. `rag/eval/` exists
so that this stack can produce its own, and until it does, §3.6 is a well-cited hypothesis.

**And so are the recommendations.** [§12.3](#123-the-adopted-answers-and-the-outside-practice-they-rest-on)
is eighteen readings of what other people do, six of them from secondary sources. It is the weakest
material in this document by construction: a research report quoting industry practice is two removes
from evidence, and *"this is how it is normally done"* has never been an argument that it is right
here. The section says so itself, and it is worth repeating where the rest of the caveats live.

Re-read before relying on any of it.
