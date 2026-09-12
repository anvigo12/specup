# Runbook — Publishing SpecUP to Spec Kit

**Audience:** whoever is cutting a SpecUP release.
**Outcome:** anyone can run `specify bundle install specup` and get the whole governed stack.
**Time:** ~30 minutes the first time, ~10 after that.

---

## 0. Read this first: the constraint that shapes every step

Spec Kit has two catalog tiers per primitive, and only one of them installs.

| Tier | Priority | `install_allowed` |
|---|---|---|
| `default` | 1 | **true** |
| `community` | 2 | **false** — discovery only |

This is uniform across extensions, presets, workflows and steps
(`extensions/__init__.py:3828`, `presets/__init__.py:4706`,
`workflows/catalog.py:464` and `:1161`). Installing from a discovery-only source fails with:

```
Preset 'openup-governance' is from a discovery-only catalog; installation is not allowed.
```

And the `default` catalog is not a third-party channel at all:

```
default catalog: 4 entries, 4 bundled, 0 with download_url
authors: ['spec-kit-core']
```

`bundled: true` with no `download_url` means "already inside the spec-kit wheel". Getting
listed there is not publishing — it is asking GitHub to vendor SpecUP into Spec Kit itself.

**Therefore: SpecUP publishes by hosting its own catalog.** This is the supported third-party
route, not a workaround — `adrkit`, in the community catalog today, points its `download_url`
at its own GitHub release and works exactly this way.

Two consequences to accept up front:

- Users run four one-time `catalog add` commands before their first install. There is no way
  around this short of Spec Kit vendoring SpecUP.
- Submitting to the **community** catalog is still worth doing, but understand what it buys:
  search visibility. The install still comes from our catalog.

### Verified, not assumed

Every claim in this runbook was exercised against spec-kit 1.0.6 using a catalog served on
`127.0.0.1` (`is_https_or_localhost_http` permits loopback, which is what makes the route
testable without publishing anything):

| Step | Result |
|---|---|
| `specify extension search openup` | listed, `Catalog: specup` |
| `specify extension add openup` | exit 0, 9 commands registered |
| `specify preset add openup-governance` | exit 0, `installed (priority 10)` |
| same with a wrong `sha256` | exit 1, `Integrity check failed for 'openup'` |

---

## 1. Pre-flight

```bash
task release:check
```

That runs both test suites, validates `bundle.yml` with Spec Kit's own validator, builds the
bundle artifact, and builds the release archives. Do not continue past a red.

Confirm the version pins are what you intend to publish. `bundle.yml` pins each component and
`tests/test_bundle.py::test_pinned_versions_match_the_components` fails if a pin has drifted
from the component's own manifest — but it cannot tell you that you *forgot* to bump.

```bash
grep -n 'version:' bundles/specup/bundle.yml
```

Also decide whether `requires.speckit_version` is still honest. It pins `>=1.0.0,<2.0.0`
because 1.0.6 is the only version anything here has been run against. **Widen it only after
actually testing the wider range**, not because a user asked.

---

## 2. Build the release archives

```bash
task release:archives
```

Produces `dist/<component>-<version>.zip` for all six components and `dist/SHA256SUMS`.

Two properties matter:

- **The component manifest sits at the archive root.** `extension.yml` at the top level, not
  under a wrapper directory. This is the layout `install_from_zip` expects; get it wrong and
  the install fails after download.
- **The archives are reproducible.** Fixed member timestamps, sorted entries, normalized
  permissions. Rebuilding an unchanged component gives a byte-identical zip and therefore an
  identical digest. Without this you cannot tell a rebuild from a tampered artifact.

Verify reproducibility if you have any doubt:

```bash
cp dist/SHA256SUMS /tmp/sums1 && task release:archives && diff /tmp/sums1 dist/SHA256SUMS
```

---

## 3. Cut the GitHub release

```bash
VERSION=0.1.0
git tag -a "v$VERSION" -m "SpecUP $VERSION"
git push origin "v$VERSION"
gh release create "v$VERSION" dist/*.zip dist/SHA256SUMS \
  --title "SpecUP $VERSION" --notes-file docs/runbooks/release-notes-$VERSION.md
```

The asset URLs are then stable and predictable:

```
https://github.com/<owner>/specup/releases/download/v0.1.0/openup-0.1.0.zip
```

**Never move or re-upload an asset under an existing tag.** The catalog pins its digest; a
replaced asset makes every install fail the integrity check, which is the system working
correctly and will still look like an outage.

---

## 4. Generate the catalog files

Four JSON files, one per primitive, committed to the repo under `catalog/` and served over
HTTPS from `raw.githubusercontent.com`.

| File | Root key | Consumed by |
|---|---|---|
| `catalog/extensions.json` | `extensions` | `specify extension add` |
| `catalog/presets.json` | `presets` | `specify preset add` |
| `catalog/workflows.json` | `workflows` | `specify workflow add` |
| `catalog/bundles.json` | `bundles` | `specify bundle install` |

**Take the `sha256` values from `dist/SHA256SUMS`. Never type one by hand.** The digest in the
catalog must be the digest of the asset actually attached to the release; if they diverge,
every install fails at the integrity check.

`sha256` is technically optional — `verify_archive_sha256` skips a `None` — and omitting it is
indefensible. It is verified *after* download, so it catches a swapped or corrupted release
asset even though the transport was HTTPS.

### `catalog/extensions.json`

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-09-12T00:00:00Z",
  "catalog_url": "https://raw.githubusercontent.com/<owner>/specup/main/catalog/extensions.json",
  "extensions": {
    "openup": {
      "id": "openup",
      "name": "OpenUP Governed Lifecycle",
      "version": "0.1.0",
      "description": "Adds the OpenUP lifecycle to Spec Kit: phases, iterations, a seven-level WBS, an executable risk register, bi-directional traceability, and machine-checkable milestone gates.",
      "author": "Aniket Gore",
      "repository": "https://github.com/<owner>/specup",
      "license": "MIT",
      "category": "process",
      "effect": "read-write",
      "download_url": "https://github.com/<owner>/specup/releases/download/v0.1.0/openup-0.1.0.zip",
      "sha256": "<from dist/SHA256SUMS>",
      "requires": { "speckit_version": ">=1.0.0,<2.0.0" },
      "provides": { "commands": 9, "hooks": 4 },
      "tags": ["governance", "openup", "lifecycle", "traceability"],
      "verified": false
    }
  }
}
```

`presets.json` and `workflows.json` follow the same shape under their own root key. The
enclosing key **is** the authoritative id — an entry whose inner `id` disagrees with its key is
rejected, so a malformed catalog cannot advertise one id and serve another.

### `catalog/bundles.json`

This is the file that makes `specify bundle install specup` work. Its entry mirrors
`bundles/specup/bundle.yml`; the components are resolved from the three catalogs above.

```json
{
  "schema_version": "1.0",
  "bundles": {
    "specup": {
      "id": "specup",
      "name": "SpecUP — OpenUP Governed Lifecycle",
      "version": "0.1.0",
      "role": "governance",
      "description": "The full OpenUP governance stack: extension, preset, and four phase workflows whose gates halt a run on a failing verdict.",
      "author": "Aniket Gore",
      "license": "MIT",
      "tags": ["governance", "openup", "lifecycle", "traceability", "quality-gates"]
    }
  }
}
```

---

## 5. Publish and verify from a clean project

Push the catalog files, then verify as a **user would**, in a throwaway project — not in this
repo, where local paths would mask a broken catalog.

```bash
mkdir /tmp/specup-verify && cd /tmp/specup-verify
specify init --here --integration claude

BASE=https://raw.githubusercontent.com/<owner>/specup/main/catalog
specify extension catalog add $BASE/extensions.json --policy install-allowed --priority 0
specify preset    catalog add $BASE/presets.json    --policy install-allowed --priority 0
specify workflow  catalog add $BASE/workflows.json  --policy install-allowed --priority 0
specify bundle    catalog add $BASE/bundles.json    --policy install-allowed --priority 0

specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt
```

Then confirm all four layers actually landed:

```bash
specify extension list                  # openup, 9 commands
specify preset resolve spec-template    # [append] openup-governance v0.1.0
specify workflow list                   # four openup-* workflows
specify bundle list                     # specup, with a NON-ZERO component count

python3 .specify/extensions/openup/scripts/python/init_openup.py --program "Verify"
python3 .specify/extensions/openup/scripts/python/audit.py; echo "exit=$?"
```

The audit **must exit 1** on a fresh scaffold — an empty plan is not a valid plan. Exit 2 means
the Python dependencies did not install and the validators cannot evaluate anything.

### The check that proves the release actually worked

```bash
specify bundle list
```

If it says **0 components**, the bundle installed nothing and merely recorded itself over
components that were already present. That is the failure mode described in
`bundles/specup/README.md`, and in a clean project it means the component catalogs are not
resolving. A correct catalog install reports six.

---

## 6. Retire the development installer

Once step 5 passes from a clean project:

1. Delete `bundles/specup/install.py` and its two tests in `tests/test_bundle.py`
   (`test_installer_reads_the_manifest_rather_than_restating_it`,
   `test_installer_documents_the_zero_component_record`).
2. Replace the install sections in `README.md` and `bundles/specup/README.md` with the
   `catalog add` + `bundle install specup` sequence.
3. Drop the "specify bundle install cannot install this bundle" bullet from the README's
   Limitations — it stops being true the moment the catalog is live.

---

## 7. Optional — submit for discovery

Open a PR against `github/spec-kit` adding SpecUP to:

- `extensions/catalog.community.json`
- `presets/catalog.community.json`
- `workflows/catalog.community.json`

Model the entry on `adrkit`. Remember this makes SpecUP **findable, not installable** — users
still register our catalog to install. Say so in the entry's `documentation` link rather than
letting them discover it at the error message.

---

## Rollback

A bad release is recoverable because nothing is mutated in place:

| Situation | Action |
|---|---|
| Catalog points at a broken asset | Revert the catalog commit. Installs return to the previous version within the 1-hour cache TTL. |
| Asset is fine, digest is wrong | Fix the `sha256` in the catalog and commit. Never re-upload the asset. |
| Version should never have shipped | `gh release delete v<x>` **and** revert the catalog entry. A catalog pointing at a deleted asset fails downloads with no useful message. |

Users can force a refresh past the cache with `specify extension update` or by clearing
`.specify/extensions/.cache/`.

---

## Reference — catalog config files

Written by `specify <primitive> catalog add`; listed here for debugging.

| Primitive | Project-scoped file | Policy key |
|---|---|---|
| extension | `.specify/extension-catalogs.yml` | `install_allowed: true` |
| preset | `.specify/preset-catalogs.yml` | `install_allowed: true` |
| workflow | `.specify/workflow-catalogs.yml` | `install_allowed: true` |
| step | `.specify/step-catalogs.yml` | `install_allowed: true` |
| **bundle** | `.specify/bundle-catalogs.yml` | **`install_policy: install-allowed`** |

The bundler uses a different key from the other four. Hand-editing that file with
`install_allowed` yields a silently discovery-only source and an install that refuses for
reasons the error message does not explain. Use `catalog add`.

All catalog URLs must be HTTPS, or HTTP on loopback. `file://` is rejected by
`is_https_or_localhost_http`, which is why a local directory cannot stand in for a catalog
during testing — serve it on `127.0.0.1` instead.
