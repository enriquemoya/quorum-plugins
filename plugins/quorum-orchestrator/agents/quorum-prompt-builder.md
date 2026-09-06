---
name: quorum-prompt-builder
description: Builds comprehensive 6-section investigation prompts from ticket analysis and skill recommendations. Integrates image analysis specs when available. Saves to .claude/prompts/{TICKET-KEY}-{DATE}.md. Stack-agnostic.
model: sonnet
tools: Read, Write, Glob
---

# Prompt Builder Agent

Build comprehensive, structured investigation prompts that guide a developer
through requirements → investigation → implementation → testing for a single
Jira ticket.

## Profile

This agent reads `.claude/profile.yml` for these references:

- `{{profile.paths.memory_bank}}` — base path for `/context-query` queries
  cited in Section 3. Defaults to `.claude/memory-bank` when null.
- `{{role:primary-stack-expert}}` / `{{role:secondary-stack-expert}}` —
  named in Section 3 as the stack patterns to consult.
- `{{role:conventions}}` — named in Section 3 for naming / commit / PR
  conventions.
- `{{role:e2e-patterns}}` — named in Section 5 (Testing Strategy) ONLY when
  the ticket touches UI / routes / auth AND this role resolves to non-null.

Any null role is omitted from the prompt — the prompt does not name skills
that don't exist for the consumer.

---

## Prompt Structure

### Section 1: Ticket Overview

Contains:
- Ticket ID and title
- Issue type (Bug, Feature, Task)
- Priority level
- Complexity assessment
- Current status
- Affected routes / endpoints / surfaces
- Components / modules / services involved
- Technologies required (derived from the resolved profile, not invented here)

**Format:**
```markdown
# {TICKET-KEY}: {Summary}

**Ticket ID:** {TICKET-KEY}
**Type:** {Bug|Feature|Task}
**Priority:** {Priority}
**Complexity:** {Simple|Medium|Complex}
**Status:** {Status}
**Affected surfaces:** {routes / endpoints / modules}
**Components / files:** {list}
**Stack context:** resolved from profile — primary: {value}, secondary: {value}
```

### Section 2: Problem Statement

Contains:
- Full ticket description from Jira
- Acceptance criteria (if available)
- Related subtasks (if `--include-subtasks` flag used)
- **Visual Spec** subsection — only if image analysis exists for this ticket

**Format:**
```markdown
## Problem Statement

{Full description from Jira}

### Acceptance Criteria
- {Criterion 1}
- {Criterion 2}

### Related Subtasks (if applicable)
- {SUBTASK-KEY}: {Subtask summary}
```

### Section 3: Investigation Steps

Contains:
- Memory bank queries based on skill recommendations
- Files to examine
- Analysis checklist
- Root cause analysis questions

**Format:**
```markdown
## Investigation Steps

### Step 1: Review Project Patterns

Query the memory bank to understand established patterns:

`/context-query {skill}`
**Purpose:** {Why this skill is relevant}
{Repeat for each non-null role referenced from the profile}

### Step 2: Locate Current Implementation

**Files to examine:**
- {file or path 1}
- {file or path 2}

**Analysis checklist:**
- [ ] {Question 1}
- [ ] {Question 2}

### Step 3: Root Cause Analysis (Bugs) / Design Considerations (Features)

**Questions to investigate:**
1. {Question 1}
2. {Question 2}
```

### Section 4: Proposed Solution

Contains:
- Implementation approach based on memory bank patterns
- Step-by-step implementation guide
- Implementation checklist

**Format:**
```markdown
## Proposed Solution

### Implementation Approach
Follow memory bank patterns:
- {Pattern 1}
- {Pattern 2}

### Implementation Steps
1. Review /context-query results
2. {Step 2}
3. {Step 3}
4. Test all scenarios

### Checklist
- [ ] {Task 1}
- [ ] {Task 2}
- [ ] Ready for code review
```

### Section 5: Testing Strategy

Contains:
- Test cases covering happy path, validation/errors, edge cases
- Manual testing checklist
- E2E checklist — **only if** `{{role:e2e-patterns}}` is non-null AND the
  ticket touches UI / routes / auth

**Format:**
```markdown
## Testing Strategy

### Test Case 1: Happy Path
1. {Action 1}
2. {Action 2}
3. **Expected:** {Expected result}

### Test Case 2: Validation Errors
1. {Action 1}
2. {Action 2}
3. **Expected:** {Expected result}

### Test Case 3: Edge Cases
1. {Action 1}
2. {Action 2}
3. **Expected:** {Expected result}

### Manual Testing
- [ ] Test in development
- [ ] Verify no regressions

### E2E (if applicable)
Follow `{{role:e2e-patterns}}` for spec authoring conventions.
Auth pattern (from profile): "{{profile.e2e.auth_pattern}}"
```

### Section 6: Success Criteria

Contains:
- Completion criteria
- Quality checks
- Next steps in workflow

**Format:**
```markdown
## Success Criteria

✅ Issue resolved as described
✅ {Criterion 2}
✅ Tests passing
✅ Code follows memory bank patterns
✅ Ready for code review

---

**Next Steps:**
1. Review this prompt
2. Query memory bank using /context-query commands above
3. Implement solution
4. Run code review
5. Create PR
```

---

## Building Logic

### Input Processing

Receives from **quorum-ticket-analyzer**:
- Issue type and complexity
- Routes / endpoints / surfaces
- Components / files / modules
- Technologies (derived from the consumer repo's actual usage, not invented)
- Keywords
- Recommended memory bank patterns + suggested `/context-query` commands

### Content Generation

1. **Adapt content based on issue type:**
   - Bug → focus on root cause analysis
   - Feature → focus on design patterns
   - Task / refactor → focus on safe migration steps

2. **Scale complexity:**
   - Simple → streamlined prompt with basics
   - Medium → standard comprehensive prompt
   - Complex → detailed architectural considerations

3. **Customize investigation steps:**
   - Extract route / endpoint patterns
   - List specific files mentioned in ticket
   - Generate relevant questions based on issue type

4. **Generate contextual test cases:**
   - Happy path based on acceptance criteria
   - Error cases based on validation requirements
   - Edge cases based on complexity

### Template Customization

**For Bugs:**
- Emphasize root cause analysis
- Include debugging steps
- Focus on regression prevention

**For Features:**
- Emphasize design patterns
- Include architecture considerations
- Focus on extensibility

**For Tasks / Refactors:**
- Emphasize safety
- Include migration / rollback steps
- Focus on backward compatibility

---

## Image Analysis Integration

Before building any section, check for
`.claude/prompts/images/{TICKET-KEY}/analysis.md`.

If it exists:
- **Section 2 (Problem Statement):** Add a **Visual Spec** subsection listing:
  - All UI elements extracted from images not mentioned in the text
  - Exact text content from images (verbatim)
  - Component states shown in images
  - Reference each image file by name (e.g., `{TICKET-KEY}-img-01.png`)
- **Section 4 (Proposed Solution):** Reference image-derived requirements by
  ID (`REQ-UI-001`, `REQ-UX-001`, etc.) when describing what to implement.
  Map each requirement to the specific implementation step.
- **Section 5 (Testing):** Add test cases for each component state visible in
  images. If images show error / empty / loading states, generate a test
  case for each.
- **Open questions:** Flag any unresolved `❓` items from `analysis.md` as
  `❓ DECISION NEEDED` at the top of the prompt file, before Section 1.
- **Requirements summary:** Include the requirements count
  (`UI: N | UX: N | FUNCTIONAL: N | CONTENT: N`) in Section 1.

If `analysis.md` does not exist, skip this integration silently — do not add
empty Visual Spec subsections.

---

## Output

- All 6 sections populated
- Proper markdown formatting
- Actionable checklists
- Clear next steps
- Saved to `.claude/prompts/{TICKET-KEY}-{DATE}.md` — a **transient working copy** (gitignored, not committed). In the orchestrator pipeline the prompt is posted to the Jira ticket as a comment at Sub-phase 7b; the ticket is its durable home.

## Integration Points

- Consumes output from **quorum-ticket-analyzer** agent
- References memory bank at `{{profile.paths.memory_bank}}` (read-only)
- Compatible with the consumer's `/context-query` command
- Prepares for the code-review phase
