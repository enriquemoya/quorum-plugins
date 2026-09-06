---
id: {{ID}}
title: {{TITLE}}
kind: initiative
subtype: {{SUBTYPE}}
no-ticket: true
status: {{STATUS}}
owner: {{OWNER}}
started: {{DATE}}
target:
created: {{DATE}}
updated: {{DATE}}
tags:
  - initiative
  - {{ID}}
---

# {{TITLE}}

> [!summary] At a glance
> <!-- One paragraph: current state of the whole initiative. Keep it in sync with the status.md Snapshot. -->

This is the **home / map of content** for the {{TITLE}} initiative — a long-running, ticketless effort. Open [[status]] for live progress & handoff, and [[lessons]] for the lessons-learned register.

## Goal / Definition of Done

<!-- The north star. What does "done" look like? This section rarely changes. -->

## Phase & Progress

<!-- For a migration: migrated-vs-remaining checklist (or embed the migration dashboard). For tooling: workstream checklist. -->
- [ ]

## Architecture & Approach

<!-- High-level approach. Record each significant, hard-to-reverse choice as a MADR note under decisions/ and link it here. -->

## Decision Log

Immutable MADR notes — one per significant choice — live in `decisions/`. Index: `decisions/_index.md`. New decisions supersede old ones via reciprocal `supersedes` / `superseded-by` wikilinks (never edit an accepted decision).

## Source / References

<!-- Free-form, optional: PRs, Confluence, design docs, dashboards. Link out; don't copy. -->
-

## Spin-off Tickets

<!-- tickets carved out of this initiative; reciprocal [[PROJ-XXXXX]] links. -->
-

## Map

- Live status & handoff: [[status]]
- Lessons learned: [[lessons]]
- Decisions: `decisions/_index.md`
<!-- Migrations also: ![[migration/dashboard]] -->
