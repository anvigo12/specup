#!/usr/bin/env python3
"""Validate that a docstring is the working context for the unit it documents.

specup.md s56-s57 argues an agent should navigate `directory -> AGENTS.md -> index.md -> the
one artifact it needs` rather than load the repository. validate_context.py checks that
hierarchy down to the file. This checks the last step, inside the file: when an agent opens
one function, its docstring is the whole context it gets, and nothing else will arrive.

Four properties, none of them stylistic:

    anchored   it names a governing artifact, so what the unit is for can be compared with
               what the project decided it should be for (DOC-003)
    bounded    it says what the unit does NOT do, or when it refuses — the half that gets
               omitted, and an agent not told the edge will infer one (DOC-004)
    honest     a claim of corroboration names two distinct sources (DOC-005)
    finite     it fits the context it is supposed to be (DOC-006)

    validate_docs.py --json

Exit 0 if the docstrings hold, 1 if one misleads, 2 if the graph will not load or the project
asks for a check that does not exist.

**Severity.** The manual's rule decides all of it: a missing thing warns, a misleading thing
fails. DOC-002 and DOC-005 fail always and cannot be lowered — a docstring naming a
requirement that no longer exists, or claiming a cross-check it did not perform, sends an
agent somewhere wrong with confidence, which is worse than silence. The rest are gaps. An
existing codebase has thousands of undocumented public symbols, and failing its first audit
over them teaches only that the tool should be switched off. They warn from day one, and
`docs.enforce` is the ratchet a project uses to make its own chosen subset consequential —
the same shape as `approvals.require_witness_at_or_above`, for the same reason.

**Scope.** Python only, via `ast`. There is no parser here for any other language, and a
perimeter file this module cannot read is reported by DOC-000 as not analysed, never as
passing. A validator that silently ignores what it cannot parse reports a clean result about
a project it did not open.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any

from openup_model import (
    SKIP,
    GraphError,
    Verdict,
    base_parser,
    load_graph,
    record,
    record_warning,
    run,
)

# The artifacts a docstring may anchor to. Requirements and non-functional requirements say
# what the unit is for; ADRs and security decisions say why it is shaped the way it is. A WBS
# node is deliberately not here: it names the work, which is finished the moment the code
# exists, and an anchor that goes stale on merge is an anchor nobody maintains.
ANCHOR_ID = re.compile(r"\b(?:NON-FR|REQ|ADR|SECURE)-[A-Z0-9.\-]+\b")

# A docstring that claims its content was checked against something else. This list is the
# vocabulary people actually use when they are asserting independence.
CROSS_CHECK_CLAIM = re.compile(
    r"cross[-\s]?check|independently\s+(?:verif|confirm|deriv|check|transcrib)|"
    r"second\s+(?:source|oracle|reading)|corroborat|oracle",
    re.IGNORECASE,
)

# A named source inside a docstring. Three shapes, because a source is cited three ways in
# practice: as a governed id, as a standard's number, or as a path/symbol in backticks.
STANDARD_REF = re.compile(r"\b[A-Z]{2,}[-\s]?[0-9][0-9.\-]*\b")
BACKTICKED = re.compile(r"`([^`\n]{2,80})`")

# A backticked span counts as a citation only when it carries a digit, a dot or a slash, so
# `TR-03111`, `IEEE 1609.2` and `docs/guide/using-specup.md` count while `raw` and `certificate`
# do not. Docstrings backtick their own parameters constantly, and a parameter name is not a
# second reading of a document: admitting one would let a claim of independence pass on a
# docstring that names a single source, which is the one thing DOC-005 exists to stop.
CITATION_LIKE = re.compile(r"[0-9./]")

# Phrases that state a boundary. Kept narrow on purpose: a generous list would match every
# docstring containing the word "not", and a check that everything passes measures nothing.
BOUNDARY = re.compile(
    r"\b(?:never|must\s+not|does\s+not|do\s+not|cannot|can't|won't|refus\w*|reject\w*|"
    r"rais\w*|is\s+not|are\s+not|no-?op|does\s+nothing|out\s+of\s+scope|not\s+a\b|"
    r"rather\s+than|instead\s+of|only\s+\w+|excludes?|ignores?|leaves?\s+\w+\s+alone)\b",
    re.IGNORECASE,
)

# Checks a project may promote to FAIL with `docs.enforce`. DOC-002 and DOC-005 are absent
# because they already fail and cannot be lowered; DOC-006 is absent on purpose — see below.
RATCHETABLE = {"DOC-001", "DOC-003", "DOC-004"}
ALWAYS_FAIL = {"DOC-002", "DOC-005"}

DEFAULT_MAX_LINES = 40


@dataclass
class Unit:
    """One thing an agent can open on its own, and therefore one working context.

    `name` is how a reader would refer to it — `authenticate`, `Validator.check`, or the
    literal string `module` for the file's own docstring. It is display only and nothing keys
    off it, so renaming a unit cannot change a verdict.
    """

    path: str
    name: str
    lineno: int
    kind: str
    doc: str | None

    @property
    def where(self) -> str:
        """Where a reader should look, in the form an editor will jump to.

        Not an identifier. Two units in different files can never collide here, but nothing
        depends on that: no check keys off this string.
        """
        return f"{self.path}:{self.lineno} {self.name}"


def exported_units(path: str, source: str) -> list[Unit]:
    """Every symbol in one module that another module could reasonably import and call.

    `__all__` decides when a module declares one, because that is what the language says the
    module exports; otherwise a leading underscore is the convention and is honoured. Public
    methods of exported classes are included: a class is not a unit of context, and an agent
    that opens one method gets that method's docstring and no other.

    Dunder methods are excluded. `__init__`, `__eq__` and their kin implement a protocol whose
    contract belongs to Python, not to this project, and demanding a governing anchor on one
    would produce a citation that means nothing.

    Nested functions and classes are excluded: nothing outside can reach them, so they are
    implementation of the unit that contains them and are documented by it.

    Raises SyntaxError. The caller reports the file as not analysed; this function does not
    decide what an unparseable file means.
    """
    tree = ast.parse(source, filename=path)
    units = [Unit(path, "module", 1, "module", ast.get_docstring(tree))]

    declared: set[str] | None = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            continue
        if isinstance(node.value, (ast.List, ast.Tuple)):
            declared = {
                element.value for element in node.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            }

    def is_exported(name: str) -> bool:
        return name in declared if declared is not None else not name.startswith("_")

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if is_exported(node.name):
                units.append(Unit(path, node.name, node.lineno, "function",
                                  ast.get_docstring(node)))
        elif isinstance(node, ast.ClassDef):
            if not is_exported(node.name):
                continue
            units.append(Unit(path, node.name, node.lineno, "class", ast.get_docstring(node)))
            for member in node.body:
                if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if member.name.startswith("_"):
                    continue
                units.append(Unit(path, f"{node.name}.{member.name}", member.lineno,
                                  "method", ast.get_docstring(member)))

    return units


def _normalise(token: str) -> str:
    """One spelling for one source, so citing it twice cannot count as two.

    Case, spacing, hyphens and underscores all go. Over-merging is the safe direction here and
    under-merging is not: two tokens wrongly treated as one makes DOC-005 demand a second
    source that really is distinct, while two spellings of one document wrongly treated as two
    lets a false claim of corroboration through, which is the whole thing the check is for.
    """
    return re.sub(r"[\s\-_]", "", token).upper()


def named_sources(doc: str) -> set[str]:
    """The distinct sources a docstring cites, for DOC-005.

    Counts three citation shapes: a governed id, a standard's designation (`TR-03111`,
    `RFC 9457`, `IEEE 1609.2`), and a backticked span that looks like a document rather than a
    symbol. Every shape goes through the same normaliser, so `TR-03111`, `` `TR-03111` `` and
    `TR 03111` are one source rather than three — a claim of independence made three times over
    one document is the exact failure this exists to catch.

    Governed ids are matched first and removed before the other two patterns run. A governed id
    of the form `REQ-<DOMAIN>-<NNNN>` otherwise yields the anchor AND the tail `<DOMAIN>-<NNNN>`
    as a standard reference, so a docstring citing one requirement would satisfy a check that
    asks for two sources.

    This counts **names**, and cannot judge independence. Two ids in one docstring may still
    be two readings of one page, which is the failure this whole check descends from. What it
    buys is that a claim of corroboration has to say what corroborated what; whether those two
    things are genuinely independent is a human judgement, and an ADR is where it gets
    recorded.
    """
    found = {_normalise(token) for token in ANCHOR_ID.findall(doc)}
    remainder = ANCHOR_ID.sub(" ", doc)
    found |= {_normalise(token) for token in STANDARD_REF.findall(remainder)}
    found |= {_normalise(token) for token in BACKTICKED.findall(remainder)
              if CITATION_LIKE.search(token)}
    return {token for token in found if token}


def _enforced(config: dict[str, Any]) -> set[str]:
    """The checks this project has decided are consequential.

    An unknown id here is exit 2 rather than a shrug. Ignoring it would leave someone
    believing a check is enforced while it quietly is not, and a governance control that is
    off while its config says it is on is worse than one that was never configured.
    """
    requested = list((config.get("docs") or {}).get("enforce", []) or [])
    known = RATCHETABLE | ALWAYS_FAIL
    for check_id in requested:
        if check_id == "DOC-006":
            raise GraphError(
                "docs.enforce lists DOC-006, which cannot be promoted to a failure. A "
                "docstring carrying an argument is an ADR in disguise; failing on its length "
                "makes deleting the reasoning the cheapest fix, and the reasoning is the part "
                "worth keeping. Link the ADR instead."
            )
        if check_id not in known:
            raise GraphError(
                f"docs.enforce names '{check_id}', which is not a check this validator "
                f"implements. Known: {', '.join(sorted(known))}."
            )
    return set(requested) | ALWAYS_FAIL


def _record_at(verdict: Verdict, check_id: str, problems: list[str], ok_message: str,
               enforced: set[str]) -> None:
    """FAIL where the project has ratcheted this check up, WARN where it has not."""
    if check_id in enforced:
        record(verdict, check_id, problems, ok_message)
    else:
        record_warning(verdict, check_id, problems, ok_message)


def validate(args: Any) -> Verdict:
    """Run DOC-000..006 over the Python files inside the traceability perimeter.

    The perimeter is the project's own, from `traceability.perimeter` — this validator does
    not define a second scope. A project that has not put its code in the perimeter gets an
    empty analysis and DOC-000 says so, rather than this module going looking.
    """
    graph, config = load_graph(args.root)
    verdict = Verdict("validate-docs")
    settings = config.get("docs") or {}
    enforced = _enforced(config)
    max_lines = int(settings.get("max_docstring_lines", DEFAULT_MAX_LINES))

    perimeter = graph.perimeter_files()
    units: list[Unit] = []
    not_analysed: list[str] = []

    for relative in perimeter:
        if not relative.endswith(".py"):
            suffix = pathlib.PurePosixPath(relative).suffix or "(no extension)"
            not_analysed.append(f"{relative}: {suffix} is not analysed; this validator reads "
                                f"Python only")
            continue
        try:
            source = (graph.root / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            not_analysed.append(f"{relative}: could not be read — {exc}")
            continue
        try:
            units.extend(exported_units(relative, source))
        except SyntaxError as exc:
            not_analysed.append(f"{relative}: does not parse — {exc.msg} at line {exc.lineno}")

    python_files = sorted({unit.path for unit in units})

    # DOC-000 — what was looked at, and what was not.
    #
    # SKIP rather than PASS whenever anything went unread. A perimeter of TypeScript reported
    # as "PASS" would be a clean result about a project this module never opened.
    if not_analysed:
        verdict.add(
            "DOC-000", SKIP,
            f"{len(not_analysed)} of {len(perimeter)} perimeter file(s) were not analysed",
            not_analysed,
        )
    else:
        verdict.ok("DOC-000",
                   f"every perimeter file was analysed ({len(perimeter)} file(s), "
                   f"{len(units)} exported symbol(s))")

    documented = [unit for unit in units if (unit.doc or "").strip()]

    # DOC-001 — an exported symbol with no docstring.
    _record_at(
        verdict, "DOC-001",
        [f"{unit.where} ({unit.kind}) has no docstring, so opening it gives an agent the "
         f"name and nothing else" for unit in units if not (unit.doc or "").strip()],
        f"every exported symbol carries a docstring ({len(units)} checked)",
        enforced,
    )

    # DOC-002 — a governing id a docstring names must resolve. Always a failure.
    #
    # The same argument as CTX-002, one level down. A docstring pointing at REQ-AUTH-0014 after
    # that requirement was superseded does not merely fail to help: it tells an agent the unit
    # is governed by something, and the agent will not find it and will decide for itself.
    dangling = [
        f"{unit.where}: docstring names {identifier}, which resolves to nothing"
        for unit in documented
        for identifier in sorted(set(ANCHOR_ID.findall(unit.doc)))
        if not graph.exists(identifier)
    ]
    record(verdict, "DOC-002", dangling,
           f"every governing id named in a docstring resolves ({len(documented)} checked)")

    # DOC-003 — the file anchors somewhere.
    #
    # Per file, not per symbol. The graph's unit of implementation is the source path: an
    # `implements` edge runs from a file to a requirement, so the file is where the anchor
    # belongs. Demanding an id on every method would produce citation noise and teach people
    # to paste the same id everywhere, which is an anchor that has stopped meaning anything.
    anchored: set[str] = {
        unit.path for unit in documented
        if any(graph.exists(i) for i in ANCHOR_ID.findall(unit.doc))
    }
    _record_at(
        verdict, "DOC-003",
        [f"{path}: no docstring in this file names a governing artifact, so nothing it "
         f"claims can be compared with what the project decided"
         for path in python_files if path not in anchored],
        f"every analysed file anchors to a governing artifact ({len(python_files)} file(s))",
        enforced,
    )

    # DOC-004 — the docstring says where the unit stops.
    _record_at(
        verdict, "DOC-004",
        [f"{unit.where}: the docstring states no boundary — what it will not do, or when it "
         f"refuses. An agent that is not told the edge will infer one" for unit in documented
         if not BOUNDARY.search(unit.doc)],
        f"every docstring states a boundary ({len(documented)} checked)",
        enforced,
    )

    # DOC-005 — a claim of corroboration names two things. Always a failure.
    #
    # The failure this comes from: a truth table transcribed from a reading of a rule rather
    # than from the page, and a predicate written to cross-check it derived from the same
    # misreading. They agreed, and both were wrong. A docstring that says "cross-checked"
    # while naming one source is making a claim of independence it cannot support, and the
    # reader's whole reason to trust the value is that claim.
    unsupported = []
    for unit in documented:
        if not CROSS_CHECK_CLAIM.search(unit.doc):
            continue
        sources = named_sources(unit.doc)
        if len(sources) < 2:
            unsupported.append(
                f"{unit.where}: the docstring claims a cross-check but names "
                f"{len(sources)} source(s). Two statements only corroborate each other if "
                f"they came from different places — say which two"
            )
    record(verdict, "DOC-005", unsupported,
           f"every cross-check claim names two distinct sources ({len(documented)} checked)")

    # DOC-006 — length. WARN, permanently, and `docs.enforce` refuses to raise it.
    #
    # A long docstring is neither missing nor misleading; it is a smell, and usually a good
    # one — someone wrote down why. Failing on it makes deleting the reasoning the cheapest
    # way to go green, and the reasoning is the part worth keeping. Move it to an ADR and link
    # the ADR, which DOC-003 then anchors to.
    record_warning(
        verdict, "DOC-006",
        [f"{unit.where}: {len(unit.doc.splitlines())} lines, over the {max_lines}-line bound. "
         f"A docstring carrying an argument is an ADR in disguise — link the ADR"
         for unit in documented if len(unit.doc.splitlines()) > max_lines],
        f"every docstring fits the {max_lines}-line bound ({len(documented)} checked)",
    )

    verdict.metrics = {
        "perimeter_files": len(perimeter),
        "python_files": len(python_files),
        "files_not_analysed": len(not_analysed),
        "exported_symbols": len(units),
        "documented": len(documented),
        "anchored_files": len(anchored),
        "enforced": sorted(enforced),
    }
    return verdict


if __name__ == "__main__":
    sys.exit(run(validate, base_parser(__doc__.splitlines()[0])))
