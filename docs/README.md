# SpecUP documentation

| | |
|---|---|
| **[Guide](guide/README.md)** | What SpecUP is, the data model, the lifecycle, the commands |
| ↳ [Using SpecUP](guide/using-specup.md) | The operating manual — every command, every check id, every config key |
| ↳ [New project](guide/new-project.md) | Greenfield adoption, governed from the first commit |
| ↳ [Existing project](guide/existing-project.md) | Brownfield adoption, where intent has to be recovered |
| **[Runbook: publishing](runbooks/publishing-to-spec-kit.md)** | Cutting a release and getting `specify bundle install specup` to work |
| **[Dev: Taskfile](dev/taskfile.md)** | The task runner, and the boundary it must not cross |

Component-level docs live next to the components:

- [`bundles/specup/README.md`](../bundles/specup/README.md) — why the bundle exists and why
  `specify bundle install` cannot install it yet
- [`workflows/README.md`](../workflows/README.md) — the enforcement pattern
- [`presets/openup-governance/README.md`](../presets/openup-governance/README.md) — the wrap
  and append contracts
- [`extensions/openup/schemas/ID-GRAMMAR.md`](../extensions/openup/schemas/ID-GRAMMAR.md) —
  normative identifiers, relations, provenance and governance states
