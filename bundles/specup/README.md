# SpecUP Bundle

Installs the whole OpenUP governance stack as one unit: the `openup` extension, the
`openup-governance` preset, and the four phase workflows.

| Component | Version | Kind | Why it is here |
|---|---|---|---|
| `openup` | 0.1.0 | extension | The validators, JSON Schemas, config and `/speckit.openup.*` commands |
| `openup-governance` | 0.1.0 | preset | Composes governance into Spec Kit's own constitution, spec, plan, tasks, `/tasks` and `/implement` |
| `openup-inception` | 0.1.0 | workflow | Lifecycle Objectives gate |
| `openup-elaboration` | 0.1.0 | workflow | Lifecycle Architecture gate |
| `openup-construction` | 0.1.0 | workflow | Initial Operational Capability gate, with a risk-first fan-out over ready work |
| `openup-transition` | 0.1.0 | workflow | Product Release gate |

## Why a bundle at all

The preset tells an agent to run validators at
`.specify/extensions/openup/scripts/python/`. Those files are installed by the extension.

A preset manifest **can** say it needs one: `openup-governance` declares
`requires.extensions: [openup]`, and Spec Kit prints a named warning with the command that
resolves it. What it cannot do is act on that. The check runs *after* the install has already
succeeded, it never installs the dependency, and nothing refuses. **Declaring is not
enforcing.**

Installed alone, the preset is still a set of instructions pointing at files that are not
there. Every governance instruction reads as authoritative and every check it names silently
does not run — now with a warning somewhere above it in the scrollback. A bundle is the only
place in Spec Kit where "these three things go together, at these versions" is both stated
*and* acted on.

Install order matters and is not ours to choose: `BundleManifest.components` fixes it as
extensions → presets → steps → workflows, which is the order needed here.

## Install a release

The supported route. Register SpecUP's catalog once, then install by id:

```bash
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog
specify extension catalog add $BASE/extensions.json --name specup --install-allowed --priority 0
specify preset    catalog add $BASE/presets.json    --name specup --install-allowed --priority 0
specify workflow  catalog add $BASE/workflows.json  --name specup
specify bundle    catalog add $BASE/bundles.json    --policy install-allowed --priority 0

specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt
```

Spec Kit's `default` catalog holds only components vendored into the Spec Kit wheel, so
every third-party project publishes its own catalog. Registering it is the supported
route, not a workaround. Each archive is pinned by SHA-256 and the install aborts if the
bytes do not match.

## Install a working tree

`install.py` installs *this checkout*, unreleased edits and all:

```bash
python3 bundles/specup/install.py --project /path/to/your/spec-kit-project
python3 -m pip install -r /path/to/your/spec-kit-project/.specify/extensions/openup/requirements.txt
```

Add `--dry-run` to see the commands and the version-pin check without changing anything.

Use it when you are developing SpecUP, when you need a change that is not released, or
when the machine cannot reach `raw.githubusercontent.com` and `github.com`. `task install
PROJECT=…` calls it.

### Why the two cannot be collapsed

A bundle manifest references components by **id**, and ids resolve only against assets
shipped inside the Spec Kit wheel or a published catalog —
`specify_cli._assets._locate_bundled_{extension,preset,workflow}`. There is no `--dev` for
bundles. The manifest's `source:` key looks like the escape hatch, but it is parsed into
`ComponentRef.source` and then read by nothing in the install path. A local catalog is not
a way around it either: catalog URLs are checked by `is_https_or_localhost_http`, so
`file://` is rejected.

A catalog therefore serves released archives pinned by digest, which by construction is
not the tree you are editing. Pointing `specify bundle install` at a local `bundle.yml`
does not fill the gap — it fails in two ways, both verified against spec-kit 1.0.6:

```
components absent    Error: Extension 'openup' not found in any catalog.   (exit 1)
components present   ✓ Installed 'specup' (0 added, 6 already present).    (exit 0)
```

The second is the dangerous one. It reports success, but the record it writes contains
`contributed_components: []` and `specify bundle list` shows **0 components**. That is
Spec Kit behaving correctly, not a bug: it refuses to claim components it did not install
itself, so that removing a bundle can never uninstall something you installed separately
(the collateral-removal guard). The consequence is that `specify bundle remove specup`
removes nothing.

`install.py` performs the install the manifest describes, in the manifest's order, and
enforces the version pins the bundler enforces on the catalog route. That pin check is the
part worth having — it fails the install when `bundle.yml` and a component's own manifest
disagree, so the bundle can never document a combination that was never built.
`tools/build_catalog.py` applies the same check at release time; `install.py` applies it at
the moment the drift is introduced.

## Uninstall

After a **catalog install**, the bundle record owns its components and one command is
enough:

```bash
specify bundle remove specup
```

After an **`install.py` install**, the record owns nothing, so remove the components
directly:

```bash
specify preset remove openup-governance
specify extension remove openup
for p in inception elaboration construction transition; do
  specify workflow remove openup-$p
done
specify bundle remove specup        # drops the record
```

`specify bundle list` tells the two apart: a catalog install lists 6 components, an
`install.py` install lists 0.

## Publishing a new version

Nothing in `bundle.yml` changes shape — it is already what the catalog serves. Bump the
versions, rebuild, regenerate, and cut the release:
[`docs/runbooks/publishing-to-spec-kit.md`](../../docs/runbooks/publishing-to-spec-kit.md).

Re-check `requires.speckit_version` each time. It pins `>=1.0.0,<2.0.0`, which is narrower
than the components' own `>=0.9.0`/`>=0.8.5` floors, because 1.0.6 is the only version this
has been exercised against.
