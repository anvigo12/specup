# `[Bundle]: Add specup` — submission body

Paste into the **Bundle Submission** issue form at
<https://github.com/github/spec-kit/issues/new?template=bundle_submission.yml>.

Do not apply a label. A maintainer applies `bundle-submission` during triage. See
[the runbook](../publishing-to-spec-kit.md#7-optional--submit-for-discovery).

This is the submission that matters most of the three: the bundle is SpecUP's intended entry
point, and the other two components are rarely installed alone.

---

**Title:** `[Bundle]: Add specup — SpecUP OpenUP Governed Lifecycle`

## Bundle ID

```
specup
```

## Bundle Name

```
SpecUP — OpenUP Governed Lifecycle
```

## Version

```
0.1.0
```

## Role or Team

```
governance
```

## Description

```
Installs the full OpenUP governance stack: the openup extension (validators, schemas, commands), the openup-governance preset, and the four phase workflows whose gates halt a run on a failing verdict.
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
https://github.com/anvigo12/specup/releases/download/v0.1.0/specup-0.1.0.zip
```

## Documentation URL

```
https://github.com/anvigo12/specup/blob/main/bundles/specup/README.md
```

## License

```
MIT
```

## Required Spec Kit Version

```
>=1.0.0,<2.0.0
```

## Integration Target (optional)

Leave empty. The bundle is integration-agnostic — `bundle.yml` pins none, and it was verified
against a `--integration claude` project only because one had to be chosen.

## Components Provided

```markdown
- extensions: openup@0.1.0
- presets: openup-governance@0.1.0
- workflows: openup-inception@0.1.0, openup-elaboration@0.1.0, openup-construction@0.1.0, openup-transition@0.1.0
- steps: none
```

Six components. Install order is not ours to choose — `BundleManifest.components` fixes it as
extensions → presets → steps → workflows, which is the order this stack needs anyway: the
preset's guidance points at validator paths the extension creates.

## Required Component Catalogs

```markdown
Three, all served over HTTPS from the project repository. Users add them once per project
before `specify bundle install specup` can resolve anything:

- Extensions: https://raw.githubusercontent.com/anvigo12/specup/main/catalog/extensions.json
- Presets:    https://raw.githubusercontent.com/anvigo12/specup/main/catalog/presets.json
- Workflows:  https://raw.githubusercontent.com/anvigo12/specup/main/catalog/workflows.json

A fourth registers the bundle itself, for the `specify bundle install specup` form:

- Bundles:    https://raw.githubusercontent.com/anvigo12/specup/main/catalog/bundles.json

None of the six components is in Spec Kit's `default` catalog, and the `community` catalog is
discovery-only, so these are required rather than optional. Every entry pins a `sha256`.
```

## Tags

```
governance, openup, lifecycle, traceability, wbs
```

## Key Features

```markdown
- Installs all six components at pinned versions in one command, which is the only place in Spec Kit where "these things go together, at these versions" can be stated and acted on.
- The four phase workflows carry the enforcement. Extensions and presets are prompt-level — they change what an agent is told — but a workflow `shell` step's exit code is the only thing that actually halts a run, and the gates live there.
- A three-way exit contract throughout: `0` pass, `1` governance failure, `2` could-not-evaluate. A gate that cannot find its evidence fails rather than skipping, and a validator that could not run is never reported as a pass.
- Version pins are checked against each component's own manifest before anything is written, so a drifted pin aborts the install instead of producing a half-governed project.
- Reproducible archives — fixed member timestamps, sorted entries, normalized permissions — so a rebuild of an unchanged component yields an identical digest and a rebuild is distinguishable from a tampered artifact.
- Ships three governance standards as bundled hard rules an agent reads: 65 coding rules (railway-oriented error handling, RFC 9457 problem details, failure across service boundaries), 56 security practices, and 21 language rules.
```

## Testing Checklist

All seven boxes are checked. Each was run against the published 0.1.0 release:

| Box | Result |
|---|---|
| `specify bundle validate --path bundles/specup` | `✓ specup is well-formed and valid` |
| `specify bundle build` produces the submitted artifact | `specup-0.1.0.zip`, digest matches the release asset byte for byte |
| Installs from the built artifact | `specify bundle install ./specup-0.1.0.zip` → `✓ Installed 'specup' (6 added, 0 already present)` |
| The submitted distribution path tested end to end, including bundle-ID install from an install-allowed catalog | `specify bundle install specup` after `bundle catalog add … --policy install-allowed` → same result |
| Installation tested in a clean Spec Kit project | throwaway `specify init` project, not the SpecUP repository |
| Required component catalogs documented and included in testing | all four registered first; without them the components do not resolve |
| Documentation complete and accurate | the linked README covers both install routes, uninstall for each, and why they cannot be collapsed |

## Submission Requirements

All six boxes are checked. `bundle.yml` is valid by Spec Kit's own validator, the README
explains the role, the six installed components and both install routes, `LICENSE` (MIT) is in
the repository, the release is tagged `v0.1.0`, the bundle id matches the manifest, and every
component reference is pinned to an exact version.

## Testing Details

```markdown
**Tested on:**
- Linux (Ubuntu), Python 3.13, Spec Kit 1.0.6

**Test project:** a throwaway `specify init --here --integration claude` project. Deliberately
not the SpecUP repository, where local paths would mask a broken catalog.

**Test scenarios:**
1. Registered all four catalogs. Note the flags differ per primitive: extension and preset need `--name` and `--install-allowed`, workflow installs by default, and bundle takes `--policy install-allowed`.
2. `specify bundle install specup` → `✓ Installed 'specup' (6 added, 0 already present)`.
3. `specify bundle list` → `specup v0.1.0 (6 components)`. The component count is the check that matters: **0** would mean the bundle recorded itself over components already present rather than installing anything.
4. `specify extension list` → `OpenUP Governed Lifecycle (v0.1.0)`, `Commands: 9 | Hooks: 4`.
5. `specify workflow list` → all four `openup-*` workflows.
6. `specify preset resolve spec-template` → `[base] core → [append] openup-governance v0.1.0`.
7. `pip install -r .specify/extensions/openup/requirements.txt`, `init_openup.py --program "Verify"` → 34 created, 1 preserved; the three standards land with 65, 56 and 21 rules.
8. `audit.py` on the fresh scaffold → **exit 1**, naming `WBS-004`, `TRC-000` and three failing gate conditions. Exit 1 is correct on an empty plan; exit 2 would have meant the dependencies were missing.
9. Also installed from the downloaded artifact — `specify bundle install ./specup-0.1.0.zip` — with the same result, confirming the local-path route independently of the bundle catalog.
10. Digests checked three ways for `openup`, `openup-governance` and `specup`: as downloaded from the release, as built locally, and as pinned in the catalog. All three agree.

**Automated suite:** 257 tests pass with spec-kit importable; 249 pass and 8 skip without it.
One of them rebuilds every component from source and compares the digest against the committed
catalog, so content changing under an unchanged version fails the build — the one defect that
installs cleanly and leaves two different `0.1.0`s in the world.
```

## Example Usage

````markdown
```bash
# One-time per project: register SpecUP's catalogs. The flags differ per primitive.
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog
specify extension catalog add $BASE/extensions.json --name specup --install-allowed --priority 0
specify preset    catalog add $BASE/presets.json    --name specup --install-allowed --priority 0
specify workflow  catalog add $BASE/workflows.json  --name specup
specify bundle    catalog add $BASE/bundles.json    --policy install-allowed --priority 0

# Install all six components at their pinned versions
specify bundle install specup

# The validators need three Python packages; without them every check exits 2
python3 -m pip install -r .specify/extensions/openup/requirements.txt

# Or install from a downloaded artifact instead of the bundle catalog
curl -L -o specup-0.1.0.zip https://github.com/anvigo12/specup/releases/download/v0.1.0/specup-0.1.0.zip
specify bundle install ./specup-0.1.0.zip

# Scaffold, then run a governed phase
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "Fleet Telemetry"
specify workflow run openup-inception
```

The workflow is where enforcement lives. Its gate step halts the run on a failing verdict
rather than reporting and continuing.
````

## Proposed Catalog Entry

```json
{
  "specup": {
    "name": "SpecUP — OpenUP Governed Lifecycle",
    "id": "specup",
    "version": "0.1.0",
    "role": "governance",
    "description": "Installs the full OpenUP governance stack: the openup extension (validators, schemas, commands), the openup-governance preset, and the four phase workflows whose gates halt a run on a failing verdict.",
    "author": "Aniket Gore",
    "license": "MIT",
    "download_url": "https://github.com/anvigo12/specup/releases/download/v0.1.0/specup-0.1.0.zip",
    "sha256": "8906da8726042852cfec5fc8fb7bdb4056379d0057b40f927c3d1e4a14c26f16",
    "repository": "https://github.com/anvigo12/specup",
    "requires": {
      "speckit_version": ">=1.0.0,<2.0.0"
    },
    "provides": {
      "extensions": 1,
      "presets": 1,
      "steps": 0,
      "workflows": 4
    },
    "tags": ["governance", "openup", "lifecycle", "traceability", "wbs"],
    "verified": false
  }
}
```

## Additional Context

```markdown
**Component resolution needs three extra catalogs.** The bundle entry itself is enough to
resolve `specify bundle install specup`, but the six components it names are not in Spec Kit's
`default` catalog and the `community` catalogs are discovery-only, so the extension, preset and
workflow catalogs above must be registered first. This is stated first in every install
document rather than left to surface as a resolution error.

**What this bundle actually enforces.** Extensions and presets are prompt-level — they change
what an agent is told, and an agent can ignore them. Only a workflow `shell` step's exit code
halts a run. The four phase workflows are in the bundle for that reason, and the documentation
says so plainly rather than implying the commands are themselves enforcement.

**Two limits stated up front, in the project's own docs:** nothing here parses a contract
document, and an approval binds content rather than a human — the signature proves the bytes
have not changed since approval, not who approved them.

**Related submissions:** the `openup` extension and the `openup-governance` preset are
submitted separately. They are the same release and are pinned by this bundle.
```
