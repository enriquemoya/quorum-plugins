---
argument-hint: "<slug|TICKET-KEY> [--human] [--dry-run] | --queue [--dry-run]"
description: The single entry point for the governed pipeline. Reads .claude/specs/<slug>/status.yml and routes to the next stage — triage, product shaping, audits, implementation, delivery. Drives one unit, or every eligible unit in one session with --queue.
---

# /quorum-orchestrate

Routes a unit of work to its next stage by reading its state. It decides
nothing about the work itself; it decides what runs next.

```
/quorum-orchestrate invoice-export             # drive one unit
/quorum-orchestrate PROJ-1234                  # a ticket key creates or finds its unit
/quorum-orchestrate invoice-export --human     # stop at every gate this run
/quorum-orchestrate --queue                    # every eligible unit, one session
/quorum-orchestrate invoice-export --dry-run   # print the route, change nothing
```

**Never infer state from prose.** Not from the conversation, not from which
files exist, not from what the last summary said. `status.yml` is the answer;
if it is missing or unparseable, BLOCK.

## Preflight

1. Read `PIPELINE.md` (the process) and `governance/rules/GLOBAL.md`.
2. Read the consumer repo's `.claude/governance/rules/` — **anything present
   there overrides the plugin default of the same name.** Read
   `CONSTITUTION.md`; if it is absent, say so and route to `/quorum-init`.
3. Resolve `.claude/profile.yml`. A missing profile means every `{{profile.*}}`
   is null: the pipeline still runs, with each skipped concern announced.
4. Read `.claude/specs/<slug>/status.yml` through `quorum-status`. No state plus
   a ticket-key argument means a new unit: route to triage.

## Routing

| Status | Next |
|---|---|
| *(none)* | `/quorum-triage` — create the unit, set origin + complexity |
| `TRIAGE` | finish triage; a human approves the path |
| `DRAFT_PRD` | `/quorum-prd` — **always human-interactive** |
| `PRD_READY` | `/quorum-spec` |
| `ANALYZING` | `/quorum-analyze`, then `/quorum-tasks` |
| `DRAFTING_SPEC` | `/quorum-architecture`, or `/quorum-tasks` when simple |
| `DRAFTING_ARCH` | `/quorum-design` |
| `DRAFTING_DESIGN` | `/quorum-tasks` |
| `DRAFTING_TASKS` | `/quorum-scope-audit` |
| `SCOPE_AUDIT` | await verdict |
| `NEEDS_REVISION` | the proposal's `target_step` |
| `READY` / `READY_WITH_CONDITIONS` | `/quorum-implement` |
| `IN_PROGRESS` | `/quorum-impl-audit` |
| `IMPL_AUDIT` | await verdict |
| `NEEDS_FIX` | `/quorum-implement --fix`, carrying the proposal |
| `VERIFIED` / `VERIFIED_WITH_CONDITIONS` | `/quorum-deliver` |
| `DELIVERING` | finish delivery → `MERGED` |
| `STUCK` | **HALT.** Human only. |
| `MERGED` / `ABANDONED` / `SUPERSEDED` | terminal — refuse |

An unroutable state is an error, not something to repair. Report it and stop.

## Gates

Every transition prints the state tracker and consults the decision matrix in
`PIPELINE.md`.

In `human` mode — and under `--human` — every gate is a HARD STOP.

In `agent` mode the matrix decides, and these HALT regardless of it:

1. a finding citing a constitution article,
2. a scope promotion (ticket → spec),
3. delivery,
4. `STUCK`,
5. a verdict carrying `panel: single-provider` that would auto-advance past
   `IMPL_AUDIT` — such a run may iterate, it may not conclude.

Before taking any audit loop, read `audit_iterations` **from `status.yml`** and
compare it against the cap of 3 per unit. Do not count in context: a fresh
context starts at zero, and the loop the cap exists to stop is exactly what
produces fresh contexts.

## `--queue`

Derives the batch from state — never from a stored list.

```
1. scan .claude/specs/*/status.yml
2. eligible: agent-eligible state ∧ profile.autonomy.mode == agent
3. drop: any unit with a depends_on that is not MERGED          (hard)
4. order topologically; a cycle HALTs and names it
5. run sequentially; two units whose tasks.md file sets fall in the same
   profile.stack.components entry never run together
6. each unit runs to MERGED, STUCK, or an escalation
7. a parked or stuck unit does NOT stop the queue
8. second pass: retry parked units — a human may have resolved one mid-run.
   End when a full pass produces no advancement.
9. derive the session report from the status.yml files
```

Step 5 measures overlap rather than asking about it: the component map is in
the profile and the file sets are in `tasks.md`.

```
QUEUE — {n} eligible, {duration}

  MERGED      {n}   {slugs}
  PARKED      {n}   {slug}  → escalation: {reason}
  STUCK       {n}   {slug}  → {n} iterations, same evidence {n}×

  Not run     {n}   depends_on: {slug} ({state})
```

`Not run` is not filler. An unattended run is reviewable only if it says what
it did not reach, and why.

## State tracker

```
╔═══════════════════════════════════════════════════════╗
║  {slug}  ·  {origin}/{complexity}  ·  mode: {mode}    ║
╠═══════════════════════════════════════════════════════╣
║  state        {status}                                ║
║  iterations   {audit_iterations}/3                    ║
║  last audit   {step} → {verdict}  (panel: {panel})    ║
║  next         {command}                               ║
╚═══════════════════════════════════════════════════════╝
```

## What this command must not do

**Do not run a stage.** It routes; each stage's own command runs it. An entry
point that also executes is an entry point nobody can dry-run.

**Do not repair `status.yml`.** Report and stop. A repaired state file is a
state file someone guessed at, and every decision after it inherits the guess.

**Do not skip a stage the routing table names.** Complexity-based skips are
decided at triage and recorded in `status.yml`; a skip invented here is a skip
no audit knows happened.

**Do not run two units against overlapping components.** Sequential is the
default and the overlap rule is not advisory — a merge conflict between two
autonomous units is the one failure an unattended batch cannot recover from.
