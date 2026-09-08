# PRD — behavioural evals for the three pipeline skills

## Problem

Ten skills in this marketplace carry `evals/evals.json`; three do not, and they
are the three the pipeline depends on to function: `quorum-status` decides where
every unit of work is, `quorum-panel` decides whether a verdict may be rendered,
and `quorum-init` writes the profile every other skill resolves against.

`scripts/check.py` and `scripts/e2e.py` decide that the documents agree with
each other and that following them produces the right routing. Neither can
decide the question an eval asks: given this skill and this situation, does a
model do the right thing? A skill can be internally consistent, structurally
wired, and still read in a way that produces the wrong behaviour.

## Users

Whoever changes one of these three skills. Today they get a green suite from a
change that alters what an agent does, because nothing exercises the reading.

## Value

A change to how `quorum-status` describes a refusal can be caught before it
ships, rather than the first time an agent repairs a malformed state file
instead of stopping.

## Success

- Each of the three skills has an `evals/evals.json` in the format the ten
  existing ones use.
- Each covers its refusals, not only its happy path — the refusals are what the
  skill exists for.
- Every eval names the fixture it reads and the assertion it makes, so a failure
  says which behaviour changed.

## Non-goals

- Running the evals in CI. They need a model; the two scripts do not, and the
  distinction is why CI runs one and not the other.
- Evals for the ten skills that already have them.
- A new eval format. Ten files establish the shape; a second shape would mean
  the format is not one.

## Constitution articles touched

- **Article 3.** These evals are the assertions behind the guarantees those
  three skills state, so the article applies directly: each one has to be
  watched failing before it is trusted.
