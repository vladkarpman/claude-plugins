#!/usr/bin/env bash

# Mobile UI Testing Plugin - Session Start Hook
# - Auto-approves mobile-mcp and screen-buffer tools for seamless test execution
# - Checks for uv/uvx availability for screen-buffer-mcp

# Check if uvx is available
uv_status="not available"
if command -v uvx &> /dev/null; then
    uv_status="available (fast screenshots enabled)"
else
    echo "⚠️  screen-buffer-mcp requires 'uv' for fast screenshots." >&2
    echo "   Install: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    echo "   Then restart Claude Code." >&2
fi

cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Mobile UI Testing plugin is active.\n\n**Auto-approved tools:** All mobile-mcp and screen-buffer tools are pre-approved for this session. Tests will run without requiring manual approval for each action.\n\n**screen-buffer-mcp:** ${uv_status}\n\nAvailable commands:\n- \`/run-test <file>\` - Execute a YAML test file\n- \`/create-test <name>\` - Create a new test from template\n- \`/generate-test <description>\` - Generate test from natural language\n- \`/record-test <name>\` - Start recording user actions\n- \`/stop-recording\` - Stop recording and generate YAML\n\nFor help writing tests, just ask about YAML test syntax."
  }
}
EOF

exit 0
