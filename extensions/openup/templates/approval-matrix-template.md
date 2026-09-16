# Approval Matrix

> **Answers** — which decisions require a named human, and who that human is. Authored, not
> generated (specup.md s5, s59, s60).
>
> **Does not answer** — whether an approval actually happened. That is recorded on the
> artifact or the edge, and `validate_approvals.py` is what reads it back.
>
> **Filled in badly when** — the **Who** column is empty. That is the whole failure mode, and
> it is silent: every gate still runs, every check still passes, and nobody notices that no
> decision has an owner until one is disputed. If nobody is named here, anyone can override
> anything and the gate is decorative.
>
> **Checked by** — `APV-000` **fails** when this file names no approver at all, and `APV-003`
> **fails** an approval whose `by` is not a name in this table. `APV-002` goes further and
> verifies the signature on a declared commit against `.specify/governance/allowed-signers`.
> What nothing checks is whether the right person is in the cell.
>
> **Authority** — the product owner, or whoever owns the organisation's delegation. Changing
> this table is a governance change, not an edit; it belongs in a diff someone reviewed.
>
> Fill in the **Who** column with real names or standing groups before the first gate. An
> empty cell is an unowned decision, which in practice means whoever is nearest at the time.
>
> The sibling documents in this directory — `definition-of-ready.md`, `definition-of-done.md`
> and `quality-gates.md` — are **generated** from the code that enforces them. This one is
> not, because who may decide something is a decision about your organisation and no validator
> can recompute it.

## What an approval is here

An approval is a named human taking accountability for a decision an agent may propose but
may not authorize (s58, s59). Recording one on a traceability edge is done with the tool, so
the signature is bound to the content it was given for:

```bash
python3 .specify/extensions/openup/scripts/python/approve_edge.py \
  --from REQ-AUTH-0014 --relation refines --to BUS-OBJ-0017 --by product-owner
```

Be clear-eyed about what that proves: it binds an approval to content, and `TRC-013` withdraws
it if the content changes. It does **not** prove a human ran the command. The strongest binding
available is `--commit` pointing at a signed commit.

## Decisions that require a named human (s59)

An agent may propose each of these. None may be silently authorized by one.

| Decision | Who approves | Recorded as |
|---|---|---|
| Business scope | | `BUS-OBJ-*` status → `APPROVED` |
| Requirement baseline | | `REQ-*` status → `BASELINED`, with `approvals` |
| Architecture baseline | | `ADR-*` status → `APPROVED`; architecture gate |
| High-risk acceptance | | `RISK-*` status → `accepted` (fails `RISK-000` without an approval) |
| Breaking API change | | `CONTRACT-*` supersession |
| Security exception | | `SECURE-*` plus security evidence |
| Release | | `GATE-PRODUCT_RELEASE` |

## Gate approvals (s60)

| Gate | Required evidence | Who approves |
|---|---|---|
| `GATE-LIFECYCLE_OBJECTIVES` | vision, stakeholders, initial risks, WBS L1–L3 | |
| `GATE-LIFECYCLE_ARCHITECTURE` | architecture, ADRs, high-risk mitigation, contracts, security review | |
| Iteration ready | tasks meeting the Definition of Ready | |
| Iteration complete | tests, scenarios, traceability, evidence | |
| `GATE-INITIAL_OPERATIONAL_CAPABILITY` | coverage, acceptance results, no critical risks | |
| `GATE-PRODUCT_RELEASE` | full audit, security validation, release documents | |

The machine-checkable conditions behind each gate are listed in the generated
`quality-gates.md`. This table records who is accountable when those conditions pass — and who
decides when someone wants to proceed anyway.

## Overrides

A workflow gate offers `override` as well as `abort`. An override is a deliberate, logged human
act, not a bypass: the run log records who overrode what and when.

| Rule | |
|---|---|
| Who may override a failing gate | |
| What must be recorded | the failing condition, the reason, and the remediation commitment |
| When the remediation is due | |

If nobody is named here, anyone can override anything and the gate is decorative.
