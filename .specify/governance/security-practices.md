# Security Practices

> **Binding.** This file is part of the agent operating contract (specup.md s7). An agent
> designing, writing or changing code in this repository obeys these rules. A human reviewer
> enforces them; no validator does. Seeded from the `openup` extension — amending it is a
> governance decision, not an edit.
>
> **Answers** — the standard the two security gate conditions are reviewed against.
>
> **Does not answer** — what this system's threats are. That is a threat model and a risk
> register; these are the rules that hold whatever the threats turn out to be.
>
> **Filled in badly when** — the evidence record says `passed` and nobody can say which rules
> were applied. A review that produced no findings and cites no rule numbers is indistinguishable
> from a review that did not happen.
>
> **Checked by** — `security_review_complete` and `security_validation_passed` read an evidence
> record and check that it says `passed`. **Neither knows what was reviewed.** That is the whole
> reason this document exists; without it, those two gate conditions check only that somebody
> wrote a file.
>
> **Authority** — the security owner named in `.specify/governance/approval-matrix.md`. A
> security exception is one of the decisions specup.md s59 reserves for a named human.

Two lifecycle gates depend on this file. `security_review_complete` closes the Lifecycle
Architecture milestone and `security_validation_passed` closes the Product Release milestone.
Both read an evidence record and check that it says `passed`. Neither knows what was
reviewed. **This document is the standard the reviewer applies**, and without it those two
conditions check only that somebody wrote a file.

The rules are numbered once, 1 to 56, so a review or a finding can cite one.

## Rules

### Secrets and credentials

1. **No secret enters the repository.** Not in code, not in a test fixture, not in a config
   file, not in a commit message, not in an evidence record.
2. **A leaked secret is rotated, not deleted.** Removing the file leaves the value valid and
   the history intact. Rotate first, then clean up, then raise a `RISK-*` entry.
3. **Read a secret at run time**, from the environment or from a secret manager. A secret baked
   into a build artifact or a container image travels wherever that artifact travels, and it
   cannot be rotated without a rebuild.
4. **No secret, token, credential, stack trace or personal datum appears in a problem
   document, a log line, or an error message.** See rule 31 of `coding-rules.md`.

### Identity and access

5. **Authenticate at the boundary. Authorize at the resource.** A request that passed
   authentication has proved who it is and nothing about what it may reach.
6. **Deny by default.** A path with no explicit rule is refused, not allowed.
7. **Check ownership on every object lookup.** An identifier taken from the request is an
   input, never a permission. This is the most common serious API defect, and it is invisible
   to a test that only uses its own data.
8. **Never take an authorization decision from the client.** A role, a scope or a tenant id in
   a request body is a claim to verify, not a fact.
9. **Distinguish 401 from 403.** 401 means the request is unauthenticated; 403 means it is
   authenticated and refused. Both carry a problem type.
10. **Give every service its own identity**, and authenticate every call between services.
    Being inside the network is not a credential. A read model, a message consumer and a
    background job each act as somebody, and that somebody must be named.
11. **Make a token short-lived, scoped and revocable.** State the lifetime, state the scopes,
    and make revocation take effect without a deployment.
12. **Authorize each step of a multi-step operation.** A saga, a wizard, and a resumable upload
    all let a caller re-enter in the middle. Authorization at step one does not carry to
    step four.

### Input and output

13. **Parse untrusted input into typed domain values at the boundary**, and reject what will
    not parse. This is rule 16 of `coding-rules.md`, and it is a security control as much as a
    design one.
14. **Reject unknown fields** rather than ignoring them. Silent acceptance is how an unwanted
    field reaches an object that binds it.
15. **Bound every size**: body length, array length, string length, page size, upload size,
    recursion depth, and request rate.
16. **Never build a query, a path, a command or a template by string concatenation.** Use
    parameters.
17. **Encode output for its destination**, not once at the input.
18. **Sanitize any input value you repeat back.** A problem document that echoes the value it
    rejected is carrying attacker-controlled text into whatever reads it next.
19. **Never put an internal detail in a response.** No stack trace, no query text, no file
    path, no host name, no internal service name, and no library version. Those belong in the
    log, indexed by the correlation id.

### Errors that do not help an attacker

20. **Answer every failed credential check with one problem type.** An unknown account and a
    wrong password give the same status, the same `type`, the same `title` and the same
    `detail`. Two different answers let a stranger enumerate your users.
21. **Keep a credential check constant in time.** Compare secrets with a constant-time
    function, and do the same work whether or not the account exists.
22. **Do not let a status code reveal existence.** Where knowing that a resource exists is
    itself privileged, answer 404 rather than 403, and apply that choice consistently. Where it
    is not privileged, answer 403 and be clear.
23. **Give a 5xx problem a correlation id and nothing more.** The caller gets `type`, `title`,
    `status` and `instance`. The cause goes to the log, where the same id finds it.
24. **Scan an outbound response for secret patterns** at the edge, as a second line of defence.
    A control that assumes every handler is correct is not defence in depth.

### Transport and interface

25. **TLS only.** No plaintext fallback, no disabled certificate verification — not even
    behind a flag, and not in a test fixture that someone will copy.
26. **Set an explicit CORS allowlist.** Never reflect the request origin, and never pair a
    wildcard origin with credentials.
27. **Rate-limit every public operation.** Limit by authenticated identity where there is one,
    and by source otherwise. Answer with 429, a problem document, and a `Retry-After` header.
28. **Make an unsafe operation idempotent.** Accept an `Idempotency-Key` on every operation a
    client can retry, scope the key to the caller, keep the recorded response for a stated
    period, and refuse a reused key that arrives with a different body.
29. **Never amplify a retry.** Exponential backoff, full jitter, a delay ceiling and an attempt
    limit, plus a circuit breaker on a dependency that is failing. A retry loop without these
    turns one slow dependency into an outage you caused. See rule 47 of `coding-rules.md`.

### Dependencies and supply chain

30. **Pin every dependency** to an exact version, with a lockfile in the repository.
31. **Verify the artifact you install.** Check the digest or the signature against what the
    publisher stated. A pinned version with no integrity check pins a name, not the bytes.
32. **Scan dependencies for known vulnerabilities** on every change, and record the result as
    evidence.
33. **Add a dependency deliberately.** A new third-party package is an architecture decision
    when it touches authentication, cryptography, serialization or process execution — record
    it as an ADR.

### Data

34. **Collect the minimum.** A field nobody needs is a field that can leak.
35. **Classify personal data** and state its retention period where it is registered.
36. **A copy inherits the classification of its source.** A read model, a cache, an export, a
    search index, a backup, a dead-letter queue and an event store each hold real data under
    real rules. Classify the copy when you create it, not after a finding.
37. **An event carries the minimum its consumers need.** Publishing a whole record because it
    was convenient hands every subscriber data it has no reason to hold, and every subscriber
    then falls under rule 36.
38. **Keep personal data out of an append-only store.** An event store and an audit log cannot
    forget, and erasure is a legal obligation in many places. Store a reference, or encrypt the
    data under a per-subject key that you can destroy.
39. **Encrypt in transit and at rest.** Name the algorithm and the key management, and never
    write your own primitive.
40. **Restrict who may publish to and subscribe from a topic.** A message bus without
    authorization is a shared database with worse auditing.
41. **Rotate keys on a stated schedule**, and make rotation possible without downtime.

### Logging, audit, and monitoring

42. **Log the decision, never the credential.** Record that authorization failed, which rule
    refused it, and the correlation id — never the token that was presented.
43. **Use one correlation id** across the log line, the trace, every message in a saga, and the
    problem document's `instance` member, so a reported failure can be found.
44. **Log a fixed field set** on every request: the correlation id, the method, the path, the
    status, the problem `type` when there was one, the timestamp, and the caller's identity.
    Never the raw credential, and never the whole request body.
45. **Make an audit record append-only.** Under `.specify/evidence/`, add — never rewrite
    history.
46. **Alert on the rate of authorization failures.** A climbing 403 rate on one endpoint is a
    security signal, and it is the earliest one you will get.
47. **Treat a filling dead-letter queue as an incident**, not a backlog. Each message in it is
    work that was accepted and never done.
48. **Track the error rate by endpoint and by class**, separating 4xx from 5xx. A 4xx rise is
    usually a client or an attacker; a 5xx rise is usually you.

### Testing the security behaviour

49. **Test every failure path you specified.** A missing credential, an expired credential, a
    wrong tenant, an oversized body, a rate limit, and a dependency that is down.
50. **Test every authorization rule with another identity's identifier.** A test that only uses
    its own data cannot fail rule 7, which is why rule 7 is the defect that survives review.
51. **Validate error responses against the contract schema**, in the test suite and against the
    running service. An error shape that drifts from the contract breaks clients in the moment
    they are already failing.
52. **Test the controls, not only the features.** A rate limit nobody has triggered, and a
    circuit breaker nobody has opened, are claims rather than controls.

### Failing

53. **Fail closed.** When a security control cannot reach its dependency, refuse the request.
    A control that allows traffic when it breaks is not a control, and this is the same rule
    the gates apply: absence of evidence is not evidence.
54. **Treat a compensating transaction as a privileged path.** It reverses a completed action,
    it often runs with no user present, and it usually runs with wide rights. Authorize it,
    audit it, and review it as carefully as the action it undoes.
55. **Do not let a degraded mode drop a control.** When a dependency fails, the feature may
    degrade. Authentication, authorization and rate limiting may not.
56. **Report a suspected compromise before you clean it up.** Preserve the logs, raise the
    risk, and tell a human. An agent must never quietly repair what looks like an intrusion.

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

### What a review covers

The record says `passed`. This list says what that word must mean, so two reviewers reach the
same verdict and a later reader knows what was examined:

| Area | Rules |
|---|---|
| Secrets | 1–4 |
| Identity and access | 5–12 |
| Input and output | 13–19 |
| Error responses | 20–24 |
| Transport and interface | 25–29 |
| Dependencies | 30–33 |
| Data and privacy | 34–41 |
| Logging and monitoring | 42–48 |
| Tests | 49–52 |
| Failure behaviour | 53–56 |

Record the scope you reviewed in the `scope` field, and every finding in `findings`. A review
that covered one requirement and a review that covered the whole service both say `passed`,
and only `scope` tells them apart.

## What this file does not do

SpecUP ships no scanner and runs no security test. The gate opens the record and reads two
fields; it cannot tell a review that happened from a file somebody wrote. Writing one of these
records to clear a gate is listed as prohibited in the constitution, and it is the easiest way
to make every security claim in this repository worthless.

## Sources

These rules follow published material, and the API rules are the security half of
`coding-rules.md`. Read the source when a rule is unclear; do not reinterpret the rule.

| Source | Covers |
|---|---|
| RFC 9457, *Problem Details for HTTP APIs* | the failure document a control returns |
| [API error handling practices](https://zuplo.com/learning-center/best-practices-for-api-error-handling) | what an error may not reveal, retries, idempotency keys, correlation ids |
| [Problem Details in practice](https://swagger.io/blog/problem-details-rfc9457-api-error-handling/) | field-level error reporting without leaking internals |
| [Cloud-native data patterns](https://learn.microsoft.com/en-us/dotnet/architecture/cloud-native/distributed-data) | one owner per dataset, read models, sagas, event stores — rules 36 to 40 and 54 |
