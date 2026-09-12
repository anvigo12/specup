#!/usr/bin/env python3
"""Scaffold the OpenUP governance tree.

Creates the directories and seeds the canonical stores from templates. Existing files are
NEVER overwritten — specup.md s31 draws the line at "generated does not mean approved", and
the converse holds too: authored content must survive re-running init.

Emits the same JSON verdict shape as the validators, so it composes into a workflow.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys

EXTENSION_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = EXTENSION_DIR / "templates"

DIRECTORIES = [
    ".specify/lifecycle",
    ".specify/governance",
    ".specify/architecture",
    ".specify/wbs",
    ".specify/risks",
    ".specify/traceability",
    ".specify/evidence",
]

# template file -> destination, relative to the project root
SEEDS = {
    "wbs-template.yaml": ".specify/wbs/wbs.yaml",
    "risk-register-template.yaml": ".specify/risks/risk-register.yaml",
    "requirements-template.yaml": ".specify/traceability/requirements.yaml",
    "traceability-template.yaml": ".specify/traceability/traceability.yaml",
    "vision-template.md": ".specify/lifecycle/vision.md",
    "stakeholders-template.md": ".specify/lifecycle/stakeholders.md",
    "index-template.md": ".specify/lifecycle/index.md",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold the OpenUP governance tree")
    parser.add_argument("--root", default=".", help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit a JSON verdict on stdout")
    parser.add_argument("--program", default=None, help="program name to seed into the WBS root")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    if not root.is_dir():
        payload = {"validator": "openup-init", "status": "ERROR",
                   "error": f"project root does not exist: {root}"}
        print(json.dumps(payload, indent=2) if args.json else f"ERROR: {payload['error']}",
              file=sys.stdout if args.json else sys.stderr)
        return 2

    created: list[str] = []
    skipped: list[str] = []

    for relative in DIRECTORIES:
        path = root / relative
        if path.is_dir():
            skipped.append(f"{relative}/ (exists)")
        else:
            path.mkdir(parents=True, exist_ok=True)
            created.append(f"{relative}/")

    for template_name, destination in SEEDS.items():
        target = root / destination
        source = TEMPLATE_DIR / template_name
        if target.exists():
            skipped.append(f"{destination} (authored content preserved)")
            continue
        if not source.is_file():
            skipped.append(f"{destination} (no template {template_name})")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_text()
        if args.program and template_name == "wbs-template.yaml":
            content = content.replace("REPLACE-WITH-PROGRAM-NAME", args.program)
        target.write_text(content)
        created.append(destination)

    config_target = root / ".specify" / "extensions" / "openup" / "openup-config.yml"
    if not config_target.exists():
        source = EXTENSION_DIR / "openup-config.yml"
        if source.is_file():
            config_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, config_target)
            created.append(str(config_target.relative_to(root)))
    else:
        skipped.append(".specify/extensions/openup/openup-config.yml (exists)")

    verdict = {
        "validator": "openup-init",
        "status": "PASS",
        "checks": [
            {"id": "INIT-001", "status": "PASS",
             "message": f"{len(created)} path(s) created", "evidence": created},
            {"id": "INIT-002", "status": "PASS",
             "message": f"{len(skipped)} path(s) left untouched", "evidence": skipped},
        ],
        "metrics": {"created": len(created), "skipped": len(skipped)},
    }

    if args.json:
        print(json.dumps(verdict, indent=2))
    else:
        print("OpenUP governance tree")
        print("=" * 22)
        for item in created:
            print(f"  created  {item}")
        for item in skipped:
            print(f"  kept     {item}")
        print(f"\n  {len(created)} created, {len(skipped)} preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
