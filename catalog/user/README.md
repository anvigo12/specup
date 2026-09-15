# User-scope catalog configuration

Four files to copy into `~/.specify/`. They register SpecUP's catalogs **once per machine**,
so that every Spec Kit project on it can run `specify bundle install specup` with no
per-project setup.

```bash
curl -sSL -o ~/.specify/extension-catalogs.yml https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user/extension-catalogs.yml
curl -sSL -o ~/.specify/preset-catalogs.yml    https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user/preset-catalogs.yml
curl -sSL -o ~/.specify/workflow-catalogs.yml  https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user/workflow-catalogs.yml
curl -sSL -o ~/.specify/bundle-catalogs.yml    https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user/bundle-catalogs.yml
```

Or, from a clone: `mkdir -p ~/.specify && cp catalog/user/*.yml ~/.specify/`.

Read them first. They are four short files that decide where your machine downloads code from.

## Everything else in `catalog/` is generated; this directory is not

`catalog/*.json` is written by `task release:catalog` from the manifests and the built
digests. The files here are hand-authored and version-controlled as themselves.

## Why not `specify <primitive> catalog add`?

Because that command cannot write here. It calls `_require_specify_project()` and writes
to `<project>/.specify/<primitive>-catalogs.yml`; there is no `--user` flag on any of the
four. So the CLI route is **four commands in every project**, repeated forever, while the
files it writes are read from `~/.specify/` just as happily.

The resolution order is the same for all four primitives:

1. `SPECKIT_CATALOG_URL` (extensions only)
2. project `.specify/<primitive>-catalogs.yml`
3. user `~/.specify/<primitive>-catalogs.yml`
4. Spec Kit's built-in stack

## The part that is easy to get wrong

**Three of the four replace; one merges.**

For extensions, presets and workflows, a config file *replaces* the entire stack below it —
`get_active_catalogs` returns the first level that loads and never consults the next. So a
file listing only `specup` silently removes Spec Kit's own `default` and `community`
catalogs. Measured on a fresh project: `specify extension search` drops from **173
extensions to 1**. Core extensions still install, because those are vendored in the
spec-kit wheel, but everything genuinely remote becomes invisible.

That is why the three files here restate `default` and `community` verbatim, at their
built-in priorities (1 and 2), with `community` left `install_allowed: false`.

Bundles are the exception: `load_source_stack` merges by id across built-in → user →
project, so `bundle-catalogs.yml` carries only the `specup` entry and the built-ins survive.

**Priority is lowest-wins.** SpecUP sits at `0` so it resolves ahead of the built-ins.

## Per-project override still works

A project that needs something different keeps full control: write
`.specify/<primitive>-catalogs.yml` in that project and it wins outright. Remember that for
the three replacing primitives, an override is a *replacement* — restate every source you
still want, including these.

## Keeping them current

The four URLs point at `main`, so they follow the catalogs without edits. If a catalog is
ever renamed or moved, these files change with it —
`tests/test_user_catalogs.py` fails when a URL here stops matching a file in `catalog/`.
