# Agent Operating Contract

> **Answers** — how an agent is allowed to operate in this repository (specup.md s7).
>
> **Does not answer** — how to perform any particular activity. That is `skills/*/SKILL.md`
> (s8). Keep the separation: `AGENTS.md` = what rules must I obey, `SKILL.md` = how do I
> perform this activity. A contract that starts explaining procedure becomes long enough that
> nobody reads the rules.
>
> **Filled in badly when** — it reads as encouragement. "Be careful", "use good judgement" and
> "follow best practices" are unfalsifiable: no agent can tell whether it complied, and no
> reviewer can tell either. Every rule below is written so that breaking it is visible.
>
> **Checked by** — `CTX-003` warns when no `AGENTS.md` is reachable above a governed directory.
> **Nothing checks that any rule here was obeyed.** The rules are enforced by the validators
> they point at, and by the reviewer, which is why each one names the check behind it or says
> that there is none.
>
> **Authority** — whoever owns the repository. The nearest `AGENTS.md` wins, so a scoped file
> narrows this one rather than replacing it.

## Mandatory startup

Before changing anything:

1. Read the nearest applicable `AGENTS.md`.
2. Read that directory's `index.md`.
3. Resolve every artifact it references. If one does not resolve, **stop** — see below.
4. Determine the current phase and iteration:
   `.specify/extensions/openup/openup-config.yml` → `lifecycle`.
5. Determine the applicable WBS node, its requirements, its risks, and its acceptance criteria.
6. Read the applicable `skills/<activity>/SKILL.md`.
7. Read the standards that bind the work you are about to do — see below.

Step 3 is the whole point of the hierarchy: navigate
`directory → AGENTS.md → index.md → the one artifact you need`, rather than loading the
repository into context (s56, s57).

## Filesystem-first rule

State lives in files, not in the conversation. Never make an implementation change without:

- a governing requirement;
- a WBS node;
- applicable acceptance criteria;
- a traceability entry.

If you cannot find one of these, that absence is the finding. Report it.

## Resolve, or stop — never infer

The single rule this whole model rests on. When a reference does not resolve, stop and say so.
Do not invent the requirement, the criterion, or the risk that would have made the task
coherent. An invented governing artifact is worse than a missing one: it looks like governance
and checks nothing.

## Re-read before asserting

Any value you are about to state as fact — a threshold, a clause, an id, a number from a
document — you re-open and read before you state it. Not the summary of it you formed earlier
in this session. The source.

This is not diligence for its own sake. A value reconstructed from what you remember reading
arrives with exactly the same confidence as one you just read, and nothing downstream can tell
the two apart: the requirement, the test and the review all inherit the error together. It
costs one file read to avoid, and it is the highest-yield habit in this document.

Two corollaries:

- **Agreement between two things you wrote is not corroboration.** If you check a transcribed
  value against a predicate you derived from the same reading, they agree because they share
  an origin, and they are wrong together. Corroboration needs a second source you did not
  produce.
- **Say which reading you did.** "Confirmed against §4.2" and "from a single reading,
  unconfirmed" are both useful reports. Only the first one is a claim, and it must be true.

## The binding standards

Three documents under `.specify/governance/` are part of this contract, not advice. Read the
one that applies before you produce the artifact it governs.

| Document | Binds | Standard |
|---|---|---|
| `language-rules.md` | every governed document you write | ASD-STE100 Simplified Technical English |
| `coding-rules.md` | every change to code | Railway Oriented Programming, RFC 9457, cloud-native data patterns |
| `security-practices.md` | design, code, and the security gate evidence | the rules the security review applies |

None of the three is machine-checked. That does not make them optional — it makes the human
reviewer the enforcement, and it means your report that you followed them is `asserted`, in
exactly the sense the provenance vocabulary uses the word. Do not claim otherwise.

## Prohibited

- bypassing a quality gate, or adjusting a threshold, perimeter or test so that one passes;
- marking work `done` without evidence — `validate_done.py` computes that, and disagreeing
  with it in prose does not change it;
- hand-writing a `derived` edge, or labelling a judgment call `derived` (`TRC-010` re-runs the
  rule and fails the edge);
- hand-writing an `approved` edge or its hash — use `approve_edge.py`;
- editing a generated view (`wbs.md`, `risk-register.md`, `traceability.md`, `coverage.md`,
  and the generated governance documents) — run `render_views.py --write`;
- editing `.specify/traceability/derived.yaml`, which is rewritten in full;
- changing a `BASELINED` artifact outside the change-control process;
- inventing a requirement, a risk, or an acceptance criterion;
- committing secrets or personal data.

## Required

Every implementation change produces the full chain:

```
Requirement → WBS node → Code → Test → Evidence → Traceability update
```

There is no separate task id: WBS **L7** *is* the executable task (s15).

## Boundaries

| | |
|---|---|
| **Always** | Work from the filesystem. Report what you found, including what you did not find. |
| **Ask a human** | Anything in `.specify/governance/approval-matrix.md`: scope, requirement baseline, architecture baseline, high-risk acceptance, breaking API change, security exception, release. Also anything destructive or irreversible. |
| **Never** | Authorize a governance decision on your own, or present a claim as evidence. |

Accountability does not transfer to an agent (s58). An AI performs bounded work; a named human
owns the decision.

## Checking where you stand

```bash
python3 .specify/extensions/openup/scripts/python/audit.py
```
