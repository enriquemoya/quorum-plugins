# Smoke — resolving a bundled file against an install

## What was run

A fixture reproducing both plugin layouts under one root, because they can
coexist and that is the only condition under which the ambiguity rule matters:

```
<root>/marketplaces/quorum-plugins/plugins/quorum-orchestrator/agents/…   (current)
<root>/cache/quorum-plugins/quorum-orchestrator/2.0.0/agents/…            (previous)
```

## Result

| Pattern | Matches | Reading |
|---|---|---|
| `*/quorum-orchestrator/agents/<file>` | 1 | the previous layout is **invisible** — a version segment sits between the plugin and `agents` |
| `*/quorum-orchestrator/*agents/<file>` | 2 | both found; the resolution stops and reports both |

No match, and a nonexistent plugin name: 0 matches, which is the STOP branch.

## What this changed

The narrow pattern was about to be written into six files. It resolves
confidently to one file while a second candidate sits unseen under the same
root — a smaller copy of the defect this unit exists to fix. The wide pattern
is required, and it is what the original document already used: **only the root
was ever wrong.** A fix that narrowed the pattern while correcting the root
would have traded a loud failure for a quiet one.

## Against a real install

The marketplace was then installed and both instructions run against it. The
installed copy is the published one, which still carries the defect, so the two
could be compared on the same tree:

| Instruction | Glob root | Matches |
|---|---|---|
| as published | `~/.claude/plugins/cache` | **0, and no error** — the root does not exist |
| as corrected | `~/.claude/plugins` | 1 |

Three resolutions were exercised, one per distinct target, all returning exactly
one match at `marketplaces/quorum-plugins/plugins/<plugin>/…`:

```
quorum-orchestrator  → agents/quorum-orchestrator.md
quorum-memory-bank   → scripts/memory-bank-to-obsidian.ps1
quorum-obsidian-vault → scripts/scaffold_vault.ps1
```

The zero-match row is the whole point. A Glob rooted at a directory that does
not exist is not an error, so every one of these lookups had been failing
silently for as long as the instruction existed, and an agent following it would
report that it could not find its operating manual rather than that the
instruction was wrong.

## What this still does not establish

The multiple-match branch has been exercised only against a fixture: a single
install has one layout. It stays in the text because the two layouts *can*
coexist, and because a resolution that picks silently between two candidates is
the failure this unit exists to prevent — but nobody has watched it fire on a
real machine.
