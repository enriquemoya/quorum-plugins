# PRD — the digest rule and the digest data disagree

## Problem

`same-evidence-thrice` was corrected this session: the digest is appended to
each history entry, and it is a digest of finding REFERENCES rather than a path
to where the evidence lives. The documents say so and an assertion pins that
they say so.

**Every `evidence_digest` in this repository is a path.** Five units carry one
and all five hold `.claude/runs/<slug>/<debate>`. No history entry carries one at
all. So the rule the documents now state and the data every unit actually
records are two different things, and the assertion cannot tell — it checks the
prose against itself.

That is the same shape as the defect it replaced. The old rule read as a bound
and bounded nothing because the value was overwritten; the new rule reads as
correct and matches nothing because the values are paths.

## Value

The bound can fire on this repository's own units, not only in principle.

## Success

- A digest is computed from the sorted finding references a verdict cited.
- Each history entry carries the digest of the verdict that produced it.
- An assertion reads the DATA, not the prose: a unit whose history contains an
  audit entry must carry a digest that is not a path.
- Existing records are not backfilled. The debates ran; their digests were never
  computed, and inventing them would be fabrication.

## Non-goals

- Changing the cap of 3 iterations per unit. It was reached once this session,
  by a unit that converged on that iteration, and nothing suggests it is
  mis-sized.

## Constitution articles touched

- **Article 3.** The assertion added this session pins that the documents state
  the rule. It does not pin that anything obeys it.
