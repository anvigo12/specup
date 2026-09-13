# Adopting SpecUP in an existing project

**Audience:** someone adding governance to a codebase that already exists.

This is the harder adoption, and it fails in a specific, predictable way if you approach it
like a new project. In a greenfield repo the graph grows with the code. Here the code exists
and the intent behind it has to be **recovered** — often from people who have left, decisions
nobody wrote down, and modules whose reason for existing is genuinely lost.

The honest starting position: most of your initial graph will be `asserted`, much of your code
will be outside the perimeter, and your first audit will fail. All three are correct. An
existing project that reports 100% coverage on day one has not been governed; it has been
decorated.

← [back to the guide](README.md) · [new project →](new-project.md)

---

## The strategy: a beachhead, not a big bang

**Do not attempt to retrofit the whole repository.** It is the single most common way this goes
wrong. Retrofitting a mature codebase in one pass produces thousands of fabricated traceability
edges — because the only way to produce them at that volume is for an agent to invent them —
and a graph of invented edges is worse than no graph. It carries the authority of governance
with none of the substance, and nobody can tell which edges are real.

Instead: govern **new and actively-changing work**, and let coverage grow as the code turns
over. A perimeter of one actively-developed service that is genuinely traced beats whole-repo
coverage that is fiction.

---

## Phase 0 — Assess before installing

Answer these first. If the answers are bad, the adoption is not ready and installing will not
help.

| Question | Why it decides the approach |
|---|---|
| Which parts of the codebase actually change? | That is your perimeter. Frozen code should stay outside it. |
| Do requirements exist anywhere? (issues, Confluence, specs) | Determines whether you are recovering or authoring intent |
| Is there a test suite with meaningful coverage? | Tests are the cheapest source of `derived` edges |
| Are there existing ADRs? | Architecture baseline is the most expensive gate condition to satisfy from nothing |
| Who will own the risk register? | If nobody, do not create one |
| Are there real contracts (OpenAPI/AsyncAPI)? | Satisfies `critical_contracts_defined` — which only checks the file exists, not that it is valid |

A useful shape of the answer: "The `payments` service is under active development, has an
OpenAPI spec and 70% test coverage, and the team lead will own risks." That is a beachhead.

---

## Phase 1 — Install, and change nothing else

```bash
cd existing-repo
specify init --here --integration claude    # if Spec Kit is not already set up
python3 /path/to/specup/bundles/specup/install.py --project .
python3 -m pip install -r .specify/extensions/openup/requirements.txt
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "Existing System"
```

`specify init --here` on a populated repo is additive — it creates `.specify/` and agent
command files. Commit before and after so the diff is reviewable.

`init_openup.py` never overwrites an existing file, so it is safe on a repo that already has
a `.specify/`.

```bash
git add -A && git commit -m "Add SpecUP governance scaffolding (no behaviour change)"
```

### The three standards arrive now, and apply forward only

That commit brings in `.specify/governance/language-rules.md`, `coding-rules.md` and
`security-practices.md`. They bind the agent through the root `AGENTS.md` and Principle VIII
of the constitution, so from here an agent writing a new requirement or a new failure path is
held to them.

**They are not a backlog.** Nothing in an existing codebase becomes non-conformant by
installing SpecUP, and rewriting existing prose into Simplified Technical English or
converting a working exception-based codebase to `Result` types is not adoption work — it is
a rewrite wearing adoption's clothes, and it is how a governance rollout gets cancelled.

Apply them to what you touch:

- a requirement you write today follows `language-rules.md`;
- a new endpoint declares RFC 9457 failure responses;
- a module you are already rewriting moves to the failure track.

If the gap between the standard and the codebase is large enough to matter, that is a risk —
register it with an owner, and let the mitigation be scheduled work rather than a standing
sense of guilt. Amending a standard to match what you actually do is also legitimate, and is a
change-control decision rather than an edit.

Nothing is enforced yet. Do not run a workflow.

---

## Phase 2 — Set a deliberately narrow perimeter

This is the most consequential decision in the whole adoption.

```yaml
# .specify/extensions/openup/openup-config.yml
traceability:
  perimeter:
    include:
      - "services/payments/**"        # the beachhead, not the repo
    exclude:
      - "**/*.generated.*"
      - "**/__snapshots__/**"
      - "**/node_modules/**"
      - "**/*.test.*"
      - "**/*.spec.*"
      - "**/migrations/**"
      - "**/vendor/**"
```

Then see the actual size of the problem:

```bash
python3 .specify/extensions/openup/scripts/python/validate_trace.py --json | \
  python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)['metrics'], indent=2))"
```

On a populated graph that reports:

```json
{
  "edges": 26,
  "requirements": 2,
  "forward_coverage": 1.0,
  "verification_coverage": 1.0,
  "backward_coverage": 1.0,
  "perimeter_files": 2,
  "orphans": 0,
  "provenance_mix": { "derived": 15, "asserted": 11, "approved": 0 },
  "asserted_share": 0.4231,
  "derived_verified": 10,
  "derived_unverified": 5,
  "acceptance_criteria": 2,
  "scenario_coverage": 1.0
}
```

Before you have added any edges it reports only `{"edges": 0}` — the check short-circuits on an
empty graph rather than computing coverage over nothing. That is expected on day one; the
number to watch first is `perimeter_files`.

If `perimeter_files` runs to hundreds and `orphans` matches it, the perimeter is still too
wide. Narrow it to one module and repeat until the orphan list is something a person could
actually work through.

`derived_verified` is the number to keep honest — not `asserted_share`, which can be moved by
relabelling. It counts only edges a rule re-derived from the filesystem this run, so it cannot
be improved except by making the repo more legible: naming test files after their subject,
tagging scenarios, filling in `iteration:`. It will start at 0 and should climb.

Watch `derived_unverified` too. It counts edges claiming a rule that does not exist yet, which
look like evidence in a coverage report and are not. On a brownfield graph that number should
stay at 0 — if it is climbing, something is labelling assertions `derived`.

### Lower the coverage thresholds — as a recorded decision

```yaml
  coverage_thresholds:
    forward: 1.00
    backward: 0.30    # ADOPTION: raise by 0.10 per quarter; target 0.95 by <date>
```

This is the one legitimate case for lowering a threshold, and it is legitimate **only** with
the target and the ratchet written next to it. A lowered threshold with no plan to raise it is
permanent, and everyone stops looking at it.

---

## Phase 3 — Recover intent, starting from what exists

You are reconstructing a graph. Take the cheap, verifiable edges first.

### 3a. Requirements from what you already have

Do not invent requirements to cover existing code. Take them from real artifacts — issue
trackers, existing specs, API documentation, compliance obligations — and register only the
ones you can point at a source for.

```yaml
requirements:
  - id: REQ-PAY-0001
    title: Idempotent payment capture
    owner: payments-team
    state: APPROVED          # it is already built and in production
    source: "JIRA PAY-4471"
    acceptance:
      - id: AC-PAY-0001-0001
        statement: Replaying a capture with the same idempotency key returns the original result
```

For behaviour that demonstrably exists but has no recorded intent, that absence is itself a
finding worth writing down. Register the requirement with `source: "recovered from
implementation"` so a reader can tell reconstructed intent from original intent.

### 3b. Start with derived edges, because they are free and true

The cheapest real edges come from the filesystem, not from judgement. Three rules are
implemented, and on a brownfield repo two of them usually pay immediately:

| Rule | What it needs from you | Typical brownfield yield |
|---|---|---|
| `test-file-naming-convention` | register each test file as a `UNIT-*`/`TC-*`/`INTG-*` artifact with `source:` | high — an existing suite is already named this way |
| `wbs-iteration-field` | put `iteration:` on WBS nodes | free, once the skeleton exists |
| `gherkin-tag-scan` | `@SCEN-`/`@AC-` tags in `.feature` files | low at first — most brownfield repos have no tagged features |

```bash
python3 .specify/extensions/openup/scripts/python/derive_edges.py --write
python3 .specify/extensions/openup/scripts/python/validate_trace.py --json
```

Every edge a rule can recompute is one you never have to defend in a review.

**Source → contract and evidence → task are not implemented.** `openapi-operation-scan`,
`openapi-operation-scan` and `evidence-manifest-scan` are declared but have no code behind them,
so an edge naming one cannot be reproduced and is reported as `derived_unverified` rather than
counted as evidence. Write those links as `asserted` instead; the label is accurate, and a
false `derived` costs you the audit's only real signal.

### 3c. Then asserted edges, honestly labelled

The `implements` edges — this module implements that requirement — are judgement, and they are
`asserted`. That is the correct label. Do not promote them to `derived` because the audit looks
better; provenance is the only thing separating evidence from claim.

```yaml
  - from: REQ-PAY-0001
    relation: implements       # stored once, active voice; the inverse is derived
    to: services/payments/capture.py
    provenance: asserted
```

Promote to `approved` only after a named human has actually reviewed the link. The approval is
hash-bound to the endpoints, so editing either end downgrades it rather than silently keeping
the sign-off.

---

## Phase 4 — Build the WBS downward from where you are

Do not reconstruct historical work as WBS nodes. The WBS describes work **to be done**, not
work already shipped. Archaeology produces a tree nobody uses.

Build L1–L3 to reflect the present:

```yaml
nodes:
  - id: WBS-1
    name: Existing System
    level: 1
    phase: CONSTRUCTION          # you are joining mid-lifecycle, not at Inception
  - id: WBS-1.1
    name: Construction
    level: 2
    parent: WBS-1
  - id: WBS-1.1.1
    name: ITER-C-01
    level: 3
    parent: WBS-1.1
```

Then add L4–L7 only for work actually planned. Under `semantic` depth policy a branch may stop
above L7 when it declares a `terminal_reason`, which is exactly right for areas you are
tracking but not currently developing:

```yaml
  - id: WBS-1.1.1.2
    name: Legacy settlement engine
    level: 4
    parent: WBS-1.1.1
    terminal_reason: "In maintenance; no planned work. Outside the traceability perimeter."
```

That records a deliberate decision rather than leaving a gap that looks like an oversight.

### Set the phase honestly

```yaml
lifecycle:
  phase: CONSTRUCTION
  iteration: ITER-C-01
```

An existing system in production is not in Inception. Claiming otherwise means you will run
the Inception workflow and hold `GATE-LIFECYCLE_OBJECTIVES` against a system that passed that
milestone years ago, in silence.

---

## Phase 5 — Risks, only if someone owns them

Register risks that are **live now** — the ones that already worry you in planning meetings.
Do not backfill historical risks that were resolved.

```yaml
- id: RISK-0001
  title: Settlement engine has no integration tests
  probability: 0.7
  impact: 0.8               # exposure 0.56, above the 0.40 threshold
  status: identified
  owner: payments-team
  phase_identified: CONSTRUCTION
```

Anything at or above the threshold needs a mitigation WBS node and a verification reference
before the Elaboration gate would pass — which is the register doing its job: it converts a
worry into scheduled work or an explicit acceptance.

If a risk is genuinely accepted, say so with an approval rather than leaving it `identified`
forever:

```yaml
  status: accepted
  acceptance_approval:
    approved_by: "Head of Engineering"
    date: 2026-09-12
    rationale: "Rewrite scheduled Q2; interim manual verification in place."
```

---

## Phase 6 — Turn on enforcement, last

Only now:

```bash
python3 .specify/extensions/openup/scripts/python/audit.py
```

It will fail. Read *which* conditions fail and decide, one at a time:

| Verdict | Action |
|---|---|
| A real gap | Schedule it. That is the adoption working. |
| A condition that does not apply to a brownfield system | Remove it from `openup-config.yml`, with a comment saying why |
| A threshold unreachable this quarter | Lower it **with a written ratchet and target date** |

Then adopt the workflow for the phase you are actually in — usually Construction:

```bash
specify workflow run openup-construction
```

From here, new work is governed. Existing code joins the graph as it is touched.

---

## A realistic timeline

| Point | Where you should be |
|---|---|
| Week 1 | Installed, scaffolded, perimeter set to one module. Nothing enforced. |
| Weeks 2–4 | Requirements recovered for the beachhead. Derived edges landed. Audit runs and fails legibly. |
| Month 2 | WBS L1–L3 reflects reality. Risks registered and owned. Construction workflow in use for new work. |
| Month 3 | Backward coverage ratchets up. Provenance mix shifts toward `derived`. |
| Months 4–6 | Perimeter widens to a second module. Repeat. |

If you are not through Phase 2 in a fortnight, the perimeter is too wide.

---

## Failure modes specific to brownfield adoption

**Retrofitting everything at once.** Produces thousands of fabricated edges. Covered above; it
is the main one.

**Asking an agent to "generate the traceability matrix" for existing code.** It will produce a
complete, plausible, entirely `asserted` graph in minutes. It will look like success. It is the
exact circularity SpecUP's provenance model exists to expose. Labelling that output `derived`
to make it look checkable now fails `TRC-010` — but the graph underneath is still fabricated,
and no validator can tell you that an `asserted` edge is wrong. The tooling protects the label,
not your judgement about what to trace.

**Setting `phase: INCEPTION` on a system in production.** You will hold the wrong gate and
learn nothing.

**Lowering thresholds without a ratchet.** Becomes permanent within a month, then invisible.

**Governing frozen code.** A module nobody touches gains nothing from being traced, and every
file in it counts against backward coverage. Exclude it and say why.

**Installing the preset without the extension.** Its guidance references validators that would
not be there — every check named, none running. The bundle exists precisely to make that
impossible; install through it.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Thousands of orphans on first run | Perimeter is the whole repo | Narrow to one module |
| Backward coverage stuck near 0 | Edges are missing, not wrong | Land `derived` edges from tests and contracts first |
| Audit is ~100% `asserted` | The graph was generated rather than recovered | Treat as unverified; re-derive what is derivable |
| `wbs_levels_1_to_3_valid` fails | Skeleton is incomplete or a level disagrees with its id | The dotted id is the truth; fix the `level` field |
| `architecture_baselined` fails, no ADRs exist | Nothing to baseline | Write the two or three ADRs that describe the system as it is |
| Gate fails on a condition that cannot apply | Brownfield mismatch | Remove the condition from config with a comment — do not fake evidence |
| Every validator exits `2` | Python dependencies missing | `pip install -r .specify/extensions/openup/requirements.txt` |
| `TRC-010` fails | An edge claims a rule that does not reproduce it | Fix the claim, not the label — usually the edge should be `asserted` |
| `TRC-011` fails | The derived store is behind the filesystem | `python3 .specify/extensions/openup/scripts/python/derive_edges.py --write` |
| `TRC-012` fails on recovered criteria | Brownfield ACs rarely have scenarios yet | Write them, or set `gherkin.require_scenario_per_ac: false` with a target date beside it |
