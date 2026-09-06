# quorum-integration-kit

Scaffolding for third-party integration partners — **with no domain knowledge of
its own**. It learns your codebase's conventions from `integration-profile.yml`
and from a reference partner you nominate, then generates in that image.

## Why a profile instead of built-in knowledge

An integration toolkit that ships opinions about *your* entities, *your* queue,
and *your* partners is useful in exactly one codebase. This one carries the
*process* — intake, pattern-match, generate, register, review — and reads the
specifics from a file you own.

## Setup

Create `integration-profile.yml` at your repo (or workspace) root. The full
contract is in
[`skills/quorum-new-integration/references/profile-schema.md`](skills/quorum-new-integration/references/profile-schema.md).
The one required field is `reference_partner`: an existing integration the
generator can pattern-match against. Without it the skill refuses to run —
by design.

## What's in it

| Component | Kind | What it does |
|---|---|---|
| `quorum-new-integration` | skill | Onboards a brand-new partner: intake → confirm → generate the full pipeline across every repo it spans, with tests and registration. |
| `quorum-integration-change` | skill | Turns a ticket into a plan whose every step names a real file. For changes to partners that already exist. |
| `integration-reviewer` | agent | Pre-merge review of an integration diff: structural conformance, AC alignment, and cross-pattern leakage. Run it before every PR. |
| `integration-change-analyzer` | agent | Read-only inventory of a partner's current code and the candidate change sites for a ticket. Feeds the change planner. |

## Flow

```
new partner ──▶ /quorum-new-integration ──▶ integration-reviewer ──▶ PR
                                                    ▲
existing ─────▶ /quorum-integration-change ─────────┘
                        │
                        └─▶ integration-change-analyzer (inventory)
```

## Design rules

These are enforced in the skill text, not just advised:

- **Never fabricate partner API details.** Anything the intake cannot answer
  becomes an explicit `TODO(partner-intake)` and is reported, never guessed.
- **Read before write.** Every generated file has a reference-partner
  counterpart that was actually read first.
- **Credentials are names, never values** — in code, fixtures, and migrations
  alike.
- **No partial generation.** A repo's file set lands complete or is reverted.
- **Generated ≠ registered.** The most common scaffold defect is a partner that
  compiles and is invisible at runtime; the reviewer checks every registration
  site.
