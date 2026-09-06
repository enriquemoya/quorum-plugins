---
argument-hint: <TICKET-KEY> [--complexity simple|medium|complex] [--skip-e2e] [--skip-env] [--resume] [--dry-run] [--include-subtasks]
description: End-to-end ticket delivery orchestrator. Drives a Jira ticket through the full pipeline (fetch → analyze → plan → implement → test → review → PR) with human approval gates at every phase.
---

# Orchestrate Command

Orchestrate the full delivery pipeline for a Jira ticket, from initial context gathering through to a PR-ready state.

## Profile

This command is stack-agnostic. The orchestrator agent (`agents/quorum-orchestrator.md`, **bundled with this plugin — it is NOT checked into the consumer repo**) reads the consumer repo's `.claude/profile.yml` to resolve `{{role:*}}` references and `{{profile.*}}` paths/commands. Null roles are skipped silently with an announcement at the relevant phase. See the bundled `PROFILE_SCHEMA.md` (ships with this plugin, alongside the agent file) for the full contract.

## Usage

```
/quorum-orchestrate PROJ-68500
/quorum-orchestrate PROJ-68500 --complexity simple
/quorum-orchestrate PROJ-68500 --resume
/quorum-orchestrate PROJ-68500 --dry-run
/quorum-orchestrate PROJ-68500 --include-subtasks
```

## What This Does

Runs a 7-phase governed pipeline with human approval at every transition. Phases 1–3 stay investigation-only by convention + Cardinal Rules + per-gate HARD STOP, not by a tool-restriction mode-switch.

```
Phase 1: Fetch & Context        → Gate 1: Context Approval
Phase 2: Analysis & Planning    → Gate 2: Plan Approval
Phase 3: Plan Confirmation      → Gate 3: Go / No-Go
Phase 4: Implementation         → Gate 4: Implementation Review
Phase 5: Testing & Quality      → Gate 5: Quality Approval
Phase 6: Code Review            → Gate 6: Review Approval
Phase 7: PR Delivery            → Sub-gate 7a (local) → Sub-gate 7b (external actions)
```

Complexity auto-detection adjusts the pipeline:
- **Simple** tickets skip quorum-ticket-analyzer agent (skill mapping is inline), auto-approve Gate 3, and skip E2E checks. Prompt generation ALWAYS runs.
- **Medium** tickets run the full pipeline
- **Complex** tickets run everything with extra architectural analysis

## Workflow Position

This command replaces the manual sequence of:
```
/quorum-prompt-gen → /context-query → implement → /quorum-validate-ticket → /e2e-coverage-check → consumer's code-review skill → /quorum-pr-template
```

The orchestrator runs all of these automatically with gates between them.

## CRITICAL: Pipeline Enforcement

When `/quorum-orchestrate` is invoked, you MUST follow the 7-phase governed pipeline defined in the plugin's bundled `agents/quorum-orchestrator.md` **exactly**. This is non-negotiable:

1. **You ARE the orchestrator** — do not improvise a different flow, do not use generic plan-mode workflows, do not skip phases.
2. **Follow the agent definition phase by phase** — read the plugin's bundled `agents/quorum-orchestrator.md` (see Initialization step 4 for how to locate it) and execute each phase in order.
3. **Print the state tracker** before every gate (Cardinal Rule 6).
4. **HARD STOP at every gate** — wait for explicit human approval. Do not auto-advance.
5. **Generate the prompt file in Phase 2** — prompts are NEVER skipped, regardless of complexity. This is a persistent documentation artifact.
6. **Complete all 7 phases** — the pipeline runs to completion (or until the human aborts). Do not stop at Phase 4 and call it done.

If you find yourself about to skip a phase or gate, STOP and re-read the agent definition.

## Process

### Initialization

1. Validate the ticket key format (`PROJ-NNNNN`)
2. Check for `--resume` flag → look for existing artifacts
3. Parse optional flags
4. **Read the orchestrator agent definition** — this is your operating manual for the entire pipeline. It ships **inside the `quorum-orchestrator` plugin** and is **NOT** present in the consumer repo, so do **not** try to read `.claude/agents/quorum-orchestrator.md` from the repo root — that path does not exist there and the read will fail. Locate the bundled file with a Glob **rooted at the plugin cache** — a default, project-rooted Glob will NOT find it (the plugin is installed under your home directory, outside the repo):
   - Glob `path`: your home `.claude/plugins/cache` directory (e.g. `C:\Users\<you>\.claude\plugins\cache`; macOS/Linux `~/.claude/plugins/cache`)
   - Glob `pattern`: `**/quorum-orchestrator/**/agents/quorum-orchestrator.md`
   - Read the single match (e.g. `…/.claude/plugins/cache/quorum-plugins/quorum-orchestrator/<version>/agents/quorum-orchestrator.md`). The `<version>` and marketplace-name segments are resolved by the Glob, so this stays version- and install-agnostic.

### Execution

Follow the 7-phase pipeline in the plugin's bundled `agents/quorum-orchestrator.md` exactly:
- Phases 1-3 stay investigation-only by convention + Cardinal Rules
- Phase 2 ALWAYS generates a prompt file (`.claude/prompts/{TICKET-KEY}-{DATE}.md` — transient/gitignored; posted to the Jira ticket as a comment at Sub-phase 7b, not committed)
- HARD STOP gate at every phase boundary (Cardinal Rule 5)

The orchestrator agent manages all 7 phases, delegating to specialized agents:

| Phase | Delegates to |
|-------|-------------|
| 1 — Fetch & Context | Atlassian MCP, `/context-query` command, **quorum-ticket-image-analyzer** agent (if images), **{{role:env-validator}}** (skipped silently if null) |
| 2 — Analysis & Planning | **quorum-ticket-analyzer** agent, **quorum-prompt-builder** agent |
| 3 — Plan Approval | (Human gate — no delegation) |
| 4 — Implementation | **{{role:primary-stack-expert}}**, **{{role:secondary-stack-expert}}** (skipped if null), **{{role:code-searcher}}** (skipped if null) |
| 5 — Testing & Quality | `/quorum-validate-ticket`, `/e2e-coverage-check`, **quorum-test-specialist** agent (which delegates to **{{role:unit-tests-gen}}** / **{{role:integration-tests-gen}}** / **{{role:e2e-tests-gen}}** per profile), **quorum-memory-synchronizer** agent |
| 6 — Code Review | consumer's code-review skill, **{{role:env-validator}}** (skipped if null) |
| 7 — PR Delivery | `/quorum-pr-template` (delegates to **quorum-pr-generator** agent), **quorum-qa-handoff-publisher** agent for the Dev→QA handoff package (combines auto-test inventory + `{{role:qa-handoff}}` manual cases into `qa_automation_tests.md` and creates the "Review Automation Tests" Jira subtask) |

### Human Gates

The orchestrator pauses at every phase boundary. At each gate you can:
- **Approve** → proceed to next phase
- **Request changes** → orchestrator adjusts and re-presents
- **Ask questions** → orchestrator answers using memory bank + codebase
- **Abort** → orchestrator stops and records state for later resume

### Complexity Auto-Detection

After fetching the ticket, the orchestrator classifies it:

| Complexity | Criteria | Pipeline Adjustments |
|------------|----------|---------------------|
| Simple | Single file, text change, no architecture impact | Skip quorum-ticket-analyzer agent (skill mapping inline), auto-approve plan, lite testing. Prompt generation ALWAYS runs. |
| Medium | 2–5 files, limited architecture impact | Full pipeline |
| Complex | 6+ files, new patterns, architectural changes | Full pipeline + extra analysis |

Override with `--complexity simple|medium|complex`.

## Flags

| Flag | Description |
|------|-------------|
| `--complexity` | Override auto-detection: `simple`, `medium`, or `complex` |
| `--skip-e2e` | Skip E2E coverage check even for Medium/Complex tickets |
| `--skip-env` | Skip environment validation checks |
| `--resume` | Resume from the last incomplete phase |
| `--dry-run` | Run Phases 1–3 only — stop after Gate 3, never advance to Phase 4 |
| `--include-subtasks` | Include Jira subtasks in ticket analysis |

## Output Artifacts

Depending on complexity and pipeline phases, the orchestrator produces:

| Artifact | Local path (transient working copy) | Phase | Durable home |
|----------|----------|-------|------|
| Investigation prompt | `.claude/prompts/{TICKET-KEY}-{DATE}.md` (gitignored) | Phase 2 | **Jira comment** on the ticket (posted at 7b) |
| Validation report | `.claude/validations/{TICKET-KEY}-{DATE}.md` (gitignored) | Phase 5 | **Jira comment** on the ticket (posted at 7b) |
| PR template | `.claude/pr-templates/{TICKET-KEY}-{DATE}.md` (gitignored) | Phase 7 | **Pasted into the PR** description |
| QA handoff | `.claude/qa-handoff/{TICKET-KEY}/qa_automation_tests.md` (gitignored) | Phase 7 | **"Review Automation Tests" subtask** body |
| Scaffolded E2E tests | `{{profile.paths.e2e_spec_root}}/{module}/{Feature}{{profile.e2e.spec_extension}}` (skipped if no e2e role) | Phase 5 | **Committed** to the repo |
| Code review | `{{profile.paths.reviews}}/.../review_{N}.md` | Phase 6 | **Committed** to the repo |
| Memory bank updates | `{{profile.paths.memory_bank}}/patterns/*.md` | Phase 5 | **Committed** to the repo |

## Examples

### Standard ticket
```
/quorum-orchestrate PROJ-68500
# Runs full pipeline with auto-detected complexity
```

### Quick fix (force simple)
```
/quorum-orchestrate PROJ-68501 --complexity simple
# Skips prompt generation, auto-approves plan, lite testing
```

### Resume interrupted work
```
/quorum-orchestrate PROJ-68500 --resume
# Detects existing artifacts, resumes from last incomplete phase
```

### Planning only (no code changes)
```
/quorum-orchestrate PROJ-68502 --dry-run
# Runs Phases 1-3 only; stops after Gate 3. Only file write is the prompt artifact in Phase 2.
```

## Agent Used

- **orchestrator** — `quorum-orchestrator/agents/quorum-orchestrator.md` (bundled with this plugin; located via Glob — see Initialization step 4)

## Error Handling

- **Invalid ticket key:** "Expected format: PROJ-NNNNN"
- **Jira connection failure:** Offers manual ticket description input
- **Agent failure:** Reports which agent failed, offers retry or skip
- **Human abort:** Records state for later `--resume`
