# Implementation audit — panel-detection-cases — iteration 2

**Verdict: VERIFIED** · panel: cpd · grok-4.6 · gpt-5.6-luna · kimi-k3

## 1. Gate results

`check.py` exit 0 (10 checks) · `e2e.py` exit 0 (43/43) · `claude plugin
validate .` exit 0. Exit codes from the commands, not a pipeline.

## 2. Requirement traceability

| requirement | evidence | status |
|---|---|---|
| AC1 fourth cause named distinctly | `quorum-panel` "panel configured but unreachable" | PASS |
| AC2 fix is auth or tier, never "configure a panel" | the outcome table's fix column | PASS |
| AC3 assertion pinned, watched failing | 6 e2e assertions, each answering a named finding | PASS |

## 3. What is correct

The scope audit rejected the change as proposed, not as incomplete. All three
critics said catalogue presence is not credentialed reachability: a seat can be
listed and unauthorised, so a catalogue lookup would report a reachable panel
that cannot run a round.

The revision delegates to the engine's existing checks rather than
reimplementing its diagnostics. That closed three findings at once — it
measures credentialed reachability (`provider:<model>` dispatches), it keeps
the typo/gates/auth distinction the engine already draws, and it cannot drift
from a diagnostic it does not duplicate.

Two indeterminate outcomes were added, both from findings raised here: a
diagnostic that did not run, and a diagnostic whose checks were renamed. Grok's
round-2 major is the sharper one — this skill reads checks by name with no
contract guaranteeing those names, so a rename must fall back to "could not
determine" and never to "no panel configured", which is the exact wrong answer
this probe exists to stop producing.

## 4. Ambiguities

Per-seat aggregation is stated (report the reachable count, name the
unreachable seats) but no rule says how many reachable seats make a runnable
panel. Left to the caller, which already decides whether to proceed.

## 5. Risks

The name coupling is real and now explicit rather than silent. An engine rename
degrades this to "could not determine" — the panel still runs, degraded and
labelled, instead of reporting a false cause.

## 6. Blockers fired

None. Reason the set is empty: three gates green, three acceptance criteria
with PASS rows and evidence, nothing outside the declared file sets, no
constitution article touched.

One finding deliberately NOT taken into this unit and recorded instead:
runtime failure-to-label mapping — a mid-round auth failure can still record
"no panel configured". That is about what happens after a round starts; this
unit is about what the panel decides before it. Kimi held the scoping call.

## 7. Verdict

**VERIFIED**

## 8. Recommended transition

`IMPL_AUDIT -> VERIFIED`. Delivery is never automatic.
