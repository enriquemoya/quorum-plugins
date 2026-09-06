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
   actually there, shows you the evidence for each value it proposes, asks about
   the few things no file can answer, and writes the profile. Re-running it is
   safe: values you set by hand are kept.

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

Claude Code serves plugins from a **cache**, not from your working tree. After
editing a plugin, sync it and reload, or the change is a silent no-op:

```bash
cp -R ~/dev/quorum-plugins/plugins/<plugin>/* \
      ~/.claude/plugins/cache/quorum-plugins/<plugin>/<version>/
```

Then restart Claude Code. Windows equivalent:

```powershell
Copy-Item "$HOME\dev\quorum-plugins\plugins\<plugin>\*" `
          "$env:USERPROFILE\.claude\plugins\cache\quorum-plugins\<plugin>\<version>\" `
          -Recurse -Force
```

Bump the plugin's `version` in its `.claude-plugin/plugin.json` when you change
behavior — the cache path is version-keyed, and a stale path is the usual reason
an edit appears not to take.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Command doesn't appear after install | Claude Code not reloaded | Restart Claude Code |
| Edits to a plugin have no effect | Editing the working tree, not the cache | Sync the cache (above), then restart |
| Skill runs but can't find the repo layout | No profile, or a bad path in it | Create/fix `profile.yml`; paths are repo-relative |
| `quorum-orchestrator` errors on a missing skill | `quorum-tooling` not installed | Install `quorum-tooling` first |
| Marketplace add fails on a private repo | No credentials for the host | Configure your git credential helper for that host |
