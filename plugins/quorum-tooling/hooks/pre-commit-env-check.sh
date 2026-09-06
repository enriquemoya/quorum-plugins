#!/bin/bash
# Claude Code PreToolUse hook — fires before every Bash tool call.
# Self-filters: only runs checks when the command is a git commit.
# Stack-agnostic. Generic secret-pattern checks run universally; consumers
# layer in stack-specific file/extension checks via
# .claude/hooks/pre-commit-env-check.local.sh (e.g. ban devsetup.json in
# .NET repos, ban credentials.json in Python repos, etc.).

INPUT=$(cat 2>/dev/null || echo "{}")
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null)

# Skip unless this is a git commit
if ! echo "$COMMAND" | grep -q "git commit"; then
    exit 0
fi

echo "Running pre-commit checks..."

# 1. Consumer-specific extension — runs first so a fail-fast exit (code 2)
#    can short-circuit the generic checks. Consumers can ban specific
#    filenames (devsetup.json, credentials.json, secrets.yml, etc.) and
#    scan their own language file extensions for connection strings.
if [ -f ".claude/hooks/pre-commit-env-check.local.sh" ]; then
    # shellcheck disable=SC1091
    . .claude/hooks/pre-commit-env-check.local.sh
    LOCAL_RC=$?
    if [ "$LOCAL_RC" -ne 0 ]; then
        exit "$LOCAL_RC"
    fi
fi

# 2. Generic: refuse to commit real env files. .env.example / .env.sample
#    / .env.template are explicitly allowed (templates with placeholders).
STAGED=$(git diff --cached --name-only 2>/dev/null)
for f in $STAGED; do
    base=$(basename "$f")
    if echo "$base" | grep -qE '^\.env(\.[a-zA-Z0-9_-]+)?$' && \
       ! echo "$base" | grep -qE '\.(example|sample|template)$'; then
        echo "Refusing to commit '$f' — looks like a real env file (not .example/.sample/.template)." >&2
        exit 2
    fi
done

# 3. Generic: scan staged diff for credential-shaped lines. Language-agnostic
#    — keys like "password", "api_key", "secret", "token", "connection_string"
#    immediately followed by a colon/equals and a non-empty alphanumeric value
#    are flagged. Warn only — false positives are common.
SECRETS=$(git diff --cached -U0 2>/dev/null | grep "^\+" | \
    grep -iE "(password|api[_-]?key|secret|token|connection[_-]?string)[\"'[:space:]]*[:=][\"'[:space:]]*[a-zA-Z0-9]" | \
    grep -v "^+++")
if [ -n "$SECRETS" ]; then
    echo "⚠ Potential secrets in staged diff (review before committing):" >&2
    echo "$SECRETS" >&2
fi

# 4. Generic: hardcoded URLs (warn only). Skips localhost / 127.0.0.1 /
#    example.com which are conventionally safe.
HARDCODED=$(git diff --cached -U0 2>/dev/null | grep "^\+" | \
    grep -iE "https?://[a-zA-Z0-9.-]+\.(com|net|org|io|co|dev|app)" | \
    grep -v "localhost" | grep -v "127\.0\.0\.1" | grep -v "example\." | grep -v "^+++")
if [ -n "$HARDCODED" ]; then
    echo "⚠ Hardcoded URLs in staged diff (consider configuration instead):"
    echo "$HARDCODED"
fi

echo "Pre-commit checks passed"
exit 0
