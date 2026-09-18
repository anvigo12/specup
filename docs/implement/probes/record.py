#!/usr/bin/env python3
"""Record the outcome of one assumption probe, and refuse the three ways it gets faked.

Answers  — whether a probe outcome may be written into
           `docs/implement/test-specup-agent-shape-assumptions.md`, and writes it if so.
           The campaign document is the store; this script is the only thing that should
           edit a RESULT block.

Does not — decide whether a probe was run honestly, whether the environment matched the one
           described, or whether the evidence supports the outcome. A reviewer does that.
           It also does not know what an assumption means: it matches probe ids and nothing
           else.

Refuses  — three things, and they are the three ways a campaign like this rots:

           1. An outcome that is not `answered`, `falsified` or `blocked`. There is no
              fourth, and "mostly works" is how a falsified probe becomes a passing one.
           2. A result against a probe with no pre-registered `**Falsified when:**` line.
              A success criterion written after the run can always be read as a pass.
           3. Overwriting a result that already carries an outcome, unless `--supersede`
              is passed, which records the old outcome in the new block rather than
              dropping it.

Governed by `EVID-0009` and the campaign document's section 2. Nothing checks this script.

Exit 0 recorded, 1 refused, 2 the document could not be read or parsed — matching SpecUP's
three-exit-code contract, where 2 is an operator error rather than a governance failure.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parent.parent / "test-specup-agent-shape-assumptions.md"

# The only three outcomes. Adding a fourth is a change to the protocol, not to this list.
OUTCOMES = ("answered", "falsified", "blocked")

_PROBE_HEADING = re.compile(r"^### (P\d+) — (.+)$", re.MULTILINE)
_FALSIFIER = re.compile(r"^\*\*Falsified when:\*\*\s*(.+)$", re.MULTILINE)
_NOT_RUN = "_not run_"


class Refused(Exception):
    """A rule in the protocol said no. Distinct from a setup fault, which exits 2."""


def _read() -> str:
    if not CAMPAIGN.is_file():
        print(f"error: {CAMPAIGN} does not exist", file=sys.stderr)
        raise SystemExit(2)
    return CAMPAIGN.read_text(encoding="utf-8")


def _blocks(text: str) -> dict[str, tuple[int, int]]:
    """Map each probe id to the character span between its RESULT markers."""
    spans: dict[str, tuple[int, int]] = {}
    for start in re.finditer(r"<!-- RESULT (P\d+) -->\n", text):
        pid = start.group(1)
        end = text.find(f"<!-- END RESULT {pid} -->", start.end())
        if end == -1:
            print(f"error: RESULT {pid} has no END marker", file=sys.stderr)
            raise SystemExit(2)
        spans[pid] = (start.end(), end)
    return spans


def _sections(text: str) -> dict[str, dict[str, str]]:
    """Per probe: its title, and its pre-registered falsifier if it has one."""
    heads = list(_PROBE_HEADING.finditer(text))
    out: dict[str, dict[str, str]] = {}
    for i, m in enumerate(heads):
        stop = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[m.end():stop]
        f = _FALSIFIER.search(body)
        out[m.group(1)] = {"title": m.group(2), "falsifier": f.group(1).strip() if f else ""}
    return out


def _outcome_of(block: str) -> str:
    m = re.search(r"^- \*\*Outcome:\*\*\s*(.*)$", block, re.MULTILINE)
    value = (m.group(1).strip() if m else "")
    return "" if value in ("", _NOT_RUN) else value


def status(text: str) -> int:
    sections, spans = _sections(text), _blocks(text)
    width = max((len(s["title"]) for s in sections.values()), default=0)
    for pid in sorted(sections, key=lambda p: int(p[1:])):
        outcome = _outcome_of(text[slice(*spans[pid])]) if pid in spans else "NO BLOCK"
        falsifier = "falsifier" if sections[pid]["falsifier"] else "NO FALSIFIER"
        print(f"{pid:4s} {sections[pid]['title']:{width}s}  "
              f"{outcome or 'not run':10s}  {falsifier}")
    missing = [p for p in sections if not sections[p]["falsifier"]]
    if missing:
        print(f"\n{len(missing)} probe(s) have no pre-registered falsifier: "
              f"{', '.join(sorted(missing))}", file=sys.stderr)
        return 1
    return 0


def record(text: str, args: argparse.Namespace) -> str:
    sections, spans = _sections(text), _blocks(text)
    pid = args.probe.upper()

    if pid not in sections:
        raise Refused(f"{pid} is not a probe in {CAMPAIGN.name}")
    if pid not in spans:
        raise Refused(f"{pid} has no RESULT block to write into")
    if not sections[pid]["falsifier"]:
        raise Refused(
            f"{pid} has no pre-registered '**Falsified when:**' line. Write the falsifier, "
            f"commit it, then run the probe. A criterion written afterwards is not one.")

    start, end = spans[pid]
    previous = _outcome_of(text[start:end])
    if previous and not args.supersede:
        raise Refused(
            f"{pid} already records '{previous}'. Pass --supersede to replace it; the old "
            f"outcome is kept in the new block rather than dropped.")

    lines = [
        f"- **Outcome:** {args.outcome}",
        f"- **Date:** {args.date}",
        f"- **Ran by:** {args.by}",
        f"- **Evidence:** {args.evidence}",
        f"- **What was found:** {args.found}",
    ]
    if previous:
        lines.append(f"- **Supersedes:** an earlier outcome of `{previous}`")
    return text[:start] + "\n".join(lines) + "\n" + text[end:]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--list", action="store_true", help="show every probe and its outcome")
    p.add_argument("--probe", help="the probe id, e.g. P1")
    p.add_argument("--outcome", choices=OUTCOMES, help="one of the three; there is no fourth")
    p.add_argument("--by", default="", help="who ran it")
    p.add_argument("--evidence", default="", help="where the output of the run lives")
    p.add_argument("--found", default="", help="what was found, in one sentence")
    p.add_argument("--date", default=_dt.date.today().isoformat())
    p.add_argument("--supersede", action="store_true", help="replace an existing outcome")
    p.add_argument("--dry-run", action="store_true", help="print the block, write nothing")
    args = p.parse_args()

    text = _read()
    if args.list or not args.probe:
        return status(text)
    if not args.outcome:
        print("error: --outcome is required when --probe is given", file=sys.stderr)
        return 2

    try:
        updated = record(text, args)
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(updated[slice(*_blocks(updated)[args.probe.upper()])], end="")
        return 0

    CAMPAIGN.write_text(updated, encoding="utf-8")
    print(f"recorded {args.probe.upper()}: {args.outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
