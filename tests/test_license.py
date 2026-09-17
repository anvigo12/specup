"""Keep every manifest's licence field agreeing with the licence that ships.

SpecUP moved from MIT to BUSL-1.1 at 0.1.2, and the licence position is now spread over
ten places: `LICENSE`, `LICENSE-MIT`, seven component manifests, and `docs/dev/licensing.md`.
Nothing in the validators reads any of them. `tools/build_catalog.py` copies `license` into
the published catalog through its `PASSTHROUGH` tuple, whose own comment says the field is
display-only to Spec Kit — so a manifest still saying `MIT` would be republished as a public
statement that SpecUP is MIT, and every existing test would stay green.

That is worse than an ordinary drift. A stale check id in the manual sends a reader to a
command that does not exist; a stale licence string in a distributed artifact is a
representation about terms that somebody may rely on, in a repository whose whole argument is
that unchecked claims are the defect. This file is the check that was missing.

It deliberately does **not** encode which licence is correct. It reads `LICENSE` and requires
the manifests to match it, so the next relicense changes one file and this test follows.
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LICENSE = REPO_ROOT / "LICENSE"
CHANGE_LICENSE = REPO_ROOT / "LICENSE-MIT"

# Every manifest that carries a `license` field, and the key path to it. All seven are
# published: three become catalog entries, four are workflow manifests inside the bundle.
MANIFESTS = [
    "extensions/openup/extension.yml",
    "presets/openup-governance/preset.yml",
    "bundles/specup/bundle.yml",
    "workflows/openup-inception/workflow.yml",
    "workflows/openup-elaboration/workflow.yml",
    "workflows/openup-construction/workflow.yml",
    "workflows/openup-transition/workflow.yml",
]

# The first line of a licence file, mapped to the SPDX identifier a manifest must carry.
# Keyed on text rather than on a constant so that replacing LICENSE is the only edit a
# future relicense needs, and an unrecognised licence fails loudly instead of passing.
SPDX_BY_FIRST_LINE = {
    "Business Source License 1.1": "BUSL-1.1",
    "MIT License": "MIT",
    "Apache License": "Apache-2.0",
}


def declared_licence() -> str:
    """The SPDX id for whatever `LICENSE` actually contains."""
    first = LICENSE.read_text().strip().splitlines()[0].strip()
    assert first in SPDX_BY_FIRST_LINE, (
        f"LICENSE starts with {first!r}, which this test does not recognise.\n"
        f"Add it to SPDX_BY_FIRST_LINE with its SPDX identifier. Do not delete this "
        f"assertion to make a relicense land — the mapping is the point."
    )
    return SPDX_BY_FIRST_LINE[first]


def licence_field(path: pathlib.Path):
    """Manifests nest the field under a top-level section whose name varies by kind."""
    data = yaml.safe_load(path.read_text()) or {}
    if "license" in data:
        return data["license"]
    for section in data.values():
        if isinstance(section, dict) and "license" in section:
            return section["license"]
    return None


@pytest.mark.parametrize("relative", MANIFESTS, ids=lambda p: p.split("/")[-2])
def test_every_manifest_declares_the_licence_that_ships(relative):
    path = REPO_ROOT / relative
    assert path.is_file(), f"{relative} is missing; the manifest list in this test is stale"
    found = licence_field(path)
    assert found == declared_licence(), (
        f"{relative} declares license: {found!r}, but LICENSE is {declared_licence()!r}.\n"
        f"Spec Kit republishes this string verbatim, so the catalog would state the wrong "
        f"terms."
    )


def test_the_change_license_named_in_LICENSE_is_present_on_disk():
    """BUSL converts to a Change License, and a reader must be able to read those terms.

    `LICENSE` names MIT and says the conversion is automatic. If the text of the Change
    License is not in the repository, the promise is unreadable at exactly the moment it
    matters.
    """
    if declared_licence() != "BUSL-1.1":
        pytest.skip("not under BUSL; no Change License to resolve")
    body = LICENSE.read_text()
    assert "Change License:       MIT License" in body, (
        "the Change License parameter is not the MIT License. BUSL covenant 1 requires a "
        "GPL-2.0-compatible Change License, and Apache-2.0 is not one."
    )
    assert CHANGE_LICENSE.is_file(), "LICENSE-MIT is missing"
    assert "MIT License" in CHANGE_LICENSE.read_text()


def test_the_busl_parameters_are_all_filled_in():
    """An unfilled parameter is the BUSL failure mode: the template ships with placeholders
    and a licence with an empty Change Date grants nothing anybody can rely on."""
    if declared_licence() != "BUSL-1.1":
        pytest.skip("not under BUSL")
    body = LICENSE.read_text()
    for parameter in ("Licensor:", "Licensed Work:", "Additional Use Grant:",
                      "Change Date:", "Change License:"):
        line = next((l for l in body.splitlines() if l.startswith(parameter)), None)
        assert line is not None, f"LICENSE has no {parameter} line"
        value = line[len(parameter):].strip()
        assert value and "[" not in value, (
            f"{parameter} is empty or still holds a placeholder: {line!r}"
        )


def test_the_readme_says_plainly_that_this_is_not_open_source():
    """BUSL is source-available, and the README must say so in those words.

    The first version of this test searched the README for "open source" and failed if it
    appeared. That was the wrong shape twice over: it fired on the disclaimer itself, and it
    could never have distinguished a false claim from a quotation or a denial. Reading prose
    for a claim that is absent does not work.

    So it asserts the opposite — that the disclaimer is present. A positive string is
    checkable; "nothing anywhere in this file misleads" is not, and pretending otherwise
    would be the decorative kind of check this project rejects.
    """
    if declared_licence() in ("MIT", "Apache-2.0"):
        pytest.skip("permissive licence; no disclaimer needed")
    readme = (REPO_ROOT / "README.md").read_text().lower()
    assert "source-available, not open source" in readme, (
        f"LICENSE is {declared_licence()}, which is not OSI-approved, and README.md does not "
        f"contain the phrase 'source-available, not open source'. A reader deciding whether "
        f"they may use this needs that stated, not inferred from the licence name."
    )
