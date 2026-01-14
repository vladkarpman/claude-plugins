# Remove scrcpy_helper and Use device-manager-mcp

**Date:** 2026-01-14
**Status:** Approved

## Overview

Remove the legacy `scrcpy_helper/` directory from the plugin and use `device-manager-mcp` as a standalone MCP server via `uvx`.

## Motivation

- `device-manager-mcp` is now a standalone PyPI package
- The `scrcpy_helper/` directory with its `.venv/` is redundant
- Using `uvx` follows the same pattern as `npx` for mobile-mcp

## Changes

### 1. Delete scrcpy_helper

Remove entire `scripts/scrcpy_helper/` directory:
- `__init__.py`
- `client.py`
- `commands.py`
- `frame_buffer.py`
- `server.py`
- `video.py`
- `.venv/` (Python 3.12 virtual environment)

### 2. Update .mcp.json

```json
{
  "mobile-mcp": {
    "command": "npx",
    "args": ["-y", "@mobilenext/mobile-mcp@latest"]
  },
  "device-manager": {
    "command": "uvx",
    "args": ["device-manager-mcp"]
  }
}
```

### 3. Update session-start.sh

Add uv availability check:
```bash
if ! command -v uvx &> /dev/null; then
    echo "⚠️  device-manager-mcp requires 'uv' for fast screenshots."
    echo "   Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   Then restart Claude Code."
fi
```

### 4. Update run-test.md

Use device-manager tools for speed-critical operations:

| Operation | Tool |
|-----------|------|
| Screenshot | `mcp__device-manager__device_screenshot` |
| Tap | `mcp__device-manager__device_tap` |
| Swipe | `mcp__device-manager__device_swipe` |
| Type | `mcp__device-manager__device_type` |
| Screen size | `mcp__device-manager__device_screen_size` |
| Launch app | `mcp__mobile-mcp__mobile_launch_app` |
| Terminate app | `mcp__mobile-mcp__mobile_terminate_app` |
| List elements | `mcp__mobile-mcp__mobile_list_elements_on_screen` |
| Press button | `mcp__mobile-mcp__mobile_press_button` |

### 5. Coordinate Conversion

YAML tests support percentage coordinates (`["50%", "80%"]`). Conversion flow:
1. Get screen size via `device_screen_size`
2. Calculate pixels: `x = width * 0.50`, `y = height * 0.80`
3. Pass to `device_tap`

## User Requirements

Install `uv` once:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Benefits

- **Cleaner plugin** - No bundled venv or Python code for scrcpy
- **Portable** - `uvx` handles Python version and dependencies
- **Consistent pattern** - Same as `npx` for Node packages
- **Always latest** - `uvx` fetches current device-manager-mcp version
