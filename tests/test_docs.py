"""A docstring is the whole working context for the unit it documents.

specup.md s56-s57 argues an agent should navigate `directory -> AGENTS.md -> index.md -> the
one artifact`, and `validate_context.py` checks that hierarchy down to the file. This suite
covers the step below it: when an agent opens one function, its docstring is everything it
gets, so the docstring has to be anchored, bounded, honest and finite.

Every test writes its own Python module into a copy of the good fixture rather than adding one
to the fixture itself. That is deliberate: the fixture's perimeter is two TypeScript files and
two `implements` edges, so a third permanently-tracked source file would drop backward coverage
to 0.67 and break `validate_trace`'s tests instead. A per-test module also states the exact
docstring under test next to the assertion about it.
"""

from __future__ import annotations

import textwrap

import pytest

from conftest import assert_fails, failing

# A module that satisfies every check, so each test can break exactly one property. It anchors
# (REQ-AUTH-0014 is in the fixture registry), states a boundary twice, claims no cross-check,
# and is far inside the length bound.
SOUND = '''
"""Verify a vehicle certificate chain, per REQ-AUTH-0014.

Does not check revocation: that is a separate unit under its own requirement.
"""


def verify_chain(certificate):
    """Report whether the chain terminates in a trusted root.

    Never contacts the network. A caller that needs revocation state fetches it first and
    passes it in.
    """
    return bool(certificate)
'''


def module(project, source: str, relative: str = "src/auth/chain.py") -> None:
    """Write one Python module into the project's perimeter."""
    path = project.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source).lstrip())


def only_python(project) -> None:
    """Remove the fixture's TypeScript, so DOC-000 has nothing left to report as unread."""
    for relative in ("src/auth/authentication_service.ts",
                     "src/security/certificate_validator.ts",
                     "src/security/certificate_validator.test.ts"):
        (project.root / relative).unlink()


def enforce(project, *check_ids: str) -> None:
    project.config(lambda c: c.setdefault("docs", {}).__setitem__("enforce", list(check_ids)))


def check(verdict, check_id: str):
    found = next((c for c in verdict.checks if c.id == check_id), None)
    assert found is not None, f"{check_id} was not reported at all"
    return found


# -- DOC-000: what was read, and what was not ------------------------------------------


def test_a_typescript_perimeter_is_reported_as_unread_never_as_passing(project):
    """The fixture untouched. This validator reads Python and the fixture has none.

    A PASS here would be a clean result about files nothing opened, which is the single
    dishonesty a validator scoped to one language can commit.
    """
    verdict = project.run("validate_docs")
    assert check(verdict, "DOC-000").status == "SKIP"
    assert verdict.metrics["python_files"] == 0
    assert verdict.metrics["files_not_analysed"] == 2
    assert all(".ts is not analysed" in item for item in check(verdict, "DOC-000").evidence)


def test_doc_000_passes_once_every_perimeter_file_was_read(project):
    """The SKIP is a statement about coverage, not a permanent condition."""
    only_python(project)
    module(project, SOUND)
    verdict = project.run("validate_docs")
    assert check(verdict, "DOC-000").status == "PASS"
    assert verdict.metrics == {
        "perimeter_files": 1, "python_files": 1, "files_not_analysed": 0,
        "exported_symbols": 2, "documented": 2, "anchored_files": 1,
        "enforced": ["DOC-002", "DOC-005"],
    }


def test_a_file_that_does_not_parse_is_unread_rather_than_clean(project):
    """A syntax error must not silently shrink the population every other check runs over."""
    module(project, "def verify_chain(:\n    pass\n")
    verdict = project.run("validate_docs")
    assert check(verdict, "DOC-000").status == "SKIP"
    assert any("does not parse" in item for item in check(verdict, "DOC-000").evidence)
    assert verdict.metrics["exported_symbols"] == 0


# -- DOC-001: an exported symbol carries a docstring -----------------------------------


UNDOCUMENTED = '''
"""Verify a vehicle certificate chain, per REQ-AUTH-0014.

Does not check revocation.
"""


def verify_chain(certificate):
    return bool(certificate)
'''


def test_an_undocumented_export_warns_by_default(project):
    """A gap, not a lie. An existing codebase has thousands of these and failing its first
    audit over them teaches only that the validator should be switched off."""
    module(project, UNDOCUMENTED)
    verdict = project.run("validate_docs")
    assert verdict.status == "PASS"
    assert check(verdict, "DOC-001").status == "WARN"
    assert any("verify_chain" in item for item in check(verdict, "DOC-001").evidence)


def test_docs_enforce_turns_the_warning_into_a_failure(project):
    """The ratchet, with nothing changed but the config — the same shape as
    `approvals.require_witness_at_or_above`, for the same reason."""
    module(project, UNDOCUMENTED)
    enforce(project, "DOC-001")
    assert_fails(project.run("validate_docs"), "DOC-001")


def test_a_private_symbol_is_not_an_export(project):
    """Nothing outside can import it, so its docstring is not anyone's working context."""
    module(project, SOUND + "\n\ndef _decode(raw):\n    return raw\n")
    assert project.run("validate_docs").metrics["exported_symbols"] == 2


def test_dunder_all_decides_the_export_set(project):
    """When a module says what it exports, that is the answer — not the underscore convention.

    `helper` is public by naming and excluded by `__all__`; the check must follow the
    declaration, or a module that narrowed its surface gets punished for it.
    """
    module(project, SOUND + '\n\n__all__ = ["verify_chain"]\n\n\ndef helper(x):\n    return x\n')
    verdict = project.run("validate_docs")
    assert verdict.metrics["exported_symbols"] == 2
    assert check(verdict, "DOC-001").status == "PASS"


def test_a_public_method_is_its_own_working_context(project):
    """A class is not a unit of context: an agent that opens one method gets that docstring
    and no other, so the method is where the requirement has to be legible."""
    module(project, SOUND + '''

class ChainVerifier:
    """Hold the trust roots for repeated verification.

    Does not fetch roots; they are passed in.
    """

    def __init__(self, roots):
        self.roots = roots

    def verify(self, certificate):
        return bool(certificate)
''')
    verdict = project.run("validate_docs")
    assert any("ChainVerifier.verify" in item for item in check(verdict, "DOC-001").evidence)
    assert not any("__init__" in item for item in check(verdict, "DOC-001").evidence)


def test_a_nested_function_is_implementation_not_an_export(project):
    """Nothing outside can reach it, so the enclosing unit's docstring documents it."""
    module(project, SOUND + "\n\ndef _outer():\n    def inner():\n        return 1\n    return inner\n")
    assert project.run("validate_docs").metrics["exported_symbols"] == 2


# -- DOC-002: a governing id that resolves. Always a failure ---------------------------


def test_a_docstring_naming_a_requirement_that_does_not_exist_fails(project):
    """CTX-002's argument, one level down. This does not merely fail to help: it tells an
    agent the unit is governed by something, and the agent will not find it and will decide
    for itself."""
    module(project, SOUND.replace("REQ-AUTH-0014", "REQ-AUTH-9999"))
    verdict = project.run("validate_docs")
    assert_fails(verdict, "DOC-002")
    assert any("REQ-AUTH-9999" in item for item in check(verdict, "DOC-002").evidence)


def test_doc_002_fails_with_an_empty_enforce_list(project):
    """It is not ratchetable. A dangling anchor is misleading, and misleading always fails."""
    module(project, SOUND.replace("REQ-AUTH-0014", "REQ-AUTH-9999"))
    enforce(project)
    assert_fails(project.run("validate_docs"), "DOC-002")


def test_docs_enforce_cannot_name_doc_002_or_doc_005(project):
    """Listing something that already fails changes nothing, and must not read as an error."""
    module(project, SOUND)
    enforce(project, "DOC-002", "DOC-005")
    assert project.run("validate_docs").status == "PASS"


# -- DOC-003: the file anchors somewhere -----------------------------------------------


def test_a_file_that_anchors_to_nothing_warns_and_ratchets(project):
    module(project, SOUND.replace(", per REQ-AUTH-0014", ""))
    verdict = project.run("validate_docs")
    assert check(verdict, "DOC-003").status == "WARN"
    assert verdict.metrics["anchored_files"] == 0

    enforce(project, "DOC-003")
    assert_fails(project.run("validate_docs"), "DOC-003")


def test_the_anchor_is_required_per_file_not_per_symbol(project):
    """The graph's unit of implementation is the source path: an `implements` edge runs from a
    file to a requirement. Demanding an id on every method would teach people to paste the same
    id everywhere, which is an anchor that has stopped meaning anything."""
    module(project, SOUND)
    verdict = project.run("validate_docs")
    assert check(verdict, "DOC-003").status == "PASS"
    assert verdict.metrics["anchored_files"] == 1


def test_an_adr_anchors_a_file_as_well_as_a_requirement(project):
    """A requirement says what the unit is for; an ADR says why it is shaped that way. Both
    are things the unit can be compared against."""
    module(project, SOUND.replace("per REQ-AUTH-0014", "per ADR-0019"))
    assert check(project.run("validate_docs"), "DOC-003").status == "PASS"


def test_a_dangling_anchor_does_not_also_count_as_an_anchor(project):
    """Otherwise the cheapest way to satisfy DOC-003 would be to invent an id."""
    module(project, SOUND.replace("REQ-AUTH-0014", "REQ-AUTH-9999"))
    verdict = project.run("validate_docs")
    assert verdict.metrics["anchored_files"] == 0
    assert check(verdict, "DOC-003").status == "WARN"


# -- DOC-004: the docstring says where the unit stops ----------------------------------


def test_a_docstring_with_no_boundary_warns_and_ratchets(project):
    """The boundary is the half that gets omitted and the half that matters: an agent that is
    not told the edge will infer one."""
    module(project, '''
    """Verify a vehicle certificate chain, per REQ-AUTH-0014."""


    def verify_chain(certificate):
        """Report whether the chain terminates in a trusted root."""
        return bool(certificate)
    ''')
    verdict = project.run("validate_docs")
    assert check(verdict, "DOC-004").status == "WARN"
    assert len(check(verdict, "DOC-004").evidence) == 2

    enforce(project, "DOC-004")
    assert_fails(project.run("validate_docs"), "DOC-004")


def test_the_boundary_vocabulary_is_narrow_enough_to_mean_something(project):
    """A list generous enough to match any docstring containing "not" would measure nothing.

    This docstring is ordinary prose with no stated edge, and has to fail the heuristic — the
    check is only worth its warnings if a description alone does not satisfy it.
    """
    import validate_docs

    assert not validate_docs.BOUNDARY.search(
        "Report whether the chain terminates in a trusted root, using the configured roots."
    )
    assert validate_docs.BOUNDARY.search("Never contacts the network.")
    assert validate_docs.BOUNDARY.search("Raises GraphError when the trust root is absent.")


# -- DOC-005: a claim of corroboration names two things. Always a failure ---------------


CROSS_CHECKED = '''
"""Decode the SSP bitmap, per REQ-AUTH-0014.

Does not validate the certificate the bitmap came from.
"""


def decode_ssp(raw):
    """Return the permission set encoded in `raw`.

    The truth table here was cross-checked against {sources}, and refuses any bit the table
    does not define.
    """
    return raw
'''


def test_a_cross_check_claim_naming_one_source_fails(project):
    """The `cits-crypto` failure, generalised. A truth table was transcribed from a reading of
    a rule rather than from the page, and the predicate written to cross-check it came from the
    same misreading. They agreed, and both were wrong."""
    module(project, CROSS_CHECKED.format(sources="`TR-03111`"))
    verdict = project.run("validate_docs")
    assert_fails(verdict, "DOC-005")
    assert any("names 1 source" in item for item in check(verdict, "DOC-005").evidence)


def test_two_distinct_sources_satisfy_the_claim(project):
    module(project, CROSS_CHECKED.format(sources="`TR-03111` and `IEEE 1609.2`"))
    verdict = project.run("validate_docs")
    assert check(verdict, "DOC-005").status == "PASS"


def test_one_document_cited_three_ways_is_still_one_source(project):
    """The defect this check exists to catch, wearing the check's own clothes.

    `TR-03111`, TR 03111 and `TR-03111` again are one document. Counting spellings rather than
    sources would let a claim of independence pass while naming a single page — which is
    precisely how the truth table agreed with itself.
    """
    module(project, CROSS_CHECKED.format(sources="`TR-03111`, TR 03111 and `TR 03111`"))
    assert_fails(project.run("validate_docs"), "DOC-005")


def test_the_governing_anchor_is_not_counted_as_a_second_source(project):
    """`REQ-AUTH-0014` yields the tail `AUTH-0014` to a standard-reference pattern, so a
    docstring citing one requirement would otherwise satisfy a check asking for two."""
    module(project, CROSS_CHECKED.format(sources="REQ-AUTH-0014"))
    assert_fails(project.run("validate_docs"), "DOC-005")


def test_a_docstring_claiming_nothing_is_never_asked_for_sources(project):
    """The check reads a claim, not a topic. Silence is not a claim of independence."""
    module(project, SOUND)
    assert check(project.run("validate_docs"), "DOC-005").status == "PASS"


# -- DOC-006: length warns, permanently ------------------------------------------------


def test_a_long_docstring_warns_and_never_fails(project):
    """Neither missing nor misleading. Failing on length makes deleting the reasoning the
    cheapest way to go green, and the reasoning is the part worth keeping."""
    body = "\n".join(f"    Line {n} of the argument." for n in range(45))
    module(project, f'''
"""Verify a vehicle certificate chain, per REQ-AUTH-0014.

Does not check revocation.
"""


def verify_chain(certificate):
    """Report whether the chain terminates in a trusted root.

    Never contacts the network.

{body}
    """
    return bool(certificate)
''')
    verdict = project.run("validate_docs")
    assert verdict.status == "PASS"
    assert check(verdict, "DOC-006").status == "WARN"
    assert any("over the 40-line bound" in item for item in check(verdict, "DOC-006").evidence)


def test_the_length_bound_is_the_project_s_to_set(project):
    module(project, SOUND)
    project.config(lambda c: c.setdefault("docs", {}).__setitem__("max_docstring_lines", 2))
    verdict = project.run("validate_docs")
    assert check(verdict, "DOC-006").status == "WARN"
    assert any("over the 2-line bound" in item for item in check(verdict, "DOC-006").evidence)


def test_doc_006_cannot_be_ratcheted_and_says_why(project):
    """Exit 2, not a quiet demotion. A project asking for something this validator refuses to
    do needs to be told, not to have its config partly honoured."""
    module(project, SOUND)
    enforce(project, "DOC-006")
    assert project.script_rc("validate_docs.py", "--json") == 2


# -- the exit contract -----------------------------------------------------------------


def test_an_unknown_check_id_in_docs_enforce_exits_2(project):
    """A governance control that is off while its config says it is on is worse than one
    nobody configured."""
    enforce(project, "DOC-042")
    assert project.script_rc("validate_docs.py", "--json") == 2


def test_the_good_fixture_exits_0(project):
    """Nothing about adopting this validator breaks a project that has no Python."""
    assert project.script_rc("validate_docs.py", "--json") == 0


def test_a_misleading_docstring_exits_1_not_2(project):
    """A governance failure, on the governance path."""
    module(project, SOUND.replace("REQ-AUTH-0014", "REQ-AUTH-9999"))
    assert project.script_rc("validate_docs.py", "--json") == 1


# -- the audit -------------------------------------------------------------------------


def test_the_audit_carries_the_docs_section(project):
    """The audit is what a workflow runs, so a check absent from it cannot halt a release."""
    import audit

    class Args:
        root = str(project.root)
        json = False

    report, code = audit.audit(Args())
    assert "docs" in report["sections"]
    assert audit.render(report).count("Docstrings") == 1


def test_a_dangling_docstring_anchor_halts_the_audit(project):
    """`audit.fail_on` names it so the Reasons block says which docstring pointed at what,
    rather than leaving a reader to find it in the docs section."""
    module(project, SOUND.replace("REQ-AUTH-0014", "REQ-AUTH-9999"))

    class Args:
        root = str(project.root)
        json = False

    import audit

    report, code = audit.audit(Args())
    assert code == 1
    assert any("dangling_docstring_anchor" in reason for reason in report["reasons"])


# -- this project's own validators -----------------------------------------------------


def test_every_shipped_script_parses_and_carries_a_module_docstring():
    """The one docstring property this repository already holds, asserted rather than assumed.

    Deliberately not asserted here: DOC-001 over every exported symbol, and DOC-003 anchoring.
    Both are currently untrue of SpecUP's own scripts — a large number of `validate`, `main`
    and dataclass methods carry no docstring, and there are no requirement ids to anchor to
    because `.specify/` holds caches and nothing else. Writing a green test over either would
    be the defect this project exists to reject; they are workstream 5's, and the audit's own
    Docstrings block is where the real figure will be read off.

    What this does assert is the floor: the validator can read the repository that ships it,
    and every file offers an agent something when it is opened.
    """
    import validate_docs
    from conftest import SCRIPTS

    missing = []
    for path in sorted(SCRIPTS.glob("*.py")):
        units = validate_docs.exported_units(path.name, path.read_text())
        missing += [u.where for u in units if u.kind == "module" and not (u.doc or "").strip()]
    assert missing == []


def test_no_shipped_docstring_claims_a_cross_check_it_cannot_support():
    """DOC-005 applied to this repository. It fails always and cannot be switched off, so it
    is the one check whose own source has no excuse for breaking it."""
    import validate_docs
    from conftest import SCRIPTS

    unsupported = []
    for path in sorted(SCRIPTS.glob("*.py")):
        for unit in validate_docs.exported_units(path.name, path.read_text()):
            doc = unit.doc or ""
            if validate_docs.CROSS_CHECK_CLAIM.search(doc):
                if len(validate_docs.named_sources(doc)) < 2:
                    unsupported.append(unit.where)
    assert unsupported == []
