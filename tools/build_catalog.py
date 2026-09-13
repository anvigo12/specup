#!/usr/bin/env python3
"""Generate the four catalog documents Spec Kit fetches to install SpecUP.

WHY THIS IS GENERATED
---------------------
A catalog entry pins a `sha256`, and Spec Kit aborts an install when the bytes it
downloaded do not match. That makes the catalog and the release assets one artifact
with two halves, and a hand-edited half is the failure nobody can debug from the
error message: a wrong digest reads as "Integrity check failed", a missing one as
"has no download_url; cannot resolve its manifest", and a stale version as a
successful install of something nobody built.

So every field here is derived. Component metadata comes from each component's own
manifest, digests come from `dist/SHA256SUMS`, and the component list comes from
bundles/specup/bundle.yml -- the same file build_archives.py reads, so a component
added to the bundle cannot be missing from the catalog.

THE FOUR SHAPES ARE NOT THE SAME
--------------------------------
This is the part that costs an afternoon if you write the files by hand, and all of
it is checked against spec-kit 1.0.6's own readers:

    extensions.json   entry key `download_url`   extensions/__init__.py:4319
    presets.json      entry key `download_url`   presets/__init__.py:5165
    workflows.json    entry key `url`            workflows/_commands.py:2224
    bundles.json      entry key `download_url`   bundler/models/catalog.py:151

`workflows.json` is the odd one out, and the symptom is specific: "Workflow
'openup-inception' does not have an install URL in the catalog", while the file
plainly contains a URL under the name every other catalog uses.

NO TIMESTAMP
------------
The published catalogs carry `updated_at`; nothing reads it. Omitting it makes this
output a pure function of the release, so regenerating without changing anything
produces no diff -- the same reason render_views.py refuses to stamp its views. A
catalog that changes on every run cannot be checked into git as evidence of what was
published.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "bundles" / "specup" / "bundle.yml"

# kind -> (repo directory, manifest filename, the manifest's root key, catalog filename,
#          the JSON key that holds the entries, the entry key that carries the archive URL)
KINDS = {
    "extensions": ("extensions", "extension.yml", "extension",
                   "extensions.json", "extensions", "download_url"),
    "presets": ("presets", "preset.yml", "preset",
                "presets.json", "presets", "download_url"),
    "workflows": ("workflows", "workflow.yml", "workflow",
                  "workflows.json", "workflows", "url"),
}

SCHEMA_VERSION = "1.0"

# Copied from each component manifest into its catalog entry when present. Everything
# here is display-only to Spec Kit; the two fields that decide whether an install
# works are added separately, and are the two that cannot be wrong.
PASSTHROUGH = ("name", "description", "author", "license", "repository", "category")


class BuildError(Exception):
    """A condition that must stop generation rather than emit a catalog that lies."""


def read_sums(dist: pathlib.Path) -> dict[str, str]:
    """Parse dist/SHA256SUMS into {archive name: digest}."""
    path = dist / "SHA256SUMS"
    if not path.is_file():
        raise BuildError(
            f"{path} does not exist. Build the archives first:\n"
            f"    task release:archives"
        )
    digests: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        digest, _, name = line.partition("  ")
        if not name:
            raise BuildError(f"{path}: cannot parse line: {line!r}")
        digests[name.strip()] = digest.strip()
    return digests


def digest_for(name: str, digests: dict[str, str], dist: pathlib.Path) -> str:
    """The digest for one archive, re-verified against the bytes on disk.

    SHA256SUMS is an intermediate file that survives a `clean`, a partial rebuild and a
    branch switch. Trusting it without re-reading the archive is how a catalog comes to
    pin the digest of a build nobody has any more -- which fails at install time, on
    someone else's machine, as an integrity error with no hint that the catalog was
    generated from a stale list.
    """
    recorded = digests.get(name)
    if recorded is None:
        raise BuildError(
            f"{name} has no entry in dist/SHA256SUMS. Rebuild with `task release:archives`."
        )
    archive = dist / name
    if not archive.is_file():
        raise BuildError(f"{archive} is missing, but SHA256SUMS records a digest for it.")
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != recorded:
        raise BuildError(
            f"{name}: SHA256SUMS records {recorded[:16]}… but the file on disk is "
            f"{actual[:16]}…. The digest list is stale; rebuild with "
            f"`task release:archives` rather than publishing either value."
        )
    return actual


def component_entry(kind: str, component_id: str, version: str, dist: pathlib.Path,
                    digests: dict[str, str], asset_base: str) -> dict[str, Any]:
    directory, manifest_name, root_key, _, _, url_key = KINDS[kind]
    path = REPO_ROOT / directory / component_id / manifest_name
    if not path.is_file():
        raise BuildError(f"{kind[:-1]} '{component_id}': no {manifest_name} at {path}")
    document = yaml.safe_load(path.read_text()) or {}
    section = document.get(root_key)
    if not isinstance(section, dict):
        raise BuildError(f"{path}: no '{root_key}:' block")

    declared = str(section.get("version", "")).strip()
    if declared != version:
        raise BuildError(
            f"{kind[:-1]} '{component_id}': bundle.yml pins {version}, {manifest_name} "
            f"declares {declared}. The catalog would advertise a combination that was "
            f"never built."
        )

    archive = f"{component_id}-{version}.zip"
    entry: dict[str, Any] = {"id": component_id, "version": version}
    entry.update({key: section[key] for key in PASSTHROUGH if section.get(key)})
    entry[url_key] = f"{asset_base}{archive}"
    entry["sha256"] = digest_for(archive, digests, dist)

    requires = document.get("requires") or {}
    if requires.get("speckit_version"):
        entry["requires"] = {"speckit_version": requires["speckit_version"]}
    if document.get("tags"):
        entry["tags"] = list(document["tags"])
    # Never true. `verified` is the publishing project's claim that Spec Kit's
    # maintainers vetted it, and nobody has vetted this one.
    entry["verified"] = False
    return entry


def bundle_entry(manifest: dict[str, Any], provides: dict[str, Any], dist: pathlib.Path,
                 digests: dict[str, str], asset_base: str) -> dict[str, Any]:
    bundle = manifest.get("bundle") or {}
    bundle_id = bundle.get("id")
    version = bundle.get("version")
    archive = f"{bundle_id}-{version}.zip"
    entry = {
        "id": bundle_id,
        "name": bundle.get("name", ""),
        "version": version,
        "role": bundle.get("role", ""),
        "description": bundle.get("description", ""),
        "author": bundle.get("author", ""),
        "license": bundle.get("license", ""),
        # Points at the `specify bundle build` artifact, not at any component archive.
        # The installer downloads this, reads the manifest inside it, and then resolves
        # each component through the catalogs above.
        "download_url": f"{asset_base}{archive}",
        "sha256": digest_for(archive, digests, dist),
        "requires": {
            "speckit_version": (manifest.get("requires") or {}).get("speckit_version", "")
        },
        "provides": {
            "extensions": len(provides.get("extensions") or []),
            "presets": len(provides.get("presets") or []),
            "steps": len(provides.get("steps") or []),
            "workflows": len(provides.get("workflows") or []),
        },
        "verified": False,
    }
    if bundle.get("repository"):
        entry["repository"] = bundle["repository"]
    if manifest.get("tags"):
        entry["tags"] = list(manifest["tags"])
    return entry


def write(path: pathlib.Path, payload: dict[str, Any]) -> bool:
    """Write a catalog file; return True if the bytes changed."""
    # ensure_ascii=False: these files are read by people as often as by the CLI, and an
    # em-dash in a bundle name has no business arriving as —.
    body = json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    if path.is_file() and path.read_text() == body:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return True


def raw_base(repository: str, branch: str) -> str:
    """The raw.githubusercontent.com URL the catalog files themselves are served from."""
    trimmed = repository.rstrip("/").removesuffix(".git")
    if not trimmed.startswith("https://github.com/"):
        raise BuildError(
            f"cannot derive a raw URL from repository {repository!r}; pass --catalog-base"
        )
    slug = trimmed[len("https://github.com/"):]
    return f"https://raw.githubusercontent.com/{slug}/{branch}/catalog/"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", default="dist", help="where the archives are (default: dist)")
    parser.add_argument("--out", default="catalog", help="output directory (default: catalog)")
    parser.add_argument("--branch", default="main",
                        help="branch the catalog files are served from (default: main)")
    parser.add_argument("--asset-base", default=None,
                        help="base URL for the release assets (default: the GitHub release "
                             "for the bundle's own version tag)")
    parser.add_argument("--catalog-base", default=None,
                        help="base URL the catalog files are served from (default: derived "
                             "from the extension's repository field)")
    args = parser.parse_args()

    dist = (REPO_ROOT / args.dist) if not pathlib.Path(args.dist).is_absolute() else pathlib.Path(args.dist)
    out = (REPO_ROOT / args.out) if not pathlib.Path(args.out).is_absolute() else pathlib.Path(args.out)

    manifest = yaml.safe_load(MANIFEST.read_text()) or {}
    provides = manifest.get("provides") or {}
    version = (manifest.get("bundle") or {}).get("version")

    extension = yaml.safe_load(
        (REPO_ROOT / "extensions" / "openup" / "extension.yml").read_text()
    ) or {}
    repository = (extension.get("extension") or {}).get("repository", "")

    asset_base = args.asset_base or f"{repository.rstrip('/')}/releases/download/v{version}/"
    if not asset_base.endswith("/"):
        asset_base += "/"
    catalog_base = args.catalog_base or raw_base(repository, args.branch)
    if not catalog_base.endswith("/"):
        catalog_base += "/"

    digests = read_sums(dist)
    changed, unchanged = [], []

    for kind, (_, _, _, filename, payload_key, _) in KINDS.items():
        entries = {}
        for item in provides.get(kind) or []:
            entries[item["id"]] = component_entry(
                kind, item["id"], item["version"], dist, digests, asset_base
            )
        payload = {
            "schema_version": SCHEMA_VERSION,
            "catalog_url": f"{catalog_base}{filename}",
            payload_key: entries,
        }
        target = out / filename
        (changed if write(target, payload) else unchanged).append(
            f"{filename} ({len(entries)} entr{'y' if len(entries) == 1 else 'ies'})"
        )

    bundle_id = (manifest.get("bundle") or {}).get("id")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "catalog_url": f"{catalog_base}bundles.json",
        "bundles": {bundle_id: bundle_entry(manifest, provides, dist, digests, asset_base)},
    }
    target = out / "bundles.json"
    (changed if write(target, payload) else unchanged).append("bundles.json (1 entry)")

    for item in changed:
        print(f"  wrote      {item}")
    for item in unchanged:
        print(f"  unchanged  {item}")
    print(f"\n{len(changed)} written, {len(unchanged)} already current -> {out}")
    print(f"assets  {asset_base}")
    print(f"served  {catalog_base}")
    print("\nCommit catalog/ and publish the archives at the asset URLs above, or the")
    print("digests point at bytes nobody can download. See")
    print("docs/runbooks/publishing-to-spec-kit.md.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
