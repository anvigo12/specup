"""Tests for the greeting composer, covering AC-GREET-0001-0001's observable half.

Named `test_greeter.py` on purpose. `test-file-naming-convention` strips the `test_` prefix
and looks for `greeter.py` with the same extension inside the traceability perimeter, so once
this project sits inside a governed root the `tests` edge derives itself.

Does not test the 200 ms budget. That is a property of the deployed service under load, not of
this function, and a unit test asserting it here would pass on a laptop and prove nothing.
"""

from __future__ import annotations

import pytest

from greeting.greeter import greet


def test_a_known_customer_gets_a_personal_line():
    assert greet("Ada") == "Welcome, Ada!"


def test_surrounding_whitespace_is_not_part_of_the_name():
    assert greet("  Ada  ") == "Welcome, Ada!"


def test_an_empty_name_is_refused_rather_than_substituted():
    """The boundary the docstring states, asserted rather than trusted."""
    with pytest.raises(ValueError):
        greet("   ")
