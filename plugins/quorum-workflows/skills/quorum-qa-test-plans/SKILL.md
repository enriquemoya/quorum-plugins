---
name: quorum-qa-test-plans
description: >
  Use to create, update, persist, resume, or list QA test plans for tracker stories.
  Plans are stored as markdown files at {cwd}/qa-test-plans/{story-key}/plan.md so
  progress is never lost between sessions. Invoke whenever the user mentions a QA test plan,
  testing a story, checking test case status, or wrapping up a session and wants to save
  progress. Trigger phrases include: "create a qa plan for PROJ-XXXXX", "test plan for
  PROJ-XXXXX", "qa test cases for PROJ-XXXXX", "persist qa plan for PROJ-XXXXX", "resume test
  plan for PROJ-XXXXX", "mark TC-01 as passed", "TC-03 blocked", "where are we on testing
  PROJ-XXXXX", "list my qa plans". Also trigger proactively when the user finishes implementing
  a story and hasn't yet created a test plan — offer to create one.
argument-hint: Jira ticket key (e.g.) and optional operation (create/update/resume/persist/list)
---

# QA Test Plans

Manages QA test plans for tracker stories on the local filesystem. Plans live at
`{cwd}/qa-test-plans/{story-key}/plan.md`, always relative to the Claude session's
working directory. A session started from `C:\dev` stores plans at
`C:\dev\qa-test-plans\PROJ-XXXXX\plan.md`.

The goal is that you can close the session at any time without losing the test plan
or your progress through it — every update is written to disk immediately.

## When to use this vs the other QA skills

These are **complementary lanes, not duplicates**:

- **`quorum-qa-test-plans`** (this skill) is the **persistent, execution-tracked** lane: it routes
  every AC to an executor (ui-tester/backend-tester/human), tracks pass/fail/blocked status across sessions,
  and reconciles whole-story coverage. Use it when QA needs to *execute and track* a story.
- **`quorum-manual-qa-test-cases`** (`quorum-tooling`) is the **one-shot, dev-facing** lane: it generates
  a manual checklist from a diff and (optionally) posts it to Jira as a comment, with no persistence
  or tracking. Use it for a quick pre-PR pass or when chaining from `/quorum-code-review`.
- **`quorum-qa-handoff-publisher`** (`quorum-orchestrator`, Phase 7) publishes **automated** coverage
  (unit + E2E) as a "Review Automation Tests" Jira subtask; it deliberately excludes manual cases and does not consume this skill's plans.

---

## Operations

### CREATE — Generate a new test plan

**Triggers**: "create qa plan for PROJ-XXXXX", "test plan for PROJ-XXXXX", "qa test cases for PROJ-XXXXX"

1. Check if `{cwd}/qa-test-plans/{story-key}/plan.md` already exists.
   - If it does: ask the user whether to open the existing plan or regenerate it.
   - If not: proceed.

2. Fetch the full story by invoking the `quorum-jira-story` skill:
   ```
   Skill(skill: "quorum-workflows:quorum-jira-story", args: "{story-key}")
   ```
   This returns the complete story with ACs, subtasks, sprint, and comments.

3. **Route every AC to a surface and an executor** (see **AC Coverage Routing** below) BEFORE generating test cases. This is the step that stops backend/log defects from escaping: a UI-only diff can sit on a story whose real risk is a backend state machine or an audit-log writer, and if no one is assigned that AC, it is verified by no one.

4. Generate test cases from the Acceptance Criteria (see **Generating Test Cases** below), one or more per AC, each tagged with the executor from step 3.

5. Write `{cwd}/qa-test-plans/{story-key}/plan.md` using the **Plan Format** below (including the **AC Coverage Matrix**). Create the directory if it doesn't exist.

6. Confirm: "Plan created at `qa-test-plans/{story-key}/plan.md` with N test cases across {executors}." **If any AC is unrouted, say so explicitly — the plan is INCOMPLETE until every AC has an executor.**

---

### PERSIST — Save a plan already in context to disk

**Triggers**: "persist qa plan for PROJ-XXXXX", "save the test plan for PROJ-XXXXX"

Use this when a test plan already exists in the current conversation (written earlier
in this session or present in loaded memory from a previous one) and the user wants to
capture it to disk.

1. Look for plan content in context — prior conversation turns, memory entries, or a plan
   already printed in this session.
   - If found: convert to **Plan Format** and write to `{cwd}/qa-test-plans/{story-key}/plan.md`.
   - If not found: fall back to CREATE (fetch from Jira, generate, then write).

2. Confirm: "Persisted to `qa-test-plans/{story-key}/plan.md`."

---

### UPDATE — Mark test cases as pass/fail/blocked/skipped

**Triggers**: "mark TC-03 as failed on PROJ-XXXXX", "TC-01 passed", "TC-05 blocked — no test client",
             "add note to TC-02", "update test result for PROJ-XXXXX"

1. Read `{cwd}/qa-test-plans/{story-key}/plan.md`. If missing, ask if the user wants to create it.

2. Locate the test case by ID (TC-01, TC-02, …) or by name if the user describes it loosely.

3. Update the `**Status**` line:
   - `⬜ Pending` — not yet run
   - `✅ Pass` — passed
   - `❌ Fail` — failed
   - `⏸ Blocked` — blocked (always capture reason in Notes)
   - `⏭ Skipped` — out of scope for this story

4. Append any notes or failure reason the user provided to the `**Notes**` field.

5. Recalculate the **Progress** summary line at the top of the file.

6. Update the `**Last Updated**` date to today.

7. Write the file back. Confirm: "Updated TC-0N to [status]."

---

### RESUME — Load and show current progress

**Triggers**: "resume PROJ-XXXXX test plan", "where are we on PROJ-XXXXX",
             "continue testing PROJ-XXXXX", "load qa plan for PROJ-XXXXX"

1. Read `{cwd}/qa-test-plans/{story-key}/plan.md`. If missing, offer to create it.

2. Print the current state:
   - Story title and **Progress** line
   - Test case table showing each TC with its status
   - Call out any blocked TCs or open questions

3. Ask what the user wants to do next — run the next pending TC, update a result, etc.

---

### RECONCILE — Close the coverage loop after executors run

**Triggers**: "reconcile PROJ-XXXXX", "did we cover the whole story", "close out PROJ-XXXXX testing",
             run automatically after a ui-tester or backend-tester run completes.

This is the **dispatcher + reconciler** — without it, a routed AC can sit owned-but-unrun (ui-tester writes a
`handoff.json`, nobody spawns backend-tester, and the gap survives with a paper trail). The invoker of this skill
(the human or orchestrating agent) OWNS this step; do not assume an unnamed "router" will.

1. Read the plan's **AC Coverage Matrix** and the executor outputs:
   - ui-tester: `{cwd}/qa-runs/{ticket}/results.jsonl` + `{ticket}/handoff.json` (the ACs it could NOT cover)
   - backend-tester: its per-routed-AC verdicts (PASS/FAIL/BLOCKED) from its report
2. **Dispatch any unconsumed handoff.** If `handoff.json` has entries with no matching backend-tester verdict, the backend half has NOT run — **invoke `<your-plugin>:backend-tester`** (pass it the ticket; it reads `handoff.json` at Step 1) before the story can be called done. Symmetrically, honor any `HANDOFF → ui-tester` lines backend-tester emitted by invoking ui-tester for those ACs.
3. Update each matrix row's Status from the executor verdicts (✅ / ❌ / ⏸ / ⬜).
4. Recompute the **whole-story verdict**: PASS only if every AC row is ✅ by its assigned executor. Any ⬜ (unrun) or unrouted AC ⇒ **INCOMPLETE** — list the specific gaps and which executor still owes a result. A 1-of-N executor pass is never a whole-story PASS.
5. Write the plan back and report the verdict + the exact remaining gaps.

### LIST — Show all stored test plans

**Triggers**: "list my qa test plans", "show qa plans", "what test plans do I have"

1. Scan `{cwd}/qa-test-plans/` for subdirectories containing `plan.md`.

2. Parse the **Progress** line from each file.

3. Display a summary table:

```
| Story    | Title                               | Progress  |
|----------|-------------------------------------|-----------|
| PROJ-68433 | AcmeSync v2: Pull virtual tours     | 3/9 done  |
| PROJ-69922 | QA — Virtual Tour toggle            | 0/5 done  |
```

---

## Plan Format

All `plan.md` files use this structure. Keep sections in this order. Omit a section
entirely if its source data is empty (e.g., no open questions, no notes yet).

```markdown
# {STORY-KEY}: {Story Summary}

**Jira**: {STORY-KEY}
**Created**: {YYYY-MM-DD}
**Last Updated**: {YYYY-MM-DD}
**Progress**: {done}/{total} complete — {N} ✅ Pass | {N} ❌ Fail | {N} ⏸ Blocked | {N} ⬜ Pending

## Acceptance Criteria

- [ ] AC-1: {description}
- [ ] AC-2: {description}

## AC Coverage Matrix

> Every AC must appear here with a surface and an executor. The story is NOT "tested" until every AC's
> assigned executor has a passing result. An unrouted AC (executor blank) means the plan is INCOMPLETE.

| AC | Risk surface | Executor | Status |
|----|--------------|----------|--------|
| AC-1 | UI-render | ui-tester | ⬜ |
| AC-2 | backend-state | backend-tester | ⬜ |
| AC-3 | audit-log-content | backend-tester | ⬜ |
| AC-4 | data-transition (round-trip) | backend-tester | ⬜ |

**Whole-story verdict**: {PASS only if every AC row is ✅ by its executor · else PARTIAL/INCOMPLETE — list the gaps}

## Test Cases

### TC-01 — {Scenario Name}

**Status**: ⬜ Pending
**Covers**: AC-1
**Executor**: ui-tester | backend-tester | human  (from the AC Coverage Matrix)

**Steps**:
1. {step}
2. {step}

**Expected**: {what should happen}
**Notes**:

---

### TC-02 — {Scenario Name}

**Status**: ⬜ Pending
**Covers**: AC-2

...

## Open Questions

- {Unresolved items from Jira comments or grooming — remove when resolved}

## Notes

{Free-form: test client info, DB queries, SQL trigger commands, session observations}
```

**Status icon reference:**

| Icon | Meaning |
|------|---------|
| ⬜ | Pending — not yet run |
| ✅ | Pass |
| ❌ | Fail |
| ⏸ | Blocked |
| ⏭ | Skipped / Out of scope |

---

## AC Coverage Routing

This is the step that closes the seam where QA-found defects escape: coverage is decided by the **story's
ACs**, not by the code diff. Classify EVERY acceptance criterion (and any edge case from grooming/comments)
by where its risk actually lives, then assign the executor who has an *oracle* for that surface. An AdminUI
UI tester (`ui-tester`) can prove "the right thing renders / the system reached the right end-state"; it has no
oracle for backend state transitions or audit-message content. A backend tester (`backend-tester`) drives
processors/jobs and asserts DB + audit state. Most non-trivial Platform stories need BOTH.

**Surface → executor:**

| Risk surface | What it means | Executor |
|--------------|---------------|----------|
| **UI-render** | A page/grid/icon/field renders the right value or state | `ui-tester` |
| **backend-state** | A job/processor/work-item changes DB rows (create/update/delete/inactivate) | `backend-tester` |
| **audit-log-content** | A log/audit/history message must name the right entity / action / severity, with no dupes | `backend-tester` |
| **data-transition** | A→B because an input changed — *especially the reverse leg* (B→A on input reappearing) and terminal boundaries (count→0) | `backend-tester` (round-trip oracle) |
| **error-handling** | Bad/partial input → correct error/retry/alert/work-item-failure path | `backend-tester` |
| **human-only** | Visual/UX judgment, external-system side effects not reachable locally | `human` (note why) |

**Rules:**
- One AC may need MORE than one executor (e.g. "the sync updates the fee AND the grid shows it" → backend-tester for the DB change, ui-tester for the render). List each.
- An AC routed to no executor makes the plan **INCOMPLETE** — surface it loudly; never let a 1-of-N slice read as "done".
- The diff being UI-only does NOT shrink the AC set. If the backend half is already merged, it still needs a `backend-tester` row — merged ≠ verified.
- This matrix is the **dispatch contract**: ui-tester emits a `handoff.json` for ACs it can't cover and `backend-tester` consumes it; the matrix is where both halves reconcile into one whole-story verdict.

## Generating Test Cases

The quality of the test plan depends on how well you translate ACs into concrete, runnable
steps. Follow these principles:

**One AC → one or more TCs.** Split when an AC has distinct scenarios — e.g., "when toggle
is ON" and "when toggle is OFF" are two separate test cases, not one.

**Name TCs after the scenario, not the AC.** "Toggle OFF: No URLs pulled" is more useful
than "AC-7 — disabled state". A reader should know what to do just from the TC name.

**Include concrete steps.** Vague steps like "trigger a sync" lose value after a week.
For integration work, concrete steps typically mean:
- The SQL to enable/disable a setting
- The SQL to trigger a sync job (update `qrtz_triggers` `next_fire_time`)
- The DB query to verify the result (SELECT from the relevant table)
- The API call or AdminUI path to verify UI behavior

**Tie each TC back to an AC** via the `Covers` field — this makes it easy to verify full
AC coverage at a glance.

**Capture open questions as Open Questions**, not as pending test cases. If there's a known
gap (e.g., "needs test client with virtual tours"), document it in Open Questions so it
doesn't silently block a TC without explanation.

**Pull from Jira comments and subtask details** — grooming notes and PM comments often
contain edge cases and constraints that don't make it into the formal ACs.

### Per-AC test-design checklist (forces the oracle types that catch real defects)

A forward "it ran / the row exists" case passes a whole class of defects. For EACH AC, before you stop
generating its test cases, ask these four and add a case wherever the answer is yes (this is what separates
a plan that catches escapes from one that rubber-stamps the happy path):

1. **Negative / suppression** — is there something that must NOT happen (no unintended delete, no spurious
   log line, out-of-scope rows untouched, feature-off ⇒ no effect)? Add a case that asserts the absence.
2. **State-transition round-trip** — does this AC move an entity A→B because an input changed? Then add the
   reverse leg: input reappears/reverts, **re-run the pipeline**, assert B→A on the primary state field (not
   a manual DB reset). Include the terminal boundary (count→0).
3. **Audit/log content** — does the AC mention logging/audit/history? Then assert the message TEXT names the
   affected entity and the right action/severity, not just that a row exists — include a degenerate case
   (equal count, swapped membership) to prove a count oracle is insufficient.
4. **Input-shape equivalence partition** — partition the SOURCE input: empty-collection vs decrement vs
   present-but-unresolvable; optional-unset vs required-unset. Each often hits a different branch.

Tag each such case with the right `Executor` (transition/content/negative-backend cases are almost always
`backend-tester`; render cases are `ui-tester`) so RECONCILE can route them.
