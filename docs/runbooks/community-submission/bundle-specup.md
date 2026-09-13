### Bundle ID

specup

### Bundle Name

SpecUP — OpenUP Governed Lifecycle

### Version

0.1.0

### Role or Team

governance

### Description

Installs the full OpenUP governance stack: the openup extension (validators, schemas, commands), the openup-governance preset, and the four phase workflows whose gates halt a run on a failing verdict.

### Author

Aniket Gore

### Repository URL

https://github.com/anvigo12/specup

### Download URL

https://github.com/anvigo12/specup/releases/download/v0.1.0/specup-0.1.0.zip

### Documentation URL

https://github.com/anvigo12/specup/blob/main/bundles/specup/README.md

### License

MIT

### Required Spec Kit Version

>=1.0.0,<2.0.0

### Integration Target (optional)

_No response_

### Components Provided

- extensions: `openup@0.1.0`
- presets: `openup-governance@0.1.0`
- workflows: `openup-inception@0.1.0`, `openup-elaboration@0.1.0`, `openup-construction@0.1.0`, `openup-transition@0.1.0`
- steps: none

Six components. Install order is not ours to choose — `BundleManifest.components` fixes it as
extensions → presets → steps → workflows, which is the order this stack needs anyway, since the
preset's guidance points at validator paths the extension creates.

### Required Component Catalogs

Three, all served over HTTPS from the project repository. Users register them once per project,
before `specify bundle install specup` can resolve anything:

- Extensions: https://raw.githubusercontent.com/anvigo12/specup/main/catalog/extensions.json
- Presets: https://raw.githubusercontent.com/anvigo12/specup/main/catalog/presets.json
- Workflows: https://raw.githubusercontent.com/anvigo12/specup/main/catalog/workflows.json

A fourth registers the bundle itself, for the `specify bundle install specup` form:

- Bundles: https://raw.githubusercontent.com/anvigo12/specup/main/catalog/bundles.json

None of the six components is in Spec Kit's `default` catalog, and the `community` catalogs are
discovery-only, so these are required rather than optional. Every entry pins a `sha256`.

### Tags

governance, openup, lifecycle, traceability, wbs

### Key Features

- Installs all six components at pinned versions in one command — the only place in Spec Kit where "these things go together, at these versions" can be both stated and acted on.
- The four phase workflows carry the enforcement. Extensions and presets are prompt-level; a workflow `shell` step's exit code is the only thing that actually halts a run, and the gates live there.
- A three-way exit contract throughout: `0` pass, `1` governance failure, `2` could-not-evaluate. A gate that cannot find its evidence fails rather than skipping, and a check that could not run is never reported as a pass.
- Version pins are checked against each component's own manifest before anything is written, so a drifted pin aborts the install instead of producing a half-governed project.
- Reproducible archives — fixed member timestamps, sorted entries, normalized permissions — so an unchanged component rebuilds to an identical digest and a rebuild stays distinguishable from a tampered artifact.
- Ships three governance standards as bundled rules an agent reads: 65 coding rules (railway-oriented error handling, RFC 9457 problem details, failure across service boundaries), 56 security practices, and 21 language rules.

### Testing Checklist

- [x] Validation succeeds with `specify bundle validate --path <bundle-directory>`
- [x] Build succeeds with `specify bundle build --path <bundle-directory>` and produces the submitted artifact
- [x] Bundle installs successfully from the built artifact
- [x] The submitted distribution path was tested end to end, including bundle-ID installation from an install-allowed catalog when a catalog entry is proposed
- [x] Installation was tested in a clean Spec Kit project
- [x] Required component catalogs are documented and were included in testing, or no extra catalogs are required
- [x] Documentation is complete and accurate

### Submission Requirements

- [x] Valid `bundle.yml` manifest included
- [x] README.md explains the bundle's intended role, installed components, and installation steps
- [x] LICENSE file included
- [x] GitHub release created with a version tag
- [x] Bundle ID matches the manifest and follows naming conventions
- [x] Every extension, preset, workflow, and step reference is pinned where the manifest requires a version

### Testing Details

**Tested on:** Linux (Ubuntu), Python 3.13, Spec Kit 1.0.6

**Test project:** a throwaway `specify init --here --integration claude` project — deliberately
not the SpecUP repository, where local paths would mask a broken catalog.

**Test scenarios:**

1. Registered all four catalogs. The flags differ per primitive, which is worth noting for anyone reproducing this: extension and preset need `--name` and `--install-allowed`, workflow installs by default, and bundle takes `--policy install-allowed`.
2. `specify bundle install specup` → `✓ Installed 'specup' (6 added, 0 already present)`.
3. `specify bundle list` → `specup v0.1.0 (6 components)`. The component count is the check that matters: **0** would mean the bundle recorded itself over components already present rather than installing anything.
4. `specify extension list` → `OpenUP Governed Lifecycle (v0.1.0)`, `Commands: 9 | Hooks: 4`.
5. `specify workflow list` → all four `openup-*` workflows.
6. `specify preset resolve spec-template` → `[base] core → [append] openup-governance v0.1.0`.
7. `pip install -r .specify/extensions/openup/requirements.txt`, then `init_openup.py --program "Verify"` → `34 created, 1 preserved`. The three standards land with 65, 56 and 21 rules respectively.
8. `audit.py` on the fresh scaffold → **exit 1**, naming `WBS-004`, `TRC-000` and three failing gate conditions. Exit 1 is correct on an empty plan; exit 2 would have meant the dependencies were missing and nothing could be evaluated.
9. Separately, installed from the downloaded artifact — `curl -L -o specup-0.1.0.zip <download url>` then `specify bundle install ./specup-0.1.0.zip` — with the same `6 added` result, confirming the local-path route independently of the bundle catalog.
10. `specify bundle validate --path bundles/specup` → `✓ specup is well-formed and valid`.
11. Digests checked three ways for `openup`, `openup-governance` and `specup`: as downloaded from the release, as built locally, and as pinned in the catalog. All three agree; the bundle artifact is `8906da8726042852cfec5fc8fb7bdb4056379d0057b40f927c3d1e4a14c26f16`.

**Automated suite:** 257 tests pass with spec-kit importable; 249 pass and 8 skip without it.
One of them rebuilds every component from source and compares the digest against the committed
catalog, so content changing under an unchanged version fails the build — the one defect that
installs cleanly and leaves two different `0.1.0`s in the world.

### Example Usage

```markdown
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

# The workflow is where enforcement lives. Its gate step halts the run on a
# failing verdict rather than reporting it and continuing.
```

### Proposed Catalog Entry

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

### Additional Context

**Repository layout, for validation.** This is a monorepo: `bundle.yml` is at
`bundles/specup/bundle.yml`, with `README.md` and `LICENSE` (MIT) at the repository root.

**Component resolution needs three extra catalogs.** The bundle entry alone is enough to
resolve `specify bundle install specup`, but the six components it names are not in Spec Kit's
`default` catalog and the `community` catalogs are discovery-only, so the extension, preset and
workflow catalogs listed above must be registered first. Every install document leads with that
rather than letting it surface as a resolution error.

**The four workflows are not separately submitted.** There is no workflow submission template
and no `add-community-workflow` automation, so they have no route into
`workflows/catalog.community.json`. They are listed here under *Components Provided* instead of
hand-editing that catalog.

**What this bundle actually enforces.** Extensions and presets are prompt-level — they change
what an agent is told, and an agent can ignore them. Only a workflow `shell` step's exit code
halts a run. The four phase workflows are in the bundle for exactly that reason, and the
documentation says so plainly rather than implying the commands are themselves enforcement.

**Two limits stated up front, in the project's own docs:** nothing here parses a contract
document, and an approval binds content rather than a human — the signature proves the bytes
have not changed since approval, not who approved them.

**Related submissions.** The `openup` extension and the `openup-governance` preset are submitted
separately. They are the same 0.1.0 release and are pinned by this bundle.
