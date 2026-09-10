# Claude Code building blocks — skill vs command vs agent vs hook vs plugin

> A one-page primer for understanding what each piece does, when to reach for which, and how they fit together in this marketplace's plugins.
>

---

## TL;DR

| Concept | What it does | Lives in | Invoked by |
|---|---|---|---|
| **Skill** | Reusable knowledge + workflow Claude can run on demand | `skills/<name>/SKILL.md` | `/<name>` slash command (or Claude picks it automatically) |
| **Command** | Lightweight slash-command entrypoint | `commands/<name>.md` | `/<name>` typed by the user |
| **Agent** | Sub-agent identity Claude can delegate work to | `agents/<name>.md` | Claude's `Agent` tool with `subagent_type: <name>` |
| **Hook** | Shell / script that fires on a Claude Code lifecycle event | `hooks/<file>.sh` + `hooks/hooks.json` | Claude Code runtime — automatic |
| **Plugin** | A bundle of any/all of the above with a manifest | `plugins/<plugin-name>/.claude-plugin/plugin.json` | `/plugin install <name>@<marketplace>` |

The plugin is the distribution unit. Everything else is a component **inside** a plugin.

---

## 1. Skill — *reusable knowledge + workflow*

A skill is a chunk of instructions Claude can follow when invoked. Think of it as a runbook: prerequisites, steps, decisions, and the output shape — all in a single `SKILL.md` file.

**Anatomy:**

```
skills/
└── quorum-code-review/
    └── SKILL.md          ← single file; supporting files optional
```

The `SKILL.md` starts with YAML frontmatter (`name`, `description`, optionally `tools`/`model`) and then the prose body that tells Claude how to perform the skill.

**When to use a skill:**
- You have a multi-step workflow you'd like Claude to run consistently every time
- The workflow is read-mostly + decision-heavy (not just one command)
- Different developers want to invoke the same workflow without re-explaining it

**Example from this repo:** `quorum-code-review` — runs an intelligent diff against the base branch, classifies findings, writes a structured `review_N.md`, follows the project-specific naming conventions for the output path.

---

## 2. Command — *lightweight slash-command entrypoint*

A command is a thin markdown file that defines a slash-command name and what Claude should do when the user types it. Conceptually simpler than a skill — usually a single-screen prompt.

**Anatomy:**

```
commands/
└── quorum-orchestrate.md
```

YAML frontmatter declares `description` and optional `argument-hint`; the body is the prompt body Claude follows on invocation.

**Skill vs Command — what's the difference?**

In practice the line is thin. The Claude Code runtime treats both as `/<name>` invocations. The conventions:

- **`skills/<name>/SKILL.md`** — heavier, may have supporting files (templates, schemas), often calls sub-agents, longer body. Auto-discoverable.
- **`commands/<name>.md`** — lighter, single-purpose, no supporting files. Typed entrypoint.

**A name must not be both.** The runtime lists commands and skills in one `/` namespace, so two files under one name means the runtime picks and neither file says which. This repository had exactly one such pair — `quorum-code-review` — documented here as a thin wrapper around the skill. It was not a wrapper: it was a second copy of the procedure that had already drifted, missing the git lifecycle contract the skill carries. The command was deleted and the skill owns the name.

**When to use a command:**
- You want a memorable slash command without the overhead of a full skill
- The action is short — one prompt, one response, no decision tree
- You're wrapping an existing skill with a friendly name

---

## 3. Agent — *sub-agent identity Claude can delegate to*

An agent is a "named persona" Claude can spawn via its `Agent` tool. Each agent has its own system prompt, its own tool allowlist, and runs in a fresh context — useful for splitting work, parallelizing, or isolating expensive context from the main conversation.

**Anatomy:**

```
agents/
└── quorum-ticket-analyzer.md   ← YAML frontmatter + prompt body
```

Frontmatter:

```yaml
---
name: quorum-ticket-analyzer
description: Extracts structured implementation/test-generation inputs from a Jira ticket.
model: sonnet                  # optional model override
tools: Read, Glob, Grep, ...   # optional tool allowlist
---
```

**When to use an agent:**
- You want Claude to delegate a focused sub-task to a specialized instance
- You need fresh context (the main thread is loaded with unrelated work)
- You want parallelism — fire 3 agents at once and synthesize their results
- The sub-task needs a different model tier (e.g., heavy thinking via opus while the main conversation runs sonnet)

**Example from this repo:** `quorum-orchestrator` delegates to `quorum-ticket-analyzer` (extract requirements), `quorum-prompt-builder` (compose investigation prompt), `quorum-pr-generator` (write the PR template), etc. Each runs as its own subagent — the orchestrator stays lightweight and the specialized agents own their narrow domains.

---

## 4. Hook — *lifecycle script that fires automatically*

A hook is a script Claude Code runs at specific events — `PostToolUse` after every tool call, `PreToolUse` before specific commands, `SessionStart` once per session, etc. The runtime invokes the hook; you don't.

**Anatomy:**

```
hooks/
├── hooks.json                   ← declares which events trigger which scripts
├── memory-bank-nudge.sh
└── pre-commit-env-check.sh
```

`hooks.json` maps events → scripts; the scripts decide what to do.

**When to use a hook:**
- You want automated behavior that runs without the user (or Claude) asking
- You need a safety net — e.g., scan for secrets before every `git commit`
- You want to nudge Claude/user with a system reminder after a load-bearing edit

**Example from this repo:** `pre-commit-env-check.sh` self-filters to only fire on `git commit` Bash invocations and warns if `.env`-style files are about to be committed.

---

## 5. Plugin — *the distribution bundle*

A plugin packages any combination of the above into a single installable unit. The plugin's job is distribution + versioning + dependency resolution.

**Anatomy:**

```
plugins/quorum-orchestrator/
├── .claude-plugin/
│   └── plugin.json         ← manifest: name, version, dependencies, paths
├── commands/               ← 4 slash commands
├── agents/                 ← 11 sub-agents
└── (skills/ optional)
```

The manifest tells Claude Code what the plugin contains:

```json
{
  "name": "quorum-orchestrator",
  "version": "1.0.0",
  "description": "End-to-end Jira ticket delivery orchestrator...",
  "commands": "./commands",
  "dependencies": [
    { "name": "quorum-tooling", "version": ">=1.0.0" }
  ]
}
```

**When to use a plugin:**
- Always, for any component you want to ship to other devs or repos
- The plugin is the only durable distribution path

**This repo's plugins:**
- `quorum-orchestrator` — orchestrator workflow + 4 commands + 11 sub-agents
- `quorum-tooling` — 10 skills (code review, unit-test generators, memory bank, etc.) + 1 command + 2 hooks (shipped dormant / consumer-wired — see [`plugins/quorum-tooling/hooks/README.md`](../plugins/quorum-tooling/hooks/README.md))

Marketplace catalog: [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) at repo root, fetched when users run `/plugin marketplace add <repo-url>`.

---

## Cheat-sheet: which one do I write?

```
I want to…
├── Run a multi-step workflow on demand, reusably
│       → Skill (skills/<name>/SKILL.md)
├── Add a memorable /<name> shortcut
│       → Command (commands/<name>.md)
├── Delegate a focused sub-task with isolated context
│       → Agent (agents/<name>.md)
├── Fire automated behavior on a lifecycle event
│       → Hook (hooks/<file>.sh + hooks.json)
└── Ship any of the above to other devs / consumer repos
        → Plugin (the parent directory with .claude-plugin/plugin.json)
```

---

## Where to learn more

- [`INSTALL.md`](../INSTALL.md) — how to install plugins
- [`docs/plugin-authoring.md`](plugin-authoring.md) — how to write a new plugin or add a skill/command/agent to an existing one
- [`docs/claude-skills-overview.md`](claude-skills-overview.md) — every skill, with examples
- [`plugins/quorum-orchestrator/PROFILE_SCHEMA.md`](../plugins/quorum-orchestrator/PROFILE_SCHEMA.md) — the `profile.yml` contract consumer repos use to customize behavior
- [Claude Code official docs](https://docs.claude.com/en/docs/claude-code/plugins-reference) — exhaustive plugin reference, including hook events, tool allowlists, and advanced manifest fields
