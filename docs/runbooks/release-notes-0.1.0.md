# SpecUP 0.1.0

First release. SpecUP adds the OpenUP governed lifecycle to [GitHub Spec
Kit](https://github.com/github/spec-kit): phases and iterations, a seven-level work breakdown
structure, an executable risk register, bi-directional traceability, and milestone gates that
a machine decides rather than a person asserts.

It exists for one problem. An AI agent asked to implement an ambiguous or unsupported
requirement does not stop — it picks a reading and proceeds, and the result looks governed
from the outside. Everything here is built to make that visible: the filesystem is the
authority, every traceability edge declares how much it is worth, and a gate that cannot find
its evidence fails rather than skipping.

## Install

```bash
specify init --here --integration claude    # if Spec Kit is not already set up

mkdir -p ~/.specify
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user
for f in extension preset workflow bundle; do
  curl -sSL -o ~/.specify/$f-catalogs.yml $BASE/$f-catalogs.yml
done

specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt
```

Registering the catalogs is one time per machine. Spec Kit's `default` catalog holds only
components vendored into the Spec Kit wheel, so every third-party project publishes its own
catalog; registering it is the supported route, not a workaround.

`specify <primitive> catalog add` does the same job per project rather than per machine, and
for three of the four primitives its config *replaces* Spec Kit's built-in catalogs instead
of merging with them. [`catalog/user/README.md`](../../catalog/user/README.md) covers the
difference.

**Do not skip the `pip install`.** Without those packages every validator exits 2, and a
workflow then halts on its setup-fault branch rather than passing a gate it could not
evaluate. That is the designed behaviour, but it is a confusing way to discover a missing
dependency.

Then scaffold:

```bash
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "Your Program"
python3 .specify/extensions/openup/scripts/python/audit.py
```

The audit exits 1 on a fresh scaffold. That is correct — an empty plan is not a valid plan.

## What ships

| Component | Contents |
|---|---|
| `openup` extension | 9 commands, 15 templates, 15 validators, 4 JSON Schemas, 4 lifecycle hooks |
| `openup-governance` preset | 4 append addenda over Spec Kit's core templates, 2 wrap overlays over `/speckit.tasks` and `/speckit.implement` |
| 4 phase workflows | Inception, Elaboration, Construction, Transition — each ends by running its gate as a shell step and branching on the exit code |

62 named checks across nine families, a four-gate milestone model with 23 condition
declarations over 22 distinct implementations, and 14 traceability relations whose inverses are
derived at load time rather than stored.

### Three binding standards

`init_openup.py` seeds three governance documents that bind the agent through the root
`AGENTS.md` and Principle VIII of the constitution addendum:

| Document | Binds | Standard |
|---|---|---|
| `.specify/governance/language-rules.md` | every governed document | ASD-STE100 Simplified Technical English |
| `.specify/governance/coding-rules.md` | every change to code | Railway Oriented Programming, RFC 9457 problem details, cloud-native data patterns |
| `.specify/governance/security-practices.md` | design, code, and the security gate evidence | the rules the security review applies |

These close a gap the structural checks cannot reach. A requirement written in a 40-word
sentence with two readings still registers, still traces, and still passes every check — while
the implementation, the test and the gate each answer a different question. A failure thrown as
an exception carries no type and no id, so it cannot be bound to an acceptance criterion or
counted as evidence.

**They are checked by people, not by code.** See the limitations below.

## What is actually enforced

Three layers, one enforcer. The preset and the extension are prompt-level: they shape what an
agent is told, and an agent can decline. Only a workflow `shell` step's exit code stops
anything.

Every validator obeys the same contract, which is what lets one script serve both an agent
reading JSON and a workflow branching on a number:

| Exit | Meaning |
|---|---|
| `0` | PASS |
| `1` | FAIL — a governance invariant was violated |
| `2` | ERROR — the graph could not be loaded, so nothing was evaluated |

Collapsing `2` into `1` would report a broken setup as a governance failure. Every workflow
branches on the two separately.

Two mechanisms are worth knowing about before you trust a coverage number:

- **`derived` is not self-certifying.** An edge claiming a derivation rule has that rule re-run
  against the filesystem; an edge the rule does not reproduce fails (`TRC-010`). An edge naming
  a rule that is not implemented is reported as unverified and counts as nothing at a gate.
- **`approved` is bound to content.** A signature carries a hash of the endpoints it was given
  for. Editing the artifact voids it (`TRC-013`), and re-approval is deliberate.

The release gate's `traceability_final` scores the share of edges that are independently
verifiable — reproduced by a rule, or approved and still matching. A graph can be 100% covered
and prove very little, and the audit prints that mix every time.

## Requires

- Spec Kit `>=1.0.0,<2.0.0`. Verified against **1.0.6 only**; the floor states what was
  exercised rather than what might work.
- Python `>=3.10`, plus `PyYAML>=6.0`, `jsonschema>=4.18`, `referencing>=0.30`.
- Integration-agnostic. The bundle pins no integration and inherits whichever one the project
  already uses.

## Limitations

Stated plainly, because a tool that overstates its coverage is the thing this one was built to
prevent.

- **The three binding standards are not machine-checked.** A human reviewer is the enforcement,
  and an agent's report that it followed them is `asserted`. Useful parts of all three are
  mechanically decidable — sentence length, the non-approved word table,
  `application/problem+json` on every failure response, the RFC 9457 member set — and a checker
  over that subset is the obvious next increment.
- **Nothing parses a contract document.** `critical_contracts_defined` confirms that a
  registered `CONTRACT-*` artifact's declared source file exists; it never opens it. Microcks
  conformance is deferred.
- **Two of five derivation rules are unimplemented.** `openapi-operation-scan` and
  `evidence-manifest-scan` are declared, reported as unverified, and never counted as evidence.
- **An approval binds content, not a human.** Nothing establishes that a person was involved:
  an agent can run `approve_edge.py --by product-owner` exactly as a human can. Read `approved`
  as "someone took accountability under this name".
- **Gherkin binds but does not run.** Scenarios are parsed and tagged into the graph;
  `acceptance_scenarios_passing` trusts whatever wrote the results file.
- **No CI pipeline and no commit-trailer validation.** The validators are CI-ready by
  construction — JSON out, exit codes — but nothing is authored.
- **`python3` in shell steps.** Windows hosts normally have `python`; adjust the `run:` lines or
  provide a shim.
- **Governance overhead is unmeasured**, and it is the thing most likely to sink the approach.
  Track it from your first Construction iteration.

## Verification

248 tests, 8 skipped without the Spec Kit engine and run against it separately — the pair is
what proves the skips are honest. The suite covers the validators against a good fixture and
one deliberate mutation per invariant, the extension and preset manifests against Spec Kit's
documented schemas, all four workflows against the real workflow engine, the installed
directory layout, and the published catalog against a fresh build of every component.

Release archives are reproducible: fixed member timestamps, sorted entries, normalized
permissions. Rebuilding an unchanged component yields a byte-identical zip, so a rebuild is
distinguishable from a tampered artifact. Every catalog `sha256` is generated from the built
archive and re-verified against the bytes on disk.

## Documentation

| Document | For |
|---|---|
| [`docs/guide/using-specup.md`](../guide/using-specup.md) | The operating manual: every check id, every config key, troubleshooting |
| [`docs/guide/README.md`](../guide/README.md) | Concepts and architecture — what it is and why it is shaped this way |
| [`docs/guide/new-project.md`](../guide/new-project.md) | Greenfield adoption |
| [`docs/guide/existing-project.md`](../guide/existing-project.md) | Brownfield adoption, narrow perimeter first |

MIT licensed.
