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

`specify` must be on PATH for the verification in step 5, which runs as a user would. The
build steps do not need it — the Taskfile uses `.venv/bin/specify`, created by `task venv` —
but step 5 deliberately does not, because a verification that borrows this repo's venv is not
verifying what a user gets.

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify --version
```

```bash
task release:check
```

That runs both test suites, validates `bundle.yml` with Spec Kit's own validator, builds the
bundle artifact, builds the release archives, and regenerates `catalog/`. Do not continue past
a red.

`tests/test_catalog.py` is the one to read the failure of carefully. It rebuilds every
component from the working tree and compares the digest against the committed catalog, so it
fails when content has changed under an unchanged version — the one defect that installs
cleanly and leaves two different `0.1.0`s in the world.

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

## 2. Build the archives and generate the catalog

```bash
task release:catalog
```

That chains the whole build: `bundle:build` produces `dist/specup-<version>.zip`,
`release:archives` produces `dist/<component>-<version>.zip` for all six components plus
`dist/SHA256SUMS`, and `build_catalog.py` writes the four files under `catalog/`.

`dist/SHA256SUMS` holds **seven** digests, not six. The bundle artifact is in there because
`bundles.json` pins a `sha256` exactly as the component catalogs do; without it,
`specify bundle install specup` fails with `Catalog entry 'specup' has no download_url;
cannot resolve its manifest`, which names neither the digest nor the missing archive.

Two properties matter:

- **The component manifest sits at the archive root.** `extension.yml` at the top level, not
  under a wrapper directory. This is the layout `install_from_zip` expects; get it wrong and
  the install fails after download.
- **The archives are reproducible.** Fixed member timestamps, sorted entries, normalized
  permissions. Rebuilding an unchanged component gives a byte-identical zip and therefore an
  identical digest. Without this you cannot tell a rebuild from a tampered artifact.

Verify reproducibility if you have any doubt:

```bash
cp dist/SHA256SUMS /tmp/sums1 && task --force release:archives && diff /tmp/sums1 dist/SHA256SUMS
```

`--force` is needed because the task is fingerprinted by `sources:` and will otherwise report
itself up to date, which is exactly the wrong answer to the question you are asking.

---

## 3. Cut the GitHub release

The assets go up before the catalog does. Step 2 has already generated `catalog/` against the
URLs this step creates, but those files stay uncommitted until step 4 — a catalog on `main`
pointing at assets that do not exist yet is live and broken.

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

### Re-cutting a tag that has already been pushed

Deleting the release *and* the tag and re-creating both at a new commit is a different act
from replacing an asset under a tag that stays put, and it is occasionally the right one —
when a release is hours old and a fix belongs *in* it rather than in a patch version nobody
needed. 0.1.0 was re-cut exactly once, to add the preset's `requires.extensions` declaration.

The precondition is checkable rather than a matter of judgement:

```bash
gh api repos/anvigo12/specup/releases/tags/v0.1.0 \
  --jq '.assets[] | "\(.name) \(.download_count)"'
```

If those counts are not fully accounted for by your own verification runs, someone is holding
the old bytes and you ship a new version instead. A digest that was correct yesterday and
differs today is indistinguishable from a compromise, and the integrity check cannot tell
which one it is looking at.

Order matters — release first, because a tag whose release is gone is inert:

```bash
gh release delete v0.1.0 --yes
git push origin :refs/tags/v0.1.0
git tag -d v0.1.0
git tag -a v0.1.0 -m "SpecUP 0.1.0"
git push origin v0.1.0
gh release create v0.1.0 dist/*.zip dist/SHA256SUMS --title … --notes-file …
```

Then **re-run step 5 in full**. The previous verification record describes bytes that no
longer exist, and a re-cut release nobody re-verified is worse than a patch release: the
version number still claims it was checked.

One thing you cannot fix from here — anyone who already fetched the old tag keeps it, because
`git fetch` will not delete a local tag whose remote is gone. `git fetch --prune-tags` does,
and is what to tell a collaborator.

---

## 4. Publish the catalog files

Four JSON files, one per primitive, committed under `catalog/` and served over HTTPS from
`raw.githubusercontent.com`. They are **generated** by `tools/build_catalog.py` — do not
hand-edit them, and do not hand-copy a digest.

| File | Root key | Archive URL key | Consumed by |
|---|---|---|---|
| `catalog/extensions.json` | `extensions` | `download_url` | `specify extension add` |
| `catalog/presets.json` | `presets` | `download_url` | `specify preset add` |
| `catalog/workflows.json` | `workflows` | **`url`** | `specify workflow add` |
| `catalog/bundles.json` | `bundles` | `download_url` | `specify bundle install` |

**The workflow catalog is the odd one out.** `workflows/_commands.py:2224` reads
`info.get("url")`, and nothing falls back to `download_url`. A workflow entry written like the
other three fails with `Workflow 'openup-inception' does not have an install URL in the
catalog` while the file visibly contains a URL. The generator handles this; a hand-edit will
not. `tests/test_catalog.py::test_each_kind_uses_the_url_key_its_installer_actually_reads`
locks it in.

The enclosing key **is** the authoritative id — an entry whose inner `id` disagrees with its
key is rejected, so a malformed catalog cannot advertise one id and serve another.

`sha256` is technically optional — `verify_archive_sha256` skips a `None` — and omitting it is
indefensible. It is verified *after* download, so it catches a swapped or corrupted release
asset even though the transport was HTTPS. The generator refuses to emit an entry without one.

Push the catalog **after** step 3, never before. The digests point at release assets; a
catalog on `main` whose assets do not exist yet is a live catalog that fails every install.

```bash
git add catalog/ && git commit -m "Publish the SpecUP $VERSION catalog"
git push origin main
```

---

## 5. Verify from a clean project

Verify as a **user would**, in a throwaway project — not in this repo, where local paths would
mask a broken catalog.

**The four `catalog add` commands do not take the same flags.** This is the second thing that
costs an afternoon, because three of the four reject `--policy` outright and the fourth
requires it to install:

| Primitive | Required | To make it installable | Priority flag |
|---|---|---|---|
| extension | `--name` | `--install-allowed` | `--priority` |
| preset | `--name` | `--install-allowed` | `--priority` |
| workflow | — (`--name` optional) | nothing — it installs by default | none |
| bundle | — | `--policy install-allowed` (the default) | `--priority` |

Omitting `--install-allowed` on the first two is the quiet failure: the catalog registers,
`search` finds the component, and `add` refuses with *"is from a discovery-only catalog"*.

```bash
mkdir /tmp/specup-verify && cd /tmp/specup-verify
specify init --here --integration claude

BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog
specify extension catalog add $BASE/extensions.json --name specup --install-allowed --priority 0
specify preset    catalog add $BASE/presets.json    --name specup --install-allowed --priority 0
specify workflow  catalog add $BASE/workflows.json  --name specup
specify bundle    catalog add $BASE/bundles.json    --policy install-allowed --priority 0

specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt
```

### If an install fails right after you pushed a catalog fix

Clear the caches before believing the error. Each primitive caches its catalog JSON for about
an hour, and a stale cache is indistinguishable from a broken catalog:

```bash
rm -rf .specify/extensions/.cache .specify/presets/.cache .specify/workflows/.cache
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

## 6. Confirm the documentation matches what shipped

Done once, for 0.1.0, and worth re-reading at each release rather than assuming:

1. `README.md`, `bundles/specup/README.md`, `docs/guide/using-specup.md`,
   `new-project.md` and `existing-project.md` all lead with `catalog add` +
   `specify bundle install specup`.
2. The README's Limitations bullet says `specify bundle install` cannot reach an *unreleased
   working tree* — not that it cannot install the bundle. The second stopped being true the
   moment the catalog went live, and leaving it there tells users the supported route does
   not work.
3. The README's **Verified behavior** table records only what has actually been run. After
   step 5 passes, add the catalog-install row. Before it, the table must say the catalog
   route is not yet exercised.

**`bundles/specup/install.py` stays.** An earlier draft of this runbook said to delete it once
a catalog existed. That is wrong, because the two installers answer different questions:

| | `install.py` | `specify bundle install specup` |
|---|---|---|
| Installs | this working tree, unreleased edits included | a published version |
| Integrity | version pins checked against each component manifest | SHA-256 per archive, plus the pins |
| Network | none | `raw.githubusercontent.com`, `github.com` |
| Bundle record | owns 0 components | owns 6 |
| Used by | `task install PROJECT=…`, SpecUP's own development | every real project |

A catalog serves released archives pinned by digest, so by construction it cannot serve an
edit nobody has released. Deleting `install.py` would leave SpecUP's own developers running
four `specify … add --dev` commands by hand, in the right order, with no pin check — which is
the combination `bundle.yml` exists to prevent.

---

## 7. Optional — submit for discovery

Being listed in Spec Kit's own community catalogs makes SpecUP **findable, not installable**.
Those catalogs are discovery-only (section 0), so someone who finds SpecUP there still
registers our catalog to install it. Say that in the submission rather than letting them meet
it at the error message.

### Do not open a catalog pull request

An earlier draft of this step said to open one. That is wrong, and `CONTRIBUTING.md` says so
in as many words: a hand-edited catalog PR *"bypasses that validation and will be closed with
a pointer back to the issue flow."*

The route is a **submission issue** per primitive. A maintainer applies the
`extension-submission` / `preset-submission` / `bundle-submission` label during triage, which
starts an agentic workflow (`.github/workflows/add-community-*.md`) that validates the release,
verifies the `download_url` and digest, and opens the catalog PR itself. Do not apply the label
yourself and do not ask for it.

This applies to **new entries, version bumps and repairs alike** — an update is still an
update and gets the same validation.

### Three submissions, not four

| Primitive | Issue template | Lands in |
|---|---|---|
| extension `openup` | `[Extension]` | `extensions/catalog.community.json` |
| preset `openup-governance` | `[Preset]` | `presets/catalog.community.json` |
| bundle `specup` | `[Bundle]` | `bundles/catalog.community.json` |
| the four `openup-*` workflows | **none exists** | `workflows/catalog.community.json` |

`workflows/catalog.community.json` is real and populated, but there is no workflow submission
template and no `add-community-workflow` automation — so there is no documented route for the
four phase workflows. Leave them out. They install from our catalog either way, the bundle
submission lists them under *Components Provided*, and hand-editing that file to close the gap
is exactly the pull request the policy above rejects.

### Prepared bodies

[`community-submission/`](community-submission/) holds one file per submission with every field
filled from the release, and records which claims were verified by running them. The figures are
version-stamped; re-derive them at each update instead of resubmitting the previous release's.

Each file *is* the issue body, in the shape GitHub renders an issue form into — `### <field
label>` then the value, and literal `- [x]` boxes. The automation parses it that way, so a
free-form body will not validate. File with `gh issue create --body-file`, and read the filed
0.1.0 issues off that README's *What was filed* table.

### Pin `download_url` to a tag, never to `latest`

CONTRIBUTING requires `…/releases/download/<tag>/…`. `catalog/*.json` is already generated that
way, so copy the URL and digest from there rather than retyping either.

---

## Rollback

A bad release is recoverable because nothing is mutated in place:

| Situation | Action |
|---|---|
| Catalog points at a broken asset | Revert the catalog commit. Installs return to the previous version within the 1-hour cache TTL. |
| Asset is fine, digest is wrong | Fix the `sha256` in the catalog and commit. Never re-upload the asset. |
| Version should never have shipped | `gh release delete v<x>` **and** revert the catalog entry. A catalog pointing at a deleted asset fails downloads with no useful message. |

Users can force a refresh past the cache with `specify extension update` or by clearing the
per-primitive cache directories:

```bash
rm -rf .specify/extensions/.cache .specify/presets/.cache .specify/workflows/.cache
```

The TTL is about an hour. Until it expires, a fixed catalog and a broken one behave
identically, so clear the cache before diagnosing anything — including during step 5.

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
