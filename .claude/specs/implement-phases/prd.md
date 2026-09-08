# PRD — reconcile the implementation stage with the pipeline around it

## Problem

`/quorum-implement` is the seam between what this marketplace was and what it
became. It still runs the seven phases it had when it WAS the entry point,
taking a ticket key and driving fetch → analyze → plan → implement → test →
review → PR. The pipeline now does five of those seven upstream, in stages with
their own audits, and hands this stage a unit whose scope has already been
audited READY.

So the stage re-does work that was already gated. Its Phase 1 fetches context
that `analysis.md` or the spec artifacts already hold; its Phase 2 plans work
that `tasks.md` already lists and that the scope audit already traced. Every one
of those phases has its own human gate, so the cost is not only duplication —
it is a gate asking about a decision made two stages earlier.

Nothing is broken today. It is the one place where following the documents means
doing the same thing twice, and the second time with less information.

## Users

Anyone the pipeline routes to implementation, which is every unit that reaches
READY.

## Value

The stage does what its name says and nothing the pipeline already did, so the
gates it asks about are decisions that are actually open.

## Success

- Every phase that duplicates an upstream stage is removed, and what it
  contributed that the upstream stage does not is identified and kept.
- The stage reads `tasks.md` as its plan rather than producing one.
- `--fix` carries the implementation audit's proposal as the run's scope.
- The e2e suite passes before and after, and gains an assertion that the stage
  refuses a unit outside the READY family.

## Non-goals

- Changing what the seven phases do where they are not duplicated. Testing,
  review and PR-artifact generation are this stage's own work.
- Touching the upstream stages. If a phase here is better than its upstream
  counterpart, that is a finding about the upstream stage, recorded and left.

## Constitution articles touched

- **Article 3.** The stage's preconditions are stated as guarantees and have no
  assertion behind them.

## Why this one is `--human`

This stage executes the pipeline. Rewriting it while running through it means a
mistake changes the machinery mid-run, and the run would be consistent with the
mistake. Every gate here is answered by a person.
