# Implementation audit — blocked-on-correction — iteration 2

**Verdict: VERIFIED** · panel: cpd · seats: grok-4.6 · gpt-5.6-luna · kimi-k3

## 1. Gate results

| command | exit | result |
|---|---:|---|
| `python3 scripts/check.py` | 0 | 10 checks |
| `python3 scripts/e2e.py` | 0 | 37/37 |
| `claude plugin validate .` | 0 | passed |

Exit codes taken from the commands, not from a pipeline.

## 2. Requirement traceability

| requirement | evidence | status |
|---|---|---|
| AC1 not BLOCKED, no blocked_on | `.claude/specs/cpd-path-proven/status.yml` | PASS |
| AC2 original entry stands, answered | same file, both entries present | PASS |
| AC3 probe attached to the unblock | invocation, exit code, observation, two timestamps | PASS |
| AC4 BLOCKED requires a probe | `quorum-status` "BLOCKED requires a probe that ran" | PASS |
| AC5 rule binds every stage | `GLOBAL.md` "Preconditions are measured, never inferred" | PASS |
| AC6 sweep reports, never corrects | `check.py` precondition check; 3 defect shapes injected, 6 findings | PASS |
| AC7 assertions watched failing | 7 e2e assertions, each answering a named panel finding | PASS |

## 3. What is correct

Both scope-audit blockers are closed, and closed by deletion rather than
specification. The panel's argument was that any "cannot probe" terminal
recreates the error a level up — one that asserts the precondition is the
original defect, one that blocks is the same park renamed. So there is no such
state: no probe means the unit does not enter BLOCKED at all.

Grok's round-2 major is closed too. "Stays where it is" was a silent park; it
is now a same-state history entry marked OPEN QUESTION, visible in the one
place state is read.

GPT's round-2 major is closed by recording `exit_code` beside `observed`: a
probe that failed to run and a probe that observed absence are opposite
conclusions that look identical in a summary.

## 4. Ambiguities

Kimi withdrew the universal-reach finding on proportionality and named a
residue: only BLOCKED is mechanically gated, so a future state whose meaning is
also a precondition claim would need the same binding. Nothing today has that
shape. Recorded, not resolved.

## 5. Risks

The sweep reports and does not correct, so a record written before this rule
stays wrong until someone answers the report. That is deliberate — a sweep that
edits state can be wrong silently — but it means the report has to be read.

## 6. Blockers fired

None. Reason the set is empty: three gates green, seven acceptance criteria
with PASS rows and evidence, no change outside the declared file sets after the
amendment below, and no constitution article touched.

**One finding, non-blocking, against this unit's own bookkeeping.** Files were
changed outside the declared sets: `scripts/e2e.py` carried the assertions AC7
required, and no task declared where they would live. The work was in scope and
the file set was not. T2 and T3 were amended and the amendment is noted in
`tasks.md` rather than made silently. `.claude/profile.yml` also carries
uncommitted changes that predate this unit; named so they are not attributed
here.

## 7. Verdict

**VERIFIED**

## 8. Recommended transition

`IMPL_AUDIT -> VERIFIED`. Delivery is never automatic.
