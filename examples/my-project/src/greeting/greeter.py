"""Compose the first greeting a newly registered customer receives, per REQ-GREET-0001.

Does not send anything. This module produces the text and nothing else — delivery, retries and
the record that a greeting was sent belong to the caller, which is what lets this be tested
without a transport.

The 200 ms budget in REQ-GREET-0001 is a budget for the whole request, not for this function.
Nothing here measures it, and a docstring claiming it did would be a claim no check could
falsify.
"""

from __future__ import annotations

DEFAULT_GREETING = "Welcome"


def greet(name: str, *, greeting: str = DEFAULT_GREETING) -> str:
    """Return the greeting line for one customer, per REQ-GREET-0001.

    Never contacts the network and never reads a clock, so the same name always produces the
    same line. A caller that needs a time-of-day greeting passes one in.

    Raises ValueError on an empty or whitespace-only name rather than substituting a
    placeholder: a greeting addressed to nobody is worse than a failed request, because it
    reaches the customer.
    """
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("a greeting needs a name; an empty one would reach the customer")
    return f"{greeting}, {cleaned}!"
