# CORS preflight failures on the widgets endpoint

## Problem

Browser calls to `/widgets` fail with a CORS error in staging only.

## Symptoms
- `OPTIONS /widgets` returns 403.
- Network tab shows no `Access-Control-Allow-Origin` header.

## Root Cause

The staging gateway stripped the preflight response headers.

## Solution

Allowlist the staging origin at the gateway and pass through preflight headers.

## Prevention

Add a smoke test that asserts the preflight headers in each environment.

## Related
- **Patterns:** [api error handling](../patterns/api-error-handling.md)
- **Decisions:** [[ghost-decision]]
