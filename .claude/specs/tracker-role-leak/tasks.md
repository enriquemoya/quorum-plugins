# Tasks — the tracker driver leaked into the agnostic layer

Every file in scope has an owning task. An earlier draft named 12 of 35 and left
23 with no owner, which three critics caught independently.

## Phase 1 — DELEGATE: the job requires a ticket

- [x] T1: the orchestrator agent — files: plugins/quorum-orchestrator/agents/quorum-orchestrator.md — AC: AC1, AC3, AC5
      37 mentions, 8 tool calls. Already references the role in places, which is
      why the co-occurrence check alone would pass it — the tool calls are what
      AC1 catches here.

- [x] T2: the four ticket-consuming agents — files: plugins/quorum-orchestrator/agents/quorum-qa-handoff-publisher.md, plugins/quorum-orchestrator/agents/quorum-ticket-image-analyzer.md, plugins/quorum-orchestrator/agents/quorum-ticket-validator.md, plugins/quorum-orchestrator/agents/quorum-ticket-analyzer.md — AC: AC1, AC3, AC5
      The image analyzer carries 13 tool calls in 9 mentions — the densest
      coupling in the marketplace.

- [x] T3: the prompt and PR files — files: plugins/quorum-orchestrator/agents/quorum-prompt-builder.md, plugins/quorum-orchestrator/agents/quorum-pr-generator.md, plugins/quorum-orchestrator/commands/quorum-prompt-gen.md, plugins/quorum-orchestrator/commands/quorum-pr-template.md — AC: AC1, AC3, AC5

- [x] T4: validate-ticket and init — files: plugins/quorum-orchestrator/commands/quorum-validate-ticket.md, plugins/quorum-orchestrator/skills/quorum-init/SKILL.md — AC: AC1, AC3, AC5
      `/quorum-init` is where a consumer declares its tracker, so this one must
      name the role and must not assume which driver answers.

- [x] T5: the QA skills and branch naming — files: plugins/quorum-tooling/skills/quorum-manual-qa-test-cases/SKILL.md, plugins/quorum-workflows/skills/quorum-qa-test-plans/SKILL.md, plugins/quorum-tooling/skills/quorum-create-branch/SKILL.md — AC: AC1, AC2, AC3, AC5
      All three hardcode a key pattern. `create-branch` needs a null-tracker
      answer specifically: `ticket_prefix` may be unset when the role is null,
      and a branch name still has to be produced.

## Phase 2 — DELETE: the job does not require a ticket

- [x] T6: the four unit-test generators — files: plugins/quorum-tooling/skills/quorum-gen-unit-tests-dotnet4x/SKILL.md, plugins/quorum-tooling/skills/quorum-gen-unit-tests-dotnet9/SKILL.md, plugins/quorum-tooling/skills/quorum-gen-unit-tests-jasmine/SKILL.md, plugins/quorum-tooling/skills/quorum-gen-unit-tests-vitest/SKILL.md — AC: AC4
      10 mentions each, same shape in all four. They do not delegate; they stop
      asking.

- [x] T7: the obsidian-vault tree — files: plugins/quorum-workflows/skills/quorum-obsidian-vault/ — AC: AC4
      Nine files: SKILL.md, evals, two scripts, three assets, two references. A
      vault scaffolder does not need a ticket system.

- [x] T8: the five remaining — files: plugins/quorum-tooling/skills/quorum-code-review/SKILL.md, plugins/quorum-tooling/skills/quorum-memory-bank/SKILL.md, plugins/quorum-workflows/skills/quorum-agent-journal/SKILL.md, plugins/quorum-orchestrator/agents/quorum-decision-documenter.md, plugins/quorum-orchestrator/agents/quorum-test-specialist.md — AC: AC4
      One mention each, plus `quorum-workflows/.claude-plugin/plugin.json`,
      whose description names the product.

## Phase 3 — the gate

- [x] T9: the four checks — files: scripts/check.py — AC: AC1, AC2, AC3, AC4, AC6
      Tool names, key patterns, co-occurrence, and the DELETE set staying clean.
      Self-exclusion by name — this file must contain the tool names it forbids,
      and a guard in this repository has already shipped twice without that.
      `.claude/specs/` and `.claude/runs/` exempt: they name the tools to
      explain them, and this spec would trip a repo-wide scan.

- [x] T10: the documentation — files: docs/claude-skills-overview.md, docs/claude-code-concepts.md, docs/plugin-authoring.md — AC: AC8
      The role, and a plain statement that one driver ships.

- [x] T11: both suites — files: (gate) — AC: AC7
