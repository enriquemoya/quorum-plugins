# Tasks — behavioural evals for the three pipeline skills

Each task's own line carries `files:` and `AC:`. Prose sits indented beneath it,
because a wrapped task line parses as neither.

## Phase 1 — read the established format

- [ ] T1: record the eval format — files: (read-only) — AC: AC1
      Read `plugins/quorum-tooling/skills/quorum-memory-bank/evals/evals.json`.
      Note the top-level keys, the per-eval keys, and how fixtures are named.

## Phase 2 — one skill at a time, each leaving the tree valid

- [ ] T2: evals for quorum-status — files: plugins/quorum-orchestrator/skills/quorum-status/evals/evals.json — AC: AC1, AC2, AC3, AC5
      Cover its refusals: does not repair a malformed status.yml, does not
      rewrite history, does not write a state the routing table disallows, does
      not derive state from artifacts on disk.

- [ ] T3: evals for quorum-panel — files: plugins/quorum-orchestrator/skills/quorum-panel/evals/evals.json — AC: AC1, AC2, AC3, AC5
      Cover detection order (three distinguishable causes), no verdict on an
      incomplete debate, no merged rebuttals, read-only critics, no silent
      degradation.

- [ ] T4: evals for quorum-init — files: plugins/quorum-orchestrator/skills/quorum-init/evals/evals.json — AC: AC1, AC2, AC3, AC5
      Cover the rules the dogfood run exercised: the polyglot sweep past a
      workspace declaration, gitignored durable artefacts, an empty constitution
      as a valid answer, null versus false.

## Phase 3 — the gate

- [ ] T5: run both suites — files: (gate; no source changes) — AC: AC4
      `python3 scripts/check.py` and `python3 scripts/e2e.py`, both green.

Notes:
- No test task. The evals ARE the tests and nothing here generates them, which
  is why `roles.unit-tests-gen` is null.
- All file sets fall in `quorum-orchestrator`, so this unit and
  `cpd-path-proven` may not run concurrently.
