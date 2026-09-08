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

# ─── Autonomy ─────────────────────────────────────────────────────────────
# How much the pipeline asks. `human` stops at every gate; `agent` decides the
# routine outcomes from the decision matrix in PIPELINE.md and escalates the
# rest.
#
# There is no `--agent` flag. Switching autonomy ON is a standing decision
# recorded here; a per-run flag would make it an accident. `--human` forces a
# single run to stop at every gate, which is the direction that is safe to make
# easy.
autonomy:
  mode: human               # human | agent

  # The frontier is fixed, not configured: everything before PRD_READY is
  # human in both modes. An agent that writes the PRD defines the problem AND
  # the solution, which is where an autonomous system errs most expensively and
  # least visibly.

  agent:
    # Audit rounds allowed per UNIT, both gates together — not per gate.
    # Three scope-audit rounds therefore leave none for the implementation
    # audit, and that unit reaches STUCK without ever implementing. Intended: a
    # scope revised three times without converging is a PRD problem, and
    # spending the rest of the budget on code built from it wastes the run.
    #
    # The counter lives in status.yml. An agent that counts its own iterations
    # has no cap, because a fresh context starts at zero and the loop the cap
    # exists to stop is what produces fresh contexts.
    max_iterations_per_unit: 3

    # Batch behaviour for `/quorum-orchestrate --queue`.
    queue:
      # Run every eligible unit and report, rather than halting on the first
      # escalation. Halting early wastes an unattended session; the report is
      # what makes the run reviewable.
      on_escalation: park-and-continue    # park-and-continue | halt
      # Retry parked units in a second pass — a human may resolve one while the
      # queue is still running. Ends when a full pass advances nothing.
      retry_parked: true

# ─── Governance ───────────────────────────────────────────────────────────
# Where the rules that judge this project live. The plugin ships defaults;
# anything present in the consumer repo OVERRIDES the plugin default of the
# same name. Nothing is copied at install except the constitution template — a
# repo-local copy of a file nobody edited is a file that goes stale silently.
governance:
  # The project's articles. REQUIRED before any audit can run: an audit with no
  # constitution can still check traceability, but it cannot check whether the
  # work violates anything this project refuses to do.
  constitution: ".claude/governance/rules/CONSTITUTION.md"

  # Optional overrides. Empty means "use the plugin's defaults for everything".
  rules_dir:     ".claude/governance/rules"
  workflows_dir: ".claude/governance/workflows"

  # Where the pipeline keeps units of work and the evidence about them.
  specs_dir: ".claude/specs"
  runs_dir:  ".claude/runs"

# ─── Observed conventions ────────────────────────────────────────────────
# What this repository DOES, discovered by `/quorum-init` from the code.
#
# Named `observed`, not `conventions`, because `roles.conventions` already
# exists and means something else: a SKILL that knows an organisation's
# naming and PR conventions. This block holds FACTS measured from this
# repository's own code. Two different things sharing one word at two
# nesting levels is how a reader ends up configuring the wrong one.
#
# The split between this block and the memory bank is deliberate and worth
# stating, because getting it backwards is what produced the hardcoding this
# block removes:
#
#   * A convention an agent BRANCHES ON belongs here — it has to be
#     machine-readable, and an agent that cannot read it will guess, and a
#     guess is where "if it's a .ts file assume Vitest" comes from.
#   * A convention an agent READS belongs in the memory bank's
#     `patterns/conventions.md` — naming, error handling, component shape.
#     Prose is the right form for those, and a schema field would flatten them.
#
# Every entry carries its evidence, for the same reason the stack inventory
# does: a convention asserted without an example is a preference.
observed:
  # How to FIND tests. Globs, not framework names — an agent that needs to
  # locate the tests for a changed file should never have to know what runs
  # them.
  test_files:
    unit_glob: null           # e.g. "src/**/*.spec.ts", "tests/test_*.py"
    e2e_glob: null            # e.g. "cypress/e2e/**/*.cy.ts"
    colocated: null           # true when tests sit beside the source file
    evidence: null

  # How to READ a test name out of a test file, so a QA handoff can list the
  # scenarios a spec covers without the publisher knowing any framework.
  #
  # A LIST, because a polyglot repo has more than one answer and the right one
  # depends on the file. First entry whose `applies_to` glob matches the file
  # wins; when none matches, the scenario list is skipped and said to be
  # skipped — never guessed at with a regex that happens to be lying around.
  #
  # `regex` must have exactly ONE capture group: the test name.
  #   - applies_to: "**/*.spec.ts"
  #     regex: "(?:it|test)\\(['\"](.+?)['\"]"
  #     evidence: "24 matches across 6 spec files"
  test_name_extraction: []

  # Commands `/quorum-init` actually RAN and saw succeed, in the order it
  # found them. This is what replaces "probe the usual suspects": the usual
  # suspects are a stack assumption, and a recorded successful run is not.
  # Empty means nothing was verified — which is a fine answer that leads to
  # "skipped, unverified" rather than to a wrong command.
  verified_commands: []       # [{ purpose: type_check|test_unit|lint, command, evidence }]

  # Anything else discovery established that an agent must branch on. Open
  # vocabulary on purpose: a fixed field list is itself a stack assumption,
  # and the next repository will have a convention this schema never imagined.
  #   - name: migrations-are-generated
  #     value: true
  #     evidence: "Migrations/ has 40 files, all with a generated header"
  other: []

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
  # How to build a link to a ticket. THE one place a ticket URL is formed —
  # `{key}` is substituted, nothing else is assumed. Before this existed, two
  # skills built Atlassian URLs by hand, which made "works with any tracker"
  # true of the schema and false of the output.
  #   Jira:    "https://your-org.atlassian.net/browse/{key}"
  #   GitHub:  "https://github.com/org/repo/issues/{key}"
  #   Linear:  "https://linear.app/org/issue/{key}"
  # `null` renders the key as plain text with no link, which is correct for a
  # tracker nobody can reach by URL and honest for one nobody configured.
  browse_url_template: null

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

---

## Required fields

Almost every field here is optional, and that is the point: `null` means "skip
this concern", so a repository that has no tracker, no E2E tier and no linter
gets a working profile with most of it empty.

But some fields are **required once something else is switched on**. A tracker
role with no way to build a ticket URL is not a smaller configuration; it is a
broken one, and it fails at the moment of use rather than at the moment of
setup. Those conditional requirements are listed here so `/quorum-init` can ask
about exactly them, and so a hand-edited profile can be checked against the
same list.

| Field | Required when | What breaks without it |
|---|---|---|
| `git.default_base_branch` | always | PRs target the wrong branch, and diffs are computed against the wrong base |
| `tracker.browse_url_template` | `roles.tracker` is non-null | every ticket reference renders as bare text; nothing links |
| `tracker.host` | the tracker skill reaches an API | the tracker skill cannot fetch or post; Phase 1 has no ticket |
| `ticket_prefix` | `roles.tracker` is non-null | ticket keys cannot be recognised in branch names or commit messages |
| `observed.test_name_extraction` | `roles.qa-handoff` is non-null | the handoff lists zero scenarios from a repository full of tests |
| `observed.test_files.unit_glob` | `roles.unit-tests-gen` is non-null | the generator cannot tell where its output belongs |
| `paths.e2e_spec_root` | `roles.e2e-patterns` or `paths.e2e_repo` is set | Phase 5's E2E steps have no directory to scan or scaffold into |
| `memory_bank.vault.path` | `memory_bank.mode` is `vault` | the bank has no location; notes would fall back into the repo |
| `memory_bank.vault.project_folder` | `memory_bank.mode` is `vault` | every project writes to the vault root and the vault stops being navigable |
| `paths.ui_glob` | `code_review.extra_rules` names UI rules | the rules are declared and never applied to anything |

**Nothing is required unconditionally except the first row.** A requirement
that cannot be satisfied is a requirement that stops the tool installing into
a repository it was meant to serve, so every other row is reachable only by
turning something on.

### What happens when a required answer is missing

The profile stays coherent: **the dependent feature is switched off, not left
half-configured.** If the operator cannot supply a ticket URL template, then
`roles.tracker` is set to `null` and the profile records why. It does not keep
a tracker role that will produce broken links on every PR.

This is the rule that makes the whole schema safe to read: a non-null value is
a promise that the concern is configured. A field that is set while its
requirements are missing turns every `if non-null` check downstream into a
lie, which is worse than the concern being absent — absent is handled
everywhere, half-configured is handled nowhere.

## Resolution rules

When a shared file contains `{{profile.X}}`:

1. **Read** the consumer repo's `.claude/profile.yml`.
2. **Resolve** the placeholder by walking the JSON-pointer-ish path.
3. **If null / missing / empty array**: the agent/command treats that
   step as "skip silently" — it does NOT throw, and it announces the skip
   in the gate summary so the human knows what was skipped.
4. **`{{role:NAME}}`** is sugar for `{{profile.roles.NAME}}` and, when
   non-null, the value is the skill filename (without `.md`) to delegate to.
5. **`{{ticket_url}}`** is DERIVED, not a field: substitute the ticket key
   into `{{profile.tracker.browse_url_template}}`. When the template is null,
   render the key as plain text with no link. It exists because nine files
   used to build `https://<host>/browse/<KEY>` by hand, which quietly made
   every one of them a Jira file — and a repository on GitHub Issues got a
   link that 404s rather than one that is absent.

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
