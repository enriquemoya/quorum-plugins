---
name: quorum-sql-review
argument-hint: [base-branch]
description: Review SQL migrations and schema changes on the current branch against a base branch — idempotency, destructive operations, lock and rewrite risk, naming conventions, table completeness, environment guards, and deployment ordering. The database counterpart to quorum-code-review; use whenever a changeset touches .sql files, migrations, or schema DDL.
---

# SQL Migration Review

Review the SQL in a changeset the way a careful DBA would: not "does it parse",
but **what happens when this runs against a live database, twice, at scale, in
the wrong order.**

This is the sibling of `/quorum-code-review`. That skill reviews application
code and flags SQL only in passing; this one owns the database surface.

Base branch: given as an argument, else `profile.git.default_base_branch`, else
the first of `develop` / `main` / `master` that exists as a ref.

## Git lifecycle contract

This skill **writes** `sql-review_{N}.md` to disk. It does **NOT** `git add` or
`git commit`, and it **never edits a migration** — it reports. Fixing is the
author's job; staging is the orchestrator's (or the human's).

---

## Setup

1. **Resolve the base branch** (above). Display: `🔍 **SQL REVIEW AGAINST: [base_branch]**`
2. **Read the profile.** From `profile.yml`:
   - `database.dialect` — `postgres` (default) / `mysql` / `sqlserver`. Dialect-specific
     checks below are skipped with a note when the dialect does not match.
   - `database.migrations_path` — where migrations live (default: search for
     `**/migrations/**/*.sql`, `**/db/**/*.sql`)
   - `database.filename_pattern` — the migration filename convention, if any
   - `database.helpers` — names of the repo's idempotency/env helper routines
   - `database.conventions` — overrides for anything in
     [`references/sql-conventions.md`](references/sql-conventions.md)
   - **Nothing declared is not a blocker.** Fall back to the documented defaults
     and say so in the review's Scope section — a convention you assumed is a
     convention the reader must be able to check.
3. **Get the application name** from `.claude/quorum-config.json` if present.
4. **Determine the output path:** `{{profile.paths.reviews}}/{year}/Sprint{N}/{App}/{branch}/sql-review_{N}.md`,
   incrementing `{N}` past any existing `sql-review_*.md` in that directory.

## Gather

```bash
git --no-pager diff --name-only [base]..HEAD -- '*.sql'
git --no-pager diff [base]..HEAD -- '*.sql'          # 30s timeout
git --no-pager log --pretty=format:'%h %s (%an)' [base]..HEAD
```

- **Also catch schema DDL outside `.sql`** — ORM migration files (EF `Migrations/*.cs`,
  Alembic, ActiveRecord, Prisma), and any `CREATE TABLE` in a string literal.
- **On timeout**, read the changed files individually rather than giving up.
- **If there is a previous `sql-review_*.md`**, read it and review only what
  changed since — but re-check every Critical it raised, and say whether each
  was fixed, argued down, or ignored.
- **If no SQL changed**, say exactly that and stop. Do not manufacture findings.

---

## The checks

Run every category. For each finding record: **severity**, `file:line`, what is
wrong, what happens if it ships, and the fix.

### 1. Idempotency — can this run twice?

The single highest-value question. A migration that is not re-runnable will
eventually be re-run.

- [ ] Every `CREATE` is guarded: `IF NOT EXISTS`, `CREATE OR REPLACE`, an
      existence check against `INFORMATION_SCHEMA`, or the repo's tag-guard helper
- [ ] **DML (`INSERT` / `UPDATE` / `DELETE`) has an idempotency guard** —
      `ON CONFLICT`, a `WHERE NOT EXISTS`, or a tag guard. Unguarded DML that
      duplicates rows on a second run is **Critical**
- [ ] `ALTER TABLE ... ADD COLUMN` uses `IF NOT EXISTS` or a catalog check
- [ ] Re-running produces no error *and* no duplicate effect. These are different
      failures — a script that errors on re-run is Major; one that silently
      doubles data is Critical

### 2. Destructive and irreversible operations

Flag every one of these, even when correct — the reviewer's job is to make sure
a human consciously approved them.

| Operation | Severity | Why |
|---|---|---|
| `DROP TABLE` / `DROP COLUMN` | **Critical** | Unrecoverable without a restore |
| `TRUNCATE` | **Critical** | Same, and it bypasses row triggers |
| `DELETE` / `UPDATE` with no `WHERE` | **Critical** | Whole-table mutation |
| Column or table `RENAME` | **Critical** | Breaks deployed code reading the old name |
| `ALTER COLUMN TYPE` that narrows | **Critical** | Silent truncation or a failed migration mid-deploy |
| `DROP` / re-`CREATE` of a constraint or index | **Major** | Window with no enforcement |
| `NOT NULL` added without a `DEFAULT` or a prior backfill | **Major** | Fails on existing rows |

For a rename, check whether the change ships as **expand → migrate → contract**
(add new, dual-write, backfill, then drop) or as a single breaking step. A single
step is only acceptable with a stated deployment freeze.

### 3. Lock and rewrite risk

What this does to a table with real row counts. See
[`references/migration-safety.md`](references/migration-safety.md) for the
per-operation detail.

- [ ] `CREATE INDEX` on a large table uses `CONCURRENTLY` (and therefore sits
      **outside** any transaction/DO block — flag the combination, it is a common bug)
- [ ] `ADD COLUMN` with a **volatile** default (e.g. `clock_timestamp()`,
      `gen_random_uuid()`) — rewrites the whole table on PostgreSQL
- [ ] Foreign keys added as `NOT VALID` then `VALIDATE CONSTRAINT` separately,
      rather than one blocking `ADD CONSTRAINT`
- [ ] No long-running `UPDATE` backfill inside a single transaction — it should
      be batched
- [ ] `ALTER TABLE` statements against the same table are batched into one
      statement where the dialect supports it
- [ ] Nothing holds an `ACCESS EXCLUSIVE` lock while doing slow work

### 4. New-table completeness

Every new table, checked against the conventions in
[`references/sql-conventions.md`](references/sql-conventions.md):

- [ ] **A `PRIMARY KEY` is defined — Critical if absent.** PostgreSQL logical
      replication needs a primary key or an explicit replica identity; without one
      the table silently breaks replication
- [ ] A sequence/identity backs the key, and the sequence is `OWNED BY` the column
      (otherwise it survives the table and leaks)
- [ ] Audit timestamp columns present per convention (`created_date`,
      `last_modified_date`)
- [ ] Audit triggers use the repo's **shared** trigger functions — a hand-rolled
      per-table trigger function is a Major finding (drift across tables)
- [ ] Columns are `NOT NULL` unless genuinely optional
- [ ] Foreign-key columns carry an actual `REFERENCES` constraint, not just a
      naming convention
- [ ] Column comments present, if the repo's convention requires them
- [ ] Text columns use the right type for case-sensitivity needs

### 5. Naming conventions

Checked against `references/sql-conventions.md`, or the repo's overrides. These
are **Minor** on their own — but a systematic breach across a changeset is Major,
because it is the beginning of a second convention.

- [ ] `lower_case_with_underscores`, singular object names
- [ ] Primary key column named per convention; FK columns named `{parent}_id`
- [ ] Object suffixes correct: view / function / trigger / trigger-function /
      PK / FK / unique / check / index / sequence
- [ ] Column names do not repeat the table name

### 6. Environment and secrets

- [ ] **No literal credential, password, token, or connection string.** Any hit
      is **Critical**, and say so plainly — a secret in a migration is a secret in
      git history forever
- [ ] Anything that must not run in production is wrapped in the repo's
      environment guard, and the guard **returns early** rather than merely
      branching
- [ ] Environment-specific values come from a lookup, not from a hardcoded
      per-environment `IF`
- [ ] `GRANT` / `REVOKE` / role changes are called out explicitly for a human to
      approve
- [ ] `SECURITY DEFINER` functions pin a `search_path` — otherwise they are a
      privilege-escalation vector

### 7. Ordering and deployment coupling

- [ ] The migration's phase/ordering places it after anything it depends on
      (referenced tables, functions) and before anything depending on it
- [ ] If the script requires **new application code** to already be deployed,
      that is stated — and the ordering reflects it
- [ ] If **existing** application code will break the moment this runs (a rename,
      a dropped column), that is called out as a deployment-sequencing risk, not
      just a schema change
- [ ] Filename matches the repo's convention, and its number does not collide
      with another migration on the same branch or on the base branch

### 8. Correctness details

- [ ] Transaction boundaries are right — nothing that cannot run in a transaction
      (`CREATE INDEX CONCURRENTLY`, `VACUUM`, some `ALTER TYPE`) sits inside one
- [ ] `BEGIN`/`END` comment markers name the ticket, per convention
- [ ] Index definitions actually serve a query — flag an index whose columns
      duplicate an existing index's prefix as redundant
- [ ] `CHECK` constraints and defaults will hold for existing rows
- [ ] Collation / case-sensitivity assumptions are explicit for text keys

---

## Output

Write the review to the path resolved in Setup:

```markdown
# SQL Review — {branch} — review {N}

**Base:** {base_branch} · **Files:** {n} SQL / {n} other DDL · **Dialect:** {dialect}
**Verdict:** PASS | PASS WITH RISKS | FAIL

## Summary
{2–4 sentences: what this changeset does to the schema and the one thing that
matters most about it}

## Scope
- Reviewed: {files}
- Skipped: {files, and why}
- Conventions applied: {profile-declared | documented defaults — say which}

## Commits
| Hash | Message | Author |

## Critical
{each: file:line · what · what happens if it ships · the fix}

## Major
## Minor
## Notes
{things that are fine but worth a human's eye — destructive ops that look
deliberate, deployment-ordering requirements, anything you could not verify}
```

**Verdict rules.** Any Critical → `FAIL`. No Critical but a destructive or
lock-risky operation present → `PASS WITH RISKS`. Otherwise `PASS`.

---

## Rules

- **Never edit a migration.** Report the fix; the author applies it.
- **Every finding cites `file:line`.** A finding without a location is not
  actionable.
- **State the consequence, not just the rule.** "No `WHERE` clause" is weak;
  "`UPDATE` with no `WHERE` — rewrites every row in `customer` on deploy" is a
  finding someone will act on.
- **Say what you could not check.** No access to row counts, no dialect
  confirmation, an unreadable ORM migration — an unstated gap reads as a pass.
- **Do not invent conventions.** If the repo declares none and the defaults do
  not obviously apply, review idempotency, destructiveness, and lock risk — which
  are universal — and note that naming was not checked.
- **A clean review is a valid result.** Do not pad it with nits to look thorough.

## Composing

- `/quorum-code-review` — application-code review; run both on a changeset that
  touches code and schema together
- `/quorum-sprint-number` — for the review path's sprint segment
