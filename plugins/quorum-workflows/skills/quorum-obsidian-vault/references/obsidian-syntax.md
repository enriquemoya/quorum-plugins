# Obsidian Flavored Markdown — quick reference

Obsidian notes are plain Markdown files, but a handful of Obsidian-specific extensions make the vault navigable and rich. Use them deliberately — they are what turn a folder of `.md` files into a linked, skimmable knowledge base. When in doubt about rendering, prefer the simplest form that works.

## Properties (YAML frontmatter)

Metadata lives in a YAML block that **must be the very first thing in the file**, fenced by `---`:

```yaml
---
key: PROJ-68433
status: in-progress
updated: 2026-05-28
tags:
  - story
  - PROJ-68433
---
```

Rules that actually bite:
- **Dates** use ISO `YYYY-MM-DD` (or `YYYY-MM-DDTHH:MM`) so they sort correctly.
- **Lists** (like `tags`, `aliases`) use the block style shown above, one `- value` per line.
- **Internal links inside frontmatter must be quoted**: `jira: "[[PROJ-68433]]"`. External URLs do not need quotes unless they contain a colon-space or other YAML-confusing punctuation — when unsure, quote it.
- `tags`, `aliases`, and `cssclasses` are built-in properties Obsidian treats specially. Don't put a `#` on tags in frontmatter — write `story`, not `#story`.

## Internal links (wikilinks)

Use wikilinks for anything **inside the vault** — Obsidian tracks renames and builds the graph from them.

| Goal | Syntax |
|------|--------|
| Link a note | `[[status]]` |
| Link with custom text | `[[status\|current status]]` |
| Link a heading | `[[status#Next Steps / Handoff]]` |
| Link a block | `[[status#^block-id]]` (append `^block-id` to the target paragraph) |

Use standard Markdown links **only for external URLs** (Jira, docs, PRs): `[PROJ-68433 in Jira](https://...)`.

## Embeds

Prefix a wikilink with `!` to embed it inline:
- Image: `![[attachments/login-pass.png]]`
- Image with width: `![[attachments/login-pass.png|500]]`
- Another note (transclude): `![[PROJ-68433]]`
- PDF page: `![[spec.pdf#page=3]]`

Save screenshots/attachments into the story's `attachments/` folder and embed them by relative path as above.

## Callouts

Callouts highlight a block. Syntax is a blockquote with a `[!type]` tag:

```markdown
> [!warning] Token expires after 1h
> The AcmeSync probe re-auths on every call; cached token will be stale.
```

Add `-` after the type for a collapsed-by-default callout, `+` for expanded:

```markdown
> [!todo]- Handoff checklist
> - [ ] Re-add csproj Compile Includes
```

Useful types for story notes: `info`, `abstract`/`summary` (snapshot), `note` (discoveries), `warning`/`danger` (risks/blockers), `todo` (handoff), `success`/`bug`/`question`, `quote`.

## Other handy syntax

- **Task checkboxes:** `- [ ]` / `- [x]` — Obsidian renders and can query these.
- **Highlight:** `==important==`
- **Comment (hidden in reading view):** `%% note to self %%`
- **Tags inline:** `#area/integrations`, `#proj-68433` (letters/numbers/`_`/`-`/`/`; can't start with a number).
- **Footnotes:** `text[^1]` then `[^1]: the note`.
- **Mermaid diagrams:** a fenced ```` ```mermaid ```` code block.
- **Math:** `$inline$` and `$$block$$` LaTeX.

## Vault mechanics worth knowing

- A "vault" is just a folder. The first time it's opened in the Obsidian app, an `.obsidian/` config folder appears — you don't need to create it.
- Notes are referenced by **filename**, not path, so keep filenames unique enough to link cleanly. Stories link by key (`PROJ-68433.md` → `[[PROJ-68433]]`); ticketless work links by slug (`platform-v2-migration.md` → `[[platform-v2-migration]]`).
- There's no database — search is full-text over the files, so write things you'll want to find later in plain words.

## Callout type as a search key (vault convention)

This vault uses callout *type* consistently so a reader (or grep) can find things fast: `> [!abstract]` = the Snapshot, `> [!note]` = a discovery, `> [!warning]`/`> [!danger]` = a risk/blocker, `> [!tip]`/`> [!success]` = a lesson learned. Lessons additionally carry an inline `#lesson` tag so one grep surfaces every lesson across the vault. Significant, hard-to-reverse decisions on a long-running initiative graduate into immutable MADR notes under `decisions/` (see `kinds-and-structure.md`).
