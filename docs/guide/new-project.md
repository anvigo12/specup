# Adopting SpecUP in a new project

**Audience:** someone starting a greenfield project that should be governed from the first
commit.

This is the easier of the two adoptions: the graph grows alongside the code, so nothing has to
be reconstructed. Expect the first Inception pass to take a day or two of real thinking — most
of that is deciding what you are building and who owns it, which is work you were going to do
anyway, now written somewhere a validator can read.

← [back to the guide](README.md) · [existing project →](existing-project.md)

---

## 0. Prerequisites

| Need | Why |
|---|---|
| Python 3.10+ | The validators |
| `specify` CLI ≥ 1.0.6 | Spec Kit itself |
| A git repo | Every governed artifact is a version-controlled file |

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify --version    # 1.0.6 or later
```

---

## 1. Create the project and install SpecUP

```bash
mkdir my-product && cd my-product && git init
specify init --here --integration claude      # or your agent of choice
```

Then register SpecUP's catalog — one time, per machine — and install the stack:

```bash
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog
specify extension catalog add $BASE/extensions.json --name specup --install-allowed --priority 0
specify preset    catalog add $BASE/presets.json    --name specup --install-allowed --priority 0
specify workflow  catalog add $BASE/workflows.json  --name specup
specify bundle    catalog add $BASE/bundles.json    --policy install-allowed --priority 0

specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt
```

The second line is not optional. Without those packages every validator exits `2`, and your
workflows will halt on the setup-fault branch rather than passing gates they could not
evaluate. Confirm:

```bash
python3 .specify/extensions/openup/scripts/python/audit.py; echo "exit=$?"
```

Exit `1` is correct here — an empty project fails its gate. Exit `2` means the dependencies
are missing.

---

## 2. Scaffold the governance tree

```bash
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "My Product"
```

Creates:

```
.specify/
├── lifecycle/      vision.md, stakeholders.md, index.md
├── governance/     approval records, language-rules.md, coding-rules.md,
│                   security-practices.md
├── architecture/   ADRs and the baseline
├── wbs/wbs.yaml
├── risks/risk-register.yaml
├── traceability/   requirements.yaml, traceability.yaml
└── evidence/
```

It never overwrites an existing file, so it is safe to re-run.

Commit this before writing anything into it. The first diff of a governance file should be
legible as a decision, not lost inside the scaffold.

```bash
git add .specify && git commit -m "Scaffold OpenUP governance"
```

---

## 3. Set the perimeter before you write code

Open `.specify/extensions/openup/openup-config.yml` and set
`traceability.perimeter.include` to where your source will actually live:

```yaml
traceability:
  perimeter:
    include:
      - "src/**"
    exclude:
      - "**/*.generated.*"
      - "**/*.test.*"
```

Doing this now costs a minute. Doing it after three months of code means your first honest
audit reports hundreds of orphans and you will be tempted to widen the exclude list to make
the number go down — which is how a perimeter stops meaning anything.

---

## 4. Inception — establish intent

```bash
specify workflow run openup-inception
```

The workflow drives the agent through vision, stakeholders, the initial risk picture and the
L1–L3 WBS skeleton, then evaluates `GATE-LIFECYCLE_OBJECTIVES`.

What the gate actually checks:

| Condition | Passes when |
|---|---|
| `vision_present` | `.specify/lifecycle/vision.md` exists and is filled in |
| `stakeholders_identified` | Stakeholders are documented |
| `initial_risks_registered` | At least one risk is registered |
| `wbs_levels_1_to_3_valid` | The L1–L3 skeleton is well-formed |
| `requirements_have_owners` | Every requirement names an owner |

Do this part yourself rather than delegating it wholesale. The agent will happily generate a
plausible vision and a stakeholder list, and you will have a gate that passes over fiction. The
commands are there to structure and validate your thinking, not to replace it.

### Write requirements with owners from the start

```yaml
# .specify/traceability/requirements.yaml
requirements:
  - id: REQ-AUTH-0001
    title: Vehicle certificate authentication
    owner: security-team
    state: DRAFT
    acceptance:
      - id: AC-AUTH-0001-0001
        statement: A vehicle presenting a valid certificate chain is authenticated within 200ms
```

`owner` is not bureaucracy — `requirements_have_owners` fails without it, and an unowned
requirement is one nobody will answer questions about in six months.

Requirements enter at `DRAFT`. Promote to `APPROVED` when they have actually been agreed; the
preset instructs agents to refuse to implement a `DRAFT` requirement, which is the point.

---

## 5. Elaboration — architecture and the risks that matter

```bash
specify workflow run openup-elaboration
```

This is where the seven-level WBS gets built out and high-exposure risks get retired.

`GATE-LIFECYCLE_ARCHITECTURE` checks:

| Condition | Passes when |
|---|---|
| `architecture_baselined` | The architecture baseline exists and is approved |
| `all_high_risks_have_mitigation` | Every risk ≥ `high_exposure_threshold` has a mitigation WBS node **and** a verification reference |
| `requirements_traceable` | Requirements reach implementation and verification |
| `critical_contracts_defined` | Interfaces touched have registered contracts |
| `security_review_complete` | A security review record exists |
| `wbs_valid` | All twelve WBS checks pass |

### Risks need real mitigations

```yaml
- id: RISK-0001
  title: Certificate validation latency
  probability: 0.6
  impact: 0.9              # exposure 0.54 -> above the 0.40 threshold
  status: mitigating
  owner: security-team
  mitigation:   [WBS-1.2.3.4.1.1.2]     # a real node scheduled in an iteration
  verification: [TC-AUTH-0031]
```

`mitigation` pointing at prose instead of a WBS node fails. That is deliberate: a mitigation
nobody scheduled is a wish.

Check as you go rather than at the gate:

```bash
python3 .specify/extensions/openup/scripts/python/validate_risk.py --json
python3 .specify/extensions/openup/scripts/python/validate_wbs.py --json
```

---

## 6. Construction — iterate

```bash
specify workflow run openup-construction
```

One iteration per run. The workflow selects ready work risk-first, fans out over it, and holds
`GATE-INITIAL_OPERATIONAL_CAPABILITY` at the end.

The loop, per task:

1. `select_work.py` applies the Definition of Ready and returns the ready set plus each
   blocked task and why.
2. `/speckit.tasks` derives tasks **from the WBS** rather than inventing them. A task not in
   the ready set is not generated; the blocker is reported instead.
3. `/speckit.implement` resolves the task's full governance chain *before* writing code:

   ```
   TASK → WBS node → iteration → phase → requirements → risks
                              → acceptance criteria → architecture → contracts → tests
   ```

   **If any link cannot be resolved, it stops and reports rather than inferring.** This is the
   single most important rule in the preset: an agent that invents the missing requirement
   produces work that looks governed and is not, and the fabricated link is indistinguishable
   from a real one on inspection.

4. After implementing: evidence is recorded, edges are added, and risks are reassessed against
   what the evidence actually showed.

### Keep the provenance honest

Never hand-write a `derived` edge. Generate them:

```bash
python3 .specify/extensions/openup/scripts/python/derive_edges.py --write
python3 .specify/extensions/openup/scripts/python/audit.py
```

The first command rewrites `.specify/traceability/derived.yaml` from the rules. Everything you
write by hand belongs in `traceability.yaml` as `asserted`.

Marking a judgment call `derived` to improve the audit is the failure this model exists to
catch, and it is now caught rather than trusted: `TRC-010` re-runs the rule an edge names and
fails the edge if it does not come back. You cannot improve the ratio by renaming things.

Watch the derived/asserted/approved mix, not just the coverage number — and inside `derived`,
watch `derived_verified` against `derived_unverified`. Early on a new project will be mostly
`asserted`, and that is fine and honest. What matters is the trend: as tests and scenarios come
online, `derived_verified` should grow. `derived_unverified` growing means edges are naming
rules nobody implemented, which is worse than `asserted` because it reads like evidence.

---

## 7. Transition — release

```bash
specify workflow run openup-transition
```

`GATE-PRODUCT_RELEASE` checks that all prior gates passed, release evidence is complete, no
high risks are open, traceability is final, and security validation passed.

---

## Daily working rhythm

Most days you will not run a whole workflow. You will:

```bash
# what can I actually work on right now?
python3 .specify/extensions/openup/scripts/python/select_work.py --json

# pick up what the filesystem changed under you
python3 .specify/extensions/openup/scripts/python/derive_edges.py --write

# is the graph still sound?
python3 .specify/extensions/openup/scripts/python/validate_wbs.py
python3 .specify/extensions/openup/scripts/python/validate_trace.py

# where do we stand overall?
python3 .specify/extensions/openup/scripts/python/audit.py
```

Or through the agent: `/speckit.openup.audit`, `/speckit.openup.gate`,
`/speckit.openup.trace`.

Run the workflow when you are crossing a phase boundary — that is when the gate matters.

---

## Habits that keep this working

**Commit governance changes with the code they govern.** A WBS edit in its own commit three
days later is a change nobody reviewed against anything.

**Let gates fail.** A failing gate is the system doing its job. The fix is the graph, never the
threshold. If you find yourself editing `openup-config.yml` to make a run pass, stop — that is
the exact failure mode this project exists to prevent, and it is invisible six months later.

**Override deliberately, not habitually.** An override is a legitimate, logged human decision
and it writes the failing verdict to `.specify/evidence/overrides/<run_id>.json`. An
undocumented override is indistinguishable from a gate that never ran. Two overrides in a row
on the same condition means the condition is wrong or the work is — decide which, and fix that.

**Keep the risk register current or delete it.** A register last touched at Inception is a
stale snapshot that looks like risk management.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Every validator exits `2` | `jsonschema`/`PyYAML`/`referencing` missing | `pip install -r .specify/extensions/openup/requirements.txt` |
| `WBS-001` fails | Declared `level` disagrees with the dotted segment count | The id is the truth — fix the level |
| Audit reports hundreds of orphans | Perimeter too wide | Narrow `traceability.perimeter.include` |
| Gate fails on `security_review_complete` with nothing to see | Absence of evidence is not evidence — the record is missing | Create the review record |
| Workflow halts immediately with exit 2 | The graph cannot load (malformed YAML) | Run the validator directly for the parse error |
| A condition "is declared but not implemented" | Config names a condition `evaluate_gate.py` does not define | Remove it from config or implement it — it fails closed by design |
