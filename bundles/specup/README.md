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
Spec Kit has **no preset→extension dependency mechanism** — a preset manifest cannot
declare that it needs an extension, and nothing stops you installing one without the
other.

Installed alone, the preset is a set of instructions pointing at files that are not
there. Every governance instruction still reads as authoritative, and every check it
names silently does not run. A bundle is the only place in Spec Kit where "these three
things go together, at these versions" can be stated at all.

Install order matters and is not ours to choose: `BundleManifest.components` fixes it as
extensions → presets → steps → workflows, which is the order needed here.

## Install

```bash
python3 bundles/specup/install.py --project /path/to/your/spec-kit-project
python3 -m pip install -r /path/to/your/spec-kit-project/.specify/extensions/openup/requirements.txt
```

Add `--dry-run` to see the commands and the version-pin check without changing anything.

## Why not `specify bundle install`

Because it cannot work for an unpublished project, and it fails in two different ways
depending on what is already installed. Both were verified against spec-kit 1.0.6:

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

The cause is that a bundle manifest references components by **id**, and ids resolve only
against assets shipped inside the Spec Kit wheel or a published catalog —
`specify_cli._assets._locate_bundled_{extension,preset,workflow}`. There is no `--dev` for
bundles. The manifest's `source:` key looks like the escape hatch, but it is parsed into
`ComponentRef.source` and then read by nothing in the install path. A local catalog is not
a way around it either: catalog URLs are checked by `is_https_or_localhost_http`, so
`file://` is rejected.

`install.py` performs the install the manifest describes, in the manifest's order, and
enforces the version pins the bundler would have enforced had these components been
published. That pin check is the part worth having — it fails the install when
`bundle.yml` and a component's own manifest disagree, so the bundle can never document a
combination that was never built.

## Uninstall

Because the bundle record owns nothing, remove the components directly:

```bash
specify preset remove openup-governance
specify extension remove openup
for p in inception elaboration construction transition; do
  specify workflow remove openup-$p
done
specify bundle remove specup        # drops the record
```

## Publishing

When SpecUP reaches a catalog, `specify bundle install specup` becomes the real route,
`install.py` should be deleted, and this section replaced with the bundle id. Nothing in
`bundle.yml` needs to change — it is already what a catalog would serve.

The one thing to re-check first is `requires.speckit_version`. It pins `>=1.0.0,<2.0.0`,
which is narrower than the components' own `>=0.9.0`/`>=0.8.5` floors, because 1.0.6 is
the only version this has been exercised against.
