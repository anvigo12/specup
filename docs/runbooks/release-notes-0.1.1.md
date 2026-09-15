# SpecUP 0.1.1

A correctness and ergonomics release. No change to what is enforced, what a gate decides, or
what any validator checks — the governance model is byte-for-byte the one 0.1.0 shipped. What
changed is the two things a person meets first: how you register the catalogs, and how many
commands the scaffold takes.

## Registering the catalogs is now genuinely once per machine

0.1.0 told you to run four `specify <primitive> catalog add` commands and called them
"one-time, per machine". That was wrong in both halves.

`catalog add` calls `_require_specify_project()` and writes
`<project>/.specify/<primitive>-catalogs.yml`. No subcommand takes a `--user` flag, so those
four commands are **per project**, repeated for every project forever.

They are also lossy. For extensions, presets and workflows a config file *replaces* the stack
below it rather than merging with it — `get_active_catalogs` returns the first scope that
loads and never consults the next. So a project config naming only `specup` becomes the entire
stack, and Spec Kit's own `default` and `community` catalogs disappear from that project.
Measured on a clean project: `specify extension search` drops from **173 extensions to 1**.
The four core extensions still install, because they are vendored in the spec-kit wheel rather
than fetched, which is exactly what makes the loss hard to notice — nothing fails, things stop
being findable.

Spec Kit reads `~/.specify/<primitive>-catalogs.yml` for all four primitives. So 0.1.1 ships
those four files:

```bash
mkdir -p ~/.specify
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user
for f in extension preset workflow bundle; do
  curl -sSL -o ~/.specify/$f-catalogs.yml $BASE/$f-catalogs.yml
done
```

Copy them once and `specify bundle install specup` resolves in any project on the machine,
with Spec Kit's own catalogs intact — the three replacing files restate `default` and
`community` at their built-in priorities. `bundle-catalogs.yml` deliberately does not, because
bundle sources merge by id and naming the built-ins there would freeze URLs that currently
track spec-kit.

The per-project route still works and is still documented, with its cost stated and the
`--id specup` flag it was missing.

## Scaffolding is one command

`init_openup.py` now generates `definition-of-ready.md`, `definition-of-done.md` and
`quality-gates.md` itself instead of printing an instruction to run `render_views.py --write`
next.

Those three documents are generated rather than seeded because they are derived from the code
that enforces them, and a governance document that disagrees with its check is worse than no
document — people follow the document while the machine applies the code. That reason is about
what *produces* them, not about when, so nothing about the guarantee changes. What changes is
that a project can no longer sit in the state where the checks exist and the documents
describing them do not, which previously took nothing more than not having read one more
paragraph.

Two flags come with it:

| Flag | Effect |
|---|---|
| `--no-render` | Scaffold only. Generation needs `jsonschema` and `referencing`; the scaffold needs neither, so this still works with only PyYAML installed. |
| `--json` | Unchanged verdict shape, with a new `INIT-003` check carrying the generation result. |

If generation cannot run, `init_openup.py` **exits 2 and says so** rather than exiting 0 with
three documents quietly missing. The scaffold is still written, so the fix is to install the
dependencies and re-run. Exit 2 is the same could-not-evaluate code every validator uses, so a
workflow halts on its setup-fault branch rather than proceeding over a tree that looks
finished.

Authored files are still never overwritten. Generated documents *are* rewritten on a re-run —
they are owned by the code, and a stale one is a defect rather than content to preserve.
`VIEW-001` fails on exactly that.

## Install

```bash
mkdir -p ~/.specify
BASE=https://raw.githubusercontent.com/anvigo12/specup/main/catalog/user
for f in extension preset workflow bundle; do
  curl -sSL -o ~/.specify/$f-catalogs.yml $BASE/$f-catalogs.yml
done

specify bundle install specup
python3 -m pip install -r .specify/extensions/openup/requirements.txt
python3 .specify/extensions/openup/scripts/python/init_openup.py --program "Your Program"
python3 .specify/extensions/openup/scripts/python/audit.py
```

The audit exits 1 on a fresh scaffold. That is correct — an empty plan is not a valid plan.

## Upgrading from 0.1.0

```bash
specify bundle remove specup && specify bundle install specup
```

Nothing in `.specify/` changes shape, and no governed artifact is touched. Re-run
`init_openup.py` afterwards if you want the three generated documents refreshed; it preserves
everything you authored.

## What ships

| Component | Version | Changed |
|---|---|---|
| `openup` extension | 0.1.1 | `init_openup.py` renders; `speckit.openup.init` documents the new exit codes |
| `openup-governance` preset | 0.1.1 | README install instructions only |
| `specup` bundle | 0.1.1 | pins the two above; README install instructions |
| `openup-inception` | 0.1.0 | unchanged — rebuilds to an identical digest |
| `openup-elaboration` | 0.1.0 | unchanged — rebuilds to an identical digest |
| `openup-construction` | 0.1.0 | unchanged — rebuilds to an identical digest |
| `openup-transition` | 0.1.0 | unchanged — rebuilds to an identical digest |

The four workflows keep their 0.1.0 versions and digests. Archives are reproducible — fixed
member timestamps, sorted entries, normalized permissions — so an unchanged component rebuilds
byte-identically, and the release assets for those four are the same bytes 0.1.0 published.
Their `download_url` points at the `v0.1.1` tag because that is where the assets are attached.

## Also corrected

- **"Without PyYAML, jsonschema and referencing every validator exits 2"** was true only of
  PyYAML. Blocking just the schema libraries takes five of the nine validators to exit 2 —
  `validate_wbs`, `validate_risk`, `validate_trace`, `render_views`, `audit` — while
  `validate_done`, `validate_context`, `select_work` and `derive_edges` run fine. The
  documented probe (`audit.py`) was in the affected set, so the check was right; the sentence
  was not.
- The guide repeated Spec Kit's own `requires.tools` warning, which `bundle install` already
  prints unprompted. Trimmed to the part that adds something: run `audit.py`, read the exit
  code.

## Unchanged, and worth restating

Extensions and presets are prompt-level: they change what an agent is told, and an agent can
decline. Only a workflow `shell` step's exit code halts a run, which is why the four phase
workflows carry the gates. Nothing here parses a contract document, and an approval binds
content rather than a human — the signature proves the bytes have not changed since approval,
not who approved them.
