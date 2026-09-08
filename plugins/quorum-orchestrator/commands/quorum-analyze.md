---
argument-hint: "<slug>"
description: Stage 1b. The ticket path's counterpart to the PRD — reads the ticket, records what it asks, which surfaces it touches, and the acceptance criteria it already carries. Says so plainly when it carries none.
---

# /quorum-analyze

Produces `analysis.md` for a ticket-path unit. Runs on `ANALYZING`.

## Process

1. Delegate to the **quorum-ticket-analyzer** agent.
2. It fetches the ticket through `{{role:tracker}}` and records what it asks,
   the surfaces it touches resolved against `profile.stack.components`, and
   **the acceptance criteria the ticket already carries**.
3. It writes `analysis.md` and transitions to `DRAFTING_TASKS`.

## When the ticket carries no criteria

Say so in `analysis.md` and do not invent any.

Triage chose this path because the problem looked settled. A ticket with
nothing measurable means it was not, and the scope audit will emit a promotion
proposal routing it to `/quorum-prd`. Manufacturing criteria here hides that,
and the work then gets built against requirements nobody agreed to.

## What this command must not do

**Do not write requirements.** `/quorum-spec` gives the criteria their ids.
This stage records what the ticket says.

**Do not design.** A ticket that names an implementation is still a problem
statement; the stages after this decide whether that implementation is right.
