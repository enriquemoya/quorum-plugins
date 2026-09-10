# Requirements — a seat whose evidence could not be read stops voting

## Goals

Make the debate act on what the severity parser already reports, so a reply
whose findings could not be read stops contributing verdict credit.

## In scope

- `quorum_core/cpd_audit.py` — `_debate_state`, `build_cpd_verdict`,
  `_compute_decision`.
- Tests in both directions.

`_debate_state` is named because a critic asked whether the parse state reaches
the decision and it was worth checking rather than assuming. It half does:
`severity_parse` IS persisted on the record, but `_debate_state` returns
`latest_round2` typed `dict[str, str]`, session to verdict string, and discards
everything else. The record-creation site needs no change; that function's
return shape does.

**Verified on both rounds, because the first check was on the wrong one.** The
premise was confirmed against a round-1 record; a critic pointed out that the
mechanism consumes round-2 records, and that schema uniformity across rounds was
asserted rather than read — the same class of unverified premise that same round
had just corrected, one read away from closed. Read: a round-2 record is a
superset of a round-1 record, adding `resumed_from` and `round1_decision_id`
and carrying `severity_parse` unchanged.

**Consumers of `_debate_state`: exactly two**, `debate_complete` and
`build_cpd_verdict`, both in `cpd_audit.py`. No third call site inherits the
signature change.

## Non-goals

- `parse_severity_block`. Its window rule is deliberate and four proposed
  changes to it were refused by a panel. **It is not wrong.** Its own docstring
  says of a contradictory block: "the verdict token stands, disclosure is the
  caller's job." The caller never did it. That is the whole defect.
- Making the parser guess.
- The appended contract, which already forbids fencing. That shipped separately
  and reduces incidence; it does not change semantics and the two must not be
  confused.

## The four parse states, and which are evidence

`SeverityParse` is a closed vocabulary and the distinction the fix needs is
already in it:

| State | Meaning | Evidence? |
|---|---|---|
| `ok` | records collected | yes |
| `none_declared` | exactly one sentinel — affirmatively zero | yes |
| `malformed` | a mix, or several sentinels — contradictory | **no** |
| `no_records` | empty window, or no verdict anchor at all | **no** |

`no_records` is not the innocent state it sounds like. The response contract
requires a terminal block, so a reply with none is non-compliant — and a fenced
block produces exactly this, because the closing fence terminates the window.

## Acceptance criteria

- AC1 *(guarantee)*: a seat whose `severity_parse` is `malformed` or
  `no_records` does not contribute its verdict token to the decision. The seat
  **remains a member of the panel and remains in the denominator** — only the
  token is withheld. Three critics raised this independently: "excluded from the
  verdict list" satisfies exclusion and escalation while violating never-shrink,
  because exclusion says nothing about the count.
- AC2 *(guarantee)*: such a debate **always escalates** — including when the
  remaining seats would produce `fail`. An earlier draft said only "never
  passes". A debate that fails anyway is not one where an unread seat is
  harmless: whoever reads the verdict is entitled to know the panel was not
  fully read, whichever way it came out.
- AC1b *(guarantee)*: the withheld token **stays on the audit record**, marked
  forfeited. Only vote aggregation skips it. This is the distinction a critic
  drew and it is not cosmetic: "no token recorded" is the `under_invoked` /
  `IncompleteDebateError` path, where no verdict is emitted at all and the panel
  reads as incomplete. "Withheld token" is the `dispatch_failure` analogue — a
  verdict IS emitted, the decision is `escalate`, the seat stays in the
  denominator and the literal token stays readable. Blanking the field, or
  omitting the record from what `_compute_decision` receives, re-implements
  exclusion and makes the denominator commitment cosmetic.
- AC2b *(guarantee)*: the panel size and the required-session count are
  unchanged across a debate containing an unreadable seat, asserted directly and
  **verified against a deliberately broken implementation that drops the seat
  while still escalating** — which is the shape that would otherwise pass every
  other criterion here.
- AC3 *(guarantee)*: the verdict names those seats, following the existing
  `repair_retired_token_free` disclosure precedent rather than inventing a
  second shape. A degraded panel is never silent.
- AC4 *(guarantee)*: the quoted-example semantics survive — an illustrative
  fenced block is still not counted as findings. The parser is untouched and a
  test pins that.
- AC5 *(guarantee)*: the dropped-finding direction is watched failing against
  the unfixed tree. `malformed` gets its own failing test, distinct from the
  fenced `no_records` case; and `none_declared` is pinned as **still voting**,
  watched failing too — otherwise the fix disenfranchises every critic who
  correctly declared zero findings, which is the largest population of compliant
  replies.
- AC5b *(regression pin, NOT Article 3 evidence)*: the inflated-example
  direction. This cannot fail on the unfixed tree — it pins behaviour that
  already exists, so claiming it was watched failing there is impossible, as a
  critic pointed out. It is watched failing against a tree where the fix has
  been made deliberately over-broad so that fenced blocks DO count. That is a
  real failing observation of the right thing.
- AC6 *(guarantee)*: the full suite passes. A change to how seats are counted
  touches the most load-bearing semantics in the engine, so a green suite is
  the minimum and its count is stated, not summed.

## Rollout consequence, intended

Replies with no terminal block at all begin forfeiting their token. That is
enforcement of a contract that has always required one, not a side effect, and
it is not a reason to split `no_records` into a lenient sub-case.

The no-verdict-anchor sub-case of `no_records` most likely already escalates
through the unrecognised-token path. What is newly handled is the sub-case with
a verdict anchor and an unreadable window — a fenced block being the instance
that produced this unit.

## Risk this spec accepts

Debates already concluded were counted under the old rule. This changes future
counting only.

**Declining to re-check them is a decision, not a limitation.** The records
persist `severity_parse`, so a sweep of what the old rule counted is possible.
An earlier draft phrased this as though detection were unavailable, which
conflated choosing not to look with being unable to.

And a critic was right that the distinction only pays if something follows from
it: declining to RE-OPEN concluded debates is defensible, declining a read-only
count is not. So a follow-up unit runs the sweep — it re-opens nothing, changes
no verdict, and turns "this does not claim they were correct" from an
unfalsifiable hedge into a number.
