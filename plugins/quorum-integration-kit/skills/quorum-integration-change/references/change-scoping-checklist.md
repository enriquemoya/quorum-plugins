# Change-scoping checklist

Walk this before calling a scoping report complete.

## Identification

- [ ] Partner(s) identified, and confirmed against the changed files or the branch
- [ ] Ticket key resolved; full acceptance criteria fetched, not the summary
- [ ] Every repo the partner spans is checked out and current

## Coverage

- [ ] Every AC has at least one change site, or an explicit "already satisfied"
      verdict with evidence
- [ ] Every change site names `file:symbol`, not a directory
- [ ] Each site is labelled `modify` / `add` / `remove` / `migrate` /
      `register` / `test`

## Cross-cutting

- [ ] Settings registry: new or renamed keys identified
- [ ] Migrations: schema change identified; backfill decided
- [ ] Shared code: does this touch a base class, a shared mapper, or a common
      contract that other partners also use?
- [ ] Satellite repos: is the other half of a contract change accounted for?
- [ ] Registration: does anything new need adding to the partner lookup or DI?
- [ ] Idempotency: does redelivery behave differently after this change?
- [ ] Retry semantics: does the error taxonomy change?

## Blast radius

- [ ] Named the partners *other than* the ticket's that this change can affect
- [ ] Named the existing tests that will now fail, and why that is correct
- [ ] Named anything that needs a coordinated deploy across repos

## Honesty

- [ ] Open questions listed rather than resolved by assumption
- [ ] Anything the analyzer could not determine is marked unknown, not omitted
