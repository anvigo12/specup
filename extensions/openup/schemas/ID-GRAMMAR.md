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
| Task | `TASK` | `TASK-<NNNN>` | `TASK-0042` |
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
- Every prefix listed in §48 is used above. None is defined and left unused.

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
| `refines` | `refined-by` | Requirement → BusinessObjective; UserStory → Requirement |
| `contains` | `contained-by` | WBSNode → WBSNode; Feature → Requirement |
| `decomposes-to` | `decomposed-from` | WBSNode → Task |
| `implements` | `implemented-by` | WBSNode / Task → Requirement |
| `modifies` | `modified-by` | Task → SourceArtifact |
| `verifies` | `verified-by` | AcceptanceCriterion / TestCase → Requirement |
| `executes` | `executed-by` | Scenario → AcceptanceCriterion |
| `tests` | `tested-by` | UnitTest / IntegrationTest → SourceArtifact |
| `conforms-to` | `conformed-by` | SourceArtifact → Contract |
| `validates` | `validated-by` | MicrocksTest → Contract |
| `mitigates` | `mitigated-by` | WBSNode / Task → Risk |
| `evidences` | `evidenced-by` | Evidence → Task / Gate / Risk |
| `depends-on` | `depended-on-by` | Task → Task; WBSNode → WBSNode |
| `belongs-to` | `owns` | WBSNode → Iteration |
| `approves` | `approved-by` | Actor → any governed artifact |
| `supersedes` | `superseded-by` | ADR → ADR; Requirement → Requirement |

**Dropped as duplicates:** `implemented-by` (§21) — store `implements` and derive it. `satisfies`
(§67) — same edge as `implements`. `validated-by` (§21, as the stored form) — store `validates`.

**Cycles** are an error on `contains`, `decomposes-to`, `refines`, `depends-on`, and `supersedes`.

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
2. Editing the endpoints of an `approved` edge downgrades it to `asserted` and records the
   downgrade — approval does not survive a change to what was approved.
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
