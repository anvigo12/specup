"""The authentication Aegra runs under for P3, and the instrument that records what reached it.

Answers  — whether a credential arrived, whose it is, and **which header carried it**. That last
           question is the reason this file exists rather than a copy of Aegra's own
           `examples/jwt_mock_auth_example.py`. P3 asks whether Agent Inbox authenticates against
           Aegra, and the inbox's connection form is labelled "LangSmith API key". Writing a
           handler that reads the header the author expects, and then reporting that the header
           arrived, is a probe that tests its author's memory. This handler reads every header the
           request carried, accepts the credential from any of the plausible ones, and writes down
           which one it actually was.

Does not — validate a real JWT. The token is a shared secret compared with `hmac.compare_digest`,
           exactly as Aegra's own example uses `mock-jwt-<user>-<role>-<team>`. P3 asks whether the
           inbox can authenticate at all, not whether RS256 verification works. A probe that also
           stood up a JWKS endpoint would be testing two things and able to explain neither
           failure. **Do not deploy this.** A real deployment verifies a signature against an
           issuer, and ADR 4's deployment envelope is where that belongs.

Records  — one JSON line per authentication attempt, to `$P3_AUTH_LOG`. The token itself is never
           written; a SHA-256 prefix stands in for it, so the transcript can show that the same
           credential arrived twice without the transcript becoming a place a credential leaks.

**Why there are no `@auth.on` handlers here, which is the interesting part.**

The first version of this file registered `@auth.on.threads.create` to stamp an owner into
metadata and `@auth.on.threads.search` to filter by it, copying Aegra's own example, so that P3's
isolation control — a second identity must not see the first's thread — would have something to
test. Reading `api/threads.py` before running it showed that both handlers were theatre:

  * `:227-228`  `# Always enforce owner from authenticated user` / `metadata["owner"] = user.identity`
                — and this runs **after** the handler's metadata is merged at `:220`, so the
                handler's stamp is overwritten by Aegra's own.
  * `:244`      the row is inserted with `user_id=user.identity`.
  * `:967`      `select(ThreadORM).where(ThreadORM.user_id == user.identity)` — unconditional, in
                the SQL, with no reference to any handler.

So Aegra scopes threads to their owner whether or not an authorization handler exists. Had the
handlers stayed, the isolation control would have passed, and it would have been measuring
Aegra's `WHERE` clause while appearing to measure this file. That is the same defect P4's step 5
had when a root-owned decoy made Unix permissions look like a Landlock denial, and it is caught
the same way: by asking which mechanism would still refuse if this file were deleted.

The control is kept, because Aegra's unconditional scoping is worth a measurement. It is now
labelled as a test of Aegra rather than of the probe's own handler.

Note also `core/auth_handlers.py:72-82`: `@auth.on` authorization defaults to **allow** — *"If no
handlers are defined -> allows by default"*. Authentication and authorization both fail open in
this server, which is a deployment finding rather than a P3 finding, and the campaign records it
as one.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import pathlib
import threading
import time
from typing import Any

from langgraph_sdk import Auth

auth = Auth()

# Two identities, so that "the inbox is authenticated" and "the inbox sees only its own threads"
# are separate observations. B never creates anything; it exists to be refused.
TOKEN_A = os.environ.get("P3_TOKEN_A", "")
TOKEN_B = os.environ.get("P3_TOKEN_B", "")
IDENTITY = {TOKEN_A: "inbox-user", TOKEN_B: "other-user"}

LOG = pathlib.Path(os.environ.get("P3_AUTH_LOG", "p3-auth-observations.jsonl"))
_LOCK = threading.Lock()

# Every header a client might reasonably put an API key in, in the order they are tried. Agent
# Inbox sends exactly one of these -- `x-api-key`, from `src/lib/client.ts` -- but the probe reads
# all of them and reports which arrived, so that the record states a measurement and not a
# transcription. `authorization` is listed because Aegra's own shipped example reads only that
# one, which is why that example cannot authenticate this client.
CREDENTIAL_HEADERS = ("x-api-key", "authorization", "api-key", "x-auth-scheme")

# Headers whose values are never written to the log. Everything else is recorded verbatim,
# because the point of the log is to show what the browser sent.
SECRET_HEADERS = frozenset({"x-api-key", "authorization", "api-key", "cookie"})


def _fingerprint(value: str) -> str:
    """A stable stand-in for a credential, so the log can compare without storing."""
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()[:16]


def _observe(record: dict[str, Any]) -> None:
    """Append one observation. Never raises: a probe instrument must not break the thing it
    is measuring, and a failed write is visible as a missing line."""
    record["t"] = time.time()
    try:
        with _LOCK, LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        pass


def _redacted(headers: dict[str, str]) -> dict[str, str]:
    return {
        k: (_fingerprint(v) if k.lower() in SECRET_HEADERS else v)
        for k, v in sorted(headers.items())
    }


def _extract(headers: dict[str, str]) -> tuple[str, str, str]:
    """Return (token, header_name, scheme) for the first credential header present.

    `authorization` is unwrapped from `Bearer <t>`; the scheme is reported separately so the
    record distinguishes "sent a bearer token" from "sent a bare key in the same header".
    """
    for name in CREDENTIAL_HEADERS:
        raw = headers.get(name)
        if not raw:
            continue
        if name == "authorization":
            scheme, _, rest = raw.partition(" ")
            if rest:
                return rest.strip(), name, scheme.lower()
            return raw.strip(), name, ""
        return raw.strip(), name, ""
    return "", "", ""


@auth.authenticate
async def authenticate(headers: dict[str, str]) -> dict[str, Any]:
    """Accept either configured token from any plausible header, and record what arrived.

    One positional parameter, deliberately. `langgraph_sdk`'s own dispatcher injects handler
    parameters **by name**, but Aegra reaches past it and calls the private handler with the whole
    headers dict positionally (`core/auth_middleware.py:260`). A handler written in the
    SDK-idiomatic style — `async def authenticate(authorization: str)` — would therefore receive
    the entire dict bound to `authorization` and fail in a way that reports as a bad credential.

    Starlette lower-cases header names before Aegra builds this dict, so the lookups are
    lower-case. The dict is normalised again anyway, because relying on that would be one more
    thing this probe assumes rather than checks.
    """
    lowered = {str(k).lower(): str(v) for k, v in headers.items()}
    token, header_name, scheme = _extract(lowered)

    observation: dict[str, Any] = {
        "origin": lowered.get("origin", ""),
        "user_agent": lowered.get("user-agent", ""),
        "credential_header": header_name or None,
        "scheme": scheme or None,
        "token_fingerprint": _fingerprint(token) if token else None,
        "headers_seen": _redacted(lowered),
    }

    if not token:
        observation["outcome"] = "rejected: no credential in any known header"
        _observe(observation)
        raise Auth.exceptions.HTTPException(
            status_code=401, detail="P3: no credential in any of " + ", ".join(CREDENTIAL_HEADERS)
        )

    # compare_digest against each configured token rather than a dict lookup, so a wrong token
    # cannot be distinguished from a right one by how long the comparison took.
    identity = ""
    for candidate, name in IDENTITY.items():
        if candidate and hmac.compare_digest(token, candidate):
            identity = name
            break

    if not identity:
        observation["outcome"] = "rejected: credential did not match"
        _observe(observation)
        raise Auth.exceptions.HTTPException(status_code=401, detail="P3: unknown credential")

    observation["outcome"] = "accepted"
    observation["identity"] = identity
    _observe(observation)

    # `identity` is the only mandatory key (`core/auth_middleware.py:265-266`). The rest is
    # returned because Aegra copies it onto the user object that the route handlers see.
    return {
        "identity": identity,
        "display_name": f"P3 {identity}",
        "is_authenticated": True,
        "permissions": ["p3:read", "p3:write"],
    }
