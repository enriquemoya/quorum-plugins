# PRD — one name, two prompts, and the platform picks

## Problem

`quorum-code-review` exists twice: `plugins/quorum-tooling/commands/quorum-code-review.md`
and `plugins/quorum-tooling/skills/quorum-code-review/SKILL.md`. The installed
inventory lists the name twice under Skills, so the runtime does not
distinguish them in the `/` namespace — which of the two prompts answers
`/quorum-code-review` is not something this repository decides.

`docs/claude-code-concepts.md` documents the pairing as deliberate: the command
is "a thin wrapper that invokes the skill" and "the user-friendly handle."

The command is not a wrapper. It is 56 lines that resolve the profile and
describe the review procedure themselves, and the two copies have already
diverged — the skill carries a git lifecycle contract (it writes `review_{N}.md`
and explicitly does not stage or commit) that the command never mentions. A
caller who lands on the command gets a review with no statement about who
commits the artifact.

## How it was found

By installing the marketplace and reading the component inventory. Neither
suite could have found it: both check file contents, and each file is
internally fine. The defect is that two of them answer to one name.

## Value

A slash command resolves to one prompt, or the ambiguity is a decision someone
made rather than one nobody noticed.

## Success

- `/quorum-code-review` resolves to exactly one prompt.
- Whatever the resolution, the documentation describes what the repository
  actually ships rather than what it intended.
- An assertion fails on any future name existing as both a command and a skill.

## Non-goals

- The review procedure itself.
- The 15 commands and 19 skills that do not collide. The sweep found exactly
  one collision, in one plugin, and no cross-plugin collisions at all.

## Constitution articles touched

- **Article 3.** "Either invocation works" is stated as a guarantee, has no
  assertion, and is not true of a wrapper that stopped wrapping.

## Open question for the spec

Three resolutions, and the audit should choose rather than the implementer:
delete the command and let the skill own the name; make the command genuinely
thin, a single line delegating to the skill; or rename one of them. The third
is the only one that keeps two entry points, and it costs a name that people
may already type.
