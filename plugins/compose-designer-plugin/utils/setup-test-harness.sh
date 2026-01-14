#!/bin/bash
# Test harness setup utility for compose-designer plugin
# Initializes the Paparazzi test harness on first run
#
# Usage:
#   ./setup-test-harness.sh [--force]
#
# Options:
#   --force    Force re-initialization even if already set up
#
# Exit codes:
#   0    Success (harness ready)
#   1    Error (check stderr for details)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
HARNESS_DIR="$PLUGIN_DIR/test-harness"

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

success() {
    echo -e "${GREEN}$1${NC}"
}

info() {
    echo -e "$1"
}

warn() {
    echo -e "${YELLOW}$1${NC}"
}

# Check if test harness directory exists
check_harness_exists() {
    if [ ! -d "$HARNESS_DIR" ]; then
        error "Test harness directory not found: $HARNESS_DIR

The test-harness directory should be part of the compose-designer plugin.
Please ensure the plugin is correctly installed."
    fi
}

# Check if Gradle wrapper is present and executable
check_gradle_wrapper() {
    local gradlew="$HARNESS_DIR/gradlew"

    if [ ! -f "$gradlew" ]; then
        error "Gradle wrapper not found: $gradlew

The test harness is missing the Gradle wrapper.
This file should be part of the plugin distribution."
    fi

    if [ ! -x "$gradlew" ]; then
        info "Making Gradle wrapper executable..."
        chmod +x "$gradlew"
    fi
}

# Check if Java/JDK is available
check_java() {
    if ! command -v java &> /dev/null; then
        error "Java not found in PATH

Paparazzi requires Java 17 or higher.
Install options:
  macOS:   brew install openjdk@17
  Linux:   apt install openjdk-17-jdk  (or equivalent)

After installing, ensure 'java' is in your PATH."
    fi

    # Check Java version (need 17+)
    java_version=$(java -version 2>&1 | head -1 | sed -n 's/.*version "\([0-9]*\).*/\1/p')

    if [ -n "$java_version" ] && [ "$java_version" -lt 17 ]; then
        warn "Java $java_version detected. Paparazzi works best with Java 17+."
    fi
}

# Check if harness is already initialized
is_initialized() {
    # Check for .gradle directory (created after first Gradle run)
    # and build directory (created after successful build)
    if [ -d "$HARNESS_DIR/.gradle" ] && [ -d "$HARNESS_DIR/build" ]; then
        return 0
    fi
    return 1
}

# Run Gradle build to initialize harness
initialize_harness() {
    info "Setting up Paparazzi test harness..."
    info "Downloading Gradle dependencies (this may take a minute)..."

    cd "$HARNESS_DIR"

    # Run build to download all dependencies and verify setup
    if ! ./gradlew build --quiet 2>&1; then
        error "Gradle build failed

Possible causes:
  - Network issues downloading dependencies
  - Missing Android SDK (set ANDROID_HOME or ANDROID_SDK_ROOT)
  - Incompatible Java version

Check the output above for specific error messages."
    fi

    success "Test harness initialized successfully"
}

# Verify Gradle can run basic tasks
verify_gradle() {
    cd "$HARNESS_DIR"

    if ! ./gradlew tasks --quiet &> /dev/null; then
        error "Gradle verification failed

The Gradle wrapper exists but cannot execute tasks.
Try running manually: cd $HARNESS_DIR && ./gradlew tasks"
    fi
}

# Main logic
main() {
    local force=false

    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --force)
                force=true
                shift
                ;;
            --help|-h)
                cat <<EOF
Test harness setup utility for compose-designer plugin

Usage: $0 [--force]

Options:
  --force    Force re-initialization even if already set up
  --help     Show this help message

This script ensures the Paparazzi test harness is ready for use.
It will:
  1. Verify the test-harness directory exists
  2. Check for Java/JDK availability
  3. Verify Gradle wrapper is executable
  4. Download dependencies and build on first run

Exit codes:
  0    Success (harness ready)
  1    Error (check stderr for details)

EOF
                exit 0
                ;;
            *)
                error "Unknown option: $1

Usage: $0 [--force]
Use --help for more information."
                ;;
        esac
    done

    # Check prerequisites
    check_harness_exists
    check_java
    check_gradle_wrapper

    # Check if already initialized
    if [ "$force" = false ] && is_initialized; then
        success "Test harness already initialized"
        exit 0
    fi

    if [ "$force" = true ]; then
        info "Force flag set, re-initializing..."
    fi

    # Initialize harness
    initialize_harness

    # Verify it works
    verify_gradle

    success "Test harness is ready"
}

main "$@"
