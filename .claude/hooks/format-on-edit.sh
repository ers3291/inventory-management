#!/bin/bash
# PostToolUse hook: format files Claude edits with the client's Prettier.
#
# Claude Code passes hook input as JSON on stdin (there is no $CLAUDE_FILE_PATH variable);
# the edited path is at .tool_input.file_path for Edit/Write/MultiEdit.
#
# Only formats files inside client/ with extensions Prettier handles there, and uses the
# project's pinned Prettier from client/node_modules (never downloads one via npx).
# Always exits 0 so a formatting problem can never block Claude's edit.

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$file" ] && exit 0

# Resolve the project root from this script's location (.claude/hooks/ -> repo root)
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
client="$root/client"
prettier="$client/node_modules/.bin/prettier"

case "$file" in
  "$client"/src/*.vue|"$client"/src/*.js|"$client"/src/*.css|"$client"/src/*.json) ;;
  *) exit 0 ;;
esac
[ -x "$prettier" ] || exit 0
[ -f "$file" ] || exit 0

# Run from client/ so Prettier picks up client/.prettierrc.json
(cd "$client" && "$prettier" --write --log-level warn "$file") >/dev/null 2>&1 || true
exit 0
