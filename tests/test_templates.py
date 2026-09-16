"""Every shipped template explains itself, and says what does not check it.

A template that does not draw its own boundary gets filled with whatever the author had
nearby. So each one carries the same five-part frame, in the same words, so that a reader who
has met it once recognises it everywhere:

    ANSWERS               what question this file settles
    DOES NOT ANSWER       and which file settles the rest
    FILLED IN BADLY WHEN  the failure mode, named specifically — not "be thorough"
    CHECKED BY            the check id, and what it does *not* verify
    AUTHORITY             who decides this is done

The fourth slot is the one that earns the set. Most of what these documents ask for is
enforced by nobody, and a template that leaves that implied teaches a reader to treat a
passing audit as a review. Saying "nothing checks this" in the document itself is the only
place that lands.

These tests are shaped like `test_preset.py`'s `test_guidance_forbids_the_gate_bypasses`: the
value of the writing is that it is there, so its absence has to break a test rather than pass
review as a tidy-up.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "extensions" / "openup" / "templates"

FRAME = ("ANSWERS", "DOES NOT ANSWER", "FILLED IN BADLY WHEN", "CHECKED BY", "AUTHORITY")


def templates() -> list[pathlib.Path]:
    return sorted(p for p in TEMPLATE_DIR.glob("*.*") if p.is_file())


def skills() -> list[pathlib.Path]:
    return sorted(TEMPLATE_DIR.glob("skills/*/SKILL.md"))


def normalised(path: pathlib.Path) -> str:
    """The file as one uppercase string, with markdown emphasis and comment markers gone.

    The frame is written as `**Answers**` in Markdown and `# ANSWERS` in YAML, because each
    has to read naturally in its own format. Only the words are the contract.
    """
    return path.read_text().replace("*", "").replace("#", " ").upper()


@pytest.mark.parametrize("path", templates(), ids=lambda p: p.name)
def test_every_template_carries_the_frame(path):
    text = normalised(path)
    missing = [slot for slot in FRAME if slot not in text]
    assert not missing, f"{path.name} is missing: {missing}"


@pytest.mark.parametrize("path", skills(), ids=lambda p: p.parent.name)
def test_every_skill_says_how_it_goes_wrong_and_what_checks_it(path):
    """Skills carry the two slots that are not already answered by their own structure.

    `Purpose` and the `AGENTS.md`/`SKILL.md` split cover what the file answers and what it
    does not, and authority lives in the approval matrix rather than per activity. What a
    procedure cannot get from its own headings is the way it is done badly, and which check
    would notice.
    """
    text = normalised(path)
    for slot in ("DONE BADLY WHEN", "CHECKED BY"):
        assert slot in text, f"skills/{path.parent.name} is missing: {slot}"


@pytest.mark.parametrize("path", templates() + skills(),
                         ids=lambda p: p.name if p.name != "SKILL.md" else p.parent.name)
def test_every_template_admits_something_is_unchecked(path):
    """The slot that stops the frame becoming decoration.

    Every one of these documents asks for something no validator reads — prose, judgement,
    whether a probability is true, whether the work is the right work. A "checked by" section
    listing only the checks that do exist would read as a complete account and would not be
    one, and a reader takes a passing audit for a review.
    """
    text = normalised(path)
    assert "NOTHING" in text or "NONE OF" in text or "NEITHER" in text, (
        f"{path.name} names what checks it but never what does not. If this template really "
        f"is fully checked, say which check covers the judgement in it."
    )


def test_the_frame_vocabulary_is_the_same_everywhere():
    """One reader, one vocabulary.

    A frame spelled five ways is five frames, and a reader stops recognising it. This catches
    the near-miss that review does not: 'WHAT CHECKS IT' and 'CHECKED BY' say the same thing
    and only one of them is greppable across the set.
    """
    near_misses = ("WHAT CHECKS IT", "WHERE AUTHORITY SITS", "HOW YOU CAN TELL THIS IS WRONG",
                   "WHAT QUESTION THIS ANSWERS")
    for path in templates() + skills():
        text = normalised(path)
        found = [phrase for phrase in near_misses if phrase in text]
        assert not found, f"{path.name} uses an older frame label: {found}"
