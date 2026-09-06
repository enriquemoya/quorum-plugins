---
name: quorum-obsidian-vault
description: >-
  Capture and maintain durable knowledge bases in the project Obsidian vault
  (vault root from $QUORUM_VAULT, default ~/quorum-vault) so any fresh session
  or human can take over work
  mid-flight. Covers four kinds of work: PROJ-XXXXX ticket stories and bug
  investigations; long-running ticketless initiatives, POCs, and migrations such
  as platform-v2; lightweight spikes; and reusable reference recipes and
  operating-feedback notes. Trigger when starting, resuming, or handing off any
  of these; when a branch/PR opens, a discovery, root cause, risk, blocker,
  decision, or lesson appears, or a screenshot of tested work is captured; and on
  phrases like "set up notes", "log this", "capture what we learned", "save
  context for later", "where did we leave off", or "write a recipe".
  Proactively offer to create or
  update vault notes when durable multi-session work begins (a ticket, a named
  POC/migration, or work that will span sessions) and after meaningful progress.
  Don't use it for one-off chat answers, code TODOs, or single facts that belong
  in auto-memory.
---

# Obsidian Vault — durable knowledge bases for project work

## Why this exists

Project work spans many sessions and often many agents. Context that lives only in
a chat transcript dies when the session ends. This skill keeps a durable,
human-readable record in an **Obsidian vault** so that a **fresh session** can
open one folder and know exactly where things stand and what to do next, and a
**human** can read the same notes as a narrative of what was done, why, what was
discovered, and what was learned.

The vault is a *complement* to your other artifacts, never a duplicate of them —
it links out to Jira, PRs, QA plans, and auto-memory, and writes in only the
knowledge that's otherwise lost.

## What goes where (kinds)

The vault holds four kinds of work, each with a folder and an identifier:

| Kind | Folder | When |
|------|--------|------|
| **story** / **bugfix** | `Stories\<PROJ-KEY>\` | Any PROJ-XXXXX ticket (bugfix = a root-cause investigation) |
| **initiative** | `Initiatives\<slug>\` | Ticketless work over many sessions: POCs, migrations (platform-v2), tooling/skill builds |
| **effort** | `Efforts\<slug>.md` | A lightweight one-sitting spike / investigation |
| **reference** | `Resources\<slug>.md` | An evergreen recipe or operating-feedback note to reread later |

**Pick the kind with this rule of thumb** (full routing + identifiers in
`references/kinds-and-structure.md`):

1. **ticket key present → `story`** (or `bugfix` if the value is the diagnosis,
   not AC delivery). This is the deterministic tie-breaker — a ticketed item is
   never routed to a ticketless kind, even if it's also a migration.
2. **No ticket, many sessions, needs durable progress → `initiative`.**
3. **No ticket, basically one sitting → `effort`** (promote later if it grows).
4. **No progress to track, just facts to reread → `reference`.**

Read `references/kinds-and-structure.md` for the exact folder trees, frontmatter
schema, and per-kind note sections. Read `references/obsidian-syntax.md` whenever
Obsidian syntax (frontmatter, wikilinks, embeds, callouts) is unclear — get it
right, because broken links and malformed frontmatter quietly degrade the vault.

## Boundaries (don't let the systems fight)

Three systems capture cross-session knowledge; keep them in their lanes:

- **This vault** = the narrative handoff of an *effort* — progress, discoveries,
  decisions, lessons, screenshots. Rich, navigable, human-readable.
- **Auto-memory** (`MEMORY.md` + files) = compact, always-loaded *index* of
  durable facts. Keep it lightweight; let it *link to* a vault note rather than
  duplicate it. Don't migrate memory wholesale into the vault.
- **`qa-test-plans/<KEY>/plan.md`** = test-case execution state for a story.
  The vault links to it; it isn't recreated here.

If a request is a one-off chat answer, a code TODO, or a single durable fact,
it belongs in the reply or in memory — not a new vault folder.

## Workflow 1 — Starting work

When durable work begins (a user says "starting PROJ-XXXXX" / "starting the
platform-v2 migration" / "spike X", or you open a branch on real work):

1. **Decide the kind** with the routing rule above.
2. **Gather the facts:**
   - *story / bugfix:* if not already in the conversation, fetch the ticket with
     `quorum-workflows:quorum-jira-story` (it pulls the user story `customfield_10202`,
     acceptance criteria `customfield_10037`, and subtasks a plain read misses).
   - *initiative / effort / reference:* there is no Jira issue — seed the Goal /
     Definition of Done / Question / procedure from the user and the conversation.
3. **Scaffold** with the bundled PowerShell script (idempotent, never clobbers,
   maintains `Home.md`). The `-Kind` drives the folder, templates, and Home
   section. Run via `pwsh`:

   ```
   # story
   pwsh <skill-dir>\scripts\scaffold_vault.ps1 -Kind story -Key PROJ-68433 `
     -Title "AcmeSync virtual tours" -Branch PROJ-68433-virtual-tours
   # initiative (POC / migration / tooling)
   pwsh <skill-dir>\scripts\scaffold_vault.ps1 -Kind initiative -Subtype migration `
     -Title "platform-v2 migration" -Owner alex
   # effort / reference
   pwsh <skill-dir>\scripts\scaffold_vault.ps1 -Kind effort -Title "spike: evaluate gRPC"
   pwsh <skill-dir>\scripts\scaffold_vault.ps1 -Kind reference -Subtype recipe -Title "AcmeSync getfees probe"
   ```

   (`scaffold_story.ps1 -Key …` still works as a story-only alias.)
4. **Fill the overview/home note** in plain language: for a story, paste the
   User Story and each AC as `- [ ]` checkboxes inline (so a fresh session needs
   no Jira access) and keep the Jira link; for an initiative, write the Goal /
   Definition of Done and the phase checklist.
5. **Seed `status.md`** (where present): write the Snapshot paragraph and the
   branch(es). Everything else fills in as work happens.

## Workflow 2 — Logging progress (do this continuously)

`status.md` is only valuable if it's current. Update it whenever something
meaningful happens — don't wait until the end:

- **Snapshot** (`> [!abstract]`): keep it rewritten to reflect *now* — the
  always-true one-paragraph answer to "where are we?".
- **Progress Log:** a dated bullet per real change (what + why), newest on top.
  For an initiative this is the running engineering logbook that lets any
  session resume cold.
- **Discoveries** (`> [!note]`): how the system actually works, with `file:line`
  refs / `[[wikilinks]]` — saves the next session the same dig.
- **Risks & Blockers** (`> [!warning]` / `[!danger]`): what could derail or is
  blocking, plus what would unblock it.
- **Decisions:** the choice + the reasoning. For an **initiative**, promote a
  significant, hard-to-reverse choice into a MADR note under `decisions/` (use
  `assets/decision-note.md`); records are immutable once accepted — supersede,
  don't edit.
- **Lessons Learned:** see the dedicated section below — this is the #1 goal.
- **Next Steps / Handoff:** keep a concrete `- [ ]` list. Imagine handing the
  keyboard to someone new — what would they do next?

When state changes, update `status:` in **both** the overview and `status.md`.

Before updating a ticketless effort, **confirm the target first** — search
`Home.md` / the `Initiatives`/`Efforts` folder for the slug, because a loose
reference ("the migration notes", "the platform thing") can match the wrong
note or spawn a duplicate. Stories self-identify by key, so no search needed.

## Workflow 3 — Screenshots & evidence

Save the image into the note's `attachments\` folder with a descriptive name,
then embed it under **Screenshots & Evidence** with a caption:

```markdown
![[attachments/virtual-tour-renders.png|500]]
*Virtual tour iframe rendering on the staging hub after the fix.*
```

`|500` sets width in px (drop it for full size). If a Playwright/browser run
already produced a screenshot, copy it into `attachments\` so evidence travels
with the note.

## Workflow 4 — Resuming / taking over

When asked to resume / continue / "pick up where we left off":

1. For a **story**, open `Stories\<KEY>\status.md`; for an **initiative**, open
   its `<slug>.md` MOC then `status.md`. Read the **Snapshot** first, then **Next
   Steps**, **Risks**, **Discoveries**, **Lessons**.
2. Open the overview/home note for scope/AC/goal.
3. If a `qa-test-plans/<KEY>/plan.md` exists (stories), check test status.
4. **Reconcile with reality** before acting — confirm the branch exists, the
   build runs, the stash is where the note says — because the note reflects what
   was true when last written and code drifts (the `updated:` date is your
   staleness signal).

Then continue the work, and keep `status.md` current as you go.

## Workflow 5 — Searching the vault

The vault is plain Markdown, so search is full-text (use Grep/Glob, not the
Obsidian app):

- Find work by key/topic: search filenames and contents under the vault root.
- "What did we learn about AcmeSync fees?" → grep the term and read the matching
  **Lessons** (`> [!tip]`/`[!success]`) and **Discoveries** (`> [!note]`).
- All lessons across the vault: grep `#lesson`. All POCs: grep `kind: initiative`.
- `Home.md` is the index — start there to see what exists.

Prefer reading the relevant `status.md` over re-deriving context from code.

## Lessons learned (the point of all this)

Capture a lesson the moment you learn it, at the right altitude, and make it
findable:

- **story / bugfix:** a `## Lessons Learned` block in `status.md`. For a bugfix,
  the root-cause-vs-symptom trace, the bug-split (fixed/deferred/discarded), and
  *why* discarded approaches were rejected are themselves the highest-value
  lessons — pin them in the overview.
- **initiative:** a separate append-only `lessons.md` register (date | context |
  lesson | link) — over months the lessons outgrow a status section.
- **effort:** an inline `## Findings / Lessons` section.
- **reference:** the whole note *is* a distilled lesson set.

**Findability contract:** tag every lesson `#lesson` (one grep finds them all);
use callout *type* as a search key (`[!tip]`/`[!success]` = lesson, `[!note]` =
discovery, `[!warning]`/`[!danger]` = risk); write the **plain words you'll
later search for** ("AcmeSync getfees feeDetailsId is all-zeros at unit
level"), not a vague gesture; date everything for staleness. When an initiative
closes, promote durable, cross-effort lessons into a `Resources\<slug>.md`
reference note.

## Cross-linking (link out, write in)

Facts that live in a source of truth (Jira, PR, Confluence, the QA plan,
auto-memory) get **linked** in a Related section; only discovered/decided/learned
knowledge gets **written** into the vault. Link related work with `[[PROJ-XXXXX]]`
and `[[<slug>]]`; an initiative links its spin-off tickets and the reference
recipes it depended on, forming a navigable graph.

## Bundled resources

- `scripts/scaffold_vault.ps1` — `-Kind`-driven scaffolder (PowerShell, no Python
  dependency; idempotent; maintains `Home.md`). `scaffold_story.ps1` is a
  story-only alias.
- `assets/` — note templates: `story-note.md`, `bugfix-note.md`,
  `status-note.md` (shared), `initiative-note.md`, `lessons-note.md`,
  `effort-note.md`, `reference-recipe.md`, `reference-feedback.md`,
  `decision-note.md` (MADR), `migration-area.md`.
- `references/kinds-and-structure.md` — the detailed per-kind spec (folder trees,
  frontmatter, routing, identifiers). Read when you need exact structure.
- `references/obsidian-syntax.md` — Obsidian Flavored Markdown cheat sheet. Read
  when syntax is unclear.
