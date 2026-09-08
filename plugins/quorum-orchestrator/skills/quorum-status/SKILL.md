---
name: quorum-status
argument-hint: "<slug> [--set <STATE> --note <text>] [--check] [--queue]"
description: Read, validate and transition the status.yml that governs a unit of work. The single source of truth for where a spec or ticket is in the pipeline — every stage reads it before acting and writes it after. Also derives the batch queue and the session report.
---

# status.yml — the state of a unit of work

Every unit under `.claude/specs/<slug>/` carries a `status.yml`. It is the only
answer to "where is this?". Stages read it before acting and append to it after.

**State is never inferred from prose.** Not from a summary, not from the
presence of a file, not from what the last message said. If `status.yml` says
`DRAFTING_TASKS`, the unit is drafting tasks even if `tasks.md` looks finished —
because the file being finished and the stage being closed are different claims,
and only one of them is recorded.

## The file

```yaml
slug: invoice-export
origin: spec                  # spec | ticket        — set by triage
complexity: medium            # simple | medium | complex — set by triage
status: DRAFTING_TASKS
created: 2026-09-07
updated: 2026-09-07

# Append-only. Never rewrite an entry.
history:
  - { at: 2026-09-07T10:04Z, from: null,   to: TRIAGE,        actor: human, note: "created" }
  - { at: 2026-09-07T10:11Z, from: TRIAGE, to: DRAFT_PRD,     actor: human, note: "triage: spec path, medium" }
  - { at: 2026-09-07T11:32Z, from: DRAFT_PRD, to: PRD_READY,  actor: human, note: "PRD approved" }

in_flight: true

# Spec-level, NOT per gate. See "The cap is per spec" below.
audit_iterations: 0

last_audit:
  step: null                  # scope-audit | impl-audit
  verdict: null
  iter: 0
  proposal_ref: null          # runs/<slug>/iter-NN-proposal.yml
  governance_version: null    # which rules produced this verdict
  panel: null                 # cpd | single-provider
  evidence_digest: null       # for same-evidence-thrice detection

last_impl: { commit: null }

depends_on: []                # slugs. Hard: a parked dependency blocks this unit.
superseded_by: null
accepted_conditions: []       # conditions a *_WITH_CONDITIONS verdict recorded
```

`created` and `updated` are **derived at write time**, never typed. A template
with a date in it ships that date to every unit created from it.

## States

| State | Meaning | Next |
|---|---|---|
| `TRIAGE` | deciding origin and complexity | `DRAFT_PRD` or `ANALYZING` |
| `DRAFT_PRD` | PRD being written — **always human** | `PRD_READY` |
| `PRD_READY` | PRD approved. **The agent frontier.** | `DRAFTING_SPEC` |
| `ANALYZING` | ticket being analysed | `DRAFTING_TASKS` |
| `DRAFTING_SPEC` | requirements | `DRAFTING_ARCH`, or `DRAFTING_TASKS` if simple |
| `DRAFTING_ARCH` | architecture | `DRAFTING_DESIGN` |
| `DRAFTING_DESIGN` | design | `DRAFTING_TASKS` |
| `DRAFTING_TASKS` | task list | `SCOPE_AUDIT` |
| `SCOPE_AUDIT` | audit running | `READY`, `READY_WITH_CONDITIONS`, `NEEDS_REVISION` |
| `READY` / `READY_WITH_CONDITIONS` | cleared to implement | `IN_PROGRESS` |
| `NEEDS_REVISION` | scope rejected | the proposal's `target_step` |
| `IN_PROGRESS` | implementing | `IMPL_AUDIT` |
| `IMPL_AUDIT` | audit running | `VERIFIED`, `VERIFIED_WITH_CONDITIONS`, `NEEDS_FIX` |
| `NEEDS_FIX` | implementation rejected | `IN_PROGRESS` |
| `VERIFIED` / `VERIFIED_WITH_CONDITIONS` | cleared to deliver | `DELIVERING` |
| `DELIVERING` | PR open, tracker updating | `MERGED` |
| `MERGED` | terminal | — |
| `ABANDONED` / `SUPERSEDED` | terminal | — |
| `STUCK` | loop control fired — **human only** | any, by a human |

Terminal states refuse every transition except by an explicit human note.

## Transitions

A transition is valid only when the routing table in `PIPELINE.md` allows it
from the current state. **Refuse an invalid transition; do not repair it.** A
stage that finds an unexpected state has either been invoked out of order or is
reading a unit someone else is driving — both want a human, not a guess.

Every write does three things, in order:

1. **Read** the current file. A missing or unparseable `status.yml` BLOCKS.
2. **Validate** the transition against the routing table.
3. **Append** to `history` and update `status` / `updated` in one write.

The append carries `actor: human | agent` — which is how a later reader can
tell an autonomous run from a supervised one without reconstructing it.

## The cap is per spec

`audit_iterations` counts audit rounds across the **whole unit**, both gates
together. Three scope-audit rounds leave none for the implementation audit, and
that unit reaches `STUCK` without ever implementing.

That is intended. A scope revised three times without converging is a problem
in the PRD, not in the code, and burning the remaining budget on an
implementation built from it wastes the run.

**The counter is read from the file, not held by the agent.** An agent that
tracks its own iterations has no cap: a fresh context starts at zero, and the
loop that the cap exists to stop is exactly the loop that produces fresh
contexts.

Before taking any audit loop:

```
read audit_iterations from status.yml
if audit_iterations >= 3          → STUCK
if evidence_digest seen 3 times   → STUCK
otherwise                         → increment, write, loop
```

`evidence_digest` is a stable digest of the finding evidence references
(`file:line` / artifact refs) a verdict cited, sorted. Three identical digests
mean three rounds that found the same thing — the loop is not converging, and
the iteration count alone would not catch it inside the cap.

## Deriving the queue

`--queue` computes the batch, never reads a stored one:

```
1. glob .claude/specs/*/status.yml
2. keep: status ∈ { PRD_READY, DRAFTING_*, SCOPE_AUDIT, READY*, IN_PROGRESS,
                    IMPL_AUDIT, NEEDS_*, VERIFIED* }
        ∧ profile.autonomy.mode == agent
        ∧ not terminal, not STUCK
3. drop: any unit whose depends_on includes a slug that is not MERGED
4. order topologically by depends_on; a cycle HALTs and names the cycle
5. exclude from concurrency: units whose task file sets fall in the same
   stack.components entry — measured from tasks.md and profile.stack, not asked
```

Step 3 is what makes `depends_on` hard. A unit whose dependency is parked does
not run, because implementing against a base that was parked produces work that
has to be redone.

A stored queue would be a second source of truth that drifts from the first.
The rule against inferring state from prose applies equally to inferring it
from a second file.

## Deriving the session report

At the end of a batch, read every `status.yml` the run touched and group:

```
QUEUE — {n} eligible, {duration}

  MERGED      {n}   {slugs}
  PARKED      {n}   {slug}  → escalation: {reason}
  STUCK       {n}   {slug}  → {iterations} iterations, same evidence {n}×

  Not run     {n}   depends_on: {slug} ({state})
```

`Not run` is not filler. An unattended run is only reviewable if it says what
it did not do and why — a report listing three successes and omitting the two
units it never reached reads as complete and is not.

## What this skill must not do

**Do not repair a malformed `status.yml`.** Report it and stop. A repaired
state file is a state file someone guessed at, and every downstream decision
inherits the guess.

**Do not rewrite history.** Corrections are appended with a note, never edited
in place. The value of an append-only log is entirely in the fact that it
cannot be tidied.

**Do not write a state the routing table does not allow.** Including "obviously
correct" ones — if the table is wrong, fix the table.

**Do not set `origin` or `complexity` outside triage.** They govern which
stages run; changing them mid-flight silently changes what was audited.

**Do not derive state from artifacts on disk.** A finished-looking `tasks.md`
does not mean `DRAFTING_TASKS` is closed. Only the transition closes it.
