"""Validate extension.yml against Spec Kit's documented manifest schema.

Transcribed from extensions/EXTENSION-API-REFERENCE.md (spec-kit v1.0.6). These rules are
Spec Kit's, not ours — getting one wrong means the extension fails to install, which is a
slow and confusing way to find out.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXTENSION_DIR = REPO_ROOT / "extensions" / "openup"
MANIFEST_PATH = EXTENSION_DIR / "extension.yml"

ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
COMMAND_PATTERN = re.compile(r"^speckit\.[a-z0-9-]+\.[a-z0-9-]+$")
SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")
SPECKIT_VERSION_PATTERN = re.compile(r"^(>=|<=|==|>|<)\d+\.\d+\.\d+(,(>=|<=|==|>|<)\d+\.\d+\.\d+)*$")
VALID_RUNTIMES = {"bash", "powershell", "python"}
KNOWN_EVENTS = {
    "before_constitution", "after_constitution", "before_specify", "after_specify",
    "before_clarify", "after_clarify", "before_plan", "after_plan",
    "before_tasks", "after_tasks", "before_implement", "after_implement",
    "before_checklist", "after_checklist", "before_analyze", "after_analyze",
    "before_taskstoissues", "after_taskstoissues",
}


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text())


def test_schema_version_is_declared(manifest):
    assert manifest["schema_version"] == "1.0"


def test_extension_block_is_complete(manifest):
    ext = manifest["extension"]
    for field in ("id", "name", "version", "description", "author", "repository", "license"):
        assert ext.get(field), f"extension.{field} is required"
    assert ID_PATTERN.match(ext["id"]), f"id {ext['id']!r} must match ^[a-z0-9-]+$"
    assert VERSION_PATTERN.match(ext["version"]), "version must be X.Y.Z with no prefix or suffix"
    assert len(ext["description"]) < 200, "description must be under 200 characters"
    assert ext["repository"].startswith("https://"), "repository must be a URL"


def test_speckit_version_specifier_is_well_formed(manifest):
    spec = manifest["requires"]["speckit_version"]
    assert SPECKIT_VERSION_PATTERN.match(spec), (
        f"{spec!r} is invalid — no spaces, and a bare version like '0.9.0' is rejected"
    )


def test_command_names_are_namespaced_under_the_extension_id(manifest):
    """specup.md s34 proposed /speckit.wbs and /speckit.audit — two segments, which the
    extension system rejects. Every command must be speckit.<ext-id>.<name>."""
    ext_id = manifest["extension"]["id"]
    for command in manifest["provides"]["commands"]:
        name = command["name"]
        assert COMMAND_PATTERN.match(name), f"{name!r} must match ^speckit\\.[a-z0-9-]+\\.[a-z0-9-]+$"
        assert name.split(".")[1] == ext_id, f"{name!r} is not namespaced under {ext_id!r}"


def test_command_files_exist_and_declare_a_description(manifest):
    for command in manifest["provides"]["commands"]:
        assert command.get("description"), f"{command['name']} has no description"
        path = EXTENSION_DIR / command["file"]
        assert path.is_file(), f"{command['name']} points at a missing file: {command['file']}"
        assert path.read_text().startswith("---\n"), f"{path.name} has no frontmatter"


def test_command_frontmatter_has_a_description(manifest):
    for command in manifest["provides"]["commands"]:
        text = (EXTENSION_DIR / command["file"]).read_text()
        frontmatter = yaml.safe_load(text.split("---")[1])
        assert frontmatter.get("description"), f"{command['file']} frontmatter needs a description"


def test_template_and_script_names_use_the_plain_slug_pattern(manifest):
    for kind in ("templates", "scripts"):
        for entry in manifest["provides"].get(kind, []):
            assert SLUG_PATTERN.match(entry["name"]), (
                f"{kind} name {entry['name']!r} must match ^[a-z0-9-]+$ "
                f"(underscores and dots are rejected)"
            )
            assert (EXTENSION_DIR / entry["file"]).is_file(), f"missing {entry['file']}"


def test_extension_templates_and_scripts_do_not_declare_a_strategy(manifest):
    """Composable strategies are preset-only; a strategy key here is a ValidationError."""
    for kind in ("templates", "scripts"):
        for entry in manifest["provides"].get(kind, []):
            assert "strategy" not in entry, (
                f"{kind} entry {entry['name']!r} declares a strategy — extensions always "
                f"resolve as 'replace'"
            )


def test_script_runtimes_are_valid(manifest):
    for entry in manifest["provides"].get("scripts", []):
        for runtime in entry.get("runtimes", []):
            assert runtime in VALID_RUNTIMES, f"{runtime!r} is not one of {sorted(VALID_RUNTIMES)}"


def test_config_template_exists(manifest):
    for entry in manifest["provides"].get("config", []):
        assert (EXTENSION_DIR / entry["template"]).is_file(), f"missing {entry['template']}"


def test_hooks_reference_known_events_and_own_commands(manifest):
    declared = {c["name"] for c in manifest["provides"]["commands"]}
    for event, hook in manifest.get("hooks", {}).items():
        assert event in KNOWN_EVENTS, f"{event!r} is not a core lifecycle event"
        entries = hook if isinstance(hook, list) else [hook]
        for entry in entries:
            assert entry["command"] in declared, f"{event} hooks an undeclared command"
            assert entry.get("priority", 10) >= 1, "priority must be >= 1"


def test_every_declared_command_file_is_referenced_exactly_once(manifest):
    files = [c["file"] for c in manifest["provides"]["commands"]]
    assert len(files) == len(set(files)), "a command file is declared twice"

    on_disk = {p.name for p in (EXTENSION_DIR / "commands").glob("*.md")}
    declared = {pathlib.Path(f).name for f in files}
    assert on_disk == declared, (
        f"commands/ and the manifest disagree: "
        f"only on disk {sorted(on_disk - declared)}, only declared {sorted(declared - on_disk)}"
    )


def test_every_script_on_disk_is_declared(manifest):
    declared = {pathlib.Path(s["file"]).name for s in manifest["provides"].get("scripts", [])}
    on_disk = {p.name for p in (EXTENSION_DIR / "scripts" / "python").glob("*.py")}
    assert on_disk == declared, (
        f"scripts/python/ and the manifest disagree: "
        f"only on disk {sorted(on_disk - declared)}, only declared {sorted(declared - on_disk)}"
    )


def test_commands_reference_scripts_at_their_installed_path(manifest):
    """Extension commands get no {SCRIPT} substitution, so the path written in the command
    must be the path the script actually installs to — and the same one a workflow shell
    step will use."""
    installed_prefix = ".specify/extensions/openup/scripts/python/"
    script_files = {pathlib.Path(s["file"]).name for s in manifest["provides"].get("scripts", [])}

    for command in manifest["provides"]["commands"]:
        text = (EXTENSION_DIR / command["file"]).read_text()
        for referenced in re.findall(r"scripts/python/([a-z_]+\.py)", text):
            assert referenced in script_files, (
                f"{command['file']} references undeclared script {referenced}"
            )
        for line in text.splitlines():
            if "scripts/python/" in line and ".py" in line and "`" in line or line.startswith("python "):
                if "scripts/python/" in line:
                    assert installed_prefix in line, (
                        f"{command['file']} references a script by a path other than its "
                        f"installed one:\n  {line.strip()}"
                    )
