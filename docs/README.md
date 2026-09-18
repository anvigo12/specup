# SpecUP documentation

| | |
|---|---|
| **[Guide](guide/README.md)** | What SpecUP is, the data model, the lifecycle, the commands |
| ↳ [Using SpecUP](guide/using-specup.md) | The operating manual — every command, every check id, every config key |
| ↳ [New project](guide/new-project.md) | Greenfield adoption, governed from the first commit |
| ↳ [Existing project](guide/existing-project.md) | Brownfield adoption, where intent has to be recovered |
| **[Runbook: publishing](runbooks/publishing-to-spec-kit.md)** | Cutting a release and getting `specify bundle install specup` to work |
| ↳ [Release notes 0.1.2](runbooks/release-notes-0.1.2.md) | **BUSL-1.1**; approval and docstring checks; SpecUP governs itself and its audit fails |
| ↳ [Release notes 0.1.1](runbooks/release-notes-0.1.1.md) | Catalogs register once per machine; scaffolding is one command |
| ↳ [Release notes 0.1.0](runbooks/release-notes-0.1.0.md) | What ships, what is enforced, what is not |
| ↳ [Community submissions](runbooks/community-submission/README.md) | Prepared bodies for Spec Kit's catalog submission issues — discovery, not installation |
| **[Dev: Taskfile](dev/taskfile.md)** | The task runner, and the boundary it must not cross |
| **[Dev: Licensing](dev/licensing.md)** | BUSL-1.1 from 0.1.2 — what the grant covers, and what the change costs |
| **[Research: agent stack](research/specup-agent-stack.md)** | The twelve components in `open-swe/`, the seven-stage retrieval pipeline, where the licence risk sits now that SpecUP composes this stack rather than shipping it, and the stack scored against the fifteen factors. **Research, plus ten decisions taken — none of them yet an ADR.** The eighteen questions are answered from established practice and reopen as each component matures. A later section researches how the agent improves itself — exploration policies, what may never be optimised, and six further questions that established practice does not answer |
| ↳ [Research: agent shape](research/specup-agent-shape.md) | The same stack organised by **how it runs** rather than by component: five planes, eleven processes, two lifecycles, the trust boundaries and the failure matrix. **Synthesis — it decides nothing, and it carries 31 numbered assumptions.** Input to the runtime specification that comes next |

Component-level docs live next to the components:

- [`catalog/user/README.md`](../catalog/user/README.md) — the four files that register
  SpecUP's catalogs once per machine, and why the CLI cannot write them
- [`bundles/specup/README.md`](../bundles/specup/README.md) — why the bundle exists, and the
  two install routes: a release from the catalog, or this working tree
- [`workflows/README.md`](../workflows/README.md) — the enforcement pattern
- [`presets/openup-governance/README.md`](../presets/openup-governance/README.md) — the wrap
  and append contracts
- [`extensions/openup/schemas/ID-GRAMMAR.md`](../extensions/openup/schemas/ID-GRAMMAR.md) —
  normative identifiers, relations, provenance and governance states
