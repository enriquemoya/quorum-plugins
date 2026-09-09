---
name: quorum-agent-journal
description: >
  Deterministic, NO-QUESTIONS vault writes for autonomous testing agents (ui-tester,
  backend-tester). Two jobs: (A) CAPTURE — at the end of a run, attach acceptance-criteria
  proof (screenshots + a per-AC, per-client matrix) to the STORY side of the vault
  Obsidian vault, AND append agent-side "kaizen" lessons (what got stuck, what wasted
  calls, the rule to try next) to an evergreen operating-feedback log. (B) GROOM —
  promote recurring kaizen lessons into the agent/skill definitions so the agent
  actually improves over time. Sits ON TOP of quorum-obsidian-vault and delegates ALL
  folder/frontmatter/template structure to it — this skill owns only idempotent
  upsert + the close-the-loop promotion. Trigger at run end ("log the run", "capture
  proof", "write kaizen") and on "groom ui-tester" / "promote lessons".
---

# Agent Journal

The human-facing `quorum-workflows:quorum-obsidian-vault` skill is interactive and judgment-driven (it asks you to confirm targets, offers proactively). An **autonomous** agent cannot answer prompts. This skill is the thin deterministic layer it calls instead: every target is derived from on-disk artifacts, nothing is asked, every write is idempotent.

**This skill never re-encodes vault structure.** Folders, frontmatter, templates, `Home.md`, and the scaffolder all belong to `quorum-obsidian-vault` (and `scripts/scaffold_vault.ps1`). If you need to know *where* a note lives or *what shape* it has, that's the vault skill's `references/kinds-and-structure.md`. This skill owns only the *upsert procedure* and the *promotion loop*.

Vault root: `$QUORUM_VAULT` (default `~/quorum-vault`). Scaffolder: `<obsidian-skill-dir>\scripts\scaffold_vault.ps1` (idempotent — "never clobbers"). **Resolve it at runtime — never type an install path:** Glob `path` `~/.claude/plugins` — the **parent**, never a directory inside it, because the layout below it has already changed once and silently — with `pattern` `**/quorum-obsidian-vault/**/scaffold_vault.ps1`. The middle `**` is load-bearing: one layout puts a version segment between the plugin and its subdirectory, and a pattern without it finds the other layout only. Exactly one match: use that absolute path. None, or more than one: STOP and report what you found — do not skip the scaffold silently, and do not pick between two candidates silently either (the story note and AC matrix would never be created, or would be created from the wrong copy).

Inputs you read (never ask the user for these):
- `{workspace}/{ticket}/build/build-receipt.json` — from build-agent.
- `{workspace}/{ticket}/results.jsonl` — per (client, AC) result rows from ui-tester.
- `{workspace}/{ticket}/proof/<client>/AC-*.png` — proof screenshots.
- the branch / ticket key (deterministic — stories self-identify by ticket key, so no search, no disambiguation).

---

## Mode A — CAPTURE (run end)

### A1. Story-side AC proof → existing `story` kind

1. **Ensure the story note exists** (idempotent — safe every run):
   ```
   pwsh <obsidian-skill-dir>\scripts\scaffold_vault.ps1 -Kind story -Key <PROJ-KEY> -Title "<from jira/branch>" -Branch <branch>
   ```
   If it already exists the scaffolder skips it. If the ticket key can't be derived from the branch, STOP and report — do not write to a guessed folder.

2. **Copy proof PNGs** from `{workspace}/{ticket}/proof/<client>/` into the story's attachments, namespaced by client so multi-cred proof doesn't collide:
   ```
   <vault>\Stories\<TICKET-KEY>\attachments\e2e\<client-slug>\AC-1-PASS.png
   ```
   Overwrite-by-name = idempotent. These are the SAME images ui-tester already wrote under `qa-runs`; the vault gets its own copy so evidence travels with the note (per vault Workflow 3).

3. **Regenerate the E2E matrix block** in `Stories\<PROJ-KEY>\status.md`. Build the whole block from `results.jsonl` and replace it atomically between fences (re-runs replace, never append duplicates):
   ```markdown
   <!-- e2e:start -->
   ## E2E Verification — <run date> (ui-tester)

   | AC | Client | Result | Proof | Evidence |
   |---|---|---|---|---|
   | AC-1 | localmf | PASS | ![[attachments/e2e/localmf/AC-1-PASS.png\|500]] | Fee row published, source=PMS |
   | AC-1 | clientB | PASS | ![[attachments/e2e/clientb/AC-1-PASS.png\|500]] | ... |
   | AC-2 | clientB | FAIL | ![[attachments/e2e/clientb/AC-2-FAIL.png\|500]] | Expected X, got Y |

   _Build: platform `<head-short>` · receipt `build/build-receipt.json` · full run report `<link to qa-runs report.md>`_
   <!-- e2e:end -->
   ```
   If the fences are absent, insert a fresh block under "Screenshots & Evidence". If present, replace everything between them. **Link to** the run `report.md`, don't paste it.

4. **Flip AC checkboxes** in the overview `Stories\<PROJ-KEY>\<PROJ-KEY>.md`: an AC that passed for **all** tested clients → `- [x]`; any client FAIL/BLOCKED → leave `- [ ]` and note "(FAIL on <client> — see status)".

### A2. Agent-side kaizen → evergreen `reference`/`feedback` log

1. **Ensure the log exists** (idempotent):
   ```
   pwsh <obsidian-skill-dir>\scripts\scaffold_vault.ps1 -Kind reference -Subtype feedback -Slug qa-kaizen -Title "ui-tester kaizen — operating lessons"
   ```
   → `<vault>\Resources\qa-kaizen.md`.

2. **Append** one dated entry per durable lesson learned this run — only real friction (a stall, wasted calls, a red-herring, a guardrail that should have fired). Newest on top. Tag `#kaizen #lesson` so the vault's one-grep contract finds it. **De-dupe** by a `key:` of `<rule-slug>` — before appending, grep the log for the exact `key:` slug; if it exists, edit that entry (bump `seen:` by 1, refresh the date) and append nothing:
   ```markdown
   ### 2026-05-29 — Redis red-herring on /home  #kaizen #lesson
   - key: redis-redherring-home · seen: 2 · severity: high · status: open
   - **Symptom/waste:** ~13 min chasing a Redis 500 toast on the /home dashboard; target route didn't need Redis.
   - **Predicted vs observed:** (for a benchmark/test finding) expected <X>; observed <Y>.
   - **Fix/rule to apply:** a dashboard toast is never a blocker for a target on another route; settings staleness ⇒ flush Memcached, never debug Redis.
   - **Promote to:** <your-plugin>:build-recipe (Redis non-blocking) + ui-tester nav rule.
   - **Run:** [[PROJ-XXXXX]] · report <link to qa-runs report.md>   (required — every entry links its run)
   ```
   If nothing notable happened, write nothing — an empty run is not a lesson.

**Idempotency contract:** running Mode A twice over the same `results.jsonl` is a no-op (scaffold skips, PNG copies overwrite by name, the fenced block is regenerated wholesale, kaizen de-dupes by key). So a partial mid-run capture followed by a final capture is safe.

---

## Mode B — GROOM & PROMOTE (close the loop)

Capturing kaizen notes is necessary but not sufficient — the agent only *improves* when a recurring lesson becomes a rule in the agent/skill text. Run this periodically (e.g. monthly, or when `qa-kaizen.md` grows), or on "groom ui-tester" / "promote lessons":

1. Read `Resources\qa-kaizen.md`. Sort open entries by `seen:` count.
2. For each entry with `seen >= 2` (a *recurring* failure, not a one-off):
   - Open the `Promote to:` target (e.g. `<your-plugin>/agents/ui-tester.md` circuit breakers, `<your-plugin>-e2e-testing`, `<your-plugin>:build-recipe`).
   - Add or tighten the concrete rule there (a circuit breaker, a hard rule, an inline warning) — the smallest edit that would have prevented the waste.
   - Mark the kaizen entry `status: promoted` with the date and a link to the edited file. Promoted entries stay (the history is the audit trail) but drop out of future grooming.
3. Report what was promoted and to where. Edits land in your local checkout of this marketplace, under `plugins/`. **After editing, sync the installed copy or the change never loads** — an unsynced live edit is a silent no-op. Find the installed copy the same way anything else here is found: Glob `~/.claude/plugins` for `**/<plugin>/**/.claude-plugin/plugin.json` and copy over the directory that contains it. Do not type the destination from memory; that path has changed before, and a copy into a stale directory looks like it worked.

The vault is the staging ground; the skill/agent definition is where behavior actually changes.

---

## Rules

- **No questions, ever.** Every target is derived from artifacts + the branch. If a required input is missing (no ticket key, no results.jsonl), STOP and report — never guess a target or prompt.
- **Link out, write in.** Source-of-truth facts (Jira, the run `report.md`, the QA plan) get linked, not duplicated. Only proof and lessons are written into the vault.
- **Deterministic slugs.** Story = ticket key (self-identifying). Kaizen log = fixed slug `qa-kaizen`. Client slug = lowercased client name. No fuzzy matching.
- **Append/replace, never clobber.** Story proof block is fence-replaced; kaizen is append-with-dedupe; the scaffolder never overwrites an existing note.
