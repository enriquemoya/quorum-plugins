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
  panel_reason: null          # why it degraded, when it did
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
| `BLOCKED` | an external precondition is missing — **not the unit's fault** | any, once the precondition is met |
| `STUCK` | loop control fired — **human only** | any, by a human |

Terminal states refuse every transition except by an explicit human note.

**`BLOCKED` is not terminal and is not `STUCK`.** `ABANDONED` and `SUPERSEDED`
are decisions somebody made; `STUCK` is this unit having exhausted its audit
budget. A unit that cannot proceed because a credential, a service or a tool is
absent has done nothing wrong and has nothing left to try — borrowing `STUCK`
for it would report a loop that never happened, and the iteration count would
say so.

### BLOCKED requires a probe that ran

A `BLOCKED` claim says a capability is absent. That is a measurement, and it
carries the measurement:

```yaml
status: BLOCKED
blocked_on: "a second model family — the panel needs cross-provider dispatch"
probe:
  invocation: "opencode models"          # what was RUN
  exit_code: 0                           # it ran
  observed: "empty list"                 # and what it saw
  at: 2026-09-08T14:22Z                  # when
```

Four rules, each closing a way absence gets mistaken for evidence.

**A probe invokes the capability being claimed, not a proxy for it.** Checking
whether a config file exists is not a probe of reachability, because the file is
not the thing claimed. This defect shipped once: a unit was BLOCKED on "no
second model family" after reading environment variables and finding no config,
while seven models were reachable by a command nobody ran.

**A probe that ran and observed absence is not a probe that failed to run.**
`exit_code: 0` with an empty result is evidence; a non-zero exit is a broken
probe and proves nothing about the capability. Record both fields so the
difference survives, because "the command failed" and "the command found
nothing" are opposite conclusions that look alike in a summary.

**There is no cannot-probe state.** Every version of one recreates the error a
level up: a terminal that asserts the precondition is the original defect, and
one that blocks on it is the same park under a new name. When no probe exists,
the unit **does not enter BLOCKED**. It stays where it is, and the precondition
is appended to `history` as an open question naming what was tried:

```yaml
  - { at: …, from: PRD_READY, to: PRD_READY, actor: agent,
      note: "OPEN QUESTION — precondition 'X' could not be probed. Tried: <what>.
             Not blocked; a human decides." }
```

A same-state history entry is deliberate. Staying put silently is a park nobody
can see; the entry makes it visible in the one place state is read.

**A reachability claim is only as current as its probe.** Reachability varies
with time — a credential expires, a service returns. The `at` timestamp is what
lets a later reader tell a measurement from a memory. Re-probe before acting on
one you did not take.

It is excluded from the queue, like `STUCK`, but for a reason a human can act on
somewhere other than this repository. The router reports the precondition rather
than asking for intervention.



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
count = occurrences of this verdict's evidence_digest in HISTORY
if audit_iterations >= 3          → STUCK
if count >= 2 (this makes 3)      → STUCK
otherwise                         → increment, append, loop
```

`evidence_digest` is a stable digest of the finding evidence references
(`file:line` / artifact refs) a verdict cited, sorted. Three identical digests
mean three rounds that found the same thing — the loop is not converging, and
the iteration count alone would not catch it inside the cap.

### The digest is appended, not overwritten

**Each history entry carries the digest of the verdict that produced it.**
`last_audit.evidence_digest` holds the latest for display; it is not what the
rule reads.

That distinction is the whole rule. An earlier version stored the digest only in
`last_audit`, where each iteration overwrote the one before — so at any moment
exactly one value existed, "seen three times" had nothing to compare against,
and **the check could never fire.** It was written down, it looked like a bound,
and it bounded nothing.

A digest is a digest of *references*, not a path to where the evidence lives.
Two rounds that cited the same three files produce the same digest even though
their transcripts sit in different directories; two rounds that cited different
files must not collide because their transcripts share a parent. Storing the
artifact path instead makes every iteration of a unit look identical, which
fails in the other direction — a loop that IS converging reads as stuck.

## Deriving the queue

`--queue` computes the batch, never reads a stored one:

```
1. glob .claude/specs/*/status.yml
2. keep: status ∈ { PRD_READY, DRAFTING_*, SCOPE_AUDIT, READY*, IN_PROGRESS,
                    IMPL_AUDIT, NEEDS_*, VERIFIED* }
        ∧ profile.autonomy.mode == agent
        ∧ not terminal, not STUCK, not BLOCKED
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
