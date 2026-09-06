---
key: {{ID}}
title: {{TITLE}}
kind: {{KIND}}
status: {{STATUS}}
jira: "{{JIRA_URL}}"
sprint:
points:
epic:
created: {{DATE}}
tags:
  - {{KIND}}
  - {{ID}}
---

# {{ID}} — {{TITLE}}

> [!info] Overview note (durable scope). For live progress & handoff, open [[status]].

## Summary

<!-- 2–4 sentences: what this story delivers and why it matters. -->

## Story & Related Tickets

<!-- Subtasks/siblings stay as rows here; they only get their own folder if a session does substantial standalone work on one. -->
| Ticket | Rel | Summary | Status |
|---|---|---|---|
| [[{{ID}}]] | self | {{TITLE}} | {{STATUS}} |

## User Story

<!-- Paste verbatim from Jira customfield_10202. -->

## Acceptance Criteria

<!-- Paste each AC from Jira customfield_10037 as a checkbox so progress is trackable. -->
- [ ]

## Scope

**In scope**
-

**Out of scope**
- <!-- name the ticket any deferred work moved to -->

## Key Decisions & Rationale

-

## Implementation Summary

<!-- Per-repo: file — one-line purpose. -->
-

## Deployment Order

<!-- The cross-repo NuGet chain if applicable: publish portal NuGet → bump platform reference → deploy platform. -->
-

## Source

- [{{ID}} in Jira]({{JIRA_URL}})

## Related

- Status & handoff: [[status]]
- QA test plan: `{{QA_PLAN}}`
