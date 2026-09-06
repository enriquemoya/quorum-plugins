---
id: {{ID}}
kind: {{KIND}}
status: {{STATUS}}
updated: {{DATE}}
tags:
  - status
  - {{ID}}
---

# {{ID}} — Status & Handoff

> [!abstract] Snapshot
> <!-- The FIRST thing a fresh session reads. One short paragraph: where the work stands RIGHT NOW, what was last done, and the immediate next move. Keep this rewritten to reflect *now* — it is the single most-read block in the vault. -->

## Branches, PRs & Environment

- **Branch(es):** {{BRANCH}} <!-- list 0..N; "n/a — no branch" is fine for a pure-investigation effort -->
- **Repos touched:** <!-- e.g. C:\dev\platform, C:\dev\portal -->
- **PRs / links:** <!-- PR #, design docs, dashboards -->
- **Cross-repo / NuGet:** <!-- producer→consumer chain + versions + deploy order, if applicable -->
- **Build/run notes:** <!-- anything non-obvious to get it running locally -->

## Progress Log

<!-- Reverse-chronological. Each entry: date + what changed + why. Newest on top. -->
### {{DATE}}
- Created notes; work starting.

## Discoveries

<!-- How the system actually works — things you had to dig to learn. Saves the next session the dig. -->
> [!note] <!-- short title -->
> <!-- detail, with file:line refs or [[wikilinks]] -->

## Risks & Blockers

> [!warning] <!-- short title -->
> <!-- detail + what would unblock -->

## Decisions

<!-- Choices made and the reasoning, so they aren't relitigated. For initiatives, promote significant ones to a decisions/ MADR note. -->
-

## Lessons Learned

<!-- The #1 thing to preserve. Tag each durable insight #lesson so it's greppable across the whole vault. -->
> [!tip] <!-- short title --> #lesson
> <!-- what was learned + why it matters, with file:line / [[link]] -->

## Screenshots & Evidence

<!-- Embed images of work done and tested. Save files under attachments/. -->
<!-- ![[attachments/example.png|500]] — caption -->

## Next Steps / Handoff

<!-- The explicit to-do list for whoever picks this up next. Be concrete. -->
- [ ]

## Related

- Overview / home: [[{{ID}}]]
- Lessons register: {{LESSONS_LINK}}
- QA test plan: `{{QA_PLAN}}`
- Jira: [{{ID}}]({{JIRA_URL}})
