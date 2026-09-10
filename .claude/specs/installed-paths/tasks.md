# Tasks — resolve bundled files without guessing the install layout

- [x] T1: the command resolves instead of Globbing a dead path — files: plugins/quorum-orchestrator/commands/quorum-implement.md — AC: AC2
      Delete the Glob-the-cache paragraph and its per-OS examples. The
      four-step resolution replaces it whole, both STOPs included.

- [x] T2: the same four steps in the other five runtime files — files: plugins/quorum-orchestrator/agents/quorum-decision-documenter.md, plugins/quorum-orchestrator/agents/quorum-memory-synchronizer.md, plugins/quorum-orchestrator/agents/quorum-pattern-documenter.md, plugins/quorum-tooling/skills/quorum-memory-bank/SKILL.md, plugins/quorum-workflows/skills/quorum-agent-journal/SKILL.md — AC: AC2
      These five are the ones an earlier draft would have left resolving to
      nothing. The literal fallbacks go, and the Glob gains the root it never
      had — the parent, not a child of it. The memory-bank skill says "never type a literal cache path" and
      then types one — that line is the defect stating itself.

- [x] T3: the docs state what was observed — files: INSTALL.md, docs/plugin-authoring.md — AC: AC3
      The layout as observed, the root named as observed rather than promised,
      and the note that it has changed before.

- [x] T4: assert the literal cannot return — files: scripts/check.py — AC: AC1, AC4
      Parent permitted as a Glob root, children forbidden — get that distinction
      wrong and the check fails every runtime file or none. Allowlist narrowed
      to the observed-layout pattern, self-exclusion by name, watched failing
      against a reintroduced literal.

- [x] T5: smoke the Glob against a real install — files: .claude/runs/installed-paths/ — AC: AC5
      One recorded run, including what it does when two directories match.
      Without it AC2 is text nobody has executed.

- [x] T6: run both suites — files: (gate; no source changes) — AC: AC4
