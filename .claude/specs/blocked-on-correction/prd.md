# PRD — a BLOCKED record that states a false precondition

## Problem

`cpd-path-proven` is recorded as BLOCKED on "a second model family reachable
from this machine". That was measured from environment variables and the absence
of a harness config, and it was wrong: seven free models across several families
were reachable the whole time, and a paid subscription has since made
thirty-four available.

A blocked record whose precondition is false is worse than no record. Its whole
purpose is telling a later reader what to fix; a wrong one sends them to fix
something that was never broken, and the unit stays parked for a reason that
stopped being true — or never was.

## Users

Whoever picks this repository up next and reads why a unit is parked.

## Value

The record says what is actually true, and `cpd-path-proven` becomes runnable
rather than appearing blocked.

## Success

- `cpd-path-proven` is no longer BLOCKED and its false `blocked_on` is gone.
- The history records the correction rather than hiding it — the original entry
  stands and a new one explains what was wrong.
- Whatever produced the wrong measurement is named, so the same mistake is
  visible rather than repeated.

## Non-goals

- Running `cpd-path-proven` itself. That is its own unit.

## Constitution articles touched

None. This corrects a record; it changes no behaviour and states no guarantee.
