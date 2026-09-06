# Common pitfalls

Failure modes that recur across integration scaffolds, and the check that
catches each one.

## Generated but never registered

The most common scaffold defect. Every file compiles, every test passes, and the
partner is invisible at runtime because it was never added to the settings
registry, the partner lookup, or the DI container.

**Check:** grep the reference partner's identifier across the whole workspace.
Every hit is a registration site your new partner also needs.

## Pattern mixing

Two pipeline families in the same codebase have different structural baselines.
Copying half from one and half from the other produces code that reviews cleanly
and behaves wrongly under load.

**Check:** name the pipeline family up front and pattern-match one reference
partner end to end. Never blend two.

## Silent transform drift

A field mapping that "looks obvious" — a date, a currency, an enum — carries an
implicit unit, timezone, or vocabulary difference. It surfaces as a data bug
weeks later, far from the integration.

**Check:** every row in the field-mapping table has an explicit transform, even
when the transform is `identity`.

## Retry on terminal errors

Treating every non-2xx as retryable turns a permanent partner-side rejection
into an infinite queue loop, and often into a rate-limit ban.

**Check:** the error taxonomy in the intake splits retryable from terminal, and
the generated handler branches on it.

## Non-idempotent ingest

Partners redeliver. Without an idempotency key the second delivery creates a
duplicate record.

**Check:** the intake names the idempotency key, and the ingest path enforces it
at the persistence boundary, not in memory.

## Credentials in fixtures

A sandbox credential pasted into a test fixture is a committed secret. It will
be found by a scanner, and rotating it breaks the test.

**Check:** fixtures reference credential *names*; real values come from the
environment at run time, and the test skips when they are absent.

## Tests that mock the thing under test

A generated test that mocks the transport *and* the mapper asserts only that the
mock was called. It passes forever, including when the mapping is wrong.

**Check:** mock the transport, exercise the real mapper against a captured
payload from the intake.
