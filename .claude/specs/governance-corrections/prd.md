# PRD — three corrections the dogfood run surfaced

## Problem

Running the pipeline against its own repository found three defects in the
process itself. All three are shipped.

**The task format cannot be written.** `SPEC_STANDARD.md` defines a task as one
line carrying `files:` and `AC:`. A task with more than one path exceeds a
readable line, so an author wraps it — and then neither field parses. In the
first unit of this run, zero of five tasks parsed. The executor reads `files:`
to know what to touch and the batch queue reads it to decide which units may
not run concurrently; both got nothing.

**A finding about the process cannot be routed.** `AUDIT_PROPOSAL.md` offers
`target_step: triage | prd | spec | architecture | design | tasks | impl`. No
stage owns a governance rule, so a finding about one can only be recorded. The
audit that found the task-format defect could name it and could not route it.

**A unit blocked from outside has no state.** `ABANDONED` and `SUPERSEDED` are
decisions someone made; `STUCK` is loop exhaustion. A unit that cannot proceed
because a credential, a service or a tool is absent is none of those, and the
router has nowhere to put it. Found trying to park a unit whose PRD requires a
cross-provider panel in an environment with one model family.

## Users

Anyone writing a `tasks.md`, which is every unit that reaches stage 5. The
first two defects fire immediately; the third fires the first time something
outside the repository is missing.

## Value

A task file that both machines reading it can parse. A finding about the
process that lands somewhere. A blocked unit that says why it is blocked
instead of borrowing a state that means something else.

## Success

- A task with three paths parses for both `files:` and `AC:`.
- A proposal can target the process, and the router knows that target means a
  human rather than a stage.
- A unit blocked on an external precondition reaches a state that names the
  precondition, and is excluded from the queue without being confused with
  loop exhaustion.
- Both suites stay green and gain an assertion per correction.

## Non-goals

- Redesigning the task format. The fix is the smallest change that makes the
  existing one writable.
- A workflow engine for governance changes. The routing target records that a
  human decides; it does not automate the decision.

## Constitution articles touched

- **Article 3.** Each correction adds a guarantee, so each needs an assertion
  that has been watched failing.

## Why this is `--human`

It changes the rules that judge every other unit, including itself. A mistake
here is consistent with everything downstream, which is the failure mode the
supervision exists for.
