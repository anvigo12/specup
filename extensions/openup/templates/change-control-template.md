# Change Control

> **Answers** — how a change to a `BASELINED` artifact is proposed, assessed and absorbed.
> Authored, not generated (specup.md s5, s52).
>
> **Does not answer** — what the change reaches. That is computed: `impact.py` traverses the
> graph in both directions. The impact *set* is a fact; the decision about it is yours.
>
> **Filled in badly when** — the impact set is assessed from memory or by reading around the
> code. Two failure modes follow, and the second is the dangerous one: a fan-out that looks
> too small is usually right about the graph and wrong about the system, which means the
> missing edges are the finding, not a reason to skip the step.
>
> **Checked by** — **nothing forces a change through this document.** There is no commit-trailer
> validation and no pre-commit hook (s43, s44). What does happen automatically is `TRC-013`:
> editing an artifact recomputes `approved_endpoints_hash`, and every edge approved for the
> old content stops counting as evidence until someone approves it again. So the graph
> notices afterwards even when nobody followed the process.
>
> **Authority** — per `.specify/governance/approval-matrix.md`, by the class of artifact being
> changed. Re-baselining is a human act.

## When this applies

Once an artifact is `BASELINED` or beyond (s31), changing it is a change-control event rather
than an edit. Below `BASELINED`, edit freely — that is what `DRAFT` and `REVIEW` are for.

## 1. Compute the impact before deciding

Never assess impact from memory or by reading around the code. Ask the graph:

```bash
python3 .specify/extensions/openup/scripts/python/impact.py --of REQ-AUTH-0014
```

It reports what the change reaches: user stories, WBS nodes, risks, ADRs, contracts, scenarios,
tests and source files. The reverse direction answers "what does this file affect?":

```bash
python3 .specify/extensions/openup/scripts/python/impact.py --of src/auth/authentication_service.ts
```

An impact set the graph cannot see is an impact set nobody will remember. If the fan-out looks
too small, the missing edges are the finding.

## 2. Record the change

| Field | |
|---|---|
| What changes | the artifact id, and what about it |
| Why | the driver — new information, defect, scope change, external requirement |
| Impact set | paste or attach the `impact.py` output |
| Risk | new or changed `RISK-*` entries |
| Approval | who, per `approval-matrix.md` |

## 3. Expect the approvals to withdraw themselves

Editing an artifact voids the signatures on the edges that touch it: `TRC-013` recomputes
`approved_endpoints_hash`, and an edge approved for the old content stops counting as evidence
until someone approves it again. That is the mechanism working, not a problem to route around —
re-approve deliberately, with:

```bash
python3 .specify/extensions/openup/scripts/python/approve_edge.py --from … --relation … --to … --by …
```

## 4. Re-baseline

A changed `BASELINED` artifact increments `baseline.version` and collects a fresh approval. The
previous version is not deleted: use `supersedes` so the history stays in the graph.

## 5. Re-run the gate

The change is absorbed when the gate that covered the artifact passes again:

```bash
python3 .specify/extensions/openup/scripts/python/audit.py --json
```

## What this does not do

There is no commit-trailer validation and no pre-commit hook (s43, s44), so nothing forces a
change through this document. It is a process you follow, backed by checks that will notice
afterwards if you did not.
