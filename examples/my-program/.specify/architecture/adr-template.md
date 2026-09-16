# ADR-nnnn — <short title: the problem solved, and the solution>

> **Answers** — one architectural decision: the forces that made it necessary, the options
> considered, the one taken, and what it costs. Register it as `ADR-nnnn` in
> `.specify/traceability/requirements.yaml`, because the Elaboration gate counts registered
> ADRs and not files on disk.
>
> **Does not answer** — whether the risk that prompted the decision is closed. It is not. See
> *Revisit when* below, which is not optional.
>
> **Filled in badly when** — it records the outcome and not the forces. An ADR whose
> *Considered options* holds one entry is a note, not a decision: nobody reading it later can
> tell whether the alternative was weighed and dropped or never seen. The second most common
> failure is an empty *Revisit when* — a decision taken under uncertainty that records no
> condition for revisiting it becomes permanent by accident.
>
> **Checked by** — `WBS-005` and `TRC-002` reject an `ADR-` id that does not resolve, `CTX-002`
> rejects one in a context map that does not resolve, `DOC-002` rejects one named in a
> docstring that does not resolve, and `architecture_baselined` fails the Elaboration gate
> while any registered ADR is below `APPROVED`. **Nothing checks what this document says.**
> The reviewer is the enforcement.
>
> **Authority** — the architect named in `.specify/governance/approval-matrix.md`. Status
> enters at `DRAFT`; moving it to `APPROVED` is a human act, and generated does not mean
> approved.
>
> **Shape** — this follows [MADR](https://adr.github.io/madr/) section for section, so these
> records read the same as ADRs anywhere else and a tool that understands MADR understands
> these. *Confirmation* and *More information* carry the two rules this project adds.
>
> Copy this file per decision, as `adr-0001-<short-slug>.md`. Do not edit it in place: it is
> the template, and a project that fills it in has no template left.

- **Status:** DRAFT <!-- DRAFT | REVIEW | APPROVED | BASELINED — must match the registry -->
- **Date:** <!-- when the decision was taken, not when the file was written -->
- **Decision-makers:**
- **Consulted:**
- **Informed:**
- **Supersedes:** — <!-- also record the `supersedes` relation, so the history is in the graph -->

## Context and Problem Statement

What is true that forces a decision now, in two or three sentences or as a question. Name the
requirements and the risks by id, because an ADR that motivates itself in prose cannot be
traced to what it serves:

- Drives: `REQ-…`, `NON-FR-…`
- Prompted by: `RISK-…`

If a normative source constrains the answer, cite it at the level a reader can check — the
document, its edition, and the clause. A citation to a document alone is a citation to several
hundred pages.

## Decision Drivers

- <driver: a force, a constraint, a quality attribute — not a preference>
- …

## Considered Options

- <option 1>
- <option 2>
- …

One option here means one of two things and the reader cannot tell which: that there was no
alternative, or that nobody looked. If there genuinely was no alternative, write that down as
the first driver.

## Decision Outcome

Chosen option: "<option>", because <the driver it satisfies that the others do not>.

### Consequences

- Good, because …
- Bad, because … — **what gets worse.** An ADR with no cost has not been thought about.
- Obligation: … — what must now stay true for this to keep holding: a version floor, an
  operational practice, a contract someone else honours.

### Confirmation

How anyone later establishes that this decision is actually in force — a check, a test, a
review step. Name it, or say that nothing confirms it.

**When this decision rests on a value transcribed from an external source** — a threshold, a
bit layout, a truth table, a size limit — confirmation has one specific requirement:

A transcription checked against a predicate written from the same reading of the source is not
checked at all. The two agree because they share an origin, and they are wrong together.
Agreement is only evidence when the two statements came from genuinely independent places: the
document itself and an implementation by someone else, two editions, a conformance vector you
did not write.

So name both sources, and name them separately. Say which one produced the value and which one
confirmed it. If there is only one, say that instead — a value marked "from a single reading,
unconfirmed" is honest and someone can act on it, while a value claiming a cross-check it never
had is the kind of error that survives review precisely because it looks finished.

`DOC-005` enforces the *naming* wherever such a claim appears in a docstring. Nothing enforces
the independence, which is why it is written here rather than left to a check.

## Pros and Cons of the Options

### <option 1>

- Good, because …
- Neutral, because …
- Bad, because …

### <option 2>

- …

## More Information

### Revisit when

**Mandatory.** At least one condition, observable by someone who was not in the room:

-

A decision taken under uncertainty does not remove the uncertainty. **Deciding is not
closing.** If a risk prompted this ADR, that risk stays `open` or `mitigating` until its
exposure actually falls and the register records why — the ADR is the choice of how to
mitigate, not the mitigation itself. Closing the risk here, on the strength of having decided
something, is the most common way a register comes to understate what a project is carrying.
