---
kind: architecture
title: Project Overview: AcmeWidgets
created: 2026-05-01
tags:
  - architecture
  - overview
updated: 2026-06-12
---

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
- See the [[form-validation|form validation pattern]].
- Decision: [[2026-05-10-use-react-query|use React Query]]
