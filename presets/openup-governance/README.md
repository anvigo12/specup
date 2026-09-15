# OpenUP Governance Preset

Composes OpenUP governance into **Spec Kit's own artifacts** — the constitution, spec, plan
and tasks templates, and the `/speckit.tasks` and `/speckit.implement` commands.

This is the one layer that can reach Spec Kit's core. An extension can only add new,
namespaced commands (`speckit.openup.*`); changing what `/speckit.implement` itself does
requires a preset.

## What it provides

| Target | Strategy | Adds |
|---|---|---|
| `constitution-template` | `append` | Filesystem-first principles, resolve-or-stop, approval boundaries, the gate contract |
| `spec-template` | `append` | Governed requirement identity, ownership, acceptance criteria |
| `plan-template` | `append` | Lifecycle position, ADRs, risk and contract linkage, decomposition expectations |
| `tasks-template` | `append` | Definition of Ready, Definition of Done, the task execution contract |
| `speckit.tasks` | `wrap` | Derive tasks from the WBS rather than inventing them; bind each to its governance |
| `speckit.implement` | `wrap` | Resolve the governance chain or stop; produce evidence and update the graph |

## Install

The intended route is the whole stack at once, through the `specup` bundle, because this
preset is only half of it — see [It expects the openup extension](#it-expects-the-openup-extension):

```bash
specify bundle install specup
```

That needs SpecUP's catalogs registered first — four files copied into `~/.specify/`, once per
machine. [`catalog/user/README.md`](../../catalog/user/README.md) has them, and explains why
`specify preset catalog add` is not the same thing.

To install only this preset, from the release or from this working tree:

```bash
specify preset add --from https://github.com/anvigo12/specup/releases/download/v0.1.1/openup-governance-0.1.1.zip
specify preset add --dev ./presets/openup-governance
```

Either way, confirm it composed rather than assuming it did:

```bash
specify preset list
specify preset resolve spec-template     # see the composition chain
```

## It expects the openup extension

The preset is useful alone — it adds the discipline to the core prompts — but its guidance
references validators that ship with the `openup` extension
(`.specify/extensions/openup/scripts/python/`). Without the extension those commands are not
present and the instructions become advice with nothing behind them.

`preset.yml` declares that dependency, so Spec Kit says so rather than leaving you to find out
from behaviour. Installing this preset into a project without the extension prints:

```
!  This preset depends on extensions that are not satisfied:
    openup is not installed
      Install with: specify extension add openup

The preset is installed.
Anything relying on an unavailable extension does nothing until that is resolved.
```

That is a warning, not a refusal — and the distinction is the point. The overrides still fall
through to the core workflow, so nothing breaks; the preset simply does less than its
instructions promise, which is the failure a silent install would hide.

Declaring the dependency does not install it. Nothing in Spec Kit's preset machinery does.
The bundle is still what guarantees the two arrive together.

## What it deliberately does not ship

No WBS, risk register, or traceability templates. Those belong to the extension. Shipping
them here too would create two sources of truth for the same artifact — exactly the drift the
governance model exists to prevent. `test_preset_does_not_duplicate_extension_templates`
enforces this.

## Two mechanics worth knowing before editing

**A wrap's frontmatter replaces the core command's.** The core `/tasks` and `/implement`
declare `scripts:` blocks that `{SCRIPT}` substitution depends on. A wrapper that omits them
still composes and still looks correct — the script invocation is simply gone. Both wrappers
here reproduce the core blocks verbatim, and
`test_wrap_commands_preserve_the_core_scripts_block` fails if that drifts.

**An addendum must not carry frontmatter.** Appended content is concatenated onto the
composed document, so a `---` block inside it lands mid-document as literal text.

## Verified behavior

Installed into a real `specify init` project (spec-kit 1.0.6, Claude integration):

- `specify preset resolve spec-template` reports `[base] core → [append] openup-governance`,
  and all four core templates gain their addendum layer.
- The composed `speckit-tasks` skill contains zero literal `{CORE_TEMPLATE}` placeholders,
  with pre-logic, core body, and post-logic in that order.
- `{SCRIPT}` resolves to `scripts/bash/setup-tasks.sh --json` — identical to an unwrapped
  core command, confirming the preserved frontmatter works.
- `specify preset remove openup-governance` restores the core command and drops the addendum
  layer, leaving nothing behind.
