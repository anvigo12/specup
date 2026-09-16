# My Project — the deliverable

> **Answers** — what `My Program` is building. This is the application: source, tests, and
> the documents that belong with them.
>
> **Does not answer** — anything about governance. There is no `.specify/` here, no WBS, no
> risk register and no traceability store. Those live in `../my-program/`.
>
> **Filled in badly when** — someone copies a `.specify/` in here as well, and the program now
> has two graphs that will disagree. If this project needs its own governance, it gets its own
> program; it does not get a second copy of this one.
>
> **Checked by** — **nothing in this directory.** Not one validator reads a file here, and the
> reason is the point of this example. See below.
>
> **Authority** — the team building it.

## Why no check reaches these files

`My Program`'s traceability perimeter is `src/**`, evaluated against **its own root**.
`graph.perimeter_files()` walks the project root and nothing above it, so `../my-project/src/`
is not in scope and never can be, whatever the include pattern says.

The consequence is worth stating plainly rather than discovering:

| | one root | two roots (this example) |
|---|---|---|
| `implements` edges to a file path | yes | no |
| backward coverage (`TRC-007`) | measures something | vacuous — nothing in the denominator |
| `DOC-*` docstring checks | run | no files to read |
| orphan source files (`TRC-008`) | reported | invisible |
| artifact-level traceability | yes | yes — requirement, criterion, risk, WBS node |

Neither layout is wrong. A program that coordinates several delivery teams genuinely is not
one repository, and pretending otherwise produces a perimeter full of paths nobody owns. What
is wrong is running the second layout and reporting its coverage figure as though it were the
first — which is why `openup-config.yml` in the program says so in the perimeter block, and
why `.specify/traceability/index.md` records backward coverage as *vacuous* rather than as
100%.

## Bringing this project under governance

When the code is ready to be traced at file level, one of two things happens, and both are
decisions rather than edits:

1. **Merge the roots.** Move `my-program/.specify/` to this project's root. `implements`
   edges can then name `src/greeting/greeter.py`, and the `DOC-*` checks have Python to read.
2. **Give this project its own program.** Run `init_openup.py` here, and let the two graphs
   reference each other by artifact id rather than by path.

## Layout

```
src/greeting/        the greeting service itself
tests/               its tests, named so test-file-naming-convention can find their subject
docs/                what the team needs that is not governed
```

The file names here are already in the shape the derivation rules expect:
`tests/test_greeter.py` strips its `test_` prefix and finds `src/greeting/greeter.py`, so the
moment these files land inside a perimeter, `derive_edges.py --write` produces a `tests` edge
without anyone asserting one. Naming a test after what it tests is the cheapest traceability
in the system, and it is free only if it is done from the start.
