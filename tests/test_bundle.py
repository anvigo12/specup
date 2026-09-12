"""Validate the specup bundle.

Two layers, matching test_workflows.py:

1. Rules transcribed from spec-kit v1.0.6's own manifest model
   (`specify_cli/bundler/models/manifest.py`) so the bundle is checked even where
   spec-kit is not installed.
2. The real `BundleManifest` parser and validator when `specify-cli` is importable,
   skipped rather than faked when it is absent.

The check that earns this file's existence is `test_pinned_versions_match_the_components`.
A bundle's only real promise is "these components, at these versions, work together". A pin
that has drifted from the component it names breaks that promise silently: the manifest
still validates, still builds, still installs, and documents a combination nobody ever built.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE_DIR = REPO_ROOT / "bundles" / "specup"
MANIFEST_PATH = BUNDLE_DIR / "bundle.yml"
INSTALLER_PATH = BUNDLE_DIR / "install.py"

# Transcribed from specify_cli/bundler/models/manifest.py.
SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
PRESET_STRATEGIES = {"replace", "prepend", "append", "wrap"}
COMPONENT_KINDS = ("extensions", "presets", "steps", "workflows")
SAFE_BUNDLE_ID = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")
SEMVER = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")

# kind -> (repo directory, component manifest filename, that manifest's root key)
KIND_LAYOUT = {
    "extensions": ("extensions", "extension.yml", "extension"),
    "presets": ("presets", "preset.yml", "preset"),
    "workflows": ("workflows", "workflow.yml", "workflow"),
}

# The version this bundle was actually exercised against. requires.speckit_version
# must admit it, or the bundle refuses to install on the only setup known to work.
VERIFIED_SPECKIT_VERSION = "1.0.6"

try:
    from specify_cli.bundler.models.manifest import BundleManifest
    from specify_cli.bundler.services.validator import validate_manifest
    from specify_cli.bundler.lib.versioning import satisfies

    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text())


@pytest.fixture(scope="module")
def components(manifest) -> list[tuple[str, dict]]:
    """Every declared component as (kind, entry), in the manifest's own order."""
    provides = manifest.get("provides", {})
    return [(kind, entry) for kind in COMPONENT_KINDS for entry in provides.get(kind) or []]


def component_version_on_disk(kind: str, component_id: str) -> str:
    directory, manifest_name, root_key = KIND_LAYOUT[kind]
    path = REPO_ROOT / directory / component_id / manifest_name
    data = yaml.safe_load(path.read_text())
    return str(data[root_key]["version"]).strip()


# -- manifest shape --------------------------------------------------------


def test_bundle_block_is_complete(manifest):
    assert manifest["schema_version"] in SUPPORTED_SCHEMA_VERSIONS
    bundle = manifest["bundle"]
    for field in ("id", "name", "version", "role", "description", "author", "license"):
        value = bundle.get(field)
        assert value and str(value).strip(), f"bundle.{field} is required and must be non-empty"
    assert SAFE_BUNDLE_ID.match(bundle["id"]), (
        f"bundle.id {bundle['id']!r} is interpolated into the artifact filename; it must be a slug"
    )
    assert SEMVER.match(bundle["version"]), f"bundle.version {bundle['version']!r} is not semver"


def test_requires_declares_a_speckit_version(manifest):
    constraint = manifest.get("requires", {}).get("speckit_version")
    assert constraint, "requires.speckit_version is required; without it any version installs"


def test_requires_tools_is_a_list_of_strings(manifest):
    """A bundle's `tools` is string[], unlike an extension.yml's list of mappings.
    A mapping here raises BundlerError at parse time rather than failing validation."""
    tools = manifest.get("requires", {}).get("tools")
    if tools is None:
        return
    assert isinstance(tools, list)
    assert all(isinstance(t, str) for t in tools), "requires.tools must be plain strings"


def test_entries_are_pinned_to_valid_semver(components):
    for kind, entry in components:
        assert entry.get("id"), f"a {kind[:-1]} entry has no id"
        if kind == "steps":
            continue  # steps are the one kind spec-kit lets go unpinned
        version = entry.get("version")
        assert version, f"{kind[:-1]} '{entry['id']}' must be pinned to a version"
        assert SEMVER.match(version), f"{kind[:-1]} '{entry['id']}': {version!r} is not semver"


def test_presets_declare_priority_and_strategy(manifest):
    """spec-kit requires both on every preset entry; a missing one is a structural error."""
    for entry in manifest["provides"].get("presets") or []:
        assert isinstance(entry.get("priority"), int), (
            f"preset '{entry['id']}' must declare an integer priority"
        )
        assert entry.get("strategy") in PRESET_STRATEGIES, (
            f"preset '{entry['id']}': strategy must be one of {sorted(PRESET_STRATEGIES)}"
        )


def test_bundle_pins_no_integration(manifest):
    """Pinning one would make the bundle refuse to install into a project using any other.
    Every SpecUP command is plain markdown and every check is a shell step, so there is
    nothing integration-specific to pin."""
    assert "integration" not in manifest, (
        "SpecUP is integration-agnostic; pinning one only creates install failures"
    )


# -- the pin contract ------------------------------------------------------


def test_pinned_versions_match_the_components(components):
    """The one that matters.

    spec-kit enforces this itself via `_assert_pinned_version`, but only on the bundled
    and catalog install paths — neither of which runs for a local install. Nothing else
    would catch a bumped component whose pin was not bumped with it.
    """
    for kind, entry in components:
        if kind == "steps":
            continue
        on_disk = component_version_on_disk(kind, entry["id"])
        assert on_disk == entry["version"], (
            f"{kind[:-1]} '{entry['id']}': bundle.yml pins {entry['version']}, "
            f"but its own manifest declares {on_disk}"
        )


def test_every_referenced_component_exists(components):
    for kind, entry in components:
        if kind == "steps":
            continue
        directory, manifest_name, _ = KIND_LAYOUT[kind]
        path = REPO_ROOT / directory / entry["id"] / manifest_name
        assert path.is_file(), f"{kind[:-1]} '{entry['id']}' has no {manifest_name} at {path}"


def test_bundle_ships_everything_this_repo_builds(components):
    """A component left out of the bundle is a component that ships only by accident."""
    declared = {(kind, entry["id"]) for kind, entry in components}
    for kind, (directory, manifest_name, _) in KIND_LAYOUT.items():
        for path in sorted((REPO_ROOT / directory).glob(f"*/{manifest_name}")):
            component_id = path.parent.name
            assert (kind, component_id) in declared, (
                f"{kind[:-1]} '{component_id}' exists in {directory}/ but the bundle omits it"
            )


# -- the reason the bundle exists -----------------------------------------


def test_the_preset_never_ships_without_its_extension(components):
    """The bundle's whole purpose.

    The preset's guidance tells an agent to run validators at
    `.specify/extensions/openup/scripts/python/`, which the extension installs. Spec Kit
    has no preset->extension dependency mechanism, so this manifest is the only place the
    pairing can be stated. A bundle carrying the preset alone would ship instructions
    pointing at files that are not there — every check named, none of them running.
    """
    kinds = {kind: {e["id"] for _, e in [(k, e) for k, e in components if k == kind]} for kind in COMPONENT_KINDS}
    if "openup-governance" in kinds["presets"]:
        assert "openup" in kinds["extensions"], (
            "the openup-governance preset requires the openup extension's validators"
        )


def test_every_phase_has_a_workflow(components):
    """Gates are the only real enforcement, and they live in workflows. A missing phase
    is a phase whose milestone cannot be held."""
    workflows = {entry["id"] for kind, entry in components if kind == "workflows"}
    for phase in ("inception", "elaboration", "construction", "transition"):
        assert f"openup-{phase}" in workflows, f"no workflow for the {phase} phase"


# -- the local installer ---------------------------------------------------


def test_bundle_ships_a_readme():
    """`specify bundle build` refuses to package a bundle without one."""
    assert (BUNDLE_DIR / "README.md").is_file()


def test_installer_reads_the_manifest_rather_than_restating_it():
    """If install.py hardcoded the component list, the pin check would be checking itself
    and the two lists could drift apart unnoticed."""
    source = INSTALLER_PATH.read_text()
    assert 'MANIFEST = BUNDLE_DIR / "bundle.yml"' in source
    assert "yaml.safe_load(MANIFEST.read_text())" in source
    for component_id in ("openup-inception", "openup-elaboration", "openup-transition"):
        assert component_id not in source, (
            f"install.py hardcodes '{component_id}'; it should read provides from bundle.yml"
        )


def test_installer_documents_the_zero_component_record():
    """Someone will run `specify bundle install` and see it exit 0 with a 0-component
    record. If that is not explained where they will look, it reads as success."""
    corpus = (INSTALLER_PATH.read_text() + (BUNDLE_DIR / "README.md").read_text()).lower()
    assert "0 added" in corpus or "contributed_components" in corpus
    assert "not found in any catalog" in corpus


# -- spec-kit's own parser and validator -----------------------------------


@pytest.mark.skipif(not ENGINE_AVAILABLE, reason="specify-cli is not installed")
def test_speckit_parses_the_manifest_without_structural_errors():
    parsed = BundleManifest.from_file(MANIFEST_PATH)
    assert parsed.structural_errors() == []


@pytest.mark.skipif(not ENGINE_AVAILABLE, reason="specify-cli is not installed")
def test_speckit_validates_the_manifest():
    report = validate_manifest(BundleManifest.from_file(MANIFEST_PATH))
    assert report.ok, "spec-kit rejected the manifest:\n  - " + "\n  - ".join(report.errors)


@pytest.mark.skipif(not ENGINE_AVAILABLE, reason="specify-cli is not installed")
def test_install_order_puts_the_extension_before_the_preset():
    """Order is spec-kit's (`BundleManifest.components`), not ours — but it is the order
    SpecUP needs, so assert it rather than assume it survives a spec-kit upgrade."""
    order = [(c.kind, c.id) for c in BundleManifest.from_file(MANIFEST_PATH).components]
    assert order.index(("extensions", "openup")) < order.index(("presets", "openup-governance"))


@pytest.mark.skipif(not ENGINE_AVAILABLE, reason="specify-cli is not installed")
def test_the_verified_speckit_version_satisfies_the_constraint():
    parsed = BundleManifest.from_file(MANIFEST_PATH)
    assert satisfies(VERIFIED_SPECKIT_VERSION, parsed.requires.speckit_version), (
        f"requires.speckit_version '{parsed.requires.speckit_version}' excludes "
        f"{VERIFIED_SPECKIT_VERSION}, the only version this bundle was verified on"
    )
