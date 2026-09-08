---
name: quorum-create-branch
description: Create a git branch for PR work following the project naming conventions
---

# Create Git Branch

Create a properly named git branch for PR work following the project branch naming convention: `{prefix}/{ticket_id}_{description}`.

## Branch Naming Convention

Format: `{prefix}/{PROJ-XXXXX}_{task_description}`

- **Prefix:** One of `hotfix`, `bugfix`, `feature`, `release`
- **Ticket ID:** Jira ticket number with a hyphen (e.g., `PROJ-12345`)
- **Description:** Lowercase words separated by underscores (e.g., `add_payment_validation`)

Example: `feature/PROJ-112233_task_description`

## Workflow

### Step 1: Gather Information from User

Prompt the user for the following (accept all in one prompt if possible):

1. **Branch prefix** — Ask user to choose: `hotfix`, `bugfix`, `feature`, or `release`
2. **Jira ticket number** — e.g., `PROJ-12345`. Validate it matches the pattern `PROJ-\d+`
3. **Source branch** — Default is `Develop`. Ask if they want a different source branch.

### Step 2: Get Task Description from Jira

1. Attempt to fetch the Jira ticket summary using `getJiraIssue` MCP tool with the ticket number from Step 1, requesting the `summary` field.
2. **If Jira is accessible:**
   - Extract the ticket summary
   - Convert to a branch-friendly description: lowercase, replace spaces and special characters with underscores, remove consecutive underscores, trim trailing underscores
   - Present the generated branch name to the user and ask for confirmation or modification
3. **If Jira is NOT accessible** (MCP tool fails or times out):
   - Inform the user that Jira could not be reached
   - Ask the user to provide a short task description
   - Convert their input to branch-friendly format (same rules as above)

### Step 3: Update Source Branch

1. Run `git fetch origin` to get latest remote refs
2. Run `git checkout {source_branch}` to switch to the source branch
3. Run `git pull origin {source_branch}` to pull latest changes
4. If any of these fail, stop and report the error to the user

### Step 4: Create the Branch

1. Construct the branch name: `{prefix}/{ticket_id}_{description}`
2. Run `git checkout -b {branch_name}` to create and switch to the new branch
3. Verify creation with `git branch --show-current`

### Step 5: Confirm

Display the result:
```
Branch created: {branch_name}
Source branch: {source_branch}
Ticket: PROJ-XXXXX ({{ticket_url}})
```

## Description Formatting Rules

When converting a Jira summary or user input to a branch description:
- Convert to lowercase
- Replace spaces with underscores
- Remove any characters that are not alphanumeric or underscores
- Collapse multiple consecutive underscores to a single underscore
- Trim leading/trailing underscores
- Truncate to 60 characters max (to keep branch names reasonable)

## Error Handling

- If the source branch doesn't exist, inform the user and ask for correction
- If there are uncommitted changes, warn the user and ask if they want to stash or abort
- If the branch name already exists, inform the user and ask how to proceed
