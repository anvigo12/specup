# A detailed usage guide for SpecUP

## Context

SpecUP is complete and verified: three Spec Kit layers plus a bundle, 13 command-line entry
points, 231 tests passing, all ten audit gaps closed at
[701c682](https://github.com/anvigo12/specup/commit/701c682).

What it does not have is an operating manual. `docs/` currently holds:

| Document | What it is |
|---|---|
| [docs/guide/README.md](docs/guide/README.md) | Concepts and architecture — *what* SpecUP is and *why* it is shaped that way |
| [docs/guide/new-project.md](docs/guide/new-project.md) | Greenfield adoption journey |
| [docs/guide/existing-project.md](docs/guide/existing-project.md) | Brownfield adoption journey |
| [README.md](README.md) | Project pitch, verification record, limitations |

Nothing answers the question a person has on day 40: *a check just failed — what is `TRC-010`,
why does it exist, and what do I type?* The check ids (`WBS-000`–`011`, `RISK-000`–`007`,
`TRC-000`–`013`, `DOD-001`–`006`, `DOR-001`–`009`, `CTX-001`–`004`, `SEL-000`–`002`,
`DRV-001`–`004`, `VIEW-001`–`002`) appear in validator output and in nine agent commands, and
are defined nowhere a user can read. Same for the config keys, the artifact/WBS/risk/edge field
sets, and the three-way exit contract.

**The deliverable:** `docs/guide/using-specup.md` — a standalone operational manual, readable
without the other three, built around one worked example carried end to end.

### Assessment of the current state (what the guide has to describe)

- **Three layers, one enforcer.** Preset and extension are prompt-level; only a workflow
  `shell` step's exit code stops anything. Bundle is distribution.
- **13 CLIs** under `extensions/openup/scripts/python/`, 8 of which emit the
  `Verdict` shape; every one takes `--root`, `--json`, `--out`; exit `0`/`1`/`2`.
  Verified: they run with no `PYTHONPATH` set, since Python puts the script's own directory on
  `sys.path`.
- **14 relations**, stored once in active voice, inverses derived at load time.
- **23 gate condition declarations over 22 implementations** across 4 gates.
- **3 of 5 derivation rules implemented**; the other two are reported, never trusted.
- **Two honest limits** the guide must state plainly: nothing parses a contract document, and
  an approval binds content, not a human.

---

## The document

`docs/guide/using-specup.md`. Audience line at the top: **engineers and leads operating a
SpecUP-governed repository day to day.**

### The worked example

One thread, from `tests/fixtures/good`, carried through every section: **`REQ-AUTH-0014`,
"Vehicle must authenticate using a valid certificate."** The reader watches it become a
requirement, decompose into `WBS-1.2.3.4.1.1.1–3`, acquire `RISK-0007`, gain edges, bind to
`SCEN-AUTH-0031`, get approved, pass the Definition of Done, and clear
`GATE-LIFECYCLE_ARCHITECTURE`.

Every command output in the guide is **real output already captured** by running the validators
against that fixture during this planning pass — the audit report, the 23-artifact impact
fan-out, the traceability metrics block, `derive_edges` with its `DRV-004` skip, `select_work`
warning that nothing is ready. Nothing is invented or prettified.

### Structure

1. **Before you start** — the three-way exit contract (`0` pass, `1` governance failure, `2`
   could-not-evaluate), why collapsing `2` into `1` would lie to the operator, the universal
   `--root/--json/--out` flags, and where the scripts live (same literal path for agent and
   workflow — extension commands get no `{SCRIPT}` substitution).
2. **Install and scaffold** — `install.py --project`, `requirements.txt` (skipping it makes
   every validator exit `2`), `init_openup.py --program`, then `render_views.py --write`
   because the three generated governance documents are deliberately not seeded.
3. **The daily loop** — the five commands a person actually runs, in order, with the reason
   each one exists: `select_work` → work → `derive_edges --write` → `validate_*` →
   `render_views --write` → `audit`.
4. **The data model, by store** — one subsection per store with the full field set from its
   schema, the fixture excerpt, and what each field is *for*:
   - `requirements.yaml` (artifact registry) — the `artifactType` enum, `status` state machine,
     why `BASELINED`+ requires `approvals` and `owner`.
   - `wbs.yaml` — the seven levels; **segment count is the level**; `kind` driving conditional
     invariants; `terminal_reason` under `semantic` vs `strict`; the L7 contract
     (owner + iteration + ≥1 requirement).
   - `risk-register.yaml` — exposure = p × i, the two thresholds, residual reduction, why
     `mitigation` must name WBS nodes and not prose, `acceptance_approval`.
   - `traceability.yaml` / `derived.yaml` — the 14 relations with domain → range, provenance,
     why the inverse is never stored, why `derived.yaml` is machine-owned.
   - Source paths as identity, and the `GOVERNANCE_FILES` hard exclusion.
5. **Provenance, and why the model needs it** — the circularity argument; the `derived` /
   `asserted` / `approved` table; `TRC-010` re-running the rule; `TRC-013` re-hashing the
   endpoints; the `LIFECYCLE_KEYS` exclusion (advancing `APPROVED → BASELINED` must not void a
   signature, editing the requirement must); source paths fingerprinting as the path, not the
   bytes. Worked `approve_edge.py` invocation plus its three refusals (derived store, derived
   edge, unresolvable endpoint) and the HONEST LIMIT.
6. **Check reference** — the core of the document. A table per validator: id, severity,
   what it checks, why it exists, what to do when it fires. All ~55 ids, sourced from the
   code, not restated from memory. Severity split called out where it is deliberate:
   `CTX-001`/`003` warn, `CTX-002`/`004` fail — *a missing map is a gap, a misleading map is a
   defect*; `TRC-013` warns and demotes rather than failing, so people do not abandon
   `approved` entirely.
7. **Gates** — the four gates, all 23 declarations, each condition's one-line meaning taken
   from `DESCRIPTIONS`; the two invariants (absence of evidence is not evidence; conditions
   fail closed); `traceability_final`'s 50% independently-verifiable bar and why it counts
   `derived_verified + approved_verified` rather than the labels.
8. **Running a phase workflow** — the shared ending block, why `continue_on_error: true`
   strengthens rather than weakens it, the override record, and the Construction fan-out.
9. **The nine agent commands** — what each is for, what it must not do (the `speckit.openup.gate`
   prohibitions verbatim in substance), and which validator sits behind it.
10. **Changing a baselined artifact** — `impact.py` first (real 23-artifact fan-out), the
    change-control steps, expecting approvals to withdraw themselves, re-baseline, re-gate.
11. **Configuration reference** — every key in `openup-config.yml`, its default, which check
    reads it, and when to change it. Explicit warning that list-valued keys **replace rather
    than merge** (this is why `GOVERNANCE_FILES` is hard-coded).
12. **Troubleshooting** — symptom → cause → fix, covering every failure I can name from the
    code: exit 2 everywhere, `WBS-001` level disagreement, orphan floods, `TRC-010`/`011`/`012`,
    stale views, `SEL-000` no open iteration, `DOR-009`/`CTX-004` missing skill, unimplemented
    condition names.
13. **What SpecUP does not do** — contracts unparsed, Microcks deferred, two rules
    unimplemented, no CI, no commit-trailer validation, approval ≠ human, overhead unmeasured.
14. **Where to go next** — links to the three existing guide pages, `ID-GRAMMAR.md`, and
    `specup.md`.

### Rules for writing it

- Every command shown uses the installed path `.specify/extensions/openup/scripts/python/…`,
  the form a reader will actually type.
- Every claim traces to code. No check id, threshold, count or field name goes in that I have
  not read in this session.
- State counts exactly: 14 relations, 22 condition implementations over 23 declarations, 3 of 5
  derivation rules, 8 verdict-emitting validators of 13 CLIs.
- Reason before mechanism, throughout — the user asked for *why*, and most of this design is
  only defensible once the failure it prevents is named.

### One-line index updates

- [docs/README.md](docs/README.md) — add the row under **Guide**.
- [docs/guide/README.md](docs/guide/README.md) — add to the numbered contents and the adoption
  cross-links.

### One pre-existing error found while assessing

[docs/guide/README.md](docs/guide/README.md) says the relation set is "a closed set of
**sixteen**" and then lists fourteen; the schema enum has fourteen. One-word fix, offered
separately so it does not hide inside the new file's diff.

---

## Verification

1. **Every example is real.** Re-run each captured command against `tests/fixtures/good` and
   diff the output against what the guide prints:
   ```bash
   python3 extensions/openup/scripts/python/audit.py --root tests/fixtures/good
   python3 extensions/openup/scripts/python/impact.py --root tests/fixtures/good --of REQ-AUTH-0014
   python3 extensions/openup/scripts/python/validate_trace.py --root tests/fixtures/good --json
   python3 extensions/openup/scripts/python/derive_edges.py --root tests/fixtures/good
   python3 extensions/openup/scripts/python/select_work.py --root tests/fixtures/good
   ```
2. **Every check id exists.** Grep each id quoted in the guide out of
   `extensions/openup/scripts/python/` and confirm the set in the guide equals the set in the
   code, in both directions — a documented check that does not exist is the exact defect the
   guide warns about.
3. **Every config key exists.** Cross-check the configuration table against
   `extensions/openup/openup-config.yml` and `DEFAULT_CONFIG` in `openup_model.py`.
4. **Every relative link resolves.** Check each `](…)` target exists on disk.
5. **The suite still passes**, since `tests/test_taskfile_boundary.py` and the manifest tests
   read repository files:
   ```bash
   python3 -m pytest tests/ -q
   ```

No source file changes, so no behaviour to re-verify beyond that.
