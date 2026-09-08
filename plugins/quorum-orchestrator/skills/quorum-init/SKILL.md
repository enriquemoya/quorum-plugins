---
name: quorum-init
argument-hint: "[--dry-run]"
description: Read the repository being installed into — its stack, its components, and the cross-cutting characteristics that change how work is planned — then write the .claude/profile.yml every other Quorum skill reads, choose where the memory bank lives (in-repo Markdown, Obsidian-flavoured, or an external vault) and take its first step. Run this once when installing the plugins into a project.
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

## Step 2 — Map the components and characteristics

Step 1 answers *what is this built with*. This step answers *what is this made
of*, which is the question a plan actually needs and the only one no manifest
states outright.

**A component owns something.** Directories are not components. The test is
ownership: a directory is a component when it owns its own build, its own test
suite, or its own deployable. `src/utils/` owns none of those and is not a
component; `apps/api/` with its own `package.json` and test folder owns all
three and is.

Look in this order and stop as soon as the tree names its own parts:

1. **Workspace declarations name the components for you** — `pnpm-workspace.yaml`,
   `package.json` `workspaces`, `nx.json`, `turbo.json`, `lerna.json`, a `.sln`
   `Project(...)` list, `Cargo.toml` `[workspace] members`, `go.work`. When one
   exists, it IS the component list; do not second-guess it.
2. **Otherwise, one level down from each source root**, take directories that
   contain a manifest, a test directory, a `Dockerfile`, or an entry point.
3. **Otherwise the repository is one component.** Say so. A single-component
   repo is a normal answer, and inventing four to look thorough makes the map
   worse.

Record for each: name, path, kind, language, where its tests live, and what it
depends on — dependencies only when a manifest states them. Do not infer a
dependency from an import you happened to read; a partial dependency graph
presented as complete is worse than none.

**Entry points** are where execution begins — the `scripts.start` target, a
`Program.cs`/`main.go`/`__main__.py`, an HTTP route registration, a queue
consumer, a cron definition. One entry per way in.

**Datastores and external services** come from what the process connects to:
compose services, connection-string keys, ORM/driver dependencies, SDK
packages. Record the dependency, never the credential — `postgres`, not a host;
`s3`, not a bucket name; `oidc`, not a tenant id. Discovery reads a repository
that may be someone else's, and a profile is a committed file.

**Characteristics** are the cross-cutting facts that change how work is
planned: CI provider and config path, Dockerfiles and compose files,
infrastructure-as-code, an API contract file (OpenAPI/GraphQL/proto), the
migration tool, i18n, the auth mechanism, and the generated-code globs (which
must agree with `paths.no_hand_edit` — one list, written twice, will drift).

**`null` and `false` are different answers.** `null` means the concern was not
examined; `false` means it was examined and is absent. "No CI" that nobody
checked and "no CI" that someone confirmed lead to different next steps, so
never write one when you mean the other.

Depth is bounded on purpose. Stop at the first level that produces names. An
inventory of every folder is an inventory nobody reads, and the point of this
map is that the next session can hold it in mind.

## Step 3 — Report what you found

Show the operator a table before writing anything: the field, the value you
propose, and the evidence. Something like:

```
roles.primary-stack-expert   vue-expert          vue@3.4 in package.json dependencies
roles.unit-tests-gen         …-vitest            vitest@1.6 in devDependencies
commands.test_unit           npm run test:unit   package.json scripts.test:unit
git.default_base_branch      main                origin/HEAD -> origin/main
paths.no_hand_edit           ["*.Designer.cs"]   14 matching files, all with a
                                                  generated-code header

stack.components             web, api, shared    pnpm-workspace.yaml packages
stack.entry_points           2 (http, ui)        api/src/main.ts, web/index.html
stack.datastores             postgres            compose service + pg@8 driver
stack.characteristics.ci     github-actions      .github/workflows/ci.yml
stack.characteristics.i18n   false               ← LOOKED FOR, ABSENT
stack.characteristics.auth   (not examined)      ← null, nobody looked

ticket_prefix                PROJ                ← GUESS: 23 of the last 40
                                                  branch names start with PROJ-
atlassian.host               (none found)        ← ASK
```

Mark guesses and gaps distinctly from findings. The operator reads this table to
catch what you got wrong, and a table where inference and evidence look alike is
a table nobody can audit. Note the last two rows: `false` and `null` occupy the
same column and mean opposite things, so render them differently or the
distinction the schema draws dies in the report.

## Step 4 — Ask about what is left

Ask only about fields you could not settle from evidence. Group the questions;
do not walk the operator through the schema field by field.

Typical remainder: the tracker host and ticket prefix, the primary stack when a
repository is genuinely dual, whether E2E lives elsewhere, and any component
whose kind the tree did not make obvious.

The memory bank is NOT part of this round. It is a decision with a trade rather
than a fact you failed to find, so it gets Step 6 to itself instead of a line in
a list of leftovers.

For every question, say what happens if they skip it. Most fields are optional
and null means "this concern does not apply" — an operator who knows that can
skip three questions instead of inventing three answers.

## Step 5 — Write the profile

Write `.claude/profile.yml` with every field, including the nulls: a written
null is a decision recorded, an absent line is a question nobody asked. Comment
each non-obvious value with the evidence it came from, so the next person to
read the profile can tell what was measured from what was assumed.

Copy `PROFILE_SCHEMA.md` alongside it if the repository does not already have
it, so the profile is readable without the plugin installed.

## Step 6 — Configure the memory bank

The bank is where this project's durable knowledge accumulates: the patterns
the code actually follows, the decisions and why, the incidents and their root
causes. Where it lives is a decision with consequences, so it is made here,
once, and recorded — not re-asked every session.

Present the three modes with their trade, then ask:

| Mode | Where it lives | Choose it when |
|---|---|---|
| `local` | `.claude/memory-bank/` in this repo, plain Markdown | the knowledge is about THIS codebase and should arrive with a clone |
| `obsidian` | the same place, Obsidian-flavoured | the same, plus a human wants the backlink graph |
| `vault` | a folder inside an Obsidian vault outside the repo | the knowledge spans several repositories, or must not be committed |

**Say the trade out loud before they choose.** `local` and `obsidian` put the
bank under version control: it is reviewed with the code, it travels with a
clone, and it is as public as the repository. `vault` does none of those — the
knowledge survives across projects and is not in any diff, which is exactly
right for cross-repo context and exactly wrong for something a new contributor
needs on day one. An operator who hears that once picks correctly; one who is
asked "local or Obsidian?" is guessing at a filesystem question.

`obsidian` is not a different bank. It is the same directory with YAML
frontmatter, `[[wikilinks]]` in each `## Related` section, and a generated
`_index.md`. Agents keep reading it with Grep; nothing depends on the Obsidian
app being installed. That is worth saying, because "Obsidian mode" sounds like
a dependency and is not one.

For `vault`, settle two paths and check them:

- the **vault root** — `$QUORUM_VAULT` if it is set, otherwise ask. Confirm the
  directory exists. Do not create a vault: an operator who has one knows where
  it is, and one who does not should choose `local` today rather than acquire a
  second tool mid-install.
- the **project folder** inside it — default to the repository's directory
  name. A vault shared by several projects with everything at its root is a
  vault nobody can navigate after the third project.

Then write into `.claude/profile.yml`:

```yaml
memory_bank:
  enabled: true
  mode: vault                       # local | obsidian | vault
  vault:
    path: /Users/…/quorum-vault     # only for mode: vault
    project_folder: acme-web
  seeded: false
paths:
  memory_bank: /Users/…/quorum-vault/acme-web/memory-bank
```

`paths.memory_bank` is the one answer to *where the bank is*, in every mode —
every agent already reads it, and pointing it into the vault is what keeps them
working unchanged. The `memory_bank` block adds only what did not exist: the
flavour, and the vault it belongs to.

If the operator declines a bank, write `enabled: false` and stop. That is a
recorded decision; leaving the block out entirely means the next session asks
again.

## Step 7 — Take the first step

Ask before this; it writes files.

Run `/quorum-memory-bank init`, then seed it from what discovery established
rather than leaving a skeleton:

- **`architecture/stack.md`** — the Step 1 and Step 2 findings written down:
  languages, runtimes, frameworks, the component map, entry points, datastores,
  and the characteristics. This is the discovery report in its durable form,
  and it is the reason the inventory was recorded in the profile: the two must
  say the same thing.
- **`patterns/conventions.md`** — what the code actually does. Test file
  naming, component structure, import ordering, error handling. Cite the files
  you read for each one; a convention asserted without an example is a
  preference, and the next session cannot tell them apart.
- **`decisions/`** — empty unless discovery found a decision already written
  down somewhere (an ADR folder, a design doc). Do not invent ADRs for choices
  you merely observed; "uses Postgres" is a fact for `architecture/`, not a
  decision record with a rationale nobody stated.
- **`troubleshooting/`** — empty. It fills from real incidents, and seeding it
  with imagined ones teaches the wrong lesson to every session that reads it.

When `mode` is `obsidian` or `vault`, finish by running
`/quorum-memory-bank obsidian` so the seeded notes carry frontmatter,
wikilinks and an index from the start. Running it after the first real note
instead means the seed and everything after it are in two different shapes.

Set `memory_bank.seeded: true` and `seeded_on` when it is done. A later
`/quorum-init` reads those to tell a bank deliberately left empty from one that
was never started.

**Write only what you observed.** A bank that opens with confident claims
nobody verified is worse than an empty one, because every later session will
believe it and none will re-check it.

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

**Do not record anything that identifies an account, a tenant or an endpoint.**
The inventory names mechanisms and dependencies — `oidc`, `postgres`, `s3` —
because a profile is a committed file and discovery often runs against a
repository that is not yours.

**Do not enumerate every directory as a component.** A component owns a build,
a test suite or a deployable. A map of forty folders is a map nobody reads, and
it hides the four parts that matter.

**Do not create an Obsidian vault.** If the operator has one, use it; if not,
`local` is the answer today. Installing a plugin is not the moment to acquire a
second tool.

**Do not seed the bank with anything you did not observe.** Every later session
reads it as established fact and none of them will re-derive it.

**Do not treat the bundled skill list as the set of possible stacks.** A Go
repository is a valid answer; it just means most roles are null until someone
writes the skills. Say that plainly rather than forcing the closest match.
