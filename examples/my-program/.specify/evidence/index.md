# Governance Index — evidence

> The context map for this directory.

## Purpose

Where evidence records land: `security-review.json`, `security-validation.json`,
`acceptance-results.json`, and anything registered as `EVID-nnnn`.

## It is empty, and the gates say so

`security_review_complete` fails here with "no security review evidence", and its own
description says why in the words the whole model rests on: **absence of evidence is not
evidence**. A missing record fails its condition rather than being skipped.

Writing a `security-review.json` that says `"status": "passed"` would clear that condition in
one line. Nothing in this repository could tell that no review happened. That is what
`.specify/governance/security-practices.md` exists for, and why the gate description states
plainly that it does not know what was reviewed.
