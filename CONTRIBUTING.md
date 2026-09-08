# Contributing

## Layout

```
.claude-plugin/marketplace.json   ← the catalog; every plugin is listed here
plugins/<plugin>/
  .claude-plugin/plugin.json      ← name, version, description, deps
  commands/*.md                   ← slash commands
  skills/<skill>/SKILL.md         ← skills, with references/ and scripts/
  agents/*.md                     ← subagents
  hooks/                          ← optional hooks
docs/                             ← cross-plugin documentation
```

Read [`docs/plugin-authoring.md`](docs/plugin-authoring.md) before adding a
plugin — it covers the manifest fields and when a capability should be a skill
versus a command versus an agent.

## Adding a plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json`.
2. Add the skills, commands, and agents.
3. **Register it in `.claude-plugin/marketplace.json`** — a plugin missing from
   the catalog is not installable, and this is the step people forget.
4. Add a row to the plugin table in the root `README.md`.
5. Install it in dev mode and run it end to end at least once.

## The bar for skill and agent text

These files are prompts, and vague prompts produce vague agents.

- **Refuse rather than guess.** If a skill needs information it does not have,
  it stops and says which file or field it wanted. It never fills the gap with a
  plausible value.
- **Unknowns are output.** Anything undetermined becomes an explicit `TODO`
  marker in the artifact and a named gap in the report.
- **Every finding cites a location.** Reviewer agents report `file:line`, never
  "somewhere in the mapping layer".
- **Gate irreversible steps on a human.** Generating a plan needs no approval;
  writing files across two repos does.
- **No domain knowledge in the plugin.** Anything true of one codebase only
  belongs in that repo's profile, not in the skill text. This is what keeps the
  marketplace a template rather than someone's private toolkit.

## Versioning

Bump the plugin's `version` in **both** its `plugin.json` and the marketplace
entry whenever behavior changes. The install cache is version-keyed; skipping
the bump means users keep running the old text.

## Before you open a PR

- The plugin installs cleanly from a fresh dev-mode add
- Every command and skill you touched has been invoked at least once
- `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"`
  passes, and so does the same check on every `plugin.json`
- No absolute local paths, no company names, no ticket keys, no credentials —
  examples use placeholders (`PROJ-1234`, `<your-org>`, `Contoso.*`)

## Checks

```
python3 scripts/check.py          # everything
python3 scripts/check.py --list   # name the checks and what each is for
```

Eight structural checks, standard library only, run in CI on every push and
pull request. They decide things a reader cannot: that every command the router
names exists, that the three files defining the pipeline's states agree, that
every `{{profile.*}}` placeholder is defined in the schema, that a plugin's
version matches the marketplace's, and that nothing in the tree names where
this code came from.

Every one of them exists because that specific thing was wrong at some point
and was found by hand, late. The provenance check found a claim in this
README on the day it was written.

`evals/evals.json` covers the other half — whether a skill behaves correctly
when a model reads it. That is judged by a model and needs one to run; these
are decided by a script and run on every commit. Neither replaces the other.

**A check that never fails is not a check.** Before trusting a new one, break
the thing it guards and watch it fail.

