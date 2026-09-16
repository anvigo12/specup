#!/usr/bin/env python3
"""Validate that approvals bind a human, not just a name.

specup.md s59 reserves a class of decision for a named human: business scope, requirement and
architecture baselines, high-risk acceptance, breaking API changes, security exceptions and
release. s31 adds "generated does not mean approved". Until this module existed, none of that
was checked, and the README said so plainly: an agent could run `approve_edge.py
--by product-owner` exactly as a human could, so `approved` meant "someone took accountability
under this name", never "a human checked this".

This closes that, and the mechanism is the one the README already named as the only real
anchor: `approval.commit` pointing at a signed commit, verified against git.

An approval therefore has a provenance level, exactly as a traceability edge does:

    witnessed   the commit resolves AND its signature verifies against the project's
                allowed signers
    claimed     a name and a date, and nothing tying them to a person

The trust root is a version-controlled project artifact, `.specify/governance/allowed-signers`,
and NOT the operator's global git config. That matters: a trust root a reviewer cannot see in
the diff is one the agent could have written. Signature verification runs with
`-c gpg.ssh.allowedSignersFile=<that file>` so the answer depends only on what is committed.

    validate_approvals.py --json

Exit 0 if every approval in scope holds, 1 if one does not, 2 if the graph will not load or
git is needed and unavailable — a missing git binary is a setup fault, not a governance
failure, and collapsing the two would report a broken environment as a broken project.
"""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Any, Iterable

from openup_model import (
    GraphError,
    Verdict,
    base_parser,
    load_graph,
    record,
    record_warning,
    run,
)

# Where the named humans come from. Authored, never generated: who may decide something is a
# fact about an organisation, and no validator can recompute it.
APPROVAL_MATRIX = ".specify/governance/approval-matrix.md"
DEFAULT_ALLOWED_SIGNERS = ".specify/governance/allowed-signers"

# Governance states at or beyond which an approval must be witnessed. Ordered, so a config
# value names a floor rather than a set.
STATE_ORDER = ["DRAFT", "REVIEW", "APPROVED", "BASELINED", "IMPLEMENTED", "VERIFIED", "ACCEPTED"]

# A markdown table row, split into its cells. The matrix is authored prose, so this stays
# deliberately forgiving — a name a human can read in the table is a name this must find.
_TABLE_ROW = re.compile(r"^\s*\|(?P<body>.*)\|\s*$")
_SEPARATOR = re.compile(r"^[\s|:-]+$")

# Cells that are structure rather than a person.
_NOT_A_NAME = re.compile(
    r"^(?:|-|—|n/?a|tbd|none|who\s+approves|who|decision|gate|rule|recorded\s+as|"
    r"required\s+evidence|what\s+must\s+be\s+recorded|when\s+the\s+remediation\s+is\s+due)$",
    re.IGNORECASE,
)


class GitUnavailable(GraphError):
    """git is needed to verify an approval and is not usable here.

    A GraphError subclass on purpose: `run()` turns it into exit 2. A project whose approvals
    declare commits, evaluated where git cannot answer, has produced no verdict — and saying
    so is different from saying the approvals are bad.
    """


def _git(root, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError as exc:
        raise GitUnavailable("git is not on PATH, and an approval declares a commit") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitUnavailable(f"git did not answer within 30s: {' '.join(args)}") from exc


def _cells(line: str) -> list[str] | None:
    """The cells of one markdown table row, or None if this is not a row."""
    match = _TABLE_ROW.match(line)
    if not match or _SEPARATOR.match(line):
        return None
    return [cell.strip().strip("`*_ ") for cell in match.group("body").split("|")]


def named_humans(root) -> set[str]:
    """Every name the approval matrix records as accountable for something.

    Reads only the "who" column of each table, found by its header. Scraping every cell would
    treat "Business scope" and "security review" as approvers, which would make APV-000 pass on
    the shipped template — the exact opposite of what it is for.

    The matrix ships with those cells blank and says why that matters: "If nobody is named
    here, anyone can override anything and the gate is decorative." **An empty result is a
    finding, not an error**, and APV-000 is where it is reported.
    """
    path = root / APPROVAL_MATRIX
    if not path.is_file():
        return set()

    names: set[str] = set()
    who_column: int | None = None
    lines = path.read_text().splitlines()

    for index, line in enumerate(lines):
        cells = _cells(line)
        if cells is None:
            # A blank line ends a table, so a stale column index cannot leak into the next one.
            if not line.strip():
                who_column = None
            continue

        # A header row is the one a separator row follows. Detecting it any other way reads a
        # body cell containing the word "approvals" as a column heading, and then every
        # subsequent row is read from the wrong column.
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if _TABLE_ROW.match(following) and _SEPARATOR.match(following):
            who_column = next(
                (i for i, cell in enumerate(cells)
                 if cell.lower().startswith("who") or "approve" in cell.lower()),
                None,
            )
            continue

        if who_column is None or who_column >= len(cells):
            # The Overrides table has no "who" heading: its rows are question/answer pairs, and
            # the question is in the first cell. Read the answer beside it.
            if len(cells) == 2 and cells[0].lower().startswith("who"):
                names.update(_split_names(cells[1]))
            continue

        names.update(_split_names(cells[who_column]))

    return names


def _split_names(cell: str) -> set[str]:
    """One matrix cell into the names it holds. A cell may list several, or a standing group."""
    if not cell or _NOT_A_NAME.match(cell):
        return set()
    found = set()
    for candidate in re.split(r",|/| or | and ", cell):
        candidate = candidate.strip().strip("`*_ ")
        if not candidate or candidate.startswith(("GATE-", "REQ-", "ADR-", "RISK-")):
            continue
        if len(candidate.split()) > 6:
            continue
        found.add(candidate)
    return found


def approvals_in_scope(graph) -> list[dict[str, Any]]:
    """Every approval in the graph, tagged with what it approves and that thing's state.

    Two shapes, both defined by `$defs/approval`: an artifact carries a list under `approvals`,
    an edge carries a single object under `approval`. They are collected into one list so a
    check reads "every approval" rather than "every approval on an artifact, and separately".
    """
    found: list[dict[str, Any]] = []

    for artifact_id, artifact in sorted(graph.artifacts.items()):
        for approval in artifact.get("approvals", []) or []:
            found.append({
                "subject": artifact_id,
                "state": artifact.get("status", "DRAFT"),
                "approval": approval,
            })

    for edges in (graph.out.values() if hasattr(graph, "out") else []):
        for edge in edges:
            approval = getattr(edge, "approval", None) or {}
            if approval:
                found.append({
                    "subject": f"{edge.from_id} --{edge.relation}--> {edge.to_id}",
                    "state": "APPROVED",
                    "approval": approval,
                })

    return found


def _at_or_above(state: str, floor: str) -> bool:
    """True when `state` is at or beyond `floor` in the governance state machine."""
    if floor not in STATE_ORDER:
        return False
    if state not in STATE_ORDER:
        return False
    return STATE_ORDER.index(state) >= STATE_ORDER.index(floor)


def validate(args: Any) -> Verdict:
    graph, config = load_graph(args.root)
    verdict = Verdict("validate-approvals")
    root = graph.root

    settings = config.get("approvals", {}) or {}
    signers_path = settings.get("allowed_signers", DEFAULT_ALLOWED_SIGNERS)

    # Off by default, and that is a decision rather than timidity. Defaulting this to BASELINED
    # would fail the first audit of every project that upgrades, over approvals recorded before
    # the field existed — the brownfield failure `existing-project.md` is written against.
    # APV-004 warns on every claimed approval regardless, so the gap is visible from day one;
    # raising the floor is the deliberate act that makes it consequential.
    witness_floor = settings.get("require_witness_at_or_above", None)

    scope = approvals_in_scope(graph)
    humans = named_humans(root)

    # APV-000 — the matrix names somebody.
    #
    # Checked first because every other check is weaker without it. A matrix with an empty
    # "who" column does not constrain anyone, and the template says so in its own words.
    record(
        verdict, "APV-000",
        [] if humans else [
            f"{APPROVAL_MATRIX} names no approver — with the 'who' column blank, anyone can "
            f"approve anything and the matrix is decorative"
        ],
        f"the approval matrix names {len(humans)} approver(s)",
    )

    declared_commits = [entry for entry in scope if entry["approval"].get("commit")]

    # APV-001 — a declared commit resolves to a real commit in this repository.
    resolved: dict[str, bool] = {}
    unresolvable: list[str] = []
    if declared_commits:
        if _git(root, "rev-parse", "--git-dir").returncode != 0:
            raise GitUnavailable(
                f"{root} is not a git repository, and {len(declared_commits)} approval(s) "
                f"declare a commit to verify against"
            )
        for entry in declared_commits:
            sha = entry["approval"]["commit"]
            ok = _git(root, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0
            resolved[sha] = ok
            if not ok:
                unresolvable.append(
                    f"{entry['subject']}: approval names commit {sha}, which is not a commit "
                    f"in this repository"
                )
    record(
        verdict, "APV-001", unresolvable,
        f"every declared approval commit resolves ({len(declared_commits)} checked)",
    )

    # APV-002 — that commit carries a signature that verifies against the project's signers.
    #
    # `-c gpg.ssh.allowedSignersFile` is what makes the trust root the committed file rather
    # than whatever the operator happens to have configured. Without it the same repository
    # would verify differently on two machines, and the check would be about the machine.
    signers = root / signers_path
    unwitnessed: list[str] = []
    witnessed = 0
    if declared_commits and not signers.is_file():
        unwitnessed.append(
            f"{signers_path} does not exist, so no signature can be verified — this file is "
            f"the project's trust root and belongs in version control"
        )
    elif declared_commits:
        for entry in declared_commits:
            sha = entry["approval"]["commit"]
            if not resolved.get(sha):
                continue  # APV-001 already reported it; one defect, one finding.
            result = _git(
                root,
                "-c", f"gpg.ssh.allowedSignersFile={signers}",
                "verify-commit", "--raw", sha,
            )
            if result.returncode == 0:
                witnessed += 1
            else:
                detail = (result.stderr or "").strip().splitlines()
                unwitnessed.append(
                    f"{entry['subject']}: commit {sha} has no signature this project trusts"
                    + (f" — {detail[-1]}" if detail else "")
                )
    record(
        verdict, "APV-002", unwitnessed,
        f"{witnessed} approval(s) are witnessed by a verified signature",
    )

    # APV-003 — the name on an approval is one the matrix records.
    unknown = [
        f"{entry['subject']}: approved by '{entry['approval'].get('by')}', who is not named "
        f"in {APPROVAL_MATRIX}"
        for entry in scope
        if humans and entry["approval"].get("by") not in humans
    ]
    record(
        verdict, "APV-003", unknown,
        f"every approval names someone the matrix records ({len(scope)} checked)",
    )

    # APV-004 — an approval with no commit is claimed, not witnessed.
    #
    # WARN, not FAIL, and the reason is a migration rather than a judgement: `commit` is
    # optional in the schema and existing approvals predate this check. `require_witness_at_or_
    # above` is the ratchet — set it, and the states at or beyond that floor start failing.
    claimed = [
        f"{entry['subject']}: approved by '{entry['approval'].get('by')}' with no commit, so "
        f"nothing ties the approval to a person"
        for entry in scope if not entry["approval"].get("commit")
    ]
    record_warning(
        verdict, "APV-004", claimed,
        f"every approval declares a commit ({len(scope)} checked)",
    )

    # The ratchet. Unlike APV-004 this one fails, and only for the states the project has
    # decided must be witnessed.
    must_witness = [
        entry for entry in scope
        if witness_floor and _at_or_above(entry["state"], witness_floor)
    ]
    unwitnessed_at_floor = [
        f"{entry['subject']} is {entry['state']}, at or above the '{witness_floor}' floor, and "
        f"its approval is claimed rather than witnessed"
        for entry in must_witness
        if not (entry["approval"].get("commit") and resolved.get(entry["approval"]["commit"]))
    ]
    record(
        verdict, "APV-005", unwitnessed_at_floor,
        f"every approval at or above '{witness_floor}' is witnessed "
        f"({len(must_witness)} checked)" if witness_floor
        else "no witness floor is set; approvals.require_witness_at_or_above turns this on",
    )

    verdict.metrics = {
        "approvals": len(scope),
        "witnessed": witnessed,
        "claimed": len(claimed),
        "named_approvers": sorted(humans),
        "witness_floor": witness_floor,
    }
    return verdict


if __name__ == "__main__":
    sys.exit(run(validate, base_parser(__doc__.splitlines()[0])))
