#!/bin/bash
# Sync plugin versions from individual plugin.json files to marketplace.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MARKETPLACE_JSON="$ROOT_DIR/.claude-plugin/marketplace.json"
PLUGINS_DIR="$ROOT_DIR/plugins"

echo "🔄 Syncing plugin versions to marketplace.json..."
echo ""

# Read marketplace.json
MARKETPLACE_CONTENT=$(cat "$MARKETPLACE_JSON")

# Function to extract version from plugin.json
get_plugin_version() {
    local plugin_path="$1"
    local plugin_json="$plugin_path/.claude-plugin/plugin.json"

    if [ ! -f "$plugin_json" ]; then
        echo "ERROR: Plugin manifest not found: $plugin_json" >&2
        return 1
    fi

    # Extract version using jq if available, otherwise use grep/sed
    if command -v jq &> /dev/null; then
        jq -r '.version' "$plugin_json"
    else
        grep '"version"' "$plugin_json" | head -1 | sed 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/'
    fi
}

# Update marketplace.json versions
TEMP_FILE=$(mktemp)
cp "$MARKETPLACE_JSON" "$TEMP_FILE"

UPDATED=false

# Process each plugin entry in marketplace.json
if command -v jq &> /dev/null; then
    # Use jq for reliable JSON manipulation
    PLUGIN_COUNT=$(jq '.plugins | length' "$MARKETPLACE_JSON")

    for i in $(seq 0 $((PLUGIN_COUNT - 1))); do
        PLUGIN_NAME=$(jq -r ".plugins[$i].name" "$MARKETPLACE_JSON")
        PLUGIN_SOURCE=$(jq -r ".plugins[$i].source" "$MARKETPLACE_JSON")

        # Only process local plugins (relative paths)
        if [[ "$PLUGIN_SOURCE" == ./* ]]; then
            PLUGIN_PATH="$ROOT_DIR/$PLUGIN_SOURCE"

            if [ -d "$PLUGIN_PATH" ]; then
                ACTUAL_VERSION=$(get_plugin_version "$PLUGIN_PATH")
                MARKETPLACE_VERSION=$(jq -r ".plugins[$i].version" "$MARKETPLACE_JSON")

                if [ "$ACTUAL_VERSION" != "$MARKETPLACE_VERSION" ]; then
                    echo "📦 $PLUGIN_NAME: $MARKETPLACE_VERSION → $ACTUAL_VERSION"
                    jq ".plugins[$i].version = \"$ACTUAL_VERSION\"" "$TEMP_FILE" > "$TEMP_FILE.new"
                    mv "$TEMP_FILE.new" "$TEMP_FILE"
                    UPDATED=true
                else
                    echo "✅ $PLUGIN_NAME: $ACTUAL_VERSION (already in sync)"
                fi
            else
                echo "⚠️  $PLUGIN_NAME: Plugin directory not found at $PLUGIN_PATH"
            fi
        else
            echo "⏭️  $PLUGIN_NAME: External plugin, skipping"
        fi
    done

    if [ "$UPDATED" = true ]; then
        mv "$TEMP_FILE" "$MARKETPLACE_JSON"
        echo ""
        echo "✅ Marketplace versions updated!"
    else
        rm "$TEMP_FILE"
        echo ""
        echo "✅ All versions already in sync!"
    fi
else
    echo "⚠️  jq not found. Install with: brew install jq"
    echo "Manual sync required."
    rm "$TEMP_FILE"
    exit 1
fi
