---
argument-hint: "<slug>"
description: Stage 2 of the governed pipeline. Produces requirements.md — goals, scope, non-goals, constraints and acceptance criteria with stable ids. Invoked by /quorum-orchestrate; reads the profile for every stack fact.
---

# /quorum-spec

Produces `requirements.md`. Runs on PRD_READY or ANALYZING.

## Process

1. Delegate to the **quorum-spec** agent.
2. It reads the upstream artifacts this unit actually has — `status.yml`
   records which stages `complexity` skipped, so a skipped stage is not a gap.
3. It reads the constitution and `profile.stack` for this system's own
   vocabulary. Nothing stack-specific is assumed; it is resolved.
4. It writes `requirements.md` and transitions to `DRAFTING_SPEC` through `quorum-status`.

Then hand back to `/quorum-orchestrate`.

## Gates

In `human` mode the artifact is presented and approved before the transition.
In `agent` mode the transition is taken and recorded — this stage is past the
`PRD_READY` frontier, and the scope audit is what checks the result.

## What this command must not do

**Do not run the next stage.** Each stage transitions and hands back; the
router decides what follows.

**Do not skip a stage on its own initiative.** Skips come from `complexity`,
were decided at triage, and are recorded — a skip invented here is one no audit
knows happened.
