#!/usr/bin/env python3
"""Install the SpecUP bundle into a Spec Kit project from *this working tree*.

WHICH INSTALLER TO USE
----------------------
This one installs the working tree. `specify bundle install specup` installs a
release. They are not alternatives -- they answer different questions:

    this script              the code in front of you, unreleased, offline
    specify bundle install   a published version, digest-verified, networked

Use the published route for real projects. Use this one when you are developing
SpecUP itself, when you need a change that is not released yet, or when the
machine cannot reach raw.githubusercontent.com and github.com.

WHY THE PUBLISHED ROUTE CANNOT COVER THIS CASE
----------------------------------------------
A bundle manifest references components by *id*. The bundler resolves each id
through `specify_cli._assets._locate_bundled_{extension,preset,workflow}`, which
looks in exactly two places: the assets shipped inside the Spec Kit wheel
(`specify_cli/core_pack/`), and a Spec Kit *source checkout* rooted at the
installed package's grandparent. Neither can ever contain a third-party project.
When both miss, the installer falls through to the published catalogs -- which
serve released archives pinned by digest, so by construction they cannot serve an
edit you have not released.

The manifest's `source:` key looks like the escape hatch and is not: it is parsed
into `ComponentRef.source` and then read by nothing in the install path. A local
catalog is not one either: catalog URLs are checked by
`is_https_or_localhost_http`, so a `file://` catalog is rejected outright.

Running `specify bundle install ./bundle.yml` against an unreleased tree has two
outcomes, both verified against spec-kit 1.0.6:

    components absent   -> "Extension 'openup' not found in any catalog." (exit 1)
    components present  -> "Installed 'specup' (0 added, 6 already present)."

The second is the trap. It exits 0 and looks like success, but the recorded
bundle has `contributed_components: []`, because Spec Kit deliberately refuses to
claim components it did not itself install (FR-022, the collateral-removal
guard). The bundle is then a label over an install it does not own, and
`bundle remove specup` removes nothing. That is Spec Kit behaving correctly, and
a confusing thing to discover; steering around it is part of why this exists.

WHAT THIS SCRIPT DOES
---------------------
Performs the install the manifest describes, in the manifest's own order, and
enforces the one guarantee the bundler would enforce if these components had come
from a catalog: that the version on disk matches the version the manifest pins. A
bundle whose pins have drifted from its components is worse than no bundle,
because it documents a combination that was never built.

`tools/build_catalog.py` applies the same check when a release is generated. This
one runs earlier -- at the moment you install the tree you are editing, which is
where the drift is introduced and cheapest to fix.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

BUNDLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BUNDLE_DIR.parent.parent
MANIFEST = BUNDLE_DIR / "bundle.yml"

# Where each component kind lives in this repo, and the manifest file that
# declares its version. Mirrors the layout `_locate_bundled_*` expects of a Spec
# Kit source checkout -- which is why the ids need no translation.
KINDS = {
    "extensions": ("extensions", "extension.yml", "extension"),
    "presets": ("presets", "preset.yml", "preset"),
    "workflows": ("workflows", "workflow.yml", "workflow"),
}


class InstallError(Exception):
    """A condition that must stop the install rather than be worked around."""


def component_dir(kind: str, component_id: str) -> Path:
    directory, _, _ = KINDS[kind]
    return REPO_ROOT / directory / component_id


def declared_version(kind: str, component_id: str) -> str:
    """Read a component's own declared version from its manifest."""
    _, manifest_name, root_key = KINDS[kind]
    path = component_dir(kind, component_id) / manifest_name
    if not path.is_file():
        raise InstallError(f"{kind[:-1]} '{component_id}': no {manifest_name} at {path}")
    data = yaml.safe_load(path.read_text())
    section = (data or {}).get(root_key)
    if not isinstance(section, dict) or not section.get("version"):
        raise InstallError(f"{path} declares no {root_key}.version")
    return str(section["version"]).strip()


def check_pins(components: list[tuple[str, str, str]]) -> None:
    """Refuse to install when a pin and the component on disk disagree.

    Mirrors `specify_cli.bundler.services.primitives._assert_pinned_version`, which
    never runs on this path because it only guards the bundled and catalog routes.
    Without it a stale pin would install silently and the bundle record would
    assert a version that was never installed.
    """
    drift = []
    for kind, component_id, pinned in components:
        actual = declared_version(kind, component_id)
        if actual != pinned:
            drift.append(f"  {kind[:-1]} '{component_id}': manifest pins {pinned}, on disk {actual}")
    if drift:
        raise InstallError(
            "Version pins disagree with the components in this repo:\n"
            + "\n".join(drift)
            + "\n\nUpdate bundles/specup/bundle.yml or the component, then re-run. "
            "Installing anyway would record a combination that was never built."
        )


def say(message: str = "") -> None:
    """Print, flushed.

    The subprocesses below write straight to the terminal while this process's
    own stdout is block-buffered when piped, so without the flush the running
    commentary arrives after the output it describes -- making it read as though
    the bundle was recorded before anything was installed.
    """
    print(message, flush=True)


def run(argv: list[str], project: Path, dry_run: bool) -> None:
    printable = " ".join(argv)
    if dry_run:
        say(f"  would run: {printable}")
        return
    say(f"  $ {printable}")
    result = subprocess.run(argv, cwd=project)
    if result.returncode != 0:
        raise InstallError(f"`{printable}` failed with exit code {result.returncode}")


def install_component(kind: str, component_id: str, entry: dict, project: Path, dry_run: bool) -> None:
    source = component_dir(kind, component_id)
    if kind == "extensions":
        # `--dev` is a flag here and the path is positional.
        argv = ["specify", "extension", "add", "--dev", str(source), "--force"]
        priority = entry.get("priority")
        if priority is not None:
            argv += ["--priority", str(priority)]
    elif kind == "presets":
        # `--dev` takes the path as its value here. The asymmetry with
        # `extension add` is Spec Kit's, not ours.
        argv = ["specify", "preset", "add", "--dev", str(source)]
        priority = entry.get("priority")
        if priority is not None:
            argv += ["--priority", str(priority)]
    elif kind == "workflows":
        argv = ["specify", "workflow", "add", "--dev", str(source)]
    else:  # pragma: no cover - KINDS is closed
        raise InstallError(f"unknown component kind '{kind}'")
    run(argv, project, dry_run)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install the SpecUP bundle from this repository into a Spec Kit project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="the Spec Kit project to install into (default: the current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the commands and the pin check without changing anything",
    )
    parser.add_argument(
        "--skip-record",
        action="store_true",
        help="skip the final `specify bundle install`, which records provenance only",
    )
    args = parser.parse_args()

    project = args.project.resolve()

    if shutil.which("specify") is None:
        raise InstallError(
            "`specify` is not on PATH. Install it with:\n"
            "  uv tool install specify-cli --from git+https://github.com/github/spec-kit.git"
        )
    if not (project / ".specify").is_dir():
        raise InstallError(
            f"{project} is not a Spec Kit project (no .specify/ directory).\n"
            "Run `specify init --here` there first."
        )

    manifest = yaml.safe_load(MANIFEST.read_text())
    provides = manifest.get("provides", {})

    # Install order is the manifest's own: extensions, then presets, then
    # workflows. It is load-bearing -- the preset's guidance references validators
    # the extension installs -- so it is read from the manifest rather than
    # restated here.
    ordered: list[tuple[str, str, dict]] = []
    for kind in ("extensions", "presets", "workflows"):
        for entry in provides.get(kind) or []:
            ordered.append((kind, entry["id"], entry))

    check_pins([(kind, cid, entry["version"]) for kind, cid, entry in ordered])
    say(f"Version pins match the components in {REPO_ROOT} ({len(ordered)} components).\n")

    for kind, component_id, entry in ordered:
        say(f"{kind[:-1]}: {component_id} @ {entry['version']}")
        install_component(kind, component_id, entry, project, args.dry_run)

    if not args.skip_record:
        say("\nRecording the bundle:")
        run(["specify", "bundle", "install", str(MANIFEST)], project, args.dry_run)
        say(
            "\nNote: `bundle list` will show specup with 0 components. That is correct and\n"
            "intended -- Spec Kit does not claim components it did not install itself, so\n"
            "`bundle remove specup` will not remove them. Remove them with\n"
            "`specify extension remove openup`, `specify preset remove openup-governance`,\n"
            "and `specify workflow remove openup-<phase>`."
        )

    say("\nOne step remains, and the validators do not work without it:")
    say(f"  python3 -m pip install -r {project}/.specify/extensions/openup/requirements.txt")
    say(
        "\nWithout those packages every validator exits 2, so a workflow halts on its\n"
        "setup-fault branch rather than passing a gate it could not evaluate."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except InstallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
