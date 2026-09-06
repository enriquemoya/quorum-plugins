# Quorum Plugins

A **Claude Code plugin marketplace template** — four installable plugins that
carry a delivery process rather than a codebase's specifics, plus the docs to
extend them with your own.

Install what fits your repo; each plugin stands on its own.

```text
/plugin marketplace add https://github.com/enriquemoya/quorum-plugins.git
/plugin install <plugin-name>@quorum-plugins
```

Full guide — dev-mode override, cache paths, per-repo setup →
[`INSTALL.md`](./INSTALL.md).

## The plugins

| Plugin | What it is | Configure with |
|---|---|---|
| [`quorum-orchestrator`](./plugins/quorum-orchestrator) | End-to-end ticket delivery pipeline: fetch → analyze → plan → implement → test → review → PR, with a human approval gate at every phase. 11 agents, 4 slash commands. | `profile.yml` |
| [`quorum-tooling`](./plugins/quorum-tooling) | Portable developer tooling: code review, SQL migration review, unit-test generators (.NET 4.7.2 / .NET 9 / Jasmine / Vitest), a memory bank with an Obsidian adapter, manual QA cases, sprint numbering, branch naming (10 skills). | `profile.yml` |
| [`quorum-workflows`](./plugins/quorum-workflows) | Cross-repo workflows: ticket-story intake, AC-routed QA test plans with executor tracking, an agent journal for autonomous runs, an Obsidian knowledge vault. | `profile.yml` |
| [`quorum-integration-kit`](./plugins/quorum-integration-kit) | Domain-neutral scaffolding for third-party integration partners: pipeline generator, ticket-driven change planner, and two pre-merge agents. | `integration-profile.yml` |

`quorum-orchestrator` depends on `quorum-tooling`. The other two are
independent.

## The idea

Most agent tooling is written against one codebase and dies with it. These
plugins are built the other way around: **the process is in the plugin, the
specifics are in a profile file your repo owns.**

That is why `quorum-orchestrator` asks for a `profile.yml` before it will run,
and why `quorum-integration-kit` refuses to scaffold until you nominate a
reference partner it can pattern-match against. A tool that guesses your
conventions produces confident, wrong code — the failure mode both are designed
to prevent.

`/quorum-init` writes that profile for you. It reads the repository, works out
the stack, test tooling, commands and layout from manifests and lockfiles rather
than folder names, and shows you the evidence behind every value before writing
it. Where the evidence runs out — your tracker, your ticket prefix — it asks
instead of defaulting. Nothing here is pinned to a stack: a Go repository with
most roles left null is a valid profile, and the skills that do not apply skip
themselves silently.

The same rule shows up throughout:

- **Human gates on irreversible steps.** The orchestrator stops for approval
  between phases; it never opens a PR on its own initiative.
- **Never fabricate what you can ask for.** Unknowns become explicit `TODO`
  markers in the output and named gaps in the report, never plausible filler.
- **Review before merge.** Every generator has a matching reviewer agent, and
  the generator's final instruction is to run it.

## Getting started

1. **Install** the marketplace and the plugins you want (above).
2. **Run `/quorum-init`** in your repository. It discovers the stack and writes
   `.claude/profile.yml`, showing its evidence as it goes. Review what it
   proposes — it is a proposal, and you are the one who knows which parts of
   your own repository it read wrong. The schema is at
   [`PROFILE_SCHEMA.md`](plugins/quorum-orchestrator/PROFILE_SCHEMA.md) if you
   would rather write it yourself.
3. **Seed the memory bank** when it offers — the discovery becomes
   `architecture/stack.md` and `patterns/conventions.md` rather than an empty
   skeleton.
4. **Run one command end to end** — `/quorum-orchestrate <WORK-ITEM>` is the
   widest path through the system.

## Docs

| Doc | Purpose |
|---|---|
| [`INSTALL.md`](./INSTALL.md) | Install, dev-mode, cache paths, troubleshooting |
| [`docs/claude-code-concepts.md`](docs/claude-code-concepts.md) | Primer — skill vs command vs agent vs hook vs plugin |
| [`docs/claude-skills-overview.md`](docs/claude-skills-overview.md) | What each skill does, with examples |
| [`docs/claude-development-guidance.md`](docs/claude-development-guidance.md) | Claude Code practices these plugins assume |
| [`docs/plugin-authoring.md`](docs/plugin-authoring.md) | How to add a plugin or extend an existing one |
| [`plugins/quorum-orchestrator/PROFILE_SCHEMA.md`](plugins/quorum-orchestrator/PROFILE_SCHEMA.md) | The `profile.yml` contract |

## Provenance

These plugins began as an internal toolkit I built for a previous employer. This
repository is a **rebuilt, domain-neutral template**: every reference to that
company, its clients, its partners, its ticket keys, and its internal
architecture has been removed, and the plugins that were inseparable from their
domain (database SMEs bound to a specific schema, partner-specific integration
knowledge, a build recipe tied to one CI pipeline) were dropped rather than
disguised. What remains is the process — which is the part that transfers.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## License

MIT — see [`LICENSE`](./LICENSE).
