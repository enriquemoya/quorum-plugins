---
argument-hint: <TICKET-KEY> [--include-subtasks]
description: Generate a structured investigation prompt for a ticket. Fetches the ticket, analyzes requirements, recommends memory bank patterns, and produces a stack-agnostic implementation/test-authoring guide.
---

# Prompt Generator Command

Generate a structured investigation prompt from a ticket. Content is shaped by the consumer repo's `.claude/profile.yml`, so any project (frontend, backend, QA-automation, etc.) can reuse this command — the prompt only references roles that the consumer has actually configured.

## Usage

```
/quorum-prompt-gen PROJ-68745
/quorum-prompt-gen PROJ-68745 --include-subtasks
```

## Profile

This command delegates to the `quorum-ticket-analyzer` and `quorum-prompt-builder` agents, which both read `.claude/profile.yml` for:

- `{{role:primary-stack-expert}}` / `{{role:secondary-stack-expert}}` — named in the prompt's "Patterns to Apply" section
- `{{role:conventions}}` — named for naming / commit / PR conventions
- `{{role:e2e-patterns}}` — only referenced when the ticket touches UI / routes / auth AND the role is non-null
- `{{profile.paths.memory_bank}}` — base path for cited `/context-query` queries

Null roles are omitted entirely from the prompt — no placeholder fallback content is added.

## What It Does

1. Fetches ticket from the tracker (`{{role:tracker}}`)
2. Runs **quorum-ticket-analyzer** — extracts routes, roles, components, complexity, technology surfaces
3. Queries memory bank for relevant patterns (paths resolved via profile)
4. Runs **quorum-prompt-builder** — generates the 6-section investigation prompt
5. Saves to `.claude/prompts/{TICKET-KEY}-{DATE}.md` (transient working copy — gitignored; in the orchestrator pipeline the prompt is posted to the ticket as a comment)

## Output Sections

1. Ticket Overview (routes, roles, complexity, stack context resolved from profile)
2. Problem Statement (AC from the tracker + Visual Spec subsection if image analysis ran)
3. Investigation Steps (`/context-query` calls scoped to the consumer's non-null roles)
4. Proposed Solution
5. Testing Strategy — the E2E checklist only renders when `{{role:e2e-patterns}}` is non-null
6. Success Criteria

## Agents Used

- **quorum-ticket-analyzer** — `.claude/agents/quorum-ticket-analyzer.md`
- **quorum-prompt-builder** — `.claude/agents/quorum-prompt-builder.md`
