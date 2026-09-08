# GLOBAL.md — working rules for every stage

Defaults shipped with the plugin. A consumer repo overrides any of them by
placing a file of the same name in `.claude/governance/rules/`.

## Scope

- No implementation without an approved scope: status must be READY-family
  before `/quorum-implement`.
- Do not edit files outside the declared scope of the unit's `tasks.md`.
- Prefer minimal, mechanical diffs. Additive-only schema and API changes unless
  the approved scope says otherwise.

## Evidence

- Every finding cites `file:line` or an artifact reference. A finding nobody can
  trace back to a specific thing cannot be acted on.
- Run the build, type-check and test gates before any final verdict. Report
  blocker-first.
- A verdict with no blockers says so explicitly, with the reason the set is
  empty. Silent passes are forbidden.

## Determinism

- The same inputs produce the same verdict within a governance version.
- Every verdict records the `governance_version` that produced it and the
  `panel` that ran, so it can be traced to the rules that judged it.

## Stack facts are not rules

Nothing in `governance/` names a language, a framework, a test runner or a
build command. Those are discovered by `/quorum-init` and live in
`profile.yml`; a rule that names one has confused a project's content with the
process's structure, and stops being true the moment the process is reused.

Where a stage needs a stack fact it resolves `{{profile.*}}` or `{{role:*}}`.
Null resolves to "skip this concern", announced at the gate.

## Mode routing

| Stage | Agent |
|---|---|
| Triage | `quorum-triage` |
| PRD | `quorum-prd` (always human-interactive) |
| Ticket analysis | `quorum-ticket-analyzer` |
| Requirements / architecture / design / tasks | `quorum-spec`, `quorum-architecture`, `quorum-design`, `quorum-tasks` |
| Scope audit, implementation audit | `quorum-audit` |
| Implementation | `quorum-orchestrator` |
| Delivery | `quorum-delivery` |

## AI assets

Process definitions ship with the plugin and are versioned there. What the
consumer repo commits is what governs *this* project and what records *this*
work: the constitution, the profile, specs, runs and the memory bank.

A repo-local copy of a plugin default that nobody edited is a file that goes
stale silently, so nothing is copied at install except the constitution
template.
