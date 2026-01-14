#!/bin/bash
# Figma API client for compose-designer plugin
# Handles Figma URL parsing, node data fetching, and image export
#
# Usage:
#   ./figma-client.sh parse <figma-url>
#   ./figma-client.sh fetch-node <figma-url>
#   ./figma-client.sh export <figma-url> <output.png> [format] [scale]
#
# Environment:
#   FIGMA_TOKEN - Figma API personal access token (required)

set -euo pipefail

# Token from environment
FIGMA_TOKEN="${FIGMA_TOKEN:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${GREEN}$1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}$1${NC}" >&2
}

# Check if token is set
check_token() {
    if [ -z "$FIGMA_TOKEN" ]; then
        error "FIGMA_TOKEN environment variable not set

Get your personal access token:
1. Go to https://www.figma.com/settings
2. Navigate to 'Account' tab
3. Scroll to 'Personal Access Tokens'
4. Create new token with 'Read-only' scope
5. Export: export FIGMA_TOKEN=\"your-token-here\"
"
    fi
}

# Parse Figma URL to extract file ID and node ID
# Supports:
#   - https://www.figma.com/file/{file_id}/{name}?node-id={node_id}
#   - https://www.figma.com/design/{file_id}/{name}?node-id={node_id}
#   - figma://file/{file_id}?node-id={node_id}
parse_url() {
    local url="$1"

    # Extract file ID (portable: works on macOS and Linux)
    file_id=$(echo "$url" | grep -oE '(file|design)/[^/]+' | head -1 | cut -d'/' -f2)

    # Extract node ID (may have format like "123:456" or "123-456") (portable sed alternative)
    node_id=$(echo "$url" | sed -n 's/.*node-id=\([^&]*\).*/\1/p')

    # Normalize node ID: convert dash to colon (Figma API requires colon format)
    node_id=$(echo "$node_id" | sed 's/-/:/g')

    # Validate
    if [ -z "$file_id" ]; then
        error "Could not extract file ID from URL: $url

Supported formats:
  • https://www.figma.com/file/{file_id}/{name}?node-id={node_id}
  • https://www.figma.com/design/{file_id}/{name}?node-id={node_id}
  • figma://file/{file_id}?node-id={node_id}
"
    fi

    if [ -z "$node_id" ]; then
        warn "No node ID found in URL. Using root document."
        node_id="0:0"
    fi

    # Output in parseable format
    echo "${file_id}|${node_id}"
}

# Fetch node data from Figma API (colors, typography, layout)
fetch_node_data() {
    check_token

    local file_id="$1"
    local node_id="$2"

    info "Fetching node data from Figma API..."

    # URL-encode node ID (replace : with %3A)
    encoded_node_id=$(echo "$node_id" | sed 's/:/%3A/g')

    # Make API request
    response=$(curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
        "https://api.figma.com/v1/files/$file_id/nodes?ids=$encoded_node_id")

    # Check for errors
    if echo "$response" | grep -q '"err"'; then
        # Extract error message (portable sed alternative)
        err_msg=$(echo "$response" | sed -n 's/.*"err":"\([^"]*\)".*/\1/p')
        [ -z "$err_msg" ] && err_msg="Unknown error"
        error "Figma API error: $err_msg

Possible causes:
  • Invalid file ID or node ID
  • Token doesn't have access to this file
  • Token expired or invalid
"
    fi

    # Output JSON response
    echo "$response"
}

# Export node as image (PNG, JPG, SVG, PDF)
export_image() {
    check_token

    local file_id="$1"
    local node_id="$2"
    local output_path="$3"
    local format="${4:-png}"
    local scale="${5:-2}"

    info "Exporting Figma node as $format (${scale}x scale)..."

    # URL-encode node ID
    encoded_node_id=$(echo "$node_id" | sed 's/:/%3A/g')

    # Request image export
    response=$(curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
        "https://api.figma.com/v1/images/$file_id?ids=$encoded_node_id&format=$format&scale=$scale")

    # Check for errors (err:null means success, err:"message" means failure)
    if echo "$response" | grep -q '"err":"'; then
        # Extract error message (portable sed alternative)
        err_msg=$(echo "$response" | sed -n 's/.*"err":"\([^"]*\)".*/\1/p')
        [ -z "$err_msg" ] && err_msg="Unknown error"
        error "Figma API error: $err_msg"
    fi

    # Extract image URL from JSON response (portable sed alternative)
    # Format: {"images":{"123:456":"https://..."}}
    image_url=$(echo "$response" | sed -n "s/.*\"$node_id\":\"\\(https:\/\/[^\"]*\\)\".*/\\1/p")

    if [ -z "$image_url" ]; then
        error "Failed to get image URL from Figma API

Response: $response

Possible causes:
  • Node doesn't exist
  • Node is not exportable
  • API rate limit reached
"
    fi

    info "Downloading image from Figma CDN..."

    # Download image
    http_code=$(curl -s -w "%{http_code}" -o "$output_path" "$image_url")

    if [ "$http_code" != "200" ]; then
        error "Failed to download image (HTTP $http_code)"
    fi

    # Verify file was created and has content
    if [ ! -s "$output_path" ]; then
        error "Downloaded file is empty or missing: $output_path"
    fi

    local file_size=$(du -h "$output_path" | cut -f1)
    info "✓ Image exported: $output_path ($file_size)"
}

# Main command router
case "${1:-}" in
    parse)
        if [ -z "${2:-}" ]; then
            error "Usage: $0 parse <figma-url>"
        fi
        parse_url "$2"
        ;;

    fetch-node)
        if [ -z "${2:-}" ]; then
            error "Usage: $0 fetch-node <figma-url>"
        fi
        IFS='|' read -r file_id node_id <<< "$(parse_url "$2")"
        fetch_node_data "$file_id" "$node_id"
        ;;

    export)
        if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
            error "Usage: $0 export <figma-url> <output-path> [format] [scale]

Arguments:
  figma-url    Figma file URL with node-id parameter
  output-path  Where to save the exported image
  format       png|jpg|svg|pdf (default: png)
  scale        1|2|3|4 (default: 2 for 2x resolution)

Example:
  $0 export 'https://figma.com/file/ABC?node-id=1:234' output.png png 2
"
        fi
        IFS='|' read -r file_id node_id <<< "$(parse_url "$2")"
        export_image "$file_id" "$node_id" "$3" "${4:-png}" "${5:-2}"
        ;;

    *)
        cat <<EOF
Figma API client for compose-designer plugin

Usage:
  $0 <command> [arguments]

Commands:
  parse <figma-url>
      Parse Figma URL and extract file ID and node ID
      Output format: file_id|node_id

  fetch-node <figma-url>
      Fetch node data (colors, typography, layout) as JSON
      Requires: FIGMA_TOKEN environment variable

  export <figma-url> <output-path> [format] [scale]
      Export node as image file
      Formats: png, jpg, svg, pdf (default: png)
      Scale: 1-4 (default: 2 for retina)
      Requires: FIGMA_TOKEN environment variable

Environment:
  FIGMA_TOKEN    Figma personal access token (required for fetch/export)
                 Get token: https://www.figma.com/settings

Examples:
  # Parse URL
  $0 parse 'https://www.figma.com/file/ABC123?node-id=1:234'

  # Export as PNG
  export FIGMA_TOKEN="your-token"
  $0 export 'https://www.figma.com/file/ABC123?node-id=1:234' output.png

  # Export as high-res JPG
  $0 export 'https://www.figma.com/file/ABC123?node-id=1:234' output.jpg jpg 4

Exit codes:
  0    Success
  1    Error (check stderr for details)

EOF
        exit 1
        ;;
esac
