# Community catalog submissions

Prepared bodies for Spec Kit's community catalog submission issues, one per primitive. They
belong to [the publishing runbook's step 7](../publishing-to-spec-kit.md#7-optional--submit-for-discovery).

| File | Issue template | Lands in |
|---|---|---|
| [`extension-openup.md`](extension-openup.md) | `[Extension]` | `extensions/catalog.community.json` |
| [`preset-openup-governance.md`](preset-openup-governance.md) | `[Preset]` | `presets/catalog.community.json` |
| [`bundle-specup.md`](bundle-specup.md) | `[Bundle]` | `bundles/catalog.community.json` |

There is no fourth file. `workflows/catalog.community.json` exists and is populated, but Spec
Kit ships no workflow submission template and no `add-community-workflow` automation, so the
four `openup-*` workflows have no route. The bundle submission lists them under *Components
Provided*; do not hand-edit the workflow catalog to close the gap.

## How the flow works

**Do not open a pull request.** Spec Kit's `CONTRIBUTING.md` is explicit that a hand-edited
catalog PR bypasses validation and is closed with a pointer back to the issue flow.

1. File the issue. Each file here **is** the issue body, written in the format GitHub renders an
   issue form into — `### <field label>` followed by the value, and literal `- [x]` checkboxes.
   So either paste field by field into the web form, or file it directly:

   ```bash
   gh issue create --repo github/spec-kit \
     --title "[Extension]: Add openup — OpenUP Governed Lifecycle" \
     --body-file docs/runbooks/community-submission/extension-openup.md
   ```

2. A maintainer applies the `extension-submission` / `preset-submission` / `bundle-submission`
   label during triage. Do not apply it yourself and do not ask for it.
3. That label starts an agentic workflow which validates the release, verifies the
   `download_url` and digest, checks that every required box is ticked, and opens the catalog PR.

The heading structure is load-bearing: the workflow parses the body by field label, and checks
the required boxes are literally `[x]`. A free-form body will not validate.

Titles:

| File | Title |
|---|---|
| `extension-openup.md` | `[Extension]: Add openup — OpenUP Governed Lifecycle` |
| `preset-openup-governance.md` | `[Preset]: Add openup-governance — OpenUP Governance` |
| `bundle-specup.md` | `[Bundle]: Add specup — SpecUP OpenUP Governed Lifecycle` |

A version bump or a repair is an update and needs the same flow — there is no lighter path for
changing an entry that already exists.

## What was filed

All three were filed against `github/spec-kit` on 2026-09-13, from the 0.1.0 release:

| Issue | Submission | Body |
|---|---|---|
| [#4566](https://github.com/github/spec-kit/issues/4566) | `[Bundle]` specup | [`bundle-specup.md`](bundle-specup.md) |
| [#4567](https://github.com/github/spec-kit/issues/4567) | `[Extension]` openup | [`extension-openup.md`](extension-openup.md) |
| [#4568](https://github.com/github/spec-kit/issues/4568) | `[Preset]` openup-governance | [`preset-openup-governance.md`](preset-openup-governance.md) |

Each posted body round-trips byte-identical to the file here, apart from one trailing newline
GitHub appends — 22, 23 and 18 `###` headings respectively, every required box `[x]`, none left
unticked.

All three are open and **unlabelled**, which is the correct state. The validation workflow does
not start until a maintainer applies the label during triage, and the catalog pull request is
opened by that workflow rather than by us. There is nothing to do in the meantime except answer
questions on the issues.

### They describe 0.1.0, and SpecUP is now at 0.1.1

Deliberately, not by neglect. The bodies here are the record of what was filed, so they keep
the figures they were filed with, and every one of those figures still holds: the `v0.1.0`
release is still published and its assets still resolve at the digests the issues cite.

What is stale is only the version a reader of those issues sees. Refiling to say `0.1.1` costs
three more issues through the same flow, for two install-ergonomics changes that alter nothing
a catalog entry records beyond the version, URL and digest. The sensible moment to update is
when a maintainer picks these up, or at the next release with real content in it — whichever
comes first. Update the bodies then, from a fresh run of step 5, rather than editing the
version string on top of the previous release's numbers.

## What a listing does and does not buy

Discovery only. The community catalogs are `install_allowed: false`, so a user who finds
SpecUP there and runs `specify extension add openup` gets *"is from a discovery-only catalog;
installation is not allowed."* Installing still means registering SpecUP's own catalog. Every
body here says so in its own text rather than leaving users to meet it at the error message.

## Keeping them current

The figures are stamped from a specific release: version, `download_url`, `sha256`, component
counts, and the verification results each checklist attests to. At the next release, re-derive
them from `catalog/*.json` and a fresh run of step 5 — do not resubmit the previous release's
numbers with a new version string on top.

Checking a testing box that was not exercised is the one failure mode here that the automation
cannot catch, because it validates the artifact rather than the claim.
