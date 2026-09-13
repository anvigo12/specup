"""The committed catalog must describe the components that are actually in this repo.

`catalog/*.json` is the only part of SpecUP that a stranger's machine acts on without a
human reading it first. Spec Kit fetches one of these files, downloads the archive it names,
and aborts if the bytes do not hash to the `sha256` recorded here. Two failures follow from
that, and neither is visible by reading the JSON:

  * **A digest that no longer matches the source.** Someone edits a validator, does not
    re-run `task release:catalog`, and the catalog now pins the digest of a build that no
    longer exists. Every install fails with "Integrity check failed", naming nothing about
    why.
  * **Content that changed under an unchanged version.** Worse, because it succeeds. The
    archive is rebuilt and re-uploaded at the same version, so `0.1.0` means one thing for
    whoever installed yesterday and another for whoever installs today. Nothing in the
    system can tell those two apart afterwards.

`test_catalog_digests_match_a_fresh_build` is the tripwire for both: it rebuilds each
component archive from the working tree and compares the digest against the committed
catalog. It fails on exactly the state where the two have diverged, which is the state a
release must never be cut from.

The bundle artifact is excluded on purpose. It is produced by `specify bundle build`, so
checking it would make this file depend on spec-kit being installed — and it carries three
files, none of which is a component. `bundles.json` is checked for version agreement instead.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = REPO_ROOT / "catalog"
BUNDLE_MANIFEST = REPO_ROOT / "bundles" / "specup" / "bundle.yml"

sys.path.insert(0, str(REPO_ROOT / "tools"))

# kind -> (catalog filename, the JSON key holding the entries, the entry key carrying the
#          archive URL). The URL key is the asymmetry that costs an afternoon: workflows use
#          `url` where everything else uses `download_url`, and a workflow entry with a
#          `download_url` fails at install time with "does not have an install URL in the
#          catalog" while the file visibly contains one.
KINDS = {
    "extensions": ("extensions.json", "extensions", "download_url"),
    "presets": ("presets.json", "presets", "download_url"),
    "workflows": ("workflows.json", "workflows", "url"),
}

COMPONENT_DIRS = {"extensions": "extensions", "presets": "presets", "workflows": "workflows"}


@pytest.fixture(scope="module")
def bundle() -> dict:
    return yaml.safe_load(BUNDLE_MANIFEST.read_text())


@pytest.fixture(scope="module")
def catalogs() -> dict[str, dict]:
    missing = [name for name, _, _ in KINDS.values() if not (CATALOG_DIR / name).is_file()]
    missing += [] if (CATALOG_DIR / "bundles.json").is_file() else ["bundles.json"]
    if missing:
        pytest.fail(
            f"catalog/ is missing {sorted(missing)}. It is a committed release artifact — "
            f"regenerate it with `task release:catalog`."
        )
    loaded = {name: json.loads((CATALOG_DIR / name).read_text())
              for name, _, _ in KINDS.values()}
    loaded["bundles.json"] = json.loads((CATALOG_DIR / "bundles.json").read_text())
    return loaded


def entries(catalogs: dict, kind: str) -> dict[str, dict]:
    filename, payload_key, _ = KINDS[kind]
    return catalogs[filename][payload_key]


def test_every_component_in_the_bundle_has_a_catalog_entry(bundle, catalogs):
    for kind in KINDS:
        declared = {item["id"] for item in bundle["provides"].get(kind) or []}
        listed = set(entries(catalogs, kind))
        assert declared == listed, (
            f"{KINDS[kind][0]} and bundle.yml disagree: "
            f"only in the bundle {sorted(declared - listed)}, "
            f"only in the catalog {sorted(listed - declared)}"
        )


def test_catalog_versions_match_the_component_manifests(bundle, catalogs):
    manifests = {"extensions": ("extension.yml", "extension"),
                 "presets": ("preset.yml", "preset"),
                 "workflows": ("workflow.yml", "workflow")}
    for kind, (filename, root_key) in manifests.items():
        for component_id, entry in entries(catalogs, kind).items():
            path = REPO_ROOT / COMPONENT_DIRS[kind] / component_id / filename
            declared = yaml.safe_load(path.read_text())[root_key]["version"]
            assert entry["version"] == declared, (
                f"{component_id}: the catalog advertises {entry['version']}, "
                f"{filename} declares {declared}"
            )


def test_bundle_entry_matches_the_bundle_manifest(bundle, catalogs):
    declared = bundle["bundle"]
    listed = catalogs["bundles.json"]["bundles"]
    assert set(listed) == {declared["id"]}
    entry = listed[declared["id"]]
    assert entry["version"] == declared["version"]
    assert entry["provides"] == {
        "extensions": len(bundle["provides"].get("extensions") or []),
        "presets": len(bundle["provides"].get("presets") or []),
        "steps": len(bundle["provides"].get("steps") or []),
        "workflows": len(bundle["provides"].get("workflows") or []),
    }


def test_each_kind_uses_the_url_key_its_installer_actually_reads(catalogs):
    """Locked in because it is invisible and asymmetric. See the KINDS comment above."""
    for kind, (filename, _, url_key) in KINDS.items():
        wrong_key = "download_url" if url_key == "url" else "url"
        for component_id, entry in entries(catalogs, kind).items():
            assert url_key in entry, f"{filename}: {component_id} has no {url_key!r}"
            assert wrong_key not in entry, (
                f"{filename}: {component_id} carries {wrong_key!r}; this kind is resolved "
                f"through {url_key!r} and the other key is silently ignored"
            )
    assert "download_url" in catalogs["bundles.json"]["bundles"]["specup"]


def test_every_entry_pins_a_digest(catalogs):
    for kind in KINDS:
        for component_id, entry in entries(catalogs, kind).items():
            assert len(entry.get("sha256", "")) == 64, (
                f"{component_id}: sha256 must be a full SHA-256 hex digest"
            )
    assert len(catalogs["bundles.json"]["bundles"]["specup"].get("sha256", "")) == 64


def test_nothing_claims_to_be_verified(catalogs):
    """`verified` is Spec Kit's maintainers vouching for a component, not ours."""
    for kind in KINDS:
        for component_id, entry in entries(catalogs, kind).items():
            assert entry.get("verified") is False, f"{component_id} claims to be verified"
    assert catalogs["bundles.json"]["bundles"]["specup"].get("verified") is False


def test_catalog_digests_match_a_fresh_build(catalogs, tmp_path):
    """The tripwire. See this module's docstring for what it is protecting against."""
    import build_archives

    drift = []
    for kind in KINDS:
        for component_id, entry in entries(catalogs, kind).items():
            source = REPO_ROOT / COMPONENT_DIRS[kind] / component_id
            target = tmp_path / f"{component_id}.zip"
            _, digest = build_archives.build(source, target)
            if digest != entry["sha256"]:
                drift.append(
                    f"  {component_id} {entry['version']}: catalog pins "
                    f"{entry['sha256'][:16]}…, this working tree builds {digest[:16]}…"
                )

    assert not drift, (
        "The committed catalog does not describe the components in this repository:\n"
        + "\n".join(drift)
        + "\n\nIf the change was intentional, bump the component version and run "
        "`task release:catalog`. Re-publishing different bytes under a version that was "
        "already released is the one repair that cannot be undone — installs before and "
        "after would disagree, and nothing records which one anybody got."
    )
