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

```bash
specify preset add --dev ./presets/openup-governance
specify preset list
specify preset resolve spec-template     # see the composition chain
```

That `--dev` route installs this working tree. The intended route is the whole stack at once
through the `specup` bundle — `specify bundle install specup`, after registering SpecUP's
catalog. See [`bundles/specup/README.md`](../../bundles/specup/README.md).

## It expects the openup extension

The preset is useful alone — it adds the discipline to the core prompts — but its guidance
references validators that ship with the `openup` extension
(`.specify/extensions/openup/scripts/python/`). Without the extension those commands are not
present and the instructions become advice with nothing behind them.

Spec Kit has no preset→extension dependency mechanism, so the bundle is what guarantees they
arrive together.

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
