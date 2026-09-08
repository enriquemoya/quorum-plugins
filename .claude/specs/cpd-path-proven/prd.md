# PRD — exercise the cross-provider panel against a real engagement

## Problem

`quorum-panel` has two paths. The degraded one — same-provider subagents — has
been run and its behaviour observed. The cross-provider one has not: it was
written against the engine's CLI with every flag verified by `--help`, but no
round has ever been dispatched through it.

Verifying that a flag exists is not verifying that a sequence of calls produces
a verdict. Between them sit the debate id, the brief on disk, the per-critic
rebuttal directory, the round-2 resume, and `cpd-conclude`'s refusal to render
on an incomplete debate. Each is a contract this skill asserts and none has been
observed holding.

The asymmetry matters because the cross-provider path is the stronger one. The
weaker path is proven and the stronger one is assumed, which is the wrong way
round: a verdict that says `panel: cpd` currently carries less evidence than one
saying `panel: single-provider`.

## Users

Anyone running an audit in a repository where the engine is installed — which is
the configuration the pipeline recommends, and therefore the one most likely to
be in use when a verdict matters.

## Value

`panel: cpd` on a verdict comes to mean a path that has been run, rather than a
path that was written carefully.

## Success

- One real debate is dispatched through `cpd-run`, rebutted through
  `cpd-resume`, and concluded through `cpd-conclude`, in an engagement where the
  engine is installed.
- The incomplete-debate refusal is observed: a debate is concluded with a
  missing round 2 and the non-zero exit is recorded.
- Whatever the run contradicts in `quorum-panel`'s description is corrected, and
  what it confirms is left alone.

## Non-goals

- Making the engine a dependency. The degraded path exists precisely so the
  pipeline works without it, and that must stay true.
- Automating a CPD run in CI. It costs model calls against several providers.

## Constitution articles touched

- **Article 3.** The panel's refusals are guarantees; this is the check that has
  not been observed failing. Concluding an incomplete debate on purpose is how
  it gets observed.
