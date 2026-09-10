# Requirements — the tracker driver leaked into the agnostic layer

## Goals

Every file under `plugins/` outside the driver either reaches the tracker
through `{{role:tracker}}` / `{{profile.tracker.*}}`, or does not mention one.

## A correction this spec had to make about itself

An earlier draft called this an **Article 2** violation. It is not one, and a
critic was right to say so: Article 2 forbids naming an external product the
repository does not integrate with. Through its driver skill the repository DOES
integrate with this one. "The driver may name it, the agnostic layer may not" is
a design rule of this marketplace, and citing the constitution for it was
misattribution — borrowed authority for a rule that has to stand on its own.

It stands on its own: **a skill that describes steps it cannot perform is
wrong.** A repository with a different tracker, or none, reads instructions to
call tools that are not there. That is a correctness defect, not a governance
one, and it needs no article.

## In scope

All 35 files under `plugins/` that mention the product, excluding the driver
skill `quorum-jira-story` and its evals. One assertion set in `scripts/check.py`.
Three documentation files.

## Non-goals

- The driver skill and its evals.
- Writing drivers for other trackers.
- Making the plugins tracker-agnostic in BEHAVIOUR. A repository whose
  `roles.tracker` names a skill this marketplace does not ship still has no
  driver. What changes is that the skills stop promising otherwise.

## The classification rule, which is a question and not a judgement

An earlier draft said "delegate near the ticket path, delete far from it", and
three critics said that permits inconsistent treatment across 35 files. They are
right. The rule is now one question, answered per file and recorded:

> **Does this file's own job require a ticket?**

Yes → it delegates, and must reference the role. No → the mention is deleted.
Two files are exempt because they ARE the abstraction: the schema and the
example profile, whose job is to show what a tracker configuration looks like.

## The inventory — all 35 files, decided

Measured: 239 mentions, 58 tracker-tool calls, and **27 of 35 files carry no
reference to the role at all.**

**DELEGATE — the job requires a ticket (14)**

`agents/quorum-orchestrator.md` · `agents/quorum-qa-handoff-publisher.md` ·
`agents/quorum-ticket-image-analyzer.md` · `agents/quorum-ticket-validator.md` ·
`agents/quorum-ticket-analyzer.md` · `agents/quorum-prompt-builder.md` ·
`agents/quorum-pr-generator.md` · `commands/quorum-prompt-gen.md` ·
`commands/quorum-validate-ticket.md` · `commands/quorum-pr-template.md` ·
`skills/quorum-init/SKILL.md` · `quorum-tooling/skills/quorum-manual-qa-test-cases/SKILL.md` ·
`quorum-tooling/skills/quorum-create-branch/SKILL.md` ·
`quorum-workflows/skills/quorum-qa-test-plans/SKILL.md`

**DELETE — the job does not require a ticket (19)**

The four unit-test generators (`dotnet4x`, `dotnet9`, `jasmine`, `vitest`); the
nine-file `quorum-obsidian-vault` tree; `quorum-code-review/SKILL.md`;
`quorum-memory-bank/SKILL.md`; `quorum-agent-journal/SKILL.md`;
`agents/quorum-decision-documenter.md`; `agents/quorum-test-specialist.md`;
`quorum-workflows/.claude-plugin/plugin.json`.

Generating unit tests does not require a ticket system. Neither does writing an
ADR, syncing a memory bank, or scaffolding a vault.

**KEEP — the file is the abstraction (2)**

`PROFILE_SCHEMA.md` and `profile.example.yml`. An earlier draft put the schema
in the delete set, which contradicted this spec's own non-goal about examples —
a critic caught it. The schema's job is to show three trackers so a reader can
see the field resolves.

## Acceptance criteria

- AC1 *(guarantee)*: no file under `plugins/`, outside the driver, names a
  tracker-specific tool or resource. 58 occurrences today.
- AC2 *(guarantee)*: no file under `plugins/` hardcodes a ticket-key pattern.
  `{{profile.ticket_prefix}}` resolves it.
- AC3 *(guarantee)*: **co-occurrence.** Any file under `plugins/` outside the
  driver and the two abstraction files that mentions a tracker concept must
  also reference `{{role:tracker}}` or `{{profile.tracker.*}}`. 27 files fail
  this today.

  This is the criterion that makes the hard half checkable. An earlier draft
  left delegation as a description with no failing case, and three critics
  called that shipping the hard half unwatched — AC1 and AC2 together bound only
  ~45 of 239 occurrences, so the goal could fail with a green gate. Co-occurrence
  does not prove the delegation is CORRECT; it proves the file that talks about
  tickets also names the thing that fetches them, which is exactly what all 27
  fail.
- AC4 *(guarantee)*: every DELETE-set file mentions no tracker at all. The
  inventory above is the list, and it is checked against the sweep rather than
  re-derived.
- AC5 *(description)*: a delegating file says what happens when
  `roles.tracker` is null — for most, "skip the step and announce it", because a
  repository with no tracker is a supported configuration. Not asserted: whether
  the stated behaviour is the RIGHT one has no failing case a script produces.
- AC6 *(guarantee)*: `scripts/check.py` enforces AC1–AC4, **excludes itself**
  (it must contain the tool names it forbids) and excludes `.claude/specs/` and
  `.claude/runs/`, which name them to explain them. Watched failing.
- AC7 *(guarantee)*: `scripts/e2e.py` still passes at its current count.
- AC8 *(description)*: the three documentation files describe the role and name
  one driver as the one that ships. A reader should not have to discover that
  the marketplace has exactly one tracker driver by trying a second tracker.
