# PRD — the panel's detection misses the state it will meet most

## Problem

`quorum-panel` probes three causes of degradation: the engine is not installed,
this is not an engagement, no critic panel is configured. A real run hit a
fourth that none of them names — authenticated, engagement present, panel
configured, but the panel points at seats from a tier the credentials do not
cover.

`quorum doctor` diagnosed that state correctly and said so: seats violating the
harness gates, entries absent from the catalogue, and a pointer at
authentication. The panel skill has no such case, so it would report "no critic
panel configured" for a panel that is configured and unreachable — sending the
operator to write a config that already exists.

That state is not exotic. It is what every operator sees between installing the
engine and paying for a provider, which is the ordinary path.

## Users

Anyone whose panel is configured for a tier they have not authenticated, which
is the default state after `quorum init` and before a subscription.

## Value

The degradation reason matches what is actually wrong, and points at the fix
that will work.

## Success

- The detection recognises a configured-but-unreachable panel and reports it
  distinctly from an unconfigured one.
- The reported fix is authentication or a tier change, not writing a config.
- The evidence for the case is the doctor output that produced it.

## Non-goals

- Reimplementing what `quorum doctor` already does. The panel needs the case,
  not the diagnostic engine.

## Constitution articles touched

- **Article 3.** The detection's three distinguishable causes are stated as a
  guarantee, so a fourth needs an assertion.
