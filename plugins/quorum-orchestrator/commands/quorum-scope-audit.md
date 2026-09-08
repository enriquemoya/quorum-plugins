---
argument-hint: "<slug> [--lenses a,b,c] [--dry-run]"
description: The first audit gate. Judges whether a unit's scope is sound and traceable enough to implement — before any code is written. Convenes a critic panel, walks the constitution, and either clears the unit to implement or emits a proposal naming the stage the fix belongs to.
---

# /quorum-scope-audit

Gate 6 of the pipeline. Runs on `DRAFTING_TASKS`; refuses any other state.

The question is not "is this spec good writing". It is **"is there enough here
to implement safely, and does any of it violate what this project refuses to
do?"**

## Preconditions

- `status.yml` is `DRAFTING_TASKS` (or `SCOPE_AUDIT` on a re-run).
- A constitution exists. Without one, half the audit is silently absent — stop
  and route to `/quorum-init`.
- `audit_iterations < 3`. At the cap, recommend `STUCK` and stop.

## What it does

1. Delegate to the **quorum-audit** agent at the `scope` gate.
2. It authors a neutral brief and convenes **quorum-panel** with the scope
   lenses — traceability, constitution, feasibility.
3. It walks every constitution article whose `Applies to` includes this unit's
   `origin`, and names the ones it skipped.
4. It traces intent → acceptance criteria → tasks, both directions.
5. It emits the matrix, the verdict, and — for any non-clean verdict — the
   proposal.

## Verdicts

| Verdict | Means | Next |
|---|---|---|
| `READY` | no blocking findings | `/quorum-implement` |
| `READY_WITH_CONDITIONS` | non-blocking findings recorded as conditions | `/quorum-implement`, conditions carried |
| `NEEDS_REVISION` | blocking findings | the proposal's `target_step` |

## Promotion, not rejection

A ticket-path unit whose acceptance criteria turn out to be unusable is not
rejected. The verdict is `NEEDS_REVISION` with a proposal whose `target_step`
is `prd` — promoting it to the spec path.

That crosses the agent frontier, so **it always stops for a human**, in both
autonomy modes. It changes what work is being done, not how it is done.

## What this command must not do

**Do not fix the spec.** The auditor names what is wrong; the drafting stage
changes it. An auditor that tidies the artifact it is judging has removed the
evidence for its own finding.

**Do not clear a unit whose panel did not conclude.** An incomplete debate
yields no verdict — that is the contract, not a failure to route around.

**Do not treat a complexity-skipped stage as missing.** `simple` units have no
`architecture.md` by design, and `status.yml` records the skip.
