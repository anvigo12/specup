# Vision — SpecUP

> **Answers** — what SpecUP is for, who it is for, and what would make it not worth having.
>
> **Does not answer** — what it must do. That is `.specify/traceability/requirements.yaml`,
> where each obligation cites the `specup.md` section it comes from.
>
> **Filled in badly when** — it describes the software instead of the problem. A vision that
> can be satisfied by shipping anything at all is not constraining the work, and a reader can
> tell because nothing in it could ever be contradicted by a release.
>
> **Checked by** — `vision_present` at the Inception gate, which checks that this **file
> exists** and opens nothing. That is worth knowing before relying on it: an unfilled template
> passes. Nothing checks that a requirement serves this vision, and nothing ever will — that
> is a reading, and `.specify/governance/approval-matrix.md` says whose.
>
> **Authority** — the maintainer. Changing this is a business-scope decision under
> `change-control.md`, which is the row of the approval matrix reserved for a named human.

## The problem

An agent that writes code can also write the record of having written it correctly. Auditor
and audited collapse into one actor, and every artifact of governance — the traceability
matrix, the coverage figure, the sign-off — becomes something the agent produced about itself.
The output is complete, plausible and self-confirming, and no reviewer can tell which parts
are evidence and which are claims.

Process frameworks do not fix this. They ask for the same artifacts and have no way to tell a
recovered fact from an invented one, so applying one to an agent produces governance theatre
faster than a human could produce it honestly.

## What SpecUP is

A governance layer over an agent it does not own: OpenUP's lifecycle, made machine-checkable,
enforced by validators that read the filesystem and nothing else.

Its one claim is that **governance is only real when it is machine-checkable and
consequential** — `BUS-OBJ-0001`. Machine-checkable, so a claim can be re-derived rather than
believed. Consequential, so failing it stops something.

The mechanism that carries the claim is provenance: every traceability edge is `derived`
(a named rule reproduced it from the filesystem, and the check re-runs the rule),
`asserted` (someone judged it), or `approved` (a human signed it, bound by hash to the content
they saw). The audit prints that mix next to every coverage figure, because a graph that is
overwhelmingly asserted must not be able to present itself as covered.

## Who it is for

A team letting an agent do substantial engineering work, that has to be able to show a third
party which parts of the record are evidence. Regulated work is the obvious case; it is not
the only one.

Not for: a project small enough that one person holds the whole design in their head. The
overhead is real and is not recovered at that size. `docs/guide/existing-project.md` says the
same thing about brownfield adoption, and `specup.md` §65 is an entire section on not doing
this to yourself.

## What would make it not worth having

Three failures, stated so they can be looked for rather than argued about later.

1. **The provenance labels stop meaning anything.** If teams routinely relabel judgements
   `derived` to move a metric, the distinction dies and the whole model is decoration.
   `TRC-010` re-runs every rule and fails an edge it cannot reproduce, which is what makes the
   label cost something rather than being free to type.
2. **The checks become the target.** A perimeter narrowed to make coverage rise, a threshold
   lowered to make a run go green, a test widened to make a suite pass. Two of those three
   have checks against them and one does not: nothing in this repository can tell a weakened
   assertion from a fixed defect.
3. **Nobody reads the audit.** A report that always fails is a report nobody opens by the
   third week. This is the one the project cannot design its way out of.

## Where SpecUP itself stands against this

Its own audit fails, in `CONSTRUCTION`, on `acceptance_scenarios_passing` and a verification
coverage of 94%, and 84% of its own graph is `asserted`. Those numbers are in
`.specify/traceability/index.md` rather than in a summary, and they are not being repaired to
make this document read better.
