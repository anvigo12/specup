# The SpecUP agent stack — what `open-swe/` names, and how it would run

**Audience:** anyone deciding whether the 0.1.3 runtime is the right shape, and anyone who has
to build it.

**Status: research. Nothing here is decided.** This document reports what each component in
`open-swe/` is, how the eleven of them compose into a production stack, and what adopting them
would cost. It registers no requirement, commits no dependency and settles no argument. The
decisions it uncovers are listed in [§11](#11-open-questions) and belong in ADRs.

> Read [`docs/dev/licensing.md`](../dev/licensing.md) first if you are here for the licence
> question. This page extends it to the runtime; that page is the authority on SpecUP's own
> terms.

**Two conclusions are worth putting at the top, because the rest of the report is the working.**

1. **Exactly one component carries a licence obligation: Neo4j, at GPL-3.0.** The tracker was
   dropped for interfaces that already exist ([§5](#5-the-interface-layer--what-replaces-plane))
   and the sandbox moved to NVIDIA OpenShell
   ([§3.4](#34-sandboxopenshell--nvidia-openshell)). [§8.1](#81-the-graph) has an Apache-2.0
   answer for the last one. The stack is one decision away from permissive end to end.
2. **Model weights are where the licence risk moved.** Three of the models a 2026 "best RAG
   models" list would recommend are **non-commercial or restricted** — `jina-reranker-v3` is
   CC BY-NC 4.0, `splade-v3` is CC BY-NC-SA 4.0, and EmbeddingGemma ships under Google's Gemma
   terms with a prohibited-use policy. [§7.2](#72-model-weights-carry-licences-too-and-the-good-ones-often-forbid-you)
   is the section that catches this, and it is the one most likely to be skipped.

---

## 1. What `open-swe/` is today

It is **54 paths containing zero bytes** — 31 directories, 4 placeholder files and 19 `.gitkeep`
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
└── sandbox/
    └── openshell/                   (empty)
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
Every claim below therefore carries one of three markers, and they are not interchangeable:

| Marker | Means |
|---|---|
| **Verified** | Read this session from the named upstream source, cited in [§12](#12-sources) |
| **Inferred** | Read off the folder layout or off how these projects are normally combined. **A guess, marked as one** |
| **Specified** | **Created deliberately, with the intent recorded here at the moment of creation.** Neither a reading nor a guess — a decision, written down |

The third marker is new and it matters. `agent-inbox/` and the whole of `rag/` below `bbpe/`
were created as part of this revision rather than found, so their intent is not being recovered —
it is being stated. **They are the first part of `open-swe/` that has recorded intent**, which is
exactly what the 0.1.2 plan's §7 *Loose end* asked for. Everything still marked *Inferred* is a
directory whose purpose remains a guess, and nobody should read an inference here as a decision
that has been taken.

**Eleven components, counted by role rather than by directory.** `db/` is a container for five
of them and `sandbox/` for one. **`rag/` is now counted as one component rather than two**, because
it stopped being "a BM25 index and a vector index" and became a seven-stage pipeline
([§3.6](#36-rag--the-retrieval-pipeline)); `agent-inbox/` is new. The total is unchanged at
eleven for those two reasons together, which is a coincidence and is recorded so the figure does
not look stale.

---

## 2. Correcting the record

The only existing mention of this folder is the 0.1.2 plan's §7 *Loose end*, and it describes a
folder that no longer exists:

| §7 says | Actually |
|---|---|
| `openswe/` | `open-swe/` |
| "six empty dirs plus two zero-byte files" | eleven components, 54 paths, all of them zero bytes |
| "untracked scaffolding… never committed" | **tracked from this commit**, structure preserved by `.gitkeep` |
| `bbpe/bbpe-codec.toon` | `rag/bbpe/tokenizer.json` — different name, different format, moved under `rag/` |
| names `langfuse`, `db/neo4j`, `db/clickhouse`, `bbpe` | adds `agent-inbox/`, `db/postgres`, `db/seaweedfs`, `db/valkey`, `langgraph/aegra/`, `sandbox/openshell/`, and the seven `rag/` stages |

The drift is recorded rather than quietly overwritten, because §7 is the document a reader would
otherwise trust. Its instruction stands and this report is the first half of it: *"Either record
their intent or remove them before 0.1.3."*

---

## 3. The eleven components

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

**Every entrypoint is a `traced_*` wrapper.** That is not decoration — it is the seam
observability attaches to, and it is why [§3.5](#35-langfuse--llm-observability) is a component
of this stack rather than an optional extra.

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
`path/to/module.py:variable` reference — so the five Open SWE graphs in §3.1 transfer across
with no change in content, only in filename. Aegra's own file also carries a `store.scopes`
block, which LangGraph's does not, and which is how it separates one tenant's stored state from
another's.

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
bound to a signed commit. Nothing does that today, and
[§11](#11-open-questions) question 3 is where it belongs.

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
| Semantic actions | `commit_and_open_pr`, `request_pr_review`, `task` | **a middleware broker** — `awrap_tool_call`, which the agent's own code path must honour |

The first two rows are enforcement. The third is interception, which is weaker, and the
difference should be stated in exactly those terms wherever SpecUP claims the agent is contained.
Network policy answers *which host*, not *which operation*: allowing egress to `github.com` does
not distinguish opening a pull request from force-pushing over a branch. The broker gets smaller
under OpenShell; it does not disappear.

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
| 2. Contextualise | `chunk/contextual/` | an LLM pass that prefixes each chunk with where it sits |
| 3. Tokenise | `bbpe/` | one byte-level BPE tokenizer, shared by every stage |
| 4. Embed | `embed/qwen3-embedding/` | the dense vectors, and the model that makes them |
| 5. Index | `index/bm25s/`, `index/ann/{hnsw,ivf}/` | lexical and dense indexes |
| 6. Fuse | `fuse/` | reciprocal rank fusion over the two result lists |
| 7. Rerank | `rerank/qwen3-reranker/` | a cross-encoder over the fused top-k |
| — | `eval/coir/`, `eval/golden/` | the harness that says whether any of it helped |

Structural retrieval is the fourth arm and it is not here, because it is a service rather than an
artifact: it lives in [§3.10](#310-dbneo4j--the-graph-store).

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

**Specified, and the reason it is a directory rather than a flag:** whether to contextualise is
the sharpest cost-versus-quality decision in the retrieval layer. Burying it in a config key is
how it gets switched off for a deadline and never switched back.

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

**Serving it needs no directory of its own.** Text Embeddings Inference (**Apache-2.0**),
Infinity (**MIT**), llama.cpp (**MIT**) and Ollama (**MIT**) all serve embedding and reranking
models, and one process can serve both this stage and §3.6.7. The serving config belongs inside
these model directories; inventing a `serve/` directory would imply a component that is one
container running two models.

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

A code index is written constantly, which argues for HNSW; a frozen dependency corpus argues for
IVF. **Having both directories is a position, not indecision** — but which is built, and when, is
not readable from the layout.

**Inferred, and the strongest inference in this section:** `hnsw` and `ivf` are the two index
types of **pgvector**, exactly and only — its index methods are `hnsw` and `ivfflat`, and
[§3.2](#32-langgraph--aegra-and-the-agent-protocol-server) records that Aegra's own compose pins
`pgvector/pgvector:pg18`. If that reading is right, `index/ann/` is not a service. It is index
definitions and build parameters — `m` and `ef_construction` for HNSW, `lists` and `probes` for
IVFFlat — against the PostgreSQL the stack already runs, and it adds no container.

The competing reading is **FAISS**, whose index classes are `IndexHNSWFlat` and `IndexIVFFlat`;
`hnswlib` and `usearch` are the same shape, narrower in scope. **The two readings differ in
exactly one place that matters:** whether vectors live in the database that already has backups,
migrations and transactions, or in files beside the process that built them.

**No licence exposure either way.** pgvector is under the PostgreSQL License; FAISS is MIT;
`hnswlib` and `usearch` are Apache-2.0. All four were read from their own `LICENSE` files.

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

**The permissive alternative is `bge-reranker-v2-m3`** — **Apache-2.0**, 0.6B, built on bge-m3,
multilingual, and the usual lightweight default. Its documented usage truncates at **512 tokens**,
against Qwen3-Reranker's 32K, and for code that difference is not academic: 512 tokens is a
medium-sized function.

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

**Verified.** Neo4j Community Edition is **GPL-3.0** — and it is now the **only** component in
this stack that carries a copyleft obligation, which makes [§8.1](#81-the-graph) the single
remaining licence decision. Its `LICENSE.txt` also carries an explicit dual-licensing clause: if
you hold a *"Commercial Agreement"* with Neo4j, *"the terms of the license in such Commercial
Agreement will supersede the GNU GENERAL PUBLIC LICENSE Version 3."* So paying is a documented
route out. Enterprise Edition is commercial-only and is no longer published to GitHub. The
official drivers, including Python, are **Apache-2.0**, and the Bolt protocol is the boundary
between them.

Modelling a codebase as a property graph and letting an agent query it with Cypher — instead of
re-reading source files — is an established pattern, with tooling built specifically to be
always-on context for coding agents.

**Inferred, and this is the weakest inference in the report:** `db/neo4j` holds a code property
graph — symbols, files, imports, call edges — that the agent queries for structural retrieval,
as the fourth arm of [§3.6](#36-rag--the-retrieval-pipeline). Nothing in the layout says this. It
could equally be agent memory, a requirements ontology, or a dependency graph.

**The new `rag/` structure makes this inference testable rather than permanent.** `eval/golden/`
is where the question "does structural retrieval find files the other three arms miss?" gets an
answer. Until then, this is the component most in need of a written intent — and the only one
whose licence depends on that intent being worth it.

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

**It now has a second plausible consumer.** `rag/index/` artifacts — a built BM25 index, a
serialised FAISS index, a contextualised corpus — are large binary blobs that are expensive to
rebuild and unwanted in git. Under the FAISS reading of §3.6.5 this is where they belong. Under
the pgvector reading they do not exist. **That is the same fork as §3.6.5, showing up in a
different directory**, which is a reason to decide it once rather than twice.

---

## 4. How they compose

The lifecycle below is **inferred** — it is how these eleven components fit together given what
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
             │              │ rag/  retrieval      │  │ OpenShell sandbox    │
             │              │ chunk→embed→index    │  │ YAML policy, hashed  │
             │              │ →fuse→rerank         │  │ execute() chokepoint │
             │              │ + Neo4j (structural) │  │ + egress gateway     │
             │              └──────────────────────┘  └──────────┬───────────┘
             │                                                   │ git push
             └──────────────────── PR opened ◄──────────────────-┘

  state:  Postgres (checkpoints, interrupts, Langfuse, pgvector) · Valkey (2 queues/caches)
          ClickHouse (traces) · SeaweedFS (raw events, index artifacts)
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
   RRF, and reranks the top-k with a cross-encoder. Neo4j answers the structural questions none
   of those reach: what calls this, what breaks if it changes.
5. **The graph interrupts, and a human decides.** `interrupt()` persists the payload to the
   checkpointer and the thread waits. The decision is taken in Agent Inbox or the dashboard —
   accept, edit, respond or ignore, bounded by the four booleans the graph declared — and
   `Command(resume=...)` continues from the same checkpoint.
6. **Every file and shell operation goes through the OpenShell sandbox.** Because `BaseSandbox`
   builds `read`/`write`/`edit`/`ls`/`glob`/`grep` on `execute()`, the policy is a real boundary
   for that whole class — and the egress gateway bounds outbound network below the agent. The
   policy hash is attested before the backend is exposed, and disagreement fails closed.
7. **The `reviewer` graph reads the PR** and records findings; `analyzer` learns the repository's
   review preferences over time.
8. **Every step emits a trace.** The `traced_*` entrypoints emit OTLP spans to Langfuse, which
   writes them to ClickHouse and the raw events to SeaweedFS.
9. **The result returns to GitHub** as a PR, a review comment, or a status on the originating
   issue.

### The three governance seams

SpecUP's interest in this stack is not that it codes. It is that steps 5, 6 and 8 are the only
points where a governance claim can be made mechanical — and **they do not all have the same
strength**, which is the most useful thing this report can say about them:

| Seam | What it is | Binds content? |
|---|---|---|
| **Step 6 — the sandbox** | a tool call satisfies the policy or it does not | **Yes.** The policy is hashed and attested, and disagreement fails closed |
| **Step 8 — the trace** | a record produced by the run rather than asserted about it | **Yes**, in the sense that matters: it is emitted, not written afterwards |
| **Step 5 — the decision** | a human accepts, edits, responds or ignores | **No.** It is a click, authenticated but unsigned, stored in a database |

Everything else in the stack is plumbing that makes those three possible. **The third is the
weak one, and it is the one SpecUP's whole model is about.**
[§11](#11-open-questions) question 3 is the gap.

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

---

## 6. The shared substrate

Counted by consumer rather than by container, the stack is smaller than its directory count:

| Service | Wanted by | Separable? |
|---|---|---|
| **PostgreSQL** | Aegra (checkpoints, interrupts), Langfuse (transactional), `rag/index/ann` via `pgvector` | Shareable as databases in one cluster. Langfuse runs its own migrations, so a shared schema is not an option — separate databases, one server |
| **Valkey** | Aegra (queue, SSE), Langfuse (cache, queue) | Yes, by database index or key prefix |
| **ClickHouse** | Langfuse only | **No.** Transitive dependency of §3.5 |
| **Neo4j** | structural retrieval only | Yes — and see [§8.1](#81-the-graph) |
| **SeaweedFS** | Langfuse (required), `rag/index` artifacts under the FAISS reading | One instance serves both |
| **Model serving** | `rag/embed`, `rag/rerank` | **One process serves both.** TEI, Infinity, llama.cpp or Ollama — permissive, and not a directory in the layout because it is config, not a component |

So eleven components resolve to **five stateful services plus one model server**, and three of
the five exist because Langfuse does.

**That concentration is worth noticing.** Before this revision, RabbitMQ existed only because
Plane did and ClickHouse only because Langfuse did. Removing Plane removed one of those
dependencies and left the other more exposed: **observability is now most of the operational
weight of the stack.** It is still the right call — step 8 is a governance seam — but the cost
should be attributed to the thing that causes it rather than spread across "the stack".

**The retrieval pipeline is the opposite case.** Seven stages, eleven directories, and under the
pgvector reading it adds **one process** — the model server — to services that already exist.
Directory count is a very poor proxy for operational weight, and `rag/` is where the two diverge
most.

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

**Every entry but one is permissive.** A `NOTICE` file becomes a shipping requirement the moment
any of them is vendored or redistributed; it does not exist yet, because nothing is vendored yet.

**Two obligations left this stack**, and both are worth recording because they were the hardest
items in the previous draft:

| Removed | Was | Why it is gone |
|---|---|---|
| Plane Community | AGPL-3.0, with §13's network clause | The tracker role was already covered ([§5](#5-the-interface-layer--what-replaces-plane)) |
| Docker Sandboxes (`sbx`) | **Proprietary** — its `LICENSE` is the single line *"Copyright © 2026 Docker Inc. All rights reserved."*, distributed as binaries only, with team-level policy behind the paid Docker AI Governance product | NVIDIA OpenShell does the same job at Apache-2.0, with a Deep Agents provider that already exists ([§3.4](#34-sandboxopenshell--nvidia-openshell)) |

### 7.1 One copyleft component

Neo4j CE is GPL-3.0, under a product licensed BUSL-1.1 and intended for sale. Two questions get
conflated here and they have different answers.

**Running it** — as a separate process, reached over Bolt, with the image pulled by a compose file
rather than redistributed. On the common reading this does not make SpecUP a derivative work: the
processes are separate, the interface is a network protocol, and Neo4j's own drivers are
deliberately Apache-2.0 precisely so that client applications are not encumbered.

**Shipping it** — vendoring the source, forking, publishing a derived image, or distributing an
appliance that includes it. This is where GPL-3.0 reciprocity applies.

**The distinction is not a loophole, and it is also not a guarantee.** It is the common reading,
it is how most of the industry operates, and it has not been tested here against this specific
deployment. One thing makes it more than academic: an "appliance" — a one-command install that
brings up the whole stack — is a natural product for this project and sits much closer to
distribution than a compose file does.

**What changed is the stakes, not the analysis.** This is no longer one of several licence
problems to be balanced. It is the last one, and [§8.1](#81-the-graph) shows that removing it also
removes a container.

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

**And one obligation this creates that the stack does not have yet:** if models are shipped rather
than downloaded at install time, their licences join the `NOTICE` file, and a model is a much
larger redistribution than a Python package. Whether SpecUP ships weights or pulls them is
[§11](#11-open-questions) question 8.

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

---

## 8. Alternatives, where there are any

Two components are still worth a substitution argument — one for licence, one for maturity. The
retrieval models have their own, in [§3.6](#36-rag--the-retrieval-pipeline) and
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
| **Drop the graph** | — | Recursive CTEs in Postgres, or the three `rag/` arms alone. Costs structural retrieval entirely |

**The strongest candidate is not another graph database.** It is **Apache AGE**, or plain
recursive SQL, in the PostgreSQL that Aegra and Langfuse already require. That removes a
container, removes the last licence obligation in the stack, and keeps the code graph in the same
backup and migration story as everything else.

It also composes with [§3.6](#36-rag--the-retrieval-pipeline): under the pgvector reading, AGE
would put the structural index in the same database as the dense one, and **the entire retrieval
layer becomes extensions on a server that is already mandatory.**

And the last row is now answerable rather than rhetorical. `eval/golden/` is exactly the
instrument that says whether the graph earns a container — which is the difference between
dropping it as a decision and dropping it as a guess.

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
| **The binding from a decision to an approval** | [§3.3](#33-agent-inbox--the-explicit-decisions). An Agent Inbox decision is `claimed`, never `witnessed`. Nothing hashes it, writes it to a reviewable file, or binds it to a signed commit — and that is the one gap SpecUP exists to close |
| **The middleware broker** | The third row of §3.4's table — `commit_and_open_pr`, `request_pr_review`, `task` — is ungoverned without it. Smaller than it was, because OpenShell's egress gateway now covers the network row, but not empty |
| **The OpenShell policy itself** | `sandbox/openshell/` is where the YAML belongs, and it is the one artifact in this stack SpecUP would genuinely govern. Nothing is in it |
| **The indexing job** | `rag/` describes a pipeline and names no thing that runs it. Something has to walk the repository, chunk, contextualise, embed and index on every commit, and decide what is incremental. It is the largest unwritten piece of the retrieval layer |
| **The embedding model's serving budget** | One model server is one process and an unquantified amount of GPU or CPU. `rag/` says which models; nothing says on what hardware, at what latency, for what corpus size |
| **Secrets** | No `.env`, no `.env.example`. Langfuse, the model provider and the GitHub App all need credentials. OpenShell's provider policy covers credentials inside the sandbox only |
| **Ingress** | Langfuse, Aegra, the Open SWE dashboard and the Agent Inbox all want HTTP. Nothing terminates TLS or routes |
| **Content in `docker-compose.yml`** | The file that would compose all of this is zero bytes |

**Two gaps closed in this revision**, and both were named in earlier drafts. The Plane → Agent
Protocol adapter is gone because Open SWE's own GitHub integration replaces it — it was *"the
component that does not exist upstream"*, the one piece SpecUP would have owned indefinitely. And
the embedding model, listed as *"the largest unpriced item here"*, is now
[§3.6.4](#364-embedqwen3-embedding--the-model-that-was-missing).

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
| **…and where the stack agrees with it** | **OpenShell's policy is a YAML file.** It is diffable, reviewable in a pull request, version-controlled — and then hash-attested at runtime, failing closed if the running policy is not the file that was approved. That is filesystem authority applied to containment, and it is the closest thing in this stack to SpecUP's own model arriving from outside it |
| **Approval provenance** | `APV-002` grades an approval `witnessed` only when a signature verifies against `allowed-signers`. Every decision this stack produces would be `claimed`. SpecUP can either say plainly that runtime decisions are a weaker class than governance approvals, or build the binding — but it cannot quietly present one as the other |
| **`requires-python`** | SpecUP declares `>=3.10` in `bundle.yml` and `extension.yml`. Deep Agents needs `>=3.11`; Aegra needs `>=3.12`. The bundle declares the highest floor, so this is a two-step jump |
| **A bundle cannot enforce** | `using-specup.md` is explicit: *"Bundle │ No │ Distribution only."* The broker's authority has to come from a workflow `shell` step or from the sandbox policy, never from the bundle |
| **No `{{ inputs.* }}` in a `run:` field** | Hard-enforced by `tests/test_workflows.py:84-99`, `allowed = {"context.run_id"}`. A rendered `openshell` invocation is a `run:` field |
| **Exit code `2` inverts at the broker** | Everywhere else in SpecUP, `2` means "not a governance failure". At the broker, `2` denies. Defensible — and it must be said in those words, because the manual teaches the opposite |
| **`specup.md` has nothing on execution** | Verified keyword counts over 3,382 lines: `docker` 0, `container` 0, `sandbox` 0, `isolat*` 0, `permission` 0, `privileg*` 0, `runtime` 0, `subprocess` 0. The authority layer traces to §51 and §56-60. **The containment layer has no textual basis at all**, and needs an *Additions* section mirroring the existing "Corrections to `specup.md`" |
| **Third-party code — and now weights** | `docs/dev/licensing.md` states *"There is none vendored. Every file in this repository is the copyright of one author."* The first component adopted makes that false. Model weights make it false in a second way, with terms that are not a code licence ([§7.2](#72-model-weights-carry-licences-too-and-the-good-ones-often-forbid-you)) |

---

## 11. Open questions

Named here, decided nowhere in this document. Each is an ADR candidate.

1. **Does SpecUP redistribute this stack, or compose it?** Determines whether §7.1's copyleft
   analysis is comfortable or load-bearing. **Everything else depends on this one**, and it is
   now a much smaller question than it was, because only one component turns on the answer.
2. **Neo4j, Apache AGE, a commercial Neo4j licence, or no graph at all?** Follows from 1, and
   now measurable through `eval/golden/`. **Answering it "AGE" makes the whole stack permissive.**
3. **Does an Agent Inbox decision become a SpecUP approval, and how?** §3.3 and §9. The decision
   has a schema, a payload and a durable record; nothing hashes it or binds it to a signer. This
   is the question where SpecUP's own model and this runtime actually meet.
4. **Which surface owns which decision** — the Open SWE dashboard, the Agent Inbox, or both? And
   does Agent Inbox authenticate against Aegra at all? §3.3's two caveats.
5. **Is OpenShell's alpha status acceptable, and behind what indirection?** §8.2. The same trade
   Aegra represents, taken twice in one stack.
6. **Is `rag/index/ann` pgvector or a local library?** §3.6.5. It also decides whether
   `db/seaweedfs` gains a second consumer, so it is one fork showing in two places.
7. **Is contextual chunking worth its recurring model cost?** §3.6.2 is the largest gain in the
   pipeline and the only stage that pays per index build.
8. **Does SpecUP ship model weights or download them?** §7.2. Shipping them makes their terms a
   redistribution obligation; downloading them makes the stack depend on a network at install.
9. **What runs the indexing job, and how incremental is it?** §9. The largest unwritten piece of
   the retrieval layer.
10. **OTLP or Langfuse's native SDK?** §5.2. The cheapest decision in this report and the one most
    likely to be made by default rather than on purpose.
11. **Is GitHub-only intake acceptable, or is a tracker-agnostic adapter needed?** §5.3.
12. **Where does governance state live once Postgres exists?** The `NON-FR-CORE-0001` question,
    and the one most likely to be decided by accident.
13. **What does the broker do about the tools no boundary catches?** §3.4's third row.
14. **Do the placeholder directories stay?** The other half of the 0.1.2 plan's *Loose end*.
    Committing them answers *"record their intent or remove them"* in favour of recording, and
    that was a decision rather than a discovery: `agent-inbox/` and `rag/` have intent written
    here, and `agent/`, `langfuse/` and the five `db/` entries still do not. **An empty directory
    in git is a claim about the future**, and the ones with no §3 entry beyond an inference are
    the ones most likely to be wrong.

---

## 12. Sources

Every URL was fetched or searched during the sessions that produced this document, 2026-09-17.
Licence claims in §7 were read from each project's own licence file or model card; roles and
architecture from the documents listed.

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

**Retrieval — the models, and their licences**
- <https://huggingface.co/Qwen/Qwen3-Embedding-0.6B> — **`apache-2.0`**; 32K context; user-defined dimensions 32–1024; instruction-aware; *"over 100 languages"* including programming languages
- <https://huggingface.co/Qwen/Qwen3-Reranker-0.6B> — **`apache-2.0`**; 0.6B, 28 layers, 32K context; cross-encoder, instruction-aware
- <https://huggingface.co/BAAI/bge-reranker-v2-m3> — `apache-2.0`; 0.6B on bge-m3; documented usage truncates at 512 tokens
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
- <https://github.com/neo4j/neo4j-python-driver> — drivers are Apache-2.0
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

**Within this repository**
- [`docs/dev/licensing.md`](../dev/licensing.md) — BUSL-1.1, the Additional Use Grant, the Elastic-2.0 exclusion
- [`AGENTS.md`](../../AGENTS.md) — "Resolve, or stop — never infer"; "Re-read before asserting"
- [`docs/guide/using-specup.md`](../guide/using-specup.md) — exit-code contract; bundles cannot enforce
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
word: one person read a source and wrote down what it said. The citations in §12 exist so that a
second person can repeat the reading, which is the only verification available.

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
  it shows up in a pull request like anything else. **What is still unchecked is agreement between
  the folder and this page.** Nothing fails if §1's inventory stops matching
  `find open-swe -mindepth 1 | sort`, and that is a check somebody could actually write.
- **Every role in §3 marked *Inferred* is a guess**, and the *Specified* ones are decisions taken
  in a research document rather than an ADR. Both are weaker than they look. Do not let either
  distinction erode into "the layout says so".

**And two things are newly fragile.** Aegra and OpenShell are young, and one of them is badged
alpha at the exact point where SpecUP's containment claim would be made. The report recommends
both, and it recommends them *because* the alternatives were a licensed runtime and a closed one.
That is a defensible trade and it is not a free one.

**The retrieval pipeline's numbers are all borrowed.** 35%, 49%, 67%, +4.3 Recall@5, 61.94
nDCG@10 — every one is somebody else's measurement on somebody else's corpus. `rag/eval/` exists
so that this stack can produce its own, and until it does, §3.6 is a well-cited hypothesis.

Re-read before relying on any of it.
