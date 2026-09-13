# Coding Rules — Railway Oriented Programming, RFC 9457

> **Binding.** This file is part of the agent operating contract (specup.md s7). An agent
> writing or changing code in this repository obeys these rules. A human reviewer enforces
> them; no validator does. Seeded from the `openup` extension — amending it is a governance
> decision, not an edit.

Failure is a first-class value here, not an interruption. Two standards say how:

- **Railway Oriented Programming** — a function has a success track and a failure track, and a failure travels the failure track as data.
- **RFC 9457, Problem Details** — when a failure crosses an HTTP boundary, it is  `application/problem+json` and it carries an identity.

## Why a governed project needs this

Every other part of this model treats a claim as worthless unless it can be checked. An
exception carrying a string breaks that: it has no id, no stable type, and no link to the
requirement that anticipated it, so a failure mode cannot be traced, cannot be covered by an
acceptance criterion, and cannot appear as evidence at a gate.

A failure with a type URI is an artifact. It can be named in a requirement, asserted in a
scenario, observed in a test, and counted in a report. That is the whole reason for the rule.

## The railway

A fallible function returns one value with two possible shapes:

```
Result<Success, Failure>        Ok(value) | Err(problem)
```

### Rules

1. **A function that can fail returns a `Result`.** Its signature says so. A signature that
   claims to return a value and sometimes throws is a lie the type system cannot catch.
2. **Never throw for an expected failure.** A rejected certificate, an absent record, a
   refused permission and a malformed request are all normal outcomes. They travel the
   failure track.
3. **Throw only for a programmer error** — a broken invariant that no caller can handle. When
   you do, say so in place:

   ```ts
   // openup: escape — unreachable; the parser guarantees a tag here.
   throw new Error("unreachable");
   ```

   An undeclared throw inside the traceability perimeter is a defect at review, the same way
   a hand-written `derived` edge is.
4. **Compose, do not nest.** Chain with `bind` (flatMap) for a fallible step and `map` for a
   total one. A ladder of `if (err) return err` is the shape this style removes.
5. **Decide short-circuit or accumulate, once.** Sequential steps short-circuit on the first
   failure. Independent validations accumulate into one failure carrying every reason. Never
   mix the two in one function.
6. **Map at the edge, not in the middle.** A failure keeps its own type through the domain
   and is translated once, at the boundary that emits it. One translation point per boundary.
7. **No `null` or `undefined` in the domain.** Absence is `Option`/`Maybe`, and it is part of
   the signature.
8. **Parse, do not validate.** Turn untrusted input into a typed domain value at the boundary,
   and return a failure if it will not parse. Downstream code receives values that cannot be
   wrong, so it needs no defensive checks.
9. **Keep the core pure; keep I/O at the shell.** A function that decides and a function that
   performs are different functions. Pure decisions are the ones a test can pin to an
   acceptance criterion.
10. **Prefer immutable values.** A value that changes after a check was made against it
    invalidates the check.
11. **Make illegal states unrepresentable.** A type that cannot hold a bad combination needs
    no rule forbidding one.
12. **Every failure mode is registered.** If a requirement anticipates a failure, that failure
    has a problem type and an acceptance criterion. A failure mode nobody wrote down is an
    untested path.

### Shape

```ts
type Problem = { type: string; title: string; status: number; detail?: string; instance?: string };
type Result<T> = { ok: true; value: T } | { ok: false; problem: Problem };

function authenticate(raw: string): Result<Session> {
  return parseCertificate(raw)          // Result<Certificate>
    .bind(checkNotExpired)              // Result<Certificate>
    .bind(checkIssuerTrusted)           // Result<Certificate>
    .map(openSession);                  // Result<Session>
}
```

Each step returns a failure rather than raising one. The caller reads one type and handles
one shape.

## RFC 9457 at the boundary

A failure that crosses an HTTP boundary becomes a problem detail document.

### Rules

13. **Use the media type `application/problem+json`.** Not `application/json` with an error
    object inside it.
14. **Declare every failure response in the contract.** An operation with no 4xx or 5xx
    response has not been specified. The OpenAPI document is where a failure mode becomes
    reviewable.
15. **Carry `type`, `title` and `status` on every problem.**
    - `type` is an absolute URI that identifies the failure mode. It is stable: clients
      branch on it, so changing one is a breaking API change and needs the approval in
      `approval-matrix.md`.
    - `title` is a short, human-readable summary of the **type**. It does not change between
      occurrences, and it follows `language-rules.md`.
    - `status` repeats the HTTP status code, and must agree with it.
16. **Use `detail` for this occurrence and `instance` to identify it.** `detail` explains what
    happened this time; `instance` is a URI for this occurrence, and is the same correlation
    id that appears in the logs.
17. **Use `about:blank` only when the status code says everything.** Any failure a client
    might branch on gets its own type URI.
18. **Put machine-readable specifics in extension members**, not in prose inside `detail`.
19. **Never put a secret, a credential, a token, a stack trace, or personal data in a problem
    document.** See `security-practices.md`.
20. **One type per failure mode, and one failure mode per type.** This is rule 1 of
    `language-rules.md` applied to machine vocabulary.

### Shape

```json
{
  "type": "https://example.com/problems/certificate-expired",
  "title": "The client certificate has expired",
  "status": 401,
  "detail": "The certificate expired on 2026-03-04.",
  "instance": "/sessions/01J9Z2P4A7",
  "errors": [{ "field": "certificate", "code": "expired" }]
}
```

And in the contract:

```yaml
responses:
  "401":
    description: The client certificate was rejected.
    content:
      application/problem+json:
        schema:
          $ref: "#/components/schemas/Problem"
```

## How this reaches the graph

A failure mode is governed like anything else:

- the requirement states it;
- an acceptance criterion covers it, with a scenario tagged to that criterion;
- the contract declares the response;
- the problem `type` URI is the name all three use.

That chain is what lets `validate_trace.py` see the failure path at all. A failure that only
exists inside a `catch` block is invisible to every check in this repository.

## What this file does not do

Nothing here is machine-checked. SpecUP parses no source file and opens no OpenAPI document;
`critical_contracts_defined` confirms that a registered contract's file exists and does not
read it. Conformance is established at review, and an agent's report that it followed these
rules is `asserted`, not evidence.
