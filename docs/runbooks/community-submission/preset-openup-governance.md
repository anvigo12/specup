### Preset ID

openup-governance

### Preset Name

OpenUP Governance

### Version

0.1.0

### Description

Composes OpenUP lifecycle governance into Spec Kit's own constitution, spec, plan and tasks templates, and wraps /tasks and /implement with the governed execution contract.

### Author

Aniket Gore

### Repository URL

https://github.com/anvigo12/specup

### Download URL

https://github.com/anvigo12/specup/releases/download/v0.1.0/openup-governance-0.1.0.zip

### Documentation URL

https://github.com/anvigo12/specup/blob/main/presets/openup-governance/README.md

### License

MIT

### Required Spec Kit Version

>=1.0.0,<2.0.0

### Required Extensions (optional)

openup

### Templates Provided

- `constitution-template` — appends filesystem-first principles, resolve-or-stop, approval boundaries and the gate contract
- `spec-template` — appends governed requirement identity, ownership, acceptance criteria, and the consistency a requirement needs
- `plan-template` — appends lifecycle position, architecture decisions, risk and contract linkage, decomposition expectations, and data/consistency decisions
- `tasks-template` — appends the Definition of Ready, the Definition of Done, and the task execution contract

All four use `strategy: append`, so core content is extended rather than replaced.

### Commands Provided

- `speckit.tasks` — `wrap`: derive tasks from the work breakdown structure rather than inventing them, and bind each to the requirement, risk and acceptance criteria it serves
- `speckit.implement` — `wrap`: resolve the governance chain or stop; produce evidence and update the traceability graph afterwards

Both reproduce the core commands' `scripts:` frontmatter blocks verbatim. A wrapper's
frontmatter *replaces* the core command's, so omitting them would leave `{SCRIPT}`
unsubstituted while the preset still appeared to compose correctly.

### Number of Scripts (optional)

_No response_

### Tags

openup, governance, traceability, lifecycle

### Key Features

- Reaches Spec Kit's *own* artifacts. An extension can only add namespaced `speckit.openup.*` commands; changing what `/speckit.implement` itself does requires a preset, and this is that layer.
- Appends to all four core templates rather than replacing them, so core guidance survives and the governance layer is strictly additive.
- Wraps `/speckit.tasks` so tasks are derived from the work breakdown structure instead of invented, each bound to the requirement, risk and acceptance criteria it serves.
- Wraps `/speckit.implement` with a resolve-or-stop contract: the governance chain is resolved before work begins, and evidence is produced and the graph updated after.
- Declares `requires.extensions: [openup]`, so installing it alone prints the missing id and the command that resolves it. That is a warning rather than a refusal — Spec Kit checks after the install has succeeded and never installs the dependency — but it turns a silent half-install into something actionable.
- Ships no WBS, risk or traceability templates on purpose. Those belong to the extension, and duplicating them here would create two sources of truth for the same artifact, which is the drift this governance model exists to prevent.

### Testing Checklist

- [x] Preset installs successfully via `specify preset add`
- [x] Template resolution works correctly after installation
- [x] Documentation is complete and accurate
- [x] Tested on at least one real project

### Submission Requirements

- [x] Valid `preset.yml` manifest included
- [x] Linked README (Documentation URL) explains how to use this preset and includes a valid `specify preset add ...` command (preferably `specify preset add --from <download-url>` using the exact download URL)
- [x] LICENSE file included
- [x] GitHub release created with version tag
- [x] Preset ID follows naming conventions (lowercase-with-hyphens)

**How each was verified**, on a clean `specify init --here --integration claude` project running
Spec Kit 1.0.6 on Linux with Python 3.13 — deliberately not the SpecUP repository, where local
paths would mask a broken artifact:

1. `specify preset add --from https://github.com/anvigo12/specup/releases/download/v0.1.0/openup-governance-0.1.0.zip` → exit 0, `✓ Preset 'OpenUP Governance' v0.1.0 installed (priority 10)`.
2. `specify preset resolve spec-template` → `[base] core → [append] openup-governance v0.1.0`. All four core templates gain their layer.
3. The composed `speckit-tasks` skill contains **zero** literal `{CORE_TEMPLATE}` placeholders, with pre-logic, core body and post-logic in that order.
4. `{SCRIPT}` resolves to `scripts/bash/setup-tasks.sh --json`, identical to an unwrapped core command — confirming the reproduced frontmatter works. A wrapper that drops it still composes and still looks right; the script invocation is simply gone, which is why this is checked explicitly.
5. Installed into a project *without* the `openup` extension, the declared dependency surfaces: `openup is not installed`, `Install with: specify extension add openup`, and the preset installs anyway.
6. `specify preset remove openup-governance` restores the core command and drops the addendum layer, leaving nothing behind.
7. Archive digest agrees three ways — as downloaded from the release, as built locally, and as pinned in the publisher's catalog: `c9bce34220773f07596e2e02e8b23f86886d4f7c3a0d38e22b1039ad2fe50137`.

The linked Documentation URL is the preset-scoped README, not the repository root, and contains
the exact `specify preset add --from <download-url>` command above.

**Repository layout, for validation.** This is a monorepo: `preset.yml` is at
`presets/openup-governance/preset.yml`, with `README.md` and `LICENSE` (MIT) at the repository
root. Inside the release archive, `preset.yml` is at the top level.

**Proposed catalog entry**, for reference:

```json
{
  "openup-governance": {
    "name": "OpenUP Governance",
    "id": "openup-governance",
    "version": "0.1.0",
    "description": "Composes OpenUP lifecycle governance into Spec Kit's own constitution, spec, plan and tasks templates, and wraps /tasks and /implement with the governed execution contract.",
    "author": "Aniket Gore",
    "repository": "https://github.com/anvigo12/specup",
    "download_url": "https://github.com/anvigo12/specup/releases/download/v0.1.0/openup-governance-0.1.0.zip",
    "sha256": "c9bce34220773f07596e2e02e8b23f86886d4f7c3a0d38e22b1039ad2fe50137",
    "homepage": "https://github.com/anvigo12/specup",
    "documentation": "https://github.com/anvigo12/specup/blob/main/presets/openup-governance/README.md",
    "license": "MIT",
    "requires": {
      "speckit_version": ">=1.0.0,<2.0.0",
      "extensions": ["openup"]
    },
    "provides": {
      "templates": 4,
      "commands": 2
    },
    "tags": ["openup", "governance", "traceability", "lifecycle"],
    "created_at": "2026-09-13T00:00:00Z",
    "updated_at": "2026-09-13T00:00:00Z"
  }
}
```

**This listing is for discovery, not installation.** The community preset catalog is
`install_allowed: false`, so `specify preset add openup-governance` resolves the entry and then
refuses it. Users install by registering SpecUP's own catalog:

    specify preset catalog add https://raw.githubusercontent.com/anvigo12/specup/main/catalog/presets.json --name specup --install-allowed --priority 0

...or, preferably, by installing the whole stack at once with the `specup` bundle, which is the
intended entry point. The bundle and the `openup` extension are submitted separately, and all
three are the same 0.1.0 release.

**The preset is half of a pair.** Its guidance tells agents to run validators that ship with the
`openup` extension. Installed alone it still composes and still reads as authoritative while
every check it names silently does not run. `requires.extensions` makes Spec Kit say so, but a
bundle is what actually guarantees the two arrive together.
