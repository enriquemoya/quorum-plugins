---
name: quorum-code-review
argument-hint: [base-branch]
description: Perform intelligent code review comparing the current branch against a base branch (resolved from profile.yml, or given explicitly)
---

# Git Code Review Command

Perform an intelligent code review comparing current branch against the base branch (given as an argument, else `profile.git.default_base_branch`, else `develop` → `main` → `master`).

## Git lifecycle contract

This skill **writes** `review_{N}.md` to disk; it does **NOT** call `git add` or `git commit`. Staging + committing the review file is the orchestrator's responsibility (Phase 6 Step 4 in `agents/quorum-orchestrator.md`), because only the orchestrator knows when in the pipeline the commit should land and which commit-message format the consumer's `{{role:conventions}}` skill prescribes.

Standalone invocation of this skill (outside the orchestrator) leaves the review file untracked on disk — the human runs `git add` + `git commit` themselves. The skill never touches the index.

## Setup Phase
1. **Set base branch:** Use the branch given as an argument. Otherwise resolve `profile.git.default_base_branch` from the consumer repo's `profile.yml`; if that is absent, fall back to the first of `develop` / `main` / `master` that exists as a ref. **Do NOT read a compare-branch value out of `quorum-config.json`** — that key is for sprint reviews and points somewhere else.
2. **Display base branch:** Show "🔍 **REVIEWING AGAINST BASE BRANCH: [base_branch]**"
3. **Get application info:** Read `.claude/quorum-config.json` for ApplicationName
4. **Ask for sprint number:** **ALWAYS prompt user to enter the current sprint number** - do not assume or skip this step. Invoke `/quorum-sprint-number` to calculate the current sprint. Present the calculated sprint number as a suggestion but allow user to override if needed.
5. **Create directory:** `code-reviews/[year]/Sprint[sprint]/[ApplicationName]/[cleaned-branch-name]/`
6. **Check for existing reviews:** Look for `review_*.md` files to determine review number for this session
7. **Set review filename:** Name output file as `review_{reviewnumber}.md` where reviewnumber increments from existing reviews

## Review Process
### Initial Review (no existing reviews)
1. **Get commits:** `git --no-pager log --pretty=format:'%h %s (%an)' [base_branch]..HEAD`
2. **Get changed files:** `git --no-pager diff --name-only [base_branch]..HEAD -- . ':!.claude' ':!code-reviews'`
3. **Get diff:** `git --no-pager diff [base_branch]..HEAD -- . ':!.claude' ':!code-reviews'` (30s timeout)
4. **Fallback on timeout:** Read individual files if diff times out
5. **Check local changes:** `git --no-pager diff --name-only HEAD`

### Follow-up Review (existing reviews found)
1. **Read last review:** Parse most recent review file for context
2. **Get recent changes:** Focus only on changes since last review
3. **Incremental analysis:** Review only new commits and local changes

## Review Content
Create comprehensive review with:
- **Summary** of changes, risks, and quality assessment
- **Commits section** listing all reviewed commits with hash, message, author
- **Security analysis** focusing on authentication, authorization, input validation
- **Code quality** assessment including architecture compliance, patterns, standards
- **Database schema validation** (see Database Rules below)
- **Bug detection** with specific fixes
- **Performance** considerations
- **Recommendations** prioritized by severity

### Database Rules
When reviewing SQL migration scripts or any files that create database tables (e.g., `CREATE TABLE` statements):
- **CRITICAL: Every new table MUST define a PRIMARY KEY.** If a `CREATE TABLE` statement does not include a primary key constraint (either inline column constraint or table-level `PRIMARY KEY(...)` clause), flag this as a **Critical** severity finding. PostgreSQL requires a primary key (or replica identity) for logical replication.
- Include this in the review output under a "Database Schema" section when SQL files are present in the changeset.
- **Test-data reset coverage:** If the repo maintains a routine that clears per-tenant data between automated test runs, evaluate every new `CREATE TABLE` for inclusion in it. List each under a "Test Reset" section with the table, a disposition (clear / skip-as-audit / skip-as-stage / skip-as-definition / unsure), and a one-line justification.

### .NET Standard Dependency Rules
When reviewing `.csproj` changes in projects that target `netstandard*`:
- **CRITICAL: .NET Standard projects must NOT reference packages that target only .NET Framework.** If a `<PackageReference>` is added to a `netstandard` project, check whether the referenced package targets .NET Standard or .NET Core. Flag any new Framework-only dependency as a **Critical** severity finding — it pollutes the .NET Standard project with Framework-specific assemblies and breaks cross-platform compatibility.
- Include this in the review output under a "Dependency Compatibility" section when `.csproj` files targeting `netstandard` are in the changeset.

## Key Requirements
- **Focus on current file state:** Read actual files to verify current implementation, don't rely solely on diff interpretation
- **Security emphasis:** Verify [Authorize] attributes, session validation, input validation
- **Scope documentation:** Always specify which files were reviewed vs skipped
- **Timeout handling:** Use 30s timeouts, fall back to individual file reads
- **Clear assessment:** Provide actionable recommendations with priority levels

## Post-Review: Test Generation
After the review document is written and saved:

1. **Determine available unit test skills:**
   - Read `roles.unit-tests-gen` from `.claude/profile.yml`. It is EITHER a scalar skill name (single-stack repo) OR a list of `{ skill, filePatterns, label? }` entries (polyglot repo). *(Legacy note: this mapping used to live in the `UnitTestSkills` array of `.claude/quorum-config.json`; that key was retired in favor of a single home in `profile.yml`. Fall back to it only if `profile.yml` has no `unit-tests-gen`.)*
   - Collect the file extensions of all changed files from the review (already known from git analysis)
   - **Scalar form:** the one skill applies to all changed source files. **List form:** match changed file extensions against each entry's `filePatterns` and collect the matching entries.
   - Build a list of applicable unit test skills with their labels (use the entry's `label`, or derive one from the skill name when absent)

2. **Ask the developer:** Use `AskUserQuestion` to ask: "Would you like to generate tests for this branch?" with dynamically built options:
   - **Manual QA Test Cases** — "Generate manual QA test cases and publish them through `{{role:tracker}}`"
   - **Unit Tests ({label})** — one option per matched unit test skill (e.g., "Unit Tests (.NET 4.7.2 Backend)", "Unit Tests (Jasmine/Karma Frontend)"). Only shown if `UnitTestSkills` is configured and at least one skill matched.
   - **All Tests** — "Generate manual QA test cases and all matched unit tests" (only shown if at least one unit test skill matched)
   - **Skip** — "Skip test generation"

3. **If Manual QA only:** Invoke the `/quorum-manual-qa-test-cases` skill using the `Skill` tool with args: `--post-review`.
4. **If Unit Tests ({label}) only:** Invoke the matching `/quorum-gen-unit-tests-*` skill using the `Skill` tool with args: `--post-review`.
5. **If All Tests:** Run unit tests first, then manual QA. Use the `Skill` tool for each invocation (NOT the Task tool) so that permissions and conversation context are inherited:
   - First: Invoke each matched `/quorum-gen-unit-tests-*` skill with args: `--post-review`
   - Then: Invoke `/quorum-manual-qa-test-cases` with args: `--post-review` (runs second so it can reference the generated unit tests to populate the "Unit Test Coverage" section accurately)
6. **If `roles.unit-tests-gen` is null / empty (and no legacy `UnitTestSkills` fallback):** Only offer Manual QA Test Cases and Skip.
7. **If Skip:** End the review session.
