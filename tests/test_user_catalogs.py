"""The copyable user-scope catalog configuration must stay true to this repo and to Spec Kit.

`catalog/user/*.yml` is documentation that executes. A person copies these four files into
`~/.specify/` and from then on their machine downloads and installs code from the URLs in
them, in every Spec Kit project they open. Two failure modes follow, and reading the YAML
shows neither:

  * **A URL that no longer names a catalog in this repo.** Rename `catalog/workflows.json`
    and the copied file keeps pointing at the old name. Resolution fails with "not found"
    against a component the user can see listed on the release page.
  * **A dropped built-in.** For extensions, presets and workflows a config file at this path
    REPLACES Spec Kit's built-in stack instead of merging with it, so a file that lists only
    `specup` removes `default` and `community` from every project on the machine. It is
    silent: installs of SpecUP keep working, and the loss shows up only as things that
    used to be findable no longer being findable.

The second is the reason these files restate `default` and `community` verbatim, and the
reason that restating is asserted here rather than left to review. Bundles merge by id, so
`bundle-catalogs.yml` is exempt and is checked for the opposite property.
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = REPO_ROOT / "catalog"
USER_DIR = CATALOG_DIR / "user"

# Spec Kit's own stack, as declared in specify_cli 1.0.6. `default` and `community` are
# identical in shape across the three replacing primitives, differing only in the path
# segment, so one table covers them.
BUILTIN_PRIORITIES = {"default": 1, "community": 2}

# primitive -> (user config filename, the catalog/*.json it must point at, spec-kit path segment)
REPLACING = {
    "extension": ("extension-catalogs.yml", "extensions.json", "extensions"),
    "preset": ("preset-catalogs.yml", "presets.json", "presets"),
    "workflow": ("workflow-catalogs.yml", "workflows.json", "workflows"),
}

SPECUP_BASE = "https://raw.githubusercontent.com/anvigo12/specup/main/catalog"
SPECKIT_BASE = "https://raw.githubusercontent.com/github/spec-kit/main"


def _load(filename: str) -> dict:
    return yaml.safe_load((USER_DIR / filename).read_text())


@pytest.mark.parametrize("primitive", sorted(REPLACING))
def test_the_specup_source_points_at_a_catalog_that_exists(primitive):
    """A URL naming a file this repo does not publish fails at resolution, not at copy time."""
    filename, catalog_json, _ = REPLACING[primitive]
    entries = _load(filename)["catalogs"]
    specup = [e for e in entries if e["name"] == "specup"]
    assert len(specup) == 1, f"{filename}: expected exactly one 'specup' source"
    assert specup[0]["url"] == f"{SPECUP_BASE}/{catalog_json}"
    assert (CATALOG_DIR / catalog_json).is_file(), (
        f"{filename} points at catalog/{catalog_json}, which is not in this repo"
    )


@pytest.mark.parametrize("primitive", sorted(REPLACING))
def test_the_builtin_stack_is_restated(primitive):
    """The whole point of the file. Omitting these hides Spec Kit's own catalogs machine-wide.

    `get_active_catalogs` returns the first scope that loads and never consults the next, so
    a user-level file is the entire stack for that primitive. Dropping `default` here costs a
    user every extension, preset or workflow Spec Kit ships, in every project, silently.
    """
    filename, _, segment = REPLACING[primitive]
    entries = {e["name"]: e for e in _load(filename)["catalogs"]}

    for name, priority in BUILTIN_PRIORITIES.items():
        assert name in entries, (
            f"{filename} must restate the built-in '{name}' source — a config file at this "
            f"path replaces the built-in stack rather than merging with it"
        )
        assert entries[name]["priority"] == priority, (
            f"{filename}: '{name}' must keep its built-in priority {priority}"
        )

    suffix = {"default": "catalog.json", "community": "catalog.community.json"}
    for name, tail in suffix.items():
        assert entries[name]["url"] == f"{SPECKIT_BASE}/{segment}/{tail}"


@pytest.mark.parametrize("primitive", sorted(REPLACING))
def test_community_stays_discovery_only(primitive):
    """Spec Kit marks it unvetted. Re-flagging it installable on a user's machine is not ours
    to do, and `catalog list` says so in as many words."""
    filename, _, _ = REPLACING[primitive]
    entries = {e["name"]: e for e in _load(filename)["catalogs"]}
    assert entries["community"]["install_allowed"] is False
    assert entries["default"]["install_allowed"] is True


@pytest.mark.parametrize("primitive", sorted(REPLACING))
def test_specup_resolves_ahead_of_the_builtins(primitive):
    """Lowest priority wins. Behind `default`, a name collision would resolve to the other one."""
    filename, _, _ = REPLACING[primitive]
    entries = {e["name"]: e for e in _load(filename)["catalogs"]}
    assert entries["specup"]["priority"] < min(BUILTIN_PRIORITIES.values())


def test_the_bundle_file_uses_the_bundle_schema():
    """Bundles are the one primitive with a different on-disk shape.

    `id` and `install_policy` rather than `name` and `install_allowed`, plus a required
    `schema_version`. A file copied from one of the other three parses as YAML and is then
    rejected, which is a worse failure than a syntax error because it looks fine.
    """
    config = _load("bundle-catalogs.yml")
    assert config["schema_version"] == "1.0"

    entries = config["catalogs"]
    assert len(entries) == 1, "only the specup source belongs here; the built-ins merge in"

    entry = entries[0]
    assert entry["id"] == "specup"
    assert entry["url"] == f"{SPECUP_BASE}/bundles.json"
    assert entry["priority"] == 0
    assert entry["install_policy"] == "install-allowed"
    assert "name" not in entry and "install_allowed" not in entry, (
        "bundle-catalogs.yml uses id/install_policy; name/install_allowed is the other schema"
    )


def test_the_bundle_file_does_not_restate_the_builtins():
    """The converse of `test_the_builtin_stack_is_restated`, and the reason it is not universal.

    `load_source_stack` merges built-in -> user -> project by id, so `default` and `community`
    survive without being named. Restating them here would pin Spec Kit's built-in bundle
    sources to whatever URLs were true when this file was written, which is how a stack goes
    stale without anyone editing it.
    """
    ids = {e["id"] for e in _load("bundle-catalogs.yml")["catalogs"]}
    assert not (ids & set(BUILTIN_PRIORITIES)), (
        "bundle sources merge by id; naming the built-ins here freezes them instead"
    )


def test_every_user_config_is_covered_by_this_file():
    """A fifth file added to the directory and not asserted on is the gap this closes."""
    present = {p.name for p in USER_DIR.glob("*.yml")}
    expected = {filename for filename, _, _ in REPLACING.values()} | {"bundle-catalogs.yml"}
    assert present == expected, (
        f"catalog/user/ holds {sorted(present)}; this test covers {sorted(expected)}"
    )
