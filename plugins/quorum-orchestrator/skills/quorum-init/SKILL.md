---
name: quorum-init
argument-hint: "[--dry-run]"
description: Discover a repository's stack, tools and layout, then write the .claude/profile.yml every other Quorum skill reads. Run this once when installing the plugins into a project.
---

# Profile discovery

Every other skill here is written against a profile rather than against a stack.
`{{role:unit-tests-gen}}` means "whatever generates unit tests in *this*
repository" — Vitest in one, xUnit in the next, pytest in the one after. That
indirection is what makes the plugins reusable, and it is worth nothing until
someone fills the profile in.

This skill fills it in. It reads the repository, proposes a profile from what it
finds, asks about the handful of things no file can tell it, and writes
`.claude/profile.yml`.

**Discovery is proposal, not conclusion.** You infer from evidence and you show
the evidence. The operator confirms. A profile field written from a guess the
operator never saw is worse than a null: null means "skip this concern", while a
wrong value means every downstream skill quietly does the wrong thing.

## Running it

- `/quorum-init` — discover, confirm, write.
- `/quorum-init --dry-run` — discover and show the proposed profile without
  writing anything.

Re-running is safe. An existing `.claude/profile.yml` is read first, and every
value already in it is kept unless discovery has evidence it is wrong — in which
case you say so and let the operator decide. Never silently overwrite a field a
human set.

---

## Step 1 — Read the repository

Work from evidence in the tree, in this order. Stop widening the search once a
signal is unambiguous; a repository that says what it is in three places does
not need a fourth consulted.

**Manifests and lockfiles** are the strongest signal, because they are what the
build actually reads:

| Found | Says |
|---|---|
| `package.json` + a lockfile | Node. Read `scripts` for the real commands. |
| `*.csproj`, `*.sln`, `Directory.Build.props` | .NET. `TargetFramework` gives the version. |
| `pyproject.toml`, `setup.py`, `requirements*.txt` | Python. |
| `go.mod` | Go. |
| `Cargo.toml` | Rust. |
| `pom.xml`, `build.gradle*` | JVM. |
| `Gemfile` | Ruby. |
| `composer.json` | PHP. |

More than one is normal — a repository with `package.json` under `web/` and a
`.csproj` under `api/` is full-stack, and that is what `primary-stack-expert`
and `secondary-stack-expert` are for. Primary is where the work usually lands;
if that is not obvious from the tree, ask rather than assume.

**Frameworks** come from the dependency lists, not from folder names. `vue` in
`package.json` dependencies means Vue; a directory called `views` means nothing.

**Test tooling** is what picks the generator role:

| Evidence | `unit-tests-gen` |
|---|---|
| `vitest` in devDependencies, `vitest.config.*` | `quorum-gen-unit-tests-vitest` |
| `jasmine` / `karma.conf.*` | `quorum-gen-unit-tests-jasmine` |
| `xunit` / `nunit` package reference, `net9.0` | `quorum-gen-unit-tests-dotnet9` |
| the same on `net48` / `net4x` | `quorum-gen-unit-tests-dotnet4x` |
| `jest` in devDependencies | none bundled — leave null and say so |
| `pytest` in dev deps | none bundled — leave null and say so |

When nothing bundled matches, leave the role null and tell the operator which
generator they would need to add. A role pointing at a skill that does not exist
fails at the moment of use, which is the worst time to find out.

**E2E** is its own tier and often its own repository:

| Evidence | `e2e-patterns` / `e2e-tests-gen` | `e2e.spec_extension` |
|---|---|---|
| `cypress.config.*`, `cypress/` | `cypress-patterns` | `.cy.ts` |
| `playwright.config.*` | `playwright-patterns` | `.spec.ts` |
| `karate-config.js`, `*.feature` | `karate-patterns` | `.feature` |

If nothing E2E is in this repository, ask whether it lives in another one before
concluding there is none — `paths.e2e_repo` exists precisely for that case.

**Commands** come from the manifest, never invented:

- Node: the `scripts` block. `type-check`, `test:unit`, `lint` are common names;
  use what is actually there.
- .NET: `dotnet build`, `dotnet test`, and a linter only if one is configured.
- Python: whatever `pyproject.toml` configures — `mypy`, `pytest`, `ruff`.

A command you cannot find in a manifest is a command you should ask about. Do
not write `npm run lint` because it is usual; write it because `lint` is in the
scripts block.

**Git** gives the base branch: `git symbolic-ref refs/remotes/origin/HEAD` when
the remote says, otherwise the current branch, otherwise ask.

**Layout** gives `paths.ui_glob` and `no_hand_edit`. Look for where component
files actually live, and for generated files that must never be edited —
`*.Designer.cs`, `*.g.ts`, anything with a "do not edit" header. Getting
`no_hand_edit` right prevents a whole class of destroyed work, so err toward
listing a generated pattern you are unsure about.

**Tracker and docs** cannot be discovered from a repository in general, only
guessed at from branch names and commit messages. Ticket keys like `ABC-123`
suggest a prefix; a `.jira` or Atlassian URL in a CI config suggests a host.
Treat both as hypotheses to confirm, never as findings.

## Step 2 — Report what you found

Show the operator a table before writing anything: the field, the value you
propose, and the evidence. Something like:

```
roles.primary-stack-expert   vue-expert          vue@3.4 in package.json dependencies
roles.unit-tests-gen         …-vitest            vitest@1.6 in devDependencies
commands.test_unit           npm run test:unit   package.json scripts.test:unit
git.default_base_branch      main                origin/HEAD -> origin/main
paths.no_hand_edit           ["*.Designer.cs"]   14 matching files, all with a
                                                  generated-code header
ticket_prefix                PROJ                ← GUESS: 23 of the last 40
                                                  branch names start with PROJ-
atlassian.host               (none found)        ← ASK
```

Mark guesses and gaps distinctly from findings. The operator reads this table to
catch what you got wrong, and a table where inference and evidence look alike is
a table nobody can audit.

## Step 3 — Ask about what is left

Ask only about fields you could not settle from evidence. Group the questions;
do not walk the operator through the schema field by field.

Typical remainder: the tracker host and ticket prefix, the primary stack when a
repository is genuinely dual, whether E2E lives elsewhere, and whether they want
the memory bank seeded now.

For every question, say what happens if they skip it. Most fields are optional
and null means "this concern does not apply" — an operator who knows that can
skip three questions instead of inventing three answers.

## Step 4 — Write the profile

Write `.claude/profile.yml` with every field, including the nulls: a written
null is a decision recorded, an absent line is a question nobody asked. Comment
each non-obvious value with the evidence it came from, so the next person to
read the profile can tell what was measured from what was assumed.

Copy `PROFILE_SCHEMA.md` alongside it if the repository does not already have
it, so the profile is readable without the plugin installed.

## Step 5 — Seed the memory bank

Ask before doing this; it writes files.

When the operator agrees, run `/quorum-memory-bank init` and seed it with what
discovery established rather than an empty skeleton:

- `architecture/stack.md` — the stack, versions, and where each part lives.
  This is the discovery report, written down.
- `patterns/conventions.md` — what the code actually does: test file naming,
  component structure, import ordering. Cite the files you read; a convention
  asserted without an example is a preference.
- `troubleshooting/` — leave it empty. It fills from real incidents, and seeding
  it with imagined ones teaches the wrong lesson.

Write only what you observed. A memory bank that opens with confident claims
nobody verified is worse than an empty one, because the next session will
believe it.

---

## What this skill must not do

**Do not write a profile field you cannot justify.** If asked to skip the
questions, write nulls for what you could not detect and say which ones. A
complete-looking profile full of plausible defaults is the failure mode this
skill exists to prevent — every downstream skill will trust it.

**Do not install or modify tooling.** Discovery reads. If the repository has no
linter, the profile records that; it does not add one.

**Do not infer a stack from a single weak signal.** A `tsconfig.json` in a
repository with no `package.json` is a leftover, not a TypeScript project.

**Do not treat the bundled skill list as the set of possible stacks.** A Go
repository is a valid answer; it just means most roles are null until someone
writes the skills. Say that plainly rather than forcing the closest match.
