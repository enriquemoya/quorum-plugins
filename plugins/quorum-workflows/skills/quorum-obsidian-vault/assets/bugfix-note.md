---
key: {{ID}}
title: {{TITLE}}
kind: bugfix
status: {{STATUS}}
ticket: "{{TICKET_URL}}"
reporter:
repro-property:
created: {{DATE}}
tags:
  - bugfix
  - {{ID}}
---

# {{ID}} — {{TITLE}}

> [!info] Defect investigation overview. The value here is the root-cause trace, not the diff. Live progress & handoff: [[status]].

## Summary

<!-- The reported defect in one or two sentences. -->

## Repro & Captured Payloads

- **Reporter:**
- **Client / property:**
- **Captured payload(s):** <!-- absolute path, e.g. C:\tmp\PROJ-XXXXX_<property>_getfees.json -->
- **Steps to reproduce:**

## Root Cause vs Symptom

> [!note] Symptom
> <!-- what was reported / observed -->

> [!danger] Root cause
> <!-- the ACTUAL cause, with the precise code path and file:line — distinct from the symptom -->

## Bug Split

<!-- One ticket often hides several bugs. Record the split so nothing is lost or re-attempted. -->
- **Fixed:**
- **Deferred:** <!-- to which ticket -->
- **Discarded approach(es):** <!-- + WHY rejected, so a fresh session doesn't re-try it -->

## Verification

<!-- test counts (pre-existing flake vs real regression), E2E proof paths, seed/restore SQL left behind, commit hash + pushed? -->
-

## Adjacent Bugs Found

<!-- Bugs discovered in passing and how they're tracked. -->
-

## Source

- [{{ID}} in the tracker]({{TICKET_URL}})

## Related

- Status & handoff: [[status]]
- QA test plan: `{{QA_PLAN}}`
