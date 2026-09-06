---
argument-hint: [base-branch]
description: Perform intelligent code review comparing current branch against a base branch. Stack-agnostic — resolves base branch and review path from the consumer's .claude/profile.yml.
---
# Git Code Review Command

Perform an intelligent code review comparing current branch against the base branch.

## Profile

This command reads `.claude/profile.yml` for:

- `{{profile.git.default_base_branch}}` — base branch when no argument is given (e.g. `Develop`, `main`, `master`)
- `{{profile.paths.config}}` — consumer config file path (defaults to `.claude/quorum-config.json`; consumers can override)
- `{{profile.paths.reviews}}` — review-output root (defaults to `.claude/reviews`)
- `{{profile.org.application_name_key}}` — JSON key inside `{{profile.paths.config}}` whose value is the application name used in the review path
- `{{role:conventions}}` — sprint numbering convention; the sprint anchor lives in the consumer's conventions skill (or `{{profile.org.sprint_anchor}}`), not in this command

## Setup Phase
1. **Set base branch:** Use the argument if provided; otherwise `{{profile.git.default_base_branch}}`.
2. **Display base branch:** Show "🔍 **REVIEWING AGAINST BASE BRANCH: [base_branch]**"
3. **Get application info:** Read `{{profile.paths.config}}` and extract `{{profile.org.application_name_key}}`.
4. **Ask for sprint number:** **ALWAYS prompt user to enter the current sprint number** — do not assume or skip this step. Calculate and suggest the current sprint number using the formula in the consumer's `{{role:conventions}}` skill (or its `{{profile.org.sprint_anchor}}` value: `{ sprint: N, start_date: YYYY-MM-DD, length_days: 14 }`). Present the calculated number as a suggestion but allow user to override.
5. **Create directory:** `{{profile.paths.reviews}}/[year]/Sprint[sprint]/[ApplicationName]/[cleaned-branch-name]/`
6. **Check for existing reviews:** Look for `review_*.md` files to determine review number for this session
7. **Set review filename:** Name output file as `review_{reviewnumber}.md` where reviewnumber increments from existing reviews

## Review Process
### Initial Review (no existing reviews)
1. **Get commits:** `git --no-pager log --pretty=format:'%h %s (%an)' [base_branch]..HEAD`
2. **Get changed files:** `git --no-pager diff --name-only [base_branch]..HEAD -- . ':!.claude'`
3. **Get diff:** `git --no-pager diff [base_branch]..HEAD -- . ':!.claude'` (30s timeout)
4. **Fallback on timeout:** Read individual files if diff times out
5. **Check local changes:** `git --no-pager diff --name-only HEAD`

### Follow-up Review (existing reviews found)
1. **Read last review:** Parse most recent review file for context
2. **Get recent changes:** Focus only on changes since last review
3. **Incremental analysis:** Review only new commits and local changes

## Review Content
Create comprehensive review with:
- **Summary** of changes, risks, and quality assessment
- **Commits section** listing all reviewed commits with hash, message, author
- **Security analysis** focusing on authentication, authorization, input validation
- **Code quality** assessment including architecture compliance, patterns, standards
- **Bug detection** with specific fixes
- **Performance** considerations
- **Recommendations** prioritized by severity

## Key Requirements
- **Focus on current file state:** Read actual files to verify current implementation, don't rely solely on diff interpretation
- **Security emphasis:** Verify the stack's authorization mechanism (e.g. attributes / decorators / middleware — see `{{role:primary-stack-expert}}`), session validation, and input validation
- **Scope documentation:** Always specify which files were reviewed vs skipped
- **Timeout handling:** Use 30s timeouts, fall back to individual file reads
- **Clear assessment:** Provide actionable recommendations with priority levels
