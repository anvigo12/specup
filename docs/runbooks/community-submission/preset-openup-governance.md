# `[Preset]: Add openup-governance` — submission body

Paste into the **Preset Submission** issue form at
<https://github.com/github/spec-kit/issues/new?template=preset_submission.yml>.

Do not apply a label. A maintainer applies `preset-submission` during triage. See
[the runbook](../publishing-to-spec-kit.md#7-optional--submit-for-discovery).

---

**Title:** `[Preset]: Add openup-governance — OpenUP Governance`

## Preset ID

```
openup-governance
```

## Preset Name

```
OpenUP Governance
```

## Version

```
0.1.0
```

## Description

```
Composes OpenUP lifecycle governance into Spec Kit's own constitution, spec, plan and tasks templates, and wraps /tasks and /implement with the governed execution contract.
```

## Author

```
Aniket Gore
```

## Repository URL

```
https://github.com/anvigo12/specup
```

## Download URL

```
https://github.com/anvigo12/specup/releases/download/v0.1.0/openup-governance-0.1.0.zip
```

## Documentation URL

```
https://github.com/anvigo12/specup/blob/main/presets/openup-governance/README.md
```

This is the preset-scoped README, not the repository root, as the form prefers. It contains
the exact `specify preset add --from <download-url>` command above.

## License

```
MIT
```

## Required Spec Kit Version

```
>=1.0.0,<2.0.0
```

## Required Extensions (optional)

```
openup
```

Declared in `preset.yml` as `requires.extensions`, so Spec Kit warns when the extension is
absent instead of leaving the user to infer it from behaviour. See *Key Features* for why
that warning matters and what it does not do.

## Templates Provided

```markdown
- constitution-template.md — appends filesystem-first principles, resolve-or-stop, approval boundaries and the gate contract
- spec-template.md — appends governed requirement identity, ownership, acceptance criteria, and the consistency a requirement needs
- plan-template.md — appends lifecycle position, ADRs, risk and contract linkage, decomposition expectations, and data/consistency decisions
- tasks-template.md — appends the Definition of Ready, the Definition of Done, and the task execution contract
```

All four use `strategy: append`, so core content is extended rather than replaced.

## Commands Provided

```markdown
- speckit.tasks.md — wrap: derive tasks from the WBS rather than inventing them, and bind each to its governance
- speckit.implement.md — wrap: resolve the governance chain or stop; produce evidence and update the graph
```

Both use `strategy: wrap` and reproduce the core commands' `scripts:` frontmatter blocks
verbatim. A wrapper's frontmatter *replaces* the core command's, so omitting them would leave
`{SCRIPT}` unsubstituted while the preset still appeared to compose correctly.

## Number of Scripts (optional)

Leave empty. The preset ships no scripts by design — the validators belong to the `openup`
extension, and shipping copies here would create two sources of truth for the same check.

## Tags

```
openup, governance, traceability, lifecycle
```

## Key Features

```markdown
- Reaches Spec Kit's *own* artifacts. An extension can only add namespaced `speckit.openup.*` commands; changing what `/speckit.implement` itself does requires a preset, and this is that layer.
- Appends to all four core templates rather than replacing them, so core guidance survives and the governance layer is additive.
- Wraps `/speckit.tasks` so tasks are derived from the work breakdown structure instead of invented, and each is bound to the requirement, risk and acceptance criteria it serves.
- Wraps `/speckit.implement` with a resolve-or-stop contract: the governance chain is resolved before work begins, and evidence is produced and the traceability graph updated after.
- Declares `requires.extensions: [openup]`, so installing it alone prints the missing id and the command that fixes it. That is a warning, not a refusal — Spec Kit checks after the install succeeds and never installs the dependency — but it converts a silent half-install into something actionable.
- Ships no WBS, risk or traceability templates on purpose. Those belong to the extension, and duplicating them would create the drift this governance model exists to prevent.
```

## Testing Checklist

All four boxes are checked, each exercised rather than assumed:

| Box | How it was verified |
|---|---|
| Installs successfully via `specify preset add` | `specify preset add --from <the URL above>` → exit 0, `✓ Preset 'OpenUP Governance' v0.1.0 installed (priority 10)` |
| Template resolution works correctly | `specify preset resolve spec-template` → `[base] core → [append] openup-governance v0.1.0`; all four core templates gain their layer |
| Documentation is complete and accurate | the linked README carries the install command, the composition table, and the two mechanics that break a preset silently |
| Tested on at least one real project | clean `specify init --here --integration claude` project, spec-kit 1.0.6 |

Two further checks worth recording, because both are failure modes that look like success:

- The composed `speckit-tasks` skill contains **zero** literal `{CORE_TEMPLATE}` placeholders,
  with pre-logic, core body and post-logic in that order.
- `{SCRIPT}` resolves to `scripts/bash/setup-tasks.sh --json` — identical to an unwrapped core
  command, confirming the reproduced frontmatter works. A wrapper that drops it still composes
  and still looks right; the script invocation is simply gone.

`specify preset remove openup-governance` restores the core command and drops the addendum
layer, leaving nothing behind.

## Submission Requirements

All five boxes are checked. `preset.yml` is valid (spec-kit's own loader accepts it,
including `requires.extensions`), the linked preset-scoped README contains
`specify preset add --from <download-url>` using the exact URL above, `LICENSE` (MIT) is in the
repository, and the release is tagged `v0.1.0`.

---

## Proposed catalog entry

The form does not ask for one, but the automation produces it. This is what we expect:

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

## Additional context to include

```markdown
**This listing is for discovery, not installation.** The community preset catalog is
`install_allowed: false`, so `specify preset add openup-governance` resolves the entry and then
refuses it. Users install by registering SpecUP's own catalog:

    specify preset catalog add https://raw.githubusercontent.com/anvigo12/specup/main/catalog/presets.json \
      --name specup --install-allowed --priority 0

...or, preferably, by installing the whole stack at once with the `specup` bundle (submitted
separately), which is the intended entry point.

**The preset is half of a pair.** Its guidance tells agents to run validators that ship with
the `openup` extension (submitted separately). Installed alone it still composes and still
reads as authoritative, while every check it names silently does not run —
`requires.extensions` makes Spec Kit say so, but a bundle is what actually guarantees the two
arrive together.
```
