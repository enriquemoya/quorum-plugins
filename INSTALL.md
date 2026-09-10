# Install

## Production install

```text
/plugin marketplace add https://github.com/enriquemoya/quorum-plugins.git
/plugin install quorum-tooling@quorum-plugins
/plugin install quorum-orchestrator@quorum-plugins
/plugin install quorum-workflows@quorum-plugins
/plugin install quorum-integration-kit@quorum-plugins
```

Install order matters in one place only: `quorum-orchestrator` declares a
dependency on `quorum-tooling`, so install tooling first.

Refresh later with:

```text
/plugin marketplace update quorum-plugins
```

## Verify

```text
/plugin list
```

You should see each installed plugin with its version. Then check that a
command resolves — type `/quorum-` and confirm the completions appear.

## Per-repo setup

Plugins are installed once per machine; **configuration is per repo.**

1. **`.claude/profile.yml`** — run **`/quorum-init`** in the repo. It reads the
   tree, works out the stack, test tooling, commands and layout from what is
   actually there, maps the components and the cross-cutting characteristics
   (entry points, datastores, CI, containers, generated code), shows you the
   evidence for each value it proposes, asks about the few things no file can
   answer, and writes the profile. It finishes by settling where the memory
   bank lives — in the repo, in the repo Obsidian-flavoured, or in an external
   vault — and taking its first step. Re-running it is safe: values you set by
   hand are kept.

   Writing it by hand is still supported — start from
   [`plugins/quorum-orchestrator/profile.example.yml`](plugins/quorum-orchestrator/profile.example.yml)
   and read the contract in
   [`plugins/quorum-orchestrator/PROFILE_SCHEMA.md`](plugins/quorum-orchestrator/PROFILE_SCHEMA.md).
   Discovery just spares you a pass through a schema you did not write.
2. **`integration-profile.yml`** at the repo root, if you use
   `quorum-integration-kit`. Contract:
   [`plugins/quorum-integration-kit/skills/quorum-new-integration/references/profile-schema.md`](plugins/quorum-integration-kit/skills/quorum-new-integration/references/profile-schema.md).
3. **`.gitignore`** — the orchestrator writes transient artifacts under
   `.claude/`. Add:

   ```gitignore
   .claude/pr-templates/
   .claude/prompts/
   .claude/transit/
   ```

A plugin that cannot find its profile refuses to run and tells you which file it
wanted. That is deliberate — see the README on why guessing is the failure mode.

## Dev mode — working on the plugins themselves

Clone the marketplace and point Claude Code at your checkout instead of the
published copy:

```bash
git clone https://github.com/enriquemoya/quorum-plugins.git ~/dev/quorum-plugins
```

```text
/plugin marketplace add ~/dev/quorum-plugins
```

Claude Code serves plugins from an **installed copy**, not from your working
tree and not from the marketplace clone either. Both of those exist and neither
is what loads:

| Under `~/.claude/plugins` | What it is | Loaded? |
|---|---|---|
| `cache/<marketplace>/<plugin>/<version>/` | the installed copy | **yes** |
| `marketplaces/<marketplace>/` | the marketplace's git clone | no |
| `installed_plugins.json` | the registry, with `installPath` per plugin | — |

`/plugin marketplace add` registers a marketplace and clones it. It does **not**
install anything, and until you install a plugin the `cache/` directory does not
exist at all. That difference is easy to miss and easy to draw a wrong
conclusion from.

**Do not type the destination.** Read it:

```bash
DEST=$(python3 -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')));print(d['plugins']['<plugin>@quorum-plugins'][0]['installPath'])")
cp -R ~/dev/quorum-plugins/plugins/<plugin>/* "$DEST/"
```

```powershell
$reg  = Get-Content "$env:USERPROFILE\.claude\plugins\installed_plugins.json" | ConvertFrom-Json
$dest = $reg.plugins.'<plugin>@quorum-plugins'[0].installPath
Copy-Item "$HOME\dev\quorum-plugins\plugins\<plugin>\*" $dest -Recurse -Force
```

Then restart Claude Code.

Bump the plugin's `version` in its `.claude-plugin/plugin.json` when you change
behaviour. **The install path is version-keyed**, so a stale path really is the
usual reason an edit appears not to take — read `installPath` again after a bump
rather than reusing the one you copied into last time.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Command doesn't appear after install | Claude Code not reloaded | Restart Claude Code |
| Edits to a plugin have no effect | Editing the working tree, not the cache | Sync the cache (above), then restart |
| Skill runs but can't find the repo layout | No profile, or a bad path in it | Create/fix `profile.yml`; paths are repo-relative |
| `quorum-orchestrator` errors on a missing skill | `quorum-tooling` not installed | Install `quorum-tooling` first |
| Marketplace add fails on a private repo | No credentials for the host | Configure your git credential helper for that host |
