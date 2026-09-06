---
kind: pattern
title: Form Validation
created: 2026-06-12
tags:
  - pattern
  - form-validation
updated: 2026-06-12
---

# Pattern: Form Validation

## When to Use

Use this pattern when capturing user input that must be validated before submit.

Don't use this pattern when:
- The form has a single trivial field with no rules.

## Implementation

### Code Example

```tsx
const schema = z.object({ email: z.string().email() });
```

### Step-by-Step
1. Define a zod schema.
2. Resolve it in the form hook.

## Benefits
- Single source of truth for rules — fewer drift bugs.

## Pitfalls

### Common Mistake 1
**Wrong:** validating only on submit.
**Correct:** validate on blur + submit.
**Why:** users get feedback sooner.

## Real Examples
- `src/components/LoginForm.tsx` — login validation

## Related
- **Decisions:** [[2026-05-10-use-react-query|adopt React Query]]
- **Architecture:** see [[overview]]
- **Patterns:** [[api-error-handling]]
