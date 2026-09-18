# Testing the agent-shape assumptions

**Audience:** whoever runs these probes, and whoever reads the results afterwards to decide
whether `docs/research/specup-agent-runtime.md` can be written.

**Status: one of eight probes has been run.** `P1` was answered on 2026-09-18 and it held. The
other seven *Result* blocks are empty, and an empty block means *not run* — never *assumed fine*.
Run `python3 docs/implement/probes/record.py --list` rather than trusting this line; it reads the
blocks below and this sentence does not.

## Why this exists

[`../research/specup-agent-shape.md`](../research/specup-agent-shape.md) (`EVID-0009`) describes
the 0.1.3 runtime as one system: five planes, eleven processes, two lifecycles, five trust
boundaries, a failure matrix. **It rests on 31 numbered assumptions and none of them has been
tested.** Thirteen are carried from [`../research/specup-agent-stack.md`](../research/specup-agent-stack.md)'s
own *Inferred* markers. **Eighteen were invented by the synthesis** to make the runtime cohere at
all, and nothing upstream states any of them.

`docs/research/specup-agent-runtime.md` has to specify that system precisely enough to build
from. Writing it on 31 untested assumptions would produce exactly the defect this project exists
to prevent — a specification that looks like governance and checks nothing. **This campaign is
what earns the right to write it.**

---

## 1. Three kinds of claim, and only one of them can be tested

**"Test all 31 assumptions" is not a coherent goal**, and saying so is the first useful thing
this document does. The register mixes three kinds of statement, and running an experiment on the
wrong kind is a category error rather than a hard job:

| Track | What it is | Count | How it is settled |
|---|---|---|---|
| **A — Probe** | An empirical question with a yes/no answer | **9** | Stand something up, observe, record what was found |
| **B — Build** | A design intention. True because you build it that way | **6** | Nothing to test. It stays **Specified**, and the runtime document says so |
| **C — Decide** | A scope declaration or a statement of intent | **16** | An ADR. There is no experiment that settles "single tenant" |

**One assumption is observed by a probe and settled by a decision, and it is worth naming rather
than rounding.** `ASM-30` — *an interrupt waits indefinitely* — has an empirical half (**does** the
software impose a TTL today? P8 answers it) and a decision half (**should** this deployment impose
one? ADR 8 answers it). It is counted once, under **C**, because an observation about current
behaviour does not settle what the deployment will do. P8 still runs, and ADR 8 consumes what it
finds.

**The gate for the runtime document is Track A complete and Track C ruled.** Track B is confirmed
while building, which is how this project already treats *Specified* against *Verified* — see the
marker contract in [stack §1](../research/specup-agent-stack.md#1-what-open-swe-is-today).

### Every assumption, assigned

| Id | The assumption, in one line | Track | Settled by |
|---|---|---|---|
| `ASM-01` | `agent/` holds SpecUP middleware and prompts, not a vendored fork | **C** | ADR 1, after P1 |
| `ASM-02` | `langgraph/aegra/` holds the Aegra deployment; `aegra.json` points at the five graphs | **B** | built |
| `ASM-03` | Open SWE's five graphs run unchanged under Aegra | **A** | **P1** |
| `ASM-04` | Agent Inbox authenticates cleanly against Aegra's JWT or OAuth | **A** | **P3** |
| `ASM-05` | `langfuse/` holds the self-hosted deployment, and the `traced_*` wrappers point at it | **A** | **P7** |
| `ASM-06` | `sandbox/openshell/` holds the policy YAML and the sandbox image definition | **B** | built |
| `ASM-07` | `db/neo4j` holds a code property graph — symbols, files, imports, call edges | **C** | ADR 5 |
| `ASM-08` | One Postgres cluster, two databases, not a shared schema | **A** | **P6** |
| `ASM-09` | One Valkey serves Aegra and Langfuse, separated by database index or key prefix | **A** | **P6** |
| `ASM-10` | ClickHouse exists for Langfuse and nothing else | **C** | ADR 4 |
| `ASM-11` | One model server serves both the embedder and the reranker | **A** | **P5** |
| `ASM-12` | One BPE tokenizer is shared by every stage rather than one per stage | **B** | built |
| `ASM-13` | `vouch/` holds the Shield rules and the `did:web` document, never the private key | **C** | ADR 6, after P4 |
| `ASM-14` | The graphs execute in Aegra's worker processes, not as a separate service | **A** | **P8** |
| `ASM-15` | One sandbox per run, created at start and destroyed at end | **C** | ADR 2 |
| `ASM-16` | The repository is cloned into the sandbox; the working tree lives there | **C** | ADR 2 |
| `ASM-17` | `vouch-bridge` is a per-host sidecar on a socket the sandbox cannot read the key from | **A** | **P4** |
| `ASM-18` | The indexing job runs outside the sandbox, as an admin process in the same package | **C** | ADR 3 |
| `ASM-19` | Indexes are pulled read-only at process start and never written at runtime | **B** | built |
| `ASM-20` | `rag/` retrieval runs in the agent process, not in the sandbox and not as a service | **C** | ADR 3 |
| `ASM-21` | The Bolt client runs in the agent process, so graph access is not a sandbox egress concern | **C** | ADR 3 |
| `ASM-22` | OTLP is emitted from the agent process, not from inside the sandbox | **B** | built |
| `ASM-23` | Application logs go to `stdout` and an OTel Collector routes them | **B** | built |
| `ASM-24` | Secrets arrive as environment variables at process start. No secrets manager at 0.1.3 | **C** | ADR 4 |
| `ASM-25` | Single tenant. Aegra's `store.scopes` exists and is not used | **C** | ADR 4 |
| `ASM-26` | All stateful services are single-instance. No HA, no replication, no failover | **C** | ADR 4 |
| `ASM-27` | All five graphs are deployed; nothing prunes `scheduler` or `analyzer` | **C** | ADR 4 |
| `ASM-28` | The governance tree is protected by the OpenShell filesystem policy, not by Shield rules | **A** | **P2** |
| `ASM-29` | One repository per run | **C** | ADR 2 |
| `ASM-30` | An interrupt waits indefinitely. No TTL, no expiry, no escalation | **C** | ADR 8, after P8 |
| `ASM-31` | The Merkle-tree incremental scheme is adopted for the indexing job | **C** | ADR 7 |

---

## 2. The probe protocol

**A probe has three possible outcomes and no fourth.**

| Outcome | Means |
|---|---|
| `answered` | The assumption held under the stated conditions |
| `falsified` | The pre-registered falsifier fired |
| `blocked` | The probe could not be run — a dependency would not install, a version was unavailable. **Never a pass** |

**"Mostly works" is not an outcome.** Neither is "works with a small change" — a small change to
Open SWE's source is precisely what `ASM-03` denies, so that reading is a `falsified`, not a
qualified `answered`.

**The falsifier is written before the probe runs.** Each probe below states what would falsify it,
and that sentence is in this document, in git, with a commit date earlier than the result. A
success criterion written afterwards can always be read as a pass, which is the same defect
`docs/guide/existing-project.md` names when it says an existing project reporting 100% coverage on
day one *"has not been governed; it has been decorated."*

[`probes/record.py`](probes/record.py) enforces both rules mechanically: it refuses an outcome
outside the three, refuses to record against a probe with no falsifier, and refuses to overwrite a
result that has already been written.

**Where things live.**

| What | Where | Tracked |
|---|---|---|
| This document, the falsifiers, the results | `docs/implement/` | **yes** |
| Probe scripts | `docs/implement/probes/` | **yes** — so a second person can repeat the reading |
| Clones, compose files, volumes, model caches | `workspace/spike-0.1.3/<probe>/` | **no** — `workspace/.gitignore` is `*` except itself |

**Nothing is written into `open-swe/`.** A pre-commit hook fails any commit that gives a file
there bytes, and that premise is load-bearing for [stack §1](../research/specup-agent-stack.md#1-what-open-swe-is-today).

---

## 3. The eight probes

### P1 — Do Open SWE's five graphs run unchanged under Aegra?

**Assumption:** `ASM-03`. **This is the load-bearing one.**

**Falsified when:** any of the five graphs needs a change to Open SWE's source to load, or to
complete one run end to end. A change to `aegra.json`, to configuration, or to an environment
variable is *not* a falsifier — those are the files this stack owns.

**Environment:** `workspace/spike-0.1.3/P1/` — Aegra, PostgreSQL, Valkey, an Open SWE checkout.
Python ≥3.12 (this host has 3.13.14).

**Steps:**

1. Clone Aegra and Open SWE into the spike directory. Record both commit SHAs in the result.
2. Bring up Aegra's own compose: `postgres` on `pgvector/pgvector:pg18`, `redis:7-alpine`, and
   `aegra` on uvicorn at `2026`.
3. Write `aegra.json` pointing `graphs` at Open SWE's five entrypoints, taken verbatim from its
   `langgraph.json` — `agent`, `reviewer`, `analyzer`, `chat`, `scheduler`, each a `traced_*`
   wrapper.
4. Confirm the server lists all five assistants over the Agent Protocol.
5. Run **one** thread to completion against the `chat` graph, which changes no code and is
   therefore the cheapest graph that proves the path.
6. Record, per graph, whether it **loaded**; and for `chat`, whether it **completed**.

**What falls if it is falsified:** `agent/` becomes a fork rather than a configuration directory,
so `ASM-01` falls with it and ADR 1 has no question left to answer.
[Stack decision 1](../research/specup-agent-stack.md#121-decisions-taken) — *SpecUP composes this
stack, it does not redistribute it* — changes reach, because vendoring makes Open SWE's MIT
notices a shipping obligation. **Stop the campaign and re-open the shape.**

<!-- RESULT P1 -->
- **Outcome:** answered
- **Date:** 2026-09-18
- **Ran by:** Claude Opus 5, at Aniket Gore's direction
- **Evidence:** workspace/spike-0.1.3/P1/run/logs/ (untracked); reproduce with docs/implement/probes/p1.sh
- **What was found:** open-swe 8aac7c5 and aegra c07ad0d resolve into one Python 3.14.4 environment; Aegra lists all five assistants over the Agent Protocol, all five graphs build (agent/reviewer/analyzer/chat 5 nodes 6 edges, scheduler 3 nodes 2 edges), and one chat thread completed with status success against a stub model. open-swe's tree stayed byte-clean — only aegra.json changed, rewriting Open SWE's module refs as file paths because Aegra resolves a graph reference as a path. Three things the probe was not looking for are in section 3.1 below.
<!-- END RESULT P1 -->

#### 3.1 — What P1 found that it was not looking for

A probe that answers its own question and nothing else has usually been run with the answer
already in mind. These three were not in the falsifier, none of them falsifies `ASM-03`, and all
three change a claim that is currently written down somewhere as settled.

**Open SWE requires Python `>=3.14`, not `>=3.12`.** Its `pyproject.toml` says so, and its
`langgraph.json` declares `"python_version": "3.14"`. The floor the 0.1.3 research carries is
Aegra's `>=3.12`, taken when Aegra was the highest floor in the stack; it no longer is. This host
happened to satisfy it — `/usr/bin/python3` is 3.14.4 — and the campaign's own environment note,
*"Python ≥3.12 (this host has 3.13.14)"*, is a reading of `python3` on a shell where `uv` shims
3.13 ahead of it. **3.13.14 would not have run this probe.** The bundle declares the highest
floor, so `requires-python` for 0.1.3 is `>=3.14`.

**`langgraph-api` is Elastic-2.0, it gets installed, and it gets imported — and none of that is
necessary.** Open SWE declares `langgraph-cli[inmem]` among its *runtime* dependencies, and that
extra pulls `langgraph-api`. Loading the five graphs then imports nine of its modules, because
`langgraph_sdk._async.client` does `try: from langgraph_api.server import app` to build an
in-process loopback transport when one is available. The chain starts in `langgraph-sdk`, which
is MIT — **no Open SWE module imports it directly.** Uninstalling `langgraph-api`,
`langgraph-runtime-inmem` and `langgraph-cli` was tried: all five graphs still loaded, nothing
under `langgraph_api` appeared in `sys.modules`, and a chat run still completed with status
`success`. So [stack §7](../research/specup-agent-stack.md)'s condition — adopt Open SWE
*provided it never depends on `langgraph-api`* — is **satisfiable but not satisfied by default**,
and the thing that satisfies it is a dependency exclusion in the composing project rather than a
patch to Open SWE. That belongs in an ADR, and it belongs in whatever builds the deployment
image, because a transitive install nobody excluded is how the Elastic licence arrives silently.

**`scheduler` is not a `traced_*` wrapper.** [Stack §1](../research/specup-agent-stack.md#1-what-open-swe-is-today)
records that *every* entrypoint in `langgraph.json` is one. Four are;
`scheduler` is `agent.graphs.scheduler:get_scheduler`. It is a small drift, and it is load-bearing
for `ASM-05`/P7: if Langfuse is reached through the `traced_*` wrappers, then on this reading the
scheduler graph is not traced, and P7 must check the scheduler separately rather than assume the
other four generalise.

**One assumption of the campaign's own is corrected too.** P1 step 5 calls `chat` *"the cheapest
graph that proves the path"*. `chat` is a read-only PR agent that expects a GitHub App
installation token, PR context seeded as virtual files, and repo coordinates in `configurable`.
It is cheap only because it **degrades**: with no `thread_id` in the run config it returns
`create_deep_agent(system_prompt="", tools=[])`, a bare agent with no tools. The run that
completed exercised Aegra's dispatch, checkpointing and run lifecycle in full, and exercised
almost none of Open SWE. **P1 answers that the graphs load and the path runs. It does not
establish that any graph does its job**, and section 8 already says no probe does.

#### 3.2 — P1b: what Open SWE's own test suite says

**This is not a probe and it must not be read as one.** It has no pre-registered falsifier, so
there is no sentence in git that it could have failed against, and [`probes/record.py`](probes/record.py)
would refuse it. It is **evidence**, gathered after P1 because P1's weakest claim was that one run
through a stub model tells you almost nothing about Open SWE. Open SWE ships its own suite, and
running it costs no credential and no model call.

Reproduce with [`probes/p1b_open_swe_suite.sh`](probes/p1b_open_swe_suite.sh), which runs it twice,
because the pair is what makes either number mean anything — the same reason `task test` and
`task test:engine` are both in [`docs/dev/taskfile.md`](../dev/taskfile.md).

| Configuration | Result |
|---|---|
| As Open SWE declares itself, PostgreSQL regressions enabled | **3434 passed, 0 skipped, 0 failed** |
| With `langgraph-api`, `langgraph-runtime-inmem` and `langgraph-cli` uninstalled | **3433 passed, 1 failed** |

**The Elastic-2.0 exclusion costs exactly one test, and it is the right one to lose.** The failure
is `tests/agent/test_local_checkpointer.py::test_pickled_dev_server_checkpoints_are_imported_once`.
The **module** under test, `agent/local_checkpointer.py`, is *"SQLite checkpointer for the desktop
app's bundled `langgraph dev` server"* — wired through `langgraph.desktop.json` — and it imports
`aiosqlite` and `langgraph.checkpoint.sqlite.aio`, neither of them Elastic-licensed. It is the
**test body** that imports `langgraph_runtime_inmem.checkpoint.InMemorySaver`, and only to
fabricate the legacy pickles the test then reads back. So what the exclusion breaks is a test of
importing checkpoints *from the dev server*, in a deployment that does not run the dev server.
**That is now the strongest evidence the licence position has**, and it is a build-time exclusion
somebody has to write down rather than a property the composition has for free.

**Two findings about Open SWE itself, neither of which P1 could have produced.**

**All 308 skips were one gate, and it is openable.** Every skip in the default run reports
`TEST_ANALYTICS_POSTGRES_URI is required for PostgreSQL regressions` — not a model key, a
database URI. Pointed at a PostgreSQL, all 308 run and all 308 pass. A suite that reports 3126
passed and 308 skipped is describing its environment, not its health, and the difference here is
308 tests nobody was running.

**One fixture accepts a single PostgreSQL spelling, and the developer documentation hands you a
different one.** Open SWE's `docs/DEVELOPMENT.md` gives `POSTGRES_URI` as
`postgresql://postgres:postgres@127.0.0.1:5433/postgres` and, in the paragraph immediately after,
`TEST_ANALYTICS_POSTGRES_URI` as `postgresql+asyncpg://<user>@localhost:5432/open_swe_test`.
Carrying the first spelling across to the second variable is the obvious move, and
`tests/analytics/conftest.py:26` hands it unmodified to `create_async_engine()`, which selects the
synchronous **psycopg2** dialect — a package in neither Open SWE's `pyproject.toml` nor its
`uv.lock`. **32 of the 169 tests in `tests/analytics` then error with `ModuleNotFoundError: No
module named 'psycopg2'`, and 137 still pass**, because every other fixture routes the same value
through `postgres.uri()`, which rewrites all three spellings by design. `deployment_db` is the
only one that does not.

Fixed upstream in [langchain-ai/open-swe#2969](https://github.com/langchain-ai/open-swe/pull/2969),
which extracts the rewriting into `postgres.normalize_uri()`, calls it from `deployment_db`, and
sets CI to export the bare `postgresql://` scheme so the path stays tested. Measured against
`postgres:16`: **137 passed / 32 errors before, 173 passed / 0 errors after.**

> **Corrected 2026-09-18, and the correction is the point.** This paragraph first said the
> *documented* value could not work, and that all 308 tests turned into errors. Both were wrong.
> `docs/DEVELOPMENT.md:93` and `.github/workflows/ci.yml:68` both name `postgresql+asyncpg://`,
> which works, and the measured split is 137 passed / 32 errors rather than 308 errors. The first
> version was written from the shape of the failure rather than from a re-reading of the source —
> the habit [`AGENTS.md`](../../AGENTS.md) forbids in the words *"re-read before asserting"* — and
> nothing caught it until the fix was written against the file. The defect is narrower than it was
> claimed to be, and it is still a defect.

---

### P2 — Does an OpenShell filesystem policy block a write to the governance tree?

**Assumption:** `ASM-28`. **This is the probe worth keeping**, because it is the only one that is
a governance check rather than a compatibility check.

**Falsified when:** the write succeeds, **or** the policy language cannot express the exclusion at
all. The second is the more likely failure and the more important one: if OpenShell's filesystem
policy cannot exclude a subtree from write while allowing its parent, the protection does not
exist at any layer, because
[stack §13.7](../research/specup-agent-stack.md#137-one-rule-and-the-five-places-it-lands)'s
original answer — Vouch Shield — is already ruled out. Shield's own documentation says path
normalisation *"resolves `..` lexically but cannot see symlinks"*.

**Environment:** `workspace/spike-0.1.3/P2/` — OpenShell installed **on the host**, Docker
present. Independent of P1.

**Steps:**

1. Install OpenShell. **If the install fails, record `blocked` with the error and stop** — the
   assumption is unanswered, not satisfied.
2. Put a copy of a SpecUP-governed tree in the sandbox's working directory, including
   `.specify/extensions/` and `.specify/governance/`.
3. Write a policy that permits write across the tree and denies it under `.specify/extensions/**`
   and `.specify/governance/**`.
4. Create the sandbox and capture the `sandbox.attestation` event, including the policy hash.
5. From inside, attempt four writes: a source file (**must succeed**), a validator under
   `.specify/extensions/` (**must fail**), `.specify/governance/allowed-signers` (**must fail**),
   and the same validator reached through a symlink from a permitted directory (**must fail** —
   this is the case Shield cannot catch and the reason the policy layer is the right one).
6. Alter the policy file after creation and confirm the version disagreement **fails closed**.

**What falls if it is falsified:** the single rule in
[stack §13](../research/specup-agent-stack.md#13-meta-cognition-exploration-and-the-parts-that-must-not-be-explored)
— *an agent may optimise what it does, never what decides whether what it did was good* — has no
enforcement point anywhere in the stack, and the five rows of that section's table become advice.

<!-- RESULT P2 -->
- **Outcome:** _not run_
- **Date:**
- **Ran by:**
- **Evidence:**
- **What was found:**
<!-- END RESULT P2 -->

---

### P3 — Does Agent Inbox authenticate against Aegra?

**Assumption:** `ASM-04`. Flagged as untested in the stack report already: the inbox's connection
form asks for a **LangSmith** API key, and Aegra's own compatibility list names Agent Chat UI,
LangGraph Studio and CopilotKit — **not Agent Inbox**.

**Falsified when:** the inbox accepts only a LangSmith key, or it connects but the interrupt list
does not render, or a `HumanResponse` does not resume the thread.

**Environment:** P1's stack, with Aegra configured for JWT. Needs P1 `answered`.

**Steps:**

1. Configure Aegra with JWT auth. **Never `none`** — see
   [stack §12.3](../research/specup-agent-stack.md#123-the-adopted-answers-and-the-outside-practice-they-rest-on)
   answer 17, and record what the compose file defaults to before you change it.
2. Run a graph that calls `interrupt()` with a well-formed `HumanInterrupt` payload.
3. Point Agent Inbox at the deployment and record what the connection form accepts.
4. Confirm the pending interrupt renders, with its four `HumanInterruptConfig` booleans honoured.
5. Answer with each of `accept`, `edit`, `response`, `ignore` and confirm the thread resumes.

**What falls if it is falsified:** the decision surface is Open SWE's dashboard alone,
[stack §3.3](../research/specup-agent-stack.md#33-agent-inbox--the-explicit-decisions) loses its
premise, and the `agent-inbox/` directory has no intent behind it.

<!-- RESULT P3 -->
- **Outcome:** _not run_
- **Date:**
- **Ran by:**
- **Evidence:**
- **What was found:**
<!-- END RESULT P3 -->

---

### P4 — Can a sandboxed process get a commit signed by a key it cannot read?

**Assumption:** `ASM-17`.

**Falsified when:** the private key has to enter the sandbox, **or** the sidecar's socket cannot
be reached from inside under a policy that denies reading the key.

**Environment:** P2's sandbox plus `vouch-bridge` on the host. Needs P2 `answered`.

**Steps:**

1. Run `vouch-bridge` on the host with a test key that exists nowhere in the repository.
2. Create a sandbox whose filesystem policy denies the key's path and whose network or socket
   policy permits the bridge endpoint and nothing else.
3. From inside, produce a commit and request a signature through the bridge.
4. Verify the signature outside the sandbox, and confirm the `Vouch-DID` trailer is present and
   resolves.
5. From inside, attempt to read the key directly. **This must fail.**

**What falls if it is falsified:** the Identity Sidecar pattern does not hold in this topology,
and the key ends up inside the boundary it is signing about — which is the arrangement Vouch's own
documentation exists to prevent: *"if you give an LLM your private key, it might accidentally leak
it in a prompt injection attack."*

<!-- RESULT P4 -->
- **Outcome:** _not run_
- **Date:**
- **Ran by:**
- **Evidence:**
- **What was found:**
<!-- END RESULT P4 -->

---

### P5 — Does one model server serve both the embedder and the reranker?

**Assumption:** `ASM-11`. Independent of every other probe and the cheapest on this list.

**Falsified when:** two processes are required — because the server cannot host two models at
once, or because it supports embedding but not reranking.

**Environment:** `workspace/spike-0.1.3/P5/` — Text Embeddings Inference or Infinity, and the two
0.6B models. **No GPU required**; CPU inference is slow and sufficient to answer the question.

**Steps:**

1. Fetch both models with `uvx hf download`, pinned to a digest, into `HF_HOME` outside the
   repository — [decisions 3 and 5](../research/specup-agent-stack.md#121-decisions-taken).
2. Start one server process configured with both.
3. Issue an embedding request and a rerank request against the same process.
4. Record the process count, the resident memory, and the wall time for each request over a small
   fixed batch — the serving budget
   [stack §9](../research/specup-agent-stack.md#9-what-the-layout-does-not-have) lists as
   unquantified.

**What falls if it is falsified:** [stack §6](../research/specup-agent-stack.md#6-the-shared-substrate)'s
"one model server" row becomes two processes, and the failure matrix gains a row.

<!-- RESULT P5 -->
- **Outcome:** _not run_
- **Date:**
- **Ran by:**
- **Evidence:**
- **What was found:**
<!-- END RESULT P5 -->

---

### P6 — Two databases on one Postgres, one Valkey for two consumers?

**Assumptions:** `ASM-08` and `ASM-09`.

**Falsified when:** Langfuse's migrations will not run beside Aegra's on one server, **or** the
two key spaces collide in Valkey under default configuration.

**Environment:** P1's stack plus Langfuse. Needs P1 `answered`.

**Steps:**

1. Create two databases on the single Postgres server. Run Aegra's migrations, then Langfuse's.
   Record any error, and record whether either requires a superuser or an extension the other
   does not have.
2. Point both at one Valkey. Exercise a run that queues work and a Langfuse ingest at the same
   time.
3. Dump the key space and check for overlap. Record whether separation came from a database
   index, a key prefix, or nothing at all.

**What falls if it is falsified:** [stack §6](../research/specup-agent-stack.md#6-the-shared-substrate)
understates the operational weight — the stack needs two Postgres servers or two Valkey
instances, and the "five stateful services" count is wrong.

<!-- RESULT P6 -->
- **Outcome:** _not run_
- **Date:**
- **Ran by:**
- **Evidence:**
- **What was found:**
<!-- END RESULT P6 -->

---

### P7 — Do the `traced_*` wrappers reach Langfuse over OTLP?

**Assumption:** `ASM-05`, and with it
[stack §12.3](../research/specup-agent-stack.md#123-the-adopted-answers-and-the-outside-practice-they-rest-on)
answer 11 — OTLP rather than the vendor SDK.

**Falsified when:** spans only arrive through Langfuse's native SDK or a LangChain callback, and
not over OTLP.

**Environment:** P1's stack plus Langfuse, ClickHouse and an S3-compatible store. Needs P1
`answered`.

**Steps:**

1. Stand up Langfuse v3 with its four backing services, including the blob store — *"all incoming
   tracing and evaluation events are persisted in S3/Blob Storage first"*.
2. Configure the OTLP exporter endpoint only. **Do not install the Langfuse SDK**, so a pass
   cannot come from the route this probe is trying to avoid.
3. Run one thread through the `chat` graph.
4. Confirm spans appear, and record whether the `gen_ai` semantic-convention attributes survive
   the trip — the caveat in answer 11 is that **agent** spans are still experimental while
   **client** spans are further along.

**What falls if it is falsified:** [stack §5.2](../research/specup-agent-stack.md#52-opentelemetry-is-not-a-ui-and-you-should-adopt-it-anyway)'s
*keep the seam, swap the implementation* argument does not apply to this stack, and the
observability half becomes a bet on one vendor — which
[stack §7.4](../research/specup-agent-stack.md#74-vendor-concentration) already notes is one owner
for both Langfuse and ClickHouse.

<!-- RESULT P7 -->
- **Outcome:** _not run_
- **Date:**
- **Ran by:**
- **Evidence:**
- **What was found:**
<!-- END RESULT P7 -->

---

### P8 — Where does graph code execute, and does an interrupt expire?

**Assumptions:** `ASM-14`, which this probe settles, and `ASM-30`, which it only **observes** —
what the software does today is not what the deployment will do, and ADR 8 decides that. Rides on
P1's stack and costs almost nothing extra.

**Falsified when:** graphs execute somewhere other than Aegra's worker processes — which would
move Vouch Shield and `rag/` out of the process
[shape §2](../research/specup-agent-shape.md#2-the-processes) puts them in — **or** an interrupt
expires, is garbage-collected, or escalates without anybody configuring it to.

**Environment:** P1's stack. Needs P1 `answered`.

**Steps:**

1. With a run in flight, record the process tree and identify which process holds the graph code.
2. Trigger an `interrupt()` and leave the thread waiting.
3. Record any TTL, sweeper or expiry in Aegra's configuration and in the checkpointer schema.
4. Restart Aegra. Confirm the interrupt survives and the thread still resumes.
5. Record how long the thread was left waiting, so the number quoted later is a measurement rather
   than an assertion.

**What falls if it is falsified:** [shape §2](../research/specup-agent-shape.md#2-the-processes)'s
inside/outside table is wrong throughout, which is the table the containment claim rests on. And
if a TTL exists, ADR 8 is answering a different question from the one it was written for.

<!-- RESULT P8 -->
- **Outcome:** _not run_
- **Date:**
- **Ran by:**
- **Evidence:**
- **What was found:**
<!-- END RESULT P8 -->

---

## 4. The decisions track — eight ADRs for sixteen assumptions

These are **not** probes. Each is a choice that has already been made implicitly by the shape
document and now needs to be made explicitly, with the forces recorded.

| ADR | Settles | Assumptions | Waits on |
|---|---|---|---|
| **1** | `agent/` is configuration, not a fork | `ASM-01` | **P1** |
| **2** | The unit of sandboxed work | `ASM-15` `ASM-16` `ASM-29` | — |
| **3** | What runs inside the boundary and what runs outside | `ASM-18` `ASM-20` `ASM-21` | — |
| **4** | The 0.1.3 deployment envelope | `ASM-10` `ASM-24` `ASM-25` `ASM-26` `ASM-27` | — |
| **5** | What the graph is for | `ASM-07` | — |
| **6** | Key custody | `ASM-13` | **P4** |
| **7** | Index build, provenance and publication | `ASM-31` | — |
| **8** | Interrupt lifetime | `ASM-30` | **P8** |

**These would be the first ADRs this project has written.** `.specify/architecture/` holds two
templates and an index today, which is what
[stack §12.1](../research/specup-agent-stack.md#121-decisions-taken) means when it says ten
rulings and none of them an ADR. Two constraints:

- **The template's *Revisit when* is not optional**, and it is the field these eight are most
  likely to leave empty. Decision 9's whole defect is a revisit nothing schedules; repeating that
  in eight new ADRs would be the same mistake with an id attached.
- **Registering an ADR must not turn the audit's two failures into three.** `TRC-008` counts
  orphan requirements, WBS leaves, high-exposure risks, scenarios, tests and contracts. An ADR
  should fall outside all six — but that is an inference about `validate_trace.py`, and it is
  settled by running `audit.py`, not by reading this sentence.

**ADR 5 deserves a warning.** `ASM-07` is the weakest inference in the whole chain: the stack
report says `db/neo4j` *could equally be agent memory, a requirements ontology, or a dependency
graph*. Nobody can test it, because the question is what it is **for**. An ADR that records a
preference here without recording the alternatives weighed is a note, not a decision.

---

## 5. The build track — six that stay Specified

`ASM-02`, `ASM-06`, `ASM-12`, `ASM-19`, `ASM-22`, `ASM-23`.

These have no experiment and no ruling. They are true when the thing is built that way and false
the moment somebody builds it differently. **The runtime document must carry them as *Specified*
rather than letting them read as findings**, and that is the entire obligation this track creates.

`ASM-19` is worth one extra line, because it looks testable and is not. *Indexes are pulled
read-only at start and never written at runtime* is an assertion about code nobody has written. It
becomes checkable the moment the indexing job exists — a filesystem policy rule, or a mount — and
until then it is an intention.

---

## 6. Sequencing

| Phase | Work | Gate to the next |
|---|---|---|
| **0** | This document, `probes/`, the `docs/README.md` row | Reviewed — **done** |
| **1** | **P1 alone.** P2 and P5 may run beside it | **P1 answered — done, 2026-09-18.** A falsification would have stopped the campaign; it did not fire |
| **2** | P3, P4, P6, P7, P8 | All eight `answered`, `falsified` or `blocked` |
| **3** | Register `EVID-0010`–`EVID-0016` in one batch | `audit.py` reports exactly two reasons |
| **4** | The eight ADRs | Each at `REVIEW` or better; audit still two reasons |
| **5** | `docs/research/specup-agent-runtime.md` | — |

---

## 7. Governance registration

**Seven evidence artifacts, one per probed assumption, registered in one batch** after the probe
wave. The count ripples into six places; doing it seven times is six unnecessary regenerations.

| Artifact | Records | From |
|---|---|---|
| `EVID-0010` | `ASM-03` | P1, and P8's observations, whose stack produced them |
| `EVID-0011` | `ASM-28` | P2 |
| `EVID-0012` | `ASM-04` | P3 |
| `EVID-0013` | `ASM-17` | P4 |
| `EVID-0014` | `ASM-11` | P5 |
| `EVID-0015` | `ASM-08`, `ASM-09` | P6 |
| `EVID-0016` | `ASM-05` | P7 |

Each `evidences` → `WBS-1.1.3`, `provenance: asserted`, following `EVID-0008` and `EVID-0009`.

**One trap, named before anybody is clever about it.** These must **not** be registered as
`derived`. In this project `derived` means a rule in `derivers.py` re-ran and reproduced the edge.
A deriver that cannot reach a running Aegra returns **`derived, unreproduced`** — which
`coverage.md` calls *"not evidence"* in those words, and which is strictly worse than an honest
`asserted` edge. Revisit only if CI can stand the stack up, which today it cannot, because there
is no `.github/workflows` in this repository at all.

**And the results go back into the register.** Each outcome is written into
[`../research/specup-agent-shape.md`](../research/specup-agent-shape.md) §9 in place, so
`EVID-0009` stops describing a set of open questions and starts describing what was found.

---

## 8. What this campaign cannot establish

**It does not test the runtime.** Eight probes over a spike environment answer eight narrow
questions. They say nothing about throughput, concurrency, cost, recovery, upgrade or any
behaviour under load — and the shape document's own failure matrix already admits that every row
in it assumes a process is up or down, with no partial failures modelled at all.

**It does not make Track B true.** Six assumptions come out the far end exactly as they went in.

**It does not make Track C correct.** An ADR records a decision and its forces. It does not make
the decision right, and `ASM-07` in particular is a question about intent that no amount of
rigour converts into a finding.

**And a `blocked` outcome is the one most likely to be misread later.** OpenShell is alpha and is
a host installation rather than a container. If P2 is blocked, `ASM-28` is unanswered — and
`ASM-28` is the assumption carrying the only enforcement point for the one rule the governance
layer has. An unanswered assumption in that position is worse than a falsified one, because
nothing about it looks wrong.

---

## What checks any of this

[`probes/record.py`](probes/record.py) checks three things and they are the three worth checking:
that an outcome is one of the three permitted words, that a falsifier was written before the
result, and that a result is not quietly overwritten. **It does not check whether the probe was
run honestly, whether the environment matched what is described here, or whether the evidence
supports the outcome.** A reviewer does that, and the evidence field exists so there is something
to review.

Nothing checks this document against the shape document. If an assumption is renumbered, split or
retired in `EVID-0009`, the classification table above goes stale silently — the same class of
drift [stack §2](../research/specup-agent-stack.md#2-correcting-the-record) records about the
0.1.2 plan, one document further along.

**And the largest risk in the campaign is not a probe failing.** It is a probe being run, going
badly, and being recorded as `answered` with a caveat. That is why there are three outcomes and no
fourth, and why the falsifiers are in git before the results are.
