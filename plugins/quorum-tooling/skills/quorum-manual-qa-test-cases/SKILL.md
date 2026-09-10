---
name: quorum-manual-qa-test-cases
argument-hint: [base-branch] [--no-post] [--post-review]
description: Generate manual QA test cases from code changes and post to the tracker
---

# Manual QA Test Case Generation Command

Generate manual QA test cases by analyzing code changes between the current branch and a base branch (resolved from `profile.git.default_base_branch`; falls back to `develop`, then `main`, then `master`), cross-reference historical the tracker stories for context, then post the full document to the ticket.

## When to use this vs the other QA skills

There are three distinct QA surfaces in the marketplace — they are **complementary lanes, not duplicates**:

| Skill / agent | Lane | Use it when |
|---|---|---|
| **`quorum-manual-qa-test-cases`** (this skill, `quorum-tooling`) | One-shot, dev-facing manual checklist from a diff. Posts to the tracker as a comment (or `--no-post`). **No persistence or status tracking.** | You want a quick pre-PR manual pass, or you're chaining from `/quorum-code-review`. |
| **`quorum-qa-test-plans`** (`quorum-workflows`) | Persistent, AC-routed, executor-tracked plans on disk (`{cwd}/qa-test-plans/{story}/plan.md`) with create/update/resume/reconcile/list lifecycle. | QA needs to *execute and track* coverage across sessions, routing each AC to ui-tester/backend-tester/human. |
| **`quorum-qa-handoff-publisher`** (`quorum-orchestrator`, Phase 7) | Publishes **automated** coverage (unit + E2E) as a "Review Automation Tests" subtask on the ticket. Manual cases deliberately excluded. | Inside the orchestrator pipeline, at PR delivery. |

This skill is the lightweight, throwaway lane. If you need durable, status-tracked execution, use `quorum-qa-test-plans` instead. The orchestrator's handoff publisher never invokes this skill.

## Flags

- `--post-review` — Fast path when chained from `/quorum-code-review`. See "Post-Review Fast Path" below.
- `--no-post` — **Suppresses the tracker posting.** When set, the skill generates the markdown to a publisher-known path (`.claude/qa-handoff/{TICKET-KEY}/manual-cases.md`) instead of `code-reviews/...` and DOES NOT call `{{role:tracker}}`. Used by the orchestrator's `quorum-qa-handoff-publisher` agent (Phase 7), which combines this output with the auto-generated test inventory and creates a single `Review Automation Tests` subtask on the ticket instead of a comment. The `--no-post` flag and `--post-review` flag may be combined.

## Post-Review Fast Path
**If this skill was invoked with `--post-review` argument** (i.e., chained from `/quorum-code-review`), the current conversation already contains all git analysis data, file contents, sprint number, base branch, and application info from the code review. In this mode:

- **SKIP** the entire Setup Phase (base branch, sprint number, ApplicationName are already known)
- **SKIP** Step 1 (ticket already extracted from branch name during review)
- **SKIP** Step 3 (all git commands, file reads, and diff data are already in the conversation)
- **DO run** Step 2 (the tracker Context Gathering) — this is new data the code review didn't collect
- **DO run** the directory/filename check — look for the review output directory that was just created and check for existing `testcases_*.md` files to set the filename
- Then proceed directly to Test Case Generation using all the context already available

This eliminates redundant git operations, file reads, and user prompts, making the chained flow significantly faster.

---

## Setup Phase
1. **Set base branch:** Use the branch given as an argument. Otherwise resolve `profile.git.default_base_branch` from the consumer repo's `profile.yml`; if that is absent, fall back to the first of `develop` / `main` / `master` that exists as a ref. **Do NOT read a compare-branch value out of `quorum-config.json`** — that key is for sprint reviews and points somewhere else.
2. **Display base branch:** Show "🧪 **GENERATING TEST CASES AGAINST BASE BRANCH: [base_branch]**" (when `--no-post` is set, prefix with "[no-post]")
3. **Get application info:** Read `.claude/quorum-config.json` for ApplicationName
4. **Ask for sprint number:** **ALWAYS prompt user to enter the current sprint number** - do not assume or skip this step. Invoke `/quorum-sprint-number` to calculate the current sprint. Present the calculated sprint number as a suggestion but allow user to override if needed. (When `--no-post` is set, skip this prompt — the orchestrator already knows the sprint context and the manual-cases.md file does not need a sprint header.)
5. **Determine output path:**
   - Default (no flag): `code-reviews/[year]/Sprint[sprint]/[ApplicationName]/[cleaned-branch-name]/testcases_{n}.md`
   - `--no-post`: `.claude/qa-handoff/{TICKET-KEY}/manual-cases.md` (the publisher knows this path; always overwrites if present, since the orchestrator runs once per ticket)
6. **Check for existing test case files** (default path only): Look for `testcases_*.md` files to determine the next number. Skip when `--no-post` is set (the filename is fixed).
7. **Set filename:** `testcases_{n}.md` (default) OR `manual-cases.md` (`--no-post`)

## Analysis Phase

### Step 1: Extract the tracker Tickets

**With `roles.tracker` null, `{{profile.ticket_prefix}}` may be unset too.** Then there is no key to recognise: skip the extraction, say so, and carry on with the branch name as given. A ticket key is an annotation here, not an input — it labels output when one is available, and its absence changes nothing else.
Scan branch name and commit messages for ticket numbers matching pattern `{{profile.ticket_prefix}}-\d+`. Normalize to `{{profile.ticket_prefix}}-NNNNN` format (uppercase prefix, hyphen, digits). Track the primary ticket (from branch name) and any additional tickets from commits.

### Step 2: the tracker Context Gathering
If a primary {{profile.ticket_prefix}}-NNNNN ticket was found, gather historical context from the tracker to inform test case generation and provide QA with cross-references:

1. **Get the tracker cloud ID:** Use `{{role:tracker}}` to retrieve the cloud ID. Store this for reuse in the the tracker posting phase.
2. **Fetch primary ticket:** Use `{{role:tracker}}` for the primary ticket with fields: `summary`, `description`, `parent`, `issuelinks`, `subtasks`, `comment`
3. **Walk the hierarchy:**
   - If the ticket has a **parent** (epic or story), note the parent's key, summary, and status
   - Use `{{role:tracker}}` with JQL: `parent = {parentKey} ORDER BY created DESC` (maxResults: 20) to find sibling stories under the same parent. This shows QA what other work has been done in this feature area.
4. **Collect linked issues:** Extract all `issuelinks` from the ticket. Record each linked issue's key, summary, status, and the **link type** (e.g., "action item from", "blocks", "is blocked by", "relates to"). These are the most relevant related tickets — bugs this fixes, stories it depends on, etc.
5. **Scan comments for context:** Read through the ticket's comments looking for:
   - References to other {{profile.ticket_prefix}}-NNNNN ticket numbers (these are related work the team discussed)
   - Background context about why this work is being done
   - Testing notes or constraints mentioned by the team
   - Any linked Confluence pages or documentation references
6. **Rovo search for related work:** Use the `search` MCP tool (Rovo) with the ticket summary as the query to find additional related ticket and Confluence pages. **Filter aggressively** — only keep results that are clearly relevant to the feature area being changed. Discard noise (old QA config failures, unrelated integrations, generic support tickets). Limit to the top 5 most relevant results.

### Step 3: Git Analysis
1. **Get commits:** `git --no-pager log --pretty=format:'%h %s (%an)' [base_branch]..HEAD`
2. **Get changed files:** `git --no-pager diff --name-only [base_branch]..HEAD -- . ':!.claude' ':!code-reviews'`
3. **Get diff:** `git --no-pager diff [base_branch]..HEAD -- . ':!.claude' ':!code-reviews'` (30s timeout)
4. **Fallback on timeout:** Read individual changed files if diff times out
5. **Read changed files:** Read each changed file in full to understand the complete implementation context, not just the diff
6. **Check for existing code review:** If `review_*.md` files exist in the same output directory, read the most recent one. Use its analysis (security findings, bug detection, recommendations) as additional context for generating more targeted test cases.
7. **Check local changes:** `git --no-pager diff --name-only HEAD`

## Test Case Generation

Analyze the changes and categorize them to drive test case generation:

### Change Type → Test Focus
- **UI Changes** (HTML, CSS, JS, Razor views, .cshtml) → Visual rendering, user interactions, form validation, responsive behavior, accessibility
- **API/Controller Changes** (.cs controllers, endpoints) → Request/response validation, authorization checks, error responses, HTTP status codes
- **Business Logic Changes** (.cs services, processors, helpers) → Happy path, edge cases, validation rules, error handling, boundary conditions
- **Database/SQL Changes** (.sql migrations) → Data integrity, idempotency (safe to run twice), rollback safety, schema compatibility
- **Configuration Changes** (system parameters, feature toggles) → Feature toggle behavior, environment-specific behavior, default values
- **Security-Related Changes** (auth, permissions, input handling) → Authentication bypass, authorization enforcement, input sanitization

### Priority Assignment Rules
Assign each test case a priority tier for the Priority / Focus Matrix:
- **P1 — Must Test Before Merge:** Core happy-path functionality that is new or significantly changed. Security-related changes. Data integrity changes. Anything where failure = production incident. If linked issues include recent bugs in the same area, bump related test cases to P1.
- **P2 — Should Test:** Error handling, validation, integration mapping, supporting workflows. Changes to existing patterns. Anything where failure = bug but not outage.
- **P3 — If Time Permits:** Edge cases, boundary conditions, cosmetic changes, configuration-only changes, regression checks for unchanged areas.

### Unit Test vs Manual QA Filtering
Before writing a test case, determine whether it is a **manual QA concern** or a **unit test concern**. Look for corresponding unit test files in the diff (files in `Test/` or `Tests/` directories).

**Do NOT create manual test cases for scenarios that are:**
- Only verifiable by reading code (e.g., "method returns X", "exception is not thrown", "internal object type is correct")
- Referencing internal method names, class names, exception types, or data structures that QA cannot observe
- Already covered by unit tests in the diff — if a unit test file explicitly tests the scenario, it belongs in unit tests, not manual QA

**Instead**, if a changed area is entirely covered by unit tests, add a single line to the "Unit Test Coverage" section (see output format below) noting what the unit tests cover. This tells QA "you don't need to manually test this — it's automated."

**Manual test cases should only cover behavior that is externally observable:**
- UI changes a user can see
- API responses that can be verified via a tool or browser
- Business workflow outcomes (e.g., "lead appears in AcmeCRM")
- Data that appears in logs, audit records, or database tables QA can query
- Configuration changes that affect visible behavior

### Guidelines
- Write test steps specific enough for a QA tester unfamiliar with the code to execute
- **Never reference internal method names, class names, or exception types in manual test case steps or expected results** — describe the observable behavior instead
- Include both positive (happy path) and negative (error/edge case) scenarios
- For each changed file, ensure at least one test case OR a unit test coverage note covers it
- Consider what existing functionality could break (regression)
- Reference specific UI elements, API endpoints, or database tables by name
- Use context from related ticket to inform regression test cases — if a linked bug was recently fixed in this area, create a specific test to verify it doesn't regress

## Output Document

Write the test case document to the output file with this structure:

```markdown
# Manual QA Test Cases - Sprint {sprint}
**Branch:** {branch_name}
**Ticket:** [{{profile.ticket_prefix}}-NNNNN]({{ticket_url}})
**Generated:** {date}
**Base Branch:** {base_branch}
**Application:** {ApplicationName}

---

## Changes Summary
{1-2 sentence description of what was changed and why}

## Related Stories & Historical Context
Tickets this work is built on top of or related to. Review these for additional testing context.

### Parent Epic/Story
- [{{profile.ticket_prefix}}-NNNNN]({{ticket_url}}) - {summary} ({status})

### Directly Linked Issues
- [{{profile.ticket_prefix}}-NNNNN]({{ticket_url}}) - {summary} ({status}) — {link type}

### Sibling Stories (same parent)
- [{{profile.ticket_prefix}}-NNNNN]({{ticket_url}}) - {summary} ({status})

### Related Tickets (from comments & search)
- [{{profile.ticket_prefix}}-NNNNN]({{ticket_url}}) - {summary} — {why it's relevant}

### Key Context from Comments
{Brief summary of relevant context found in ticket comments — background, constraints, testing notes from the team}

## Test Environment Setup
- {Any prerequisites, test data, or configuration needed before testing}

---

## Quick Developer Checklist
Condensed checklist for developers to verify before submitting for review.

- [ ] {Scenario} - {Brief description of what to verify}
- [ ] {Scenario} - {Brief description}

---

## Priority / Focus Matrix

| Priority | Test Cases | Focus Area | Risk Level |
|----------|-----------|------------|------------|
| P1 - Must Test | TC-001, TC-002, ... | {Focus area summary} | HIGH — {Risk description} |
| P2 - Should Test | TC-005, TC-006, ... | {Focus area summary} | MEDIUM — {Risk description} |
| P3 - If Time Permits | TC-010, TC-011, ... | {Focus area summary} | LOW — {Risk description} |

### P1 — Must Test Before Merge
These test cases cover the core new functionality and any changes that could cause data loss, security bypass, or broken integrations. **Block merge if these fail.**

### P2 — Should Test
These cover supporting functionality, error handling, and integration points. Failures here indicate bugs but are less likely to cause production incidents.

### P3 — If Time Permits
Edge cases, cosmetic changes, and low-risk paths. Important for completeness but unlikely to block a release.

---

## Detailed Test Cases

### TC-001: {Descriptive Test Case Name}
**Priority:** P1 | P2 | P3
**Category:** Functional | Security | Edge Case | Regression | UI | Performance

**Preconditions:**
- {Required state/setup for this specific test}

**Steps:**
1. {Step-by-step instructions}
2. {Specific enough for QA tester unfamiliar with the code}

**Expected Results:**
- {Observable outcomes after each significant step}

---

### TC-002: {Next Test Case}
...

---

## Unit Test Coverage
Scenarios covered by automated unit tests — no manual QA needed for these.

- **{Area/file}** — {What the unit tests verify} ({test file name})

## Regression Checks
{Test cases for existing functionality that could be affected by the changes}

## Files Changed Reference
{Table mapping changed files to the test case IDs that cover them}
```

**Format rules:**
- Omit any section or subsection that has no applicable content (e.g., if no parent epic, skip that subsection; if no edge cases, skip that section)
- In "Related Stories & Historical Context", limit sibling stories to the 10 most recent. For Rovo search results, only include tickets that are clearly relevant.
- Always include the link type for linked issues (it explains the relationship)
- The Priority / Focus Matrix must reference actual TC-XXX IDs from the Detailed Test Cases section
- Each test case in the Detailed Test Cases section must show its priority tier (P1, P2, or P3) instead of HIGH/MEDIUM/LOW

## the tracker Integration Phase

After writing the test case document to disk:

### When `--no-post` is set (called from `quorum-qa-handoff-publisher`)
- **Skip all the tracker posting steps below.** The orchestrator's publisher will create the `Review Automation Tests` subtask once, with the combined automated + manual content.
- **Show success message instead:** `"✅ Manual QA test cases saved to: {filepath}  (no-post mode — caller will publish to the tracker)"`
- The publisher reads the file at `.claude/qa-handoff/{TICKET-KEY}/manual-cases.md` and merges its Priority Matrix + Detailed Test Cases into the combined `qa_automation_tests.md`.

### Default (standalone use, no `--no-post`)
1. **Reuse cloud ID** from the the tracker Context Gathering phase (already fetched earlier). If it wasn't fetched (no ticket found earlier), call `{{role:tracker}}` now.
2. **Identify primary ticket:** Use the primary {{profile.ticket_prefix}}-NNNNN ticket number extracted from the branch name
3. **Post comment:** Use `{{role:tracker}}` to post the **full test case document** as a comment on the ticket (everything from the output document: summary, related stories, checklist, priority matrix, detailed test cases, regression checks, and files changed reference)
4. **Comment format:** Prefix the content with a header: `## Manual QA Test Cases (Auto-Generated)\nGenerated from branch: {branch_name}\n\n` followed by the full document content
5. **No ticket found:** If no {{profile.ticket_prefix}}-NNNNN ticket was found in the branch name or commits, skip the tracker posting and inform the user: "⚠️ No ticket found - skipping comment on the ticket. Test cases saved to: {filepath}"
6. **Success message:** After posting, show: "✅ Manual QA test cases posted to [{{profile.ticket_prefix}}-NNNNN]({{ticket_url}}) and saved to: {filepath}"

## Key Requirements
- **Focus on testable behavior:** Generate test cases for observable behavior, not implementation details
- **Actionable steps:** Every test case must have concrete steps a person can follow
- **Complete coverage:** Map every changed file to at least one test case
- **Leverage code review:** If a review exists, use its findings to strengthen test cases (e.g., security concerns become security test cases)
- **Leverage the tracker context:** Use related ticket history to inform regression tests and priority assignments. If linked bugs exist in the same area, create targeted regression test cases and assign them P1.
- **Timeout handling:** Use 30s timeouts for git operations, fall back to individual file reads
- **Idempotent the tracker posting:** Each run creates a new comment (does not edit previous ones)
