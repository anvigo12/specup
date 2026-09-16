# Governance Index — governance

> The context map for this directory.
>
> **Checked by** — `CTX-001`, `CTX-002`. `APV-000` fails when `approval-matrix.md` names no
> approver at all.

## Purpose

Who may decide what, how a change to a baselined artifact is handled, and whose signature
counts as a human approval.

## Files here

| File | What it settles | Checked by |
|---|---|---|
| `approval-matrix.md` | who may approve what | `APV-000` (names somebody), `APV-003` (an approval names one of them) |
| `change-control.md` | how a baselined artifact changes | nothing — no commit hook forces a change through it |
| `allowed-signers` | whose signature counts | `APV-002`, and only when an approval declares a commit |

## Not here, and why

`language-rules.md`, `coding-rules.md` and `security-practices.md` are seeded by
`init_openup.py` into a real project and are omitted from this example. Nothing reads them —
they bind at review — and 45 KB of standard text would bury the parts of this tree a gate
actually looks at. Run `init_openup.py` to see them.

`definition-of-ready.md`, `definition-of-done.md` and `quality-gates.md` are **generated** by
`render_views.py` from the code that enforces them, and are absent here for a different
reason: they are derived artifacts, and committing a copy into an example is how a generated
document starts disagreeing with the check it describes.
