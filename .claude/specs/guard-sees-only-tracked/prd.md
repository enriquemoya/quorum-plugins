# PRD — every guard is blind to a file that is not committed yet

## Problem

`scripts/check.py` enumerates files with `git ls-files`. All fourteen checks
inherit that: a file is outside every guard until it is committed.

This is not theoretical and it is not once. Twice in one session a check passed
at commit time and failed immediately after, because the files it should have
scanned were still untracked when it ran. A sibling repository shipped a
provenance guard with the same shape — it passed while untracked and had been
failing since the commit that added it.

The failure mode is specific and nasty: the guard is green exactly when a new
file is most likely to be wrong, and turns red only after the wrong thing is in
history.

## Value

A check that runs before a commit sees what the commit will contain.

## Success

- The scan covers tracked files plus staged and untracked ones, excluding what
  `.gitignore` excludes.
- A file that is deliberately ignored stays ignored — the fix must not start
  scanning build output or a scratch directory.
- Watched failing: a new, uncommitted file carrying a known-bad pattern is
  caught before it is committed.

## Non-goals

- `scripts/e2e.py`, which reads named files rather than enumerating.
- A pre-commit hook. The fix is what the scan looks at, not when it runs.

## Constitution articles touched

- **Article 3.** Fourteen guarantees rest on a scan whose blind spot has been
  observed twice and never closed.
