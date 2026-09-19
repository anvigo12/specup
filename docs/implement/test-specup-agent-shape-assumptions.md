# Testing the agent-shape assumptions

**Audience:** whoever runs these probes, and whoever reads the results afterwards to decide
whether `docs/research/specup-agent-runtime.md` can be written.

**Status: four of eight probes have been run, and all four are answered — three of them only
under a condition the assumption did not state.** `P1` was answered on 2026-09-18 and it held.

`P2` was **falsified** the same day, then **re-run on 2026-09-19 against OpenShell's rolling
`dev` build and answered**. The difference is a Landlock ABI version: on every stable release,
up to and including `v0.0.116` which `install.sh` gives you by default, a sandboxed process can
still empty `.specify/governance/allowed-signers` with `truncate(2)`. On the `dev` build that
call returns `EACCES`. **Both readings stand**, and the gap between them is now a
minimum-version deployment constraint rather than a defect with no fix.

`P5` was answered on 2026-09-19: one process did serve both the embedder and the reranker, at
one pid and 3337 MiB. It carries two conditions the assumption never mentioned. The runtime must
be **Infinity and not TEI**, which takes one model per process. And the reranker must **not** be
the one this project decided on — `Qwen3-Reranker-0.6B` declares a causal-LM architecture that
the serving runtime cannot type as a reranker, so it either stops the server from starting or
gets loaded as an embedder.

`P4` was answered on 2026-09-19, and it is the sharpest case of the pattern so far: the
**topology** held completely — a key that never left the host signed a commit made inside a
sandbox that could not read a copy of that key sitting in its own filesystem — while the
**component the assumption names does not do the job**. `vouch-bridge` exists, and it is a C2PA
image and audio signing service. There is also no local socket to reach it on, because an
OpenShell sandbox is a container with no mount flag. Nothing shipped fills this role today.

**Three probes have now returned a condition rather than a plain yes**, which is the pattern
worth noticing: the assumptions were not wrong, they were underspecified — and twice the
specific *component* named turned out to be the wrong one while the *shape* survived. The other
four *Result* blocks are empty, and an empty block means *not run* — never *assumed fine*. Run
`python3 docs/implement/probes/record.py --list` rather than trusting this line; it reads the blocks
below and this sentence does not.

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

**Environment:** `workspace/spike-0.1.3/P2/` — OpenShell reachable, Docker present. Independent
of P1. The gateway is a systemd **user** service, so the published tarballs can be verified by
`sha256`, extracted into the spike directory and run unprivileged; a root install is one way to
get a gateway, not the only one.

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
- **Outcome:** answered
- **Date:** 2026-09-19
- **Ran by:** Claude Opus 5, at Aniket Gore's direction
- **Evidence:** workspace/spike-0.1.3/P2/evidence-p2-devbuild.txt and evidence-p2-release-rerun.txt (untracked); p2-allowlist.yaml, p2-subtraction.yaml, p2-allowlist-tampered.yaml alongside them
- **What was found:** HISTORY: falsified 2026-09-18 on v0.0.116; answered 2026-09-19 on the dev build; this block supersedes that same-day 'answered' only to correct one overstatement in its text, and the outcome is unchanged. FINDING: re-run against OpenShell 0.0.117-dev.204+ge38d7254e (commit e38d7254e, the rolling dev release rebuilt 2026-09-18), which builds the ruleset at Landlock ABI::V3. Stated as an allowlist, all three protected writes are denied including through a symlink, and truncate(2) on .specify/governance/allowed-signers returns EACCES with the file unchanged at 2732 bytes - while truncate(2) on a writable path in the same sandbox under the same policy succeeds, which is what makes the denial evidence rather than an artifact. p2.sh exits 0 on this build and 1 on v0.0.116; both runs are in the evidence files, from the same script. THE ANSWER IS CONDITIONAL ON THE BUILD: every stable release to date, up to and including the v0.0.116 that install.sh gives you by default, builds at ABI::V2, and v0.1.0-pre.1 through pre.4 are git tags with no published artifacts. A minimum OpenShell version is therefore a deployment constraint with a security reason. TWO FURTHER OBSERVATIONS, both on the dev build: it no longer logs the ABI at all, so the two lines that diagnosed the original defect are gone and only a behavioural test can tell an operator whether truncation is covered; and a live policy that removes a read_write path is refused with InvalidArgument recording no version, while one that adds a read_write path over a read_only subtree is accepted and reported Effective although the kernel keeps enforcing the original ruleset. Whether v0.0.116 also refused the removal was not tested. See 3.3.
- **Supersedes:** an earlier outcome of `answered`
<!-- END RESULT P2 -->

#### 3.3 — What P2 found, and what the answer is conditional on

**P2 was run twice, against two builds, and got two different outcomes. The difference is a
version number.** On `v0.0.116` — the latest stable release, and what `install.sh` gives you by
default — the falsifier fired. On `0.0.117-dev.204+ge38d7254e`, the rolling `dev` build, the
exclusion holds completely. Both readings are in the record, because both are true of the
software they name, and only one of them is true of anything you can install as a release today.

| | `v0.0.116` (stable) | `0.0.117-dev.204` (`dev`) |
|---|---|---|
| Exclusion by subtraction | every protected write succeeds | every protected write succeeds |
| Exclusion as an allowlist | all three denied, symlink included | all three denied, symlink included |
| `truncate(2)` on the trust root | **SUCCEEDS — 2732 bytes → 0** | **DENIED — `EACCES`, 2732 bytes** |
| Landlock ABI the ruleset is built at | `ABI::V2` | `ABI::V3` |
| `p2.sh` exit code | 1 | 0 |

**The falsifier was written as *"the write succeeds"*, and on the stable release a write
succeeded.** That sentence is in git from `afb6b75`, before any of this ran, which is the only
reason it can settle the question at all. The first result is not withdrawn and
`record.py --supersede` keeps it visible in the block above. What changed is not the reading of
the evidence; it is which build the evidence came from.

**The protection is real, and it is expressed backwards from how anyone would write it.**
A `read_only` entry nested inside a `read_write` parent adds **no restriction whatsoever**. Landlock
grants an access if *any* enclosing hierarchy rule grants it, so a narrower rule can only ever add
rights, never subtract them. Written the obvious way — the whole tree writable, the governance
subtrees carved out — every protected write succeeded while a control path in no list was correctly
denied, proving enforcement was live the whole time. Written as an **allowlist** — enumerate what may
be written, never what may not — the same three writes are denied, **including through a symlink from
a permitted directory**. That symlink case is the one
[stack §13.7](../research/specup-agent-stack.md#137-one-rule-and-the-five-places-it-lands) says Vouch
Shield cannot catch, because Shield normalises `..` lexically and cannot see symlinks. Landlock binds
inodes rather than path strings, so it catches it. **The enforcement point SpecUP wanted does exist.**

**And then the trust root was destroyed anyway.** Appending to
`.specify/governance/allowed-signers` is denied. Calling `truncate(2)` on it **succeeds**, and the
file went from 2732 bytes to 0 — the file `APV-002` verifies signatures against, emptied by the
sandboxed process the policy was written to contain. The cause is exact: `0.0.116` applies Landlock
**`ABI::V2`**, which predates `LANDLOCK_ACCESS_FS_TRUNCATE` (ABI 3), so truncation is not an access
right the ruleset can withhold. The sandbox's own attestation says so in one line —
`CONFIG:PROBED abi:v8` then `CONFIG:APPLYING abi:V2` — the host offered ABI 8 and the policy was built
at 2.

**On the `dev` build the same call is refused.** `truncate(2)` on `allowed-signers` returns
**`EACCES`** and the file stays at 2732 bytes. The control that makes this conclusive is on the
same sandbox under the same policy: `truncate(2)` on `src/app.py`, which the allowlist permits,
**succeeds**. So truncation is not broken in the sandbox — it is withheld on the `read_only`
hierarchy and nowhere else. Withholding it requires `LANDLOCK_ACCESS_FS_TRUNCATE`, which exists
only at ABI 3 and above, so the behaviour establishes the applied ruleset without depending on
anything the log says. That matters more than it should, for the reason below.

> **The answer is conditional on the build, and the condition is a deployment constraint.**
> `main`, `v0.1.0-pre.2` onward and the `dev` build carry `let abi = ABI::V3;` with the comment
> *"Read-only policy must also deny pathname truncation."* No stable release does. `v0.1.0-pre.1`
> through `pre.4` are **git tags with no published release artifacts**, so the only prebuilt
> binary carrying the fix today is the rolling `dev` release — which moves, and therefore has to
> be pinned by commit in any record that cites it. This one is
> `e38d7254e6099a42d6b80329b8e4ef6f0817931f`, rebuilt 2026-09-18.
>
> **SpecUP therefore acquires a minimum OpenShell version with a security reason behind it, and
> that is an ADR, not a note.** Until the fix reaches a stable release, an operator following
> OpenShell's own install instructions gets a build on which the governance exclusion does not
> survive `truncate(2)`.

**Nothing was installed to get this reading, and that was not a compromise.** The release
gateway is a systemd **user** service, not a system one, so the `dev` tarballs were verified
against their published `sha256` sums, extracted under `workspace/spike-0.1.3/P2/dev/`, and run
as the same unprivileged user with `--db-url` pointing into the workspace. No root, no package
manager, no change outside the spike directory, and `systemctl --user start openshell-gateway`
puts `v0.0.116` back. [`probes/README.md`](probes/README.md) says a probe that silently acquires
root to answer a question about containment is a worse problem than the unanswered question;
this is what the alternative looks like when the alternative exists.

**Three further findings, none of which the probe was looking for.**

**The `dev` build no longer says which ABI it applied, and that is a loss.** `v0.0.116` printed
`CONFIG:PROBED abi:v8` and then `CONFIG:APPLYING abi:V2` — two adjacent lines that named the
defect exactly. The `dev` build prints `Isolation boundary attached backend=openshell-sandbox`
and `Isolation boundary enforcement confirmed backend=openshell-sandbox`, and a
case-insensitive search of the whole sandbox log for `abi` or `landlock` returns **nothing**.
The attestation got less specific in the release that fixed the bug the attestation had
diagnosed. An operator can no longer read the log and know whether truncation is covered; the
only way to find out is to try it. **That is the argument for keeping `p2.sh` as a permanent
re-runnable assertion rather than a one-off**, which [§2](#2-the-probe-protocol) already
suspected P2 was uniquely suited to be.

**The attested hash describes the submitted document, not the enforced ruleset — and this did not
change.** **Adding** a `read_write` path that overlaps a `read_only` subtree is **accepted** on
both builds: version 2, new hash, `policy get` reporting `Status: Effective`, `policy list`
marking version 1 `Superseded` with no error. Enforcement does not change — the write stayed
denied and the file stayed at 2732 bytes on both. So the system reports a policy as effective
that the kernel is not enforcing. Read that against the stack report's quotation of OpenShell's
own guarantee — *"current, active, revision, and effective-config versions must all be positive
and agree with the exact submitted policy/hash; ... any version disagreement fails closed."* Here
every version **agrees**, at 2, and the ruleset is still 1's. There is no disagreement to detect,
so nothing fails closed. `policy get` returns a hash and a status and no filesystem lists at all,
so the hash can be compared but never inspected — which is the difference between a record and an
assertion that this project's whole provenance vocabulary rests on.

**The direction that would be dangerous is refused.** A live `policy set` that **removes** a
`read_write` path fails with `InvalidArgument` and a message naming the path — *"filesystem
read_write path '/sandbox/tree/.specify/governance' cannot be removed on a live sandbox"* — and
`policy list` records no phantom version. So a tightening cannot be reported as effective while
the kernel keeps the wider ruleset; only a widening can, and a widening over-promises access the
kernel then refuses. The defect is in what the control plane **says**, not in what it enforces.
Stated precisely, because the distinction is the whole finding: removal was tested only on the
`dev` build, so whether `v0.0.116` also refused it is **untested**.

**Both defaults are still the unsafe ones.** `include_workdir` defaults to **`true`**, which
appends the working directory to `read_write` and silently grants exactly what a governance
exclusion withholds. `landlock.compatibility` defaults to **`best_effort`**. Both still appear
that way in the quickstart example in NVIDIA's own `policies.mdx` at the `dev` commit. One
correction to the falsified run's wording: the `dev` documentation describes `best_effort` as
skipping an **individual** missing path with a warning and applying the remaining rules, rather
than dropping enforcement wholesale — *"In `best_effort` mode, the path is skipped with a warning
and remaining rules are still applied. In `hard_requirement` mode, sandbox startup fails
immediately."* That is a narrower failure than first recorded, and it does not change the
recommendation: set both explicitly, and `hard_requirement` is what makes step 6 mean anything.

**One operational note that cost an hour.** `--upload` runs **after** the policy binds, so a
`hard_requirement` policy naming paths inside an uploaded tree aborts startup before the upload
happens. The governed tree has to be in the image.

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

**Environment:** P2's sandbox plus a signing sidecar on the host. Needs P2 `answered`.

*Corrected 2026-09-19, after the run.* This said *"plus `vouch-bridge` on the host"*. That
component does not sign git objects — see [3.5](#35--what-p4-found-and-the-sidecar-that-does-not-exist) —
so the probe supplies its own sidecar and the assumption's component name is part of what P4
settles rather than part of its setup.

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
- **Outcome:** answered
- **Date:** 2026-09-19
- **Ran by:** Aniket Gore
- **Evidence:** workspace/spike-0.1.3/P4/evidence-p4.txt
- **What was found:** The topology holds, and the component the assumption names does not. A key on the host signed a commit made inside an OpenShell sandbox: the sandbox could not read a copy of that same key sitting in its own filesystem (DENIED under the probe policy, READ under a control policy that lists the parent, so Landlock refused it rather than Unix permissions), it reached the sidecar over the one endpoint the network policy names and got policy_denied on the adjacent port, and the commit verifies outside with ssh-keygen against the public key. But ASM-17 is wrong twice. vouch-bridge is a C2PA image and audio signing service that mints an ephemeral certificate chain per request; it signs no git object and holds no long-lived key. And there is no local socket: an OpenShell sandbox is a container, sandbox create has no mount flag, so a host unix socket is not in its filesystem at all and egress is a transparent L7 proxy. The sidecar and the git shim in this probe are 120 lines written to make the question answerable. No shipped component fills this role today.
<!-- END RESULT P4 -->

#### 3.5 — What P4 found, and the sidecar that does not exist

*The number is the order a finding was written, not its place on the page — so 3.5 sits above
3.4. Renaming a heading here once broke two links in another document, and keeping the numbers
stable is worth more than keeping them sorted.*

**`ASM-17` holds as a topology and fails as a description of a component.** A key that never
left the host signed a commit that was made inside the sandbox:

| Step | Result |
|---|---|
| Private key readable inside, under the probe policy | **DENIED** |
| The same key, under a policy that lists the parent `/sandbox` | **READ** — so Landlock refused it, not Unix permissions |
| Control file in the same sandbox | READ |
| Host unix socket (`/run/user/1000/gcr/ssh`) visible inside | **NO** — `/run/user/1000/` does not exist there |
| Commit produced inside, signed through the sidecar | `fc9524a7…` |
| Endpoint the network policy does not name | `policy_denied` |
| Signature checked outside with `ssh-keygen -Y verify` | **`Good "git" signature for agent@p4.invalid`** |
| `Vouch-DID` trailer vs. the key that signed | identical `did:key:z6Mkosh…` |
| Signatures the sidecar issued | **1** |

**`vouch-bridge` is not the component this assumption thinks it is.** It is real — it installs
from `vouch-protocol` as a console script pointing at `vouch.bridge.server:main` — but its own
FastAPI application describes itself as a *"C2PA image signing, QR badge overlay, and audio
watermarking service"*. Its two endpoints are `sign_image` and `verify_image`, it has a
companion `audio_routes.py`, and it generates an **ephemeral three-level certificate chain per
request**. It signs no git object, and it holds no long-lived key to withhold. So the sentence
in [stack §3.12](../research/specup-agent-stack.md#312-vouch--agent-identity-and-the-broker) —
*"`vouch-bridge` is the local signing daemon that implements it"* — names a real binary for a
job it does not do.

**Worth recording how that was nearly missed in the other direction.** `vouch-bridge` appears in
neither the project README nor the PyPI description, so the first two readings concluded it did
not exist at all and P4 was about to be recorded `blocked` on a missing prerequisite. Installing
the package is what showed the console script. **A component's absence from its own
documentation is not evidence of its absence**, and the reverse error — declaring something
missing because the docs are quiet — would have been just as wrong as the claim it was
correcting.

**There is also no local socket, and there cannot be one.** An OpenShell sandbox is a container,
`openshell sandbox create` has **no mount or volume flag**, and the host's `/run/user/1000/` is
simply not in the sandbox's filesystem. Egress is a transparent L7 proxy: every sandbox gets
`http_proxy=http://10.200.0.1:3128` and an injected CA at `/etc/openshell-tls/`. So a sidecar in
this topology has to be an **HTTP endpoint the proxy can route to**, named in the policy:

```yaml
network_policies:
  sidecar:
    endpoints:
      - { host: 192.168.48.231, port: 21777, protocol: rest, enforcement: enforce, access: full }
    binaries:
      - { path: "/usr/local/bin/p4-bridge-client" }
```

**The containment is real rather than advisory, and that was worth checking.** Unsetting
`http_proxy` and connecting straight to the host does not escape it — the connection fails. The
only host port a sandbox can open is the proxy itself. A policy enforced only by an environment
variable would be no policy at all, because the first thing a misbehaving agent does is ignore
it.

**`binaries` is the control that has no analogue in the shape document.** Egress is attributed
to the executable that requests it, so the signing endpoint can be reachable by the bridge
client and by nothing else in the sandbox. That is a stronger statement than *"the sandbox may
reach the sidecar"*, and the runtime specification should use it.

**What the sandbox does hold is a bearer token, and that is the honest reduction rather than a
loophole.** It is permission to *ask for* a signature while the sandbox runs, not possession of
a key afterwards. Revoking it is restarting the sidecar; a leaked key file is still a key file
tomorrow. The property `ASM-13` actually wants is this one, and it should be written that way.

**One probe-design error, kept because it is the interesting half.** The first run reported the
key `DENIED` and it meant nothing: the decoy was owned by root at mode `0600`, so ordinary Unix
permissions were refusing the read and Landlock was never consulted. The control that caught it
is now step 5b — boot the same image, list the parent `/sandbox`, and the same read must
**succeed**. It does. This is the same failure as the `read: DENIED` that turned out to be a
redirect to an unlisted `/dev/null`, in [3.3](#33--what-p2-found-and-what-the-answer-is-conditional-on),
and it is the reason a denial without a matching permit is not evidence.

**Two things about Vouch that a deployment has to know, neither of them about P4.** The bridge
binds **`0.0.0.0` by default** and `auth_enabled` is `bool(VOUCH_BRIDGE_SECRET)` — so with no
secret set, a signing service listens on every interface with authentication switched off; the
`--help` that discovered this started a live server, because `main()` parses no arguments. And
**`vouch git init` writes `--global` git config** — `user.signingkey`, `gpg.format=ssh`,
`commit.gpgsign=true` — plus a key pair into `~/.ssh/`. On a machine that deliberately has no
global git config, that is not a setup step, it is a change to every repository the operator
owns. This probe configured the equivalent per-repository instead.

**So what has to be built is now specific.** Not *"deploy `vouch-bridge`"*, but: a signing
service that holds one long-lived key, exposes one HTTP endpoint, fixes the signature namespace
rather than taking it from the caller, logs every signature durably, and applies a policy over
*what* it will sign rather than signing whichever bytes arrive. The probe's sidecar does the
first three in 120 lines and deliberately does neither of the last two. **ADR 6 is where that
gets decided**, and it now has a measured topology to decide against rather than an assumption.

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
- **Outcome:** answered
- **Date:** 2026-09-19
- **Ran by:** Claude Opus 5, at Aniket Gore's direction
- **Evidence:** workspace/spike-0.1.3/P5/evidence-p5-mixed-pair.txt (the answering run), evidence-p5.txt and evidence-p5-st5.txt (the two Qwen3-Reranker failures), evidence-p5-versions.txt (all versions) - untracked
- **What was found:** ONE process served both. Infinity 0.0.77 (MIT) loaded Qwen/Qwen3-Embedding-0.6B and a cross-encoder reranker in a single process: /models reported capabilities ['embed'] and ['rerank'] separately, /embeddings returned 1024 dims, /rerank ranked, and the process tree read from /proc was exactly 1 pid at 3337 MiB RSS on CPU float32. Both endpoints were checked for correctness and not just for HTTP 200: two queries retrieved 2/2 correctly by cosine over the embeddings and ranked 2/2 correctly through /rerank. The runtime choice is load-bearing and was read from upstream rather than assumed - TEI's usage line is 'text-embeddings-router [OPTIONS] --model-id <MODEL_ID>', singular and required, so TEI is one model per process and cannot satisfy ASM-11 at all. THE RERANKER THE STACK DECIDED DOES NOT WORK HERE, and that is the finding this probe was not looking for. Qwen/Qwen3-Reranker-0.6B declares architectures ['Qwen3ForCausalLM'], and infinity_emb/inference/select_model.py:47 selects a reranker only when the string 'SequenceClassification' appears in architectures, with no flag to override. On Infinity's own pin (sentence-transformers 3.4.1) the server will not start at all, because the model's modules.json references sentence_transformers.base and cross_encoder.modules.logit_score, which are v5 namespaces. On sentence-transformers 5.7.0 the server starts and loads both models in one process, but registers the reranker with capabilities ['embed'] and /rerank returns HTTP 400 - the pre-registered falsifier's exact wording, 'it supports embedding but not reranking'. A third observation: one unloadable model aborts the whole server, so the healthy embedder does not survive a bad reranker, which is a tighter coupling than the shape document's degradation row assumes. Serving budget, previously unquantified: 3337 MiB for the answering pair, 5321 MiB for two 0.6B Qwen models, 1.70s to embed 8 short texts and 0.08s to rerank 4 documents on 4 AVX2 cores with no usable accelerator. See 3.4.
<!-- END RESULT P5 -->

#### 3.4 — What P5 found, and the reranker that has to be replaced

**`ASM-11` holds. One process serves both.** Infinity 0.0.77 loaded an embedder and a reranker
together, registered them under separate capabilities, answered both endpoints, and read as
exactly one pid in `/proc` — not a supervisor with children, one process.

| | |
|---|---|
| Processes in the server's tree | **1** |
| Resident memory, whole tree | 3337 MiB, CPU `float32` |
| `/models` capabilities | `embed` → `['embed']`, `rerank` → `['rerank']` |
| Embed 8 short texts | 1.70s, 1024 dims |
| Rerank 4 documents | 0.08s |
| Retrieval correct / ranking correct | **2/2 and 2/2** |

**The runtime choice is the answer, not a detail.** Text Embeddings Inference cannot satisfy
`ASM-11` at all: its usage line is `text-embeddings-router [OPTIONS] --model-id <MODEL_ID>`,
singular and required — **one model per process**. Infinity's own help says the opposite in as
many words: *"cli options can be overloaded i.e. `v2 --model-id model/id1 --model-id
model/id2`"*. [Stack §12.1](../research/specup-agent-stack.md#121-decisions-taken) lists TEI,
Infinity, llama.cpp and Ollama as interchangeable permissive options. **For this assumption they
are not interchangeable**, and a deployment that picks TEI has falsified `ASM-11` by
construction.

**And the reranker the stack decided cannot be served at all.**
[Stack §3.6.7](../research/specup-agent-stack.md#367-rerankqwen3-reranker--the-last-18-points)
names `Qwen3-Reranker-0.6B`. It declares `architectures: ["Qwen3ForCausalLM"]`, and Infinity
selects a reranker on exactly one condition, at `infinity_emb/inference/select_model.py:47`:

```python
if any("SequenceClassification" in arch for arch in config.get("architectures", [])):
    return RerankEngine.from_inference_engine(engine_args.engine)
...
return EmbedderEngine.from_inference_engine(engine_args.engine)
```

A causal-LM reranker never matches, and **no flag overrides it** — `--served-model-name` renames
a model, it does not retype it. The failure has two shapes depending on a dependency version,
and neither is a warning:

| `sentence-transformers` | What happens |
|---|---|
| **3.4.1** — Infinity's own pin (`<4.0.0`) | **The server does not start.** `ModuleNotFoundError: No module named 'sentence_transformers.base'`. The model's `modules.json` names `sentence_transformers.base.modules.transformer.Transformer` and `cross_encoder.modules.logit_score.LogitScore`, both **v5** namespaces |
| **5.7.0** — above the pin | Server starts, **one process, both models loaded** — and the reranker registers as `capabilities=['embed']`. `/rerank` returns **HTTP 400** |

The second row is the pre-registered falsifier in its own words: *"it supports embedding but not
reranking."* It did not fire against `ASM-11`, because the assumption is about the **serving
architecture** and the architecture held as soon as the reranker was one Infinity can type. It
fired against the **model pairing**, which is a different claim living in a different document.

> **So stack §3.6.7's decision needs changing, and the replacement is already written there.**
> That section names **`bge-reranker-v2-m3`** (Apache-2.0, `XLMRobertaForSequenceClassification`,
> so it matches the check) as the permissive alternative, and states the cost: a **512-token**
> documented window against Qwen3-Reranker's 32K, *"and for code that difference is not
> academic."* That cost now has to be paid, or the serving runtime has to change. It is a
> decision, so it belongs in an ADR rather than here.

**One further finding the probe was not looking for: the failure is not isolated.** When the
reranker could not load, the **whole server aborted** — `Creating 2 engines: ['embed', 'rerank']`
and then `Application startup failed. Exiting.` The healthy embedder did not survive the broken
reranker. [Shape §7](../research/specup-agent-shape.md) records the model server's failure mode
as *"dense retrieval and reranking stop; BM25 survives"*, which reads as two capabilities
degrading. **One process is one blast radius**, and that is the cost side of the answer this
probe returned: `ASM-11` is true, and it is true because they share a process.

**The serving budget, which [stack §9](../research/specup-agent-stack.md#9-what-the-layout-does-not-have)
lists as unquantified.** On four AVX2 cores with no usable accelerator: **3337 MiB** for the
answering pair and **5321 MiB** for two 0.6B Qwen models, 1.70s to embed eight short texts,
0.08s to rerank four documents. Cold start to ready was 95s for the two Qwen models.

**And a ceiling worth recording before anyone proposes larger models.** Both models must be
resident at once — that is what the assumption *means* — so the pair's cost is the sum:

| Pair, `float32`, both resident | |
|---|---|
| 0.6B + 0.6B | **4.4 GiB** — measured at 5321 MiB with overhead |
| 4B + 4B | 30.0 GiB |
| 8B + 8B | 58.7 GiB |

Against roughly 10 GiB available here, only the first fits, which is the pair stack §3.6 already
chose. Reduced precision does not rescue the others on this class of host: `torch` reports **no
AVX-512 BF16** on this CPU, so `bfloat16` is emulated and slower than `float32`, and 4B+4B is
still 15 GiB at half precision. **A machine with AMX or a GPU should re-measure rather than
inherit these numbers** — they are a floor for the architecture, not a limit of it.

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
| **2** | P3, P6, P7, P8. **P2, P4 and P5 are closed** — P2 falsified 2026-09-18 on `v0.0.116`, re-run 2026-09-19 on the `dev` build and answered, superseded in place; P5 answered 2026-09-19; P4 answered 2026-09-19, the last one that needed nothing from P1. **The four that remain all need P1's stack standing up again**, and P6 and P7 additionally need Langfuse | All eight `answered`, `falsified` or `blocked` |
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

**And a `blocked` outcome is the one most likely to be misread later.** OpenShell is alpha, and
its installer wants root. *(Corrected 2026-09-19: the installer wants root, but OpenShell does
not need it. The gateway is a systemd **user** service, so the published tarballs run unprivileged
from a working directory — which is how P2 was re-run. A `blocked` on packaging grounds should
therefore be argued, not assumed.)* If P2 had stayed blocked, `ASM-28` would be unanswered — and
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
