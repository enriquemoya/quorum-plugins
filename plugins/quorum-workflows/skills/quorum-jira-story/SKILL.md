---
name: quorum-jira-story
description: >
  Use before working on any Jira ticket. Most Jira instances keep acceptance
  criteria and the user story in CUSTOM fields, which a plain getJiraIssue
  call misses entirely — this skill resolves those field IDs from profile.yml
  (discovering them by label the first time), fetches every required field,
  retrieves each subtask in parallel, and outputs a structured summary ready
  for implementation.
  Invoke whenever the user references an ticket number and wants to
  read, implement, review, or understand any story — whether they say
  "fetch", "load", "pull up", "what does PROJ-XXXXX say", or just
  "starting work on PROJ-XXXXX".
argument-hint: Jira ticket key (e.g.)
---

# Jira Story Fetch

Fetches a complete picture of a Jira story from your configured instance.
Use this before starting implementation work on any ticket.

## Step 0 — Normalize the ticket key

The user may pass the key in any of these formats — normalize to uppercase with a hyphen before calling the API:

| Input | Normalized |
|---|---|
| `PROJ-68433` | `PROJ-68433` |
| `proj-68433` | `PROJ-68433` |
| `PROJ 68433` | `PROJ-68433` |
| `68433` | `PROJ-68433` |

## Step 1 — Fetch the parent story

Call `getJiraIssue` with **`fields: ["*all"]`** to get all standard and custom fields in one request:

```
cloudId:  your-org.atlassian.net
issueKey: {normalized key}
fields:   ["*all"]
responseContentFormat: markdown
```

Extract the following from the response:

| Field | Location in response | Purpose |
|---|---|---|
| Summary | `fields.summary` | Story title |
| User Story | `fields.{story_description}` | "As a..." statement |
| Acceptance Criteria / Description | `fields.{acceptance_criteria}` | Main requirements body — AC, endpoints, mappings, rules |
| Sprint | `fields.{sprint}[0].name` | Extract sprint number for migration naming (see note below) |
| Story Points | `fields.{story_points}` | Sizing reference |
| Status | `fields.status.name` | Current workflow state |
| Assignee | `fields.assignee.displayName` | Owner |
| Parent / Epic | `fields.parent.key` + `fields.parent.fields.summary` | Epic context |
| Subtasks | `fields.subtasks[]` | Dev task keys + summaries |
| Comments | `fields.comment.comments[]` | PM clarifications, log definitions, spec additions |

> **Note on description vs custom field:** `fields.description` is often null on Story-type issues — the actual body lives in the acceptance-criteria custom field. Always read both; use whichever is non-null.

> **Note on sprint name:** The sprint name is typically a full string like `"Sprint 288 (4/8/26–4/21/26)"`. Extract just the sprint number (e.g., `S288` or `288`) for SQL migration naming conventions.

## Step 2 — Fetch each subtask in parallel

For every key in `fields.subtasks`, call `getJiraIssue` in parallel (one call per subtask simultaneously — do not wait for each to finish before starting the next):

```
fields: ["summary", "description", "status", "assignee", "{acceptance_criteria}"]
```

Subtask `description` (and the acceptance-criteria field if present) contains the detailed implementation spec for each dev task.

## Step 3 — Present the full story

Output a structured summary in this format. **Omit any section entirely if its source data is null or empty** — don't print an empty header.

```
## {KEY} — {Summary}

**Epic:** {parent key} — {parent summary}
**Sprint:** {sprint name}  |  **Points:** {story points}  |  **Status:** {status}  |  **Assignee:** {assignee}

---
### User Story
{user-story field content}

---
### Acceptance Criteria
{acceptance-criteria field content — render as readable markdown, not raw ADF}

---
### Subtasks
| Key | Title | Status |
|---|---|---|
| PROJ-XXXXX | DEV - ... | Open |
...

### Subtask Details
#### {subtask key} — {subtask summary}
{subtask description / acceptance-criteria field}

---
### Comments
#### {author} — {date}
{comment body}
```

## Field IDs are per-instance — resolve them, never assume them

`customfield_NNNNN` IDs are assigned per Jira instance. The same number means
different things in different orgs, so a hardcoded ID silently reads the wrong
field rather than failing.

**Resolution order:**

1. Read `atlassian.fields` from the consumer repo's `profile.yml`:

   ```yaml
   atlassian:
     cloud_id: your-org.atlassian.net
     fields:
       story_description:   customfield_XXXXX
       acceptance_criteria: customfield_XXXXX
       sprint:              customfield_XXXXX
       story_points:        customfield_XXXXX
       epic_link:           customfield_XXXXX
   ```

2. **If the profile does not declare them**, discover them once:

   ```
   getJiraIssue  issueKey: <any story in the project>  expand: names
   ```

   The `names` map returns the human label for every `customfield_NNNNN`. Match
   on the labels ("Acceptance Criteria", "Story Description", "Sprint", "Story
   Points", "Epic Link" — your instance's wording may differ).

3. **Report what you found and tell the user to record it in `profile.yml`**, so
   the discovery does not repeat on every call.

If a field cannot be resolved, say which one and continue with the rest — never
substitute a guessed ID.
