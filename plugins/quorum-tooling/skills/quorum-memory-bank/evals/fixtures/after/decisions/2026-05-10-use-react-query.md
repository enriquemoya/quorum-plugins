---
kind: decision
title: Use React Query for server state
status: accepted
created: 2026-05-10
tags:
  - decision
  - 2026-05-10-use-react-query
updated: 2026-06-12
---

# Decision: Use React Query for server state

**Date:** 2026-05-10
**Status:** Accepted
**Deciders:** Platform team

## Context

Components were each hand-rolling fetch + cache + retry logic.

## Decision

We will adopt React Query for all server state because it standardizes caching,
retries, and invalidation.

## Consequences

### Positive
- Less bespoke caching code.

### Negative
- New dependency to learn.

## Alternatives Considered

### Alternative 1: SWR
**Why not chosen:** smaller feature set for our mutation-heavy screens.

## Related
- **Patterns:** [[api-error-handling]]
- **Supersedes:** [[2026-04-02-monorepo-structure|monorepo data layer]]
