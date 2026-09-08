# CONSTITUTION.md — what this marketplace will not do

Three articles. Few on purpose: every one is blocking in both audits and both
autonomy modes, and a constitution that fires on ordinary work is one people
learn to override.

Each is checkable by pointing at a file and a line. Anything softer than that
belongs in the memory bank as a convention.

## Article 1 — governance never names a stack

No file under `governance/` names a language, a framework, a test runner, a
package manager or a build command. Stack facts are discovered by
`/quorum-init` and live in `profile.yml`; a stage that needs one resolves
`{{profile.*}}` or `{{role:*}}`.

**Applies to:** all

**How an auditor checks it:** grep `plugins/*/governance/**` for framework and
tool names. Any hit is a violation. The prose may name a stack in an *example*
that illustrates resolution — `npm run type-check` shown beside `mypy .` in a
table of what a placeholder resolves to — but never as the thing a rule
branches on.

**Why:** this is the defect the template was extracted from. Its origin had an
orchestrator claiming to be stack-agnostic while its own `GLOBAL.md` declared
`TypeScript = UI only; C# = domain`. A rule naming a framework stops being true
the moment the process is reused, and it stops being true silently, because
everything downstream stays internally consistent.

## Article 2 — nothing names where this came from

No tracked file names a person, a prior organisation, an external product this
repository does not integrate with, a specific PR or CI run, or narrates a
change in the first person.

**Applies to:** all

**How an auditor checks it:** `python3 scripts/check.py`, the provenance check.
It scans every git-tracked file across six categories and exits non-zero on any
hit.

**Why:** a template that names its origin is not a template — a reader cannot
tell which parts are theirs to change. This is not hypothetical here: the check
was written on the day the README was still claiming an origin, having survived
every by-hand scrub before it.

## Article 3 — no guarantee without a check that has been observed failing

Any behaviour these documents state as a guarantee must have an assertion in
`scripts/check.py` or `scripts/e2e.py`, and that assertion must have been
watched failing against a deliberately broken tree before being trusted.

**Applies to:** all

**How an auditor checks it:** for each guarantee added or changed by the diff,
find the assertion. Then look for the record that it was seen to fail — a
commit message naming the injected defect and the resulting count, or a test
that reverts the fix.

**Why:** the product here is prose. Nothing compiles, so a guarantee with no
assertion is a sentence, and an assertion nobody has seen fail is a sentence
with a green tick beside it. Both suites were built this way: four injected
defects produce seven findings in `check.py`, and reverting four fixes produces
seven failures in `e2e.py`.
