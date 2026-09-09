# Requirements — a false BLOCKED record, and the method that produced it

## Goals

Make `cpd-path-proven`'s state true, and close the method error that made it
false — in the mechanism, not only in an instruction.

## In scope

- `.claude/specs/cpd-path-proven/status.yml`.
- The `BLOCKED` transition contract in `quorum-status`.
- The precondition rule in every agent that evaluates one, not just triage.
- A sweep of existing records for the same method.

## Non-goals

- Running `cpd-path-proven`. That is its own unit.
- A general evidence framework. The requirement is narrow: a `BLOCKED` claim
  carries the probe that established it.

## Constraints

- The history log is append-only. The original entry stays and is answered.
- `BLOCKED` was added the same day and this is its first use, so the contract
  can still be tightened without migrating existing records.

## Acceptance criteria

- AC1: `cpd-path-proven` is not BLOCKED and carries no `blocked_on`.
- AC2: the history keeps the original entry and adds one stating plainly what
  the measurement got wrong — an inference from absence, not a probe.
- AC3: the unblocking entry carries the probe command and its output. A claim
  that something IS reachable needs the same evidence as a claim that it is
  not; asserting the reverse repeats the error in the other direction.
- AC4: `quorum-status` requires probe evidence on any transition to `BLOCKED`,
  and states what to do when no probe is known — a rule with no runnable probe
  and no terminal for "I cannot probe this" re-arms the failure it prevents.
- AC5: every agent that evaluates a precondition carries the rule, not only
  triage. The rule names the two shapes that produced this: an absent config
  file, and an environment-variable proxy.
- AC6: existing `status.yml` records are swept for preconditions asserted
  without a probe, and any hit is reported rather than silently corrected.
- AC7: an assertion pins AC4 and AC5, and has been watched failing.
