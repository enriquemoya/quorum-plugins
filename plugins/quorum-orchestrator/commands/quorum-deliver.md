---
argument-hint: "<slug>"
description: Stage 9, the last one. Opens the PR with the accepted conditions in its body, posts the QA handoff, updates the tracker. Runs only on a VERIFIED-family verdict and never automatically — delivery acts outward.
---

# /quorum-deliver

Runs on `VERIFIED` or `VERIFIED_WITH_CONDITIONS`. Refuses any other state.

**Never automatic.** Delivery is on the never-automatic list in both autonomy
modes: a PR, a tracker comment and a merge are visible to other people and
cannot be quietly undone.

## Process

1. Delegate to the **quorum-delivery** agent.
2. It checks the verdict, the gate that produced it, and `last_audit.panel` —
   a `single-provider` verdict needs an explicit human approval to deliver on.
3. Transition to `DELIVERING`.
4. PR body (with the accepted conditions), QA handoff, ticket link through
   `{{ticket_url}}`, push, open, update the tracker.
5. `MERGED` is written **after the merge happens**, not when the PR opens.

## What this command must not do

**Do not merge.** The merge click is a human's.

**Do not write `MERGED` on an open PR.** A state that runs ahead of reality is
worse than no state — the queue reads it, and `depends_on` is hard.

**Do not drop the accepted conditions.** They are the difference between "this
passed" and "this passed given these caveats".
