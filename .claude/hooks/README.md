# Claude Code Hooks

This directory contains hooks for Claude Code that automate tasks during development.

## Available Hooks

### 1. Post Tool Use Logger (`post-tool-use.sh`)

**Purpose**: Logs all tool usage to help with debugging and tracking Claude's actions.

**Trigger**: Runs after every tool call (Read, Write, Edit, Bash, etc.)

**Configuration**: Enabled in `.claude/settings.local.json` under the `hooks.PostToolUse` section.

**Log Location**: `.claude/logs/tool-usage-YYYY-MM-DD.log`

**Log Format**:
```
=== Tool Usage: 2025-10-16 09:15:23 ===
Tool: Read
Session: abc123
Input: {"file_path": "/path/to/file.js"}
Response: {"content": "..."}
```

**Features**:
- Creates daily log files with timestamps
- Uses `jq` for clean JSON parsing (falls back to raw logging if jq is not installed)
- Logs tool name, session ID, input parameters, and response
- Never blocks tool execution

**Usage**:
The hook runs automatically once configured. To view logs:
```bash
# View today's log
cat .claude/logs/tool-usage-$(date +%Y-%m-%d).log

# View logs with live updates
tail -f .claude/logs/tool-usage-$(date +%Y-%m-%d).log

# Search logs for specific tool
grep "Tool: Bash" .claude/logs/*.log
```

**Requirements**:
- Optional: `jq` for better JSON formatting (`brew install jq` on macOS)

### 2. User Prompt Submit Hook (`user-prompt-submit.sh`)

**Purpose**: Runs pre-commit linting checks when Claude creates commits.

**Trigger**: Runs when the user's prompt contains "commit" or "git commit"

**Features**:
- Lints Python files with `ruff`
- Lints JavaScript/Vue files with `eslint`
- Blocks commits if linting fails

### 3. Format on Edit (`format-on-edit.sh`)

**Purpose**: Formats every frontend file Claude edits with Prettier, so Claude's output always matches the project style.

**Trigger**: `PostToolUse` on `Edit|Write|MultiEdit`.

**Behavior**:
- Reads the hook input JSON from stdin and takes `.tool_input.file_path` (Claude Code does not set a `$CLAUDE_FILE_PATH` variable).
- Only formats `client/src/**/*.{vue,js,css,json}`; everything else is ignored.
- Uses the pinned Prettier in `client/node_modules` with `client/.prettierrc.json` (no semicolons, single quotes, 120 columns), so it never downloads anything.
- Always exits 0, so it can't block an edit.

**Enable it** by adding this to `.claude/settings.json` (project, shared) or `.claude/settings.local.json` (just you), or via `/hooks`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-on-edit.sh" }
        ]
      }
    ]
  }
}
```

**Requirements**: `jq` and `cd client && npm install` (Prettier is a devDependency).

**Test it**: ask Claude to "Add an extra function to api.js with deliberately messy formatting", and the saved file should come out formatted.

## Disabling Hooks

To temporarily disable a hook, you can:

1. **Comment out in settings**: Edit `.claude/settings.local.json` and remove the hook configuration
2. **Remove execute permission**: `chmod -x .claude/hooks/post-tool-use.sh`
3. **Delete the hook file**: `rm .claude/hooks/post-tool-use.sh`

## Creating Custom Hooks

See the [Claude Code Hooks Documentation](https://docs.claude.com/en/docs/claude-code/hooks.md) for more information on creating custom hooks.

### Available Hook Events:
- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution
- `UserPromptSubmit` - When user submits a prompt
- `Stop` - When agent finishes responding
- `SubagentStop` - When subagent finishes
- `SessionStart` - When session starts
- `SessionEnd` - When session ends

### Hook Exit Codes:
- `0` - Success, allow action to proceed
- `2` - Block action and show error message
- Other non-zero - Error occurred

## Troubleshooting

**Hook not running?**
- Check that the hook file is executable: `ls -l .claude/hooks/`
- Verify configuration in `.claude/settings.local.json`
- Check Claude Code logs for errors

**Permission errors?**
- Ensure the hook script has execute permissions: `chmod +x .claude/hooks/*.sh`

**Can't find logs?**
- Logs are created in `.claude/logs/` directory
- Check that `CLAUDE_PROJECT_DIR` environment variable is set correctly
- Try running the hook manually to test: `./.claude/hooks/post-tool-use.sh`
