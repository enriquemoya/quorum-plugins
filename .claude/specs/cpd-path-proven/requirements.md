# Requirements — the cross-provider path, run and corrected

## Goals

Replace three statements in `quorum-panel`'s CPD path with what the runs
measured, each anchored to the engine state that produced it.

## In scope

- The CPD path section of `plugins/quorum-orchestrator/skills/quorum-panel/SKILL.md`.
- Evidence under `.claude/runs/cpd-path-proven/`.

## Non-goals

- Making the engine a dependency. The degraded path exists so the pipeline
  works without it and that must stay true.
- Automating a CPD run in CI. It costs model calls across providers.
- Changing the engine.
- **Seat counting.** Removed from this unit by its own scope audit: a seat that
  recorded no verdict token is the deferred `verdict-credit-on-ambiguity`
  defect under another name, and it collides there with never-shrink and
  `debate_complete`. Whichever unit inherits it also inherits the condition
  that its reading rule be written mode-portably, or the degraded path loses
  the check.

## What the runs established

Six debates ran end to end — three model families each, `cpd-run` →
per-critic `cpd-resume` → `cpd-conclude`. Three are kept as evidence; the
others established only that the path runs.

Two of them straddle a change to the contract the dispatch layer appends, so
each claim below names the engine state it was taken under. A transcript is
evidence for the engine that produced it and no other.

## Acceptance criteria

The deliverable is the correction. These name what the corrected text must
say, not verifications that were already satisfied when the unit opened.

- AC1: the incomplete-debate refusal appears as an observation — exit code,
  empty stdout, the stderr message — taken on the engine as it stands, not
  inherited from a transcript that predates the contract change.
- AC2: the skill says the dispatch layer appends the severity contract and the
  author embeds it too, with the 2-of-3 → 3-of-3 figure stated as a single
  observation on one panel and explicitly not as a rate or a cause.
- AC3: the skill forbids fencing the terminal block, and says what a fenced
  block costs — findings discarded, verdict still counted.
- AC4: the evidence is committed where a reader meets the claim, with each run
  anchored to its engine state.
