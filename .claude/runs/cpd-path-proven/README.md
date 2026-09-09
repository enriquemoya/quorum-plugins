# Evidence — the cross-provider path, as run

Three scope audits, each three model families, `cpd-run` → per-critic
`cpd-resume` → `cpd-conclude`. Kept because the claims in `quorum-panel`'s CPD
path are corrections against these runs, and a reader should be able to check
them without re-spending the model calls.

## Anchoring

Every claim below names the engine state it was taken under. A transcript is
evidence for the engine that produced it and for no other, and two of these
runs straddle a change to the contract the dispatch layer appends.

| Run | Engine state | What it is evidence for |
|---|---|---|
| `u2-scope-heavy` | before the appended contract forbade fencing | a seat whose findings were fenced, discarded, and still voted |
| `u3-scope` | after | the contract followed in all three replies |
| `u4-scope` | after | this unit's own scope audit, `escalate` |

The refusal measurement is separate and was re-taken deliberately: running
`cpd-conclude` against a debate missing round 2, on the engine as it stands
now, exits `2`, prints nothing, and names the missing pairings on stderr. The
earlier observation of the same behaviour predates the contract change, so it
was not inherited.

## What is not here

The two free-tier probes and the fence-parser debate. They established that the
path runs at all and that a formatting difference between families surfaces a
defect neither of the others showed; neither claim is load-bearing for the
skill text, and keeping every transcript makes the ones that matter harder to
find.
