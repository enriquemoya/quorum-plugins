---
argument-hint: "<slug|TICKET-KEY> [--scope \"<what you want built>\"]"
description: Stage 0 of the governed pipeline. Reads the ticket or the stated scope and decides how the work enters — the spec path when the problem is still open, the ticket path when it is bounded — and how deep the product stages go. Creates status.yml with origin and complexity.
---

# /quorum-triage

Creates a unit of work and decides its route. Everything after this reads the
two fields it writes.

```
/quorum-triage PROJ-1234
/quorum-triage invoice-export --scope "let accountants export a month as CSV"
```

## What it decides

| Field | Values | Governs |
|---|---|---|
| `origin` | `spec` \| `ticket` | which upstream stages run |
| `complexity` | `simple` \| `medium` \| `complex` | which of them are skipped |

The full criteria live in `agents/quorum-triage.md`. In short: **origin turns
on whether the problem statement is settled**, not on size; **complexity turns
on how many places must agree**, not on diff length.

## Process

1. Delegate to the **quorum-triage** agent.
2. It reads the source — the ticket through `{{role:tracker}}`, or the
   `--scope` text — plus `profile.stack.components` and any overlapping unit
   already in flight.
3. It proposes `origin` and `complexity` **with the evidence for each**, and
   names the stages that will run and the ones that will be skipped.
4. **A human approves the route.** This gate holds in both autonomy modes: the
   route decides how much scrutiny the work receives, and an agent choosing its
   own scrutiny is not a check.
5. On approval, `quorum-status` creates `.claude/specs/<slug>/status.yml` and
   transitions to `DRAFT_PRD` (spec) or `ANALYZING` (ticket).

Then hand back to `/quorum-orchestrate`.

## Preconditions

- A constitution exists at `{{profile.governance.constitution}}`. If not, say
  so and route to `/quorum-init` — an audit with no articles cannot check
  whether the work violates anything this project refuses to do.
- The slug is free. An overlapping in-flight unit becomes `depends_on` or a
  supersession, and both are a human's call.

## What this command must not do

**Do not draft anything.** Triage classifies. The PRD, the analysis and the
task list belong to their own stages.

**Do not choose `ticket` to save stages.** Being overruled by the scope audit
costs a full audit round — more than the stages the shortcut skipped. When
genuinely unsure, take the deeper path and say why; the spec path compresses by
complexity, a wrong ticket path has to be redone.

**Do not classify from a title.** Read the source. A ticket with no body is not
a bounded change; it is an unbounded one that happens to be short.
