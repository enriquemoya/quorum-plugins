# PRD — a round-1 dispatch that loses a seat still exits 0

## Problem

`quorum cpd-run` dispatched three critics; one recorded `dispatch_failure` after
timing out. The command **exited 0**.

The engine did the right thing with the seat — it labelled the failure rather
than counting it as a vote, and `cpd-conclude` later refused to render a verdict
until the key was retired. So nothing unsafe happens. What is missing is the
signal: an unattended run reading only the exit code sees success and moves on,
and discovers the short panel one stage later, if at all.

This matters more now than it did. A seat whose evidence could not be read
forfeits its token as of this release, so the difference between a full panel
and a degraded one is load-bearing at the moment of dispatch, not only at
conclusion.

## Value

An unattended run learns at dispatch that its panel is short.

## Success

- A round-1 dispatch that records any `dispatch_failure` exits non-zero, with
  the failed seats named on stderr.
- The exit code is distinguishable from the incomplete-debate refusal, which
  already exits 2 and means something different.
- Idempotent fill still works: re-running to fill only the missing seat is the
  documented remedy and must keep returning success when it completes the panel.

## Non-goals

- Retrying automatically. The engine deliberately does not, and the reason —
  a failure whose cause is unknown should not be repeated silently — still
  holds.

## Where this was seen

Observed twice in one session: once when a seat timed out with no shell-level
cap applied, and once after the cap was installed and the seat timed out anyway.
Recorded then only in a commit message.
