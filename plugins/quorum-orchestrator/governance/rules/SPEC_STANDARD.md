# SPEC_STANDARD.md — the artifacts a unit of work carries

Folder: `.claude/specs/<slug>/`

| File | Path | Holds |
|---|---|---|
| `status.yml` | both | lifecycle state — the only source of truth |
| `prd.md` | spec | problem, users, value, success metrics, articles it serves |
| `analysis.md` | ticket | what the ticket asks, surfaces touched, acceptance criteria found |
| `requirements.md` | both | goals, scope, non-goals, constraints, acceptance criteria |
| `architecture.md` | spec | components touched, data/contract deltas, boundaries |
| `design.md` | spec | flows, contracts, schema and indexes, edge cases, states |
| `tasks.md` | both | phased task list; every task maps to an acceptance criterion |

`architecture.md` and `design.md` are skipped at `complexity: simple`, and the
skip is announced at the gate. `analysis.md` and `prd.md` are mutually
exclusive: they answer the same question from the two origins.

## Rules

- **Trace both ways.** Every artifact traces back to the PRD or the ticket, and
  forward to an acceptance criterion. A value point with no downstream
  requirement, or a task with no upstream criterion, is a finding.
- **Do not invent behaviour.** A spec records decisions that were made, not
  ones the author would like.
- **Do not implement in a spec.** Contracts and schemas, yes; code, no.
- **Stack facts come from `profile.yml`.** A spec that hardcodes a framework
  has embedded an assumption the profile already answers, and the two will
  disagree.

## tasks.md

Each task carries the file set it touches. That list is load-bearing twice
over: the executor reads it instead of rediscovering the map each session, and
the batch queue measures it against `profile.stack.components` to decide which
units may not run concurrently.

```markdown
- [ ] T1: <what> — files: <path>, <path> — AC: <criterion id>
```
