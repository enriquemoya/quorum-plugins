# PRD — the tracker driver leaked into the agnostic layer

## Problem

`roles.tracker` plus `tracker.browse_url_template` model any tracker or none,
and `/quorum-init` fills them from the repository. The abstraction is sound and
the schema shows three different trackers as examples.

Thirty-five files under `plugins/` ignore it. They do not name a product in an
illustrative example, which Article 1 explicitly permits — they call one
directly as procedure: fetch the ticket with a named MCP tool, read a named
cloud resource, extract keys with a hardcoded prefix pattern. A repository whose
tracker is anything else, or nothing, gets a skill that describes steps it
cannot perform.

The concentration says where the leak came from: one agent (32 occurrences),
one QA skill (23), one publisher agent (21). These are the files closest to the
ticket path, and the coupling spread outward from them into skills that have no
business knowing what a tracker is — four unit-test generators name it, and
generating unit tests does not require a ticket system.

## What is NOT the problem

- `quorum-jira-story` and its evals. That skill IS the driver for one tracker;
  naming the product it drives is what a driver does. Article 2 forbids naming
  a product the repository does not integrate with, and through this skill it
  does.
- The schema's examples. Article 1's own text permits naming a product in an
  example that illustrates resolution, and `browse_url_template` shows three.

## Value

A repository with a different tracker, or none, can use these skills. Today
they read as instructions and behave as assumptions.

## Success

- No file under `plugins/` outside the driver calls a tracker-specific tool or
  resource by name.
- Where a step needs the tracker, it delegates to `{{role:tracker}}` and states
  what happens when that role is null — which for most of these is "skip the
  step and say so", not "fail".
- The four unit-test generators stop mentioning a tracker at all.
- An assertion fails on a tracker-specific tool name outside the driver.

## Non-goals

- Writing drivers for other trackers.
- The ticket path itself. Triage fetches tickets and that is correct; what is
  wrong is HOW, not THAT.

## Constitution articles touched

- **Article 1** is not violated: nothing under `governance/` names it. That was
  checked and is worth stating, because "41 files name a product" sounds like
  an Article 1 finding and is not one.
- **Article 2** is the live one, in its narrow reading: a driver's name leaking
  into the layer that must work with any tracker or none.

## Scale, measured

| Layer | Files | Occurrences | Action |
|---|---|---|---|
| agnostic (`plugins/`, not the driver) | 35 | 203 | the sweep |
| the driver (`quorum-jira-story`) | 2 | 10 | keep |
| documentation | 3 | 16 | rewrite as role + one example |
| `governance/` | 0 | 0 | — |
| records (`.claude/specs`, `.claude/runs`) | — | — | exempt |
