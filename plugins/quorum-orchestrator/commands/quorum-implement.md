---
argument-hint: "<slug> [--fix] [--skip-e2e] [--skip-env] [--dry-run]"
description: The implementation stage of the governed pipeline. Runs ONLY on a unit whose scope has been audited READY. Drives implementation → tests → code review → PR artifacts through gates, then hands back at IN_PROGRESS for the implementation audit. Invoked by /quorum-orchestrate; not an entry point.
---

# /quorum-implement — the implementation stage

Stage 7 of the pipeline in `PIPELINE.md`. It is **not** the entry point:
`/quorum-orchestrate` routes here when a unit reaches a READY-family state, and
routes elsewhere when it does not.

## Preconditions (hard)

- `status.yml` is `READY`, `READY_WITH_CONDITIONS`, or `NEEDS_FIX`. Any other
  state: REFUSE and route back to `/quorum-orchestrate`.
- `tasks.md` exists and every task maps to an acceptance criterion.
- Under `--fix`, the proposal at `last_audit.proposal_ref` is read first and its
  findings are the scope of this run — not an occasion to revisit the design.

## Handoff

On completion the unit is left at `IN_PROGRESS` with code, tests and the review
artifact committed and the PR artifacts staged locally. **This stage never
delivers.** The PR is opened by `/quorum-deliver`, after the implementation
audit returns a VERIFIED-family verdict.

---

Everything below is the stage's internal pipeline.

## Profile

This command is stack-agnostic. The orchestrator agent (`agents/quorum-orchestrator.md`, **bundled with this plugin — it is NOT checked into the consumer repo**) reads the consumer repo's `.claude/profile.yml` to resolve `{{role:*}}` references and `{{profile.*}}` paths/commands. Null roles are skipped silently with an announcement at the relevant phase. See the bundled `PROFILE_SCHEMA.md` (ships with this plugin, alongside the agent file) for the full contract.

## Usage

```
/quorum-implement invoice-export                # a slug, always
/quorum-implement invoice-export --fix          # the audit proposal is the scope
/quorum-implement invoice-export --dry-run      # read and confirm, write nothing
```

The argument is a **slug**. A unit that came from the ticket path carries its
ticket key as a field in `status.yml`, and that key is used for branch names,
commit trailers and links — but it is not how this stage is addressed. Units on
the spec path have no ticket key at all, and that is the path this stage is
reached by most.

## What This Does

Runs a 5-phase stage with a human gate at every transition — **five stops, not
the eight this document once described.** A `--human` unit that changes how
often it interrupts a person says the new number rather than leaving it to be
counted.

```
Phase 1: Read the unit, confirm scope   → Gate 1: Go / No-Go
Phase 2: Implementation                 → Gate 2: Implementation Review
Phase 3: Testing & Quality              → Gate 3: Quality Approval
Phase 4: Code Review                    → Gate 4: Review Approval
Phase 5: PR artifacts, staged locally   → Gate 5: Artifacts Approval
```

**Phase 1 reads; it does not plan.** `tasks.md` is the plan. It arrived with the
unit, every task maps to an acceptance criterion, and a scope audit already
traced it. Re-deriving it here would produce a second plan with less
information than the first, and a gate asking about a decision made two stages
earlier.

Two phases this stage used to run are gone because the pipeline runs them
upstream, each with its own audit: fetching context, which `analysis.md` and the
spec artifacts now hold, and planning, which `tasks.md` now is. One thing they
produced survives and no upstream stage replaces it — the investigation prompt,
written in Phase 1 and never skipped, whatever the complexity.

**There is no external-action gate here.** An earlier version had one, while the
Handoff section above said this stage never delivers. Delivery is
`/quorum-deliver`'s, after the implementation audit returns a VERIFIED-family
verdict. This stage stages artifacts locally and stops.

Complexity is **read from `status.yml`**, where triage recorded it. It is not
re-derived: a value computed here can disagree with the one the scope audit ran
under, and nothing downstream would know which it saw.

| Complexity | What it changes here |
|---|---|
| Simple | lighter testing; the code review still runs |
| Medium | the full stage |
| Complex | the full stage, with extra architectural attention in Phase 4 |

## Workflow Position

Stage 7 of the pipeline. It is entered from a READY-family state and leaves the
unit at `IN_PROGRESS` for the implementation audit. Within the stage, the work
that used to be a manual sequence runs with gates between the steps:

```
implement → validate → e2e coverage → consumer's code-review skill → PR artifacts
```

The two commands that used to open that sequence — prompt generation and
context query — are upstream now, except for the prompt artifact itself, which
Phase 1 still writes.

## CRITICAL: Pipeline Enforcement

Follow the phases defined in the plugin's bundled
`agents/quorum-orchestrator.md` **exactly**. This is non-negotiable:

1. **You ARE the stage** — do not improvise a different flow, do not use generic
   plan-mode workflows, do not skip phases.
2. **Follow the agent definition phase by phase** — read the bundled
   `agents/quorum-orchestrator.md` (Initialization step 4 says how to locate it)
   and execute each phase in order.
3. **Print the state tracker** before every gate.
4. **HARD STOP at every gate** — wait for explicit human approval. Do not
   auto-advance.
5. **Write the prompt file in Phase 1** — never skipped, whatever the
   complexity. It is the one artifact the removed phases produced that no
   upstream stage replaces.
6. **Do not stop early.** Phase 2 producing working code is not the end of the
   stage; the audit that follows reads tests, review and artifacts too.
7. **Do not deliver.** Opening a PR, posting to a tracker, or anything else
   visible outside this repository belongs to `/quorum-deliver`.

If you find yourself about to skip a phase or gate, STOP and re-read the agent
definition.

## Process

### Initialization

1. Read `.claude/specs/<slug>/status.yml`. The state must be in the READY
   family; anything else is a REFUSE, not a repair.
2. Read `tasks.md`. **Every task line must carry an `AC:` naming criteria that
   exist in `requirements.md`.** A task with no acceptance criterion, or one
   naming an id that is not there, means the unit was not audited as it now
   stands — REFUSE and route back to `/quorum-orchestrate`. The Preconditions
   above have always claimed this; this step is where it is actually checked.
3. Read `complexity` from `status.yml`. Do not derive it. Parse the flags.
4. **Read the orchestrator agent definition** — this is your operating manual for the entire pipeline. It ships **inside the `quorum-orchestrator` plugin** and is **NOT** present in the consumer repo, so do **not** try to read `.claude/agents/quorum-orchestrator.md` from the repo root — that path does not exist there and the read will fail. Resolve it:
   - **Ask the runtime, do not search.** Read
     `~/.claude/plugins/installed_plugins.json`. Its
     `plugins["<plugin>@<marketplace>"][].installPath` is where the live copy
     is — the runtime writes it at install time, so it is right by construction
     and stays right across layout changes.
   - **Then read `<installPath>/agents/quorum-orchestrator.md`.** **Check that file exists before using it** — a version bump leaves the old path in place, and a registry entry pointing at a directory that is gone resolves silently to nothing, which is the same failure as a wrong root. If it is missing, fall through.
   - **If that file or the entry is missing**, Glob `path`
     `~/.claude/plugins/cache` with `pattern` `**/quorum-orchestrator/**/quorum-orchestrator.md`. The middle
     `**` is load-bearing: the install path carries a version segment, so a
     pattern without it matches nothing.
   - **Do not Glob the parent `~/.claude/plugins`.** A marketplace clone lives
     beside the installed copies under that parent, so the search finds two
     files with the same name of which only one is loaded.
   - **No match: STOP and report.** Never guess a path. A Glob rooted at a
     directory that does not exist returns nothing and raises nothing, so a
     wrong root looks exactly like a missing plugin.
   - **More than one and no `installPath` to break the tie: STOP and report
     every match.**

### Execution

Follow the 5 phases in the plugin's bundled `agents/quorum-orchestrator.md`:

- **Phase 1 reads and confirms; it does not plan.** `tasks.md` is the plan.
- Phase 1 ALWAYS writes the prompt file — transient, gitignored, never skipped.
- HARD STOP at every phase boundary.

| Phase | Delegates to |
|-------|-------------|
| 1 — Read the unit, confirm scope | the spec artifacts (`requirements.md`, `analysis.md`, `tasks.md`), **quorum-prompt-builder** agent, **{{role:env-validator}}** (skipped silently if null) |
| 2 — Implementation | **{{role:primary-stack-expert}}**, **{{role:secondary-stack-expert}}** (skipped if null), **{{role:code-searcher}}** (skipped if null) |
| 3 — Testing & Quality | `/quorum-validate-ticket`, `/e2e-coverage-check`, **quorum-test-specialist** agent (which delegates to **{{role:unit-tests-gen}}** / **{{role:integration-tests-gen}}** / **{{role:e2e-tests-gen}}** per profile), **quorum-memory-synchronizer** agent |
| 4 — Code Review | consumer's code-review skill, **{{role:env-validator}}** (skipped if null) |
| 5 — PR artifacts | `/quorum-pr-template` (delegates to **quorum-pr-generator** agent), **quorum-qa-handoff-publisher** agent for the Dev→QA handoff package (combines the auto-test inventory with `{{role:qa-handoff}}` manual cases into `qa_automation_tests.md`) |

Phase 5 produces artifacts and stops. Publishing them — a PR, a tracker
comment, a follow-up issue — is `/quorum-deliver`'s work, and only after the
implementation audit passes.

An image analyser and a ticket analyser used to run in the removed phases.
Neither is invoked here any more; a unit arrives with its analysis done. Both
still ship, and the stage that fetches a ticket is triage.

### Human Gates

The orchestrator pauses at every phase boundary. At each gate you can:
- **Approve** → proceed to next phase
- **Request changes** → orchestrator adjusts and re-presents
- **Ask questions** → orchestrator answers using memory bank + codebase
- **Abort** → orchestrator stops and records state for later resume

### Complexity

Read from `status.yml`, where triage recorded it. **There is no procedure here
for computing it**, deliberately: a value derived at this stage can disagree
with the one the scope audit ran under, and every decision after it inherits
the disagreement without knowing.

| Complexity | What it changes in this stage |
|---|---|
| Simple | lighter testing in Phase 3; the code review still runs; the prompt file is still written |
| Medium | the full stage |
| Complex | the full stage, with extra architectural attention in Phase 4 |

To change it, change it at triage — where it is recorded, and where the audit
trail can see that it moved.

## Flags

| Flag | Description |
|------|-------------|
| `--fix` | Carry the implementation audit's proposal at `last_audit.proposal_ref` as this run's scope. Not an occasion to revisit the design. |
| `--skip-e2e` | Skip the E2E coverage check |
| `--skip-env` | Skip environment validation checks |
| `--dry-run` | Read the unit, confirm scope, stop at Gate 1 — **before the first phase that writes to the repository.** Described that way on purpose: a dry run pinned to a phase number stops meaning what it says the moment the phases are renumbered, which has now happened once. The prompt artifact is still written; it is transient and gitignored. |

Three flags this table used to carry are gone, and each for its own reason
rather than as a batch:

- `--complexity` — the value is read from `status.yml`. An override here can
  disagree with the value the scope audit ran under.
- `--resume` — `status.yml` holds the state and `/quorum-orchestrate` re-routes
  from it. A second resume mechanism inside one stage is a second source of
  truth about where the work is.
- `--include-subtasks` — an option of the ticket fetch, which is upstream now.

## Output Artifacts

Paths are keyed by the unit's **slug**. A unit that came from the ticket path
also carries its key, and where a name below shows `<slug>` such a unit may use
`<slug>-<key>` — but the slug is what always exists.

| Artifact | Local path (transient working copy) | Phase | Durable home |
|----------|----------|-------|------|
| Investigation prompt | `.claude/prompts/<slug>-{DATE}.md` (gitignored) | Phase 1 | `{{role:tracker}}` comment, posted by `/quorum-deliver` |
| Validation report | `.claude/validations/<slug>-{DATE}.md` (gitignored) | Phase 3 | `{{role:tracker}}` comment, posted by `/quorum-deliver` |
| PR template | `.claude/pr-templates/<slug>-{DATE}.md` (gitignored) | Phase 5 | **Pasted into the PR** description |
| QA handoff | `.claude/qa-handoff/<slug>/qa_automation_tests.md` (gitignored) | Phase 5 | a subtask on the unit's ticket, created by `/quorum-deliver` |
| Scaffolded E2E tests | `{{profile.paths.e2e_spec_root}}/{module}/{Feature}{{profile.e2e.spec_extension}}` (skipped if no e2e role) | Phase 3 | **Committed** to the repo |
| Code review | `{{profile.paths.reviews}}/.../review_{N}.md` | Phase 4 | **Committed** to the repo |
| Memory bank updates | `{{profile.paths.memory_bank}}/patterns/*.md` | Phase 3 | **Committed** to the repo |

**With `roles.tracker: null` the first two, and the QA handoff, have no durable
home at all.** They are written, they are gitignored, and they are gone with the
working tree. That is correct and not a gap to be filled by committing them —
`check.py` asserts that transit artefacts stay uncommitted. What the stage must
not do is stay quiet about it: announce at Gate 5 which artifacts have nowhere
to go, so a person can copy one out if they want it.

## Examples

### A unit that is READY
```
/quorum-implement invoice-export
# Reads status.yml and tasks.md, writes the prompt, stops at Gate 1.
```

### Carrying an audit's findings
```
/quorum-implement invoice-export --fix
# The proposal at last_audit.proposal_ref is the scope. Not a redesign.
```

### Confirming scope without writing
```
/quorum-implement invoice-export --dry-run
# Stops at Gate 1, before the first phase that writes to the repository.
# The prompt artifact is still written; it is gitignored.
```

### Refusals, which are the common case
```
/quorum-implement invoice-export
# → REFUSE: status is DRAFTING_TASKS, not a READY-family state.
# → REFUSE: tasks.md T4 names AC9, which requirements.md does not define.
```

## Agent Used

- **orchestrator** — `quorum-orchestrator/agents/quorum-orchestrator.md` (bundled with this plugin; resolved as Initialization step 4 describes)

## Error Handling

- **Unknown slug:** no `.claude/specs/<slug>/` — REFUSE and route back to `/quorum-orchestrate`, which decides whether this is a new unit.
- **`{{role:tracker}}` unreachable:** not this stage's problem. Nothing here fetches a ticket, and nothing here posts one.
- **Agent failure:** Reports which agent failed, offers retry or skip
- **Human abort:** Records state for later `--resume`
