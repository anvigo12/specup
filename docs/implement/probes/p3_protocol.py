#!/usr/bin/env python3
"""Replay the requests Agent Inbox makes, and check what Aegra answers.

Answers  — whether Aegra serves the six Agent Protocol operations Agent Inbox uses, with the
           credential Agent Inbox can send, and whether each of the four `HumanResponse` verbs
           resumes an interrupted thread.

Does not — prove that anything renders. This file never opens a browser. It establishes the
           protocol facts so that, when the browser half disagrees with it, the disagreement
           localises to the client rather than to Aegra. Used on its own it would answer a
           question P3 did not ask: the falsifier's middle clause is about a list rendering, and
           a passing HTTP replay is not evidence for it. `p3_browser.js` is the other half, and
           neither half is the probe.

Why raw HTTP rather than `langgraph_sdk`. The client under test is the **JavaScript** SDK, and
the Python one in this venv is a different implementation of the same protocol. Driving the
Python SDK and reporting that Aegra answered would be testing the wrong client. The bodies below
are written out literally so the record shows the bytes, and `p3.sh` checks them against the
JavaScript SDK actually installed under `agent-inbox/node_modules`.

Exit 0 the protocol held, 1 a falsifier fired, 2 a setup fault.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

# The four verbs, with the exact `args` shape Agent Inbox sends for each. Read from
# `src/components/agent-inbox/hooks/use-interrupted-actions.tsx` and `utils.ts` rather than from
# the README, because the two disagree and the code is what runs.
#
#   accept   args is null when only allow_accept is set, and the whole ActionRequest when
#            allow_edit is set too and the user changed nothing.
#   edit     args is an ActionRequest whose every value has been stringified by the textarea.
#   response args is a bare string.
#   ignore   args is null.
VERBS = ("accept", "edit", "response", "ignore")


class Falsified(Exception):
    """A pre-registered falsifier fired."""


class Fault(Exception):
    """The probe could not be run. Never reported as a result."""


def call(
    base: str,
    method: str,
    path: str,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> tuple[int, Any]:
    """One HTTP call. Returns (status, parsed-or-text). Never raises on an HTTP error status,
    because a 401 is a measurement here rather than a failure."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token is not None:
        # The one header Agent Inbox can send: `src/lib/client.ts` builds
        # `defaultHeaders: { ...(langchainApiKey && { "x-api-key": langchainApiKey }) }`
        # and there is no Authorization path anywhere in that repository.
        req.add_header("x-api-key", token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw
    except urllib.error.URLError as exc:
        raise Fault(f"{method} {path} could not reach the server: {exc}") from exc


def interrupted_thread(base: str, token: str, graph: str, payload: dict[str, Any]) -> str:
    """Create a thread, run the graph on it, and wait for it to pause. Returns the thread id.

    The run matters, not just the thread. Aegra writes `graph_id` into thread metadata in
    `services/run_preparation.py`, at run creation — a thread that is created and never run
    carries `graph_id: null` and can never match the metadata filter Agent Inbox always sends,
    so a probe that created bare threads would find an empty inbox for a reason that has nothing
    to do with authentication or schema.
    """
    status, thread = call(base, "POST", "/threads", token, {})
    if status != 200 or not isinstance(thread, dict):
        raise Fault(f"could not create a thread: HTTP {status} {thread}")
    tid = thread["thread_id"]

    status, run = call(base, "POST", f"/threads/{tid}/runs", token,
                       {"assistant_id": graph, "input": payload})
    if status not in (200, 201):
        raise Fault(f"could not start a run: HTTP {status} {run}")

    for _ in range(60):
        status, row = call(base, "GET", f"/threads/{tid}", token)
        if status == 200 and isinstance(row, dict) and row.get("status") == "interrupted":
            return tid
        if status == 200 and isinstance(row, dict) and row.get("status") == "error":
            raise Fault(f"the run errored instead of interrupting: {row}")
        time.sleep(1)
    raise Fault(f"thread {tid} never reached status 'interrupted'")


def interrupt_value(base: str, token: str, tid: str) -> Any:
    """Read the interrupt exactly where Agent Inbox reads it on the Aegra path.

    Aegra's `Thread` response model has six fields and `interrupts` is not among them
    (`models/threads.py:86-91`), so the inbox's primary branch — `thread.interrupts` — can never
    fire here, and everything goes through `GET /threads/{id}/state`. This reads the same place:
    `tasks[-1].interrupts[-1].value`, per `contexts/utils.ts:291-312`.
    """
    status, state = call(base, "GET", f"/threads/{tid}/state", token)
    if status != 200 or not isinstance(state, dict):
        raise Fault(f"could not read thread state: HTTP {status}")
    tasks = state.get("tasks") or []
    if not tasks:
        # contexts/utils.ts:291-293 indexes the last task with no emptiness guard, so this state
        # would throw a TypeError in the browser that the inbox swallows into "invalid schema".
        raise Falsified("the interrupted thread has no tasks, which the inbox renders as an "
                        "invalid schema rather than as the error it is")
    interrupts = tasks[-1].get("interrupts") or []
    if not interrupts:
        raise Falsified("the last task carries no interrupts")
    return interrupts[-1].get("value")


def resume(base: str, token: str, tid: str, graph: str, response: dict[str, Any],
           stream: bool) -> tuple[int, Any]:
    """Send one `HumanResponse` the way Agent Inbox sends it.

    Always a list of exactly one element: *"When the Agent Inbox sends a response, it will always
    send back a list with a single HumanResponse object in it"* (its README), and
    `use-interrupted-actions.tsx` builds that list from the single selected submit type.

    `stream` picks between the two endpoints the inbox uses: `runs.stream` for accept, edit and
    response, and the non-streaming `runs.create` for ignore.
    """
    path = f"/threads/{tid}/runs/stream" if stream else f"/threads/{tid}/runs"
    body: dict[str, Any] = {"assistant_id": graph, "command": {"resume": [response]}}
    if stream:
        body["stream_mode"] = "events"
    return call(base, "POST", path, token, body)


# A run passes through these on its way somewhere; none of them is an answer.
IN_FLIGHT = frozenset({"busy", "pending"})


def settled(base: str, token: str, tid: str, timeout: int = 60) -> str:
    """Wait for the thread to reach a state that is not in flight, and report where it landed.

    The first version of this waited only for the status to stop being `interrupted`, which is
    wrong for the non-streaming endpoint. `POST /threads/{id}/runs` returns as soon as the run is
    queued, so the thread is briefly `busy`; the caller then read the state before the graph had
    written anything and reported that a perfectly good `ignore` had not reached the graph. The
    streaming endpoint hid the bug, because it does not return until the stream is done — so the
    first three verbs passed and only the fourth failed, which reads like a fact about `ignore`
    and was a fact about this function.
    """
    last = "unknown"
    for _ in range(timeout):
        status, row = call(base, "GET", f"/threads/{tid}", token)
        if status == 200 and isinstance(row, dict):
            last = row.get("status", "unknown")
            if last not in IN_FLIGHT:
                return last
        time.sleep(1)
    return last


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base-url", required=True)
    p.add_argument("--token-a", required=True, help="the identity the inbox uses")
    p.add_argument("--token-b", required=True, help="a second identity, for the isolation control")
    p.add_argument("--graph", default="p3_hitl")
    p.add_argument("--out", help="write the observations here as JSON")
    args = p.parse_args()

    base = args.base_url.rstrip("/")
    out: dict[str, Any] = {"base_url": base, "graph": args.graph}

    # ---------------------------------------------------------------- authentication
    # Three observations, and the third is the one that makes the first two mean anything: a
    # server that refused everything would pass both negative controls.
    status, body = call(base, "POST", "/threads/search", None, {"limit": 1})
    out["no_credential"] = {"status": status, "detail": body}
    if status != 401:
        raise Falsified(
            f"an unauthenticated search returned HTTP {status}, not 401 — the deployment is open, "
            f"so nothing below is a statement about authentication")

    status, _ = call(base, "POST", "/threads/search", "not-the-token", {"limit": 1})
    out["wrong_credential"] = {"status": status}
    if status != 401:
        raise Falsified(f"a wrong credential returned HTTP {status}, not 401")

    status, rows = call(base, "POST", "/threads/search", args.token_a, {"limit": 1})
    out["right_credential"] = {"status": status}
    if status != 200:
        raise Falsified(
            f"the correct credential in x-api-key returned HTTP {status}. Agent Inbox can send no "
            f"other header, so this is the falsifier's first clause")

    # ---------------------------------------------------------------- the interrupt
    tid = interrupted_thread(base, args.token_a, args.graph, {})
    out["thread_id"] = tid
    value = interrupt_value(base, args.token_a, tid)
    out["interrupt_value"] = value

    if not isinstance(value, list):
        raise Falsified(
            f"the interrupt value is a {type(value).__name__}, not a list. contexts/utils.ts:312 "
            f"casts it to HumanInterrupt[] without validating, so the inbox would render a row "
            f"with no action UI and no error")
    if len(value) != 1:
        raise Falsified(f"expected exactly one HumanInterrupt, got {len(value)}")
    first = value[0]
    for key in ("action_request", "config"):
        if key not in first:
            raise Falsified(f"the interrupt has no '{key}'; the inbox tests for exactly these two "
                            f"keys and substitutes an improper_schema placeholder without them")
    out["action"] = first["action_request"].get("action")
    out["config"] = first.get("config")

    # ---------------------------------------------------------------- isolation
    # Aegra scopes threads by `user_id == identity` in the SQL itself, with no reference to any
    # authorization handler. This measures Aegra, not the probe's auth module — see p3_auth.py.
    status, rows_b = call(base, "POST", "/threads/search", args.token_b,
                          {"limit": 50, "status": "interrupted"})
    visible = [r["thread_id"] for r in rows_b] if isinstance(rows_b, list) else []
    out["second_identity_sees"] = visible
    if tid in visible:
        raise Falsified("a second identity can see the first's interrupted thread — the "
                        "deployment authenticates but does not isolate")

    # ---------------------------------------------------------------- the inbox's own search
    status, rows = call(base, "POST", "/threads/search", args.token_a, {
        "offset": 0, "limit": 10, "status": "interrupted",
        "metadata": {"graph_id": args.graph},
    })
    found = [r["thread_id"] for r in rows] if isinstance(rows, list) else []
    out["inbox_search_found"] = found
    if tid not in found:
        raise Falsified(
            "the search Agent Inbox issues — status 'interrupted' plus metadata.graph_id — does "
            "not return the interrupted thread, so the inbox would show 'No threads found'")

    # ---------------------------------------------------------------- the four verbs
    # Each verb gets its own thread: a resumed thread is no longer interrupted, and reusing one
    # would test only the first verb and then four failures.
    action_request = first["action_request"]
    edited = {"action": action_request["action"],
              "args": {k: str(v) for k, v in action_request["args"].items()}}
    edited["args"]["operation"] = "replace"   # an edit the graph can be shown to have received

    payloads: dict[str, dict[str, Any]] = {
        "accept": {"type": "accept", "args": action_request},
        "edit": {"type": "edit", "args": edited},
        "response": {"type": "response", "args": "Rejected: this write needs a WBS node first."},
        "ignore": {"type": "ignore", "args": None},
    }

    out["verbs"] = {}
    for verb in VERBS:
        vtid = interrupted_thread(base, args.token_a, args.graph, {})
        code, _ = resume(base, args.token_a, vtid, args.graph, payloads[verb],
                         stream=verb != "ignore")
        landed = settled(base, args.token_a, vtid)
        _, state = call(base, "GET", f"/threads/{vtid}/state", args.token_a)
        recorded = (state or {}).get("values", {}).get("human_response")
        out["verbs"][verb] = {
            "thread_id": vtid,
            "endpoint": "runs/stream" if verb != "ignore" else "runs",
            "http": code,
            "status_after": landed,
            "graph_received": recorded,
        }
        if landed == "interrupted":
            raise Falsified(f"a '{verb}' HumanResponse did not resume the thread; it is still "
                            f"interrupted after the resume was accepted with HTTP {code}")
        if recorded != [payloads[verb]]:
            raise Falsified(
                f"the graph received {recorded!r} for '{verb}', not the one-element list the "
                f"inbox sends ({[payloads[verb]]!r})")

    out["outcome"] = "protocol holds"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Falsified as exc:
        print(f"\nFALSIFIED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except Fault as exc:
        print(f"\nsetup fault: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
