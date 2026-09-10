# Tasks — the tracker driver leaked into the agnostic layer

## Phase 1 — near the ticket path, the call becomes a delegation

- [ ] T1: the orchestrator agent — files: plugins/quorum-orchestrator/agents/quorum-orchestrator.md — AC: AC1, AC3
      32 occurrences, the largest single concentration. Ticket fetching becomes
      `{{role:tracker}}`, with the null case naming what is skipped.

- [ ] T2: the handoff publisher and the image analyzer — files: plugins/quorum-orchestrator/agents/quorum-qa-handoff-publisher.md, plugins/quorum-orchestrator/agents/quorum-ticket-image-analyzer.md — AC: AC1, AC3
      Both act on a ticket. Both must say what they do without one.

- [ ] T3: the QA skills — files: plugins/quorum-tooling/skills/quorum-manual-qa-test-cases/SKILL.md, plugins/quorum-workflows/skills/quorum-qa-test-plans/SKILL.md — AC: AC1, AC3

## Phase 2 — far from it, the mention is deleted

- [ ] T4: the four unit-test generators — files: plugins/quorum-tooling/skills/quorum-gen-unit-tests-dotnet4x/SKILL.md, plugins/quorum-tooling/skills/quorum-gen-unit-tests-dotnet9/SKILL.md, plugins/quorum-tooling/skills/quorum-gen-unit-tests-jasmine/SKILL.md, plugins/quorum-tooling/skills/quorum-gen-unit-tests-vitest/SKILL.md — AC: AC4
      Generating unit tests does not require a ticket system. These do not
      delegate; they stop asking.

- [ ] T5: branch naming and the remaining files — files: plugins/quorum-tooling/skills/quorum-create-branch/SKILL.md, plugins/quorum-orchestrator/PROFILE_SCHEMA.md, plugins/quorum-orchestrator/agents/quorum-pr-generator.md — AC: AC1, AC2
      The branch skill validates `PROJ-\d` by hand; the profile already carries
      `ticket_prefix` and requires it whenever a tracker role is set.

## Phase 3 — the gate

- [ ] T6: assert the coupling cannot return — files: scripts/check.py — AC: AC5
      Tool names outside the driver, and hardcoded key patterns. Watched failing.

- [ ] T7: the documentation — files: docs/claude-skills-overview.md, docs/claude-code-concepts.md, docs/plugin-authoring.md — AC: AC1

- [ ] T8: both suites — files: (gate) — AC: AC6
