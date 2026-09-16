# Examples

Two directories, and the relationship between them is the first thing they teach.

| | What it is | Governed? |
|---|---|---|
| [`my-program/`](my-program/) | the **governance**. "My Program" — its vision, plan, risks, and graph. `WBS-1` is a program. | yes: this is the `.specify/` tree |
| [`my-project/`](my-project/) | the **deliverable**. What gets built. | no — and the README there explains why that is a consequence, not an omission |

Every file in both is self-describing: it says what it settles, what it does not, how you can
tell it has been filled in badly, and which check would notice. Where nothing checks it, it
says that too — which is most of the interesting cases.

## What this example is in, and what it is not

**`my-program` passes the Inception gate and fails the Elaboration gate on five conditions.**

That is the point. A worked example that shipped green would teach that the gates are
decorative, and the first thing anyone would learn from copying it is how to produce a project
that reports success. This one is in the state a real program is in on its first day: the case
is made, the plan exists, the risks are sized, and nothing is built.

```bash
# From the repository root.

# Passes 5/5. Exit 0.
python3 extensions/openup/scripts/python/evaluate_gate.py \
    --gate GATE-LIFECYCLE_OBJECTIVES --root examples/my-program

# Fails 5 of 7. Exit 1.
python3 extensions/openup/scripts/python/evaluate_gate.py \
    --gate GATE-LIFECYCLE_ARCHITECTURE --root examples/my-program

# The whole picture, including the provenance mix.
python3 extensions/openup/scripts/python/audit.py --root examples/my-program
```

### The five it fails, and why each one is correct

| Condition | Why it fails | The cheap repair, and what it would cost |
|---|---|---|
| `architecture_baselined` | no `architecture.md`, no registered `ADR-nnnn` | copy the template into place. The condition checks only that the file **exists**, so a blank one clears it — which is why `init_openup.py` seeds `architecture-template.md` and not `architecture.md` |
| `all_high_risks_have_mitigation` | `RISK-0001` has mitigation work and no verification reference | add a `verification:` entry naming a test nobody has designed. The gate goes green and the register becomes false |
| `requirements_traceable` | nothing `implements` either requirement | assert an `implements` edge from the task that writes the vision. It resolves, it type-checks, forward coverage reads 100%, and **no check in this repository can detect that it is false** |
| `critical_contracts_defined` | no `CONTRACT-*` registered | register one pointing at an empty file. The condition checks the `source` exists; it never opens it |
| `security_review_complete` | `.specify/evidence/` is empty | write `security-review.json` containing `"status": "passed"`. Nothing knows whether a review happened |

Every repair in the right-hand column takes under a minute and every one of them is available
right now. That is not a gap in the tooling — it is the boundary of what any filesystem check
can establish, and the reason the audit prints the provenance mix beside every coverage figure
and the reason `security-practices.md` exists at all. **A gate stops an accident. It does not
stop a decision to lie.**

### The two it passes

`wbs_valid` and `human_approvals_witnessed`. The second one passes because
`approval-matrix.md` here is **filled in** — the shipped template leaves the *Who* column
blank and `APV-000` fails on it. Scaffold a fresh tree and watch:

```bash
mkdir -p /tmp/fresh   # --root must already exist
python3 extensions/openup/scripts/python/init_openup.py --root /tmp/fresh --program "Fresh"
python3 extensions/openup/scripts/python/validate_approvals.py --root /tmp/fresh
```

## Using these

Copy either into `workspace/`, which is committed as an empty folder precisely so that your
own program can live there without becoming part of SpecUP:

```bash
cp -r examples/my-program workspace/my-program
cp -r examples/my-project workspace/my-project
```

`workspace/.gitignore` ignores everything inside it. A project there is governed *by* SpecUP;
it is not part of SpecUP.

## What is deliberately missing from `my-program`

Each of these is absent for a reason, and the reason is the lesson.

| Missing | Why |
|---|---|
| `language-rules.md`, `coding-rules.md`, `security-practices.md` | `init_openup.py` seeds all three. Omitted here because nothing reads them — they bind at review — and 45 KB of standard text would bury the parts a gate actually looks at |
| `definition-of-ready.md`, `definition-of-done.md`, `quality-gates.md` | **generated** by `render_views.py` from the code that enforces them. Committing a copy is how a generated document starts disagreeing with its check |
| `wbs.md`, `risk-register.md`, `coverage.md` | the same argument. Run `render_views.py --write --root examples/my-program` to produce them |
| `skills/*/SKILL.md` | seeded by `init_openup.py`. No WBS node here names one, so `CTX-004` has nothing to resolve |
| any task at `status: done` | `validate_done.py` computes done from the graph. At Inception nothing is implemented or verified, so nothing can honestly be done — including the task that wrote the vision, whose own work is finished. See the note in `wbs.yaml` |
