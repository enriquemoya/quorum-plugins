# Tasks — three corrections the dogfood run surfaced

Written in the format this unit corrects, which is the first check that it works.

## Phase 1 — the shipped defect

- [x] T1: make the task format writable — files: plugins/quorum-orchestrator/governance/rules/SPEC_STANDARD.md — AC: AC1
      The task line carries files: and AC: and does not wrap; prose moves to
      indented continuation lines. States the parser regex so both readers agree.

## Phase 2 — the two holes an audit falls into

- [x] T2: give a proposal somewhere to put a process finding — files: plugins/quorum-orchestrator/governance/rules/AUDIT_PROPOSAL.md — AC: AC2
      target_step gains `governance`, routing to a human in both modes and never
      blocking the unit that raised it.

- [x] T3: add BLOCKED — files: plugins/quorum-orchestrator/skills/quorum-status/SKILL.md, plugins/quorum-orchestrator/PIPELINE.md, plugins/quorum-orchestrator/commands/quorum-orchestrate.md — AC: AC3
      A unit stopped by an external precondition is not STUCK and not a decision.
      Records blocked_on, excluded from the queue, routed as a HALT that reports.

## Phase 3 — the assertions Article 3 requires

- [x] T4: pin all three — files: scripts/e2e.py, scripts/check.py — AC: AC4
      Eight assertions. Verified by reverting the three corrections: seven fail.
