# Smoke — resolving a bundled file against an install

## The correction this file exists to record

An earlier version of this document reported that
`~/.claude/plugins/cache/` does not exist, and eight files plus both suites
were rewritten on that basis.

**The observation was taken on a machine where a marketplace had been
registered and no plugin installed.** Registering clones the marketplace to
`~/.claude/plugins/marketplaces/<mkt>/`; it does not install anything, and the
`cache/` tree is created by installation. The two steps look like one from the
outside — `/plugin marketplace add` reports success and the plugins appear in
the marketplace listing — and nothing distinguishes them until you look for a
directory that installation is what creates.

So the original instruction in these files was **right**: root at
`~/.claude/plugins/cache`, pattern with a middle `**` for the version segment,
example path `cache/<mkt>/<plugin>/<version>/`. All three correct. The rewrite
replaced a working instruction with one that fails.

## What the runtime actually does

`~/.claude/plugins/installed_plugins.json`, format version 2, after installing
four plugins from one marketplace:

```
quorum-orchestrator@quorum-plugins    → ~/.claude/plugins/cache/quorum-plugins/quorum-orchestrator/2.1.0
quorum-tooling@quorum-plugins         → ~/.claude/plugins/cache/quorum-plugins/quorum-tooling/2.1.0
quorum-workflows@quorum-plugins       → ~/.claude/plugins/cache/quorum-plugins/quorum-workflows/1.0.0
quorum-integration-kit@quorum-plugins → ~/.claude/plugins/cache/quorum-plugins/quorum-integration-kit/0.1.0
```

`installPath` is the live copy. The marketplace clone is a second copy of every
file, under the same parent, that is never loaded.

## Measured, on a real install

| Glob root | Matches for `**/quorum-orchestrator/**/agents/quorum-orchestrator.md` |
|---|---|
| `~/.claude/plugins/cache` | 1 — the installed copy |
| `~/.claude/plugins` (the parent) | **2** — installed copy plus marketplace clone |
| `~/.claude/plugins/cache`, before any plugin was installed | 0, and no error |

Row two is why the rewrite was wrong: rooting at the parent makes the ordinary
case ambiguous, so a resolution that stops on ambiguity stops on every machine.

Row three is why the rewrite happened: a Glob rooted at a directory that does
not yet exist returns nothing and raises nothing, so "not installed" and "wrong
path" are the same observation.

## The multiple-match branch, exercised

A critic pointed out this branch was recorded as unexercisable when a decoy
makes it trivial. Copying one plugin to a second marketplace directory:

```
3 matches:
  ~/.claude/plugins/marketplaces/quorum-plugins-decoy/plugins/quorum-orchestrator/agents/…
  ~/.claude/plugins/cache/quorum-plugins/quorum-orchestrator/2.1.0/agents/…
  ~/.claude/plugins/marketplaces/quorum-plugins/plugins/quorum-orchestrator/agents/…
```

The decoy was removed afterwards. That run is also what surfaced the cache
directory, so the finding that reshaped this unit came from taking a critic's
"you could just test it" literally.

## What resolution ships

Read `installPath` from the registry. Fall back to a Glob rooted at
`~/.claude/plugins/cache` when the entry is absent. Never the parent. Stop on
zero matches, and on several with no `installPath` to break the tie.

The registry is preferred over any path because it is the runtime's own record
rather than an inference about the runtime's directory layout — which is the
class of thing this unit has now been wrong about twice.
