# Claude Code Shared Skills — Overview

> **Source repository:** [quorum-plugins](https://github.com/enriquemoya/quorum-plugins) (the `quorum-plugins` marketplace; skills ship in the `quorum-tooling` plugin)

A high-level overview of the skills this marketplace ships, how to install them, and what they do for your day-to-day workflow.

---

## What Are Claude Code Skills?

Claude Code skills are reusable capabilities that extend Claude with custom knowledge and workflow automation. The skills below ship in the **`quorum-tooling`** and **`quorum-workflows`** plugins — install them once and they are available across every project.

They encode conventions, tooling patterns, and common workflows so you don't have to re-explain them in every conversation. What is specific to *your* codebase lives in `profile.yml`, not in the skill.

Skills are invoked with a simple slash command, e.g. `/quorum-code-review`.

> **New to Claude Code plugins?** Start with [`docs/claude-code-concepts.md`](claude-code-concepts.md) for the skill / command / agent / hook / plugin primer.

---

## Quick Links

| Resource | Link |
|----------|------|
| Install guide | [`INSTALL.md`](../INSTALL.md) |
| Concepts primer | [`claude-code-concepts.md`](claude-code-concepts.md) |
| Plugin authoring | [`plugin-authoring.md`](plugin-authoring.md) |
| `profile.yml` contract | [`PROFILE_SCHEMA.md`](../plugins/quorum-orchestrator/PROFILE_SCHEMA.md) |

---

## Getting Started with Claude Code

### Windows Support

Claude Code now runs natively on Windows. No WSL, no Linux VM — install it directly using the official installer. Run the following from a Command Prompt:

```
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

Full quickstart guide: https://code.claude.com/docs/en/quickstart

### Launching Claude Code

The most straightforward way to start a session is directly from the Windows Command Prompt in your project directory:

```
cd C:\dev\platform
claude
```

Claude will start, load your project's `CLAUDE.md` (if present), and you're ready to go. Any installed skills are immediately available via `/skill-name`.

### Setting up a tracker

Nothing in this marketplace talks to a tracker directly. Skills that need one
resolve `{{role:tracker}}` from your `profile.yml`, and that role names whichever
skill implements it.

**One driver ships: `quorum-jira-story`.** If your tracker is something else, the
role has nothing to point at and every step that needs a ticket announces the
skip — which is a supported configuration, not a broken one. Writing a driver
for another tracker is the way to change that, and no such driver is included.

The rest of this section sets up the one that ships.

Run this once per repository where you want Jira integration (e.g., `platform`, `websitehub`, `service_api`):

```
cd C:\dev\<repo>
claude mcp add --transport sse atlassian https://mcp.atlassian.com/v1/sse
```

Then authenticate:

1. Start Claude Code in that repo and run `/mcp`
2. Copy the authorization URL into your browser and complete the OAuth login
3. When prompted to grant permissions: **check Jira only — uncheck Confluence**

> **Important:** Always uncheck Confluence when granting permissions. The skills only need Jira access, and scoping permissions narrowly is good practice.

Repeat for each repository where you want Jira integration.

---

## Installing the Skills

All 10 skills are bundled inside the **`quorum-tooling`** plugin. Install it via this plugin marketplace:

```text
/plugin marketplace add https://github.com/enriquemoya/quorum-plugins.git
/plugin install quorum-tooling@quorum-plugins
```

This puts every `quorum-*` slash command directly in your hands — no per-repo setup, no junction-linking. Updates land via `/plugin marketplace update`.

For the full install / dev-mode / fallback flow, see [`INSTALL.md`](../INSTALL.md).

### Verifying the install

```text
/plugin list                 # both quorum plugins should appear
/quorum-sprint-number          # liveness check — should print current sprint
```

If the commands resolve, the skills are live.


---

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| Code Review | `/quorum-code-review` | Intelligent code review against a base branch resolved from profile.yml |
| Unit Tests — .NET 9 | `/quorum-gen-unit-tests-dotnet9` | Generate NUnit 4 / Moq / AutoFixture tests for changed files |
| Unit Tests — .NET 4.7.2 | `/quorum-gen-unit-tests-dotnet4x` | Generate NUnit / Moq tests for legacy .NET Framework projects |
| Unit Tests — Jasmine | `/quorum-gen-unit-tests-jasmine` | Generate Jasmine/Karma tests for AngularJS / Angular 5+ / Vue 2 |
| Unit Tests — Vitest | `/quorum-gen-unit-tests-vitest` | Generate Vitest tests for Vue 3 projects |
| Manual QA Test Cases | `/quorum-manual-qa-test-cases` | Generate prioritized QA test cases and publish them through the tracker role |
| SQL Migration Review | `/quorum-sql-review` | Review migrations for idempotency, destructive ops, lock/rewrite risk, and conventions |
| Sprint Number | `/quorum-sprint-number` | Calculate and display the current sprint number |
| Memory Bank | `/quorum-memory-bank` | Maintain a project memory bank of patterns and decisions |

---

## How Claude Remembers Your Project

Claude Code has two layers of persistent memory, and understanding the difference helps you get better results while keeping token costs low.

### Layer 1 — `CLAUDE.md` (always loaded)

Every project can have a `CLAUDE.md` file in its root. Claude **automatically loads this file at the start of every session** — it is always in context before you type a single message.

This is the right place for information Claude should *always* know:

- Project name and tech stack
- Key conventions and constraints
- How to build and run the project
- Links to important docs and runbooks
- "Never do X" rules the team has established

Keep `CLAUDE.md` focused and concise. Because it is loaded unconditionally on every session, every line in it costs tokens every time.

### Layer 2 — Memory Bank (loaded on demand)

The memory bank lives in `.claude/memory-bank/` inside each project and holds deeper reference material organized into four categories:

| Category | What goes here |
|----------|---------------|
| `architecture/` | System structure, component relationships, data flow diagrams |
| `decisions/` | Architecture Decision Records (ADRs) — why things are the way they are |
| `patterns/` | Reusable code patterns with real examples from the codebase |
| `troubleshooting/` | Known issues, root causes, and step-by-step resolutions |

Memory bank files are **not loaded automatically**. They are pulled in on demand — either by asking Claude to read a specific file, or by running `/quorum-memory-bank query <topic>`, which searches the bank and surfaces only the relevant context. This keeps token usage low during normal development while still making deep knowledge available when you need it.

```
# Ask Claude to load a specific area of memory
/quorum-memory-bank query form validation

# Or just ask Claude directly
"Read .claude/memory-bank/patterns/acmecrm-integration.md before we continue"
```

**Practical rule of thumb:** if you find yourself explaining the same thing to Claude at the start of multiple sessions, it belongs in the memory bank (and possibly a summary in `CLAUDE.md`).

---

## Spotlight: `/quorum-memory-bank`

The memory bank skill manages the `.claude/memory-bank/` directory for a project. It is how your team encodes hard-won knowledge so Claude can apply it without re-learning it every session.

### Subcommands

| Command | What it does |
|---------|-------------|
| `/quorum-memory-bank init` | Scan the project and create the initial architecture overview |
| `/quorum-memory-bank update` | Review recent git history and sync the memory bank with new patterns or decisions |
| `/quorum-memory-bank add-pattern` | Interactively document a reusable code pattern with a real codebase example |
| `/quorum-memory-bank decision` | Record an architectural decision as an ADR with context, alternatives, and consequences |
| `/quorum-memory-bank query <topic>` | Search the memory bank and return only the relevant context |
| `/quorum-memory-bank cleanup` | Archive obsolete content, consolidate duplicates, fix stale references |

### Example: recording a new pattern

After solving a tricky problem or establishing a new convention, capture it before the session ends:

```
/quorum-memory-bank add-pattern
```

Claude will walk you through:
1. What problem does this pattern solve?
2. What is the implementation? (it will find a real example in the codebase)
3. What are the benefits?
4. What are common mistakes to avoid?

The result is a structured `.md` file in `patterns/` that any developer — or Claude in a future session — can reference immediately.

### Example: querying before a complex task

Before starting work in an unfamiliar area, ask Claude to check what's already documented:

```
/quorum-memory-bank query AcmeCRM lead submission
```

Claude searches all four categories, reads the matching files, and synthesizes a focused answer — only loading what's relevant to the question rather than the entire memory bank.

---

## Spotlight: `/quorum-code-review`

The code review skill is the primary entry point for the developer workflow. Run it against any feature branch and it will:

1. **Analyze** all commits and changed files vs. the `Develop` branch
2. **Write a review document** covering security findings, code quality, bug detection, and prioritized recommendations — saved to `code-reviews/{year}/Sprint{n}/{app}/{branch}/review_1.md`
3. **Offer follow-on test generation** — after saving the review it asks whether you want:
   - Manual QA test cases (published through the tracker role when one is configured)
   - Unit tests for each matched language/framework
   - Both

Because the follow-on skills run **within the same conversation**, they reuse all the git analysis and file context from the review — no redundant work.

```
/quorum-code-review
```

Or against a specific base branch:

```
/quorum-code-review master
```

---

## Spotlight: `/quorum-manual-qa-test-cases`

This skill bridges the gap between code changes and QA. It:

1. **Reads the diff** and categorizes changes by type (UI, API, business logic, SQL, config, security)
2. **Queries the tracker** for the linked ticket — walking the parent/sibling hierarchy and related issues for historical context
3. **Generates a prioritized test plan** with three tiers:
   - **P1 — Must Test Before Merge** (core happy path, security, data integrity)
   - **P2 — Should Test** (error handling, integration, validation)
   - **P3 — If Time Permits** (edge cases, cosmetic changes)
4. **Publishes the document** as a comment on the ticket, through the tracker role and saves it locally

Test cases are scoped to **externally observable behavior** only — anything already covered by unit tests is noted in a "Unit Test Coverage" section so QA knows not to duplicate that effort.

```
/quorum-manual-qa-test-cases
```

> **Related lane:** this is the one-shot, throwaway checklist. For *persistent, status-tracked* QA execution that routes each AC to an executor and survives across sessions, use **`quorum-qa-test-plans`** (`quorum-workflows`). The orchestrator's `quorum-qa-handoff-publisher` is a third, separate lane that publishes automated (unit + E2E) coverage only.

---

## Spotlight: `/quorum-sql-review`

The database counterpart to `/quorum-code-review`. It reviews the migrations in a
changeset the way a DBA would — not "does it parse", but *what happens when this
runs against a live table, twice, at scale, in the wrong order.*

Eight check categories, ordered by how much damage each one prevents:

- **Idempotency** — can it run twice? Unguarded DML that duplicates rows is Critical;
  a script that merely errors on re-run is Major. Different failures, different severity.
- **Destructive operations** — `DROP`, `TRUNCATE`, unqualified `DELETE`/`UPDATE`,
  renames, narrowing type changes. Flagged even when correct, so a human approves them.
- **Lock and rewrite risk** — the volatile-`DEFAULT` table rewrite, `CREATE INDEX`
  without `CONCURRENTLY`, `CONCURRENTLY` wrongly nested inside a `DO` block,
  foreign keys added without `NOT VALID` → `VALIDATE`.
- **New-table completeness** — a missing primary key is Critical: PostgreSQL logical
  replication silently breaks without one.
- **Naming conventions** — Minor alone, Major when systematic, because that is a
  second convention being born.
- **Environment and secrets** — a literal credential in a migration is a secret in
  git history forever.
- **Ordering and deployment coupling** — does this break code that is already deployed?
- **Correctness details** — transaction boundaries, redundant indexes, collation.

Everything configurable is read from `profile.yml`; the defaults live in
[`references/sql-conventions.md`](../plugins/quorum-tooling/skills/quorum-sql-review/references/sql-conventions.md)
and the lock/rewrite detail in
[`references/migration-safety.md`](../plugins/quorum-tooling/skills/quorum-sql-review/references/migration-safety.md).
The review writes `sql-review_{N}.md` with a `PASS` / `PASS WITH RISKS` / `FAIL`
verdict and never edits a migration.

```
/quorum-sql-review            # vs. the resolved base branch
/quorum-sql-review main
```

---

## Workflow Integration

The skills are designed to chain together naturally inside a single Claude Code session:

```
/quorum-code-review
  └─ Review saved
      └─ "Generate tests?" prompt
          ├─ /quorum-gen-unit-tests-dotnet9  (tests written + published through the tracker role)
          └─ /quorum-manual-qa-test-cases    (test cases written + posted to the tracker)
```

All output is saved to the `code-reviews/` directory in your project alongside the source code, and comments are published through the tracker roleo the relevant the tracker ticket.

---

## More Information

- Install and dev-mode: [`INSTALL.md`](../INSTALL.md)
- Skill / command / agent / hook primer: [`claude-code-concepts.md`](claude-code-concepts.md)
- All skill source files: [`plugins/quorum-tooling/skills/`](../plugins/quorum-tooling/skills/)
