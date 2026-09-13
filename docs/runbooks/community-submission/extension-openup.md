# `[Extension]: Add openup` — submission body

Paste into the **Extension Submission** issue form at
<https://github.com/github/spec-kit/issues/new?template=extension_submission.yml>.

Do not apply a label. A maintainer applies `extension-submission` during triage, which starts
the validation workflow that opens the catalog PR. See
[the runbook](../publishing-to-spec-kit.md#7-optional--submit-for-discovery).

---

**Title:** `[Extension]: Add openup — OpenUP Governed Lifecycle`

## Extension ID

```
openup
```

## Extension Name

```
OpenUP Governed Lifecycle
```

## Version

```
0.1.0
```

## Description

```
Adds the OpenUP lifecycle to Spec Kit: phases, iterations, a seven-level WBS, an executable risk register, bi-directional traceability, and machine-checkable milestone gates.
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
https://github.com/anvigo12/specup/releases/download/v0.1.0/openup-0.1.0.zip
```

## License

```
MIT
```

## Homepage (optional)

```
https://github.com/anvigo12/specup
```

## Documentation URL (optional)

```
https://github.com/anvigo12/specup/blob/main/docs/guide/using-specup.md
```

## Changelog URL (optional)

Leave empty. The repository has no `CHANGELOG.md`; 0.1.0 is the first release and its notes
are the release body itself. Add one before the second release rather than pointing this at a
file that documents a single version.

## Required Spec Kit Version

```
>=1.0.0,<2.0.0
```

The upper bound is deliberate. 1.0.6 is the only version anything here has been run against,
and the honest range is the tested one.

## Required Tools (optional)

```markdown
- python3 (>=3.10) - required
- PyYAML (>=6.0) - required, via `pip install -r .specify/extensions/openup/requirements.txt`
- jsonschema (>=4.18) - required, same file
- referencing (>=0.30) - required, same file
```

## Number of Commands

```
9
```

## Number of Hooks (optional)

```
4
```

## Tags

```
governance, traceability, risk, lifecycle, openup
```

## Key Features

```markdown
- Nine `speckit.openup.*` commands covering phase, iteration, WBS, risk, traceability, behaviour, gate and audit.
- A three-way exit contract across every validator — `0` pass, `1` governance failure, `2` could-not-evaluate — so a check that could not run is never reported as a check that passed.
- A seven-level work breakdown structure in which the ID segment count *is* the level, with level 7 requiring an owner, an iteration and at least one bound requirement.
- A risk register with computed exposure (probability × impact) whose mitigations must name WBS nodes rather than prose, so "we will monitor it" cannot close a risk.
- Bi-directional traceability over 14 relations, stored once in active voice with inverses derived at load time, where every edge carries provenance: `derived`, `asserted` or `approved`.
- Four hooks (`after_specify`, `after_plan`, `after_tasks`, `after_implement`) that keep the graph current without an agent being asked to remember.
```

## Testing Checklist

All five boxes are checked, and each was exercised rather than assumed:

| Box | How it was verified |
|---|---|
| Installs successfully via download URL | `specify extension add openup --from <the URL above>` → exit 0, 9 commands registered |
| All commands execute without errors | the 9 skills register under `.claude/skills/`; the 13 validators they invoke are covered by 257 tests against the real engine |
| Documentation is complete and accurate | `docs/guide/using-specup.md` documents every check id, config key and gate condition, each traced to the code that implements it |
| No security vulnerabilities identified | no network calls, no credential handling, no shell interpolation of user input; all validators are read-only except the explicit `--write` paths |
| Tested on at least one real project | clean `specify init` project, spec-kit 1.0.6 |

## Submission Requirements

All six boxes are checked. `extension.yml` sits at the archive root (the layout
`install_from_zip` expects), `README.md` and `LICENSE` (MIT) are in the repository, and the
release is tagged `v0.1.0`.

## Testing Details

```markdown
**Tested on:**
- Linux (Ubuntu), Python 3.13, Spec Kit 1.0.6

**Test project:** a throwaway `specify init --here --integration claude` project, deliberately
not the SpecUP repository — local paths there would mask a broken catalog.

**Test scenarios:**
1. `specify extension add openup --from https://github.com/anvigo12/specup/releases/download/v0.1.0/openup-0.1.0.zip` → exit 0, 9 commands listed.
2. `specify extension list` → `OpenUP Governed Lifecycle (v0.1.0)`, `Commands: 9 | Hooks: 4 | Status: Enabled`.
3. `pip install -r .specify/extensions/openup/requirements.txt`, then `init_openup.py --program "Verify"` → 34 files created, 1 preserved.
4. `audit.py` on that fresh scaffold → **exit 1**, naming `WBS-004`, `TRC-000` and three failing gate conditions. Exit 1 is the correct answer here: an empty plan is not a valid plan. Exit 2 would have meant the dependencies were missing and nothing could be evaluated.
5. Archive digest checked three ways — as downloaded from the release, as built locally, and as pinned in the publisher's catalog. All three agree: `012e11f5949060d5…`.

**Automated suite:** 257 tests pass with spec-kit importable; 249 pass and 8 skip without it.
The 8 skip rather than fake, because a green test that never ran the engine proves less than
an honest skip.
```

## Example Usage

````markdown
```bash
# Install the extension directly from the release
specify extension add openup --from https://github.com/anvigo12/specup/releases/download/v0.1.0/openup-0.1.0.zip

# Its validators need three Python packages; without them every check exits 2
python3 -m pip install -r .specify/extensions/openup/requirements.txt

# Scaffold the governance tree
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "Fleet Telemetry"

# Then, from an agent:
/speckit.openup.wbs                          # build the seven-level breakdown
/speckit.openup.risk                         # register risks, bind mitigations to WBS nodes
/speckit.openup.trace                        # derive and validate the traceability graph
/speckit.openup.gate LIFECYCLE_OBJECTIVES    # evaluate the milestone against evidence
```

The gate is the part that actually stops anything. It reports which conditions failed and
why, and a phase cannot advance past it.
````

## Proposed Catalog Entry

```json
{
  "openup": {
    "name": "OpenUP Governed Lifecycle",
    "id": "openup",
    "description": "Adds the OpenUP lifecycle to Spec Kit: phases, iterations, a seven-level WBS, an executable risk register, bi-directional traceability, and machine-checkable milestone gates.",
    "author": "Aniket Gore",
    "version": "0.1.0",
    "download_url": "https://github.com/anvigo12/specup/releases/download/v0.1.0/openup-0.1.0.zip",
    "sha256": "012e11f5949060d57bef2c5ea15772e4649fc92d723e171a85e6230fb87cb46f",
    "repository": "https://github.com/anvigo12/specup",
    "homepage": "https://github.com/anvigo12/specup",
    "documentation": "https://github.com/anvigo12/specup/blob/main/docs/guide/using-specup.md",
    "license": "MIT",
    "category": "process",
    "effect": "read-write",
    "requires": {
      "speckit_version": ">=1.0.0,<2.0.0",
      "tools": [
        { "name": "python3", "version": ">=3.10", "required": true }
      ]
    },
    "provides": {
      "commands": 9,
      "hooks": 4
    },
    "tags": ["governance", "traceability", "risk", "lifecycle", "openup"],
    "verified": false,
    "downloads": 0,
    "stars": 0,
    "created_at": "2026-09-13T00:00:00Z",
    "updated_at": "2026-09-13T00:00:00Z"
  }
}
```

`sha256` is included even though most community entries omit it. It is verified after
download, so it catches a swapped or corrupted release asset regardless of the transport.

## Additional Context

```markdown
**This listing is for discovery; it is not the install route.** The community catalog is
`install_allowed: false`, so `specify extension add openup` resolves the entry and then
refuses it. Users install by registering SpecUP's own catalog first:

    specify extension catalog add https://raw.githubusercontent.com/anvigo12/specup/main/catalog/extensions.json \
      --name specup --install-allowed --priority 0

That is said plainly in the linked documentation rather than left for users to meet at the
error message.

**The extension is one of three layers and is usually not installed alone.** The
`openup-governance` preset (submitted separately) composes the same governance into Spec Kit's
own constitution, spec, plan and tasks templates, and four phase workflows carry the gates
that actually halt a run. The `specup` bundle installs all six components together and is the
intended entry point.

**On what this does and does not enforce.** Extensions and presets are prompt-level: they
change what an agent is told. Only a workflow `shell` step's exit code stops anything. The
documentation says so directly rather than implying the commands are themselves enforcement.
```
