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

Claude Code serves plugins from an installed copy, not from your working tree.
After editing a plugin, sync that copy and reload, or the change is a silent
no-op.

**Do not type the destination from memory.** The layout under
`~/.claude/plugins` has changed at least once — an earlier shape was
`cache/<marketplace>/<plugin>/<hash>/`, the shape observed now is
`marketplaces/<marketplace>/plugins/<plugin>/` with no version or hash segment.
Anything written here about the inside of that directory is **observed, not
contracted**: it was true when it was checked and nothing in this repository
would notice if it stopped being.

So find it rather than construct it:

```bash
# POSIX
DEST=$(dirname "$(find ~/.claude/plugins -path '*/<plugin>/*/.claude-plugin/plugin.json' | head -1)")
[ -n "$DEST" ] && cp -R ~/dev/quorum-plugins/plugins/<plugin>/* "$(dirname "$DEST")/"
```

```powershell
# Windows
$m = Get-ChildItem "$env:USERPROFILE\.claude\plugins" -Recurse -Filter plugin.json |
     Where-Object { $_.FullName -like "*\<plugin>\*" }
if ($m.Count -eq 1) {
  Copy-Item "$HOME\dev\quorum-plugins\plugins\<plugin>\*" $m[0].Directory.Parent.FullName -Recurse -Force
}
```

If the search returns **nothing**, stop — the plugin is not installed, and
copying into a guessed path produces a directory that looks right and loads
never. If it returns **more than one**, stop and look: two layouts can coexist
under that root, and syncing into one while Claude Code reads the other is the
same silent no-op with extra steps.

Then restart Claude Code.

Bump the plugin's `version` in its `.claude-plugin/plugin.json` when you change
behaviour. That is worth doing for the marketplace listing and for anyone
reading a diff — note that it is **not** what makes an edit take effect, which
an earlier version of this document claimed on the strength of a version-keyed
path that the observed layout does not have.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Command doesn't appear after install | Claude Code not reloaded | Restart Claude Code |
| Edits to a plugin have no effect | Editing the working tree, not the cache | Sync the cache (above), then restart |
| Skill runs but can't find the repo layout | No profile, or a bad path in it | Create/fix `profile.yml`; paths are repo-relative |
| `quorum-orchestrator` errors on a missing skill | `quorum-tooling` not installed | Install `quorum-tooling` first |
| Marketplace add fails on a private repo | No credentials for the host | Configure your git credential helper for that host |
