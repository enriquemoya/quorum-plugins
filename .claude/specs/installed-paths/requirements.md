# Requirements — resolve bundled files without guessing the install layout

## Goals

Replace every hardcoded plugin-install path with a resolution whose every
branch is falsifiable, and assert the literal cannot return.

## In scope

Six runtime files that must locate a bundled file at run time, two
documentation files that describe the layout, and one assertion in
`scripts/check.py`. The two groups get different treatment and are not
"eight files doing the same thing" — an earlier draft said that and was wrong:
`INSTALL.md` and `docs/plugin-authoring.md` describe, they do not resolve.

## Non-goals

- The Obsidian adapter, the memory bank and the journal themselves. Only how
  their files are located.

## What is known, and how well

| Fact | Evidence | Confidence |
|---|---|---|
| Installed plugins live under `plugins/marketplaces/<mkt>/plugins/<plugin>/` | observed in an install | direct |
| No version or hash segment in that path | observed | direct |
| `~/.claude/plugins` contains both the old and the current shapes | observed + secondhand | direct for current only |
| `${CLAUDE_PLUGIN_ROOT}` is substituted in hook commands and MCP server config | platform binary strings | direct |
| It is substituted in the body of a command, agent or skill | — | **no evidence** |
| The `cache/<mkt>/<plugin>/<hash>/` shape once existed | another marketplace's docs | secondhand |

## Two rejected approaches, and why they are recorded

**Correcting `cache/` to `marketplaces/`.** Rejected: the layout changed once
already, silently, and nothing here noticed for as long as it has existed.

**Resolving via `echo "$CLAUDE_PLUGIN_ROOT"` with a Glob fallback.** Rejected
for a sharper reason: in these layers an empty `echo` is indistinguishable from
the variable never being injected, so the primary branch cannot be falsified
and the fallback fires silently. That is the original defect wearing a new
shape — a mechanism that looks authoritative and fails without saying so.

`~/.claude/plugins` is therefore the **observed current** search root, not a
contract. It survives the rename this unit was created by; it does not survive
the platform moving the plugin root, and nothing here can promise that it will.

## The resolution, for the six runtime files

```
1. Glob `**/<plugin-name>/<relative path>` rooted at ~/.claude/plugins.
2. Exactly one match: verify the file exists, then use it.
3. No match: STOP and report. Never guess a path.
4. More than one match — the same plugin under two marketplaces, or a stale
   directory from the previous layout — STOP and report every match.
   Choosing one silently is how the wrong file gets read confidently.
```

Step 4 is not defensive padding: the old and current layouts can coexist under
the same root, which is precisely when two matches appear.

The Glob is rooted at the **parent** (`~/.claude/plugins`). Naming a child of
it — `cache`, `marketplaces`, a marketplace name, a version — is what AC1
forbids.

## Acceptance criteria

- AC1 *(guarantee)*: no tracked file names a **child** of `~/.claude/plugins`
  in a path literal, in any separator style. The parent is permitted as a Glob
  root — that distinction is the whole check, and stating it wrong fails either
  every runtime file or none. Two documentation files are allowlisted, and the
  allowance is restricted to the observed-layout pattern so the expelled
  `cache/` shape cannot return there either. `check.py` excludes itself by
  name, since it must contain the pattern it forbids.
- AC2 *(guarantee)*: each of the six runtime files carries all four steps,
  including both the no-match and the multiple-match STOP. The **text** is what
  is asserted.
- AC3 *(description)*: `INSTALL.md` and `docs/plugin-authoring.md` state the
  layout as observed, and name `~/.claude/plugins` as an observed root rather
  than a promise. Not asserted: separating "observed" from "contracted"
  statically needs a marker convention, and inventing one to satisfy Article 3
  would be ceremony.
- AC4 *(guarantee)*: `scripts/check.py` fails on any child literal outside the
  allowlist, watched failing against a reintroduced one, with the injected
  defect and the resulting count in the commit message.
- AC5 *(description, evidence required)*: the Glob is exercised once against a
  real install and the transcript recorded under `.claude/runs/installed-paths/`.
  **No green suite is evidence that resolution works** — the suites check the
  text, and the text is what was wrong.

## What this unit does not close

Whether `${CLAUDE_PLUGIN_ROOT}` reaches a command's, agent's or skill's own
tool calls is unverified and is now out of scope rather than assumed either
way. If someone observes it working in one of those layers, it becomes a
faster first branch — but only after being watched, and only with an
existence check behind it, because a non-empty value from a foreign plugin's
root would otherwise yield a confident wrong path.

Shell portability is also out of scope by construction: the resolution is a
Glob, not a shell command, so it carries no bash assumption. The earlier
`echo`-based draft did, and that is one more reason it is not the design.
