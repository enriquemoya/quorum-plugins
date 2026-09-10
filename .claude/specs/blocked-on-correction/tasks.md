# Tasks — a false BLOCKED record, and the method that produced it

## Phase 1 — the record

- [x] T1: clear the false block — files: .claude/specs/cpd-path-proven/status.yml — AC: AC1, AC2, AC3
      Return to PRD_READY, drop blocked_on, append an entry naming the
      inference-from-absence, and attach the probe command and its output that
      established reachability.

## Phase 2 — the mechanism

- [x] T2: BLOCKED requires probe evidence — files: plugins/quorum-orchestrator/skills/quorum-status/SKILL.md, scripts/e2e.py — AC: AC4, AC7
      A transition to BLOCKED carries blocked_on AND the probe that established
      it. When no probe is known, that is itself the finding: say so and escalate
      rather than asserting the precondition.

- [x] T3: the rule reaches every precondition evaluator — files: plugins/quorum-orchestrator/governance/rules/GLOBAL.md, scripts/e2e.py — AC: AC5, AC7
      Governance, not one agent: a precondition is established by running a
      probe. Neither an absent config file nor an unset environment variable is
      evidence of unreachability.

## Phase 3 — the sweep

- [x] T4: sweep existing records — files: scripts/check.py — AC: AC6
      A check that finds any status.yml claiming a precondition without probe
      evidence. Reports; never corrects.

## Phase 4 — the gate

- [x] T5: run both suites — files: (gate; no source changes) — AC: AC7

Amendment (impl audit, iteration 1): T2 and T3 gained `scripts/e2e.py`. AC7
required assertions and no task declared where they would live, so the work was
in scope and the file set was not — a containment finding against the task
list rather than against the change. Recorded here rather than corrected
silently: a file set edited without a note is how bookkeeping drifts.

`.claude/profile.yml` also carries uncommitted changes. They are NOT this
unit's: the panel_tiers block was written before this unit opened. Named so the
next reader does not attribute it here.
