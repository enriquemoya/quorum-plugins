# Tasks — reconcile the implementation stage with the pipeline around it

## Phase 1 — the invocation contract

- [x] T1: one argument, one flag set — files: plugins/quorum-orchestrator/commands/quorum-implement.md — AC: AC1, AC2
      Usage takes a slug. Add `--fix` to the table; delete `--complexity`,
      `--resume` and `--include-subtasks` per the decisions in requirements.
      The frontmatter is already correct and is not rewritten — it is the
      thing the rest is reconciled against. The ticket key stays as an optional
      field of a ticket-path unit.

- [x] T2: complexity is read, not re-derived — files: plugins/quorum-orchestrator/commands/quorum-implement.md — AC: AC4
      The auto-detection table becomes what the values mean here. No procedure
      for computing one remains in the file.

## Phase 2 — the duplicated phases

- [x] T3: replace fetch and plan with reading the unit — files: plugins/quorum-orchestrator/commands/quorum-implement.md — AC: AC3, AC7
      Both become reads of the spec artifacts, with `tasks.md` as the plan. The
      prompt file is kept and is the whole keep-set.

- [x] T4: renumber, and state the new gate count — files: plugins/quorum-orchestrator/commands/quorum-implement.md — AC: AC3, AC5
      Removing two phases changes every later number and changes how many times
      the stage stops a person. A `--human` unit that changes its own gate count
      says the new number rather than leaving it to be counted. `--dry-run` is
      redescribed by what it stops before.

## Phase 3 — the tracker

- [x] T5: roles, not products — files: plugins/quorum-orchestrator/commands/quorum-implement.md — AC: AC6
      Every named tracker becomes `{{role:tracker}}`. The artifact table gains
      the null-tracker row: transient, not committed, announced at the gate.

## Phase 4 — the gate

- [x] T6: assert the guarantees — files: scripts/e2e.py — AC: AC8
      Six assertions: slug not ticket key, declared flags match documented
      flags, no complexity-derivation procedure, dry-run states what it stops
      before, no product name plus a stated null-tracker home, and tasks.md
      named as the plan with its AC mapping checked. Each watched failing
      against a broken copy first; the injected defect and resulting count go
      in the commit message.

- [x] T7: run both suites — files: (gate; no source changes) — AC: AC8
