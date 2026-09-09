# Requirements — reconcile the implementation stage with the pipeline around it

## Goals

`/quorum-implement` stopped being the entry point and kept the document it had
when it was one. Make the stage describe what it now does, and delete what the
pipeline does upstream.

## In scope

- `plugins/quorum-orchestrator/commands/quorum-implement.md`.
- Assertions in `scripts/e2e.py` for the guarantees this document states.

## Non-goals

- The seven phases' own work. Testing, code review and PR artifacts are this
  stage's, and stay.
- Upstream stages. A phase here that is better than its upstream counterpart is
  a finding about the upstream stage, recorded and left.
- The tracker abstraction. `roles.tracker` plus `browse_url_template` already
  models any tracker or none.

## What the document says that the pipeline contradicts

1. The frontmatter takes `<slug>`; Usage shows a ticket key five times, with
   the old entry-point invocation.
2. Flags disagree three ways: the table lists `--complexity`, `--resume` and
   `--include-subtasks`, which the frontmatter does not declare, and omits
   `--fix`, which the preconditions make load-bearing.
3. Initialization step 1 validates a ticket-key format. A unit on the spec path
   has no ticket key, and that is the path this stage is reached by most.
4. Complexity is auto-detected "after fetching the ticket". Triage sets it and
   `status.yml` records it.
5. `--dry-run` runs Phases 1–3 only — precisely the phases that duplicate
   upstream.
6. Phase 1 delegates to a named external product for ticket fetching.
7. Two artifacts have their durable home listed on a named tracker, and the
   table says nothing about a repository with no tracker configured.
8. Artifact paths are keyed by `{TICKET-KEY}`, null on the spec path.
9. `tasks.md` is never read. The unit arrives with an audited task list and the
   stage plans its own work instead.

## Decisions this spec makes, rather than deferring

**The three undeclared flags are all deleted.** Decided here because each
deletion has a reason that belongs to scope, not to implementation:

| Flag | Decision | Why |
|---|---|---|
| `--complexity` | delete | AC4 reads complexity from `status.yml`; an override can disagree with the value the scope audit ran under |
| `--resume` | delete | `status.yml` holds the state and `/quorum-orchestrate` re-routes from it — a second resume mechanism is a second source of truth |
| `--include-subtasks` | delete | a ticket-fetch option, and the fetch phase is being removed |

**The keep-set from the removed phases is closed to one item: the prompt
file.** No upstream stage produces one. Anything else later found to be unique
is a new finding against this unit, not an open clause inside it.

**A null tracker means the two artifacts are transient and not committed.**
`check.py` already asserts that transit artefacts stay uncommitted, so "durable
home" was the wrong requirement for them. The stage announces at the gate that
they have no external home.

## Acceptance criteria

Each criterion states either a guarantee — which AC8 asserts — or a
description, marked as such. Nothing here is a guarantee without an assertion.

- AC1 *(guarantee)*: the stage takes a slug throughout. The ticket key remains
  as what it now is — an optional field on a unit that came from the ticket
  path — and is not deleted.
- AC2 *(guarantee)*: the flag table and the frontmatter declare the same set,
  `--fix` included and the three above absent.
- AC3 *(description)*: Phases 1 and 2 are replaced by reading the unit's
  artifacts, and the prompt file is the one element kept. Not asserted:
  "the right things were removed" has no failing case a script can produce.
  What IS asserted, under AC2 and AC7, is the contract that survives them.
- AC4 *(guarantee)*: complexity is read from `status.yml`. The document
  contains no procedure for deriving it.
- AC5 *(guarantee)*: `--dry-run` states what it stops before. Asserted
  positively — a check that only forbids a phase number also passes a file
  where the flag was deleted, or where it stops before nothing.
- AC6 *(guarantee)*: no external product is named in this file where a role is
  meant, and the file states where the two artifacts live when no tracker is
  configured. `check.py`'s transit-artefact rule is the reason they are not
  committed, not the assertion for this criterion — it does not name them.
- AC7 *(guarantee)*: `tasks.md` is the plan, and the stage refuses a unit whose
  tasks do not map to acceptance criteria. The mapping is mechanical: every
  task line ends with `AC:` naming one or more ids, and every id it names
  exists in `requirements.md`.
- AC8 *(guarantee)*: `scripts/e2e.py` asserts AC1, AC2, AC4, AC5, AC6 and AC7. Each
  assertion is watched failing against a deliberately broken copy first, and
  the injected defect and resulting count go in the commit message — which is
  where Article 3 tells an auditor to look.

## What this unit does not close

Article 2 stays open. This unit removes one file's product names; 41 tracked
files keep them. None is under `governance/`, so Article 1 is unaffected, and
the repository does integrate with that product through a driver skill — so
the violation here is narrower than "a product is named": it is a driver's name
leaking into the layer that must work with any tracker or none. The remaining
sweep is its own unit, and this unit completing is not evidence the article is
cleared.
