# PRD — the marketplace does not work installed

## Problem

Eight tracked files tell an agent to find a bundled file under
`~/.claude/plugins/cache/`. That directory does not exist. Installed plugins
live under `~/.claude/plugins/marketplaces/<marketplace>/plugins/<plugin>/`,
with no version or hash segment.

The most consequential instance is `/quorum-implement`, which explains at
length how to Glob for its own orchestrator agent — the file it calls "your
operating manual for the entire pipeline". Rooted at a directory that does not
exist, the Glob returns nothing and the read fails. The stage cannot locate its
own agent in a real installation.

This was found by inspecting an installed marketplace, which is the first time
anything in this repository has been checked against an install rather than
against a checkout.

## Why it was wrong

The path was not invented. Another marketplace's documentation describes the
same `plugins/cache/<marketplace>/<plugin>/<hash>/` shape, so that layout
existed and has since changed. That is the finding: a hardcoded path to
someone else's internal layout is correct until it silently is not, and nothing
here would have noticed.

## Value

The product is verified against the form it is delivered in, not only the form
it is developed in.

## Success

- No tracked file names a plugin-install directory it does not own.
- Where the platform documents a variable for this, it is used.
- Where it does not, the resolution is a search with a stated failure mode
  rather than a guessed literal.
- An assertion prevents the literal from coming back, watched failing first.

## Constitution articles touched

- **Article 3.** "Resolve the adapter" is stated as a working procedure in
  eight places with nothing checking that it resolves.

## Why this one is agent mode

The correction is mechanical and its failing case is a grep. The judgement —
which mechanism belongs in which layer — is in the spec, not the edit.
