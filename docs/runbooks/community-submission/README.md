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

1. Open the issue from the template and paste the field values from the matching file.
2. A maintainer applies the `extension-submission` / `preset-submission` / `bundle-submission`
   label during triage. Do not apply it yourself and do not ask for it.
3. That label starts an agentic workflow which validates the release, verifies the
   `download_url` and digest, and opens the catalog PR.

A version bump or a repair is an update and needs the same flow — there is no lighter path for
changing an entry that already exists.

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
