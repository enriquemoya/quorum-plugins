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

1. **Workspace declarations name the components — of their own ecosystem** —
   `pnpm-workspace.yaml`, `package.json` `workspaces`, `nx.json`, `turbo.json`,
   `lerna.json`, a `.sln` `Project(...)` list, `Cargo.toml` `[workspace]
   members`, `go.work`. Take what one declares without second-guessing it, then
   **keep sweeping**: a JS workspace cannot name a Python worker sitting beside
   it, so a polyglot repo declares some of its components and hides the rest.
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

### Conventions — what the code already does

The memory bank used to derive this on its own, which meant two skills could
reach different conclusions about the same repository. Discovery does it once,
here, and the bank consumes the result.

Split what you find by **who uses it**, because the two halves want different
forms:

**Machine-readable → `observed:` in the profile.** These are the ones an
agent BRANCHES on, and an agent that cannot read a convention will assume one:

- **Where tests live.** A glob, derived from where test files actually are —
  `observed.test_files.unit_glob`, `e2e_glob`, and whether they sit beside
  the source. Take it from the files present, not from the runner's default.
- **How to read a test's name.** Open several real test files and find the
  line shape that carries the name. Record it as a regex with exactly one
  capture group, scoped by an `applies_to` glob, **with the match count you
  observed**. A polyglot repo needs more than one entry; a repo whose tests you
  could not parse needs none, and "none" is the honest answer that makes the QA
  handoff say "unread" instead of listing nothing and looking complete.
- **Commands that actually run.** Do not record a command because a manifest
  declares it. Run it. `observed.verified_commands` holds what succeeded,
  with evidence — that is what lets downstream phases stop probing a list of
  ecosystems they happen to know.

**Prose → the memory bank, in Step 7.** Naming, error handling, component
shape, import ordering, how state is organised, what a module's public surface
looks like. These are read by a human or an agent about to write code, and
flattening them into schema fields would lose exactly what makes them useful.

**Cite a file and line for every convention, in both halves.** A convention
without an example is a preference, and the difference matters most to the
session that inherits it and cannot re-derive it. Three real citations beat
twelve confident assertions.

**Report frequency, not just existence.** "18 of 20 spec files use `describe`
+ `it`" is a convention; "one file does" is a file. Say which you found, and
where a repository is genuinely inconsistent, record that as the finding rather
than picking the more common half and presenting it as the rule.

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


### Say which bundled skills this repository will use

End the report with the shortlist, because a marketplace of four plugins
installs a lot of things and most of them are irrelevant to any one
repository:

```
Will be used:
  quorum-gen-unit-tests-vitest    roles.unit-tests-gen
  quorum-code-review              always
  quorum-memory-bank              memory_bank.enabled

Inert here (no role points at them — installed, never invoked):
  quorum-gen-unit-tests-dotnet9   no .NET in this repo
  quorum-gen-unit-tests-jasmine   no Jasmine/Karma configured
  quorum-sql-review               no migrations directory found

Would be needed, not bundled:
  a pytest generator               pytest is configured; roles.unit-tests-gen
                                   stays null and Phase 5 skips generation
```

The third group is the one that matters. A role pointing at a skill that does
not exist fails at the moment of use, which is the worst time to find out — so
leave the role `null`, name the gap here, and let the operator decide whether
to write the generator or live without that step. Do not force the closest
bundled match: a Vitest generator aimed at a pytest suite produces confident
nonsense.

Nothing needs uninstalling. A skill no role names is never invoked; it costs
nothing but the confusion of appearing in a list, and naming it inert here is
what removes that.

## Step 4 — Run the questionnaire

Not "ask about what is left" — a questionnaire, driven by the **Required
fields** table in `PROFILE_SCHEMA.md`. That table is the source of truth for
what has to be answered; this step walks it.

The rule it encodes: a field is required **only once something else is switched
on**. Discovery decides most of those switches, so the questionnaire is short
in a simple repository and long in a rich one — which is the right shape, and
not something to shorten by guessing.

**Build the question set:**

1. Take every row of the Required-fields table whose *"required when"*
   condition now holds, given what Steps 1-3 established.
2. Drop the rows discovery already settled with evidence.
3. What remains is the questionnaire. Ask it in ONE grouped pass — a tracker
   block, an E2E block, a testing block — never field-by-field down the schema.

**For every question, state three things:**

- what the value is for,
- what happens if they skip it,
- and the default, when there is one worth defaulting to.

An operator who is told "skip this and ticket links render as plain keys" can
skip three questions confidently. One who is asked "tracker host?" with no
context invents an answer, and an invented answer is indistinguishable from a
measured one once it is in the file.

**Ask for the shape, not the vendor.** `tracker.browse_url_template` is
`https://…/{key}`; it is not "your Jira host". A question phrased around one
vendor gets a vendor-shaped answer, and the operator on GitHub Issues or Linear
either answers wrong or concludes the tool is not for them. Show two or three
concrete templates from different trackers so the shape is obvious.

**A skipped required answer switches its feature OFF.** This is the part that
keeps the profile honest: if the operator cannot supply the ticket URL
template, set `roles.tracker: null` and say so — do not leave a tracker role
that will emit broken links on every PR. Half-configured is worse than absent,
because absent is handled everywhere downstream and half-configured is handled
nowhere.

Record every skip and its consequence in the Step 3 report, so the operator
sees the shape of what they turned off rather than discovering it three phases
later.

**The memory bank is not part of this round.** It is a decision with a trade,
not a fact you failed to find, so it gets Step 6 to itself.

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

## Step 7 — Scaffold the constitution

The pipeline's audits cannot run without one. `quorum-audit` stops and routes
back here when `{{profile.governance.constitution}}` is absent — it can still
check traceability, but not whether the work violates anything this project
refuses to do, and a verdict silently missing half the audit is worse than none.

Copy the plugin's `governance/rules/CONSTITUTION.template.md` to
`.claude/governance/rules/CONSTITUTION.md`. **It ships with no articles**, and
that is the one file scaffolded into the repo — everything else in
`governance/` stays in the plugin, because a repo-local copy of a file nobody
edited goes stale silently.

Then ask for the articles.

**Ask for refusals, not values.** "What must this system never do?" gets an
article. "What do we care about?" gets a mission statement, and a mission
statement fires on nothing.

The test to apply to every candidate, and to say out loud:

> Could an auditor point at a file and a line and say *"this violates
> article N"*?

If not, it is a convention and belongs in the memory bank. Recording it here
instead gives it blocking weight it cannot carry, and an auditor that fires on
unfalsifiable articles is one people learn to override.

Three prompts that tend to surface real ones:

- **What would make you refuse to ship, however good the code was?**
- **What has gone wrong before that must not recur?** — an incident is the
  best source of an article, because the consequence is already known.
- **What does this domain forbid?** Regulatory, contractual, or safety
  constraints are articles by construction; they were written by somebody else
  and this project only has to not violate them.

Write **few**. A constitution with twenty articles is one nobody reads, and
every article is blocking in both audits and both autonomy modes. Starting with
two that matter beats twenty that mostly do not.

For each, record `Applies to: all | spec | ticket`. A hotfix routed through the
ticket path is not shaping the product, and holding it to product-shaping
articles produces noise rather than safety. Default `all`; narrow with a reason.

**An empty constitution is a valid answer, said out loud.** Write the file with
no articles, tell the operator the audits will check traceability and the data
rules but nothing project-specific, and record that they chose this. A file
with articles nobody meant is worse than a file with none — the first misfires
on real work, the second only under-checks.

## Step 8 — Take the first step

Ask before this; it writes files.

Run `/quorum-memory-bank init`, then seed it from what discovery established
rather than leaving a skeleton:

- **`architecture/stack.md`** — the Step 1 and Step 2 findings written down:
  languages, runtimes, frameworks, the component map, entry points, datastores,
  and the characteristics. This is the discovery report in its durable form,
  and it is the reason the inventory was recorded in the profile: the two must
  say the same thing. If they diverge later, the profile is the machine's
  answer and this document is the human's — reconcile rather than picking.
- **`patterns/conventions.md`** — the PROSE half of the conventions found in
  Step 2: naming, component structure, import ordering, error handling, how
  state is organised. Write what Step 2 observed, with its citations. Do not
  re-scan for them here — a second pass produces a second opinion, and two
  documents disagreeing about the same repository is the failure this
  consolidation removes.
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
