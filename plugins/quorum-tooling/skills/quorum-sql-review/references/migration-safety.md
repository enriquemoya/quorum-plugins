# Migration safety — locks, rewrites, and blast radius

What each operation actually does to a live table. Written for PostgreSQL; the
principles carry to other engines but the lock names and the version-specific
escapes do not.

The reviewer's question is never "is this valid SQL". It is: **what happens when
this runs against the production table, at its real row count, while traffic is
hitting it.**

---

## The lock ladder

| Lock | Blocks | Taken by |
|---|---|---|
| `ACCESS EXCLUSIVE` | *everything*, including `SELECT` | `ALTER TABLE` (most forms), `DROP`, `TRUNCATE`, `REINDEX` |
| `SHARE ROW EXCLUSIVE` | writes, schema changes | `CREATE TRIGGER`, `ADD FOREIGN KEY` |
| `SHARE` | writes | `CREATE INDEX` (non-concurrent) |
| `SHARE UPDATE EXCLUSIVE` | schema changes only | `CREATE INDEX CONCURRENTLY`, `VALIDATE CONSTRAINT` |

The severity of a lock is **duration × level**. An `ACCESS EXCLUSIVE` held for
2 ms is fine. Held for 40 seconds while a table rewrites, it is an outage —
every query behind it queues, and the queue itself takes the site down long
before the migration finishes.

**The queue is the real danger.** An `ACCESS EXCLUSIVE` request waits behind
running queries *and* blocks everything that arrives after it. One slow
`SELECT` plus one `ALTER TABLE` equals a full stall. This is why a
`lock_timeout` on migrations is worth recommending.

---

## Operations, by risk

### Safe — metadata only

- `ADD COLUMN` with **no** default, or with a **constant** default (PG 11+)
- `DROP CONSTRAINT`
- `ALTER COLUMN DROP NOT NULL`
- `RENAME` (safe to the *database*; catastrophic to deployed code — see below)
- Adding an index `CONCURRENTLY`

### Rewrites the whole table

Every row is rewritten; the table is locked `ACCESS EXCLUSIVE` throughout.

| Operation | Escape |
|---|---|
| `ADD COLUMN` with a **volatile** default (`clock_timestamp()`, `gen_random_uuid()`, `nextval()`) | Add the column nullable, backfill in batches, then set the default |
| `ALTER COLUMN TYPE` (most conversions) | Add a new column, dual-write, backfill, swap, drop |
| `SET NOT NULL` on a large table | Add a `CHECK (col IS NOT NULL) NOT VALID`, `VALIDATE`, then `SET NOT NULL` — the validated check lets PG skip the scan (PG 12+) |

The volatile-default case is the one that most often reaches production
unnoticed, because a constant default is free and the two look identical in a
diff. `DEFAULT now()` is safe (stable within the statement);
`DEFAULT clock_timestamp()` is not.

### Long lock without a rewrite

| Operation | Escape |
|---|---|
| `CREATE INDEX` (non-concurrent) | `CREATE INDEX CONCURRENTLY` — but it **cannot run inside a transaction block**, so it must live outside any `DO $$` / `BEGIN` wrapper, and it needs a retry path because it can leave an `INVALID` index behind on failure |
| `ADD FOREIGN KEY` | `ADD CONSTRAINT ... NOT VALID`, then `VALIDATE CONSTRAINT` in a separate statement — validation takes only `SHARE UPDATE EXCLUSIVE` |
| `ADD CHECK` | Same `NOT VALID` → `VALIDATE` split |

### Irreversible

- `DROP TABLE` / `DROP COLUMN` — recoverable only from a backup
- `TRUNCATE` — also bypasses row-level triggers, so audit trails miss it
- `DELETE` / `UPDATE` with no `WHERE`

For these the review does not ask "is it safe" — nothing makes them safe. It
asks: **is it deliberate, is it reversible by a restore whose RPO someone has
checked, and does a human know it is in this changeset?**

---

## Renames and the expand/contract pattern

A rename is trivially safe for the database and breaks every deployed process
still using the old name. The safe shape is three deploys, not one:

1. **Expand** — add the new column/table. Application dual-writes; reads still
   use the old.
2. **Migrate** — backfill in batches. Flip reads to the new. Both still exist.
3. **Contract** — after the old is provably unused, drop it.

A single-step rename is acceptable **only** with a stated deployment freeze, and
the review should say so out loud rather than let it pass as ordinary DDL.

The same shape applies to a narrowing type change, a column split, and a table
split. When a migration collapses these into one step, that is the finding.

---

## Backfills

A backfill is not DDL, and it fails differently:

- **Batch it.** A single `UPDATE` over millions of rows holds one transaction,
  bloats WAL, blocks vacuum, and cannot be interrupted cleanly.
- **Make it resumable.** Drive it off a key range or a null-check so a rerun
  picks up where it stopped.
- **Keep it out of the migration** when it takes more than a few seconds — a
  migration runner that times out mid-backfill leaves an ambiguous state.
- **Never backfill and constrain in the same transaction.** Backfill, verify,
  then add the constraint.

---

## Review heuristics

Questions worth asking of any migration diff:

- **How many rows?** If nobody knows, that is the first finding. The same DDL is
  trivial at 10³ rows and an outage at 10⁸.
- **What is the worst-case lock hold?** Multiply the slowest plausible statement
  by the lock level.
- **What happens if it fails halfway?** Is the state resumable, or does it need a
  human with psql?
- **What breaks if the application deploy lands after this instead of before?**
  Both orders should be considered; only one is usually safe.
- **Is there a rollback?** For destructive operations, "restore from backup" is
  an answer — but only if someone has said it out loud and knows the RPO.

## Recommendations worth making

- Set `lock_timeout` (and `statement_timeout`) on migration sessions, so a
  blocked `ALTER` fails fast instead of queueing traffic behind it.
- Prefer `IF NOT EXISTS` over "we'll only run it once."
- Keep one logical change per migration file — a file that both creates a table
  and backfills another is two different failure modes sharing a transaction.
