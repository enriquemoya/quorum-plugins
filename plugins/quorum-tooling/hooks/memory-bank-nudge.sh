#!/bin/bash
# PostToolUse hook — fires after Write or Edit tool calls.
# Stack-agnostic. Suggests a memory-bank update when load-bearing files
# change. Consumers extend this with stack-specific triggers via
# .claude/hooks/memory-bank-nudge.local.sh (gitignored or per-repo).

echo "📝 Checking for memory bank update triggers..."

CHANGES=$(git diff --name-only HEAD 2>/dev/null)
NEEDS=0
export NEEDS

if [ -z "$CHANGES" ]; then
    echo "  ✅ No uncommitted changes"
    exit 0
fi

export CHANGES

# 1. Consumer-specific extension — runs first so the consumer can fire
#    triggers for its own stack (e.g. "auth helpers in src/test/resources/auth/
#    changed" for Karate, "composables in src/core/hooks/ changed" for Vue,
#    "*.csproj changed" for .NET, etc.). The extension is expected to
#    print "🔔 ..." lines for each trigger and set NEEDS=1 for any firing.
if [ -f ".claude/hooks/memory-bank-nudge.local.sh" ]; then
    # shellcheck disable=SC1091
    . .claude/hooks/memory-bank-nudge.local.sh
fi

# 2. Generic triggers — apply universally regardless of stack.

echo "$CHANGES" | grep -qE "^\.claude/(agents|commands|skills|hooks)/" \
    && echo "  🔔 Claude tooling changed → consider updating memory-bank/decisions/" \
    && NEEDS=1

echo "$CHANGES" | grep -qE "^(README|CHANGELOG|ARCHITECTURE)(\.md)?$" \
    && echo "  🔔 Top-level docs changed → memory-bank/architecture may need refresh" \
    && NEEDS=1

echo "$CHANGES" | grep -qE "^\.claude/profile\.yml$" \
    && echo "  🔔 .claude/profile.yml changed → all role-resolved agents may behave differently" \
    && NEEDS=1

[ "$NEEDS" -eq 0 ] && echo "  ✅ No triggers detected" || echo "  Run: /update-memory-bank"
