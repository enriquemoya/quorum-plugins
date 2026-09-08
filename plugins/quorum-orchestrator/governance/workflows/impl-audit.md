# Workflow: IMPLEMENTATION AUDIT

Input: slug. Agent: `quorum-audit` (gate: impl).
Precondition: status `IN_PROGRESS` or `IMPL_AUDIT`; `audit_iterations < 3`;
a constitution exists.

Steps:
1) GATE FIRST. Run type-check, unit tests and lint from
   `profile.commands.*`, falling back to `profile.observed.verified_commands`.
   Record exit codes and log paths. A VERIFIED verdict is FORBIDDEN when the
   gate is red, stale or missing; a non-zero exit is a high-severity blocking
   finding with `target_step: impl`.
2) Read the approved scope and the diff. Refuse on a terminal state.
3) Author a neutral brief over the DIFF, not the spec's promises.
4) Convene `quorum-panel` (lenses: satisfaction, integrity, test adequacy).
   `rounds_complete: false` ends the audit with no verdict.
5) Requirement traceability table: | requirement | evidence (file:line) |
   PASS/FAIL |. A FAIL row forbids VERIFIED without a matching
   `accepted_conditions` entry.
6) Constitution + data rules against the actual diff.
7) Scope containment: changes outside tasks.md's declared file sets are a
   finding regardless of merit.
8) Emit runs/<slug>/impl-audit-iter-NN-{matrix,verdict}.md + proposal.
9) Write last_audit + increment audit_iterations through `quorum-status`.

Output sections: (1) gate results, exit codes, log paths (2) correct
(3) ambiguities (4) missing (5) risks (6) blockers fired (7) verdict, naming
the panel (8) recommended transition.

Agent mode: a VERIFIED-family verdict carrying `panel: single-provider` does
not auto-advance to delivery. Record the reason and wait for a human.

Next on VERIFIED-family: `/quorum-deliver`.
