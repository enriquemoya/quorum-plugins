# Project Overview: AcmeWidgets

**Generated:** 2026-05-01

## Tech Stack
- TypeScript, React, Node.js, PostgreSQL

## Project Structure
- `src/components/` — React components
- `src/api/` — REST client + error handling
- `src/db/` — repositories

## Key Components
- LoginForm — credential capture + validation
- ApiClient — typed fetch wrapper

## Data Flow
- UI → ApiClient → REST → repositories → PostgreSQL

## Related
- See the [form validation pattern](../patterns/form-validation.md).
- Decision: [use React Query](../decisions/2026-05-10-use-react-query.md)
