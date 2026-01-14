#!/bin/bash
# Extract design tokens from Figma via MCP
#
# Usage: ./figma-tokens.sh <figma-url>
# Output: JSON with extracted color, spacing, typography tokens

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
