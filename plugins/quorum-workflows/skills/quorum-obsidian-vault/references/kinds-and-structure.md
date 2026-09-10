# Vault kinds & structure (reference)

The Work Vault — rooted at `$QUORUM_VAULT`, defaulting to `~/quorum-vault` — captures lessons, context, findings, and progress for every kind of work that outlives a single chat session. This file is the detailed spec; `SKILL.md` is the workflow. Read this when you need the exact folder tree, frontmatter fields, or per-kind sections.

## The kinds at a glance

| Kind | Folder | Identifier | Notes created | Has status.md? | Ticket? |
|------|--------|-----------|---------------|----------------|---------|
| `story` | `Stories\<KEY>\` | ticket key | `<KEY>.md` + `status.md` + `attachments\` | yes | always |
| `bugfix` | `Stories\<KEY>\` | ticket key | `<KEY>.md` (bug-shaped) + `status.md` + `attachments\` | yes | always |
| `initiative` | `Initiatives\<slug>\` | slug | `<slug>.md` (MOC) + `status.md` + `lessons.md` + `decisions\` (+ `migration\` if migration) + `attachments\` | yes | never |
| `effort` | `Efforts\<slug>.md` | slug | one note | no (collapsed in) | never |
| `reference` | `Resources\<slug>.md` | slug | one note | no (evergreen) | never |

`bugfix` is a sub-variant of `story` — same folder and identity, only the overview note leads with Repro / Root-Cause / Bug-Split sections. `initiative` absorbs POCs, migrations, and self-directed tooling/skill efforts (distinguished by `subtype: poc|migration|tooling`). `reference` covers reread-verbatim recipes and operating-feedback notes (`type: recipe|feedback`).

## Choosing a kind (routing)

1. **Is there a ticket key?** → `story` (or `bugfix` if the value is a root-cause investigation rather than AC delivery). The ticket key is the deterministic tie-breaker: a ticketed item is NEVER routed to a ticketless kind, even if it's also a migration.
2. **No ticket, spans many sessions, needs durable progress state?** (the platform-v2 migration, a POC, a tooling/skill build) → `initiative`.
3. **No ticket, lightweight, basically one sitting?** (a spike, a throwaway investigation) → `effort`. Promote to an `initiative` later if it grows.
4. **No progress to track — a fact-set/how-to to reread later?** (a probe recipe, a repo map, an agent-briefing lesson) → `reference`.

When the work is named but you're unsure it'll recur, start as an `effort` and promote — don't pre-build a heavy `Initiatives\` tree for a one-off.

## Identifiers

- **Stories/bugfix:** the the tracker key verbatim (`PROJ-68433`) — it's the folder name, the overview filename (`PROJ-68433.md` → `[[PROJ-68433]]`), and `key:` in frontmatter. Self-identifying, so no disambiguation needed.
- **Ticketless kinds:** a lowercase hyphenated slug derived from the title (`platform-v2-migration`, `local-nuget-skill`, `spike-evaluate-grpc`). The slug is the folder/file name and `id:`. Because slugs are fuzzy, the skill **searches Home.md / the folder first and confirms the target before any update** to avoid duplicates or wrong-target writes.

## Frontmatter schema

Every note carries `kind:` as the first-class discriminator — it's what makes the vault queryable (`grep "kind: initiative"`, or a Dataview query if the plugin is installed).

Shared core: `id` (or `key` for stories), `title`, `kind`, `status`, `created`, `updated`, `tags: [<kind>, <id>]`.

- **story / bugfix** add: `ticket`, `sprint`, `points`, `epic` (bugfix swaps in `reporter`, `repro-property`).
- **initiative** adds: `subtype`, `no-ticket: true`, `owner`, `started`, `target`.
- **effort** adds: `no-ticket: true`, `promoted-to` (set when it graduates).
- **reference** adds: `type`, `topic`/`subject`, `no-ticket: true`; has **no status** (evergreen) and never archives.

Ticketless notes OMIT the `ticket:` line entirely — never emit an empty `ticket: ""` or a dangling `[ in the tracker]()` link. The scaffolder strips those lines automatically.

## Status lifecycle

`not-started → in-progress → blocked / in-review → done`, plus `abandoned` (efforts) and `archived` (completed initiatives left in place). Reference notes have no status. When state changes, update `status:` in **both** the overview and `status.md`. Completed initiatives may later be moved to an `Archive\` folder and flipped to `archived` — that move is manual for now (not scaffolded).

## status.md — the shared spine (story + bugfix + initiative)

One living handoff note, identical across the ticketed-and-initiative kinds (this is the reusable crown jewel):

`Snapshot` (`> [!abstract]`, the always-true "where are we?") · `Branches, PRs & Environment` (0..N branches, cross-repo/NuGet chain, "n/a — no branch" allowed) · `Progress Log` (reverse-chron, what+why) · `Discoveries` (`> [!note]` + file:line) · `Risks & Blockers` (`> [!warning]`/`[!danger]` + what unblocks) · `Decisions` · `Lessons Learned` (`> [!tip]`/`[!success]` tagged `#lesson`) · `Screenshots & Evidence` · `Next Steps / Handoff` (`- [ ]`) · `Related`.

Stories additionally surface AC/QA verification and a "Pending the tracker Updates (drafted? posted?)" block in the overview. Initiatives embed `![[migration/dashboard]]` when relevant.

## Initiative internal structure

```
Initiatives\platform-v2-migration\
  platform-v2-migration.md   # MOC/home: goal, phase checklist, decision-log link, map
  status.md                    # living logbook (the shared spine above)
  lessons.md                   # append-only lessons register (date | context | lesson | link)
  decisions\
    _index.md                  # the ADL (Architecture Decision Log) index table
    0001-target-framework.md   # one immutable MADR note per significant choice
  migration\                   # only for subtype: migration
    dashboard.md               # per-area status table + burndown
    areas\
      auth-module.md           # one note per seam (status: not-started→…→verified)
  attachments\
```

`decisions/` uses MADR: each record is immutable once `accepted`; when direction changes, write a NEW record and link with reciprocal `supersedes` / `superseded-by`. Use `assets\decision-note.md`. Migration areas use `assets\migration-area.md`.

## Home.md

A kind-segmented map of content titled **Work Vault**, with sections `## Stories`, `## Initiatives & POCs`, `## Efforts & Spikes`, `## Resources`. The scaffolder files each new note under the right section (newest on top) and guards against duplicate links. Each initiative's own `<slug>.md` is itself a second-tier MOC, so navigation is Home → initiative MOC → child notes.
