---
kind: pattern
title: API Error Handling
created: 2026-06-12
tags:
  - pattern
  - api-error-handling
updated: 2026-06-12
---

# Pattern: API Error Handling

## When to Use

Use this pattern when calling the REST API from the UI and you need consistent
error surfacing.

## Implementation

### Code Example

```ts
const res = await apiClient.get('/widgets');
if (!res.ok) throw new ApiError(res);
```

## Benefits
- One error shape across the app.

## Real Examples
- `src/api/ApiClient.ts` — typed fetch wrapper

## Related
- **Patterns:** [[form-validation]]
- **Decisions:** [[2026-05-10-use-react-query|use React Query]]

## See also
- The [[overview|project overview]] for where this sits.
