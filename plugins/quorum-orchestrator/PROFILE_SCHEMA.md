# `profile.yml` — Consumer-Repo Contract for shared `.claude/`

Each project that consumes these Claude Code plugins (`quorum-orchestrator` +
`quorum-tooling`) declares its stack, paths, and commands in
**`.claude/profile.yml`** at its repo root.
The shared agents, commands, and hooks read this file at runtime and adapt
their behavior to the consumer's stack — no shared file needs to know
whether the consumer is Vue + Cypress, .NET + NUnit, Karate, Python, or
something else.

This file documents the schema, the resolution rules, and includes a
complete worked example.

---

## Why a profile?

The shared `.claude/` (orchestrator, agents, commands, hooks) describes
**process**, not **stack**:

- _Process_: "in Phase 4 the implementer should delegate to a stack-expert
  skill, then run type-check, then run unit tests, then lint."
- _Stack_: "the stack-expert skill is `vue-expert`; type-check is
  `npm run type-check`; etc."

The profile is the bridge. The shared files reference **roles**, **paths**,
**commands**, and **conventions** via `{{profile.*}}` placeholders. The
consumer repo's `profile.yml` resolves those placeholders.

A repo with no profile (or one with `null` everywhere) gets a minimum-viable
process — no type-check, no E2E coverage scan, no stack expert. The shared
phases still run; they just skip what the profile says doesn't apply.

---

## Schema

```yaml
# .claude/profile.yml — placed at the consumer repo root.
# All fields are optional. Missing or `null` fields are treated as "skip".

# ─── Roles ───────────────────────────────────────────────────────────────
# Each role names a SKILL the orchestrator + agents delegate to for a
# specific concern. The shared files reference `{{role:NAME}}`; the value
# you put here is the skill's filename (without `.md`) as it appears under
# `.claude/skills/` in this repo or under `~/.claude/skills/` globally.
#
# Standard roles (extend as needed):
#   primary-stack-expert    — the dominant language/framework expert
#                              (e.g. vue-expert, dotnet-expert,
#                               react-expert, python-expert)
#   secondary-stack-expert  — only when a repo is genuinely full-stack
#                              (e.g. a service that has both BE + a small UI)
#   code-searcher           — repo-navigation patterns
#   conventions             — naming / commit / PR conventions for the org
#   e2e-patterns            — E2E framework patterns / auth + spec
#                              conventions skill (cypress-patterns,
#                              playwright-patterns, karate-patterns, …)
#   env-validator           — env-file + config validator agent (if any)
#   unit-tests-gen          — generator skill that scaffolds unit / component
#                              test files (e.g. quorum-gen-unit-tests-vitest,
#                              quorum-gen-unit-tests-dotnet9,
#                              quorum-gen-unit-tests-jasmine). Accepts EITHER a
#                              scalar skill name (single-stack) OR a list of
#                              { skill, filePatterns, label? } entries for
#                              polyglot repos — the test planner / code-review
#                              extension-match each changed file to a generator.
#                              (Supersedes the legacy `UnitTestSkills` array in
#                              quorum-config.json — that key is retired.)
#                              Consumed by `quorum-test-specialist` agent.
#   integration-tests-gen   — generator for integration tests if the consumer
#                              keeps that tier (rarely defined; usually null).
#   e2e-tests-gen           — generator skill that scaffolds E2E spec files
#                              (e.g. cypress-spec-generator,
#                              karate-feature-generator). May be the same
#                              skill as `e2e-patterns` for stacks that bundle
#                              the patterns + generator together (today
#                              cypress-patterns can cover both).
#   qa-handoff              — skill invoked at Phase 7 to generate the
#                              Dev→QA handoff package (manual QA test cases
#                              + posting to Jira). For today this is
#                              `quorum-manual-qa-test-cases`. `null` skips
#                              the handoff step.
#
# Use `null` for roles that don't apply to your stack.
roles:
  primary-stack-expert: null
  secondary-stack-expert: null
  code-searcher: code-searcher
  conventions: null
  e2e-patterns: null
  env-validator: null
  unit-tests-gen: null
  integration-tests-gen: null
  e2e-tests-gen: null
  qa-handoff: null

# ─── Stack inventory ─────────────────────────────────────────────────────
# What `/quorum-init` found when it read this repository. This block is a
# RECORD, not a switch: nothing branches on it. It exists so the discovery
# that produced the roles above is inspectable, and so the memory bank and
# the orchestrator can describe the system without re-deriving it — two
# answers to "what is this repo" that disagree are worse than one.
#
# Every entry carries the evidence it came from. An entry with no evidence
# is a guess someone typed, and should be deleted rather than trusted.
stack:
  # Languages actually built, not merely present. A stray `.ts` file in a
  # C# repo is not a TypeScript language entry.
  #   - name: TypeScript
  #     version: "5.4"          # from the toolchain, null when unpinned
  #     evidence: "tsconfig.json + typescript@5.4 in devDependencies"
  languages: []

  # What runs the built artifact: node 20, net9.0, python 3.12, jvm 21.
  runtimes: []

  # npm / pnpm / yarn / bun / nuget / uv / poetry / pip / go / cargo / maven.
  # Take it from the LOCKFILE present, not from what the README suggests.
  package_managers: []

  # Frameworks and the layer each one occupies, so "Vue + ASP.NET" reads as
  # two layers rather than one confused stack.
  #   - name: Vue
  #     version: "3.4"
  #     layer: ui               # ui | api | worker | data | infra | test
  #     evidence: "vue@3.4 in dependencies"
  frameworks: []

  # Data stores the code actually talks to. Read compose files, connection
  # strings, ORM configs and driver dependencies — a `postgres` service in
  # docker-compose is evidence; a `# TODO: maybe redis` comment is not.
  datastores: []

  # Third-party services the code calls out to at runtime (payment, auth,
  # mail, object storage, feature flags). Names the DEPENDENCY, never a
  # credential, an account id, a tenant or an endpoint that identifies one.
  external_services: []

  # Where execution begins. One entry per way in.
  #   - kind: http             # http | cli | worker | ui | job | library
  #     path: src/main.ts
  #     evidence: "scripts.start runs it"
  entry_points: []

  # The parts a change lands in. This is the map a newcomer needs and the
  # one thing no manifest states, so it is assembled from the tree: a
  # component is a directory that owns its own build, its own tests, or its
  # own deployable — not every folder.
  #   - name: web
  #     path: apps/web
  #     kind: ui                # ui | api | worker | lib | infra | tests
  #     language: TypeScript
  #     tests: apps/web/src/**/*.spec.ts
  #     depends_on: [shared]    # only when the manifest states it
  components: []

  # Cross-cutting characteristics that change how work is planned. Recorded
  # only when observed; `null` means "not looked for" and `false` means
  # "looked for and absent" — those are different and the difference matters.
  characteristics:
    monorepo: null            # { tool: pnpm|nx|turbo|lerna|dotnet-sln, workspaces: [...] }
    containerised: null       # { dockerfiles: [...], compose: [...] }
    ci: null                  # { provider: ..., config: path, jobs: [...] }
    infra_as_code: null       # { tool: terraform|bicep|cdk, path: ... }
    api_contract: null        # { kind: openapi|graphql|proto, path: ... }
    i18n: null                # { framework: ..., locales_path: ... }
    auth: null                # the MECHANISM (oidc, session, api-key), never a provider account
    migrations: null          # { tool: ef|alembic|prisma|flyway, path: ... }
    generated_code: null      # { globs: [...] } — mirrors paths.no_hand_edit

  # When this inventory was taken, and against which commit. A stack record
  # with no date silently becomes a claim about a tree that no longer exists.
  discovered_on: null         # ISO date
  discovered_at_ref: null     # git rev at discovery time

# ─── Paths ───────────────────────────────────────────────────────────────
# Repo-specific paths the orchestrator + agents need at runtime.
paths:
  # Glob (or list of globs) describing user-visible UI source files.
  # Used by Phase 5's "Component E2E review" step. `null` in non-UI repos.
  ui_glob: null

  # If E2E specs live in a SEPARATE repo, the absolute path to it; the
  # orchestrator's Phase 5 will operate on that repo for coverage scans
  # and spec scaffolding. `null` when E2E is in-repo or doesn't apply.
  e2e_repo: null

  # Where E2E specs live, relative to `e2e_repo` (or to THIS repo if
  # `e2e_repo` is null). `null` skips Phase 5 E2E steps.
  e2e_spec_root: null

  # Root of the memory bank in THIS repo. Defaults to `.claude/memory-bank`.
  memory_bank: ".claude/memory-bank"

  # Path to the consumer's app-level config file (read by the code-review
  # command for ApplicationName + branch comparisons).
  # Defaults to `.claude/quorum-config.json`.
  config: ".claude/quorum-config.json"

  # Root where review artifacts get written. Defaults to `.claude/reviews`.
  reviews: ".claude/reviews"

  # ── Artifact homes ────────────────────────────────────────
  # The orchestrator sorts its `.claude/**` artifacts by audience/lifecycle
  # using one test: "if the ticket vanished, would the artifact still be
  # useful?"  Yes → repo (committed); no → Jira or the PR (transient).
  #
  #   COMMITTED to the repo (durable knowledge about the codebase):
  #     .claude/memory-bank/   (patterns, decisions, troubleshooting)
  #     .claude/reviews/       (review_{N}.md — committed in Phase 6)
  #
  #   TRANSIT artifacts — durable home is Jira or the PR, NEVER committed.
  #   The orchestrator (Phase 1) auto-appends these to the consumer's root
  #   .gitignore under a marked block; consumers may also add them manually:
  #     .claude/prompts/       → posted to the Jira ticket as a comment (7b)
  #     .claude/validations/   → posted to the Jira ticket as a comment (7b)
  #     .claude/pr-templates/  → pasted into the PR description
  #     .claude/qa-handoff/    → "Review Automation Tests" subtask body (7b)
  # ─────────────────────────────────────────────────────────────────────

  # Auto-generated files that must NEVER be hand-edited or hand-merged
  #. When the orchestrator's Phase 4 plans an edit
  # to a matching path, or when a cherry-pick / merge conflict touches one,
  # the orchestrator refuses and asks the human to regenerate via the
  # appropriate tool (Entity Framework designer, scaffolder, codegen run,
  # etc.). Empty array (default) disables the protection.
  # .NET API example: ["*.Designer.cs", "*.edml", "*.Diagram1.view"]
  no_hand_edit: []

# ─── Memory bank ─────────────────────────────────────────────────────────
# WHERE the bank lives is `paths.memory_bank` above — every agent already
# reads that, and it stays the one answer to that question. This block says
# WHAT FLAVOUR the bank is and, when it lives outside the repository, which
# vault holds it.
memory_bank:
  # `false` skips every memory-bank step everywhere. A repo that does not
  # want one should say so once, here, rather than declining the prompt in
  # each session.
  enabled: true

  # local    — plain Markdown inside the repo, committed with the code.
  #            The default, and the right answer when the knowledge is about
  #            THIS codebase and should travel with a clone.
  # obsidian — the same in-repo location, Obsidian-flavoured: YAML
  #            frontmatter, `[[wikilinks]]` in `## Related`, a generated
  #            `_index.md`. Still committed, still readable by Grep; the
  #            vault features are a human convenience layered on top.
  # vault    — the bank lives OUTSIDE the repository, in an Obsidian vault
  #            that may span several projects. `paths.memory_bank` then
  #            points at the per-project folder inside that vault, so every
  #            consumer keeps working unchanged.
  #
  # Choosing `vault` moves knowledge out of version control. That is a real
  # trade — it survives across repos and is not reviewed with the code — and
  # `/quorum-init` states it before asking rather than after.
  mode: local

  # Only read when `mode: vault`.
  vault:
    path: null                # absolute path to the vault root, or $QUORUM_VAULT
    project_folder: null      # folder inside the vault for THIS project

  # Set by `/quorum-init` when it seeds the bank, so a later run can tell an
  # empty bank from one deliberately left empty.
  seeded: false
  seeded_on: null

# ─── Commands ────────────────────────────────────────────────────────────
# Shell commands the orchestrator runs at well-known steps. `null` skips
# the corresponding step entirely.
commands:
  type_check: null   # e.g. "npm run type-check" / "dotnet build" / "mypy ."
  test_unit: null    # e.g. "npm run test:unit" / "dotnet test" / "pytest"
  lint: null         # e.g. "npm run lint" / "dotnet format --verify-no-changes" / "ruff check"

# ─── Git ─────────────────────────────────────────────────────────────────
git:
  # Default base branch for PRs / code review comparisons.
  # e.g. "Develop" (today), "main", "master".
  default_base_branch: "master"

# ─── Atlassian / Jira ────────────────────────────────────────────────────
tracker:
  # Read by whichever skill `roles.tracker` names. With `roles.tracker: null`
  # this block is ignored entirely.
  # Tracker host (e.g. "your-org.atlassian.net").
  # Used by the PR template command to build ticket
  # links. `null` produces a `YOUR-JIRA-HOST` placeholder so the human
  # notices and fills it in once.
  host: null

  # Issuetype the `quorum-qa-handoff-publisher` agent uses when creating the
  # "Review Automation Tests" subtask under the story (Phase 7 of the
  # orchestrator). Must be a subtask-eligible type in the project. A common
  # uses `Dev Task` (which is subtask: true under stories). Generic Jira
  # consumers may use `Subtask`. Defaults to `Dev Task` when null.
  subtask_issuetype: "Dev Task"

  # OPTIONAL override map for the Jira custom-field IDs that hold a Story's
  # real content. Many Jira instances leave the STANDARD
  # `description` field empty on Story-type issues and store the narrative /
  # acceptance criteria in custom fields. The orchestrator's Phase 1 fetch
  # reads these IDs and treats them as the description / AC source; it falls
  # back to the built-in defaults when this key is absent, so most repos do
  # NOT need to set it. Override only when your Jira uses different field IDs.
  # Discover IDs via `getJiraIssue … expand=names` (the `names` map shows the
  # human label for each `customfield_NNNNN`).
  #   Built-in defaults: story_description=customfield_10202,
  #                  acceptance_criteria=customfield_10037,
  #                  epic_link=customfield_10007
  fields:
    story_description:   null   # e.g. customfield_10202 ("Story Description")
    acceptance_criteria: null   # e.g. customfield_10037 ("Acceptance Criteria")
    epic_link:           null   # e.g. customfield_10007 ("Epic Link")

# ─── Ticket prefix ───────────────────────────────────────────────────────
# Jira project key prefix used throughout this org (e.g. "PROJ", "ENG").
# Defaults to "PROJ". Used by validation, sprint-
# review filtering, and the PR template.
  ticket_prefix: "PROJ"

# ─── Org-level metadata ──────────────────────────────────────────────────
# Free-form org metadata referenced by command templates.
org:
  # JSON key inside `paths.config` whose value is the user-facing
  # application name. Defaults to "ApplicationName".
  application_name_key: "ApplicationName"

  # Anchor for sprint-number calculation. Sprint N started on `start_date`
  # and runs for `length_days`; subsequent sprints are computed by
  # floor-division. Consumed by /quorum-code-review and any skill that needs
  # "what sprint are we in today?". `null` disables sprint suggestion.
  sprint_anchor: null
  # Example shape (uncomment and edit):
  # sprint_anchor:
  #   sprint: 284
  #   start_date: "2026-02-11"
  #   length_days: 14

# ─── E2E specifics ───────────────────────────────────────────────────────
e2e:
  # Globs that signal "this change probably needs an E2E test." Used as the
  # trigger filter for `/e2e-coverage-check` in Phase 5.
  trigger_paths: []

  # Short description of the auth/test pattern the consumer uses. The
  # orchestrator quotes this verbatim to the human at Gate 5 so QA writers
  # know what convention to follow. Free-form text.
  auth_pattern: null

  # Default branch base when scaffolding new E2E specs in the E2E repo.
  branch_base: "master"

  # File extension for scaffolded E2E specs (e.g. ".cy.ts", ".spec.ts",
  # ".feature"). Used by the orchestrator's artifact-table rendering.
  spec_extension: null

# ─── Env validation ──────────────────────────────────────────────────────
env:
  # Globs of env/config files that, when changed, should re-trigger the
  # env-validator in Phase 6.
  trigger_paths: []

# ─── Code review extras ──────────────────────────────────────────────────
# The shared code-review skill applies a base ruleset; extra repo-specific
# rules go here. The reviewer prepends these as additional checks before
# producing the review document.
code_review:
  extra_rules: []
```

---

## Resolution rules

When a shared file contains `{{profile.X}}`:

1. **Read** the consumer repo's `.claude/profile.yml`.
2. **Resolve** the placeholder by walking the JSON-pointer-ish path.
3. **If null / missing / empty array**: the agent/command treats that
   step as "skip silently" — it does NOT throw, and it announces the skip
   in the gate summary so the human knows what was skipped.
4. **`{{role:NAME}}`** is sugar for `{{profile.roles.NAME}}` and, when
   non-null, the value is the skill filename (without `.md`) to delegate to.

### Worked example

A consumer repo declares:

```yaml
commands:
  type_check: "npm run type-check"
  test_unit: "npm run test:unit"
  lint: null
```

When Phase 5 reaches the `lint` step:

- It reads `{{profile.commands.lint}}` → `null`.
- It SKIPS the lint execution.
- It MUST announce in the Gate 5 tracker: `Lint: ⏭️ Skipped — profile.commands.lint is null`.

This makes "what the orchestrator did" auditable from the gate summary
alone, without needing to know the profile.

---

## Reference: worked consumer profiles

These are what `web_client`, `service_api`, and
`e2e_automation` would publish today. They're committed to the
consumer repos in Phase C / E, not here — included here as the canonical
illustration of how the schema gets populated for a real stack.

### `web_client` (Vue + Vite + Pinia + TanStack)

```yaml
roles:
  primary-stack-expert: vue-expert
  secondary-stack-expert: null
  code-searcher: code-searcher
  conventions: quorum-conventions
  e2e-patterns: cypress-patterns
  env-validator: env-validator
  unit-tests-gen: quorum-gen-unit-tests-vitest
  integration-tests-gen: null
  e2e-tests-gen: cypress-patterns   # patterns skill doubles as generator for today
  qa-handoff: quorum-manual-qa-test-cases

paths:
  ui_glob: "src/modules/*/{views,components}/**/*.vue"
  e2e_repo: "C:/dev/e2e_automation"
  e2e_spec_root: "cypress/e2e/marketing-portal/ui"
  memory_bank: ".claude/memory-bank"
  config: ".claude/quorum-config.json"
  reviews: ".claude/reviews"

commands:
  type_check: "npm run type-check"
  test_unit: "npm run test:unit"
  lint: "npm run lint"

git:
  default_base_branch: "Develop"

tracker:
  host: "your-org.atlassian.net"
  subtask_issuetype: "Dev Task"

  ticket_prefix: "PROJ"

org:
  application_name_key: "ApplicationName"
  sprint_anchor:
    sprint: 284
    start_date: "2026-02-11"
    length_days: 14

e2e:
  trigger_paths:
    - "src/modules/signin/"
    - "src/router/"
    - "src/modules/*/views/*.vue"
    - "src/modules/*/components/**/*.vue"
  auth_pattern: |
    Real Cognito + IMAP OTP via cy.loginAs(role) + reserveTestClient(...)
    (cached per role via cy.session). Mock auth is NOT used.
  branch_base: "master"
  spec_extension: ".cy.ts"

env:
  trigger_paths:
    - ".env.*"
    - "cypress.config.ts"

code_review:
  extra_rules:
    - "TypeScript strict compliance (no `any`, prefer interfaces for public types)"
    - "State management: Pinia for transient client state, TanStack Query for server state — never mix"
    - "Error handling via SystemErrorStore + showErrorToast"
    - "data-testid naming: `{module}-{element}` kebab-case"
```

### `service_api` (.NET 9 + EF Core)

```yaml
roles:
  primary-stack-expert: dotnet-expert
  secondary-stack-expert: null
  code-searcher: code-searcher
  conventions: quorum-conventions
  e2e-patterns: null
  env-validator: null
  unit-tests-gen: quorum-gen-unit-tests-dotnet9
  integration-tests-gen: null
  e2e-tests-gen: null              # API exercises happen via the QA repo's specs
  qa-handoff: quorum-manual-qa-test-cases

paths:
  ui_glob: null
  e2e_repo: "C:/dev/e2e_automation"   # API contracts get exercised by the E2E repo's smoke specs
  e2e_spec_root: "cypress/e2e/marketing-portal/api"
  memory_bank: ".claude/memory-bank"
  config: ".claude/quorum-config.json"
  reviews: ".claude/reviews"
  no_hand_edit:
    - "*.Designer.cs"      # EF Designer-generated; regenerate via Update Model From Database
    - "*.edml"             # EF EDMX serialized model; same
    - "*.Diagram1.view"    # EF designer diagram; same

commands:
  type_check: "dotnet build"
  test_unit: "dotnet test"
  lint: "dotnet format --verify-no-changes"

git:
  default_base_branch: "Develop"

tracker:
  host: "your-org.atlassian.net"
  subtask_issuetype: "Dev Task"

  ticket_prefix: "PROJ"

org:
  application_name_key: "ApplicationName"
  sprint_anchor:
    sprint: 284
    start_date: "2026-02-11"
    length_days: 14

e2e:
  trigger_paths:
    - "src/Controllers/**/*.cs"
    - "src/Domain/Services/**/*.cs"
  auth_pattern: |
    API contract specs use OAuth client credentials (no UI Cognito flow).
  branch_base: "master"
  spec_extension: ".feature"   # Karate-style API specs in the QA repo

env:
  trigger_paths:
    - "appsettings*.json"
    - "Dockerfile"

code_review:
  extra_rules:
    - "Controllers have [Authorize] unless explicitly anonymous"
    - "EF Core: avoid SaveChangesAsync inside loops; prefer batched ops"
    - "Async methods end with `Async` suffix"
    - "Public DTOs in `.Models` namespace; internal types stay internal"
```

### `e2e_automation` (Cypress + Karate)

```yaml
roles:
  primary-stack-expert: null      # QA repo is "test code"; no production stack
  secondary-stack-expert: null
  code-searcher: code-searcher
  conventions: quorum-conventions
  e2e-patterns: cypress-patterns  # AND karate-patterns — see note
  env-validator: null
  unit-tests-gen: null            # no unit tier in the QA repo
  integration-tests-gen: null
  e2e-tests-gen: cypress-patterns # also points at karate-feature-generator
                                  # for the Karate side once extracted (Phase E)
  qa-handoff: null                # QA repo IS the QA — no handoff needed

paths:
  ui_glob: null
  e2e_repo: null                  # E2E IS this repo
  e2e_spec_root: "cypress/e2e"
  memory_bank: ".claude/memory-bank"
  config: ".claude/quorum-config.json"
  reviews: ".claude/reviews"

commands:
  type_check: "npx tsc --noEmit --project tsconfig.json"
  test_unit: null                 # No unit tests; all integration via cypress/karate
  lint: null                      # No lint script today (potential follow-up)

git:
  default_base_branch: "master"

tracker:
  host: "your-org.atlassian.net"
  subtask_issuetype: "Dev Task"

  ticket_prefix: "PROJ"

org:
  application_name_key: "ApplicationName"
  sprint_anchor:
    sprint: 284
    start_date: "2026-02-11"
    length_days: 14

e2e:
  trigger_paths:
    - "cypress/e2e/**/*.cy.ts"
    - "cypress/support/**/*.ts"
    - "karate/**/*.feature"
  auth_pattern: |
    Real Cognito + IMAP OTP via cy.loginAs(role) + reserveTestClient(...)
    for UI specs. OAuth client-credentials for API/Karate specs.
  branch_base: "master"
  spec_extension: ".cy.ts"        # Cypress is the dominant E2E framework here

env:
  trigger_paths:
    - "cypress.config.ts"
    - "config/environments/*.env.json"

code_review:
  extra_rules:
    - "Specs MUST use real Cognito + IMAP OTP — never mock auth"
    - "Test ID format: PROJ-XXXXX-TC-NNN inside `it(...)` title"
    - "Describe block format: `PROJ-XXXXX | {module} | {smoke|regression}`"
```

> **Note on `e2e-patterns` plurality** — the role is single-valued today.
> If a repo legitimately needs two E2E frameworks (e.g. Cypress + Karate
> in `e2e_automation`), pick the dominant one and document the
> second via `code_review.extra_rules`. A follow-up could split into
> `e2e-ui-patterns` + `e2e-api-patterns` if that becomes load-bearing.

---

## How a brand-new project adopts this

1. Install the plugins (see [`INSTALL.md`](../../INSTALL.md)):
   ```
   /plugin marketplace add https://github.com/enriquemoya/quorum-plugins.git
   /plugin install quorum-tooling@quorum-plugins
   /plugin install quorum-orchestrator@quorum-plugins
   ```
2. Copy the bundled `profile.example.yml` (ships with the `quorum-orchestrator`
   plugin) → `<new-project>/.claude/profile.yml`.
3. Fill in the roles and paths that apply; leave the rest as `null`.
4. The orchestrator works immediately — skipping what doesn't apply, using
   what does.

No code in the plugins needs to know about the new stack. The profile is
the only thing that changes per consumer repo.

## Versioning

The schema lives at this file. Breaking changes get a `schema_version`
field bump (planned: when shared files start REQUIRING a field). For now,
all fields are optional → any pre-schema repo "just works."
