"""Validate the openup-governance preset.

Preset rules are transcribed from spec-kit v1.0.6 (presets/ARCHITECTURE.md, docs/reference/
presets.md) and from the two official wrap examples: presets/constitution-sync and
presets/self-test.

The subtle failure this file guards against: a `wrap` command's frontmatter REPLACES the core
command's. The core `/tasks` and `/implement` declare `scripts:` blocks that `{SCRIPT}`
substitution depends on, so a wrapper that omits them silently breaks the command it wraps —
the composed file still looks correct, and the script invocation is simply gone.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PRESET_DIR = REPO_ROOT / "presets" / "openup-governance"
MANIFEST_PATH = PRESET_DIR / "preset.yml"

ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
VALID_TYPES = {"template", "command", "script"}
VALID_STRATEGIES = {"replace", "prepend", "append", "wrap"}
# Scripts support only replace and wrap (presets/ARCHITECTURE.md composition table).
SCRIPT_STRATEGIES = {"replace", "wrap"}

# Transcribed verbatim from spec-kit templates/commands/{tasks,implement}.md frontmatter.
# A wrap MUST reproduce these or {SCRIPT} resolves to nothing in the composed command.
CORE_SCRIPTS = {
    "speckit.tasks": {
        "sh": "scripts/bash/setup-tasks.sh --json",
        "ps": "scripts/powershell/setup-tasks.ps1 -Json",
        "py": "scripts/python/setup_tasks.py --json",
    },
    "speckit.implement": {
        "sh": "scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks",
        "ps": "scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks",
        "py": "scripts/python/check_prerequisites.py --json --require-tasks --include-tasks",
    },
}


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text())


@pytest.fixture(scope="module")
def entries(manifest) -> list[dict]:
    return manifest["provides"]["templates"]


def frontmatter_and_body(path: pathlib.Path) -> tuple[dict | None, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        return None, text
    _, block, body = text.split("---", 2)
    return yaml.safe_load(block), body


# -- manifest --------------------------------------------------------------


def test_preset_block_is_complete(manifest):
    assert manifest["schema_version"] == "1.0"
    preset = manifest["preset"]
    for field in ("id", "name", "version", "description", "author", "repository", "license"):
        assert preset.get(field), f"preset.{field} is required"
    assert ID_PATTERN.match(preset["id"])
    assert VERSION_PATTERN.match(preset["version"])
    assert len(preset["description"]) < 200, "description must be under 200 characters"


def test_everything_is_declared_under_provides_templates(manifest):
    """Presets use ONE list discriminated by `type`, unlike extensions which use separate
    commands/templates/scripts lists. Getting this wrong makes the preset install as empty."""
    provides = manifest["provides"]
    assert set(provides) == {"templates"}, (
        f"presets declare a single `templates` list; found {sorted(provides)}"
    )


def test_entries_are_well_formed(entries):
    for entry in entries:
        assert entry["type"] in VALID_TYPES, f"{entry['name']}: bad type {entry['type']!r}"
        assert entry.get("description"), f"{entry['name']} has no description"
        strategy = entry.get("strategy", "replace")
        assert strategy in VALID_STRATEGIES, f"{entry['name']}: bad strategy {strategy!r}"
        if entry["type"] == "script":
            assert strategy in SCRIPT_STRATEGIES, (
                f"{entry['name']}: scripts support only {sorted(SCRIPT_STRATEGIES)}"
            )
        assert (PRESET_DIR / entry["file"]).is_file(), f"missing {entry['file']}"


def test_files_on_disk_and_manifest_agree():
    declared = {e["file"] for e in yaml.safe_load(MANIFEST_PATH.read_text())["provides"]["templates"]}
    on_disk = {
        str(p.relative_to(PRESET_DIR))
        for p in PRESET_DIR.rglob("*.md")
        if p.name != "README.md"
    }
    assert on_disk == declared, (
        f"only on disk {sorted(on_disk - declared)}, only declared {sorted(declared - on_disk)}"
    )


# -- the wrap contract -----------------------------------------------------


def wrapped(entries) -> list[dict]:
    return [e for e in entries if e.get("strategy") == "wrap"]


def test_wrap_files_contain_exactly_one_core_placeholder(entries):
    for entry in wrapped(entries):
        body = (PRESET_DIR / entry["file"]).read_text()
        count = body.count("{CORE_TEMPLATE}")
        assert count == 1, (
            f"{entry['file']}: found {count} {{CORE_TEMPLATE}} placeholders; a wrap needs "
            f"exactly one or the core content is dropped or duplicated"
        )


def test_wrap_files_declare_the_strategy_in_frontmatter(entries):
    """Both official examples (constitution-sync, self-test) declare `strategy: wrap` in the
    command frontmatter as well as in the manifest."""
    for entry in wrapped(entries):
        front, _ = frontmatter_and_body(PRESET_DIR / entry["file"])
        assert front is not None, f"{entry['file']} has no frontmatter"
        assert front.get("strategy") == "wrap", f"{entry['file']} frontmatter needs strategy: wrap"


def test_wrap_commands_preserve_the_core_scripts_block(entries):
    """The subtle one. A wrapper's frontmatter replaces the core's, so omitting `scripts:`
    silently removes the command's script invocation."""
    for entry in wrapped(entries):
        if entry["type"] != "command" or entry["name"] not in CORE_SCRIPTS:
            continue
        front, _ = frontmatter_and_body(PRESET_DIR / entry["file"])
        scripts = front.get("scripts")
        assert scripts, f"{entry['file']} drops the core `scripts:` block, breaking {{SCRIPT}}"
        assert scripts == CORE_SCRIPTS[entry["name"]], (
            f"{entry['file']} `scripts:` does not match core {entry['name']}.\n"
            f"  expected: {CORE_SCRIPTS[entry['name']]}\n"
            f"  found:    {scripts}"
        )


def test_wrap_has_content_on_both_sides_of_the_placeholder(entries):
    for entry in wrapped(entries):
        _, body = frontmatter_and_body(PRESET_DIR / entry["file"])
        pre, post = body.split("{CORE_TEMPLATE}")
        assert len(pre.strip()) > 100, f"{entry['file']}: no meaningful pre-logic"
        assert len(post.strip()) > 100, f"{entry['file']}: no meaningful post-logic"


# -- the append contract ---------------------------------------------------


def test_append_addenda_are_fragments_without_frontmatter(entries):
    """An addendum is concatenated onto composed content. Frontmatter inside it would land
    mid-document as literal text."""
    for entry in entries:
        if entry.get("strategy") != "append":
            continue
        text = (PRESET_DIR / entry["file"]).read_text()
        assert not text.startswith("---\n"), (
            f"{entry['file']} starts with frontmatter, but it is appended to another document"
        )
        assert text.lstrip().startswith("#"), f"{entry['file']} should open with a heading"


def test_append_entries_target_core_templates(entries):
    core_templates = {"constitution-template", "spec-template", "plan-template", "tasks-template"}
    appended = {e["name"] for e in entries if e.get("strategy") == "append"}
    assert appended == core_templates, (
        f"expected addenda on every core template; missing {sorted(core_templates - appended)}"
    )


# -- design invariants -----------------------------------------------------


def test_preset_does_not_duplicate_extension_templates(entries):
    """The extension owns the WBS, risk and traceability starters. Shipping them here too
    would create the two-sources-of-truth drift the governance model exists to prevent."""
    extension_templates = {
        p.name for p in (REPO_ROOT / "extensions" / "openup" / "templates").glob("*")
    }
    preset_files = {pathlib.Path(e["file"]).name for e in entries}
    overlap = extension_templates & preset_files
    assert not overlap, f"preset duplicates extension templates: {sorted(overlap)}"


def test_preset_only_touches_spec_kit_core_artifacts(entries):
    """A preset's job is composing Spec Kit's OWN artifacts. Anything namespaced to the
    openup extension belongs in the extension, where it resolves as `replace`."""
    for entry in entries:
        assert not entry["name"].startswith("openup-"), (
            f"{entry['name']} is an extension-owned artifact, not a core one"
        )
        if entry["type"] == "command":
            assert entry["name"].count(".") == 1, (
                f"{entry['name']}: a preset composes two-segment CORE commands; "
                f"three-segment extension commands belong to their extension"
            )


def test_referenced_validators_exist_at_their_installed_path(entries):
    script_dir = REPO_ROOT / "extensions" / "openup" / "scripts" / "python"
    for entry in entries:
        text = (PRESET_DIR / entry["file"]).read_text()
        for script in re.findall(r"\.specify/extensions/openup/scripts/python/([a-z_]+\.py)", text):
            assert (script_dir / script).is_file(), (
                f"{entry['file']} references {script}, which does not exist"
            )


def test_guidance_forbids_the_gate_bypasses(entries):
    """The preset's value is refusing the shortcuts at the moment of temptation. If this
    guidance is ever edited away, the preset becomes ordinary prompt decoration."""
    corpus = " ".join((PRESET_DIR / e["file"]).read_text().lower() for e in entries)
    for phrase in (
        "do not lower a threshold",
        "absence of evidence is not evidence",
        "stop and report",
        "generated does not mean approved",
    ):
        assert phrase in corpus, f"the preset no longer states: {phrase!r}"
