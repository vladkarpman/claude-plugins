#!/bin/bash
# Figma Token Extraction Utility
#
# Parses a Figma URL and outputs JSON metadata for use with Figma MCP tools.
# This script does NOT extract actual tokens - it provides the file_id and node_id
# needed to call Figma MCP tools (get_design_context, get_variable_defs, get_screenshot).
#
# Usage: ./figma-tokens.sh <figma-url>
# Output: JSON with file_id, node_id, and list of MCP tools to call
#
# Example:
#   ./figma-tokens.sh "https://www.figma.com/design/ABC123/MyDesign?node-id=1-234"
#   # Returns: {"file_id": "ABC123", "node_id": "1:234", ...}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

error() { echo -e "${RED}Error: $1${NC}" >&2; exit 1; }
info() { echo -e "${GREEN}$1${NC}" >&2; }

# Parse Figma URL to extract node ID
parse_url() {
    local url="$1"
    # Reuse existing figma-client.sh parsing
    "${SCRIPT_DIR}/figma-client.sh" parse "$url"
}

# Main
if [ -z "${1:-}" ]; then
    error "Usage: $0 <figma-url>"
fi

FIGMA_URL="$1"

info "Extracting design tokens from Figma..."
info "Note: This script outputs token info. Use Figma MCP tools directly for full extraction."

# Parse URL
IFS='|' read -r file_id node_id <<< "$(parse_url "$FIGMA_URL")"

# Validate extracted values
if [ -z "$file_id" ]; then
    error "Could not extract file_id from URL: $FIGMA_URL"
fi
if [ -z "$node_id" ]; then
    error "Could not extract node_id from URL: $FIGMA_URL"
fi

echo "{"
echo "  \"file_id\": \"$file_id\","
echo "  \"node_id\": \"$node_id\","
echo "  \"extraction_method\": \"figma_mcp\","
echo "  \"tools_to_use\": ["
echo "    \"mcp__figma-desktop__get_design_context\","
echo "    \"mcp__figma-desktop__get_variable_defs\","
echo "    \"mcp__figma-desktop__get_screenshot\""
echo "  ]"
echo "}"
