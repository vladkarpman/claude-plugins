# Release Workflow

This document describes how to release new versions of plugins in the marketplace.

## Overview

The marketplace uses automated version syncing and release creation through GitHub Actions. The workflow ensures that:

1. Plugin versions in `plugin.json` are the source of truth
2. Marketplace catalog (`marketplace.json`) stays in sync automatically
3. Releases are created with proper changelogs

## Releasing a Plugin Update

### 1. Update Plugin Version

Edit the plugin's `plugin.json` file:

```bash
# Example: Update mobile-ui-testing
vim plugins/mobile-ui-testing/.claude-plugin/plugin.json
```

Change the version field following [semantic versioning](https://semver.org/):
- **Patch** (1.0.0 → 1.0.1): Bug fixes, no breaking changes
- **Minor** (1.0.0 → 1.1.0): New features, backward compatible
- **Major** (1.0.0 → 2.0.0): Breaking changes

### 2. Sync Marketplace Version

Run the sync script locally:

```bash
./scripts/sync-versions.sh
```

This updates `.claude-plugin/marketplace.json` to match plugin versions.

### 3. Commit Changes

```bash
git add plugins/*//.claude-plugin/plugin.json
git add .claude-plugin/marketplace.json
git commit -m "chore: bump mobile-ui-testing to v3.3.2"
git push origin main
```

### 4. Automated Release

The GitHub Action will automatically:
- ✅ Verify versions are in sync
- ✅ Create a git tag (e.g., `v1.2.0`)
- ✅ Generate release notes with changelog
- ✅ Publish GitHub release

## Marketplace Version Updates

The marketplace version in `.claude-plugin/marketplace.json` (`metadata.version`) should be bumped when:
- Adding new plugins
- Removing plugins
- Changing marketplace metadata

Individual plugin version changes don't require marketplace version bumps.

## Manual Release Creation

To create a release manually:

```bash
# Via GitHub UI: Actions → Create Release → Run workflow

# Or via gh CLI:
gh workflow run release.yml -f version=v1.2.0
```

## Version Sync Automation

### On Push to Main
When you push plugin version changes, the `sync-marketplace.yml` workflow:
1. Detects plugin.json changes
2. Runs sync script
3. Auto-commits updated marketplace.json (if needed)

### On Pull Requests
When a PR includes plugin version changes:
1. Workflow validates versions are in sync
2. Fails PR if marketplace.json is out of sync
3. Comments with instructions to sync locally

## Local Development

### Pre-commit Hook (Optional)

To automatically sync versions before each commit:

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
./scripts/sync-versions.sh
git add .claude-plugin/marketplace.json
EOF

chmod +x .git/hooks/pre-commit
```

### Testing Plugin Changes

```bash
# Load plugin locally for testing
claude --plugin-dir ./plugins/mobile-ui-testing

# Or install from local marketplace
claude plugin marketplace add file://$(pwd)
claude plugin install mobile-ui-testing@vladkarpman-plugins
```

## Users Getting Updates

### Automatic Updates

Users can update all marketplace plugins:

```bash
# Update marketplace catalogs
claude plugin marketplace update

# Update all installed plugins
claude plugin update
```

### Version Pinning

Users can pin specific versions:

```bash
# Install specific version
claude plugin install mobile-ui-testing@3.3.1

# Update to latest
claude plugin install mobile-ui-testing@latest
```

## Troubleshooting

### Version Mismatch Detected

If GitHub Actions reports version mismatch:

```bash
./scripts/sync-versions.sh
git add .claude-plugin/marketplace.json
git commit --amend --no-edit
git push --force-with-lease
```

### Release Tag Already Exists

If you need to recreate a release:

```bash
# Delete local and remote tag
git tag -d v1.2.0
git push origin :refs/tags/v1.2.0

# Update marketplace version
vim .claude-plugin/marketplace.json
git commit -am "chore: bump marketplace version"
git push

# Workflow will create new release
```

## Best Practices

1. **Always test locally** before pushing version bumps
2. **Write meaningful commit messages** - they appear in changelog
3. **Update plugin README** when releasing major changes
4. **Coordinate breaking changes** - communicate with users first
5. **Use semantic versioning** - helps users understand impact

## Example Release Flow

```bash
# 1. Make changes to plugin
vim plugins/mobile-ui-testing/commands/run-test.md

# 2. Update plugin version
vim plugins/mobile-ui-testing/.claude-plugin/plugin.json
# Change: "version": "3.3.2" → "3.3.3"

# 3. Sync and commit
./scripts/sync-versions.sh
git add -A
git commit -m "feat(mobile-ui-testing): add retry logic to run-test"
git push origin main

# 4. Wait for GitHub Actions to create release
# Done! Users can now update with: claude plugin update
```
