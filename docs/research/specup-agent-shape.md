# The SpecUP agent runtime — the shape it takes in production

**Audience:** anyone who has to stand this stack up, operate it, or write the specification that
comes after this one.

**Status: synthesis. It decides nothing and researches nothing new.** Every component, licence and
ruling behind this page is argued in
[`specup-agent-stack.md`](specup-agent-stack.md), which is 2,790 lines and is organised by
*component*. This page is organised by **how the thing runs**. It describes one coherent production
system, in the order a reader would need to understand it to operate it, and it stops there.

**What it is for.** It is the input to `docs/research/specup-agent-runtime.md`, which does not exist
yet. That document will have to specify processes, interfaces and failure behaviour precisely enough
to build from. This one establishes the shape it specifies — and, more importantly, **the list of
things that shape rests on**.

> **The governing rule of this page: a coherent story is more dangerous than an incoherent one.**
> The stack report marks each claim *Verified*, *Inferred*, *Specified* or *Decided*, and the
> inferences are visible because they sit beside the readings that produced them. Synthesising them
> into a single narrative hides that seam — everything reads equally solid once it is in a
> deployment diagram. So **every load-bearing inference in this document carries an id**, and
> [§9](#9-the-assumption-register) is the register. There are **31 of them**. A reader who takes one
> thing from this page should take that number.

**What this page deliberately leaves out**, because the stack report already holds it and
duplicating it would create two places to keep current:

| Not here | Where it lives |
|---|---|
| Licence analysis, copyleft exposure, model-weight terms | [stack §7](specup-agent-stack.md#7-the-licence-position) |
| Why each component was chosen, and what was rejected | [stack §3](specup-agent-stack.md#3-the-twelve-components), [§8](specup-agent-stack.md#8-alternatives-where-there-are-any) |
| The ten rulings and the twenty-four open questions | [stack §12](specup-agent-stack.md#12-what-is-decided-and-what-is-not), [§13.10](specup-agent-stack.md#1310-six-new-questions) |
| The fifteen-factor scoring | [stack §11](specup-agent-stack.md#11-the-stack-as-a-fifteen-factor-application) |
| Exploration policies and self-improvement | [stack §13](specup-agent-stack.md#13-meta-cognition-exploration-and-the-parts-that-must-not-be-explored) |

---

## 1. Five planes, not twelve components

The stack report counts twelve components because it is answering *what is each directory for*. A
runtime is not laid out that way. Counted by **what fails together and what is trusted together**,
the same software resolves into five planes:

| Plane | Answers | Holds | Fails how |
|---|---|---|---|
| **Control** | *what work exists and where is it up to* | Aegra, PostgreSQL, Valkey | **Hard.** Nothing runs |
| **Execution** | *what the agent is allowed to do, and doing it* | the five graphs, Vouch Shield, the OpenShell daemon and sandboxes, `vouch-bridge` | **Hard.** Work stops mid-flight |
| **Knowledge** | *where in this repository* | the model server, the index files, the graph over Bolt, the indexing job | **Soft.** The agent gets worse, and nothing says so |
| **Evidence** | *what happened, and can it be checked later* | Langfuse, ClickHouse, SeaweedFS, the OTel Collector, `stdout`, the signed commits | **Soft, and this is the dangerous one** |
| **Interface** | *where a human sees it and decides* | GitHub, the Open SWE dashboard, Agent Inbox, the Langfuse UI | **Soft.** Work continues unobserved |

**That grouping is the synthesis, and it earns its place by predicting something the component list
does not.** Two planes fail *soft*, and one of those two carries a governance seam. When the
evidence plane degrades, work continues and produces no record — which is indistinguishable from
work that produced a record nobody read. [§7](#7-failure-modes-and-what-each-one-actually-costs)
takes that apart.

**The trust gradient runs across the planes, not down them.** The control plane holds state nobody
can diff. The execution plane holds the only two hash-attested boundaries in the system. The
evidence plane holds the only artifact that can still be verified a year later by somebody who was
not there. Those three facts are what the rest of this page is arranged around.

---

## 2. The processes

**Eleven processes, one host prerequisite, and one thing that is not a process.** Everything below
is *Verified* from the stack report unless it carries an `ASM-` id.

| # | Process | What it is | Binds | State | If it dies |
|---|---|---|---|---|---|
| 1 | **Aegra** | Agent Protocol server on uvicorn | TCP `2026` | none in-process | Runs stop; they resume from the checkpoint |
| 2 | **Aegra worker** | where the LangGraph runs actually execute (`ASM-14`) | — | none in-process | The run resumes from its last checkpoint |
| 3 | **PostgreSQL** | checkpoints, thread state, **every pending interrupt**, Langfuse transactional | `5432` | **authoritative** | Everything stops |
| 4 | **Valkey** | Aegra's job queue and SSE pub/sub; Langfuse's cache and queue | `6379` | ephemeral | New runs do not start; clients cannot reattach |
| 5 | **ClickHouse** | Langfuse traces, observations, scores | `8123`/`9000` | derived | Traces stop being queryable |
| 6 | **SeaweedFS** | Langfuse raw events; built index artifacts | S3 gateway | **authoritative for raw events** | Langfuse ingest halts; no process can load an index |
| 7 | **Langfuse** | trace store UI and API; OTLP endpoint | HTTP | none in-process | The evidence plane goes blind |
| 8 | **Model server** | one process serving the embedder **and** the reranker (`ASM-11`, **measured 2026-09-19**) | HTTP | none | Dense retrieval and reranking stop; BM25 survives. **Corrected: they stop together and they also stop if either model fails to load** — a reranker Infinity could not type aborted startup and took the healthy embedder with it. One process is one blast radius |
| 9 | **OpenShell daemon** | creates and supervises sandboxes | host socket | sandbox lifecycle | Every tool call fails |
| 10 | **`vouch-bridge`** | the signing sidecar; holds the agent's private key | local socket (`ASM-17`) | **the key** | No commit can be signed; no PR can be opened |
| 11 | **OTel Collector** | receives `stdout` logs and OTLP spans, routes both | OTLP | buffer | Logs and traces are dropped at the edge |
| — | **The graph server** | reached over Bolt; **SpecUP does not run it** | `7687` | the customer's | Structural retrieval stops |
| — | **The OpenShell runtime** | a **host installation**, not a container | — | — | Nothing starts |

**Not a process:** `rag/` is a library in the agent's own process (`ASM-20`), and Vouch Shield is a
library in the same process. Neither is a service, neither has a port, and neither appears in a
compose file. The stack report says this twice and it is the single easiest thing to get wrong when
drawing this system, because both of them *behave* like services.

**The sandbox is a process the agent creates**, one per run (`ASM-15`), holding the cloned working
tree (`ASM-16`) and destroyed at the end. It is the only process in this system whose lifetime is
shorter than a run.

### Where each process sits relative to the sandbox boundary

This is the question the component list does not answer and the runtime cannot avoid.

| Inside the sandbox | Outside it, in the agent process | Outside it, elsewhere |
|---|---|---|
| The cloned working tree | the five graphs | Aegra, Postgres, Valkey |
| `execute()` and everything built on it — `read`, `write`, `edit`, `ls`, `glob`, `grep` | Vouch Shield | the model server |
| Build and test commands | `rag/` retrieval (`ASM-20`) | the graph over Bolt (`ASM-21`) |
| | the Bolt client | `vouch-bridge` and the signing key |
| | the OTLP exporter (`ASM-22`) | Langfuse, ClickHouse, SeaweedFS |

**The consequence is worth stating in one sentence: the sandbox contains code execution over a
working tree, not the agent's reasoning.** Retrieval, policy evaluation and trace emission all
happen in the agent's own process, outside the boundary. That is coherent — it is what makes the
`execute()` chokepoint meaningful — and it means the containment claim is narrower than "the agent
is sandboxed" suggests. Anybody writing marketing copy about this should read this table first.

---

## 3. The state, and which of it can be reviewed

Six stores. **One of them is a filesystem and the difference is not cosmetic** — it is the whole of
`NON-FR-CORE-0001`.

| Store | Holds | Durable | Diffable | Lost if it goes |
|---|---|---|---|---|
| **PostgreSQL** | run checkpoints, thread state, **pending human decisions**, Langfuse transactional state | yes | **no** | every run in flight, and every queued decision |
| **Valkey** | job queue, SSE channels, Langfuse cache | no | no | queue position; runs recover from checkpoints |
| **ClickHouse** | traces, observations, scores | yes, derived | no | nothing permanently — SeaweedFS holds the raw events |
| **SeaweedFS** | raw trace events, built index artifacts | yes | no | trace recoverability, and every index |
| **The repository** | `.specify/` governance tree, `vouch/` rules and `did.json`, the OpenShell policy YAML, source | yes | **yes** | nothing — it is git |
| **Local disk** | the BM25 and ANN index files, the model cache at `HF_HOME` | no | no | rebuildable, expensively |

**Two rows in that table are where SpecUP's model and this runtime actually collide.**

**First, Postgres holds human decisions.** An `interrupt()` payload and its answer live in the
checkpointer. That is governance data in a store that cannot be diffed, reviewed or bisected —
the conflict [stack §10](specup-agent-stack.md#10-where-this-argues-with-specup-as-it-stands) calls
its sharpest, and it is a runtime fact rather than a design opinion. **Nothing in this shape
resolves it.** The decision is `claimed` at the moment it is taken, and it stays `claimed` unless
something later hashes it and binds it to a signed commit.

**Second, the governance tree is inside the sandbox.** `.specify/` lives in the repository being
worked on, so when Open SWE clones that repository into a sandbox, the governance tree goes with it
— including `.specify/extensions/openup/scripts/python/`, which is the set of validators.
[Stack §13.7](specup-agent-stack.md#137-one-rule-and-the-five-places-it-lands) says an agent may
never write to those, and guesses that Vouch Shield is the mechanism. **On this shape that guess is
wrong, and the correction matters:**

- Shield evaluates `action` + `target` + `resource`, and its own documentation says path
  normalisation *"resolves `..` lexically but cannot see symlinks"* and that *"servers must
  independently confine real paths to a configured root."* It is interception.
- OpenShell's **filesystem policy** is locked at sandbox creation, hash-attested, and fails closed
  on any version disagreement. It is containment.

**So the protection of the governance tree belongs in the OpenShell policy YAML, not in the Shield
rules.** That is `ASM-28`, it is the most consequential correction this synthesis makes to the
source document, and it costs nothing to adopt because the policy file has to be written anyway.

**And it leaves a second problem that this shape cannot solve.** If the validators are inside the
sandbox, so is every run of them, and an agent that can execute code in a sandbox can influence what
they print. **The evaluation that decides whether the agent's work passes must happen outside the
sandbox, on the pull request, after the sandbox is gone.** That is CI. This repository has no
`.github/workflows` today, so the place that check belongs does not exist yet
([§10](#10-what-this-hands-to-the-runtime-document)).

---

## 4. The run lifecycle

One run, end to end. Every numbered step is a boundary crossing or a state write; nothing else is
listed.

```
 INTAKE          CONTROL              EXECUTION                  EVIDENCE
 ──────          ───────              ─────────                  ────────
 GitHub  ──(1)──► Aegra ──(2)──► agent graph
 issue/PR         │ thread             │
                  │ Postgres           ├──(3)── rag/ retrieval  ──► index files
                  │ Valkey queue       │        + Bolt              (read-only)
                  │                    │
                  │                    ├──(4)── interrupt() ───► Postgres
                  │                    │          ▲                 │
 Agent Inbox ◄────┴────────────────────┘          └── Command(resume)
                                       │
                                       ├──(5)── Shield check  ──► deny → stop
                                       │
                                       ├──(6)── execute() ─────► OpenShell sandbox
                                       │                          policy hash attested
                                       │                          egress gateway
                                       │
                                       ├──(7)── sign ──────────► vouch-bridge
                                       │
                                       └──(8)── OTLP spans ────► Langfuse → ClickHouse
                                                                          └► SeaweedFS
 GitHub  ◄──(9)── PR, signed, Vouch-DID trailer
```

**1. Intake.** A GitHub App event — an issue labelled, a PR comment, a review request — or a task
started in the dashboard. No adapter exists or is needed; this is Open SWE's own integration.
**What is not specified anywhere:** which events are accepted, from which repositories, and whether
an unrecognised event is dropped or queued.

**2. The run is accepted.** Aegra creates a thread, writes the first checkpoint to Postgres and
enqueues the job in Valkey. **From this moment the run survives a process restart** — which is the
capability Aegra exists in this stack to provide, and the reason `langgraph-api` is not needed.

**3. Retrieval.** The `agent` graph asks *where in this repository*. Four arms answer: BM25 over
`index/bm25s/`, dense over `index/ann/hnsw/` for code and `index/ann/ivf/` for static binding
documents, fused by reciprocal rank fusion, and the top-k reranked by a cross-encoder. The graph,
over Bolt, answers the structural questions the other three cannot: what calls this, what breaks if
it changes. **All four run in the agent's process, against artifacts built earlier**
([§5](#5-the-indexing-lifecycle)). Nothing in this step writes.

**4. The interrupt.** `interrupt()` persists the payload and the thread stops. The decision is taken
in Agent Inbox or the dashboard — **accept, edit, respond or ignore**, bounded by the four booleans
the graph declared at the moment it asked — and `Command(resume=...)` continues from the same
checkpoint. **This is the only step with no time bound** (`ASM-30`): a thread can wait indefinitely,
and the Postgres row waits with it.

**5. The Shield check.** Every tool call is evaluated against a rules file that denies by default.
`action` and `target` match exactly; `resource` is glob-matched against normalised paths. Unknown
keys are rejected at load. On any failure a structured error is raised **before the tool body runs**.
**Note the exit-code inversion here**: everywhere else in SpecUP `2` means *not a governance
failure*; at the broker, a denial stops the action.

**6. Execution.** What survives the check reaches the sandbox. Because `BaseSandbox` builds
`read`/`write`/`edit`/`ls`/`glob`/`grep` on `execute()`, the filesystem and process policy is a real
boundary for that entire class, and the egress gateway bounds outbound network below the agent. The
policy hash is attested before the backend is exposed and any version disagreement fails closed.
**Steps 5 and 6 are not redundant and neither replaces the other:** Shield knows what an operation
*means* and cannot see a symlink; OpenShell knows what a process can *reach* and cannot tell a pull
request from a force-push.

**7. Signing.** The commit is signed by `vouch-bridge`, which holds the key and runs outside the
sandbox. **The key is never inside the boundary it is signing about**, which is the entire point of
the Identity Sidecar pattern and is not optional in a stack whose premise is that the agent is
contained.

**8. Telemetry.** The `traced_*` entrypoints emit OTLP spans. Langfuse writes them to ClickHouse and
the raw events to SeaweedFS first, which is what makes its ingest recoverable. **Application logs do
not go here** — they go to `stdout` and the Collector routes them, with `trace_id` injected so the
two correlate without being stored together.

**9. Delivery.** A pull request, a review comment, or a status on the originating issue. The commits
carry an SSH signature and a `Vouch-DID` trailer. **This is the only step whose output can be
verified after the fact by somebody who was not there.**

### The five boundaries, and what each one actually binds

Reordered from [stack §4](specup-agent-stack.md#4-how-they-compose) by strength, because the runtime
consequence of each is different:

| Step | Boundary | Enforced or intercepted | Binds content |
|---|---|---|---|
| 6 | tool call → sandbox | **Enforced.** Kernel-level, policy hashed at creation | **Yes** — the policy, by hash, failing closed |
| 6 | sandbox → network | **Enforced.** Egress gateway below the agent | Host, not operation. `github.com` allowed does not distinguish a PR from a force-push |
| 9 | agent → git | **Enforced.** The key is unreachable from the model | **Yes**, and it survives the deployment |
| 5 | agent → tool call | **Intercepted.** The agent's own process performs the check | The rules, yes. The issuer list, no — it is an environment variable |
| 4 | human → decision | **Neither.** Authenticated, unsigned, stored in a database | **No** |

**The bottom row is the one SpecUP's whole model is about, and it is the only one with nothing
behind it.** Four boundaries were strengthened across two revisions of the stack report and this one
did not move.

---

## 5. The indexing lifecycle

**This is a second lifecycle, not a step in the first**, and treating it as a step is the most
common way to get this architecture wrong. It has a different trigger, a different credential, a
different network posture and a different failure mode. [Stack §9](specup-agent-stack.md#9-what-the-layout-does-not-have)
calls it *"the largest unwritten piece of the retrieval layer"*; what follows is the shape it has to
take given everything else already decided, and it is **Specified** throughout.

```
commit ──► Merkle walk ──► changed chunks only
                             │
                             ├─ 1. chunk      tree-sitter AST (cAST)
                             ├─ 2. contextualise  ──► PROVIDER  ⚠ egress + credential
                             ├─ 3. tokenise   one shared BPE
                             ├─ 4. embed      local model server
                             ├─ 5. index      bm25s │ ann/hnsw (code) │ ann/ivf (static)
                             │
                             └──► artifact + ML-BOM ──► SeaweedFS ──► agent pulls read-only
```

**Trigger and scope.** A commit on a watched branch. The job hashes the working tree as a Merkle
tree — a hash per file, and a hash per folder derived from its children's — so a small edit changes
only that file's hash and its parents' up to the root. Only chunks under a changed hash are
re-processed; embeddings are cached by chunk content hash. **Without this the job re-runs stage 2
over the whole repository on every commit, and stage 2 is the only metered stage.**

**Where it runs, and why not in the sandbox** (`ASM-18`). Stage 2 sends every changed chunk to the
configured provider. It therefore needs outbound access to the provider API and a provider
credential — **the two things the sandbox policy is strictest about**. Running the indexer inside a
sandbox means punching both holes in the boundary that exists to prevent exactly that. It runs
outside, as an admin process in the same package as the graphs, against a release, with the same
config. That is factor XII, and it is the factor's own prescription rather than a preference.

**Two indexes, split by how fast the data changes** — not by benchmark score:

| Index | Corpus | Why |
|---|---|---|
| `ann/hnsw/` | code, and anything that churns | HNSW tolerates incremental updates |
| `ann/ivf/` | ADRs, contracts, API specifications, standards | IVF is *"not resilient to index updates"* and needs rebuilding — free for a corpus that is frozen between releases, and it costs a fifth of HNSW's memory |

**Publication and load.** The built index is a large binary artifact. It goes to SeaweedFS with a
**CycloneDX ML-BOM** beside it carrying the commit, the model id and pinned revision, the chunker
version and the release id. The agent process **pulls it read-only at start and never writes it at
runtime** (`ASM-19`) — which is what makes the process share-nothing despite retrieval being a local
library, and is the whole of
[stack §11.3](specup-agent-stack.md#113-two-collisions-and-both-resolve)'s second collision.

**The one thing nothing in this shape answers: what retrieval does at a cold start.** A fresh
deployment has no index. A process that starts before the first indexing run completes has four
retrieval arms and three of them return nothing. **Nowhere is it written whether that is a startup
failure, a degraded mode, or silence** — and silence is what it will be unless somebody decides
otherwise ([§10](#10-what-this-hands-to-the-runtime-document)).

---

## 6. Configuration and policy, item by item

[Stack §11.3](specup-agent-stack.md#113-two-collisions-and-both-resolve) drew the line and
[stack §12.2](specup-agent-stack.md#122-the-eighteen-questions) question 15 observed that *"nothing
applies it to the stack's actual settings."* **This section applies it.** The test is the factor's
own: config is *"everything that is likely to vary between deploys"*; a policy varies between
**decisions**.

**Config — the environment, per factor III:**

| Item | Belongs to |
|---|---|
| Postgres DSN (Aegra), Postgres DSN (Langfuse) | control |
| Valkey URL | control |
| ClickHouse URL and credentials | evidence |
| SeaweedFS S3 endpoint, access key, secret | evidence |
| Langfuse host, public key, secret key | evidence |
| OTLP endpoint | evidence |
| Bolt URI, user, password | knowledge |
| Model server URL | knowledge |
| `HF_HOME` / model cache directory | knowledge |
| GitHub App id, private key, webhook secret | interface |
| Provider API key | knowledge |
| Listening ports, log level, `VOUCH_TARGET` | all |

**Policy — a version-controlled file, per `NON-FR-CORE-0001`:**

| Item | Where | Note |
|---|---|---|
| The OpenShell policy YAML | `sandbox/openshell/` | filesystem, process, network, providers. Hash-attested at creation. **This is where the governance tree is protected** — `ASM-28` |
| The Vouch Shield rules | `vouch/` | `deny_default: true`; the allow list for `commit_and_open_pr`, `request_pr_review`, `task` |
| **The trusted issuer list** | `vouch/` | **Moves out of `VOUCH_TRUSTED_ISSUERS`.** Keep an environment override that logs loudly when used |
| `.specify/governance/allowed-signers` | the repository | the **human** trust root, and never the agent's |
| Embedder and reranker model id **and pinned revision** | `rag/embed/`, `rag/rerank/` | an unpinned revision makes retrieval quality unreproducible and no test catches it |
| Embedding output dimension | `rag/embed/` | Matryoshka truncation changes the index, so it is a decision, not a deploy detail |
| Chunker size budget | `rag/chunk/cast/` | changes every chunk boundary |
| RRF `k` and per-list weights | `rag/fuse/` | one formula, two parameters, and they move results measurably |
| Rerank depth | `rag/rerank/` | the quality-versus-latency dial |
| Which corpus goes to `ivf` versus `hnsw` | `rag/index/` | decision 2, made concrete |
| **Whether stage 2 egress is on** | `rag/chunk/contextual/` | this decides whether customer source leaves the network. It is not a deploy detail under any reading |
| Aegra's auth mode | `langgraph/aegra/` | and it is **never `none`** |
| The Conventional Commits type list | `.pre-commit-config.yaml` | already written |

**Three items resist the line and should be decided rather than defaulted.** The provider *model
id* for stage 2 (changing Sonnet for Opus changes index quality, so it is a decision wearing a
config's clothes); the sandbox image reference (a deploy detail until the day it pins a toolchain
version the build depends on); and the embedding dimension, listed above as policy on the argument
that it changes the artifact rather than the deployment.

---

## 7. Failure modes, and what each one actually costs

| What stops | Work stops | Work degrades | Data lost |
|---|---|---|---|
| **PostgreSQL** | **everything** | — | pending interrupts, if it does not return |
| **Valkey** | new runs; client reattach | — | queue position only; runs resume from checkpoints |
| **OpenShell daemon** | every tool call | — | the sandbox's working tree |
| **`vouch-bridge`** | every commit and PR | — | nothing |
| **Aegra** | new runs | — | nothing; in-flight runs resume |
| **SeaweedFS** | Langfuse ingest; index load at process start | — | raw trace events |
| **Model server** | — | **dense retrieval and reranking.** BM25 survives alone | nothing |
| **The graph** | — | **structural retrieval.** Three arms of four survive | nothing |
| **Provider API** | — | **stage 2.** New chunks are indexed uncontextualised | nothing |
| **ClickHouse** | — | traces unqueryable; raw events still land | nothing — SeaweedFS holds them |
| **Langfuse** | — | **the evidence plane goes blind** | spans in flight |
| **GitHub** | intake and delivery | — | nothing |

**Four readings worth carrying into the runtime document.**

**The knowledge plane degrades silently and nothing measures it.** A dead model server does not look
like an outage. It looks like an agent that has become worse at finding things — and since nobody
has a baseline, it looks like that indefinitely. `eval/golden/` is the instrument that would turn
this into a signal, and it is a directory with nothing in it.

**The evidence plane fails soft and it carries a governance seam.** Step 8 is one of only four
places a claim about this system can be made mechanical. When Langfuse is down, work proceeds and
produces no record — which is not distinguishable afterwards from work whose record nobody read.
**A failure in the only plane that can fail without anybody noticing is the failure most worth
alarming on**, and there is no alarm.

**Postgres is a single point of failure for both execution state and governance data.** That is not
a criticism of the design; it follows from the checkpointer being the durability mechanism. It does
mean the backup story for one database is the recovery story for every pending human decision, and
those two sentences are usually owned by different people.

**Nothing in this table is a *partial* failure.** Every row assumes a process is up or down. The
real failure modes of a stack like this — a slow Postgres, a rate-limited provider, a sandbox that
starts but cannot reach the egress gateway, an index that loaded but is six commits stale — are all
absent, because nothing in the source material bounds them. That absence is itself a finding.

---

## 8. What holds it together, and where it does not

The user-facing test of a runtime shape is whether it is one system or six pieces in a diagram.
**Four things make it one:**

1. **One protocol at the control plane.** The Agent Protocol. Four independent clients — the Open
   SWE dashboard, Agent Inbox, Agent Chat UI, LangGraph Studio — work against one API that nobody
   had to design for them. It is why removing the tracker cost a table of features rather than a
   rewrite.
2. **One chokepoint at the execution plane.** `execute()`. A provider implements one method and
   `BaseSandbox` builds six file operations on it, so a single policy covers a class of tools rather
   than a list of them.
3. **One signal format at the evidence plane.** OTLP. The `traced_*` wrappers are already the seam;
   instrumenting to the protocol rather than to a vendor SDK means the endpoint is a config item and
   not a rewrite.
4. **One identity across all three.** The agent's DID appears in the Shield rules that authorise it,
   in the commit trailer that records it, and in the credential that carries its intent. Three
   different layers naming the same subject in the same syntax.

**And three things do not hold together yet. They are the three the next document has to close:**

**The human decision is unsigned.** Everything the agent does is attributable and everything a human
decides is a click. The asymmetry is backwards from what the system is for.

**The governance tree is inside the thing being contained.** `.specify/` is in the repository, the
repository is in the sandbox, and the validators are in `.specify/`. The protection is available —
it is a filesystem rule in a hash-attested policy — and the **evaluation** still has nowhere trusted
to run, because there is no CI.

**There is no index at startup and no stated behaviour without one.** Three of four retrieval arms
depend on an artifact built by a lifecycle that is not implemented, published to a store, and pulled
at process start. The first deployment of this stack will run with one arm and no error.

---

## 9. The assumption register

**Thirty-one.** Column three says where each came from: *carried* means the stack report already
marks it *Inferred* and this document repeats it; **new** means this synthesis introduced it to make
the runtime coherent, and nothing upstream says it.

### Control and execution

| Id | The assumption | Source | If it is wrong |
|---|---|---|---|
| `ASM-01` | `agent/` holds SpecUP middleware and prompts over Open SWE, not a vendored fork | carried | Vendoring makes Open SWE's MIT notices a shipping obligation and changes decision 1's reach |
| `ASM-02` | `langgraph/aegra/` holds the Aegra deployment; `aegra.json` points at the five Open SWE graphs | carried | The control plane has no manifest and §2's process list loses its first two rows |
| `ASM-03` | ~~**Open SWE's five graphs run unchanged under Aegra**~~ **ANSWERED 2026-09-18 — it holds.** See below | carried | The largest single risk in this shape. Aegra's own compatibility list names Agent Chat UI, LangGraph Studio and CopilotKit — **not Open SWE.** If the graphs need changes, `agent/` becomes a fork and `ASM-01` falls with it |
| `ASM-14` | **The graphs execute in Aegra's worker processes**, not as a separate service | **new** | Shield and `rag/` are libraries in *some* process; if it is not this one, §2's boundary table is wrong throughout |
| `ASM-15` | One sandbox per run, created at start and destroyed at end | **new** | Per-thread or per-repository sandboxes change the isolation story between concurrent runs entirely |
| `ASM-16` | The repository is cloned into the sandbox; the working tree lives there | **new** | If the tree is mounted from the host, the filesystem policy is protecting a bind mount and `ASM-28` needs rewriting |
| `ASM-25` | Single tenant. Aegra's `store.scopes` exists and is not used at 0.1.3 | **new** | Multi-tenancy changes the state model, the trust model and the index model at once |
| `ASM-27` | All five graphs are deployed; nothing prunes `scheduler` or `analyzer` | **new** | Deploying fewer is cheaper and changes what the `scheduler` graph's absence means for recurring work |
| `ASM-29` | One repository per run | **new** | Open SWE supports more; multi-repository runs change retrieval scoping and the index layout |
| `ASM-30` | **An interrupt waits indefinitely.** No TTL, no expiry, no escalation | **new** | A Postgres row and a thread live forever. If there is a timeout, what happens to the run at expiry is unspecified |

### Knowledge

| Id | The assumption | Source | If it is wrong |
|---|---|---|---|
| `ASM-07` | `db/neo4j` holds a code property graph — symbols, files, imports, call edges | carried. **The weakest inference in the stack report** | It could be agent memory, a requirements ontology or a dependency graph. Step 3 of the lifecycle describes the wrong query |
| `ASM-11` | **One model server serves both the embedder and the reranker** — **ANSWERED 2026-09-19.** One Infinity process served both, at 3337 MiB and one pid. Two conditions it did not state: the runtime must be Infinity and not TEI, which takes one `--model-id` per process; and the reranker must declare `SequenceClassification`, which `Qwen3-Reranker` does not | carried | Two processes, two serving budgets, and §7's single degradation row becomes two |
| `ASM-12` | One BPE tokenizer is shared by every stage rather than one per stage | carried | A lexical hit and a dense hit stop referring to the same span — a retrieval bug that is very hard to see from results |
| `ASM-18` | **The indexing job runs outside the sandbox**, as an admin process in the same package | **new** | Running it inside means granting the sandbox provider egress and a provider credential, which is most of what the policy exists to deny |
| `ASM-19` | Indexes are pulled read-only at process start and never written at runtime | **new** | Factor VI's resolution collapses and the process stops being share-nothing |
| `ASM-20` | **`rag/` retrieval runs in the agent process, not in the sandbox and not as a service** | **new** | Determines whether index files are inside or outside the boundary, and whether the model server is reachable from the sandbox |
| `ASM-21` | The Bolt client runs in the agent process, so graph access is not a sandbox egress concern | **new** | If the graph is queried from inside, `7687` must be opened in the egress policy |
| `ASM-31` | The Merkle-tree incremental scheme is adopted for the indexing job | **new** (from [stack §12.3](specup-agent-stack.md#123-the-adopted-answers-and-the-outside-practice-they-rest-on) answer 9) | Every commit re-runs stage 2 over the whole repository, which is the only metered stage |

### State and evidence

| Id | The assumption | Source | If it is wrong |
|---|---|---|---|
| `ASM-08` | One Postgres cluster, two databases, not a shared schema | carried | Langfuse runs its own migrations, so a shared schema is not an option — but two clusters is, and it changes the backup story |
| `ASM-09` | One Valkey instance serves Aegra and Langfuse, separated by database index or key prefix | carried | Two instances, or a key collision nobody notices until it matters |
| `ASM-10` | ClickHouse exists for Langfuse and nothing else | carried | It becomes an independent choice rather than a transitive dependency, and §7's row changes meaning |
| `ASM-05` | `langfuse/` holds the self-hosted deployment, and the `traced_*` wrappers point at it | carried | The alternative is LangSmith, which is the hosted product this stack exists to avoid |
| `ASM-22` | OTLP is emitted from the agent process, not from inside the sandbox | **new** | The egress policy must allow the collector, and spans from sandboxed work need a different path |
| `ASM-23` | Application logs go to `stdout` and an OTel Collector routes them | **new** (from answer 16) | Factor XI is violated and Langfuse becomes a log store, which is what it looks like and is not |
| `ASM-24` | Secrets arrive as environment variables at process start. **No secrets manager is in scope at 0.1.3** | **new** | The stack has eight credentials and no rotation story; this assumption is what makes that acceptable *for now* and it should expire |

### Identity and containment

| Id | The assumption | Source | If it is wrong |
|---|---|---|---|
| `ASM-06` | `sandbox/openshell/` holds the policy YAML and the sandbox image definition | carried | The most governance-relevant directory in the layout has no stated contents |
| `ASM-13` | `vouch/` holds the Shield rules and the `did:web` document, **and never the private key** | carried | A repository is the worst possible place for a signing key, and a directory named for identity is where somebody will put one |
| `ASM-17` | `vouch-bridge` runs as a **per-host sidecar**, reached over a local socket the sandbox cannot see | **new** | Per-run means a key in each sandbox, which inverts the Identity Sidecar pattern |
| `ASM-26` | All stateful services are single-instance. **No HA, no replication, no failover** | **new** | §7's failure table is a list of outages rather than degradations |
| `ASM-28` | **The governance tree is protected by the OpenShell filesystem policy, not by Shield rules** — **ANSWERED 2026-09-19, and only above a version floor.** Written as an allowlist the policy blocks writes, symlinks included. `truncate(2)` is blocked at Landlock `ABI::V3` (the `dev` build) and **not blocked on any stable release**, where the trust root went from 2732 bytes to 0. Falsified 2026-09-18 on `v0.0.116`; that reading stands | **new — and it corrects [stack §13.7](specup-agent-stack.md#137-one-rule-and-the-five-places-it-lands)** | Shield cannot see symlinks and says so; a path rule there is advisory. If the policy cannot express the exclusion, the protection does not exist at any layer |
| `ASM-04` | Agent Inbox authenticates cleanly against Aegra's JWT or OAuth | carried, and flagged untested upstream | Its connection form asks for a LangSmith API key. If this fails, the decision surface is the dashboard alone and [stack §3.3](specup-agent-stack.md#33-agent-inbox--the-explicit-decisions) loses its premise |

### Six can be tested in an afternoon, and three of them are load-bearing

Everything above is untested. These six need no new code:

| Test | Settles |
|---|---|
| ~~Point an `aegra.json` at one Open SWE graph and start a run~~ **done** | **`ASM-03`** — the largest risk in the shape, and it holds |
| Open Agent Inbox against a local Aegra with JWT configured | **`ASM-04`** |
| ~~`openshell sandbox create` with a policy that excludes `.specify/extensions/**`, then try to write there~~ **done — and the write was the wrong test** | **`ASM-28`** — appending is blocked on every build; truncating is blocked only at Landlock ABI 3, which no stable release uses |
| Run `vouch-bridge` on the host and sign from inside a sandbox over the socket | `ASM-17` |
| Write one byte to an index file from the agent process and see whether anything objects | `ASM-19` |
| Start the agent with no index present | the cold-start behaviour nothing specifies |

**The three in bold are the ones that change the shape rather than a detail.** If `ASM-03` is false
this document describes a different system.

> **`ASM-03` was tested on 2026-09-18 and it holds.** Against `open-swe@8aac7c5` and
> `aegra@c07ad0d` on Python 3.14.4: Aegra listed all five graphs over the Agent Protocol, all five
> built, one `chat` thread completed with status `success`, and **Open SWE's tree was byte-clean
> afterwards.** The full record, the falsifier it was measured against and the reproduction script
> are in
> [`../implement/test-specup-agent-shape-assumptions.md`](../implement/test-specup-agent-shape-assumptions.md#p1--do-open-swes-five-graphs-run-unchanged-under-aegra).
>
> **It cost this document three corrections**, and none of them was what the probe was looking for:
>
> 1. **The floor is Python `>=3.14`, not `>=3.12`.** That figure came from Aegra, which is no
>    longer the highest floor in the stack. Open SWE's `pyproject.toml` and its `langgraph.json`
>    both say 3.14. Every `requires-python` statement for 0.1.3 inherits the new number.
> 2. **`aegra.json` cannot copy Open SWE's graph references verbatim.** Aegra resolves the left of
>    the `:` as a file path; Open SWE writes a module path. The rewrite is configuration, which is
>    why `ASM-03` survived — but [stack §3.2](specup-agent-stack.md#32-langgraph--aegra-and-the-agent-protocol-server)'s
>    *"no change in content, only in filename"* was wrong and is corrected there.
> 3. **`langgraph-api` (Elastic-2.0) arrives transitively through Open SWE**, and is imported when
>    present. Removing it was tried and cost nothing. The stack's licence condition is therefore
>    satisfiable, but it is **not the default**, and it becomes a build-time exclusion somebody has
>    to write down. This is new material for `ASM-01`'s ADR.
>
> **What the probe did not establish:** that any graph does its job. The `chat` run went through a
> stub model and, without PR context, `chat` degrades to a bare agent with no tools. P1 answers
> that the path runs, and that is all it answers.
>
> **P1b closes part of that gap without a credential.** Open SWE's own suite was run inside the
> same environment: **3434 passed, 0 skipped, 0 failed**, and **3433 passed with 1 failed** once
> `langgraph-api` was uninstalled. The single failure is a test of importing checkpoints from the
> `langgraph dev` server — a path an Aegra deployment does not use, and one whose *test body*,
> not its module, is what needs the Elastic-licensed package. **That is the evidence the exclusion
> in point 3 rests on.** It is recorded as evidence and not as a probe outcome, because it had no
> pre-registered falsifier. See
> [campaign §3.2](../implement/test-specup-agent-shape-assumptions.md#32--p1b-what-open-swes-own-test-suite-says).

> **`ASM-28` was tested twice — falsified on 2026-09-18, answered on 2026-09-19 — and the
> difference is a version number.** The row above now reads that way, and
> the reasoning belongs here because this is the assumption that decides whether
> [stack §13](specup-agent-stack.md#13-meta-cognition-exploration-and-the-parts-that-must-not-be-explored)'s
> single rule has an enforcement point or is advice.
>
> **The good half.** OpenShell installs, Landlock enforces, and the exclusion works — **but only as
> an allowlist.** A `read_only` path nested inside a `read_write` parent adds no restriction at all,
> because rights are the union of every matching hierarchy; a narrower rule can add rights and never
> subtract them. Enumerate what may be written and the governance tree is protected, **including
> through a symlink from a permitted directory** — the case this document said Shield could not
> catch. Landlock binds inodes, not path strings, so that half of `ASM-28` is vindicated.
>
> **The half that falsified it, on the shipped release.** `truncate(2)` is not a write Landlock
> can withhold at the ABI `v0.0.116` uses. Appending to `.specify/governance/allowed-signers` is
> denied; truncating it succeeds, and **the file `APV-002` verifies signatures against went from
> 2732 bytes to 0.** The host offered Landlock ABI 8 and the policy was built at ABI 2 — which
> predates `LANDLOCK_ACCESS_FS_TRUNCATE`.
>
> **The re-run, and what it settles.** On OpenShell's rolling `dev` build
> (`0.0.117-dev.204+ge38d7254e`), which carries `ABI::V3`, the same call returns **`EACCES`** and
> the file is untouched — while `truncate(2)` on a permitted path in the same sandbox under the
> same policy still succeeds, which is what makes the denial evidence rather than an artifact.
> So the exclusion does hold completely, and it holds on **no stable release**: `v0.1.0-pre.1`
> through `pre.4` are git tags with no published artifacts, and `install.sh` gives you `v0.0.116`
> by default.
>
> **What this changes for §10 and for the ADRs.** The enforcement point is not imaginary, so the five
> rows of stack §13's table are not advice — but they are only real under a pinned OpenShell version,
> and that pin becomes a requirement rather than a preference. **A minimum OpenShell version is now a
> deployment constraint with a security reason behind it**, which is the sort of thing an ADR has to
> carry a *Revisit when* for. One more reason it has to be a pin and not a note: the `dev` build
> **stopped logging the ABI**, so an operator can no longer read the attestation and tell whether
> truncation is covered. The only way to know is to run the probe. The full record and all three
> further findings are in
> [campaign §3.3](../implement/test-specup-agent-shape-assumptions.md#33--what-p2-found-and-what-the-answer-is-conditional-on).

---

## 10. What this hands to the runtime document

`docs/research/specup-agent-runtime.md` has to specify what this page only shapes. In dependency
order, because several of these determine the others:

1. ~~**Test `ASM-03` before writing anything else.**~~ **Done, 2026-09-18 — the graphs run
   unchanged, so `agent/` is a configuration directory and every other section's assumption
   stands.** What replaces this item is narrower and now has evidence behind it: state the
   Python floor as `>=3.14`, state that `aegra.json` rewrites Open SWE's module references as file
   paths, and state the `langgraph-api` exclusion as a build-time requirement rather than a
   property the composition has for free.
2. **Write the OpenShell policy YAML.** It is the only artifact that makes `ASM-28` real, and it is
   the one file in this stack that is simultaneously a governance artifact and a containment
   mechanism. It must exclude `.specify/extensions/**` and `.specify/governance/**` from write.
3. **Write the Shield rules** for `commit_and_open_pr`, `request_pr_review` and `task`. Deny-by-
   default means an unwritten file is a closed door rather than an open one, so the agent does
   nothing at all until this exists.
4. **Specify the indexing job.** Trigger, incrementality, where it runs, which credential it holds,
   what it publishes, and what the ML-BOM contains. [§5](#5-the-indexing-lifecycle) is its shape;
   none of it is written.
5. **Decide the cold-start behaviour.** Failure, degraded mode, or silence — and if degraded, what
   reports the degradation.
6. **Move the trusted issuer list into a file** and give the environment override a loud log line.
   It is the smallest item here and it closes the sharpest disagreement with `NON-FR-CORE-0001`.
7. **Put the governance evaluation in CI**, outside the sandbox, on the pull request. There is no
   `.github/workflows` in this repository today, so this is a directory that has to exist before the
   check can.
8. **Bound the unbounded.** Interrupt TTL, run timeout, sandbox lifetime, provider rate limits,
   index staleness. [§7](#7-failure-modes-and-what-each-one-actually-costs)'s last paragraph is the
   list, and every item on it is currently infinite by omission.

**And one thing the runtime document should not do.** It should not resolve an assumption by
choosing the convenient reading and moving on. Each of the thirty-one above has a *what breaks if it
is wrong* column for a reason: the cost of a wrong assumption in this shape is not a bug, it is a
section of a document that describes a system nobody built.

---

## What checks any of this

**Nothing, and less than nothing checks the stack report.**

That report is at least a set of readings with citations, so a second person can repeat them. **This
page is a synthesis of those readings**, which is one remove further from evidence: every statement
here is either a restatement of something in the stack report or an inference drawn across two of
them. The thirty-one assumption ids exist because that second category would otherwise be invisible.

**Six of the thirty-one are testable today and three have now been tested; all three hold, and
two of them hold only under a condition they did not state.** `ASM-03` was exercised against a
running Aegra on 2026-09-18 and held, so the first two planes of
[§1](#1-five-planes-not-twelve-components) are no longer a hypothesis with a diagram — the
control plane loads and runs the graphs the execution plane is built from. `ASM-28` was
exercised against a running OpenShell the same day and was **falsified**, then re-run on
2026-09-19 against the `dev` build and **answered**: the filesystem policy blocks writes to the
governance tree, symlinks included, and blocks `truncate(2)` only above a Landlock ABI no stable
release uses. `ASM-11` was answered on 2026-09-19 — one process did serve both models — on
condition that the runtime is Infinity rather than TEI, and that the reranker is not the one
this project had decided on. **The other twenty-eight are exactly as untested as they were**,
and one probe answering does not make the rest more likely; it only removes the one that would
have invalidated the others.

**That `ASM-28` first came back falsified is the most useful thing on this page.** Had it been
run a day later it would have come back clean, and the version floor it now carries — the whole
security constraint — would never have been noticed. A campaign where every probe confirms the
document is a campaign that was not measuring anything.

**And the document has a specific failure mode worth naming, because it is the one a synthesis
invites.** A reader who wants an architecture will find one here: five planes, eleven processes, two
lifecycles, a boundary table and a failure matrix. It reads like a system that exists. **No part of
it has been built, and `open-swe/` still contains 56 paths and zero bytes.** The coherence is real —
it is what the synthesis was for — and coherence is not evidence.

Re-read [`specup-agent-stack.md`](specup-agent-stack.md) before relying on any claim here about a
component. This page is the shape; that page is the working.
