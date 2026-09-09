# Requirements — behavioural evals for the three pipeline skills

## Goals

Give `quorum-status`, `quorum-panel` and `quorum-init` the eval coverage the
other ten skills already have, in the format those ten established.

## In scope

- One `evals/evals.json` per skill, under that skill's directory.
- Coverage of each skill's refusals.
- Fixtures where a case needs one.

## Non-goals

- Running evals in CI. They need a model; `check.py` and `e2e.py` do not.
- Changing the eval format. Ten files establish it.
- Evals for skills that already have them.

## Constraints

- The format is whatever `plugins/quorum-tooling/skills/quorum-memory-bank/evals/evals.json`
  uses. Read it; do not infer it.
- No eval may require network access or a configured tracker.
- Fixtures live under the skill's own `evals/fixtures/`, as the existing ones do.

## Acceptance criteria

- AC1: `quorum-status`, `quorum-panel` and `quorum-init` each have an
  `evals/evals.json` that parses as JSON and carries the same top-level keys as
  the existing ten.
- AC2: every eval names the fixture it reads and states its assertions
  explicitly, so a failure identifies which behaviour changed.
- AC3: each skill's evals cover at least its stated refusals — the "What this
  skill must not do" section is the checklist.
- AC4: `python3 scripts/check.py` and `python3 scripts/e2e.py` stay green.
- AC5: no eval requires a network call or a configured tracker to run.
