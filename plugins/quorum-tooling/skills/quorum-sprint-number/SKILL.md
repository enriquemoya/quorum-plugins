---
name: quorum-sprint-number
description: Calculate and display the current sprint number
---

# Sprint Number Calculator

Calculate the current sprint number and display it. Each sprint lasts exactly 2 weeks (14 days).

## Anchor Point
- **Sprint 284** started on **February 11, 2026** and runs through end of day **February 24, 2026**

## Formula
```
Current Sprint = 284 + floor((days since February 11, 2026) / 14)
```

Where "days since February 11, 2026" is calculated from the start of February 11, 2026 UTC to today's date.

## Examples
| Date | Days Since Feb 11 | Calculation | Sprint |
|---|---|---|---|
| Feb 11, 2026 | 0 | 284 + floor(0/14) = 284 | 284 |
| Feb 20, 2026 | 9 | 284 + floor(9/14) = 284 | 284 |
| Feb 24, 2026 | 13 | 284 + floor(13/14) = 284 | 284 |
| Feb 25, 2026 | 14 | 284 + floor(14/14) = 285 | 285 |
| Mar 11, 2026 | 28 | 284 + floor(28/14) = 286 | 286 |

## Usage
When invoked directly, calculate and display:
```
Current Sprint: {sprint_number}
Sprint dates: {start_date} — {end_date}
```

## For Other Skills
This file is the **single source of truth** for sprint calculation. Other skills that need the sprint number should invoke `/quorum-sprint-number` to get the current sprint.
