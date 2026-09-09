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

## What this smoke does NOT establish

It ran against a fixture, not against this marketplace installed. Installing a
marketplace is a slash command, which an agent cannot invoke. The remaining
step is one real install plus one resolution, recorded here.

Until that exists, AC2 is text that has been exercised only in reproduction.
