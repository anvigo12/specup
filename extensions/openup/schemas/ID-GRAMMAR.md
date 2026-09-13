# SpecUP ID Grammar and Relation Vocabulary

**Status:** normative. This file is the single source of truth for identifiers and relations.
Schemas in this directory enforce it; validators reject anything outside it.

`specup.md` describes IDs in three mutually inconsistent ways (§17–21 unpadded, §48 zero-padded with
eight unused prefixes, WBS both bare and prefixed). This document resolves those conflicts. §48's
zero-padded form is canonical because padding makes IDs sort lexicographically, which the generated
Markdown views in §47 depend on.

---

## 1. Identifier grammar

Every governed artifact has exactly one ID. IDs are **stable for the life of the artifact** — they are
the edges of the knowledge graph (§48), so renaming one breaks traceability. Supersede, never rename.

**Uniqueness is enforced at load time, not merely asserted here.** All three stores refuse a repeated
id with a `GraphError` — exit 2, "cannot evaluate", rather than a failing check. A store declaring one
id twice does not describe a graph that violates a rule; it describes no graph at all, since the loader
must discard one of the two to build anything and every check downstream would then run over an
arbitrary choice. Nothing allocates IDs: they are authored, and the `<DOMAIN>` tag is what lets teams
and per-feature `specs/*/artifacts.yaml` registries allocate ordinals independently without colliding.

### 1.1 Common tokens

| Token | Pattern | Notes |
|---|---|---|
| `<NNNN>` | `[0-9]{4}` | zero-padded ordinal, unique within its type |
| `<DOMAIN>` | `[A-Z][A-Z0-9]{1,11}` | domain/capability tag, e.g. `AUTH`, `BILLING` |
| `<DOTTED>` | `[1-9][0-9]*(\.[1-9][0-9]*){0,6}` | WBS path, 1–7 segments, no leading zeros |

### 1.2 Types

| Entity (§66) | Prefix | Full pattern | Example |
|---|---|---|---|
| BusinessObjective | `BUS-OBJ` | `BUS-OBJ-<NNNN>` | `BUS-OBJ-0017` |
| Requirement (functional) | `REQ` | `REQ-<DOMAIN>-<NNNN>` | `REQ-AUTH-0014` |
| Requirement (non-functional) | `NON-FR` | `NON-FR-<DOMAIN>-<NNNN>` | `NON-FR-AUTH-0017` |
| Feature / Capability | `FEAT` | `FEAT-<NNNN>` | `FEAT-0014` |
| UserStory | `USR-STR` | `USR-STR-<NNNN>` | `USR-STR-0014` |
| Flow | `FLOW` | `FLOW-<DOMAIN>-<NNNN>-<NNNN>` | `FLOW-AUTH-0014-0003` |
| AcceptanceCriterion | `AC` | `AC-<DOMAIN>-<NNNN>-<NNNN>` | `AC-AUTH-0014-0003` |
| Scenario (Gherkin) | `SCEN` | `SCEN-<DOMAIN>-<NNNN>` | `SCEN-AUTH-0031` |
| WBSNode | `WBS` | `WBS-<DOTTED>` | `WBS-1.2.3.4.1.2` |
| Risk | `RISK` | `RISK-<NNNN>` | `RISK-0007` |
| TraceRelation | `TRACE` | `TRACE-<NNNN>` | `TRACE-0007` |
| ArchitectureDecision | `ADR` | `ADR-<NNNN>` | `ADR-0019` |
| SecurityDecision | `SECURE` | `SECURE-<NNNN>` | `SECURE-0019` |
| TestCase (acceptance) | `TC` | `TC-<DOMAIN>-<NNNN>` | `TC-AUTH-0031` |
| UnitTest | `UNIT` | `UNIT-<DOMAIN>-<NNNN>` | `UNIT-AUTH-0031` |
| IntegrationTest | `INTG` | `INTG-<DOMAIN>-<NNNN>` | `INTG-AUTH-0031` |
| Contract | `CONTRACT` | `CONTRACT-<DOMAIN>-<NNNN>` | `CONTRACT-AUTH-0001` |
| MicrocksTest | `MICROCKS-TEST` | `MICROCKS-TEST-<NNNN>` | `MICROCKS-TEST-0091` |
| Evidence | `EVID` | `EVID-<NNNN>` | `EVID-0233` |
| Iteration | `ITER` | `ITER-[IECT]-[0-9]{2}` | `ITER-E-02` |
| Gate | `GATE` | `GATE-<SCREAMING_SNAKE>` | `GATE-LIFECYCLE_ARCHITECTURE` |
| SourceArtifact | — | repo-relative POSIX path | `src/security/certificate_validator.ts` |

Notes:

- **Iteration** closes the doc's informal variants (`E2` at `specup.md:893`, `C-04` at `:1758`) into one
  form. The phase letter is `I`nception, `E`laboration, `C`onstruction, `T`ransition.
- **Phase** is an enum, not an ID: `INCEPTION | ELABORATION | CONSTRUCTION | TRANSITION`.
- **SourceArtifact** has no synthetic ID — the path *is* the identity, so traceability survives a
  validator rebuild. Paths are repo-relative, POSIX-separated, never absolute.
- **Modelled prefixes** — every one above is a node the graph can reach: an edge may start or
  end at it, and a validator resolves it. `SourceArtifact` included.
- **Deliberately absent: `TASK`.** §48 lists it and §21/§26/§44/§67 route through it, but §15
  already defines WBS **L7** as the Executable Task. A parallel `TASK-*` identity would be a
  second name for one thing, which is precisely the drift this model exists to prevent, so the
  WBS node *is* the task. The `modifies` and `decomposes-to` relations went with it: `modifies`
  had no domain left, and WBS decomposition is already encoded in the id (`WBS-1.2.3` is the
  parent of `WBS-1.2.3.4`), so storing it as an edge would be a second representation of the
  same fact.
- **Reserved but unmodelled: `FLOW`, `TRACE`, `SECURE`.** These have patterns and are accepted
  as ids, but no relation signature admits them, so no edge can reach one today. They are
  reserved so that adding them later renames nothing. Until a signature admits them, do not
  read their presence in the grammar as a claim that the model uses them.

---

## 2. Relation vocabulary

Closed set. A relation not listed here is a validation error.

`specup.md` uses three overlapping vocabularies — §21 (`implemented-by`, `executed-by`,
`verified-by`), §66 (`implements`, `tested-by`, `belongs-to`), §67 (`decomposes-to`, `satisfies`).
The canonical form below is **active voice, stored once**. The inverse is never stored; it is derived
at load time, which is what makes bi-directional traversal (§20, §22) mechanical rather than a second
hand-maintained dataset.

| Relation | Inverse (derived) | Typical domain → range |
|---|---|---|
| `refines` | `refined-by` | Requirement → BusinessObjective; UserStory → Requirement; ADR / SecurityDecision → Requirement |
| `contains` | `contained-by` | WBSNode → WBSNode; Feature → Requirement |
| `implements` | `implemented-by` | WBSNode / SourceArtifact → Requirement / ADR / SecurityDecision |
| `verifies` | `verified-by` | AcceptanceCriterion / TestCase → Requirement |
| `executes` | `executed-by` | Scenario → AcceptanceCriterion |
| `tests` | `tested-by` | UnitTest / IntegrationTest → SourceArtifact |
| `conforms-to` | `conformed-by` | SourceArtifact → Contract |
| `validates` | `validated-by` | MicrocksTest → Contract |
| `mitigates` | `mitigated-by` | WBSNode → Risk |
| `evidences` | `evidenced-by` | Evidence → WBSNode / Gate / Risk |
| `depends-on` | `depended-on-by` | WBSNode → WBSNode |
| `belongs-to` | `owns` | WBSNode → Iteration |
| `approves` | `approved-by` | Actor → any governed artifact |
| `supersedes` | `superseded-by` | any → any (see below) |

**`approves` and `supersedes` accept any type at both ends, on purpose.** `approves` starts at
a human actor, which has no id form at all. `supersedes` is genuinely open: a contract supersedes
a contract, an ADR an ADR, a requirement a requirement — and across types when a decision replaces
the thing it was made about. Constraining it to the two pairs §21 happens to mention would reject
legitimate history for no benefit. Every other relation has a checked domain and range (`TRC-003`).

**Dropped as duplicates:** `implemented-by` (§21) — store `implements` and derive it. `satisfies`
(§67) — same edge as `implements`. `validated-by` (§21, as the stored form) — store `validates`.

**Cycles** are an error on `contains`, `refines`, `depends-on`, and `supersedes`.

---

## 3. Provenance

Every traceability edge carries `provenance`. This exists because the agent that writes the code is
otherwise also the agent that writes the proof it was traced — auditor and audited collapse into one
process, and the evidence claim in §72 becomes circular.

| Value | Meaning | Trust |
|---|---|---|
| `derived` | Recomputed by a validator from the filesystem (test-file naming, Gherkin tags, codegen output). Reproducible; overwritten on every run. | Machine-checkable **once the rule reproduces it** |
| `asserted` | Claimed by an agent or author. Not independently reproducible. | Claim only |
| `approved` | `asserted`, then signed off by a named human with a timestamp. | Governance-grade |

Rules:

1. A validator may create and overwrite `derived` edges freely; it must never silently modify
   `asserted` or `approved` edges. Derived edges live in their own machine-owned store
   (`.specify/traceability/derived.yaml`), which `derive_edges.py --write` rewrites in full.
2. Editing the endpoints of an `approved` edge downgrades it: `TRC-013` recomputes
   `approved_endpoints_hash` from the endpoints as they now stand and, when it disagrees, WARNs
   and moves the edge out of `approved_verified`, which is the count `traceability_final` scores.
   Approval does not survive a change to what was approved. The hash covers the two endpoint
   bodies **and the relation**, so re-pointing an approved edge at a different relation voids the
   signature rather than inheriting it.
   - **`status`, `approvals` and `baseline` are excluded** from the fingerprint. An approval is
     about *what* was approved, not where the artifact sits in §31's state machine: advancing
     `APPROVED → BASELINED` must not void a signature, but editing the requirement must.
   - **A source-path endpoint fingerprints as the path, not the file's bytes.** An approved edge
     to a file records which file was approved for this role; source churn is continuous, and
     hashing content would void every approval on every commit until nobody used approvals at
     all. Whether the file is still *correct* is what tests and `TRC-010` derivation are for.
     This is stated here because the two behaviours are indistinguishable from outside.
   - Nobody can compute this hash by hand, so `approve_edge.py` is the supported way to write
     one. A required field with no tool to produce it is the same defect in a new place.
3. Gates may require a minimum provenance level. Baseline gates (§30, §59) require `approved` for
   requirement-level edges.
4. `audit.py` reports the derived : asserted : approved ratio. A graph that is overwhelmingly
   `asserted` proves little, and the report must make that visible rather than showing 100% coverage.
5. **`derived` is a claim until the rule is re-run.** `derived_by` must name a rule in
   `derivers.py`, and `TRC-010` re-executes that rule and fails the edge if it does not come back.
   Without this the provenance model reproduces the circularity it exists to break, one level up:
   the schema only ever required `derived_by` to be *present*, so relabelling an assertion
   `derived` was free and moved the very ratio rule 4 reports. Edges naming a rule that is
   declared but not implemented are counted separately as `derived_unverified` and are **not**
   evidence — `traceability_final` scores reproduced derivations and human approvals only.

---

## 4. Governance states

Per §31, applied to every governed artifact:

```
DRAFT → REVIEW → APPROVED → BASELINED → IMPLEMENTED → VERIFIED → ACCEPTED
```

Forward transitions only, one step at a time, except that any state may drop back to `DRAFT` on
amendment. `BASELINED` and beyond require an `approved_by` entry. **Generated does not mean
approved** (§31): artifacts created by a command always enter at `DRAFT`.
