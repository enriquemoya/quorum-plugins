# Requirements — three corrections the dogfood run surfaced

## Goals

Make the task format writable, give a process finding somewhere to land, and
give a unit blocked from outside a state that says so.

## In scope

- `SPEC_STANDARD.md` task format.
- `AUDIT_PROPOSAL.md` `target_step`.
- The `BLOCKED` state across the three files that define the state set.
- One assertion per correction.

## Non-goals

- Redesigning the task format beyond making the existing one writable.
- Automating what happens after a `governance` target.

## Acceptance criteria

- AC1: a task carrying three paths parses for both `files:` and `AC:`.
- AC2: a proposal can name the process as its target, and that target routes to
  a human without blocking the unit that raised the finding.
- AC3: a unit stopped by an external precondition reaches a state that records
  the precondition and is excluded from the queue, distinct from `STUCK`.
- AC4: each correction has an assertion, and each assertion has been watched
  failing.
