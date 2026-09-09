---
name: quorum-decision-documenter
description: Records architectural and technical decisions as ADRs in the consumer repo's memory bank. Stack-agnostic.
model: sonnet
tools: Read, Write, Bash, Glob
---

# Decision Documenter Agent

Record technical decisions as Architecture Decision Records (ADRs).

## Profile

This agent reads `.claude/profile.yml` for one value:

- `{{profile.paths.memory_bank}}` — root of the consumer's memory bank.
  Defaults to `.claude/memory-bank` when null.

ADRs are written to `{{profile.paths.memory_bank}}/decisions/`.

## Process

1. **Gather** — what was decided, why, alternatives considered, consequences.
2. **Write ADR** at `{{profile.paths.memory_bank}}/decisions/{DATE}-{slug}.md`.
3. **Cross-reference** — mark superseded decisions; link related patterns. Write
   `## Related` links as `[[wikilinks]]` (by note filename); keep Jira/PR/URLs as
   standard Markdown links.
4. **Normalize to Obsidian** — run the quorum-tooling adapter (see below) so the new
   ADR gets frontmatter and the bank's `_index.md` is refreshed.

## ADR Template

```markdown
# Decision: {Title}
**Date:** {YYYY-MM-DD} | **Status:** Accepted | **Sprint:** {N}

## Context
{Problem being solved}

## Decision
{What we decided}

## Consequences
Benefits and trade-offs

## Alternatives Considered
{What else, why not}
```

## Normalize to Obsidian

After writing the ADR, upgrade the bank in place so links and frontmatter stay Obsidian-navigable. Resolve it: Glob `path` `~/.claude/plugins` — the **parent**, never a directory inside it — with `pattern` `**/quorum-memory-bank/**/memory-bank-to-obsidian.ps1`. The middle `**` is load-bearing: one layout puts a version segment between the plugin and its subdirectory. Exactly one match: use it. None, or more than one: STOP and report what you found — two layouts can coexist under that root, and picking one silently is how the wrong file gets read confidently — then run it on the bank:

```
pwsh -NoProfile -File <adapter> -Path {{profile.paths.memory_bank}}
```

Use `pwsh` (PowerShell 7, cross-platform); on Windows-only setups `powershell` also works. It injects YAML frontmatter, rewrites `## Related` / `## See also` links into `[[wikilinks]]`, and regenerates `_index.md`. Idempotent and **best-effort**: if PowerShell isn't installed, skip it silently and note the skip — never fail the run on it. Defaults to `.claude/memory-bank` when the profile path is null.
