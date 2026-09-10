# Requirements — the tracker driver leaked into the agnostic layer

## Goals

Every file under `plugins/` outside the driver reaches the tracker through
`{{role:tracker}}`, or does not reach it at all.

## In scope

35 files under `plugins/`. One assertion in `scripts/check.py`. Three
documentation files.

## Non-goals

- `quorum-jira-story` and its evals. That skill IS the driver; naming what it
  drives is what Article 2 permits.
- The schema's `browse_url_template` examples. Article 1's own text allows
  naming a product in an example that illustrates resolution, and that field
  shows three different trackers precisely to make the point.
- Writing drivers for other trackers.

## The three coupling shapes, counted

| Shape | Count | Fix |
|---|---|---|
| a named MCP tool — `getJiraIssue`, `getAccessibleAtlassianResources`, "Atlassian MCP" | ~39 | delegate to `{{role:tracker}}` |
| a hardcoded key pattern `PROJ-\d` | 6 | `{{profile.ticket_prefix}}` — the field already exists and is required when `roles.tracker` is non-null |
| the product named in prose where "the tracker" is meant | remainder | the role, or the plain noun |

The ticket-key *examples* (`PROJ-68433` and friends) are not a shape. `PROJ-` is
already a placeholder prefix, and an example key is an example.

## Where the leak concentrates, and what that says

Three files hold 76 of the 203 occurrences: the orchestrator agent, a QA
test-case skill and the handoff publisher. Those sit closest to the ticket path,
which is where a tracker belongs. The rest spread outward — four unit-test
generators name a tracker, and generating unit tests does not require one.

The sweep therefore has two different jobs. Near the ticket path the call
becomes a delegation. Far from it the mention is deleted, because those steps
should never have known.

## Acceptance criteria

- AC1 *(guarantee)*: no file under `plugins/`, excluding the driver skill and
  its evals, names a tracker-specific tool or resource.
- AC2 *(guarantee)*: no file under `plugins/` hardcodes a ticket-key pattern;
  the pattern resolves from `{{profile.ticket_prefix}}`.
- AC3 *(description)*: where a step needs the tracker it delegates to
  `{{role:tracker}}` and says what happens when that role is null. For most of
  these the answer is "skip the step and announce it", not "fail" — a repository
  with no tracker is a supported configuration, not a broken one.
- AC4 *(description)*: the four unit-test generators stop mentioning a tracker.
- AC5 *(guarantee)*: `scripts/check.py` fails on a tracker-specific tool name
  outside the driver, watched failing against a reintroduced one, with the
  injected defect and count in the commit message.
- AC6 *(guarantee)*: `scripts/e2e.py` still passes. Several of these files carry
  assertions already and the sweep must not quietly change what they promise.

## What this unit does not claim

It does not make the plugins tracker-agnostic in behaviour — only in text. A
repository whose `roles.tracker` names a skill this marketplace does not ship
still has no driver, and this unit does not write one. What changes is that the
skills stop describing steps they cannot perform.
