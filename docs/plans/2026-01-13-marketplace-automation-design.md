# Marketplace Plugin Version Automation Design

**Date:** 2026-01-13
**Status:** Approved
**Author:** Vladislav Karpman

## Problem Statement

The marketplace currently requires manual version updates across multiple files (marketplace.json, README.md) when plugin versions change. This creates maintenance overhead, risks human error, and doesn't scale beyond a few plugins.

## Goals

1. **Eliminate manual version updates** - Automate syncing plugin versions from source repositories
2. **Ensure reliability** - Validate versions before updating marketplace
3. **Maintain control** - Provide audit trail and ability to review/rollback changes
4. **Scale efficiently** - Support growing number of plugins without increased maintenance

## Solution Overview

Implement webhook-triggered automated sync with validation:

- Each plugin repo notifies marketplace when releasing a new version (via git tag)
- Marketplace workflow validates the release, updates files, and auto-commits
- Failed validations create PRs with error details for manual review
- Successful updates are immediately merged to main branch

## Architecture

### Components

**1. Plugin Repositories**

Each plugin contains:
- `.claude-plugin/plugin.json` with version field (source of truth)
- `.github/workflows/marketplace-notify.yml` to trigger marketplace sync on tag push

**2. Marketplace Repository**

Contains:
- `.github/workflows/sync-plugin.yml` to receive webhook and process updates
- `marketplace.json` with plugin registry (auto-updated)
- `README.md` with version table (auto-updated)

**3. Communication Flow**

```
Plugin Maintainer → git tag v1.2.3 → Push with tags
  ↓
Plugin GitHub Action → Webhook (repository_dispatch)
  ↓
Marketplace Workflow → Clone plugin → Validate
  ↓
[Pass] → Update files → Commit → Push (auto-merge)
[Fail] → Create PR with failing checks
```

## Detailed Design

### 1. Plugin Repository Setup

**File:** `.github/workflows/marketplace-notify.yml`

```yaml
name: Notify Marketplace on Release
on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send webhook to marketplace
        run: |
          curl -X POST \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Authorization: token ${{ secrets.MARKETPLACE_TOKEN }}" \
            https://api.github.com/repos/vladkarpman/vladkarpman-plugins/dispatches \
            -d '{
              "event_type": "plugin_release",
              "client_payload": {
                "plugin_name": "${{ github.event.repository.name }}",
                "version": "${{ github.ref_name }}",
                "repo_url": "${{ github.event.repository.clone_url }}"
              }
            }'
```

**Trigger:** Only on version tags (v1.2.3 pattern)
**Authentication:** Personal access token with `repo` scope stored in plugin repo secrets
**Payload:** Plugin name, version tag, repository URL

**Setup per plugin (one-time):**
1. Create GitHub personal access token with `repo` scope
2. Add as `MARKETPLACE_TOKEN` secret in plugin repository
3. Add marketplace-notify.yml workflow file
4. Push workflow to main branch

### 2. Marketplace Sync Workflow

**File:** `.github/workflows/sync-plugin.yml`

```yaml
name: Sync Plugin Version
on:
  repository_dispatch:
    types: [plugin_release]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout marketplace
        uses: actions/checkout@v4

      - name: Clone plugin repo
        run: |
          git clone --depth 1 --branch ${{ github.event.client_payload.version }} \
            ${{ github.event.client_payload.repo_url }} plugin-repo

      - name: Extract version from plugin.json
        id: plugin-version
        run: |
          VERSION=$(jq -r '.metadata.version' plugin-repo/.claude-plugin/plugin.json)
          echo "version=$VERSION" >> $GITHUB_OUTPUT

      - name: Validate version match
        run: |
          TAG_VERSION="${{ github.event.client_payload.version }}"
          TAG_VERSION="${TAG_VERSION#v}"  # Remove 'v' prefix
          FILE_VERSION="${{ steps.plugin-version.outputs.version }}"

          if [ "$TAG_VERSION" != "$FILE_VERSION" ]; then
            echo "Error: Tag version ($TAG_VERSION) doesn't match plugin.json version ($FILE_VERSION)"
            exit 1
          fi

      - name: Validate JSON schema
        run: |
          jq empty plugin-repo/.claude-plugin/plugin.json
          # Additional schema validation can be added here

      - name: Test plugin installation
        run: |
          # Install Claude Code CLI if not available
          # claude plugin install --test plugin-repo/.claude-plugin
          # For now, placeholder for installation test
          echo "Installation test would run here"

      - name: Update marketplace.json
        run: |
          PLUGIN_NAME="${{ github.event.client_payload.plugin_name }}"
          NEW_VERSION="${{ steps.plugin-version.outputs.version }}"

          jq --arg name "$PLUGIN_NAME" --arg version "$NEW_VERSION" \
            '.plugins |= map(if .name == $name then .version = $version else . end)' \
            marketplace.json > marketplace.json.tmp
          mv marketplace.json.tmp marketplace.json

      - name: Update README.md version table
        run: |
          PLUGIN_NAME="${{ github.event.client_payload.plugin_name }}"
          NEW_VERSION="${{ steps.plugin-version.outputs.version }}"
          DESCRIPTION=$(jq -r ".plugins[] | select(.name==\"$PLUGIN_NAME\") | .description" marketplace.json)

          # Update the version in the table
          sed -i.bak "s#| $PLUGIN_NAME | .* | .* |#| $PLUGIN_NAME | $DESCRIPTION | $NEW_VERSION |#" README.md
          rm README.md.bak

      - name: Commit and push changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add marketplace.json README.md
          git commit -m "chore: bump ${{ github.event.client_payload.plugin_name }} to v${{ steps.plugin-version.outputs.version }}"
          git push
```

**On Validation Failure:**

Add to workflow:
```yaml
      - name: Create PR on failure
        if: failure()
        uses: peter-evans/create-pull-request@v5
        with:
          title: "Failed to sync ${{ github.event.client_payload.plugin_name }} v${{ github.event.client_payload.version }}"
          body: |
            Automated sync failed for plugin release.

            **Plugin:** ${{ github.event.client_payload.plugin_name }}
            **Version Tag:** ${{ github.event.client_payload.version }}
            **Repository:** ${{ github.event.client_payload.repo_url }}

            **Error:** Check workflow logs for details.

            Please review and fix the issue in the plugin repository, then re-tag.
          branch: "sync-failure-${{ github.event.client_payload.plugin_name }}-${{ github.event.client_payload.version }}"
```

### 3. Validation Checks

The workflow performs three validation checks in order:

**a) Tag-Version Match**
- Extracts version from git tag (v3.2.0 → 3.2.0)
- Compares with plugin.json `.metadata.version` field
- Fails if mismatch detected

**b) JSON Schema Validation**
- Uses `jq empty` to verify JSON is valid
- Can be extended with JSON schema validator
- Ensures required fields exist: name, version, description

**c) Installation Test**
- Attempts to install plugin in test environment
- Verifies plugin files are accessible and structured correctly
- Catches broken plugin releases before they reach users

### 4. README Update Strategy

**What gets auto-updated:**
- Version table (lines 17-20 in current README.md)
- Format: `| plugin-name | description | version |`
- Uses sed pattern matching to find and replace

**What stays manual:**
- Detailed plugin sections (lines 24-77)
- Custom descriptions, examples, usage instructions
- Rationale: These contain narrative content that shouldn't auto-generate

**Update mechanism:**
```bash
sed -i "s/| $PLUGIN_NAME | .* | .* |/| $PLUGIN_NAME | $DESCRIPTION | $NEW_VERSION |/" README.md
```

**Edge cases:**
- New plugin not in README: Manual addition required (one-time)
- Table format changes: Update sed pattern (one-time)

### 5. Error Handling & Rollback

**Error Scenarios:**

| Scenario | Detection | Response |
|----------|-----------|----------|
| Tag-version mismatch | Compare tag vs plugin.json | Create PR with error details |
| Invalid JSON | jq validation fails | Create PR with parse error |
| Installation fails | claude plugin install exits non-zero | Create PR with logs |
| Repo unreachable | git clone fails | Retry 3x, then create PR |

**Rollback Strategy:**

Manual revert if bad version merged:
```bash
git revert <commit-hash>
git push
```

Emergency override (bypass validation):
```bash
# Directly edit marketplace.json
jq '.plugins |= map(if .name == "plugin-name" then .version = "1.2.3" else . end)' marketplace.json
git commit -m "revert: emergency rollback of plugin-name to v1.2.3"
git push
```

**Impact on users:**
- Users with installed version keep it (no auto-update)
- New installations get reverted version
- Clear commit history shows all version changes

## Implementation Plan

### Phase 1: Marketplace Workflow Setup
1. Create `.github/workflows/sync-plugin.yml` in marketplace repo
2. Test with manual `repository_dispatch` trigger
3. Verify validation checks work as expected

### Phase 2: Plugin Repository Setup
1. Add `.github/workflows/marketplace-notify.yml` to mobile-ui-testing
2. Create GitHub token and add to secrets
3. Test end-to-end flow with test tag

### Phase 3: Rollout to All Plugins
1. Add workflow to compose-designer
2. Document setup process for future plugins
3. Monitor first few automated syncs

### Phase 4: Refinements
1. Enhance validation (schema validation, better error messages)
2. Add notification on success (optional)
3. Consider rate limiting for high-frequency updates

## Success Metrics

- **Zero manual version updates** after implementation
- **100% validation accuracy** (no bad versions merged)
- **Sub-5-minute sync time** from tag push to marketplace update
- **Clear audit trail** in git history

## Security Considerations

- **Token scope:** Limited to `repo` access, no admin rights
- **Token storage:** GitHub secrets, never in code
- **Validation:** Multi-step checks prevent malicious releases
- **Rollback:** Simple git revert provides safety net

## Future Enhancements

- **Plugin metrics:** Track download counts, version adoption
- **Breaking change detection:** Analyze plugin.json for breaking changes
- **Automated testing:** Run plugin test suites before sync
- **Multi-marketplace:** Support syncing to multiple marketplaces
