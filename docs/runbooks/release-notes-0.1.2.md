# SpecUP 0.1.2

Two claims that 0.1.1 made in prose are now checks. The templates that teach the model were
rewritten to explain themselves. SpecUP governs itself for the first time, and its own audit
fails — the numbers are below, untuned.

**The licence changed.** SpecUP is [Business Source License 1.1](../../LICENSE) from this
release, source-available rather than open source. Read
[Upgrading from 0.1.1](#upgrading-from-011) before installing.

## The licence, first, because it changes what you may do

0.1.0 and 0.1.1 were MIT. **They still are, permanently** — MIT cannot be withdrawn from copies
already distributed, and the `v0.1.1` tag remains a permissively licensed governance engine that
anyone may fork and continue. This release binds 0.1.2 onward only.

The Additional Use Grant permits production use:

| | |
|---|---|
| **Yes** | Govern your own software, at any scale, commercial or not |
| **Yes** | Run agents against repositories you or your organisation control |
| **Yes** | Read, fork, modify and redistribute under these same terms |
| **Yes** | Sell consulting, integration or development services around it |
| **No** | Offer SpecUP's functionality to third parties as a commercial product or service |

Each version becomes MIT four years after it is published, automatically. MIT rather than
Apache-2.0 because BUSL covenant 1 requires a GPL-2.0-compatible Change License and Apache-2.0
is compatible only from GPL-3.0 — naming it would have breached the covenant that grants the
right to use the BUSL text at all.

**What it costs, stated rather than omitted:** Spec Kit's community catalogs require *"an open
source license file (MIT, Apache 2.0, etc.)"*, so SpecUP is no longer eligible to be listed in
them. Those catalogs are `install_allowed: false` and every install already goes through
SpecUP's own catalog, so installation is unaffected and discovery is what is lost. The three
submissions filed from 0.1.0 still describe an MIT release and have not been edited, because
they are the record of what was filed.

Full position, including what checks any of it: [`docs/dev/licensing.md`](../dev/licensing.md).

## Human approval is now mechanical — `APV-000` to `APV-005`

0.1.1's README said the only real anchor for an approval was a signed commit verified against
git, *"which is not implemented"*. It is now.

An approval acquires a provenance level, the same way an edge already had one:

| Level | Meaning |
|---|---|
| `witnessed` | `approval.commit` resolves **and** its signature verifies against the project's allowed signers |
| `claimed` | a name and a date, and nothing tying them to a person |

The trust root is `.specify/governance/allowed-signers`, a version-controlled project artifact
in `gpg.ssh.allowedSignersFile` format — reviewable, diffable, and a governance change when it
changes.

`APV-004` **warns** rather than fails on an approval with no commit, because that is a data
migration and not a defect: approvals written before this release cannot have the field. It
ratchets through `approvals.require_witness_at_or_above`, which ships unset.

Signature verification is tested against a real signed commit in a temporary repository, and a
real unsigned one. A mocked signature would have tested nothing.

## The docstring contract — `DOC-000` to `DOC-006`

A docstring is the complete working context for the unit it documents, and nothing more — the
code-level form of the progressive disclosure the whole model rests on.

`DOC-002` requires an exported symbol's docstring to name a governing artifact that resolves.
`DOC-006` bounds length and warns rather than fails, because a long docstring is a smell and a
hard failure would push people to delete reasoning rather than move it to an ADR.

Python only, via `ast`. Non-Python perimeter files are counted and reported `SKIP`, never
passed.

**`DOC-002` found three defects in SpecUP's own code on its first run** — three docstrings
naming an example requirement id that resolves to nothing.

## Every template now explains itself

Each shipped template carries a five-slot frame: what question it answers and what it does not,
how you can tell it has been filled in badly, what checks it *(and if nothing does, it says
so)*, a worked example with the reasoning intact, and where authority sits.

The worked examples come from a real project with a real normative corpus, and the most useful
one is a failure: a truth table was transcribed from a reading of a rule rather than from the
rule, and the predicate written to cross-check it was derived from the same misreading. **They
agreed, and both were wrong.** That is the independent-oracle pattern the ADR template now
carries and `DOC-005` checks — a docstring claiming corroboration must name two distinct
sources, and it is one of the two DOC checks that fail unconditionally.

## A worked example that fails its next gate

[`examples/`](../../examples/) ships a governed program that **passes `GATE-LIFECYCLE_OBJECTIVES`
and fails `GATE-LIFECYCLE_ARCHITECTURE` on five conditions** — the state a real program is in on
its first day.

Every one of those five has a one-minute repair that turns the gate green and the record false,
and `examples/README.md` names each one. A template that shipped green would teach that the
gates are decorative.

## SpecUP governs itself, and the audit fails

`.specify/` held three cache directories. It now holds SpecUP's own governance tree, built by
following [`docs/guide/existing-project.md`](../guide/existing-project.md) end to end — the
first execution of that guide rather than a reading of it.

```
Phase CONSTRUCTION  →  GATE-INITIAL_OPERATIONAL_CAPABILITY   FAIL, exit 1
  forward 100%   backward 100%   verification 95%
  78 edges: 13 derived (17%), 65 asserted (83%), 0 approved
```

**The number that matters is not the coverage.** Backward coverage is 100% over a 17-file
perimeter its author chose. Beside it: 83% of the graph is assertion nothing can confirm.
SpecUP's own `test-file-naming-convention` rule reproduces exactly one of its edges, because it
names test files after the behaviour under test rather than after the module. `RISK-0003`
records that.

Two gate conditions fail and neither is being repaired:

- `acceptance_scenarios_passing` — there are no `.feature` files. Writing
  `acceptance-results.json` by hand would satisfy the condition with a document nothing
  produced, and that file is the one thing in the model nothing can distinguish from a real
  record.
- `NON-FR-DOCS-0001` — "the manual matches the code" is registered with no verifier, so
  verification coverage reports 95% instead of 100%. Deleting the requirement would buy the
  missing 5% and lose the obligation.

**Running the tool on itself found eight defects**, four of them fixed in the engine. The full
list is in [`.specify/traceability/index.md`](../../.specify/traceability/index.md); the one
worth repeating is that a risk accepted by a human is an approval under `acceptance_approval`,
and no `APV-*` check collected it — the single approval in this repository was the one nothing
verified.

## Install

```bash
mkdir -p ~/.specify
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user
for f in extension preset workflow bundle; do
  curl -sSL -o ~/.specify/$f-catalogs.yml $BASE/$f-catalogs.yml
done

specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "Your Program"
python3 .specify/extensions/openup/scripts/python/audit.py
```

The audit exits 1 on a fresh scaffold. That is correct — an empty plan is not a valid plan.

## Upgrading from 0.1.1

**Read the licence before you run this.** Upgrading moves you from MIT to BUSL-1.1 for 0.1.2
onward. If your use is internal — governing your own software, running agents on your own
repositories — nothing about your situation changes. If you are offering SpecUP's functionality
to third parties commercially, staying on 0.1.1 keeps you under MIT, permanently and legitimately.

```bash
specify bundle remove specup && specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt
```

Nothing in `.specify/` changes shape and no governed artifact is touched. Two new validators
appear; both are additive and neither fails a project that has not adopted them:

- `validate_approvals.py` reports every existing approval as `claimed`, which is accurate, and
  `APV-004` warns rather than fails.
- `validate_docs.py` ships `docs.enforce: []`, so `DOC-001`, `DOC-003` and `DOC-004` warn until
  you promote them. `DOC-002` and `DOC-005` fail unconditionally and are **not** listable in
  that ratchet — a dangling id and a false cross-check claim are misleading rather than missing,
  and the guide's rule is that a missing thing warns while a misleading thing fails. `DOC-006`
  is refused from the ratchet outright: failing on docstring length would make deleting the
  reasoning the cheapest way to go green.

`audit.py` gained two sections, so its output is longer and its exit code rules are unchanged.

## What ships

| Component | Version | Changed |
|---|---|---|
| `openup` extension | 0.1.2 | `validate_approvals.py`, `validate_docs.py`, every template rewritten, `__pycache__` excluded from the default perimeter, licence field |
| `openup-governance` preset | 0.1.2 | `constitution-addendum.md` gains the meta-cognitive frame; licence field |
| `specup` bundle | 0.1.2 | pins the above and the four workflows; licence field |
| `openup-inception` | 0.1.1 | licence field |
| `openup-elaboration` | 0.1.1 | licence field |
| `openup-construction` | 0.1.1 | licence field |
| `openup-transition` | 0.1.1 | licence field |

**The four workflows change digest for the first time since 0.1.0.** 0.1.1 was able to state
that they rebuilt byte-identically and republish 0.1.0's assets; that is no longer true. Each
`workflow.yml` carries a `license:` field and all four moved, so all four are rebuilt and
re-versioned. No step, gate or condition changed in any of them.

## Checks

**69 named checks plus `GATE-000`**, up from 56 plus `GATE-000` at 0.1.1. Thirteen added, none
removed, none renumbered.

| Family | Checks | |
|---|---|---|
| `WBS-` | 12 | |
| `RISK-` | 8 | |
| `TRC-` | 14 | |
| `DOR-` | 9 | |
| `DOD-` | 6 | |
| `CTX-` | 4 | |
| `INIT-` | 3 | |
| `APV-` | **6** | new |
| `DOC-` | **7** | new |

Every id in [`docs/guide/using-specup.md`](../guide/using-specup.md) §6 was checked against the
code in both directions for this release: 70 in the manual, 70 in the code, no difference either
way.

## Also corrected

- **`CTX-002` globbed every `index.md` under the project root**, so a governed tree nested
  inside another — `examples/`, `tests/fixtures/` — reported dangling ids from a graph the run
  never loads. It now skips a directory carrying its own `.specify/`.
- **`perimeter_files()` walks the working tree rather than git's index**, so every `.pyc` under
  `__pycache__/` counted as an in-perimeter source file. Added to the shipped default excludes.
- **Both YAML examples in the brownfield guide were invalid** — wrong top-level key, `state` for
  `status`, and a risk-acceptance shape the schema rejects outright. Both corrected, with a note
  that the risk register *is* schema-validated and the artifact registry is not.
- **`approve_edge.py` still described the signed-commit binding as unimplemented** after this
  release implemented it. The README bullet had been rewritten and the docstring had not.
- **`E2E-` was reserved in the id grammar but not modelled.** Now modelled.
- **`workspace/` is committed as an empty folder**, never its contents.

## Unchanged, and worth restating

Extensions and presets are prompt-level: they change what an agent is told, and an agent can
decline. Only a workflow `shell` step's exit code halts a run, which is why the four phase
workflows carry the gates.

An approval binds content, not a human. A verified signature proves the bytes have not changed
since approval and that the signer is in `allowed-signers`; it does not prove the signer read
anything. `APV-002` narrows the gap that 0.1.1 left entirely open, and does not close it.

Nothing here parses a contract document, and no check reads a binding standard. The three
documents under `.specify/governance/` are enforced by a human reviewer, which is why each one
says so.

## Verified

- **407 tests** — 399 passed and 8 skipped without spec-kit importable; 407 passed with it. The
  eight skip rather than fake, and running only one of the two suites proves less than it looks.
- Signature verification exercised against a real signed commit and a real unsigned one.
- The worked example evaluated at both gates, and pinned to the exact set of conditions it fails.
- SpecUP's own audit run and its numbers recorded rather than tuned.
- Every check id cross-checked against the manual in both directions.
