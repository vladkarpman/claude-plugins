# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code plugin marketplace containing two plugins:
- **mobile-ui-testing**: YAML-based mobile UI testing framework using mobile-mcp
- **compose-designer**: Design-to-Compose code generator with visual validation

This is a marketplace repository with automated version syncing and release workflows.

## Common Commands

### Version Management
```bash
# Sync plugin versions to marketplace.json
./scripts/sync-versions.sh

# Check marketplace consistency
git diff .claude-plugin/marketplace.json
```

### Plugin Development
```bash
# Load plugin locally for testing
claude --plugin-dir ./plugins/mobile-ui-testing
claude --plugin-dir ./plugins/compose-designer-plugin

# Install from local marketplace (alternative method)
claude plugin marketplace add file://$(pwd)
claude plugin install mobile-ui-testing@vladkarpman-plugins
```

### Plugin Validation
```bash
# Validate mobile-ui-testing structure
cd plugins/mobile-ui-testing && ./tests/integration/run-integration-tests.sh

# Validate compose-designer structure
cd plugins/compose-designer-plugin && ./tests/validate-plugin.sh
```

## Architecture

### Marketplace Structure

```
.claude-plugin/marketplace.json    # Marketplace catalog (auto-synced)
plugins/
├── mobile-ui-testing/
│   └── .claude-plugin/plugin.json # Source of truth for version
└── compose-designer-plugin/
    └── .claude-plugin/plugin.json # Source of truth for version
```

**Version sync flow:**
1. Update `plugins/{name}/.claude-plugin/plugin.json` version
2. Push to main branch
3. GitHub Actions automatically:
   - Syncs marketplace.json
   - Handles version conflicts
   - Creates git tag
   - Generates changelog
   - Publishes GitHub release

### Release Workflow (Automated)

Triggered by changes to `plugins/*/.claude-plugin/plugin.json`:

1. **Sync**: `./scripts/sync-versions.sh` updates marketplace.json
2. **Version conflict**: Auto-bumps marketplace patch version if tag exists
3. **Commit**: Commits marketplace.json changes
4. **Tag**: Creates git tag (format: v{marketplace.version})
5. **Release**: Generates changelog and creates GitHub release

Manual trigger: `gh workflow run auto-release.yml -f force=true`

### Plugin Structure

Both plugins follow standard Claude Code plugin conventions:
- **Commands** (`commands/`): Slash commands with YAML frontmatter
- **Agents** (`agents/`): Specialized subagents (compose-designer only)
- **Skills** (`skills/`): Reusable teaching content (mobile-ui-testing only)
- **Hooks** (`hooks/`): Event-driven automation
- **Scripts** (`scripts/`): Utilities (Python/Bash)

Each plugin has its own `CLAUDE.md` - refer to those for plugin-specific guidance.

## Release Process

### Quick Release (Recommended)

```bash
# 1. Update plugin version
vim plugins/mobile-ui-testing/.claude-plugin/plugin.json
# Change: "version": "3.3.3" → "3.3.4"

# 2. Commit and push (marketplace sync is automatic)
git add plugins/mobile-ui-testing/.claude-plugin/plugin.json
git commit -m "feat(mobile-ui-testing): add new feature"
git push origin main

# GitHub Actions handles the rest automatically
```

### Manual Sync (Optional)

```bash
# Preview changes locally before pushing
./scripts/sync-versions.sh
git diff .claude-plugin/marketplace.json

# Commit both files together
git add plugins/mobile-ui-testing/.claude-plugin/plugin.json
git add .claude-plugin/marketplace.json
git commit -m "feat(mobile-ui-testing): add new feature"
git push origin main
```

## Version Management Rules

**Plugin versions** (`plugins/{name}/.claude-plugin/plugin.json`):
- Source of truth for individual plugin versions
- Follow semantic versioning
- Trigger automated releases when changed

**Marketplace version** (`.claude-plugin/marketplace.json` → `metadata.version`):
- Auto-synced by workflow
- Auto-bumped if release tag collision occurs
- Manual bump only needed for marketplace metadata changes

**Semantic versioning:**
- Patch (1.0.0 → 1.0.1): Bug fixes
- Minor (1.0.0 → 1.1.0): New features, backward compatible
- Major (1.0.0 → 2.0.0): Breaking changes

## Key Conventions

### Script Portability
- Use `#!/usr/bin/env python3` or `#!/bin/bash` shebangs
- Avoid GNU-specific flags (e.g., `grep -P` not available on macOS)
- Quote all bash variables: `"$variable"`
- Test scripts on both macOS and Linux

### Plugin References
Always use `$CLAUDE_PLUGIN_ROOT` in scripts to reference plugin files:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tool.py"
```

### Commit Messages
Follow conventional commits format for changelog generation:
- `feat(plugin-name): description` - New features
- `fix(plugin-name): description` - Bug fixes
- `chore(plugin-name): description` - Maintenance (excluded from changelog)

## Troubleshooting

### Version Mismatch
If marketplace.json is out of sync:
```bash
./scripts/sync-versions.sh
git add .claude-plugin/marketplace.json
git commit --amend --no-edit
git push --force-with-lease
```

### Release Tag Already Exists
Workflow automatically handles this by bumping marketplace patch version. No manual intervention needed.

To force a specific version:
```bash
# Delete tag
git tag -d v1.2.0
git push origin :refs/tags/v1.2.0

# Update marketplace version manually
vim .claude-plugin/marketplace.json
git commit -am "chore: bump marketplace version"
git push
```

## Dependencies

**Repository-level:**
- `jq` (for version syncing script)
- Git (for version control)

**Plugin-specific:**
- See individual plugin CLAUDE.md files for their dependencies

## Documentation

- `README.md` - User-facing marketplace overview
- `RELEASING.md` - Detailed release process documentation
- `plugins/mobile-ui-testing/CLAUDE.md` - Mobile testing plugin guidance
- `plugins/compose-designer-plugin/CLAUDE.md` - Compose designer plugin guidance
