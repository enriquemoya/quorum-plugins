---
argument-hint: "<slug>"
description: Stage 1a. Shapes the problem — problem, users, value, success, non-goals, the constitution articles it touches — by interviewing the operator. Always human-interactive; the transition to PRD_READY is the agent frontier and only a human crosses it.
---

# /quorum-prd

Writes `prd.md` for a unit on the spec path. Runs on `DRAFT_PRD`.

**Always human-interactive**, in both autonomy modes. This is the frontier: an
agent that writes the PRD defines the problem and the solution at once.

## Process

1. Delegate to the **quorum-prd** agent.
2. It reads `status.yml`, the constitution, and the memory bank for prior
   decisions on this surface.
3. It interviews the operator and writes what was answered — leaving visible
   gaps where nothing was.
4. **The operator approves.** `quorum-status` transitions to `PRD_READY`.

Then hand back to `/quorum-orchestrate`.

## What this command must not do

**Do not auto-approve**, under any autonomy mode. `PRD_READY` means a human
read the problem statement and agreed with it.

**Do not invent a success metric.** A `TBD` is an open question the scope audit
will fire on; an invented metric is a decision nobody made that every later
stage treats as settled.
