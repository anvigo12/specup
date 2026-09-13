# Security Practices

> **Binding.** This file is part of the agent operating contract (specup.md s7). An agent
> designing, writing or changing code in this repository obeys these rules. A human reviewer
> enforces them; no validator does. Seeded from the `openup` extension — amending it is a
> governance decision, not an edit.

Two lifecycle gates depend on this file. `security_review_complete` closes the Lifecycle
Architecture milestone and `security_validation_passed` closes the Product Release milestone.
Both read an evidence record and check that it says `passed`. Neither knows what was
reviewed. **This document is the standard the reviewer applies**, and without it those two
conditions check only that somebody wrote a file.

## Rules

### Secrets and credentials

1. **No secret enters the repository.** Not in code, not in a test fixture, not in a config
   file, not in a commit message, not in an evidence record.
2. **A leaked secret is rotated, not deleted.** Removing the file leaves the value valid and
   the history intact. Rotate first, then clean up, then raise a `RISK-*` entry.
3. **No secret, token, credential, stack trace or personal datum appears in a problem
   document, a log line, or an error message.** See rule 19 of `coding-rules.md`.

### Identity and access

4. **Authenticate at the boundary. Authorize at the resource.** A request that passed
   authentication has proved who it is and nothing about what it may reach.
5. **Deny by default.** A path with no explicit rule is refused, not allowed.
6. **Check ownership on every object lookup.** An identifier taken from the request is an
   input, never a permission. This is the most common serious API defect, and it is invisible
   to a test that only uses its own data.
7. **Never take an authorization decision from the client.** A role, a scope or a tenant id in
   a request body is a claim to verify, not a fact.
8. **Distinguish 401 from 403.** 401 means the request is unauthenticated; 403 means it is
   authenticated and refused. Both carry a problem type.

### Input and output

9. **Parse untrusted input into typed domain values at the boundary**, and reject what will
   not parse. This is rule 8 of `coding-rules.md`, and it is a security control as much as a
   design one.
10. **Reject unknown fields** rather than ignoring them. Silent acceptance is how an unwanted
    field reaches an object that binds it.
11. **Bound every size**: body length, array length, string length, page size, upload size,
    recursion depth, and request rate.
12. **Never build a query, a path, a command or a template by string concatenation.** Use
    parameters.
13. **Encode output for its destination**, not once at the input.

### Transport and interface

14. **TLS only.** No plaintext fallback, no disabled certificate verification — not even
    behind a flag, and not in a test fixture that someone will copy.
15. **Set an explicit CORS allowlist.** Never reflect the request origin, and never pair a
    wildcard origin with credentials.
16. **Rate-limit every public operation**, and return a problem document when the limit is
    reached.
17. **Make an unsafe operation idempotent** where a client can retry it.

### Dependencies and supply chain

18. **Pin every dependency** to an exact version, with a lockfile in the repository.
19. **Scan dependencies for known vulnerabilities** on every change, and record the result as
    evidence.
20. **Add a dependency deliberately.** A new third-party package is an architecture decision
    when it touches authentication, cryptography, serialization or process execution — record
    it as an ADR.

### Data

21. **Collect the minimum.** A field nobody needs is a field that can leak.
22. **Classify personal data** and state its retention period where it is registered.
23. **Encrypt in transit and at rest.** Name the algorithm and the key management, and never
    write your own primitive.
24. **Rotate keys on a stated schedule**, and make rotation possible without downtime.

### Logging and audit

25. **Log the decision, never the credential.** Record that authorization failed, which rule
    refused it, and the correlation id — never the token that was presented.
26. **Use one correlation id** across the log line, the trace and the problem document's
    `instance` member, so a reported failure can be found.
27. **Make an audit record append-only.** Under `.specify/evidence/`, add — never rewrite
    history.

### Failing

28. **Fail closed.** When a security control cannot reach its dependency, refuse the request.
    A control that allows traffic when it breaks is not a control, and this is the same rule
    the gates apply: absence of evidence is not evidence.

## Every finding is a risk

A security finding is registered in `.specify/risks/risk-register.yaml` like any other risk,
with `probability`, `impact`, an owner, and mitigation bound to WBS nodes. It is not a comment
in a review thread. A finding at or above the high exposure threshold blocks the Lifecycle
Architecture gate until it has mitigation and verification, which is the behaviour you want
from a serious one.

**Accepting a security risk is a human decision** and is listed in
`.specify/governance/approval-matrix.md`. An agent may register a risk, propose a mitigation
and record evidence. An agent may not accept one, and may not record a security exception.

## The evidence records

Both gate conditions read a JSON file. These are the shapes `evaluate_gate.py` actually
parses, so a record in any other shape fails the condition.

`.specify/evidence/security-review.json` — read by `security_review_complete`:

```json
{
  "status": "passed",
  "reviewer": "security-team",
  "at": "2026-09-11T10:00:00Z",
  "scope": ["REQ-AUTH-0014"],
  "findings": []
}
```

The condition passes only when `status` is exactly `passed`. Any other value fails, and a
missing file fails.

`.specify/evidence/security-validation.json` — read by `security_validation_passed`:

```json
{
  "status": "passed",
  "critical_findings": 0,
  "at": "2026-09-11T10:30:00Z"
}
```

The condition needs `status` to be `passed` **and** `critical_findings` to be zero.

Register each record as an `EVID-nnnn` artifact and reference it from the WBS node that
produced it. An evidence file nothing points at is invisible to the graph.

## What this file does not do

SpecUP ships no scanner and runs no security test. The gate opens the record and reads two
fields; it cannot tell a review that happened from a file somebody wrote. Writing one of these
records to clear a gate is listed as prohibited in the constitution, and it is the easiest way
to make every security claim in this repository worthless.
