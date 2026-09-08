# PIPELINE.md — the governed delivery process

The process every unit of work flows through, gated by state in `status.yml`.
The stages are fixed; which of them run is decided per unit by triage, and how
much a human is asked is decided by the autonomy mode.

## The pipeline

```
                  ┌── spec path:  PRD → requirements → architecture → design ──┐
ENTRY → TRIAGE ───┤                            (skippable by complexity)        ├─► tasks
                  └── ticket path: fetch → analyze ───────────────────────────┘      │
                                                                                     ▼
                                                                             SCOPE AUDIT
                                                                                     │
                                                                              READY  ▼
                                                                            IMPLEMENT
                                                                                     │
                                                                                     ▼
                                                                            IMPL AUDIT
                                                                                     │
                                                                           VERIFIED  ▼
                                                                             DELIVERY
```

| # | Stage | Command | Agent | Artifact in `.claude/specs/<slug>/` |
|---|---|---|---|---|
| 0 | **Triage** | `/quorum-triage` | `quorum-triage` | `status.yml` (origin + complexity) |
| 1a | **PRD** | `/quorum-prd` | `quorum-prd` | `prd.md` |
| 1b | **Ticket analysis** | `/quorum-analyze` | `quorum-ticket-analyzer` | `analysis.md` |
| 2 | **Requirements** | `/quorum-spec` | `quorum-spec` | `requirements.md` |
| 3 | **Architecture** | `/quorum-architecture` | `quorum-architecture` | `architecture.md` |
| 4 | **Design** | `/quorum-design` | `quorum-design` | `design.md` |
| 5 | **Tasks** | `/quorum-tasks` | `quorum-tasks` | `tasks.md` |
| 6 | **Scope audit** | `/quorum-scope-audit` | `quorum-audit` | `runs/<slug>/scope-audit-*` |
| 7 | **Implementation** | `/quorum-implement` | `quorum-orchestrator` | code, tests, review |
| 8 | **Implementation audit** | `/quorum-impl-audit` | `quorum-audit` | `runs/<slug>/impl-audit-*` |
| 9 | **Delivery** | `/quorum-deliver` | `quorum-delivery` | PR opened, tracker updated |

`/quorum-orchestrate <slug>` is the single entry point. It reads `status.yml`
and routes to the correct next stage. **It never infers state from prose.**

## Triage decides the path, the audit corrects it

Triage runs first and writes two fields that govern everything after:

| Field | Values | Decides |
|---|---|---|
| `origin` | `spec` \| `ticket` | which upstream stages run |
| `complexity` | `simple` \| `medium` \| `complex` | which of them are skipped |

A clear, bounded change with usable acceptance criteria takes the ticket path.
Anything whose problem statement is still open takes the spec path.

**Triage is a proposal, not a verdict.** The scope audit re-checks the same
question with the artifacts in hand — traceability from intent to acceptance
criteria to tasks. When a ticket turns out to be underspecified, the audit does
not reject it: it emits a proposal promoting it to the spec path. Which stages
that promotion re-runs is the proposal's `target_step`.

That ordering matters. An operator rarely knows in advance whether a ticket
carries enough to implement safely; the auditor can tell, because by then there
is something to measure.

## State machine

`status.yml` is the only source of truth for where a unit of work is.

```
(none)
  └─► TRIAGE ─┬─► DRAFT_PRD ─► PRD_READY ─┐          [spec path]
              │                            ├─► DRAFTING_SPEC
              │                            │      ─► DRAFTING_ARCH      (skip: simple)
              │                            │      ─► DRAFTING_DESIGN    (skip: simple)
              │                            └─────► DRAFTING_TASKS
              └─► ANALYZING ──────────────────────► DRAFTING_TASKS      [ticket path]

  DRAFTING_TASKS ─► SCOPE_AUDIT
       SCOPE_AUDIT ─► { READY | READY_WITH_CONDITIONS | NEEDS_REVISION }
       NEEDS_REVISION ─► <proposal.target_step>            (loop)
       { READY | READY_WITH_CONDITIONS } ─► IN_PROGRESS
  IN_PROGRESS ─► IMPL_AUDIT
       IMPL_AUDIT ─► { VERIFIED | VERIFIED_WITH_CONDITIONS | NEEDS_FIX }
       NEEDS_FIX ─► IN_PROGRESS                             (loop)
       VERIFIED ─► DELIVERING ─► MERGED
  Any ─► ABANDONED | SUPERSEDED | STUCK
```

Every transition appends to `history`. **History is append-only; past entries
are never rewritten.** A state that can be edited backwards is not a record.

## Loop control

Both loops are bounded, and the bounds are the whole safety story once an agent
is driving.

| Loop | Where | Trigger | Bound |
|---|---|---|---|
| **Inner** | within a stage | build / test / lint red | retries within the stage, no audit |
| **Outer** | across stages | audit verdict | **3 iterations per spec**, and same-evidence-thrice |

**The cap is per spec, not per gate.** Three scope-audit iterations leave none
for the implementation audit: that unit reaches `STUCK` without ever having
implemented. That is the intended reading — a scope revised three times without
converging is a problem in the PRD, not in the code.

**The counter lives in `status.yml`, not in the agent.** An agent that counts
its own iterations has no cap. `audit_iterations` is read from the file,
incremented on write, and compared against the bound before any loop is taken.

`same-evidence-thrice`: if the same finding evidence (`file:line` or artifact
ref) appears in three audit iterations, the loop is not converging. `STUCK`.

## Autonomy

```yaml
autonomy:
  mode: human          # human | agent
```

Mode is a profile default; `--human` forces a single run to stop at every gate.
There is no `--agent` flag: switching autonomy on is a standing decision, and a
per-run flag makes it an accident.

**The agent frontier is `PRD_READY`.** Everything before it is human, always.
An agent that writes the PRD defines the problem and the solution, which is
where an autonomous system errs most expensively and least visibly.

```
TRIAGE ─► DRAFT_PRD ─► PRD_READY ─────────────────────────► MERGED
└──── always human ──┘└──── agent-eligible (with escalations) ────┘
```

### Decision matrix

| Verdict | Findings | Iteration | `agent` | `human` |
|---|---|---|---|---|
| `READY` / `SAFE` | none | — | advance | ask |
| `*_WITH_CONDITIONS` | none blocking | — | advance, record conditions | ask |
| `NEEDS_REVISION` / `NEEDS_FIX` | blocking | `< 3` | loop to `target_step` | ask |
| any | cites a constitution article | — | **HALT — human** | halt |
| any | — | `>= 3` | `STUCK` | `STUCK` |
| any | same evidence 3× | — | `STUCK` | `STUCK` |

### Never automatic, in either mode

1. **A constitution violation.** The constitution is law; a finding citing an
   article is always blocking. An agent that auto-fixes a constitutional
   violation and continues is precisely the failure the constitution exists to
   prevent.
2. **Scope promotion** (ticket → spec). It changes what work is being done.
3. **Delivery.** Opening a PR or merging acts outward.
4. **`STUCK`.** By definition.

### Agent mode and a degraded panel

An audit records which panel produced it. When `panel: single-provider` — the
cross-provider engine was unavailable and the panel ran same-provider — an
agent-mode run **may iterate but may not conclude**: it cannot auto-advance
past `IMPL_AUDIT`. It records the reason and waits for a human.

A degraded panel that auto-approves is a silent pass on the method rather than
on the code, and silent passes are forbidden.

## Batch orchestration

`/quorum-orchestrate --queue` drives every eligible unit in one session.

**The queue is derived, never stored.** It is recomputed from the `status.yml`
files on each run. A stored queue is a second source of truth that drifts from
the first, and state is not inferred from a second file any more than it is
inferred from prose.

```
1. scan .claude/specs/*/status.yml
2. eligible: status ∈ { PRD_READY … VERIFIED } ∧ autonomy.mode: agent
3. order by depends_on (topological; a cycle HALTs and reports)
4. sequential
5. each unit runs until MERGED | STUCK | escalation
6. session report
```

**Sequential, and not out of caution alone.** Two units implementing in
parallel against overlapping files is the direct route to merge conflicts the
agent cannot resolve. Overlap is *measured*, not asked about: two units whose
task file sets fall in the same `stack.components` entry do not run together.

**`depends_on` is hard.** A unit whose dependency is parked does not run.
Implementing against a base that was parked produces work that has to be redone.

**A parked or stuck unit does not stop the queue.** It is recorded and the run
continues; one bad unit should not consume an unattended session.

**Parked units are retried in a second pass.** A human may resolve an
escalation while the queue is still running. The run ends when a full pass
produces no advancement.

### Session report

```
QUEUE — 5 eligible, 4h 12m

  MERGED      3   invoice-export, tenant-filter-fix, retry-backoff
  PARKED      1   bank-recon      → escalation: constitution article 2
  STUCK       1   movement-class  → 3 iterations, same evidence 2×

  Not run     2   depends_on: bank-recon (parked)
```

The last two lines carry as much weight as the first. Saying what did **not**
happen, and why, is what makes an unattended run reviewable.

The report is derived at the end from the `status.yml` files, for the same
reason the queue is.

## Non-negotiables

Enforced at every stage by `governance/rules/`.

1. **No implementation without an approved scope.** Status must be READY-family
   before `/quorum-implement`.
2. **The project constitution is law.** `governance/rules/CONSTITUTION.md` in
   the consumer repo holds the articles this project will not violate. A PRD or
   spec that violates one cannot be READY; a diff that violates one cannot be
   SAFE. The plugin ships a template with **no articles** — the articles are
   the project's, and `/quorum-init` asks for them.
3. **Audits emit a proposal for every non-clean verdict.** Silent passes are
   forbidden. A verdict with no blockers states so explicitly, with the reason
   the set is empty.
4. **Evidence or it did not happen.** Every finding cites `file:line` or an
   artifact reference.
5. **The audit never fixes.** It emits findings and a proposal; fixes happen at
   the stage the proposal targets.
6. **Deterministic within a governance version.** Every verdict records the
   governance version that produced it, so a verdict can be traced to the rules
   that judged it and re-run against them.
7. **Stack facts come from the profile**, never from a rule. What a repository
   is built with and made of is discovered by `/quorum-init` and recorded in
   `profile.yml`. A governance rule that names a framework has confused a
   project's content with the process's structure.

## Where things live

```
PLUGIN (versioned, updated through the marketplace)
  PIPELINE.md                 ← this file
  PROFILE_SCHEMA.md
  commands/                   ← the entry points
  agents/                     ← who executes each stage
  governance/rules/           ← defaults: GLOBAL, SPEC_STANDARD, AUDIT_PROPOSAL
  governance/workflows/       ← defaults: per-stage step definitions
  skills/

CONSUMER REPO (committed with the code it governs)
  .claude/profile.yml         ← stack, conventions, autonomy, tracker
  .claude/governance/
      rules/CONSTITUTION.md   ← the project's articles — scaffolded by init
      rules/*.md              ← only when overriding a plugin default
      workflows/*.md          ← only when overriding a plugin default
  .claude/specs/<slug>/       ← prd, requirements, architecture, design, tasks, status.yml
  .claude/runs/<slug>/        ← audit matrices, verdicts, proposals
  .claude/memory-bank/        ← patterns, decisions, architecture, troubleshooting
```

**Precedence: the repo wins.** A rule or workflow present in the consumer repo
overrides the plugin's default of the same name. Nothing is copied at install
time except the constitution template — a repo-local copy of a file nobody
edited is a file that silently goes stale.

Every verdict records `governance_version`, so which defaults were in force is
recoverable even after the plugin moves.
