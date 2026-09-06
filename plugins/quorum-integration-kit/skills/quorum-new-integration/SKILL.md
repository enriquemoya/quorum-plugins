---
name: quorum-new-integration
description: Scaffold a complete third-party integration pipeline for a new partner — inbound ingest, outbound sync, settings, lookup, and tests — from a declared partner profile. Use when onboarding a new integration partner, adding a partner to an existing integration family, or when the user says "add integration for X", "onboard partner X", "scaffold the X pipeline". Reads integration-profile.yml for the repo layout; refuses to generate until the profile and the partner intake are both complete.
---

# New integration — pipeline scaffold

You generate the full file set for a new integration partner, following the
conventions **this repository already uses**, not a convention this skill
invented. That distinction drives every phase below: you read the existing
partners first, and you generate in their image.

> **This skill ships no domain knowledge.** It does not know what your partners
> do, what your entities are called, or how your queue works. It learns that
> from `integration-profile.yml` and from the reference partner you nominate.

---

## Phase A — Load the profile

Read `integration-profile.yml` from the repo root (see
[`references/profile-schema.md`](references/profile-schema.md) for the full
contract). You need, at minimum:

| Key | What it tells you |
|---|---|
| `repos` | Which checkouts are in play, and their roles. Cross-repo integrations name more than one. |
| `paths.integrations_root` | Where per-partner code lives, per repo. |
| `paths.settings_registry` | The file that enumerates partner settings. |
| `paths.migrations` | Where schema migrations go. |
| `reference_partner` | An existing partner to pattern-match against. |
| `pipelines` | Which pipeline families exist (e.g. `inbound_ingest`, `outbound_sync`). |
| `test.framework` / `test.layout` | How tests are organized and named. |

**Refuse to continue** if the file is missing or lacks `reference_partner` —
scaffolding without a pattern to match produces plausible code in the wrong
shape, which is worse than no code. Tell the user to create the profile and
name a partner, and stop.

## Phase B — Read the reference partner

Before you write anything, read the reference partner's full file set. Build an
explicit inventory:

```
For each file in the reference partner's pipeline:
  - path (relative to its repo)
  - role (transport / mapping / settings / registration / test)
  - what is partner-SPECIFIC vs what is boilerplate
```

Report the inventory to the user. This is the template you will instantiate,
and naming it out loud is how the user catches a wrong reference early.

## Phase C — Partner intake

Collect what only the user can tell you. Use
[`references/partner-intake-template.md`](references/partner-intake-template.md)
and fill every field:

- Partner display name and the code identifier (`{Partner}`) to use in types
- Which pipeline families this partner needs (from `pipelines` in the profile)
- Auth model and where credentials will live — **names only, never values**
- Endpoint list with request/response shape per operation
- Field mapping: partner field → your entity field, including every transform
- Rate limits, pagination style, and error semantics
- Sandbox/test credentials availability

**Never invent an endpoint, a field name, or an auth flow.** Anything the user
cannot supply becomes an explicit `TODO(partner-intake)` in the generated code,
listed in your final report. Guessed integration details fail in production, not
in review.

## Phase D — Confirm the plan

Present, and wait for approval:

1. Every file you will create, with its full path
2. Every existing file you will modify, and the exact edit
3. The migrations you will add
4. The tests you will generate
5. Every `TODO(partner-intake)` that will remain

Do not generate until the user approves. A wrong scaffold spread across two
repos is expensive to unpick.

## Phase E — Generate

Work repo by repo, in dependency order (types and contracts before the code
that consumes them). For each file:

- **Match the reference partner's structure exactly** — same section order, same
  naming, same error handling, same logging. Consistency across partners is the
  point of a scaffold.
- **Register the partner** everywhere the registry pattern requires it: the
  settings enumeration, the lookup/factory, the migration, any DI wiring.
  A generated partner that is never registered is the single most common
  scaffold defect.
- **Generate tests alongside**, per `test.layout`. A pipeline without tests is
  not scaffolded; it is drafted.

## Phase F — Report

Return:

- Files created and files modified, grouped by repo
- Every `TODO(partner-intake)` with its location and what it needs
- The migrations added and whether they have been run
- The exact command to run the new tests
- **The next step: run the `integration-reviewer` agent before opening a PR**

---

## Rules

- **Read before write.** Every generated file has a reference-partner
  counterpart you have actually read.
- **Never fabricate partner API details.** `TODO(partner-intake)` instead.
- **Credentials are names, never values.** No secret ever lands in a generated
  file, a migration, or a test fixture.
- **No partial generation.** If you cannot complete a repo's file set, revert
  what you wrote in it and report why.
- **Cross-repo means cross-repo.** When the profile names multiple repos, a
  partner is not scaffolded until every repo's half is present and registered.
