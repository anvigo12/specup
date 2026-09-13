#!/usr/bin/env python3
"""Build reproducible release archives for every component the bundle declares.

One archive per component, plus a SHA256SUMS file. The digests are the point: a
catalog entry pins `sha256`, Spec Kit verifies the downloaded bytes against it
(`verify_archive_sha256`), and a mismatch aborts the install. So the digest in the
catalog must be the digest of the archive actually attached to the release — which
means neither may be produced by hand.

Reproducibility is not decoration either. Archive members are written with a fixed
timestamp and sorted order, and permissions collapse to 0755/0644, mirroring
`specify_cli.bundler.services.packager`. Without that, rebuilding an unchanged
component yields a different digest every time, and nobody can tell a rebuild from
a tampered artifact.

The component list is read from bundles/specup/bundle.yml rather than restated, so
a component added to the bundle cannot be forgotten here.

The bundle artifact itself is digested too, and is NOT built here. `specify bundle
build` produces it, because the catalog resolves a bundle entry by downloading that
exact archive and reading the manifest inside it. Hashing it here rather than in the
bundler keeps one file — SHA256SUMS — as the single list every catalog `sha256`
field is copied from, which is the property that makes `tools/build_catalog.py`
possible at all.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import sys
import zipfile

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "bundles" / "specup" / "bundle.yml"

# kind -> (repo directory, the manifest that must sit at the archive root)
KINDS = {
    "extensions": ("extensions", "extension.yml"),
    "presets": ("presets", "preset.yml"),
    "workflows": ("workflows", "workflow.yml"),
}

EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
# Machine-local config must never ship: it would override the installed defaults
# on someone else's machine with values from ours.
EXCLUDE_NAMES = {".DS_Store", "openup-config.local.yml"}

FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def collect(source: pathlib.Path) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for root, dirnames, filenames in os.walk(source, followlinks=False):
        root_path = pathlib.Path(root)
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS and not (root_path / d).is_symlink()
        ]
        for name in filenames:
            path = root_path / name
            if name in EXCLUDE_NAMES or path.suffix in EXCLUDE_SUFFIXES:
                continue
            if path.is_symlink():
                continue
            files.append(path)
    # Sort by the archive name, not the Path: Path ordering is platform-dependent,
    # which would lay members out differently across hosts and change the digest.
    return sorted(files, key=lambda p: p.relative_to(source).as_posix())


def build(source: pathlib.Path, target: pathlib.Path) -> tuple[int, str]:
    """Write a deterministic zip of *source* to *target*; return (file count, sha256)."""
    files = collect(source)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            # The component manifest must land at the archive ROOT, not under a
            # wrapper directory -- that is the layout `install_from_zip` expects.
            arcname = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(filename=arcname, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            with path.open("rb") as handle:
                mode = 0o755 if os.fstat(handle.fileno()).st_mode & 0o111 else 0o644
                info.external_attr = mode << 16
                archive.writestr(info, handle.read())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return len(files), digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="dist", help="output directory (default: dist)")
    args = parser.parse_args()

    out_dir = (REPO_ROOT / args.out).resolve() if not os.path.isabs(args.out) else pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = yaml.safe_load(MANIFEST.read_text()) or {}
    provides = manifest.get("provides", {})
    sums: list[str] = []
    failures: list[str] = []

    for kind, (directory, manifest_name) in KINDS.items():
        for entry in provides.get(kind) or []:
            component_id, version = entry["id"], entry["version"]
            source = REPO_ROOT / directory / component_id
            if not (source / manifest_name).is_file():
                failures.append(f"{kind[:-1]} '{component_id}': no {manifest_name} in {source}")
                continue
            target = out_dir / f"{component_id}-{version}.zip"
            count, digest = build(source, target)
            sums.append(f"{digest}  {target.name}")
            print(f"  {target.name:<38} {count:>3} files  {digest[:16]}…")

    # The bundle artifact. Built by `specify bundle build`, not here, but digested here
    # because a catalog bundle entry needs `download_url` + `sha256` exactly like a
    # component entry does -- and a missing digest there is the failure that looks like a
    # broken catalog: `specify bundle install specup` reports "has no download_url; cannot
    # resolve its manifest" and names nothing about why.
    bundle = manifest.get("bundle") or {}
    bundle_id, bundle_version = bundle.get("id"), bundle.get("version")
    bundle_archive = out_dir / f"{bundle_id}-{bundle_version}.zip"
    if bundle_archive.is_file():
        digest = hashlib.sha256(bundle_archive.read_bytes()).hexdigest()
        with zipfile.ZipFile(bundle_archive) as archive:
            count = len(archive.namelist())
        sums.append(f"{digest}  {bundle_archive.name}")
        print(f"  {bundle_archive.name:<38} {count:>3} files  {digest[:16]}…  (bundle)")
    else:
        failures.append(
            f"bundle artifact {bundle_archive.name} is missing from {out_dir}. Build it "
            f"first:\n    specify bundle build --path bundles/specup --output {args.out}\n"
            f"  Without it the catalog's bundles.json carries no sha256, and "
            f"`specify bundle install {bundle_id}` fails on a manifest it cannot resolve."
        )

    if failures:
        for failure in failures:
            print(f"error: {failure}", file=sys.stderr)
        return 1

    sums_path = out_dir / "SHA256SUMS"
    sums_path.write_text("\n".join(sums) + "\n")
    print(f"\n{len(sums)} archive(s) -> {out_dir}")
    print(f"digests          -> {sums_path}")
    print("\nGenerate the catalog from these digests with `task release:catalog`. See")
    print("docs/runbooks/publishing-to-spec-kit.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
