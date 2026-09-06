---
argument-hint: <TICKET-KEY>
description: Validate work artifacts (code changes, tests) against a Jira ticket's acceptance criteria. Stack-agnostic — checks AC coverage and convention compliance; delegates syntax-level checks to consumer's e2e-patterns / test-generator skills.
---

# Validate Ticket Command

Validate that the current branch's artifacts satisfy a Jira ticket's requirements.

## Usage

```
/quorum-validate-ticket PROJ-68745
```

## Profile

This command delegates to the `quorum-ticket-validator` agent, which reads `.claude/profile.yml` for:

- `{{role:conventions}}` — naming / commit / PR / test-id conventions
- `{{role:e2e-patterns}}` / `{{role:e2e-tests-gen}}` — E2E spec authoring + naming. When both are null, E2E checks are skipped silently.
- `{{profile.paths.e2e_spec_root}}` / `{{profile.paths.e2e_repo}}` — where to look for E2E specs (this repo or a sibling)
- `{{profile.paths.ui_glob}}` — scope for the "selector quality" check

## Process

1. Fetch ticket from Jira (`getJiraIssue`) to retrieve AC
2. Discover artifacts via `git diff` and grep for the ticket key
3. Delegate to **quorum-ticket-validator** agent
4. Save validation report

## Output

Validation report saved to `.claude/validations/{TICKET-KEY}-{DATE}.md` (transient working copy — gitignored; in the orchestrator pipeline it is posted to the Jira ticket as a comment).

Checks performed (each gated on the relevant role being non-null):
- AC coverage — every AC item has at least one piece of evidence in code or tests
- Naming / test-id conventions (per `{{role:conventions}}`)
- E2E artifact presence + tier tags + selector quality (per `{{role:e2e-patterns}}`)
- Memory bank pattern compliance
- No hardcoded credentials in staged code

## What this command does NOT do

- It does NOT run the tests (Phase 5 of `/quorum-orchestrate` runs them via `{{profile.commands.test_unit}}` etc.)
- It does NOT enforce linting (that belongs to the code-review skill)
- It does NOT parse spec syntax (that belongs to the stack-specific generator)

## Agent Used

- **quorum-ticket-validator** — `.claude/agents/quorum-ticket-validator.md`
