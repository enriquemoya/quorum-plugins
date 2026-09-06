---
name: quorum-integration-change
description: Plan a ticket-driven change to an EXISTING integration partner — map acceptance criteria to concrete code-change sites across every repo the integration spans, then produce an implementation plan. Use when a ticket modifies existing integration behavior, when the user says "plan PROJ-1234", "scope this integration change", or "what does this ticket touch". For brand-new partners use quorum-new-integration instead.
---

# Integration change — scoping and plan

You turn a ticket into a plan whose every step names a real file. You do not
implement; you produce the plan the implementer follows.

## Phase A — Load context

1. Read `integration-profile.yml` (see the new-integration skill's
   [`profile-schema.md`](../quorum-new-integration/references/profile-schema.md)).
2. Resolve the ticket. Take the key from the argument, or derive it from the
   current branch using `tracker.branch_pattern`. Fetch the ticket and read the
   **full** acceptance criteria — not just the summary.
3. Identify the partner(s) in scope. If the ticket does not name one, derive it
   from the branch or ask. Never guess.

**Refuse to plan** without acceptance criteria. A plan built from a title is a
plan that misses half the work.

## Phase B — Inventory the current state

Delegate to the `integration-change-analyzer` agent. Give it: the partner(s),
the acceptance criteria, and the profile. It returns a scoping report — the
current file inventory and the candidate change sites.

Do this before forming any opinion about the change. The analyzer looks at what
*is*; you decide what *should be*.

## Phase C — Map ACs to change sites

Build the mapping table. Every acceptance criterion gets at least one row:

| AC | Change site (file:symbol) | Kind | Risk |
|---|---|---|---|
| AC-1 | `src/Integrations/Acme/Inbound/Mapper.cs:MapRecord` | modify | field transform |

`Kind` is one of: `modify`, `add`, `remove`, `migrate`, `register`, `test`.

An AC with no change site is a gap — either the AC is already satisfied (say so,
with the evidence) or you have not found the site yet. Never leave it blank.

## Phase D — Check the cross-cutting surfaces

Integration changes leak. For each of these, state explicitly whether it is
affected, and why:

- **The settings registry** — new or changed configuration keys
- **Migrations** — schema, and whether a backfill is needed
- **Other partners** — a change in shared mapping or base-class code touches
  every partner, not just this one
- **The satellite repos** — a contract change in one repo needs the other's half
- **Idempotency and retry** — does the change alter what a redelivery does?
- **Tests** — which existing tests now assert the wrong thing

"Not affected" is a valid answer. Silence is not.

## Phase E — Emit the plan

```markdown
# {TICKET} — {title}

## Scope
{one paragraph: what changes and what does not}

## Acceptance criteria → change sites
{the Phase C table}

## Cross-cutting
{the Phase D checklist, each with a verdict}

## Steps
1. {ordered, each naming its files}

## Tests
{which to add, which to update, the command to run them}

## Risks and open questions
{anything that could make this plan wrong}
```

Present the plan and stop. Implementation is a separate, approved step.

## Rules

- **Every step names a file.** A step that says "update the mapping" is not a
  step.
- **Never plan against a summary.** Full ACs or refuse.
- **Report gaps as gaps.** An AC you cannot place is the most valuable line in
  the plan.
- **Do not implement in this skill**, even for a one-line change.
