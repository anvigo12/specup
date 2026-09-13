# Taskfile — developing SpecUP

**Audience:** anyone working *on* SpecUP.

[Taskfile.yml](../../Taskfile.yml) wraps the repo's development, packaging and release
commands. It is a convenience layer for contributors and nothing else — see
[The boundary](#the-boundary) below, which is the part worth reading even if you never run
`task`.

## Install

```bash
# macOS / Linux
brew install go-task

# or, without a package manager
sh -c "$(curl -sSL https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin
```

`task` is a single Go binary with no runtime dependencies. It is **not** required to use
SpecUP, run the tests, or install the bundle — every task here is a thin wrapper over a
command you can run directly, and each doc shows the underlying command too.

```bash
task            # list everything
```

## Tasks

### Tests

| Task | What it runs |
|---|---|
| `task test` | `python3 -m pytest tests/ -q` — 189 passed, 8 skipped |
| `task test:engine` | the same suite under `.venv`, with spec-kit importable — 197 passed |
| `task test:both` | both, in order |

The two suites are not redundant, and `test:both` is the one to run before pushing. Eight
tests exercise Spec Kit's real engine and validators; without spec-kit installed they
**skip rather than fake**, because a green test that never ran the engine is worse than an
honest skip. Running only `task test` therefore proves less than it appears to, and running
only `task test:engine` never checks that the skip guards work. The pair is the check.

`task venv` builds the engine environment (spec-kit 1.0.6, pytest, and the validator
dependencies). Every task that needs it depends on it, so you rarely call it directly. It is
idempotent — a `status:` guard skips the rebuild when `.venv/bin/python` already exists. To
force a rebuild:

```bash
task venv --force
```

### The bundle

| Task | What it runs |
|---|---|
| `task bundle:validate` | `specify bundle validate --path bundles/specup --offline` |
| `task bundle:build` | `specify bundle build` → `dist/specup-0.1.0.zip` |

`bundle:validate` uses Spec Kit's own validator rather than ours, so it catches manifest rules
we have not transcribed into `tests/test_bundle.py`. Offline, the reference checks downgrade
to warnings — those six `! Could not verify …` lines are expected and not failures.

### Installing into a project

```bash
task install:dry PROJECT=/path/to/spec-kit-project   # commands + pin check, no changes
task install     PROJECT=/path/to/spec-kit-project   # the real thing
```

`PROJECT` is required; the task fails immediately without it rather than defaulting to the
current directory, which would otherwise install SpecUP into SpecUP.

Both run [`bundles/specup/install.py`](../../bundles/specup/install.py), which checks every
version pin in `bundle.yml` against the component's own manifest before touching anything.
A drifted pin aborts the install:

```
error: Version pins disagree with the components in this repo:
  extension 'openup': manifest pins 0.2.0, on disk 0.1.0
```

### Release

| Task | What it runs |
|---|---|
| `task release:archives` | seven reproducible zips + `dist/SHA256SUMS` |
| `task release:catalog` | the four `catalog/*.json` documents, from those digests |
| `task release:check` | both suites, validate, build, archives, catalog — the pre-tag gate |

`release:archives` calls [`tools/build_archives.py`](../../tools/build_archives.py), which
reads the component list from `bundle.yml` rather than restating it, so a component added to
the bundle cannot be forgotten at release time. Six archives are the components; the seventh
is the bundle artifact `specify bundle build` produces, which is why `release:archives`
depends on `bundle:build`.

`release:catalog` calls [`tools/build_catalog.py`](../../tools/build_catalog.py), which
re-verifies every digest against the bytes on disk and refuses when `bundle.yml`'s pin
disagrees with a component's own manifest. The generated catalog is a pure function of the
release: running it twice reports "0 written, 4 already current".

The archives are byte-reproducible — fixed member timestamps, sorted entries, normalized
permissions, mirroring Spec Kit's own packager. Rebuilding an unchanged component yields an
identical digest. That matters because the catalog pins `sha256` and Spec Kit verifies the
downloaded bytes against it; without reproducibility you cannot distinguish a rebuild from a
tampered artifact. Confirm it any time:

```bash
cp dist/SHA256SUMS /tmp/s1 && task release:archives && diff /tmp/s1 dist/SHA256SUMS
```

The task declares `sources:` and `generates:`, so re-running it with nothing changed is a
no-op.

From here, follow [the publishing runbook](../runbooks/publishing-to-spec-kit.md).

### Housekeeping

| Task | Effect |
|---|---|
| `task clean` | removes `dist/`, `.pytest_cache`, `__pycache__` |
| `task clean:all` | the above plus `.venv` |

`dist/` and `.venv/` are gitignored.

---

## The boundary

**Everything in `Taskfile.yml` is for developing, testing, packaging or publishing SpecUP.
Nothing SpecUP *runs* goes through it.**

No workflow `run:` field may call `task`. No gate may be evaluated through it. No extension
command or preset instruction may tell an agent to run it. `task` must never appear in any
manifest's `requires.tools`.

[`tests/test_taskfile_boundary.py`](../../tests/test_taskfile_boundary.py) enforces all four.

### Why — this is a governance rule, not a style preference

Validators live under `.specify/extensions/openup/`, a directory `specify extension add` owns
and reinstalls. Tampering with one is visible and gets reverted on the next update.

A `Taskfile.yml` lives at a project root. Editing it is an unremarkable act that leaves no
trace anywhere Spec Kit looks.

So if a gate were evaluated through `task gate`, redefining that task as `exit 0` would become
a clean, reviewable-looking way to turn a failing gate green. That is precisely what
[`speckit.openup.gate.md`](../../extensions/openup/commands/speckit.openup.gate.md) forbids —
and unlike editing a validator, the bypass would be indistinguishable from ordinary project
maintenance.

Two supporting reasons:

- **It would break a property the README states plainly:** the path an agent runs and the path
  a workflow runs are the same string. An indirection layer reintroduces a second thing to
  keep in sync.
- **It would add a shipped dependency.** A SpecUP consumer needs `python3` and three pip
  packages. Adding a Go binary to that set makes a missing `task` a failure at *gate* time,
  because Spec Kit surfaces `requires.tools` as an install-time warning, not a check. The
  wrapper also risks collapsing the three-way exit contract: `2` (could-not-evaluate) must
  never be confused with `1` (governance failure), and `task` has its own failure modes —
  binary absent, Taskfile unparseable — that are neither.

### What that rules in and out

| Use | Verdict |
|---|---|
| Running the test suites | Yes |
| Building and validating the bundle | Yes |
| Building release archives and digests | Yes — the strongest fit in the repo |
| Installing SpecUP into a project | Yes — it is a dev installer either way |
| A workflow `shell` step calling `task` | **No** — enforcement must not be project-editable |
| An extension command telling an agent `task audit` | **No** — same reason |
| Replacing the Spec Kit workflow engine | **No** — two orchestrators, two sources of truth about what runs when |
| CI calling `task` as the *authority* on a check | **No** — CI should call the validators directly, so the check cannot be edited away inside the repo under test |
| CI calling `task` as a convenience alias | Fine, provided the validators remain the authority |

### One thing not verified

The README lists `python3` in shell steps as a portability limitation (Windows hosts normally
have `python`). Taskfile's embedded `mvdan/sh` interpreter is the documented fix for that class
of problem, but it has not been tested here and it trades a portability problem for a
distribution one — every Windows user would then need `task` as well. A `python3` shim, or
resolving the interpreter in the workflow, is the cheaper fix and stays inside the boundary
above.
