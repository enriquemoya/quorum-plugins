# SQL conventions — the default rulebook

These are the conventions `/quorum-sql-review` checks against **when the repo
declares none of its own**. They are a reasonable PostgreSQL house style, not
law. Override any of them under `database.conventions` in `profile.yml`:

```yaml
database:
  dialect: postgres
  migrations_path: db/migrations
  filename_pattern: "{db}_{phase}_S{sprint}_{seq}_{ticket}.sql"
  helpers:
    tag_has_run: deploy_tag_has_run
    get_environment_type: deploy_get_environment_type
    insert_audit_trigger_fn: insert_create_modified_date_tf
    update_audit_trigger_fn: update_modified_date_tf
  conventions:
    case: lower_snake
    plurality: singular
    pk_column: id
    audit_columns: [created_date, last_modified_date]
    require_column_comments: true
    suffixes:
      view: _v
      function: _f
```

When the repo declares a convention, **the repo wins** — the reviewer's job is
to enforce the codebase's consistency, not this document's taste.

---

## Naming

### General

| Rule | Correct | Wrong |
|---|---|---|
| Case | `lower_case_with_underscores` | `CustomerOrder`, `customerOrder` |
| Plurality | singular — `customer` | `customers` |
| Primary key column | `id` | `customer_id`, `pk_customer` |
| Foreign key column | `{referenced_table}_id` — `job_id` | `fk_job`, `jobRef` |
| Column names | `name` | `customer_name` (repeats the table) |

The last rule has one exception: an ID reference *should* carry the referenced
table's name, because that is what makes the join readable.

### Object suffixes

| Object | Suffix | Example |
|---|---|---|
| View | `_v` | `customer_summary_v` |
| Function | `_f` | `calculate_total_f` |
| Trigger | `_t` | `customer_audit_insert_t` |
| Trigger function | `_tf` | `customer_audit_tf` |
| Primary key | `_pk` | `customer_pk` |
| Foreign key | `_fk` | `order_customer_fk` |
| Unique constraint | `_u` | `customer_email_u` |
| Check constraint | `_c` | `order_amount_c` |
| Index | `_idx` | `customer_email_idx` |
| Sequence | `_seq` | `customer_seq` |

A suffix breach in isolation is **Minor**. The same breach repeated across a
changeset is **Major** — that is a second convention being born.

---

## New table: the completeness checklist

A new table is complete when it has all of:

1. **A primary key.** Not optional. PostgreSQL logical replication requires a
   primary key or an explicitly set replica identity; a table without one
   silently breaks replication rather than failing loudly.
2. **A sequence or identity backing the key**, and — for an explicit sequence —
   `ALTER SEQUENCE ... OWNED BY {table}.{column}` so it is dropped with the table
   instead of leaking.
3. **Audit timestamps:** `created_date` and `last_modified_date`, both
   `timestamptz DEFAULT clock_timestamp() NOT NULL`.
4. **Audit triggers** wired to the repo's *shared* trigger functions —
   `insert_create_modified_date_tf()` and `update_modified_date_tf()` by default.
   A hand-rolled per-table trigger function is a finding: it will drift from the
   others and nobody will notice until the timestamps disagree.
5. **Column comments** on every column, when `require_column_comments` is on.
6. **`NOT NULL` by default.** Nullable is a decision, not a default.
7. **Real foreign keys.** A `BIGINT` column named `job_id` with no `REFERENCES`
   clause is a naming convention pretending to be a constraint.
8. **An existence guard** — wrapped in `IF NOT EXISTS` on
   `INFORMATION_SCHEMA.TABLES`, or the equivalent.

### Reference shape

```sql
-- BEGIN: {TICKET} — {description}
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 'x' FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = current_schema() AND TABLE_NAME = 'customer')
    THEN
        CREATE SEQUENCE IF NOT EXISTS "customer_seq"
            INCREMENT BY 1 START WITH 1 NO MAXVALUE;

        CREATE TABLE IF NOT EXISTS "customer" (
            "id" BIGINT NOT NULL
                 DEFAULT nextval('customer_seq'::regclass)
                 CONSTRAINT "customer_pk" PRIMARY KEY,
            "email" citext NOT NULL,
            "created_date" timestamptz DEFAULT clock_timestamp() NOT NULL,
            "last_modified_date" timestamptz DEFAULT clock_timestamp() NOT NULL);

        ALTER SEQUENCE "customer_seq" OWNED BY "customer"."id";

        CREATE TRIGGER customer_create_date_t BEFORE INSERT ON customer
            FOR EACH ROW EXECUTE FUNCTION insert_create_modified_date_tf();
        CREATE TRIGGER customer_modified_date_t BEFORE UPDATE ON customer
            FOR EACH ROW EXECUTE FUNCTION update_modified_date_tf();

        COMMENT ON COLUMN "customer"."id" IS 'Unique identifier';
        COMMENT ON COLUMN "customer"."email" IS 'Login email, case-insensitive';
    END IF;
END $$ LANGUAGE 'plpgsql';
-- END: {TICKET}
```

### Column types

- **Case-insensitive text** → `citext`. Case-sensitive → `text`. Avoid
  `varchar(n)` unless the length is a real domain constraint, not a guess.
- **Foreign keys** → `BIGINT` matching the parent's key type exactly. A type
  mismatch across a join silently disables index usage.
- **Money** → `numeric`, never `float`.
- **Timestamps** → `timestamptz`. A naked `timestamp` discards the offset and
  the bug surfaces during a DST transition.

---

## Structure

### The DO-block wrapper

Wrap migration bodies in an anonymous block so guards and error handling are
consistent:

```sql
DO $$
BEGIN
    -- body
END $$ LANGUAGE 'plpgsql';
```

**Do not wrap** — these are already idempotent standalone DDL, and wrapping some
of them actively breaks:

- `CREATE OR REPLACE VIEW`
- `CREATE OR REPLACE FUNCTION`
- `CREATE INDEX IF NOT EXISTS`
- **`CREATE INDEX CONCURRENTLY`** — cannot run inside a transaction block at all.
  A `CONCURRENTLY` index inside a `DO` block is a hard error at runtime, and it
  is one of the most common review findings.

### Ticket markers

Every script opens and closes with a comment naming its ticket:

```sql
-- BEGIN: {TICKET} — {description}
-- END: {TICKET}
```

This is what makes a migration greppable back to the change that motivated it.

### Filenames

The default pattern is `{db}_{phase}_S{sprint}_{seq}_{ticket}.sql`, e.g.
`portal_1_S285_1_PROJ1234.sql`. What the reviewer actually checks:

- the filename matches whatever `database.filename_pattern` declares
- the sequence number does not collide with another migration on this branch or
  on the base branch — a collision means one of them will be skipped or applied
  out of order, depending on the runner
- the **phase** is right: a new table lands in a later phase than the migrations
  that reference it; anything depending on freshly deployed application code
  lands after that deploy

---

## Environment guards

When a migration must behave differently per deployment tier, it reads the
environment from a lookup rather than branching on a hardcoded hostname or
database name:

```sql
DO $$
DECLARE
    env varchar;
BEGIN
    SELECT environment_type INTO env FROM control.environment_info LIMIT 1;

    IF env = 'p' THEN
        RAISE NOTICE 'skipped in production';
        RETURN;
    END IF;

    -- non-production work here
END $$ LANGUAGE 'plpgsql';
```

Two rules the reviewer enforces:

1. **Guard by early `RETURN`, not by branching.** A branch that merely skips the
   dangerous statement leaves the rest of the block running in production.
2. **Prefer a catalog check over an environment check** where one exists. If the
   real question is "is this materialized view populated", ask
   `pg_matviews.ispopulated` — environment detection is for logic that genuinely
   differs by tier, not as a proxy for state.

The table and column names above are the defaults; the repo's own are read from
`database.helpers` in `profile.yml`.
