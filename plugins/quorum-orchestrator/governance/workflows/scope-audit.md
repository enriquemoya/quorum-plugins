# Workflow: SCOPE AUDIT

Input: slug. Agent: `quorum-audit` (gate: scope).
Precondition: status `DRAFTING_TASKS` or `SCOPE_AUDIT`; `audit_iterations < 3`;
a constitution exists.

Steps:
1) Read prd/analysis, requirements, architecture, design, tasks, status.yml.
   Refuse on a terminal state. Note which stages complexity skipped.
2) Author a neutral brief — artifacts and articles, never the author's reading.
3) Convene `quorum-panel` (lenses: traceability, constitution, feasibility).
   `rounds_complete: false` ends the audit with no verdict.
4) Constitution walk: every article whose `Applies to` includes this `origin`.
   Name the skipped ones.
5) Traceability both ways: intent -> acceptance criteria -> tasks.
6) Origin check: a ticket with unusable acceptance criteria yields a promotion
   proposal (`target_step: prd`), never a rejection. Promotion always stops for
   a human.
7) Emit runs/<slug>/scope-audit-iter-NN-{matrix,verdict}.md and, for any
   non-clean verdict, iter-NN-proposal.yml.
8) Write last_audit + increment audit_iterations through `quorum-status`.

Output sections: (1) correct (2) ambiguities (3) missing (4) risks
(5) blockers fired — or "no blockers fired (reason: ...)" (6) verdict, naming
the panel (7) recommended transition.

Next on READY-family: `/quorum-implement`.
