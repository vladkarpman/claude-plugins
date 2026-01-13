#!/usr/bin/env bash

# Mobile UI Testing Plugin - Session Start Hook
# Auto-approves mobile-mcp tools for seamless test execution

cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Mobile UI Testing plugin is active.\n\n**Auto-approved tools:** All mobile-mcp tools (tap, swipe, type, screenshot, etc.) are pre-approved for this session. Tests will run without requiring manual approval for each action.\n\nAvailable commands:\n- `/run-test <file>` - Execute a YAML test file\n- `/create-test <name>` - Create a new test from template\n- `/generate-test <description>` - Generate test from natural language\n- `/record-test <name>` - Start recording user actions\n- `/stop-recording` - Stop recording and generate YAML\n\nFor help writing tests, just ask about YAML test syntax."
  }
}
EOF

exit 0
