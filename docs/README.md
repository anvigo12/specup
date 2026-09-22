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
| **[Implement: shape assumptions](implement/test-specup-agent-shape-assumptions.md)** | The campaign that answers those 31 assumptions. Nine are probes, six are design intentions with nothing to test, and sixteen need a ruling rather than an experiment. Eight probes, each with a falsifier written before it runs. **Five are run and all five are answered — four of them only under a condition they did not state. P1 — Open SWE's five graphs run under Aegra untouched — at the cost of three corrections it was not looking for, plus one defect sent upstream as [open-swe#2969](https://github.com/langchain-ai/open-swe/pull/2969). P2 was falsified, then re-run and answered: the OpenShell policy blocks writes to the governance tree, symlinks included, and on the rolling `dev` build it blocks `truncate(2)` too — but on every stable release `truncate(2)` still empties the signature trust root, so SpecUP now carries a minimum OpenShell version as a security constraint. P4 answered: a key that never left the host signed a commit made inside a sandbox that could not read a copy of that key in its own filesystem — but `vouch-bridge`, the component the assumption names, signs C2PA images and audio rather than git objects, and there is no local socket to reach it on, so this sidecar is work SpecUP has to do. P5 answered: one process did serve both the embedder and the reranker — but only on Infinity and not TEI, and not with the reranker this project had decided on, which the serving runtime cannot load at all. P3 answered in a real browser: Agent Inbox authenticated against an Aegra that refuses anonymous callers, listed the interrupts and resumed the thread on all four response verbs — but the LangSmith key the stack report worried about is a placeholder rather than a constraint, the credential travels in a header Aegra's own auth example does not read, and **Open SWE calls `interrupt()` nowhere**, so the queue the inbox exists to provide would be empty. The other three result blocks are empty, and empty means not run** |
| ↳ [Probe scripts](implement/probes/README.md) | The tracked half of the campaign: the harness that refuses the three ways a result gets faked, the scripts for the probes that have actually run, and one regression guard that is evidence rather than a probe |

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
