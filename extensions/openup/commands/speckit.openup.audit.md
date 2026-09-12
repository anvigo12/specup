---
description: "Filesystem-first compliance audit with coverage, orphans, and evidence quality"
---

# Compliance Audit

Aggregate every validator and the current phase gate into one report, so governance state is
observable rather than inferred (specup.md s33).

## User Input

```text
$ARGUMENTS
```

Empty audits the whole project. A scope (e.g. `specs/001-auth`) narrows the report.

## Execution

```bash
python .specify/extensions/openup/scripts/python/audit.py --json
```

Exit codes: `0` pass, `1` fail, `2` the graph could not be loaded.

## What it covers

```
lifecycle -> WBS -> requirements -> risks -> traceability -> evidence -> gate
```

## Reading the report

Report every section. Three parts deserve explicit comment rather than a number:

**Coverage vs. evidence quality.** Forward coverage can read 100% while most edges are
`asserted` — claims by an agent, not independently reproducible. Always report the
derived/asserted/approved split next to the coverage figures, and say plainly when coverage
is high but largely unverified. A project can be fully "traced" and still have no evidence
anyone could check. This is the number most likely to be quietly dropped from a summary;
do not drop it.

**Orphans.** `TRC-008` lists requirements nothing implements, WBS leaves doing nothing for
any requirement, unmitigated high risks, and scenarios bound to no criterion. Each is work or
intent that has drifted out of the graph.

**Backward coverage.** Files inside the perimeter that no requirement reaches. Either the
file is unnecessary, or a requirement is undocumented, or the perimeter is wrong. Say which
you think it is; do not invent edges to close the gap.

## Acting on failures

For each failure, name the file to change and the change to make. Prefer, in order:

1. Fix the graph — add the missing edge, criterion, or mitigation node.
2. Fix the perimeter or thresholds in `openup-config.yml`, **if** they are genuinely wrong,
   as a separate visible change with a stated reason.
3. Report the failure as real and leave it.

Never fabricate evidence files, approvals, or edges to make the audit pass. An audit that is
made to pass has no value; a failing audit with a clear cause is doing its job.

## Continuous use

This is the same script a workflow `shell` step and a CI job run. Run it on requirement
changes, WBS changes, contract changes, and iteration boundaries (s61) — not only at release,
when the accumulated drift is expensive.
