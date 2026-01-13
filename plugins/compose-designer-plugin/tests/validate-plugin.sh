#!/bin/bash
# Plugin validation script for compose-designer
# Validates plugin structure, configuration, components, and utilities
#
# Usage:
#   ./tests/validate-plugin.sh
#
# Exit codes:
#   0 - All validations passed
#   1 - One or more validations failed

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
}

# Check if file exists and is readable
check_file() {
    local file="$1"
    local description="$2"

    if [ -f "$file" ]; then
        pass "$description exists: $file"
        return 0
    else
        fail "$description missing: $file"
        return 1
    fi
}

# Check if file is executable
check_executable() {
    local file="$1"
    local description="$2"

    if [ -x "$file" ]; then
        pass "$description is executable: $file"
        return 0
    else
        fail "$description not executable: $file"
        return 1
    fi
}

# Validate JSON syntax
validate_json() {
    local file="$1"
    local description="$2"

    if python3 -m json.tool "$file" > /dev/null 2>&1; then
        pass "$description has valid JSON syntax"
        return 0
    else
        fail "$description has invalid JSON syntax"
        return 1
    fi
}

# Extract and validate YAML frontmatter
validate_frontmatter() {
    local file="$1"
    local description="$2"
    shift 2
    local required_fields=("$@")

    # Check if file starts with ---
    if ! head -1 "$file" | grep -q "^---$"; then
        fail "$description missing YAML frontmatter"
        return 1
    fi

    # Extract frontmatter (between first two --- lines)
    local frontmatter=$(sed -n '/^---$/,/^---$/p' "$file" | sed '1d;$d')

    # Check required fields
    local all_present=true
    for field in "${required_fields[@]}"; do
        if echo "$frontmatter" | grep -q "^$field:"; then
            pass "$description has required field: $field"
        else
            fail "$description missing required field: $field"
            all_present=false
        fi
    done

    if [ "$all_present" = true ]; then
        return 0
    else
        return 1
    fi
}

# Main validation
main() {
    info "Starting compose-designer plugin validation..."
    info "Working directory: $(pwd)"

    # ═══════════════════════════════════════════════════
    section "1. Plugin Manifest Validation"
    # ═══════════════════════════════════════════════════

    if check_file ".claude-plugin/plugin.json" "Plugin manifest"; then
        validate_json ".claude-plugin/plugin.json" "Plugin manifest"

        # Check required fields
        if grep -q '"name"' .claude-plugin/plugin.json; then
            pass "Manifest has 'name' field"
        else
            fail "Manifest missing 'name' field"
        fi

        if grep -q '"version"' .claude-plugin/plugin.json; then
            pass "Manifest has 'version' field"
        else
            warn "Manifest missing 'version' field (recommended)"
        fi

        if grep -q '"description"' .claude-plugin/plugin.json; then
            pass "Manifest has 'description' field"
        else
            warn "Manifest missing 'description' field (recommended)"
        fi
    fi

    # ═══════════════════════════════════════════════════
    section "2. Command Files Validation"
    # ═══════════════════════════════════════════════════

    if check_file "commands/config.md" "Config command"; then
        validate_frontmatter "commands/config.md" "Config command" "name" "description"
    fi

    if check_file "commands/create.md" "Create command"; then
        validate_frontmatter "commands/create.md" "Create command" "name" "description" "argument-hint"
    fi

    # ═══════════════════════════════════════════════════
    section "3. Agent Files Validation"
    # ═══════════════════════════════════════════════════

    if check_file "agents/design-generator.md" "Design generator agent"; then
        validate_frontmatter "agents/design-generator.md" "Design generator agent" \
            "description" "capabilities" "model" "color" "tools"
    fi

    if check_file "agents/visual-validator.md" "Visual validator agent"; then
        validate_frontmatter "agents/visual-validator.md" "Visual validator agent" \
            "description" "capabilities" "model" "color" "tools"
    fi

    if check_file "agents/device-tester.md" "Device tester agent"; then
        validate_frontmatter "agents/device-tester.md" "Device tester agent" \
            "description" "capabilities" "model" "color" "tools"
    fi

    # ═══════════════════════════════════════════════════
    section "4. Utility Scripts Validation"
    # ═══════════════════════════════════════════════════

    if check_file "utils/image-similarity.py" "Image similarity utility"; then
        check_executable "utils/image-similarity.py" "Image similarity utility"

        # Test help output
        local help_output=$(./utils/image-similarity.py --help 2>&1)
        if echo "$help_output" | grep -q "usage:"; then
            pass "Image similarity utility responds to --help"
        elif echo "$help_output" | grep -q "Required package not installed"; then
            warn "Image similarity utility missing Python dependencies (expected for validation)"
        else
            fail "Image similarity utility --help failed unexpectedly"
        fi
    fi

    if check_file "utils/figma-client.sh" "Figma client utility"; then
        check_executable "utils/figma-client.sh" "Figma client utility"

        # Test help output
        local figma_output=$(./utils/figma-client.sh 2>&1)
        if echo "$figma_output" | grep -q "Figma API client"; then
            pass "Figma client utility shows help text"
        else
            fail "Figma client utility help text not found"
        fi
    fi

    # ═══════════════════════════════════════════════════
    section "5. Example Files Validation"
    # ═══════════════════════════════════════════════════

    check_file "examples/README.md" "Examples README"
    check_file "examples/button-example.png.txt" "Button example placeholder"
    check_file "examples/card-example.png.txt" "Card example placeholder"

    # ═══════════════════════════════════════════════════
    section "6. Directory Structure Validation"
    # ═══════════════════════════════════════════════════

    # Check required directories
    for dir in ".claude-plugin" "commands" "agents" "utils" "examples" "tests" "docs"; do
        if [ -d "$dir" ]; then
            pass "Directory exists: $dir"
        else
            if [ "$dir" = "docs" ]; then
                warn "Optional directory missing: $dir"
            else
                fail "Required directory missing: $dir"
            fi
        fi
    done

    # ═══════════════════════════════════════════════════
    section "7. Documentation Validation"
    # ═══════════════════════════════════════════════════

    check_file "README.md" "Plugin README"
    check_file "docs/plans/2026-01-13-compose-designer-implementation.md" "Implementation plan"

    # ═══════════════════════════════════════════════════
    section "8. Security Checks"
    # ═══════════════════════════════════════════════════

    # Check for hardcoded secrets
    info "Checking for hardcoded secrets..."
    if grep -r "FIGMA_TOKEN.*=" --include="*.sh" --include="*.md" . 2>/dev/null | grep -v "FIGMA_TOKEN=\"\${FIGMA_TOKEN" | grep -v "export FIGMA_TOKEN" | grep -v "Get your personal access token" > /dev/null; then
        fail "Found potential hardcoded FIGMA_TOKEN"
    else
        pass "No hardcoded secrets found"
    fi

    # Check for proper quoting in bash scripts
    info "Checking bash script safety..."
    local unquoted_vars=0
    for script in utils/*.sh; do
        if [ -f "$script" ]; then
            # Look for common unquoted variable patterns (simplified check)
            if grep -E '\$[A-Z_]+[^"]' "$script" | grep -v "#" | grep -v "echo" > /dev/null 2>&1; then
                warn "Potential unquoted variables in $script (manual review recommended)"
                unquoted_vars=$((unquoted_vars + 1))
            fi
        fi
    done

    if [ $unquoted_vars -eq 0 ]; then
        pass "No obvious unquoted variable issues in bash scripts"
    fi

    # ═══════════════════════════════════════════════════
    section "9. Cross-Platform Compatibility"
    # ═══════════════════════════════════════════════════

    # Check for non-portable grep patterns
    info "Checking for non-portable grep patterns..."
    if grep -r "grep -P" --include="*.sh" --include="*.md" --exclude="validate-plugin.sh" . 2>/dev/null | grep -v "# BEFORE:" > /dev/null; then
        fail "Found non-portable grep -P usage (not available on macOS)"
    else
        pass "No non-portable grep -P patterns found"
    fi

    # Check for CLAUDE_PLUGIN_ROOT usage
    info "Checking for CLAUDE_PLUGIN_ROOT usage..."
    local plugin_root_count=$(grep -r "CLAUDE_PLUGIN_ROOT" --include="*.sh" --include="*.md" . 2>/dev/null | wc -l)
    if [ "$plugin_root_count" -gt 0 ]; then
        pass "Found $plugin_root_count references to CLAUDE_PLUGIN_ROOT (portability)"
    else
        warn "No CLAUDE_PLUGIN_ROOT references found (may affect portability)"
    fi

    # ═══════════════════════════════════════════════════
    section "Validation Summary"
    # ═══════════════════════════════════════════════════

    echo ""
    echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
    echo -e "${YELLOW}Warnings: $WARN_COUNT${NC}"
    echo -e "${RED}Failed: $FAIL_COUNT${NC}"
    echo ""

    if [ $FAIL_COUNT -eq 0 ]; then
        echo -e "${GREEN}✓ All critical validations passed!${NC}"
        if [ $WARN_COUNT -gt 0 ]; then
            echo -e "${YELLOW}⚠ Review $WARN_COUNT warning(s) above${NC}"
        fi
        exit 0
    else
        echo -e "${RED}✗ $FAIL_COUNT validation(s) failed${NC}"
        echo -e "${RED}Fix the issues above and re-run validation${NC}"
        exit 1
    fi
}

# Run main
main
