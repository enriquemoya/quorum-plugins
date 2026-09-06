---
argument-hint: <TICKET-KEY> [base-branch]
description: Generate a PR description linking the Jira ticket, investigation prompt, validation report, and run commands. Stack-agnostic — works for any artifact type (code changes, test files, configs).
---

# PR Template Command

Generate a PR description linking all artifacts for a ticket's PR.

## Usage

```
/quorum-pr-template PROJ-68745
/quorum-pr-template PROJ-68745 main
```

## Profile

This command delegates to the `quorum-pr-generator` agent, which reads `.claude/profile.yml` for:

- `{{role:conventions}}` — branch naming, commit format, PR checklist content
- `{{profile.git.default_base_branch}}` — default base branch when none is passed (e.g. `Develop`, `main`, `master`)
- `{{profile.tracker.host}}` and `{{profile.tracker.ticket_prefix}}` — for the ticket link in the PR body

## Process

1. Validate ticket key format against `{{profile.tracker.ticket_prefix}}` (defaults to `PROJ-NNNNN` when null)
2. Resolve base branch — argument > `{{profile.git.default_base_branch}}` > fallback
3. Fetch ticket from Jira via MCP
4. Find artifacts: `.claude/prompts/`, `.claude/validations/`
5. Analyze git diff — list files added/modified
6. Delegate to **quorum-pr-generator** agent
7. Save to `.claude/pr-templates/{TICKET-KEY}-{DATE}.md`

## Agent Used

- **quorum-pr-generator** — `.claude/agents/quorum-pr-generator.md`
