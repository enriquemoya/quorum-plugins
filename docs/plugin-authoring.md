# Plugin authoring — how to add a new plugin or extend an existing one

> Step-by-step guide to authoring plugins for this marketplace: directory layout, manifest schema, marketplace registration, dependency declarations, versioning, and the dev/test loop.
>

---

## When to add what

| Goal | Reach for |
|---|---|
| Add a new skill / command to behavior already covered by an existing plugin | Drop a file into the existing plugin's `skills/` / `commands/` / `agents/` dir |
| Add a new specialized sub-agent (orchestrator helper) | Drop into `quorum-orchestrator/agents/` |
| Add a generic utility skill the orchestrator does NOT need | Drop into `quorum-tooling/skills/` |
| Add a whole new bundle of related tooling (different domain, separate ownership) | Create a new plugin under `plugins/<plugin-name>/` |

The building-block primer is in [`docs/claude-code-concepts.md`](claude-code-concepts.md) — read that first if "skill vs command vs agent" isn't obvious.

---

## Part 1 — Add a skill / command / agent to an existing plugin

### Step 1: Pick the right plugin

This marketplace ships four plugins today:

| Plugin | What lives here |
|---|---|
| `quorum-orchestrator` | Orchestrator-specific workflow (commands + sub-agents) — drop here when the new file is invoked **by the orchestrator** or directly drives the orchestrator's pipeline |
| `quorum-tooling` | Generic utility skills + commands + hooks usable outside the orchestrator — drop here when the new file is **stand-alone** |

If a new file fits both, pick `quorum-tooling` (more reusable) and have the orchestrator depend on it.

### Step 2: Drop the file in the right subdirectory

Use the `quorum-` prefix on the filename (and on the YAML `name:` frontmatter field for agents):

```
plugins/quorum-tooling/skills/quorum-my-new-skill/SKILL.md
plugins/quorum-orchestrator/commands/quorum-my-new-command.md
plugins/quorum-orchestrator/agents/quorum-my-new-agent.md
```

### Step 3: Frontmatter

**Skill** (`SKILL.md`):

```yaml
---
name: quorum-my-new-skill
description: One-sentence description shown in /<skill-name> autocomplete and tool registries.
---
```

**Command** (`commands/<name>.md`):

```yaml
---
description: One-sentence description.
argument-hint: [optional-arg-shape]     # shown in autocomplete
---
```

**Agent** (`agents/<name>.md`):

```yaml
---
name: quorum-my-new-agent
description: One-line — what this sub-agent specializes in. Shown when the orchestrator decides whether to delegate to it.
model: sonnet                           # optional override; omit to inherit caller's model
tools: Read, Glob, Grep, Bash           # optional allowlist; omit to inherit caller's allowlist
---
```

The `name:` field must match the filename (minus `.md`). The orchestrator dispatches via `subagent_type: <name>` so the two must agree.

### Step 4: Body content

After the frontmatter, write the prose Claude follows when the skill/command/agent is invoked. Patterns to copy from existing files:

- Open with a 1–2 sentence "you are…" framing
- Document inputs/outputs explicitly
- Use numbered steps for procedures, bullets for principles
- End with the explicit return shape if the file is a sub-agent (so the caller knows what to expect)

### Step 5: Update the plugin's manifest (only if needed)

If the new file goes into a standard directory (`skills/`, `commands/`, `agents/`, `hooks/`), Claude Code **auto-discovers** it — no manifest change required. The auto-discovery dirs are declared once in `plugin.json` (e.g., `"commands": "./commands"`).

You only need to edit `plugin.json` if you're adding a **non-standard directory** or component (e.g., MCP servers, custom output styles). See [Claude Code plugins reference](https://docs.claude.com/en/docs/claude-code/plugins-reference) for the full optional-field list.

### Step 6: Bump the plugin version

If the addition is user-visible (a new slash command, a new sub-agent the orchestrator can call), bump `version` in the plugin's `.claude-plugin/plugin.json`:

```diff
- "version": "1.0.0"
+ "version": "1.1.0"
```

Use semver:

- **PATCH** (`1.0.0` → `1.0.1`) — bug fixes, internal-only changes
- **MINOR** (`1.0.0` → `1.1.0`) — new skill/command/agent added, no breaking change to existing
- **MAJOR** (`1.0.0` → `2.0.0`) — renamed/removed something users depend on (slash-command rename, sub-agent ID change)

If another plugin depends on yours via `dependencies: [{ name, version }]`, bumping MAJOR forces them to update their constraint or stay pinned to your old version. Bumping MINOR/PATCH is transparent under `>=` constraints.

### Step 7: Test locally (dev-mode install)

```text
/plugin marketplace add ~/dev/quorum-plugins
/plugin install <plugin-name>@quorum-plugins
```

Then invoke the new file and confirm it resolves + behaves correctly. Full dev workflow → [`INSTALL.md`](../INSTALL.md).

### Step 8: Commit + PR

Standard flow: feature branch, single commit per logical change, PR description references the ticket. Record behavior changes in the repo `CHANGELOG`.

---

## Part 2 — Create a whole new plugin

### Step 1: Decide whether you really need a new plugin

A new plugin is the right unit when:

- The new bundle has a **different audience or ownership** (e.g., QA-only skills shipped separately from dev tooling)
- The new bundle has **different lifecycle** (e.g., experimental skills you want to version-pin independently)
- The new bundle has **different dependencies** (e.g., MCP servers your existing plugins don't need)

If none of those apply, add to an existing plugin instead.

### Step 2: Create the directory layout

```
plugins/<new-plugin-name>/
├── .claude-plugin/
│   └── plugin.json
├── README.md                      ← optional but recommended
├── commands/                      ← optional
├── agents/                        ← optional
├── skills/                        ← optional
└── hooks/                         ← optional
```

Use the `quorum-` prefix on the plugin directory name itself: `plugins/quorum-<something>/`.

### Step 3: Write `plugin.json`

Minimum manifest:

```json
{
  "name": "quorum-your-plugin",
  "version": "1.0.0",
  "description": "One-paragraph description of what this plugin ships.",
  "author": { "name": "Your Name" },
  "commands": "./commands",
  "skills": "./skills"
}
```

Add `agents` / `hooks` / `mcpServers` paths only if you have non-default directory names. Standard names auto-discover.

**Declaring dependencies** (the quorum-orchestrator → quorum-tooling pattern):

```json
"dependencies": [
  { "name": "quorum-tooling", "version": ">=1.0.0" }
]
```

⚠️ `dependencies` is an **array of entries** (each entry is either a string plugin-name or an object with `name` + `version`), NOT an npm-style object. Caught this the hard way during Phase 3 dev-mode testing — Claude Code rejects object form with "expected array, received object".

### Step 4: Register in `marketplace.json`

Edit the marketplace catalog at [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) (repo root, **not** under `plugins/`):

```diff
  "plugins": [
    {
      "name": "quorum-orchestrator",
      "source": "./plugins/quorum-orchestrator",
      ...
    },
+   {
+     "name": "quorum-your-plugin",
+     "source": "./plugins/quorum-your-plugin",
+     "description": "…",
+     "category": "development"
+   },
    ...
  ]
```

The `source` field is relative to the marketplace root (= the directory containing `.claude-plugin/`, = repo root in our layout). Always start with `./`. The exact path resolution rule is in the [official docs](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces#relative-paths).

### Step 5: Validate

Quick static checks (run from repo root):

```bash
# JSON syntax
node -e "JSON.parse(require('fs').readFileSync('.claude-plugin/marketplace.json'))"
node -e "JSON.parse(require('fs').readFileSync('plugins/quorum-your-plugin/.claude-plugin/plugin.json'))"

# Source path resolves
ls plugins/quorum-your-plugin/.claude-plugin/plugin.json
```

Runtime check (in a fresh Claude Code session):

```text
/plugin marketplace remove quorum-plugins
/plugin marketplace add ~/dev/quorum-plugins
/plugin install quorum-your-plugin@quorum-plugins
/plugin list
```

If install succeeds + `/plugin list` shows the new plugin, you're good.

### Step 6: Documentation

If the new plugin is non-trivial:

- Add a `README.md` inside the plugin dir explaining its purpose
- Add a row to the consumer-cutover doc's plugin install list if downstream consumers should install it

---

## Part 3 — Versioning and dependency hygiene

### Version pinning

Per [Claude Code marketplace docs](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces#version-resolution-and-release-channels):

- If a plugin's `version` is set in its `plugin.json`, the plugin is pinned to that string. Users only get an update when the version changes.
- If `version` is omitted, the plugin tracks the marketplace's git commit SHA — users get updates on every `/plugin marketplace update`.

**Convention:** always declare a `version` field. Bump it when you ship a change you want users to opt into.

### Dependency constraints

Use semver ranges in `dependencies`:

| Constraint | Accepts |
|---|---|
| `">=1.0.0"` | Any version ≥ 1.0.0 (most permissive — accepts MAJOR bumps) |
| `"^1.0.0"` | Same MAJOR, any MINOR/PATCH (`1.x.x` but not `2.x.x`) |
| `"~1.2.0"` | Same MAJOR + MINOR, any PATCH (`1.2.x` but not `1.3.0`) |
| `"1.2.3"` | Exact version only |

Default for inter-plugin dependencies: `">=1.0.0"`. Tighten only when you've observed a real compatibility break.

### When dependencies break

If you bump a dependency to a MAJOR version that's incompatible with its consumer, the consumer's install will fail at `/plugin install` time with a clear error. The fix is either:

- Update the consumer's `dependencies` constraint to accept the new major (after testing compatibility)
- Keep the consumer pinned to the old major and let the two coexist

Claude Code does not auto-resolve transitive conflicts the way npm/yarn do — it just refuses to install if a constraint is unsatisfiable.

---

## Part 4 — Common gotchas

### Plugin source path must start with `./`

```json
"source": "./plugins/quorum-x"     // ✓ ok
"source": "plugins/quorum-x"       // ✗ Claude Code rejects
"source": "/plugins/quorum-x"      // ✗ absolute path semantics, not what you want
```

### Plugin name conflicts with built-in slash commands

Anthropic ships `/init`, `/review`, `/security-review` as built-in slash commands. If your skill or command shadows one of these, Claude Code's resolution order may surprise you. **Always use the `quorum-` prefix on user-invokable names** — it's the whole point of the convention.

### Renaming a skill / command / agent

A rename is a breaking change to anyone with the old name in their muscle memory or in their `subagent_type` references. Bump the plugin's MAJOR version, document the old → new mapping in the repo `CHANGELOG`, and keep the old name working for one release where you can.

### "Plugins can't reference files outside their directory"

Claude Code copies each installed plugin to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` and records that path as `installPath` in `~/.claude/plugins/installed_plugins.json`. Read the registry rather than constructing the path: the version segment changes on every bump, and a marketplace clone under `~/.claude/plugins/marketplaces/` holds a second copy of every file that is never the one loaded. Paths like `../shared-utils` in a plugin's prose or scripts will NOT resolve at runtime because the file isn't copied. If you need cross-plugin sharing, use the `dependencies:` mechanism (the dependent plugin gets its own cache copy) or symlinks declared via `${CLAUDE_PLUGIN_ROOT}` in hooks. See the [official caching docs](https://docs.claude.com/en/docs/claude-code/plugins-reference#plugin-caching-and-file-resolution).

### `.claude-plugin/plugin.json` is the source of truth

If you set the same field in both a plugin's `plugin.json` AND its `marketplace.json` entry, the **marketplace entry wins** for marketplace-exposed fields (`description`, `category`, `tags`, etc.). For runtime fields (`commands`, `agents`, `hooks`), the plugin manifest wins. Avoid duplication when you can.

---

## `profile.yml`: the consumer-stack contract

These plugins are **stack-agnostic** — they don't hardcode paths, roles, or Jira conventions. A consumer repo describes its stack once in `.claude/profile.yml`, and plugins resolve `{{profile.PATH.TO.VALUE}}` / `{{role:NAME}}` placeholders against it at runtime.

- **Canonical schema:** [`plugins/quorum-orchestrator/PROFILE_SCHEMA.md`](../plugins/quorum-orchestrator/PROFILE_SCHEMA.md) — the full contract (paths, roles, atlassian config, e2e settings).
- **Worked example:** [`plugins/quorum-orchestrator/profile.example.yml`](../plugins/quorum-orchestrator/profile.example.yml) — copy this into a consumer repo's `.claude/profile.yml` and fill in the values.
- **Reference implementation:** the `quorum-orchestrator` agents already resolve placeholders this way (e.g. `quorum-qa-handoff-publisher`, `quorum-ticket-analyzer`).

**When authoring a consumer-facing plugin:** if it needs stack-specific paths/roles, read them from `profile.yml` via placeholders rather than hardcoding, and ship a `profile.example.yml` documenting the keys you consume. Plugins that are fully self-contained (no consumer-stack assumptions) don't need a profile.

> **Status:** the convention and canonical schema live in `quorum-orchestrator` today. Repo-wide adoption — rewriting non-orchestrator agents to resolve `{{profile.*}}`/`{{role:*}}` instead of any remaining hardcoded assumptions — is tracked as remaining follow-up work; this entry establishes the shared convention.

---

## Reference

- [`docs/claude-code-concepts.md`](claude-code-concepts.md) — the building-block primer
- [`docs/claude-skills-overview.md`](claude-skills-overview.md) — every skill with examples
- [`INSTALL.md`](../INSTALL.md) — install + dev-mode + fallback flow
- [`plugins/quorum-orchestrator/PROFILE_SCHEMA.md`](../plugins/quorum-orchestrator/PROFILE_SCHEMA.md) — the `profile.yml` contract consumer repos use
- [Claude Code plugins reference (official)](https://docs.claude.com/en/docs/claude-code/plugins-reference) — exhaustive manifest schema + all component types
- [Claude Code marketplace docs (official)](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces) — marketplace schema, source types, hosting options
