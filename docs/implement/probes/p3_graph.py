"""The graph P3 interrupts, and the check that its payload is the shape Agent Inbox reads.

Answers  — nothing on its own. It is the fixture: a graph that pauses on `interrupt()` with a
           payload in the `HumanInterrupt` shape, records verbatim whatever the resume carried,
           and then completes. Everything P3 concludes is read from Aegra and from the browser,
           not from here.

Does not — call a model. There is no LLM in this graph and no provider key anywhere in P3. Aegra
           ships `examples/react_agent_hitl`, which is the obvious fixture and was rejected: it
           only interrupts when the model returns tool calls, and P1's stub answers with a text
           block and `stop_reason: end_turn`, so it would route straight to `__end__`. The probe
           would then have found an empty inbox and the falsifier would have scored that as "the
           interrupt list does not render" — a false falsification caused by the fixture. A graph
           that interrupts unconditionally cannot fail that way.

The one design decision worth defending: `interrupt([request])` passes a **list**.

Agent Inbox's README shows `interrupt(request)` with a bare dict. Its code disagrees with its
README, and against Aegra the code is what runs. Aegra's `Thread` model carries no `interrupts`
field (`models/threads.py:86-91`), so the inbox never takes its primary parsing path and always
falls back to `GET /threads/{id}/state`. That fallback ends at
`contexts/utils.ts:312` with a bare cast:

    return { status: "interrupted", thread, interrupts: lastInterrupt.value as HumanInterrupt[] };

There is no validation on that line. A bare dict is not rejected — it is cast to an array, and
every consumer that then reads `.length` gets `undefined`, which renders as a thread row with no
action UI and no error message anywhere. A probe that sent a dict would see a blank row and would
have to guess whether Aegra, the schema, or the inbox was at fault. Sending a list removes that
confound. The README's shape is recorded in the campaign as a documentation defect rather than
silently worked around.
"""

from __future__ import annotations

import os
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

# The four booleans, all on by default. Every one of Agent Inbox's four response verbs needs its
# own affordance rendered, and a run that switched them off could not exercise the verb it hid.
# The probe overrides this per thread to check the reverse: that a flag set to false removes the
# control it governs.
DEFAULT_CONFIG: dict[str, bool] = {
    "allow_ignore": True,
    "allow_respond": True,
    "allow_edit": True,
    "allow_accept": True,
}

# A distinctive action name, so that the rendered row title can be asserted against a string that
# could not have come from anywhere else. "Interrupt" is what the inbox titles a row it failed to
# parse, so a title that matches this constant is the discriminator between a parsed interrupt and
# the improper-schema placeholder.
DEFAULT_ACTION = "specup_governed_write"

DEFAULT_ARGS: dict[str, Any] = {
    "path": ".specify/traceability/requirements.yaml",
    "operation": "append",
    "requirement_id": "EVID-0012",
}

DEFAULT_DESCRIPTION = (
    "**P3 fixture.** The agent is asking to append one evidence artifact to the governed "
    "traceability registry. This description exists so the probe can assert that markdown "
    "reached the inbox row."
)


def _keep_last(_old: Any, new: Any) -> Any:
    """Last write wins. The graph writes each key at most once per run."""
    return new


class State(TypedDict, total=False):
    """Everything the probe needs to read back out of the thread state.

    `human_response` is written verbatim, with no interpretation. The probe asserts on the exact
    object the inbox sent, and a graph that normalised it first would be hiding the measurement
    inside the instrument.
    """

    action: Annotated[str, _keep_last]
    args: Annotated[dict[str, Any], _keep_last]
    description: Annotated[str, _keep_last]
    interrupt_config: Annotated[dict[str, bool], _keep_last]
    human_response: Annotated[Any, _keep_last]
    resumed: Annotated[bool, _keep_last]


def _payload(state: State) -> dict[str, Any]:
    """Build the one `HumanInterrupt` this graph emits."""
    return {
        "action_request": {
            "action": state.get("action") or DEFAULT_ACTION,
            # `or`, not `is not None`: a state key carrying a reducer is initialised to its
            # type's empty value rather than left absent, so an unset `args` arrives as `{}` and
            # an identity test would emit that empty dict instead of the default. Caught by the
            # self-test below, which printed `"args": {}` on the first run of this file.
            "args": state.get("args") or DEFAULT_ARGS,
        },
        "config": state.get("interrupt_config") or DEFAULT_CONFIG,
        "description": state.get("description") or DEFAULT_DESCRIPTION,
    }


def check_payload_against_upstream() -> str:
    """Compare this file's literal payload with the TypedDicts langgraph ships.

    A probe that hand-writes a schema is testing its author's transcription of that schema. This
    reads the keys upstream declares and compares them with the keys emitted above, so a drift in
    either direction is a startup failure rather than a silently wrong payload.

    It reports rather than raises when the types cannot be found, because their location is
    itself unstable: in langgraph 1.2.11 `langgraph.prebuilt.interrupt` still defines them but
    marks them deprecated and directs the reader to `langchain.agents.interrupt` -- a module that
    does not exist in langchain 1.4.1, which is the version this same stack resolves. A dangling
    deprecation pointer is a finding for the record, not a reason to stop.
    """
    try:
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from langgraph.prebuilt.interrupt import (  # type: ignore[attr-defined]
                ActionRequest,
                HumanInterrupt,
                HumanInterruptConfig,
            )
    except Exception as exc:  # pragma: no cover - reported, never fatal
        return f"upstream types not importable ({type(exc).__name__}: {exc}); payload unchecked"

    emitted = _payload({})
    problems: list[str] = []

    for name, declared, actual in (
        ("HumanInterrupt", HumanInterrupt, emitted),
        ("ActionRequest", ActionRequest, emitted["action_request"]),
        ("HumanInterruptConfig", HumanInterruptConfig, emitted["config"]),
    ):
        want = set(getattr(declared, "__annotations__", {}))
        got = set(actual)
        if got - want:
            problems.append(f"{name}: emits keys upstream does not declare: {sorted(got - want)}")
        missing_required = want - got - {"description"}
        if missing_required:
            problems.append(f"{name}: upstream declares keys not emitted: {sorted(missing_required)}")

    if problems:
        raise RuntimeError("P3 payload does not match upstream's declared shape: " + "; ".join(problems))
    return "payload matches langgraph.prebuilt.interrupt (deprecated there; successor module absent)"


def ask(state: State) -> dict[str, Any]:
    """Pause, and record what came back.

    On resume LangGraph re-executes this node from the top, so nothing above `interrupt()` may
    have a side effect. Building the payload twice is free; writing a file here would not be.
    """
    answer = interrupt([_payload(state)])
    return {"human_response": answer, "resumed": True}


def build() -> Any:
    builder = StateGraph(State)
    builder.add_node("ask", ask)
    builder.add_edge(START, "ask")
    builder.add_edge("ask", END)
    # Aegra supplies a Postgres checkpointer at run time and compiling with one here would be
    # overridden. InMemorySaver is used only when this file is executed directly, below.
    return builder.compile()


graph = build()


if __name__ == "__main__":  # a self-test that needs no server
    import json
    import uuid

    print(check_payload_against_upstream())
    local = StateGraph(State)
    local.add_node("ask", ask)
    local.add_edge(START, "ask")
    local.add_edge("ask", END)
    app = local.compile(checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    first = app.invoke({}, cfg)
    print("interrupted:", json.dumps(first["__interrupt__"][0].value, indent=2, default=str))
    from langgraph.types import Command

    final = app.invoke(Command(resume=[{"type": "accept", "args": None}]), cfg)
    print("resumed with:", json.dumps(final.get("human_response"), default=str))
    assert final.get("resumed") is True, "the graph did not continue past the interrupt"
    print("OK -", os.path.basename(__file__), "interrupts and resumes locally")
