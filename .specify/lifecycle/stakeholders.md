# Stakeholders — SpecUP

> **Answers** — who is affected by SpecUP, what each of them needs from it, and who decides.
>
> **Does not answer** — which decisions need a named human. That is
> `.specify/governance/approval-matrix.md`, and the two must agree: a role that approves
> something there has to appear here with a name behind it.
>
> **Filled in badly when** — every row is a job title and no row is a person. A stakeholder
> list of roles is a list of nobody, and the test is whether you could send one of them a
> question today.
>
> **Checked by** — `stakeholders_identified` at the Inception gate, which checks that this
> **file exists**. It does not read it. `APV-000` and `APV-003` are the checks with teeth, and
> they read the approval matrix rather than this document.
>
> **Authority** — the maintainer.

## The honest summary

**One person builds, decides, reviews and releases SpecUP.** Every row in the approval matrix
names the same person. That is recorded as `RISK-0001`, exposure 0.54, and it is `accepted`
rather than mitigated because a solo project cannot schedule work that produces a second
person. The acceptance is itself an unwitnessed approval, which is the recursion stated
plainly rather than left for a reader to notice.

Everything below is therefore a description of interests, not of an organisation.

| Stakeholder | Who | Interest | Decides |
|---|---|---|---|
| Maintainer | one person, named in `.specify/governance/allowed-signers` when a key is added | that the tool's claims are true | everything |
| Adopting team | unknown; SpecUP is published, not deployed | that adoption cost is recoverable and the audit is legible on a real codebase | nothing here; they decide whether to adopt |
| The agent under governance | any coding agent reading `AGENTS.md` | that the operating contract is unambiguous, and that no rule can be satisfied by editing a check | nothing, by design (`specup.md` §51, §58, §59) |
| Reviewer of a governed repository | a third party, at audit time | that provenance separates evidence from claim, and that the audit says which is which | nothing; they read |
| Spec Kit | upstream | that the extension stays additive and does not reach into the task runner | its own interfaces |

## What each one is currently owed

- **The adopting team** is owed a real adoption cost. There is now one measurement — SpecUP's
  own, in `.specify/traceability/index.md` — taken by the author of the tool on a repository
  designed around it. `README.md` says so where it quotes the figure.
- **The reviewer** is owed the provenance mix beside every coverage figure, which the audit
  prints and which cannot be switched off.
- **The agent** is owed an `AGENTS.md` at or above every directory it works in. `CTX-003`
  warns when one is missing, and it looks only at governed directories — a source tree with
  no operating contract above it passes that check in silence. `RISK-0004` is the related
  finding.

## What nobody is owed by this document

A commitment about a release date, a support channel, or a second maintainer. None exists,
and writing one here would be the failure mode this template names: a row that could never be
contradicted by anything SpecUP actually does.
