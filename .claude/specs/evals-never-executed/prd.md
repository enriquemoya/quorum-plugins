# PRD — twenty evals that have never been run

## Problem

Three skills gained eval suites this session: `quorum-init`, `quorum-panel`,
`quorum-status`. Twenty cases in total, written, committed, and **never
executed**. They need a model, which puts them outside CI, and nothing since has
run them.

An eval nobody has run is a file. It has never passed, never failed, and never
demonstrated that its grader distinguishes a good answer from a bad one — which
is the only thing that makes an eval worth having.

The unit that produced them closed `VERIFIED_WITH_CONDITIONS` and recorded this,
along with a second gap: four of `quorum-init`'s eight refusal cases have no
coverage at all.

## Value

The evals become evidence instead of intent.

## Success

- All twenty cases run against a model, and the results are recorded with the
  model and date — an eval result is evidence for the model that produced it.
- Each case is watched failing against a deliberately wrong answer. A grader
  that passes everything is worse than no grader, because it looks like
  coverage.
- The four uncovered `quorum-init` refusals get cases, or are recorded as
  deliberately uncovered with the reason.

## Non-goals

- Putting evals in CI. They cost model calls; the constraint is real and this
  unit does not pretend otherwise.
- Writing evals for the remaining skills. Three were chosen and the rest were
  never claimed.

## Constitution articles touched

- **Article 3.** Twenty assertions exist and none has been observed doing
  anything, which is the exact shape the article forbids.

## The tool exists

`claude plugin eval` runs them, including a no-plugin baseline arm. It was never
invoked during the session that wrote them.
