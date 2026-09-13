# Agent Operating Contract — source

> Scoped rules for implementation code (specup.md s7). The repository-root `AGENTS.md` applies
> as well; this adds what is specific to changing code under governance.

## The standards that bind code

Read these before you write anything here. They are part of this contract:

- **`.specify/governance/coding-rules.md`** — Railway Oriented Programming. A function that
  can fail returns a `Result`; a failure is a value on the failure track, never an exception.
  At an HTTP boundary that failure becomes an RFC 9457 problem document with a stable `type`
  URI. An exception thrown for anything but a programmer error is a defect at review, and a
  legitimate one is declared in place with `openup: escape — <reason>`.
- **`.specify/governance/security-practices.md`** — deny by default, authorize at the
  resource, parse untrusted input into typed values at the boundary, bound every size, and
  keep secrets out of logs and out of problem documents.

A new failure mode is not only code. It needs a problem `type`, an acceptance criterion, and a
scenario — otherwise it is an untested path that no check in this repository can see.

## Before changing a file

Every file inside the traceability perimeter must be reachable from a requirement
(`TRC-007`). Before you edit one, know which:

```bash
python3 .specify/extensions/openup/scripts/python/impact.py --of src/auth/authentication_service.ts
```

If that returns nothing, the file is an orphan. Adding an edge to silence the check is not the
fix — find the requirement it actually serves, or raise that there is not one.

## After changing a file

1. **Tests are the specification, not a formality.** Never adjust a test, widen an assertion,
   or narrow a scenario to make a suite go green. The acceptance criterion is the spec;
   changing the test to match the implementation inverts the relationship everything here
   rests on.
2. **Re-derive, do not hand-write.** New test files and scenarios produce new edges:

   ```bash
   python3 .specify/extensions/openup/scripts/python/derive_edges.py --write
   ```
3. **Record evidence**, register it as `EVID-nnnn`, and reference it from the WBS node.
4. **Check before claiming done:**

   ```bash
   python3 .specify/extensions/openup/scripts/python/validate_done.py --json
   ```

## The perimeter

Only files matching `traceability.perimeter` in `openup-config.yml` are governed. If a check
fires on a file that should not be governed, fix the **perimeter** — never invent an edge to
silence it, and never widen the perimeter to hide an untraced file.
