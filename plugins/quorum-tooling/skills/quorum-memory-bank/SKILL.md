---
name: quorum-memory-bank
argument-hint: <init|update|add-pattern|decision|query|cleanup|obsidian>
description: Maintain a project memory bank of patterns, decisions, architecture, and troubleshooting docs
---

# Memory Bank

Maintain a per-project memory bank that documents patterns, decisions, architecture, and troubleshooting solutions. It is persistent context for Claude Code across sessions: what the code actually does, why it was decided that way, and what has already gone wrong.

The bank is plain Markdown throughout. Where it lives and what shape the notes take are set once by `/quorum-init` and recorded in `.claude/profile.yml` — in the repository and committed with the code, or in an Obsidian vault outside it. See *Where the bank lives* below and resolve both before writing anything.

Under the Obsidian flavours the notes gain YAML frontmatter, `[[wikilinks]]` in each `## Related` section, and a generated `_index.md`. Nothing depends on the Obsidian app: agents still read the bank with Grep, and the vault features are a human convenience layered on plain files. Keep external links (tracker tickets, PRs, URLs) as standard Markdown links — a wikilink only resolves inside the vault.

## Usage

- `/quorum-memory-bank init` — Initialize the memory bank structure for the current project
- `/quorum-memory-bank update` — Synchronize the memory bank with recent codebase changes
- `/quorum-memory-bank add-pattern` — Interactively document a reusable code pattern
- `/quorum-memory-bank decision` — Record an architectural or technical decision
- `/quorum-memory-bank query {topic}` — Search the memory bank for relevant context
- `/quorum-memory-bank cleanup` — Archive obsolete content and consolidate the memory bank
- `/quorum-memory-bank obsidian [lint]` — Upgrade the bank in place to Obsidian-flavored Markdown (frontmatter + `[[wikilinks]]` + `_index.md`), or lint its links
- `/quorum-memory-bank` (no args) — Same as `update`

## Memory Bank Structure

```
<memory-bank>/
├── architecture/       # System structure, component relationships, data flow
├── decisions/          # Technical decisions and ADRs (Architecture Decision Records)
├── patterns/           # Reusable code patterns and conventions
└── troubleshooting/    # Known issues, root causes, and solutions
```

Each category may also contain an `_archived/` subdirectory for obsolete content.

## Project Context

Read `.claude/quorum-config.json` if it exists to get the `ApplicationName`. Use this in summaries and reports. If it doesn't exist, infer the project name from the repository root directory name.

## Where the bank lives, and in what flavour

Resolve both from `.claude/profile.yml` before doing anything, in every mode:

| Question | Field | Default when absent |
|---|---|---|
| Is there a bank at all? | `memory_bank.enabled` | `true` |
| Where is it? | `paths.memory_bank` | `.claude/memory-bank` |
| What flavour? | `memory_bank.mode` | `local` |
| Which vault? | `memory_bank.vault.*` | not applicable |

`paths.memory_bank` is the answer to *where* in all three modes — under `vault`
it points into the vault, which is what lets every agent that already reads it
keep working unchanged. `memory_bank.mode` only says what shape the notes take.

**`enabled: false` means stop.** The repository decided once that it does not
keep a bank; asking again each session is how a recorded decision gets undone
by attrition. Say the bank is disabled and where to change it, then stop.

**`mode: obsidian` or `vault` means every note you write carries frontmatter
and `[[wikilinks]]` from the moment it is written** — do not write plain notes
and convert later. A bank half in one shape and half in the other has to be
migrated exactly once more than one written correctly.

When there is no profile at all, use the defaults above and say which ones you
assumed. Guessing silently is how a second bank appears in a second location.

---

## Init Mode

When the argument is `init`:

1. **Create the directory structure:**
   ```
   <memory-bank>/
   <memory-bank>/architecture/
   <memory-bank>/decisions/
   <memory-bank>/patterns/
   <memory-bank>/troubleshooting/
   ```

   where `<memory-bank>` is the path resolved above — NOT a literal
   `.claude/memory-bank`, which would put the bank back in the repository for
   every operator who chose a vault.

2. **Start from the profile, not from scratch.**

   Read `.claude/profile.yml` first. If `/quorum-init` has run, the stack, test
   tooling, commands, layout and generated-file patterns are already established
   from evidence — reuse them rather than re-deriving them differently. Two
   answers to "what stack is this" that disagree are worse than one.

   When there is no profile, say so and offer to run `/quorum-init` before
   continuing. Proceeding without it is supported, but the bank you produce will
   be a scan rather than a record, and nothing downstream will share its
   conclusions.

   `/quorum-init` also settles WHERE the bank goes and in what flavour, with the
   trade stated (in-repo notes are reviewed with the code and travel with a
   clone; a vault survives across repositories and appears in no diff). Running
   `init` here without that decision defaults to `local` in this repository —
   which is a fine default and a poor surprise, so name it.

3. **Scan only for what the profile does not cover.**

   When `/quorum-init` has run, the profile already holds the component map,
   the entry points, the datastores, the characteristics, and the
   machine-readable conventions (test globs, test-name extraction, verified
   commands). **Read them; do not re-derive them.** This skill used to discover
   all of that itself, which meant two skills could reach different conclusions
   about the same repository and neither could tell which was current.

   What is genuinely left for this step:
   - **Data flow between components** — how a request or a job actually moves
     through the parts the profile names. The profile records the parts; it
     does not record the traffic between them.
   - **The prose conventions Step 2 observed but did not flatten** — naming,
     error handling, component shape, import ordering. If discovery recorded
     them, write those; if it did not, derive them here with a file and line
     for each, because a convention stated without an example is a preference.

   When there is no profile at all, do the whole scan here and say so — the
   result is a scan rather than a shared record, and nothing downstream will
   agree with it.

4. **Create initial architecture doc:**

   Write `<memory-bank>/architecture/overview.md`:
   ```markdown
   # Project Overview: {ApplicationName}

   **Generated:** YYYY-MM-DD

   ## Tech Stack
   - [Languages, frameworks, libraries identified]

   ## Project Structure
   - [Key directories and their purposes]

   ## Key Components
   - [Main modules/services and what they do]

   ## Data Flow
   - [How data moves through the system]

   ## Build & Deploy
   - [Build tools, deployment process if identifiable]
   ```

5. **Report** what was created and suggest areas to document further.

---

## Update Mode

When the argument is `update` or no argument is provided:

### Step 1: Review Recent Changes

1. **Check git history:**
   ```bash
   git log --oneline -n 20
   git diff HEAD~10..HEAD --stat
   ```

2. **Identify significant changes:** new features, modified components, new patterns, bug fixes, architecture changes, refactoring.

### Step 2: Review Current Memory Bank

1. Read existing docs in each category directory
2. Identify gaps: new patterns not documented, outdated docs, missing decisions, unrecorded troubleshooting solutions

### Step 3: Update Documentation

Create or update files as needed using the templates defined in the Document Templates section below.

### Step 4: Archive Obsolete Content

1. Create `_archived/` subdirectory within the relevant category
2. Move obsolete files there with an "ARCHIVED" prefix
3. Add archive date and reason in the file header
4. Update cross-references in remaining docs

### Step 5: Validate Consistency

1. **Cross-references:** Ensure links between docs are valid
2. **Examples:** Verify code examples match current implementation
3. **File paths:** Check that referenced paths still exist
4. **Dates:** Ensure dates are accurate

### Step 6: Report Changes

```markdown
## Memory Bank Update Complete — {ApplicationName}

### Files Created
- `{category}/{filename}.md` — {Brief description}

### Files Updated
- `{category}/{filename}.md` — {What changed}

### Files Archived
- `_archived/{filename}.md` — {Why archived}

### Coverage Gaps
{Note any areas that still need documentation}

### Recommendations
{Suggest additional documentation if needed}
```

---

## Add Pattern Mode

When the argument is `add-pattern`:

### Step 1: Understand the Pattern

Ask the user:
1. **What problem does it solve?** — scenario, when to use it
2. **What is the implementation?** — code example, key components, dependencies
3. **What are the benefits?** — why use this pattern
4. **What are common mistakes?** — pitfalls and anti-patterns

### Step 2: Search for Existing Implementation

Find real examples in the codebase:
1. Use Grep/Glob to find similar implementations
2. Extract the clearest, most current example
3. Use actual code from the project, not hypothetical examples

### Step 3: Create Pattern Document

**File:** `<memory-bank>/patterns/{pattern-name}.md` (kebab-case)

```markdown
# Pattern: {Clear Pattern Name}

## When to Use

{Describe the scenario where this pattern applies}

Use this pattern when:
- {Condition 1}
- {Condition 2}

Don't use this pattern when:
- {When it doesn't apply}

## Implementation

### Prerequisites
- {Required dependencies or setup}

### Code Example

{Actual code from the project — real, working example with comments}

### Step-by-Step
1. {Step 1 with code}
2. {Step 2 with code}
3. {Step 3 with code}

## Benefits
- {Benefit 1} — {Why this matters}
- {Benefit 2} — {Why this matters}

## Pitfalls

### Common Mistake 1
**Wrong:**
{Show the mistake}

**Correct:**
{Show the right way}

**Why:** {Explain the issue}

## Variations
### Variation 1: {Name}
{When to use, with code example}

## Testing
{How to test code using this pattern, with example}

## Real Examples
Where this pattern is used in the codebase:
- `src/{path}/{file}` — {Brief description}

## Related
- **Patterns:** {Link to related patterns}
- **Decisions:** {Link to decisions that led to this pattern}
- **Architecture:** {Link to relevant architecture docs}
```

### Step 4: Link to Related Content

1. Update architecture docs if the pattern relates to system structure
2. Cross-reference from related patterns
3. Reference from decisions if the pattern implements a decision

### Step 5: Confirm with User

Present the created file path and a brief summary. Ask if they'd like to review or add anything.

---

## Decision Mode

When the argument is `decision`:

### Step 1: Gather Decision Context

Ask the user:
1. **What is being decided?** — technology choice, architecture pattern, convention, trade-off
2. **Why is this decision being made?** — problem being solved, context
3. **What alternatives were considered?** — other options and trade-offs
4. **What are the consequences?** — benefits, drawbacks, long-term implications

### Step 2: Create Decision Document

**File:** `<memory-bank>/decisions/YYYY-MM-DD-{title-slug}.md`

```markdown
# Decision: {Clear, Concise Title}

**Date:** YYYY-MM-DD
**Status:** Accepted | Proposed | Superseded | Deprecated
**Deciders:** {Who made this decision}

## Context

{Describe the situation and problem}

Forces at play:
- {Technical constraints}
- {Business requirements}
- {Team capabilities}
- {Timeline considerations}

## Decision

{State the decision clearly and concisely}

We will {action/choice} because {primary reason}.

### Details
{Specific details about the implementation}

## Consequences

### Positive
- {Benefit 1}
- {Benefit 2}

### Negative
- {Trade-off 1}
- {Limitation 1}

### Neutral
- {Impact 1}

## Alternatives Considered

### Alternative 1: {Name}
**Pros:** {advantages}
**Cons:** {disadvantages}
**Why not chosen:** {reason}

### Alternative 2: {Name}
**Pros:** {advantages}
**Cons:** {disadvantages}
**Why not chosen:** {reason}

## Implementation
- [ ] {Step 1}
- [ ] {Step 2}

## Related
- **Patterns:** {Link to related patterns}
- **Architecture:** {Link to architecture docs}
- **Decisions:** {Link to related decisions}
- **Supersedes:** {If this replaces a previous decision}
```

### Step 3: Link to Related Documentation

1. Update architecture docs if the decision affects system architecture
2. Update pattern docs if the decision establishes new patterns
3. If this supersedes a previous decision, mark the old one as "Superseded" and link between them

### Step 4: Confirm with User

Present the created file path and summary. Note any follow-up implementation tasks.

---

## Query Mode

When the argument starts with `query`:

Everything after `query` is the topic to search for. Example: `/quorum-memory-bank query form validation`

### Step 1: Understand the Query

Analyze the topic to determine:
- What category it belongs to (patterns, decisions, architecture, troubleshooting)
- What specific information is being sought
- What level of detail is needed

### Step 2: Search Memory Bank

Search `<memory-bank>/` across all categories:
1. Use Glob to find relevant files by name
2. Use Grep to search for keywords within files
3. Read matching files to gather context

### Step 3: Synthesize Response

Provide a focused response including:
1. **Direct answer** — address the specific query
2. **Relevant patterns** — show applicable code patterns
3. **Related decisions** — link to architectural decisions
4. **Architecture context** — explain how it fits in the system
5. **Common issues** — note any troubleshooting items
6. **Code examples** — show actual examples from the memory bank
7. **Source files** — list which memory bank files the answer came from

### Step 4: Handle Missing Information

If the memory bank doesn't have information:
1. Acknowledge the gap: "This isn't documented in the memory bank yet."
2. Search the codebase directly to find the answer
3. Offer to document the findings using `add-pattern` or `decision`
4. Provide guidance based on what was found in the code

---

## Cleanup Mode

When the argument is `cleanup`:

### Step 1: Review Current State

List all content in `<memory-bank>/` and categorize each item as:
- **Active and current** — keep
- **Completed/stable** — candidate for archival
- **Outdated** — should be archived
- **Duplicate/overlapping** — candidate for consolidation

### Step 2: Identify Archive Candidates

Look for:
- **Completed features:** fully implemented and stable, no longer actively developing
- **Superseded decisions:** replaced by newer decisions
- **Obsolete patterns:** no longer used in codebase or replaced by better patterns
- **Resolved issues:** troubleshooting entries for permanently fixed issues

### Step 3: Create Archive Structure

Ensure `_archived/` subdirectories exist in each category:
```
<memory-bank>/decisions/_archived/
<memory-bank>/patterns/_archived/
<memory-bank>/architecture/_archived/
<memory-bank>/troubleshooting/_archived/
```

### Step 4: Archive Content

For each item to archive:
1. Add archive header to the file:
   ```markdown
   # ARCHIVED: {Original Title}

   **Archived Date:** YYYY-MM-DD
   **Archived Reason:** {Why this was archived}
   **Replaced By:** {Link to replacement, if any}

   ---
   {Original content follows}
   ```
2. Move to the `_archived/` subdirectory
3. Update cross-references in remaining active docs

### Step 5: Consolidate Similar Content

- Merge similar patterns into one comprehensive document
- Combine related decisions that are better understood together
- Consolidate troubleshooting entries with the same root cause

### Step 6: Clean Up Active Content

For content that stays active:
- Remove temporary notes and completed TODOs
- Update stale code examples to match current implementation
- Fix broken file path references
- Ensure consistent formatting

### Step 7: Report Cleanup Results

```markdown
## Memory Bank Cleanup Complete — {ApplicationName}

### Archived
- `{category}/_archived/{file}.md` — {Reason}

### Updated
- `{category}/{file}.md` — {What changed}

### Consolidated
- Merged {file-a} and {file-b} into {new-file}

### Removed
- `{file}.md` — {Reason for removal}

### Current State
- {X} active decisions
- {Y} active patterns
- {Z} architecture docs
- {N} troubleshooting entries
- {M} archived items
```

---

## Obsidian Mode

When the argument is `obsidian` (optionally `obsidian lint`):

Upgrade the memory bank **in place** to Obsidian-flavored Markdown so it opens as an Obsidian vault — without depending on the Obsidian app or CLI (agents keep reading it via Grep; opening it in Obsidian is an optional human convenience for the backlink graph). The adapter is **idempotent** and never clobbers existing frontmatter values.

It does three things:
1. **Frontmatter** — injects YAML frontmatter (`kind` from the folder, `title` from the H1, `status`/`created`/`updated` parsed from the body where present, `tags`). Adds only missing keys when a note already has frontmatter.
2. **Links** — rewrites references inside each `## Related` section into `[[wikilinks]]` (relative `*.md` links and `` `backtick-wrapped` `` known note names); leaves external URLs as standard Markdown links.
3. **Index** — regenerates `<memory-bank>/_index.md`, a Map-of-Content grouped by category (newest-first), which gives humans and agents a single navigable entry point.

### Step 1: Resolve the adapter script

The script ships with this skill. **Resolve it at runtime — never type an install path.** Read `~/.claude/plugins/installed_plugins.json` and take `plugins["quorum-tooling@quorum-plugins"][].installPath`; the file is at `<installPath>/skills/quorum-memory-bank/scripts/memory-bank-to-obsidian.ps1` **Check that file exists before using it** — a version bump leaves the old path in place, and a registry entry pointing at a directory that is gone resolves silently to nothing, which is the same failure as a wrong root. If it is missing, fall through.. The runtime writes that record at install time, so it survives layout changes and version bumps. If the entry is missing, Glob `path` `~/.claude/plugins/cache` (an inference about the runtime's layout, observed on format version 2 of the registry — the registry itself is the fact) with `pattern` `**/quorum-memory-bank/**/memory-bank-to-obsidian.ps1` — the middle `**` is load-bearing, because the install path carries a version segment. Do not Glob the parent `~/.claude/plugins`: a marketplace clone sits beside the installed copies there, so it returns two files of which only one is loaded. No match, or more than one with no installPath to break the tie: STOP and report what you found — the adapter is best-effort, but reading the wrong copy of it is not.

### Step 2: Resolve the memory-bank path

Use the path resolved in *Where the bank lives* above — `{{profile.paths.memory_bank}}`, defaulting to `.claude/memory-bank`. Under `mode: vault` this is a path outside the repository, and that is correct: the adapter rewrites notes wherever they are.

### Step 3: Run

```
# migrate (default)
pwsh -NoProfile -File <script> -Path <memory-bank-path>
# lint only (read-only; exits non-zero if any [[wikilink]] is broken)
pwsh -NoProfile -File <script> -Path <memory-bank-path> -Mode lint
```

Prefer `pwsh` (PowerShell 7, cross-platform); on Windows-only setups `powershell` (5.1) also works. Report what was rewritten and whether `_index.md` changed.

### Conventions & limits

- **Requires PowerShell on PATH** (`pwsh` on macOS/Linux, `pwsh`/`powershell` on Windows). Consumers without it keep the bank as plain Markdown — there is no automatic file-watcher; normalization runs only when you invoke this subcommand (or the orchestrator's documenter/synchronizer agents do).
- **Notes link by filename stem, so stems must be globally unique** across `architecture/ decisions/ patterns/ troubleshooting/` — two `overview.md` in different folders collide (`[[overview]]` is ambiguous). The adapter warns on duplicates; rename to resolve.
- **Only `## Related` / `## See also` sections are linkified** (any heading level). Put cross-references there, or they won't be turned into `[[wikilinks]]`. External URLs (the tracker/PRs) stay as standard Markdown links.
- **Frontmatter dates:** `created` is set once (from a body `**Date:**`/`**Generated:**` or the run date) and never clobbered; `kind` is corrected to match the folder; `updated` advances to the run date only when a note is actually rewritten (a no-op run leaves it alone, so re-running is safe).

---

## Document Templates

### Pattern Template
**File:** `<memory-bank>/patterns/{pattern-name}.md`

See the full template in the Add Pattern Mode section above.

### Decision Template
**File:** `<memory-bank>/decisions/YYYY-MM-DD-{title}.md`

See the full template in the Decision Mode section above.

### Architecture Template
**File:** `<memory-bank>/architecture/{component}.md`

```markdown
# {Component/System Name}

## Overview
{High-level description}

## Structure
{Organization and layout}

## Key Components
- {Component A}: {Purpose}
- {Component B}: {Purpose}

## Data Flow
{How data moves through this part of the system}

## Related
- {Links to decisions, patterns}
```

### Troubleshooting Template
**File:** `<memory-bank>/troubleshooting/{issue-name}.md`

```markdown
# {Problem Title}

## Problem
{Description of the issue}

## Symptoms
- {Error messages}
- {Unexpected behavior}

## Root Cause
{What actually caused this}

## Solution
{Step-by-step fix}

## Prevention
{How to avoid this in the future}
```

---

## Documentation Standards

- **Be specific:** Document concrete patterns, not vague ideas
- **Use real code:** Include actual examples from the project, not hypothetical code
- **Link related content:** Connect patterns, decisions, and architecture
- **Keep concise:** Focus on "why" and "how," not just "what"
- **Date everything:** Track when decisions were made
- **Archive, don't delete:** Maintain history for reference
- **Update regularly:** Don't let the memory bank get stale

## What NOT to Document

- Implementation details better suited for code comments
- Temporary workarounds (unless documenting for planned removal)
- Obvious language or framework features
- IDE or tooling preferences
- Personal notes or TODOs
