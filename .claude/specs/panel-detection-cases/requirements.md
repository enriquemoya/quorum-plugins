# Requirements — a fourth detection case for the panel

## Goals
Distinguish a configured-but-unreachable panel from an unconfigured one.

## In scope
- `plugins/quorum-orchestrator/skills/quorum-panel/SKILL.md` detection section.
- One assertion.

## Non-goals
- Reimplementing doctor's diagnostics.

## Acceptance criteria
- AC1: the detection names a fourth cause: the panel is configured but its seats
  are not reachable with the current credentials.
- AC2: its reported fix is authentication or a tier change, never "configure a
  panel".
- AC3: an assertion pins the fourth case, and has been watched failing.
