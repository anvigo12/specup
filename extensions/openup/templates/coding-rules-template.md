# Coding Rules — Railway Oriented Programming, RFC 9457

> **Binding.** This file is part of the agent operating contract (specup.md s7). An agent
> writing or changing code in this repository obeys these rules. A human reviewer enforces
> them; no validator does. Seeded from the `openup` extension — amending it is a governance
> decision, not an edit.

Failure is a first-class value here, not an interruption. Three standards say how:

- **Railway Oriented Programming** — a function has a success track and a failure track, and a failure travels the failure track as data.
- **RFC 9457, Problem Details** — when a failure crosses an HTTP boundary, it is  `application/problem+json` and it carries an identity.
- **The cloud-native data patterns** — when a failure crosses a *service* boundary, the compensation is part of the design, and the consistency the caller gets is part of the requirement.

The three parts below follow that order: inside a function, at the interface, and between
services. The rules are numbered once, 1 to 65, so a review can cite one.

## Why a governed project needs this

Every other part of this model treats a claim as worthless unless it can be checked. An
exception carrying a string breaks that: it has no id, no stable type, and no link to the
requirement that anticipated it, so a failure mode cannot be traced, cannot be covered by an
acceptance criterion, and cannot appear as evidence at a gate.

A failure with a type URI is an artifact. It can be named in a requirement, asserted in a
scenario, observed in a test, and counted in a report. That is the whole reason for the rule.

The same argument reaches further than one process. A saga step that fails and leaves no
compensation is an unfinished requirement. An eventually consistent read that no requirement
describes is a defect report waiting to be filed by a user. Both are meaning left in
someone's head, which is the one failure this whole model exists to prevent.

---

# Part 1 — The railway

A fallible function returns one value with two possible shapes:

```
Result<Success, Failure>        Ok(value) | Err(problem)
```

## Rules

### Signatures and failure types

1. **A function that can fail returns a `Result`.** Its signature says so. A signature that
   claims to return a value and sometimes throws is a lie the type system cannot catch.
2. **Never throw for an expected failure.** A rejected certificate, an absent record, a
   refused permission and a malformed request are all normal outcomes. They travel the
   failure track.
3. **Throw only for a defect** — a broken invariant that no caller can handle. A defect is not
   a domain failure, and it must never appear in a function's declared failure type. When you
   throw, say why in place:

   ```ts
   // openup: escape — unreachable; the parser guarantees a tag here.
   throw new Error("unreachable");
   ```

   An undeclared throw inside the traceability perimeter is a defect at review, the same way
   a hand-written `derived` edge is.
4. **Give every failure a tag.** A failure is a distinct type with a discriminant, never a
   string and never a bare error code. Effect writes this as `Data.TaggedError("...")`, Kotlin
   as a `sealed interface`. The tag is what makes an exhaustive handler checkable by a
   compiler, and it is what maps one-to-one onto a problem type URI at the boundary.
5. **Name a failure for the rule that was broken, not for the code that found it.**
   `CertificateExpired` is a failure. `ValidationError` is a category, and a category cannot
   carry an acceptance criterion.
6. **Keep the failure type of a module closed.** A caller must be able to list every way a
   call can fail by reading its type. A failure type that widens to `Error` or `Throwable`
   tells the caller nothing and forces a defensive handler.

### Composition

7. **Compose, do not nest.** Chain with `bind` (flatMap) for a fallible step and `map` for a
   total one. A ladder of `if (err) return err` is the shape this style removes.
8. **Decide short-circuit or accumulate, once.** Sequential steps short-circuit on the first
   failure. Independent validations accumulate into one failure carrying every reason. Never
   mix the two in one function.
9. **Accumulate every independent check before you answer.** A caller that must send four
   requests to find four broken fields is being made to do the work of the validator. The
   accumulated list becomes the `errors` array of the problem document — rule 34.
10. **Handle a failure by name, not by catching everything.** Recover from the tags you can
    recover from, and let the rest travel. A handler that catches a whole failure type erases
    the distinctions the rest of this file depends on.
11. **Make the handler exhaustive.** Add a failure mode, and the compiler must name every
    place that does not yet handle it. This is the single largest benefit of the style, and a
    default branch throws it away.
12. **Map at the edge, not in the middle.** A failure keeps its own type through the domain
    and is translated once, at the boundary that emits it. One translation point per boundary.
13. **Convert a third-party exception where you call it.** Wrap the throwing call, catch the
    exception you expect, and return a domain failure. Never let a library's exception type
    travel through the domain, and never catch one so broadly that it hides a defect.
14. **Never discard a failure.** An empty catch block, a `Result` nobody reads, and a fallback
    that silently returns a default are all the same defect: a failure that left both tracks.
    If a failure is genuinely acceptable, say so in code and record why.

### Values

15. **No `null` or `undefined` in the domain.** Absence is `Option`/`Maybe`, and it is part of
    the signature.
16. **Parse, do not validate.** Turn untrusted input into a typed domain value at the
    boundary, and return a failure if it will not parse. Downstream code receives values that
    cannot be wrong, so it needs no defensive checks.
17. **Prefer immutable values.** A value that changes after a check was made against it
    invalidates the check.
18. **Make illegal states unrepresentable.** A type that cannot hold a bad combination needs
    no rule forbidding one.

### Effects

19. **Keep the core pure; keep I/O at the shell.** A function that decides and a function that
    performs are different functions. Pure decisions are the ones a test can pin to an
    acceptance criterion.
20. **Declare what a function needs.** Pass a dependency as a parameter, a context receiver, or
    a typed requirement. A function that reaches for a global clock, a global configuration or
    a global connection cannot be tested against a criterion, because the criterion cannot set
    it up.
21. **Bind a resource to a scope.** Acquire and release as a pair, so a failure on the failure
    track releases the resource exactly as a success does. Never rely on a later line running.
22. **Make a retry a policy, not a loop.** State the schedule, the ceiling and the attempt
    limit in one place, and retry only a failure that rule 44 marks retryable. A retry around
    a non-retryable failure is a slower way to return the same problem.

### Governance

23. **Every failure mode is registered.** If a requirement anticipates a failure, that failure
    has a problem type and an acceptance criterion. A failure mode nobody wrote down is an
    untested path.
24. **One domain failure, one problem type.** The tag in rule 4 and the `type` URI in rule 28
    name the same thing. A reviewer reading the requirement, the handler and the contract must
    see one name, not three.

## Shape

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

## The libraries that already do this

You do not have to build the railway. Two libraries carry it as their central idea, and this
file uses them as the reference for how the rules look in practice. **Neither is required by
this repository.** Use the idiom your stack already has, and use these as the definition of
what "done properly" means.

### Effect — TypeScript

`Effect<Success, Error, Requirements>` carries three type parameters. The second is the error
channel, which holds every failure the program declares. The third is the requirements
channel, which holds every service it needs. Both are rule 1 and rule 20, checked by the
compiler.

```ts
import { Data, Effect } from "effect";

class CertificateMalformed extends Data.TaggedError("CertificateMalformed")<{ reason: string }> {}
class CertificateExpired   extends Data.TaggedError("CertificateExpired")<{ expiredAt: string }> {}
class IssuerUntrusted      extends Data.TaggedError("IssuerUntrusted")<{ issuer: string }> {}

const authenticate = (raw: string) =>
  Effect.gen(function* () {
    const certificate = yield* parseCertificate(raw);
    yield* checkNotExpired(certificate);
    yield* checkIssuerTrusted(certificate);
    return yield* openSession(certificate);
  });
// Effect<Session, CertificateMalformed | CertificateExpired | IssuerUntrusted, TrustStore>
```

That inferred type is the whole point. It lists every failure mode and every dependency, and
it is the closest thing this repository has to a machine-readable statement of rule 6.

At the boundary, translate by tag:

```ts
const handler = (raw: string) =>
  authenticate(raw).pipe(
    Effect.catchTags({
      CertificateMalformed: (e) => problem(400, "certificate-malformed", e.reason),
      CertificateExpired:   (e) => problem(401, "certificate-expired",   `The certificate expired on ${e.expiredAt}.`),
      IssuerUntrusted:      (e) => problem(401, "issuer-untrusted",      `The issuer ${e.issuer} is not trusted.`),
    }),
  );
```

Add a failure mode, and the compiler names the boundary that does not yet handle it. That is
rule 11 working.

Use `Effect.fail` for a declared failure and `Effect.die` for a defect. A defect never enters
the error channel, so rule 3 is a type-level rule here rather than a review convention.

### Arrow — Kotlin

Arrow offers the same model twice: `Either<Failure, Success>` as a value, and `Raise<Failure>`
as a scope. Inside `either { }` you call `bind()` to unwrap or short-circuit, and `ensure()` to
fail on a broken condition.

```kotlin
sealed interface AuthFailure {
  data class CertificateMalformed(val reason: String) : AuthFailure
  data class CertificateExpired(val expiredAt: Instant) : AuthFailure
  data class IssuerUntrusted(val issuer: String) : AuthFailure
}

fun authenticate(raw: String): Either<AuthFailure, Session> = either {
  val certificate = parseCertificate(raw).bind()
  ensure(certificate.notAfter > clock.now()) { CertificateExpired(certificate.notAfter) }
  ensure(trustStore.contains(certificate.issuer)) { IssuerUntrusted(certificate.issuer) }
  openSession(certificate)
}
```

A sealed interface makes the `when` at the boundary exhaustive, so a new failure mode breaks
the build until somebody maps it to a status code and a problem type.

Convert a library exception where you call it, and never wider:

```kotlin
catch({ users.insert(username, email) }) { e: SQLException ->
  if (e.isUniqueViolation()) raise(UserAlreadyExists(username)) else throw e
}
```

Rethrowing what you did not expect is rule 13 and rule 3 together: a unique-key violation is a
domain failure, and a dropped connection is not.

Accumulate with `zipOrAccumulate`, `mapOrAccumulate` or `accumulate { }`:

```kotlin
fun buildRegistration(name: String, age: Int): EitherNel<RegistrationProblem, Registration> = either {
  zipOrAccumulate(
    { ensure(name.isNotEmpty()) { EmptyName } },
    { ensure(age >= 0) { NegativeAge(age) } },
  ) { _, _ -> Registration(name, age) }
}
```

The `NonEmptyList` this produces becomes the `errors` array of the problem document. Rule 9
and rule 35 are the same rule, seen from the two sides of a boundary.

### Concept map

| Concept | Plain `Result` | Effect (TypeScript) | Arrow (Kotlin) |
|---|---|---|---|
| the two tracks | `Ok` \| `Err` | `Effect<A, E, R>` | `Either<E, A>`, `Raise<E>` |
| declare a failure | return `Err(...)` | `Effect.fail(...)` | `raise(...)` |
| a tagged failure type | discriminated union | `Data.TaggedError("Tag")` | `sealed interface` |
| a defect | `throw`, with an escape marker | `Effect.die(...)` | `throw` |
| sequence a fallible step | `bind` / `flatMap` | `yield*` inside `Effect.gen` | `.bind()` inside `either { }` |
| transform a success | `map` | `Effect.map` | a plain expression |
| guard a condition | `if (!ok) return Err(...)` | `Effect.filterOrFail` | `ensure`, `ensureNotNull` |
| accumulate | fold over the results | `Effect.validateAll` | `zipOrAccumulate`, `mapOrAccumulate` |
| handle one failure by name | `switch` on the tag | `Effect.catchTag`, `Effect.catchTags` | `recover`, an exhaustive `when` |
| handle everything | — | `Effect.catchAll` | `getOrElse`, `fold` |
| translate at the edge | an explicit function | `Effect.mapError` | `withError` |
| wrap a throwing library | one `try`/`catch` | `Effect.try`, `Effect.tryPromise` | `catch({ }) { e: X -> }` |
| result as a value | the `Result` itself | `Effect.either`, `Effect.option` | `Either`, `nullable { }`, `result { }` |
| a declared dependency | a parameter | the `R` channel, `Layer` | a context receiver |
| a scoped resource | `try`/`finally` | `Effect.acquireRelease`, `Scope` | `resourceScope { }`, `autoCloseable` |
| a retry policy | — | `Effect.retry(Schedule…)` | `Schedule`, `CircuitBreaker` |

API names move between major versions. Check each against the version you use, and update
this table when you upgrade rather than leaving a name that no longer exists.

---

# Part 2 — RFC 9457 at the boundary

A failure that crosses an HTTP boundary becomes a problem detail document. Everything a client
can act on must be in that document, and nothing that helps an attacker may be.

## Rules

### The document

25. **Use the media type `application/problem+json`.** Not `application/json` with an error
    object inside it. The XML form is `application/problem+xml`.
26. **Carry `type`, `title` and `status` on every problem.**
    - `type` is an absolute URI that identifies the failure mode, at most 1024 characters.
    - `title` is a short, human-readable summary of the **type**, at most 1024 characters.
    - `status` repeats the HTTP status code, between 100 and 599.
27. **Keep `title` constant for a type.** It describes the failure mode, not this occurrence.
    Only translation may change it. It follows `language-rules.md`.
28. **Treat a `type` URI as a published interface.** Clients branch on it. Changing one, or
    reusing one for a different failure, is a breaking API change and needs the approval named
    in `approval-matrix.md`.
29. **Make the `type` URI resolve to documentation.** A URI a developer can open is worth more
    than a URI they must ask about. Use the IANA problem type registry where an entry already
    fits, and publish your own types under one stable base URI.
30. **Use `detail` for this occurrence.** It says what happened this time, in terms the caller
    can act on. It names the field, the limit or the value that was wrong.
31. **Never put a secret, a credential, a token, a stack trace, an internal host name, or
    personal data in a problem document.** `detail` is where this leak happens, because it is
    the member somebody fills in from a caught exception. See `security-practices.md`.
32. **Use `instance` to identify this occurrence.** It is a URI, and it carries the same
    correlation id that appears in the logs and the trace. Rule 48.
33. **Use `about:blank` only when the status code says everything.** Any failure a client might
    branch on gets its own type URI.
34. **Put machine-readable specifics in extension members**, not in prose inside `detail`.
    Two extensions are conventional and worth adopting as-is:

    | Member | Type | Use |
    |---|---|---|
    | `code` | string, at most 50 characters | a project error code, from your own registry |
    | `errors` | array | one entry per field-level failure |
    | `errors[].detail` | string | what is wrong with this one field |
    | `errors[].pointer` | JSON Pointer | where in the request body |
    | `errors[].parameter` | string | which query or path parameter |
    | `errors[].header` | string | which header |

35. **Report every failure in one response.** Rule 9 at the boundary. One request, one list of
    everything wrong with it.
36. **One type per failure mode, and one failure mode per type.** This is rule 1 of
    `language-rules.md` applied to machine vocabulary.
37. **Evolve the format by addition only.** Add an optional member. Never repurpose a member,
    never narrow a type, and never remove one without a deprecation period. State in the
    contract that a client must ignore an extension member it does not recognise.

### The status code

38. **Use the most specific status code that applies.** A `400` for everything, or a `500` for
    everything, tells the client only that it should give up.

    | Status | Use it when |
    |---|---|
    | `400 Bad Request` | the request is malformed — broken JSON, a missing required field |
    | `401 Unauthorized` | the caller is not authenticated, or the credential is invalid |
    | `403 Forbidden` | the caller is authenticated, and is refused |
    | `404 Not Found` | the resource does not exist |
    | `409 Conflict` | the request fights the current state — a duplicate create, a stale version |
    | `422 Unprocessable Content` | the request parses, and breaks a business rule |
    | `429 Too Many Requests` | the caller passed a rate limit — always with `Retry-After` |
    | `500 Internal Server Error` | an unhandled defect inside this service |
    | `502 Bad Gateway` | an upstream service answered with something invalid |
    | `503 Service Unavailable` | this service is down or overloaded — with `Retry-After` when the delay is known |
    | `504 Gateway Timeout` | an upstream service did not answer in time |

39. **Separate `400` from `422`.** `400` means the request could not be read. `422` means it
    was read, and a business rule refused it. A client fixes those two in different places.
40. **Separate `401` from `403`.** `401` means the request is unauthenticated. `403` means it
    is authenticated and refused. Both carry a problem type. See `security-practices.md`.
41. **Never answer a failure with `200`.** The exceptions are the protocols that mandate it —
    rule 49.

### The contract

42. **Declare every failure response in the contract.** An operation with only a 2xx response
    has not been specified. The OpenAPI document is where a failure mode becomes reviewable.

    ```yaml
    responses:
      "401":
        description: The client certificate was rejected.
        content:
          application/problem+json:
            schema:
              $ref: "#/components/schemas/Problem"
            examples:
              certificateExpired:
                $ref: "#/components/examples/CertificateExpired"
    ```

43. **Share one `Problem` schema** across the whole API, and give each failure mode a named
    example under it. One schema and many examples is what lets a reviewer see the failure
    modes without reading the handler.
44. **State whether a failure is retryable**, in the contract and in the problem type's
    documentation. A client cannot work this out from a status code alone.

    | Retryable | Not retryable |
    |---|---|
    | `429`, `500`, `502`, `503`, `504` | `400`, `401`, `403`, `404`, `409`, `422` |

    Retrying a non-retryable failure wastes the caller's time and your capacity, and returns
    the same problem.
45. **Test every failure path you declared.** Trigger each one: invalid input, a missing
    credential, an unknown id, a rate limit, and an upstream that is down. Validate the
    response against the `Problem` schema. A failure response that no test produces is a
    failure response nobody has seen.

### Behaviour around the failure

46. **Send `Retry-After` with `429` and with `503`** when you know the delay. A client that
    must guess will guess badly.
47. **Retry with exponential backoff and full jitter.** Double the wait after each attempt,
    multiply by a random factor, cap the delay, and cap the attempt count. Backoff without
    jitter synchronises every client onto the same instant and turns a recovery into a second
    outage.
48. **Carry one correlation id through everything.** The same id appears in the incoming
    header, the log line, the trace span, the outgoing call, and the problem document's
    `instance`. A user quoting an id from a failure message must lead you to the exact log
    line.
49. **Keep these rules on other protocols.** GraphQL answers `200` and puts failures in the
    `errors` array, so the stable identity goes in `extensions.code`. gRPC uses its own status
    codes and a details message. In both, the identity, the stability and the registration
    rules are unchanged; only the transport differs.

## Shape

```json
{
  "type": "https://example.com/problems/certificate-expired",
  "title": "The client certificate has expired",
  "status": 401,
  "detail": "The certificate expired on 2026-03-04.",
  "instance": "/sessions/01J9Z2P4A7",
  "code": "401-02"
}
```

With field-level failures accumulated per rule 35:

```json
{
  "type": "https://example.com/problems/invalid-body-property",
  "title": "A property of the request body is invalid",
  "status": 422,
  "detail": "Two properties of the request body are invalid.",
  "instance": "/registrations/01J9Z2P4A7",
  "code": "422-01",
  "errors": [
    { "detail": "The name must not be empty.", "pointer": "/name" },
    { "detail": "The age must be a positive integer.", "pointer": "/age" }
  ]
}
```

---

# Part 3 — Failure across a service boundary

A distributed system removes the two guarantees a single database gave you: a query that
reaches every table, and a transaction that rolls everything back. You do not get them back.
You replace them with a design, and the design is part of the requirement.

## Rules

### Ownership

50. **One service owns a dataset.** It is the only writer, and it is the authority. Every other
    copy is derived, and says so.
51. **Never read another service's store.** No shared database, no cross-schema join, no
    reporting query against someone else's tables. A shared table is a shared schema, and a
    shared schema removes the independence the split was for.
52. **Copy data deliberately into a read model.** A local, denormalized copy of what another
    service owns removes a synchronous call from the request path, and keeps this service
    working while the owner is down. Duplicating data this way is an established practice, not
    an anti-pattern — as long as rule 50 holds and the copy never becomes a second authority.
53. **Replicate by event, not by call.** The owner publishes a change; the holder of the read
    model subscribes and updates it. A synchronous query to another service couples the two
    and makes the caller's availability the product of both.
54. **Choose the store for the workload.** A relational store for rich relationships, a
    document store for aggregates, a key-value store for a cache or a cart. One service, one
    store, chosen for what that service does.

### Consistency

55. **State the consistency each requirement needs.** "Immediate" and "eventual" are properties
    of a requirement, and a requirement that does not say which one it needs has not been
    written. Where the answer is eventual, name the staleness bound as an acceptance
    criterion, so a test can observe it.
56. **Do not attempt a distributed transaction.** There is none to attempt. A sequence of local
    transactions across services is a saga, and you write it.
57. **Write the compensating transaction with the step it undoes.** A saga step whose
    compensation is not written is unfinished work, not a later improvement. Register the
    compensation as its own WBS node under the same requirement.
58. **A compensation can fail.** Give it its own failure type, its own problem type, and its
    own alert. A saga whose recovery path is assumed to succeed has no recovery path.
59. **Choose choreography or orchestration, and record which.** Choreography is a chain of
    events and no coordinator. Orchestration is one coordinator issuing commands. Both work;
    mixing them by accident does not. This is an ADR.
60. **Make every consumer idempotent.** A message transport delivers at least once, so a
    consumer will see a duplicate. Deduplicate by message id, and make the handler safe to run
    twice.
61. **Do not depend on message order** unless the transport guarantees it for that key, and
    then say so in the design. Out-of-order delivery is normal, and a handler that assumes
    order fails rarely and silently, which is the worst way to fail.
62. **Never drop a failed message.** Route it to a dead-letter queue and alert. A message that
    left both tracks is the distributed form of rule 14.
63. **Degrade on the failure track.** When a dependency is unavailable, either return a problem
    document that says so, or serve the local read model and state that the data can be stale.
    Never serve stale data silently, and never present a guess as a fact.
64. **Apply CQRS and event sourcing strategically.** Separating the read model from the write
    model, or storing a sequence of events instead of a current state, both buy scale and
    history and both cost complexity. Each is an ADR that names the problem it solves, not a
    default.
65. **Trace a saga end to end with one correlation id** — rule 48, carried through every
    message. Without it, a partial failure is a set of unrelated log lines in five services.

---

## How this reaches the graph

A failure mode is governed like anything else:

- the requirement states it, and states the consistency it needs;
- an acceptance criterion covers it, with a scenario tagged to that criterion;
- the contract declares the response;
- the problem `type` URI is the name all three use;
- a compensating transaction is a WBS node, owned and scheduled like any other work.

That chain is what lets `validate_trace.py` see the failure path at all. A failure that only
exists inside a `catch` block is invisible to every check in this repository, and so is a
compensation that exists only in someone's intention.

## What this file does not do

Nothing here is machine-checked. SpecUP parses no source file and opens no OpenAPI document;
`critical_contracts_defined` confirms that a registered contract's file exists and does not
read it. Conformance is established at review, and an agent's report that it followed these
rules is `asserted`, not evidence.

## Sources

These rules follow published material. Read the source when a rule is unclear; do not
reinterpret the rule.

| Source | Covers |
|---|---|
| RFC 9457, *Problem Details for HTTP APIs* | the members, the media type, the extension model |
| [IANA HTTP Problem Type registry](https://www.iana.org/assignments/http-problem-types/) | problem types you do not have to invent |
| [Problem Details in practice](https://swagger.io/blog/problem-details-rfc9457-api-error-handling/) | the `code` and `errors` extensions, documenting problems in OpenAPI |
| [API error handling practices](https://zuplo.com/learning-center/best-practices-for-api-error-handling) | status code selection, retries, idempotency keys, correlation ids |
| [Cloud-native data patterns](https://learn.microsoft.com/en-us/dotnet/architecture/cloud-native/distributed-data) | one owner per dataset, materialized views, sagas, CQRS, event sourcing |
| [Effect](https://effect.website/docs/v4/onboarding) | the typed error channel and typed requirements, in TypeScript |
| [Arrow](https://arrow-kt.io/learn/quickstart/) | `Either`, the `Raise` DSL and error accumulation, in Kotlin |
