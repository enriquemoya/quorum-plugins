# Workflow: TRIAGE

Input: slug or ticket key. Agent: `quorum-triage`. Precondition: no status.yml,
or status TRIAGE. A constitution must exist.

Steps:
1) Read the source — the ticket via roles.tracker, or the stated scope.
   Classifying from a title is guessing at the question that governs everything
   after this.
2) Resolve reach against profile.stack.components and profile.observed.
3) Grep for an overlapping in-flight unit. Overlap becomes depends_on or a
   supersession — both a human's call, never a silent parallel effort.
4) Propose origin (spec | ticket) and complexity (simple | medium | complex),
   each with its evidence, and name the stages that will run and be skipped.
5) A HUMAN approves the route, in both autonomy modes: the route decides how
   much scrutiny the work receives.
6) Create status.yml and transition to DRAFT_PRD or ANALYZING.

Anything with no obvious rollback is complex regardless of diff size.
When genuinely unsure, take the deeper path: the spec path compresses by
complexity, a wrong ticket path has to be redone after a full audit round.
