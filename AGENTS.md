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
python3 extensions/openup/scripts/python/audit.py
```

---

# This repository in particular

Everything above is the contract SpecUP ships to the projects it governs. The rest of this
file is what differs when the project being governed **is SpecUP**, and each item is here
because getting it wrong is silent.

## The scripts are not installed here, they are developed here

Run the validators from `extensions/openup/scripts/python/`, not from
`.specify/extensions/openup/`. This repository has no installed copy, and adding one would
create two copies of the engine with nothing keeping them in step.

## There are two config files and they are different documents

| File | What it is |
|---|---|
| `extensions/openup/openup-config.yml` | a **product** artifact — the defaults every project inherits on install |
| `.specify/extensions/openup/openup-config.yml` | a **project** artifact — how SpecUP governs itself |

`load_config` reads the second and falls back to the first. Before the second existed, SpecUP
was governed by the defaults it publishes, so tuning its own posture would have re-tuned every
new project's starting point. Nothing warns you about this. Change the product config only
when the change is right for every project; change the project config for SpecUP's own
decisions.

## A check id in an `index.md` will be reported as a dangling reference

`CTX-002` reads any id-shaped token in a context map as an artifact reference, and `WBS-004`
and `RISK-005` are id-shaped. They are check ids, they resolve to nothing, and the check is
right to say so. Name such checks in prose inside a context map. `TRC-`, `DOC-`, `CTX-` and
`APV-` share no prefix with an artifact type and are safe.

## The perimeter is the seventeen modules, and nothing else

`traceability.perimeter` covers `extensions/openup/scripts/python/**`. `tools/`, the schemas,
the templates and the workflows are outside it, with the reasons written next to the setting.
Adding a module to that directory means adding an `implements` edge to a registered
requirement, or backward coverage falls below its threshold on the next run.

## The licence is BUSL-1.1, and it lives in ten places

`LICENSE` is the authority. Seven component manifests repeat it as a `license:` string, and
`tools/build_catalog.py` republishes that string into the public catalog without reading it.
`tests/test_license.py` is the only thing holding the ten together, and it reads `LICENSE`
rather than hardcoding a name — so a future relicense edits `LICENSE`, `LICENSE-MIT` and
`docs/dev/licensing.md`, and the test follows.

Two consequences worth knowing before writing anything about the project:

- **Do not call SpecUP open source.** It is source-available. BUSL is not OSI-approved, and
  `test_the_readme_says_plainly_that_this_is_not_open_source` fails if the README stops saying
  so.
- **Changing a manifest's `license:` changes its build digest.** All four workflow manifests
  moved at 0.1.2, so the four workflows no longer rebuild to their 0.1.0 digests and need
  version bumps at release. `tests/test_catalog.py` is the thing that says so.

## What this repository cannot do, and should stop rather than fake

- **Witness an approval.** There is one maintainer and `allowed-signers` holds no key.
  `RISK-0001` is accepted, not solved. Do not add a key you did not generate.
- **Produce acceptance evidence.** `.specify/evidence/` is empty and
  `acceptance_scenarios_passing` fails. Do not write the JSON by hand to make a gate pass;
  that is the one file in the model that nothing can distinguish from a real record.
- **Raise its own derived-edge share by writing `tests` edges by hand.** That is what
  `test-file-naming-convention` is for, it recovers one edge here, and `RISK-0003` is the
  honest statement of why.
