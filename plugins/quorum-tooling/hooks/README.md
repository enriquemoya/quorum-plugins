# quorum-tooling hooks

Two stack-agnostic lifecycle hooks. They ship **dormant** — `quorum-tooling` deliberately
does **not** include a `hooks/hooks.json`, so installing the plugin never auto-registers them.
Each consumer repo opts in (see [Activating](#activating) below).

> **Why dormant?** A `hooks/hooks.json` here would auto-fire in *every* repo that installs
> `quorum-tooling`, including unrelated ones. These hooks are meant to be opt-in per repo so each
> consumer can layer its own stack-specific checks via the `.local.sh` extension points below.

## The hooks

| Script | Event | Matcher | What it does |
|---|---|---|---|
| `memory-bank-nudge.sh` | `PostToolUse` | `Write\|Edit` | After a file edit, checks `git diff` for load-bearing changes (`.claude/{agents,commands,skills,hooks}/`, top-level docs, `.claude/profile.yml`) and nudges `/update-memory-bank`. Warn-only. |
| `pre-commit-env-check.sh` | `PreToolUse` | `Bash` | Self-filters to `git commit` invocations. Blocks committing real `.env` files (exit 2); warns on credential-shaped lines and hardcoded URLs in the staged diff. |

Both are `#!/bin/bash` and use `git`, `grep`, and (for `pre-commit-env-check`) `python3` to parse
the tool-call JSON on stdin. **On Windows they run under Git Bash** — `bash` must be on `PATH`.

### Consumer extension points

Each hook sources an optional repo-local extension *first*, so a consumer can add stack-specific
triggers/checks without forking the script:

- `memory-bank-nudge.sh` → `.claude/hooks/memory-bank-nudge.local.sh`
  (print `🔔 ...` lines and set `NEEDS=1` for any custom trigger)
- `pre-commit-env-check.sh` → `.claude/hooks/pre-commit-env-check.local.sh`
  (may `exit 2` to fail-fast and block the commit before the generic checks run)

These `.local.sh` files live in the consumer repo, not here.

## Activating

In the consumer repo (one-time):

1. Copy the `hooks` object from [`hooks.json.example`](./hooks.json.example) into that repo's
   `.claude/settings.json` under the top-level `"hooks"` key — or save the whole object as the
   repo's own `.claude/hooks/hooks.json`. `${CLAUDE_PLUGIN_ROOT}` resolves to the cached
   `quorum-tooling` install dir, so the paths keep working after a plugin update.
2. (Optional) add `.claude/hooks/*.local.sh` extensions for stack-specific behavior.
3. Confirm `bash` is on `PATH` (Git Bash on Windows).

### Verify they fire

- **memory-bank-nudge:** edit a file under `.claude/skills/` (or a top-level `README`), then make any
  `Write`/`Edit` — the hook should print a `🔔 ... → consider updating memory-bank/` nudge.
- **pre-commit-env-check:** `git add` a file literally named `.env`, then attempt a `git commit` —
  the hook should refuse with `Refusing to commit '.env' ...` and exit code 2.
