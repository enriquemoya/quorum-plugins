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
- **Patterns:** `form-validation`
- **Decisions:** [use React Query](../decisions/2026-05-10-use-react-query.md)

## See also
- The [project overview](../architecture/overview.md) for where this sits.
