# Licensing — what SpecUP is under, and what changed

**Audience:** anyone deciding whether they may use SpecUP, and anyone working on it.

From **0.1.2**, SpecUP is under the [Business Source License 1.1](../../LICENSE), with an
Additional Use Grant that permits production use and a Change License of MIT that takes effect
four years after each version is published.

It is **source-available, not open source.** The Open Source Initiative does not approve BUSL,
and this document does not claim otherwise. Saying "open source" of a BUSL project is the exact
class of claim this project exists to reject.

> This page is a reading of the license, written to be useful. It is not the license and it is
> not legal advice. Where this page and [`LICENSE`](../../LICENSE) disagree, `LICENSE` wins.

## The three files

| File | What it is |
|---|---|
| [`LICENSE`](../../LICENSE) | BUSL-1.1, the terms SpecUP 0.1.2 onward is under |
| [`LICENSE-MIT`](../../LICENSE-MIT) | the Change License, and the terms 0.1.0 and 0.1.1 shipped under |
| this page | the reasoning, which BUSL covenant 4 forbids putting in `LICENSE` |

That last row is a constraint, not a preference. BUSL's covenant 4 is *"Not to modify this
License in any other way"* — the parameters block may be filled in and nothing else may be
touched. A licensor who annotates the terms loses the right to call the result a Business
Source License.

## What you may do, without asking anyone

The Additional Use Grant permits **production use**. In plain terms:

| | |
|---|---|
| **Yes** | Govern your own software with it, at any scale, commercial or not |
| **Yes** | Run agents against repositories you or your organisation control |
| **Yes** | Read, modify, fork, and redistribute it under these same terms |
| **Yes** | Build internal tooling on top of it |
| **Yes** | Sell consulting, integration, training or development services around it |
| **No** | Provide a *Governed Agent Service* — see below |

A **Governed Agent Service** is a commercial offering that lets third parties, other than your
own employees and individual contractors, reach SpecUP's functionality in whole or in
substantial part: hosted by you, embedded in someone else's product, or shipped as a component
of one. That is the one thing withheld, and it is withheld because it is the thing being sold.

The services carve-out is deliberate and is stated in the grant itself. Running SpecUP for a
client, as part of delivering software to that client, is not a Governed Agent Service — so
long as the client's own use would itself be permitted here.

If you need something this grant does not cover, the route is a commercial license, and
`LICENSE` names where to ask.

## What did not change, and will not

**SpecUP 0.1.0 and 0.1.1 remain under the MIT License, permanently.**

This is not an oversight and it is not a loophole waiting to be closed. MIT is irrevocable for
copies already distributed. The `LICENSE` file at the `v0.1.0` and `v0.1.1` tags says MIT, and
it will keep saying MIT, because relicensing changes the terms of future distributions and
cannot reach a copy someone already holds. Anyone may fork `v0.1.1` today and continue a
permissively licensed governance engine from it, forever, and nothing here prevents that.

So the honest statement of what this relicense protects is: **everything from 0.1.2 forward, and
nothing before it.** The validators, templates, gates and workflows as they stood at 0.1.1 are
already out, under terms that cannot be withdrawn. What is newly protected is the work that has
not shipped yet — which is, almost entirely, the agent runtime.

Anyone reading this to decide whether SpecUP might be pulled out from under them should weigh
that fact rather than a promise. Four-year conversion to MIT is written into the license; the
existence of a permissively licensed `v0.1.1` is written into git.

## The Change Date

Each version becomes available under MIT **four years after it is first published**, per
version, automatically.

The date is stated as that formula rather than as a fixed calendar date. BUSL's own terms make
the fourth anniversary of publication a ceiling regardless — *"the Change Date, or the fourth
anniversary of the first publicly available distribution of a specific version, whichever comes
first"* — so a formula and the maximum date it can express are the same thing, and the formula
cannot go stale in a file that ships with every release. A hardcoded date would need bumping at
each version and would be wrong in exactly the silent way this repository spends most of its
effort detecting.

## Why MIT is the Change License, and not Apache-2.0

BUSL covenant 1 requires a Change License that is **GPL-2.0-compatible**. Apache-2.0 is not: its
patent and indemnity terms are incompatible with GPL-2.0, and it is compatible only from
GPL-3.0 onward. Naming Apache-2.0 would breach the covenant that grants the right to use the
BUSL text and name at all.

MIT is GPL-2.0-compatible, so it satisfies the covenant. It is also the license SpecUP is
leaving, which means the conversion returns each version to precisely what it was rather than to
something adjacent to it.

## The dependency position, which the relicense does not change

[`release-plan-0.1.2.md`](../runbooks/release-plan-0.1.2.md) §1 ruled out depending on
`langgraph-api`, the Elastic-2.0 Agent Server binary, on the grounds that it would convert a
permissively licensed tool into one needing a commercial key. SpecUP is no longer permissively
licensed, so it is worth saying clearly that **the conclusion survives and the reason does not.**

Becoming source-available grants no rights to anyone else's source-available software. Elastic's
license binds SpecUP exactly as it did before. What changes is who bears the cost: the constraint
used to protect SpecUP's users from an unannounced commercial dependency, and it now also
protects SpecUP's *customers* from being pushed into a second vendor's agreement to run something
they are already paying for.

So the rule holds in the same words: run graphs **in-process against the MIT `langgraph`
library**, never against the Agent Server. Where the Agent Server is genuinely the right answer —
multi-tenant, many concurrent runs — that stays an operator's decision to license, taken
knowingly.

### There is now a third option, and 0.1.3 takes it

[**Aegra**](https://github.com/aegra/aegra) is an **Apache-2.0** implementation of the Agent
Protocol on FastAPI and PostgreSQL, and it describes itself as *"a drop-in replacement for
LangSmith Deployments. Use the same LangGraph SDK, same APIs, but run it on your own
infrastructure."* Its dependency list was read rather than trusted, and it is the part that
matters: `langgraph`, `langgraph-sdk` and `langgraph-checkpoint-postgres`, and **no
`langgraph-api`, `langgraph-runtime` or `langgraph-cli`** — none of the Elastic-licensed
packages. So it delivers what the Agent Server delivers without the licence that made the Agent
Server unusable here.

Apache-2.0 is permissive and imposes nothing on a BUSL-1.1 work beyond notice and attribution,
which means a `NOTICE` file becomes a shipping requirement at the point Aegra is vendored or
redistributed. It is not a candidate for this project's **Change License** — covenant 1 rules
Apache-2.0 out, for the reasons above — but that is a separate question from depending on it,
and the two should not be confused.

**Two constraints come with it, and neither is a licence question:**

- **Python `>=3.12`.** SpecUP declares `>=3.10` in `bundle.yml` and `extension.yml`, and the
  0.1.3 research had already raised that to `>=3.11` for `deepagents`. Aegra raises it again.
- **PostgreSQL and Redis become runtime dependencies**, and that is the one to argue about
  before adopting rather than after. `NON-FR-CORE-0001` is filesystem authority: state lives in
  files, because a file can be read by a reviewer, diffed, and version-controlled. A checkpoint
  database is a second state store that none of those things are true of. The defensible line
  is that *agent execution* state and *governance* state are different objects and only the
  second is SpecUP's — but that line has to be drawn deliberately, in an ADR, because the
  undrawn version of it is how a filesystem-first tool acquires a database nobody decided on.

Open SWE itself is MIT, which imposes nothing. MIT permits incorporating a work into a
source-available or proprietary product provided the notice is kept, so adopting Open SWE as the
`specup-agent` default stack never required this relicense. Monetising it did. The two are worth
keeping separate, because conflating them would make the license change look forced when it was
chosen.

## Third-party code

There is none vendored. Every file in this repository is the copyright of one author, which is
what made relicensing possible without tracing consent — verified by `git log --format='%an'`
across every commit.

When Open SWE lands as the `specup-agent` stack, that stops being true, and the MIT notices for
the incorporated portions become a shipping requirement rather than a courtesy. A `NOTICE` file
is the place for them, and it does not exist yet because nothing is vendored yet.

## What checks any of this

**Nothing.** This is the honest part.

No validator reads a license. The `license:` field in
[`extension.yml`](../../extensions/openup/extension.yml),
[`bundle.yml`](../../bundles/specup/bundle.yml),
[`preset.yml`](../../presets/openup-governance/preset.yml) and the four `workflow.yml` files is a
display string that Spec Kit copies into its catalog verbatim — `tools/build_catalog.py`'s
`PASSTHROUGH` tuple, whose own comment says everything in it is display-only. Three tests assert
the field is *present*; none asserts what it says. No schema constrains the value.

So seven manifests, two license files and this page are kept consistent by a person reading them,
and a stale `license: "MIT"` in a workflow manifest would ship green. It is recorded as a risk
in [`.specify/risks/risk-register.yaml`](../../.specify/risks/risk-register.yaml) rather than
described as handled.
