# Panel tiers — the same brief, three times

## What was run

One brief, dispatched unchanged to three panel tiers. Three model families per
tier, round 1 only for the comparison. The brief was a real scope audit, not a
synthetic prompt.

| Tier | Contract followed | Findings | Analysis |
|---|---|---|---|
| free | 1 of 3 replies | 1 | 6,210 chars |
| medium | 2 of 3 | 8 | 8,970 chars |
| heavy | 2 of 3, then **3 of 3** | 8 → 9 | 11,788 chars |

"Contract followed" means the reply ended with an unfenced terminal findings
block, which is what the dispatch layer asks for and what the severity floor
needs in order to fire.

## The conclusion that matters, and it is not the obvious one

**Heavier models did not follow the contract better. They found what the lighter
ones did not.**

The 2-of-3 figure is identical between medium and heavy. What changed was the
content: the heavy panel produced a finding neither other tier reached, and it
reached it because one of its families formats replies differently — the fenced
block that exposed the verdict-credit defect appeared there and nowhere else.

The 2 → 3 improvement in the heavy row came from a change to the BRIEF, not the
tier: the severity contract was embedded in the brief in addition to being
appended by the dispatch layer. **One observation on one panel. Not a rate, and
not evidence that embedding causes compliance.**

## What this does not measure

Cost, latency, and whether a finding was correct. The finding counts are counts,
not quality: the free tier's single finding was not wrong, it was one thing seen
where others saw eight.

## The operational finding, recorded because it cost time

One seat timed out at 600s three times on a 189-line brief and returned on
shorter ones in the same session. n is one and no causal claim is made. The
mitigation is cheap — keep briefs under roughly 120 lines and move long context
into annexes — and if a short brief also times out, the cause is something else
and worth investigating rather than working around.

A second measurement from the same incident: the timeout was not being enforced
at all. The dispatch script warns when no `timeout` binary is on PATH and the
600s cap silently does not apply. Installing GNU coreutils made the cap real,
and the seat still timed out — so the missing binary was a second defect, not
the explanation for the first.
