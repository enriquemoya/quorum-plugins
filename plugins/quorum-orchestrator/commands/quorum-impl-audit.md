---
argument-hint: "<slug> [--lenses a,b,c] [--dry-run]"
description: The second audit gate. Judges the implementation against the approved scope, with the build/test/lint gate run first — a red gate forbids a clean verdict. Convenes a critic panel over the actual diff, and either clears the unit to deliver or emits a proposal.
---

# /quorum-impl-audit

Gate 8 of the pipeline. Runs on `IN_PROGRESS`; refuses any other state.

This gate audits **what was built**, not what the spec promised. The promise
was audited at the other gate.

## Preconditions

- `status.yml` is `IN_PROGRESS` (or `IMPL_AUDIT` on a re-run).
- A constitution exists.
- `audit_iterations < 3` — the counter is spec-level, so scope rounds already
  spent count here. At the cap, recommend `STUCK`.

## Gate first

Before any judging, run the verification gate:

```
{{profile.commands.type_check}}   or  observed.verified_commands[purpose=type_check]
{{profile.commands.test_unit}}    or  observed.verified_commands[purpose=test_unit]
{{profile.commands.lint}}         or  observed.verified_commands[purpose=lint]
```

**Capture the exit code of the COMMAND, never of a pipeline.** This gate asks
for the last lines of output, and the natural way to get them is
`<command> 2>&1 | tail -40` — which reports `tail`'s exit status. A command that
died with 127 reports 0 through that pipe, and the rule below then passes a
build that never ran.

Run the command first, then read the file:

```bash
<command> >gate.log 2>&1; rc=$?      # rc is the command's
tail -40 gate.log                     # output, separately
```

`set -o pipefail` also works where the shell supports it. What does not work is
trusting `$?` after a pipe, and this was verified rather than assumed: a
missing binary exits 127 directly, 0 through `| tail`, and 127 again with
pipefail set.

**A `VERIFIED` verdict is forbidden when the gate is red, stale, or missing.**
Record exit codes and log paths in the verdict's first section. A non-zero exit
becomes a high-severity blocking finding with `target_step: impl`.

**Exit 127 is not a red build — it is a missing toolchain**, and the two want
different findings. Say which: "the test command is not installed here" sends
the operator to their environment, "three tests fail" sends them to the code.

A clean verdict over a failing build is the single outcome that makes every
future verdict worthless — after it, nobody has reason to believe the next one.

## What it does

1. Delegate to the **quorum-audit** agent at the `impl` gate.
2. Gate run, recorded.
3. **quorum-panel** over the diff with the implementation lenses —
   satisfaction, integrity, test adequacy.
4. Requirement-traceability table: `| requirement | evidence (file:line) |
   PASS/FAIL |`. A FAIL row forbids `VERIFIED` unless `accepted_conditions`
   carries a matching entry.
5. Constitution and data rules checked against the diff.
6. Scope containment: files changed outside `tasks.md`'s declared sets are a
   finding regardless of merit.
7. Matrix, verdict, proposal.

## Verdicts

| Verdict | Means | Next |
|---|---|---|
| `VERIFIED` | gate green, every requirement PASS, no blocking findings | `/quorum-deliver` |
| `VERIFIED_WITH_CONDITIONS` | non-blocking findings recorded | `/quorum-deliver`, conditions carried |
| `NEEDS_FIX` | gate red or blocking findings | `/quorum-implement --fix` |

## Agent mode

A `VERIFIED`-family verdict carrying `panel: single-provider` **may not
auto-advance to delivery.** It records the reason and waits for a human.

The panel is the last check before the work goes outward. When it ran degraded,
the thing standing between an autonomous run and a bad merge is weaker than the
design assumes, and delivery is not the place to discover that.

## What this command must not do

**Do not fix the code.** `/quorum-implement --fix` does, carrying the proposal.

**Do not deliver.** Opening a PR is `/quorum-deliver`, after this verdict.

**Do not accept the spec's word for anything.** Every claim is checked against
the diff. "The spec says tenant filtering is applied" is not evidence that it is.
