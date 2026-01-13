# Marketplace Automation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement webhook-triggered automated plugin version syncing from plugin repos to marketplace with validation and auto-merge.

**Architecture:** Plugin repos trigger marketplace via repository_dispatch when git tags are pushed. Marketplace workflow validates version match, JSON schema, and installation, then auto-updates marketplace.json and README.md. Failures create PRs with error details.

**Tech Stack:** GitHub Actions, bash, jq, sed, git

---

## Task 1: Create Basic Marketplace Sync Workflow

**Files:**
- Create: `.github/workflows/sync-plugin.yml`

**Step 1: Create workflow file with basic structure**

Create `.github/workflows/sync-plugin.yml`:

```yaml
name: Sync Plugin Version

on:
  repository_dispatch:
    types: [plugin_release]
  workflow_dispatch:
    inputs:
      plugin_name:
        description: 'Plugin name'
        required: true
      version:
        description: 'Version tag (e.g., v3.2.0)'
        required: true
      repo_url:
        description: 'Plugin repository URL'
        required: true

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout marketplace
        uses: actions/checkout@v4

      - name: Log received payload
        run: |
          echo "Plugin: ${{ github.event.client_payload.plugin_name || github.event.inputs.plugin_name }}"
          echo "Version: ${{ github.event.client_payload.version || github.event.inputs.version }}"
          echo "Repo: ${{ github.event.client_payload.repo_url || github.event.inputs.repo_url }}"
```

**Step 2: Test workflow with manual trigger**

Run: Go to Actions tab → Sync Plugin Version → Run workflow
Inputs: plugin_name=mobile-ui-testing, version=v3.1.0, repo_url=https://github.com/vladkarpman/mobile-ui-testing.git
Expected: Workflow runs, logs show correct values

**Step 3: Commit**

```bash
git add .github/workflows/sync-plugin.yml
git commit -m "feat: add basic marketplace sync workflow

Add GitHub Actions workflow to receive plugin release webhooks.
Supports both repository_dispatch and manual workflow_dispatch for testing."
```

---

## Task 2: Add Plugin Cloning and Version Extraction

**Files:**
- Modify: `.github/workflows/sync-plugin.yml`

**Step 1: Add clone step**

Add after "Log received payload" step:

```yaml
      - name: Set workflow variables
        id: vars
        run: |
          PLUGIN_NAME="${{ github.event.client_payload.plugin_name || github.event.inputs.plugin_name }}"
          VERSION="${{ github.event.client_payload.version || github.event.inputs.version }}"
          REPO_URL="${{ github.event.client_payload.repo_url || github.event.inputs.repo_url }}"

          echo "plugin_name=$PLUGIN_NAME" >> $GITHUB_OUTPUT
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "repo_url=$REPO_URL" >> $GITHUB_OUTPUT

      - name: Clone plugin repo
        run: |
          git clone --depth 1 --branch ${{ steps.vars.outputs.version }} \
            ${{ steps.vars.outputs.repo_url }} plugin-repo

      - name: Extract version from plugin.json
        id: plugin-version
        run: |
          if [ ! -f plugin-repo/.claude-plugin/plugin.json ]; then
            echo "Error: plugin.json not found"
            exit 1
          fi

          VERSION=$(jq -r '.metadata.version' plugin-repo/.claude-plugin/plugin.json)

          if [ -z "$VERSION" ] || [ "$VERSION" = "null" ]; then
            echo "Error: version not found in plugin.json"
            exit 1
          fi

          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "Extracted version: $VERSION"
```

**Step 2: Test workflow with manual trigger**

Run: Actions → Sync Plugin Version → Run workflow with same inputs
Expected: Workflow clones repo, extracts version "3.1.0" from plugin.json

**Step 3: Commit**

```bash
git add .github/workflows/sync-plugin.yml
git commit -m "feat: add plugin cloning and version extraction

Clone plugin repo at tagged version and extract version from plugin.json.
Includes error handling for missing files and invalid JSON."
```

---

## Task 3: Add Version Validation

**Files:**
- Modify: `.github/workflows/sync-plugin.yml`

**Step 1: Add validation step**

Add after "Extract version from plugin.json" step:

```yaml
      - name: Validate version match
        run: |
          TAG_VERSION="${{ steps.vars.outputs.version }}"
          TAG_VERSION="${TAG_VERSION#v}"  # Remove 'v' prefix
          FILE_VERSION="${{ steps.plugin-version.outputs.version }}"

          echo "Tag version: $TAG_VERSION"
          echo "File version: $FILE_VERSION"

          if [ "$TAG_VERSION" != "$FILE_VERSION" ]; then
            echo "❌ Error: Version mismatch"
            echo "Git tag: v$TAG_VERSION"
            echo "plugin.json: $FILE_VERSION"
            echo ""
            echo "The version in .claude-plugin/plugin.json must match the git tag."
            echo "Please update plugin.json and create a new tag."
            exit 1
          fi

          echo "✅ Version validation passed"

      - name: Validate JSON schema
        run: |
          echo "Validating plugin.json structure..."

          # Check JSON is valid
          if ! jq empty plugin-repo/.claude-plugin/plugin.json 2>/dev/null; then
            echo "❌ Error: Invalid JSON in plugin.json"
            exit 1
          fi

          # Check required fields
          NAME=$(jq -r '.name' plugin-repo/.claude-plugin/plugin.json)
          VERSION=$(jq -r '.metadata.version' plugin-repo/.claude-plugin/plugin.json)
          DESC=$(jq -r '.metadata.description' plugin-repo/.claude-plugin/plugin.json)

          if [ -z "$NAME" ] || [ "$NAME" = "null" ]; then
            echo "❌ Error: Missing 'name' field in plugin.json"
            exit 1
          fi

          if [ -z "$VERSION" ] || [ "$VERSION" = "null" ]; then
            echo "❌ Error: Missing 'metadata.version' field in plugin.json"
            exit 1
          fi

          if [ -z "$DESC" ] || [ "$DESC" = "null" ]; then
            echo "❌ Error: Missing 'metadata.description' field in plugin.json"
            exit 1
          fi

          echo "✅ JSON schema validation passed"
```

**Step 2: Test validation with correct version**

Run: Actions → Sync Plugin Version → Run workflow with mobile-ui-testing v3.1.0
Expected: Both validation steps pass with ✅

**Step 3: Test validation with wrong version**

Run: Actions → Sync Plugin Version → Run workflow with version=v999.0.0
Expected: Workflow fails at "Validate version match" with clear error message

**Step 4: Commit**

```bash
git add .github/workflows/sync-plugin.yml
git commit -m "feat: add version and schema validation

Validate git tag matches plugin.json version.
Validate plugin.json has required fields: name, metadata.version, metadata.description.
Clear error messages for all validation failures."
```

---

## Task 4: Add Installation Test Placeholder

**Files:**
- Modify: `.github/workflows/sync-plugin.yml`

**Step 1: Add installation test step**

Add after "Validate JSON schema" step:

```yaml
      - name: Test plugin installation
        run: |
          echo "📦 Testing plugin installation..."
          echo ""
          echo "Note: Full installation test requires Claude Code CLI."
          echo "For now, we verify plugin structure exists."

          # Check plugin structure
          if [ ! -d "plugin-repo/.claude-plugin" ]; then
            echo "❌ Error: Missing .claude-plugin directory"
            exit 1
          fi

          if [ ! -f "plugin-repo/.claude-plugin/plugin.json" ]; then
            echo "❌ Error: Missing plugin.json"
            exit 1
          fi

          # List plugin contents for visibility
          echo ""
          echo "Plugin structure:"
          ls -la plugin-repo/.claude-plugin/

          echo ""
          echo "✅ Plugin structure validation passed"
          echo "TODO: Add full installation test when Claude Code CLI is available in CI"
```

**Step 2: Test with manual workflow**

Run: Actions → Sync Plugin Version → Run workflow
Expected: Installation test passes, shows plugin structure

**Step 3: Commit**

```bash
git add .github/workflows/sync-plugin.yml
git commit -m "feat: add plugin installation test placeholder

Verify plugin directory structure exists.
Add TODO for full installation test when CLI available in CI."
```

---

## Task 5: Add File Update Logic

**Files:**
- Modify: `.github/workflows/sync-plugin.yml`

**Step 1: Add marketplace.json update step**

Add after "Test plugin installation" step:

```yaml
      - name: Update marketplace.json
        run: |
          echo "📝 Updating marketplace.json..."

          PLUGIN_NAME="${{ steps.vars.outputs.plugin_name }}"
          NEW_VERSION="${{ steps.plugin-version.outputs.version }}"

          # Check if plugin exists in marketplace
          PLUGIN_EXISTS=$(jq --arg name "$PLUGIN_NAME" '.plugins | map(select(.name == $name)) | length' .claude-plugin/marketplace.json)

          if [ "$PLUGIN_EXISTS" -eq 0 ]; then
            echo "❌ Error: Plugin '$PLUGIN_NAME' not found in marketplace.json"
            echo "Please add the plugin to marketplace.json first."
            exit 1
          fi

          # Update version
          jq --arg name "$PLUGIN_NAME" --arg version "$NEW_VERSION" \
            '.plugins |= map(if .name == $name then .version = $version else . end)' \
            .claude-plugin/marketplace.json > .claude-plugin/marketplace.json.tmp

          mv .claude-plugin/marketplace.json.tmp .claude-plugin/marketplace.json

          echo "✅ Updated $PLUGIN_NAME to version $NEW_VERSION"

          # Show the change
          echo ""
          echo "Updated entry:"
          jq --arg name "$PLUGIN_NAME" '.plugins[] | select(.name == $name)' .claude-plugin/marketplace.json

      - name: Update README.md version table
        run: |
          echo "📝 Updating README.md..."

          PLUGIN_NAME="${{ steps.vars.outputs.plugin_name }}"
          NEW_VERSION="${{ steps.plugin-version.outputs.version }}"

          # Check if plugin exists in README
          if ! grep -q "| $PLUGIN_NAME |" README.md; then
            echo "⚠️  Warning: Plugin '$PLUGIN_NAME' not found in README.md version table"
            echo "Skipping README update. Please add plugin to README manually."
          else
            # Update version in table
            # Pattern: | plugin-name | description | version |
            sed -i.bak "s/| $PLUGIN_NAME | \(.*\) | .* |/| $PLUGIN_NAME | \1 | $NEW_VERSION |/" README.md
            rm -f README.md.bak

            echo "✅ Updated version in README.md"

            # Show the change
            echo ""
            echo "Updated line:"
            grep "| $PLUGIN_NAME |" README.md
          fi
```

**Step 2: Test file updates**

Run: Actions → Sync Plugin Version → Run workflow
Expected: marketplace.json and README.md show updated version

**Step 3: Verify changes in workflow artifacts**

Expected: Can see diff of marketplace.json and README.md in workflow logs

**Step 4: Commit**

```bash
git add .github/workflows/sync-plugin.yml
git commit -m "feat: add marketplace.json and README.md update logic

Update plugin version in marketplace.json using jq.
Update version in README.md table using sed.
Error handling for missing plugins."
```

---

## Task 6: Add Git Commit and Push

**Files:**
- Modify: `.github/workflows/sync-plugin.yml`

**Step 1: Add commit and push step**

Add after "Update README.md version table" step:

```yaml
      - name: Commit and push changes
        run: |
          PLUGIN_NAME="${{ steps.vars.outputs.plugin_name }}"
          NEW_VERSION="${{ steps.plugin-version.outputs.version }}"

          # Configure git
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          # Check if there are changes
          if ! git diff --quiet .claude-plugin/marketplace.json README.md; then
            echo "📝 Committing changes..."

            git add .claude-plugin/marketplace.json README.md
            git commit -m "chore: bump $PLUGIN_NAME to v$NEW_VERSION

Automated sync from plugin repository release."

            git push

            echo "✅ Changes pushed to main branch"
          else
            echo "ℹ️  No changes detected, skipping commit"
          fi

      - name: Summary
        if: success()
        run: |
          echo "## ✅ Sync Complete" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Plugin:** ${{ steps.vars.outputs.plugin_name }}" >> $GITHUB_STEP_SUMMARY
          echo "**Version:** v${{ steps.plugin-version.outputs.version }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "Marketplace updated successfully!" >> $GITHUB_STEP_SUMMARY
```

**Step 2: Test end-to-end with manual workflow**

Run: Actions → Sync Plugin Version → Run workflow
Expected: Workflow completes, creates commit, pushes to main

**Step 3: Verify commit appears in main branch**

Run: `git pull && git log -1`
Expected: See commit "chore: bump mobile-ui-testing to v3.1.0"

**Step 4: Commit**

```bash
git add .github/workflows/sync-plugin.yml
git commit -m "feat: add git commit and push logic

Automatically commit marketplace.json and README.md changes.
Skip commit if no changes detected.
Add job summary for visibility."
```

---

## Task 7: Add PR Creation on Failure

**Files:**
- Modify: `.github/workflows/sync-plugin.yml`

**Step 1: Add permissions for PR creation**

Add at the top of the `sync` job (after `runs-on`):

```yaml
    permissions:
      contents: write
      pull-requests: write
```

**Step 2: Add PR creation step**

Add at the end of the workflow (after "Summary" step):

```yaml
      - name: Create PR on failure
        if: failure()
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "sync: failed update for ${{ steps.vars.outputs.plugin_name }} v${{ steps.vars.outputs.version }}"
          title: "⚠️ Failed to sync ${{ steps.vars.outputs.plugin_name }} v${{ steps.vars.outputs.version }}"
          body: |
            ## ❌ Automated Sync Failed

            **Plugin:** ${{ steps.vars.outputs.plugin_name }}
            **Version Tag:** ${{ steps.vars.outputs.version }}
            **Repository:** ${{ steps.vars.outputs.repo_url }}

            ### Error Details

            The automated sync workflow failed validation. Check the [workflow logs](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}) for details.

            ### Common Causes

            - **Version mismatch:** Git tag doesn't match plugin.json version
            - **Invalid JSON:** plugin.json has syntax errors or missing required fields
            - **Installation failed:** Plugin structure is invalid
            - **Repository unreachable:** Clone failed (network, permissions, etc.)

            ### How to Fix

            1. Review the error in the workflow logs
            2. Fix the issue in the plugin repository
            3. Create a new git tag with the corrected version
            4. The workflow will automatically retry

            ### Manual Override

            If you need to bypass validation:
            1. Manually edit `.claude-plugin/marketplace.json`
            2. Update the version for this plugin
            3. Commit and close this PR
          branch: "sync-failure-${{ steps.vars.outputs.plugin_name }}-${{ steps.vars.outputs.version }}"
          delete-branch: true
```

**Step 3: Test PR creation with forced failure**

Modify one validation step temporarily to fail, run workflow
Expected: Workflow fails, creates PR with error details

**Step 4: Verify PR was created**

Check: GitHub PRs tab should show new PR with "Failed to sync" title
Expected: PR has clear error message and instructions

**Step 5: Revert test change and commit**

```bash
git add .github/workflows/sync-plugin.yml
git commit -m "feat: add PR creation on validation failure

Create PR with error details when sync validation fails.
Includes troubleshooting guide and manual override instructions.
Uses peter-evans/create-pull-request action."
```

---

## Task 8: Create Plugin Notification Workflow Template

**Files:**
- Create: `.github/plugin-workflows/marketplace-notify.yml`
- Create: `.github/plugin-workflows/README.md`

**Step 1: Create template workflow**

Create `.github/plugin-workflows/marketplace-notify.yml`:

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
      - name: Checkout
        uses: actions/checkout@v4

      - name: Extract version from tag
        id: version
        run: |
          TAG_NAME="${GITHUB_REF#refs/tags/}"
          echo "tag=$TAG_NAME" >> $GITHUB_OUTPUT
          echo "Released version: $TAG_NAME"

      - name: Send webhook to marketplace
        env:
          MARKETPLACE_TOKEN: ${{ secrets.MARKETPLACE_TOKEN }}
        run: |
          curl -X POST \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Authorization: token $MARKETPLACE_TOKEN" \
            https://api.github.com/repos/vladkarpman/vladkarpman-plugins/dispatches \
            -d '{
              "event_type": "plugin_release",
              "client_payload": {
                "plugin_name": "${{ github.event.repository.name }}",
                "version": "${{ steps.version.outputs.tag }}",
                "repo_url": "${{ github.event.repository.clone_url }}"
              }
            }'

      - name: Summary
        run: |
          echo "## 📢 Marketplace Notified" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Plugin:** ${{ github.event.repository.name }}" >> $GITHUB_STEP_SUMMARY
          echo "**Version:** ${{ steps.version.outputs.tag }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "The marketplace will sync this release automatically." >> $GITHUB_STEP_SUMMARY
          echo "Check the [marketplace repository](https://github.com/vladkarpman/vladkarpman-plugins/actions) for sync status." >> $GITHUB_STEP_SUMMARY
```

**Step 2: Create README with setup instructions**

Create `.github/plugin-workflows/README.md`:

```markdown
# Plugin Marketplace Notification Workflow

This directory contains the workflow template that plugin repositories should add to automatically notify the marketplace when a new version is released.

## Setup Instructions

### One-Time Setup per Plugin Repository

**1. Create GitHub Personal Access Token**

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name: "Marketplace Sync Token"
4. Scopes: Select only `repo` (Full control of private repositories)
5. Click "Generate token"
6. Copy the token (you won't see it again)

**2. Add Token to Plugin Repository**

1. Go to plugin repository (e.g., mobile-ui-testing)
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `MARKETPLACE_TOKEN`
5. Value: Paste the token from step 1
6. Click "Add secret"

**3. Add Workflow to Plugin Repository**

1. Copy `marketplace-notify.yml` to plugin repo at: `.github/workflows/marketplace-notify.yml`
2. Commit and push:
   ```bash
   git add .github/workflows/marketplace-notify.yml
   git commit -m "ci: add marketplace notification workflow"
   git push
   ```

### Release Process

Once setup is complete, releasing a new version is simple:

```bash
# 1. Update version in .claude-plugin/plugin.json
# Edit plugin.json and change metadata.version to "3.2.0"

# 2. Commit the version change
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 3.2.0"

# 3. Create and push git tag
git tag v3.2.0
git push origin v3.2.0

# 4. Workflow automatically triggers and notifies marketplace
# Check Actions tab to see notification workflow run
# Check marketplace repo to see sync workflow run
```

### Troubleshooting

**Workflow doesn't trigger:**
- Verify tag format matches `v*.*.*` (e.g., v1.2.3)
- Check that workflow file is on the main branch

**Webhook fails to send:**
- Verify `MARKETPLACE_TOKEN` secret exists in plugin repo
- Verify token has `repo` scope
- Check token hasn't expired

**Marketplace sync fails:**
- Check marketplace Actions tab for sync workflow
- Review error message in created PR
- Verify version in plugin.json matches git tag

## Workflow Details

**Triggers:** Push of git tags matching pattern `v*.*.*`

**Actions:**
1. Extracts version from git tag
2. Sends `repository_dispatch` webhook to marketplace
3. Marketplace automatically validates and syncs

**Required Secret:** `MARKETPLACE_TOKEN` with `repo` scope
```

**Step 3: Commit template files**

```bash
git add .github/plugin-workflows/
git commit -m "docs: add plugin notification workflow template

Add reusable workflow template for plugin repositories.
Include comprehensive setup instructions and troubleshooting guide."
```

---

## Task 9: Setup Notification Workflow in mobile-ui-testing

**Files:**
- Create in mobile-ui-testing repo: `.github/workflows/marketplace-notify.yml`

**Step 1: Navigate to mobile-ui-testing repository**

```bash
cd /path/to/mobile-ui-testing
git pull
```

**Step 2: Copy workflow template**

```bash
mkdir -p .github/workflows
cp /path/to/vladkarpman-plugins/.github/plugin-workflows/marketplace-notify.yml .github/workflows/
```

Or create `.github/workflows/marketplace-notify.yml` with the template content.

**Step 3: Verify workflow file**

Run: `cat .github/workflows/marketplace-notify.yml`
Expected: See complete workflow with marketplace webhook

**Step 4: Commit to mobile-ui-testing**

```bash
git add .github/workflows/marketplace-notify.yml
git commit -m "ci: add marketplace notification workflow

Automatically notify marketplace when version tags are pushed.
Enables automated version syncing."
git push
```

**Step 5: Add MARKETPLACE_TOKEN secret**

Manual steps:
1. Go to https://github.com/vladkarpman/mobile-ui-testing/settings/secrets/actions
2. Click "New repository secret"
3. Name: `MARKETPLACE_TOKEN`
4. Value: (use the personal access token with repo scope)
5. Click "Add secret"

---

## Task 10: Setup Notification Workflow in compose-designer

**Files:**
- Create in compose-designer-plugin repo: `.github/workflows/marketplace-notify.yml`

**Step 1: Navigate to compose-designer repository**

```bash
cd /path/to/compose-designer-plugin
git pull
```

**Step 2: Copy workflow template**

```bash
mkdir -p .github/workflows
cp /path/to/vladkarpman-plugins/.github/plugin-workflows/marketplace-notify.yml .github/workflows/
```

**Step 3: Commit to compose-designer-plugin**

```bash
git add .github/workflows/marketplace-notify.yml
git commit -m "ci: add marketplace notification workflow

Automatically notify marketplace when version tags are pushed.
Enables automated version syncing."
git push
```

**Step 4: Add MARKETPLACE_TOKEN secret**

Manual steps:
1. Go to https://github.com/vladkarpman/compose-designer-plugin/settings/secrets/actions
2. Click "New repository secret"
3. Name: `MARKETPLACE_TOKEN`
4. Value: (use the same personal access token)
5. Click "Add secret"

---

## Task 11: Test End-to-End Flow

**Files:**
- Test only, no files modified

**Step 1: Create test tag in mobile-ui-testing**

```bash
cd /path/to/mobile-ui-testing
git tag v3.1.0-test
git push origin v3.1.0-test
```

**Step 2: Verify notification workflow triggers**

1. Go to https://github.com/vladkarpman/mobile-ui-testing/actions
2. Find "Notify Marketplace on Release" workflow
3. Verify it runs successfully

Expected: Workflow shows "Marketplace Notified" summary

**Step 3: Verify marketplace sync workflow triggers**

1. Go to https://github.com/vladkarpman/vladkarpman-plugins/actions
2. Find "Sync Plugin Version" workflow
3. Verify it runs automatically

Expected: Workflow validates, updates files, commits to main

**Step 4: Verify marketplace was updated**

```bash
cd /path/to/vladkarpman-plugins
git pull
cat .claude-plugin/marketplace.json | jq '.plugins[] | select(.name=="mobile-ui-testing")'
```

Expected: Version shows "3.1.0" (without -test suffix if that's in plugin.json)

**Step 5: Clean up test tag**

```bash
cd /path/to/mobile-ui-testing
git tag -d v3.1.0-test
git push origin :refs/tags/v3.1.0-test
```

**Step 6: Verify test in compose-designer**

Repeat steps 1-5 for compose-designer-plugin with appropriate version tag.

---

## Task 12: Document Automation in Main README

**Files:**
- Modify: `README.md`

**Step 1: Add automation section to README**

Add new section after "Available Plugins" table and before "Plugins" section:

```markdown
## Plugin Version Management

This marketplace uses **automated version syncing**. When plugin maintainers release new versions, the marketplace updates automatically.

### How It Works

1. **Plugin Release:** Maintainer updates version in plugin.json and pushes git tag (e.g., `v3.2.0`)
2. **Notification:** Plugin's GitHub Action notifies this marketplace via webhook
3. **Validation:** Marketplace validates version match, JSON schema, and installation
4. **Sync:** If validation passes, marketplace.json and this README are automatically updated
5. **Audit:** Every update creates a git commit for full traceability

### For Plugin Maintainers

To enable automated sync for your plugin:

1. Add `.github/workflows/marketplace-notify.yml` (see `.github/plugin-workflows/` for template)
2. Add `MARKETPLACE_TOKEN` secret to your plugin repository
3. Release new versions by creating git tags matching your plugin.json version

See [plugin workflow documentation](.github/plugin-workflows/README.md) for detailed setup instructions.

### Version History

All version updates are tracked in git history. To see version changes:

```bash
git log --grep="chore: bump" --oneline
```
```

**Step 2: Verify formatting**

Run: `cat README.md`
Expected: New section appears in correct location with proper formatting

**Step 3: Commit README update**

```bash
git add README.md
git commit -m "docs: document automated version management

Add section explaining webhook-triggered automation.
Include instructions for plugin maintainers and version history tracking."
```

---

## Task 13: Add Final Documentation

**Files:**
- Create: `docs/AUTOMATION.md`

**Step 1: Create comprehensive automation guide**

Create `docs/AUTOMATION.md`:

```markdown
# Marketplace Automation Guide

## Overview

The vladkarpman-plugins marketplace uses webhook-triggered automation to sync plugin versions. When plugins release new versions, the marketplace updates automatically within minutes.

## Architecture

```
Plugin Repository                    Marketplace Repository
─────────────────                    ──────────────────────

1. Developer pushes tag v3.2.0
        ↓
2. GitHub Action triggers
        ↓
3. Sends repository_dispatch  ────→  4. Sync workflow receives event
                                              ↓
                                     5. Validates (3 checks):
                                        - Tag matches plugin.json
                                        - JSON schema valid
                                        - Plugin installs
                                              ↓
                              ┌──────────────┴────────────────┐
                              ↓                                ↓
                    6a. Validation passes          6b. Validation fails
                         - Updates files               - Creates PR
                         - Auto commits                - Includes errors
                         - Pushes to main              - Manual review needed
```

## Validation Checks

### 1. Tag-Version Match

Ensures git tag matches plugin.json version:

```bash
Tag: v3.2.0 → File: "3.2.0" ✅
Tag: v3.2.0 → File: "3.1.9" ❌
```

### 2. JSON Schema Validation

Verifies plugin.json structure:

```json
{
  "name": "plugin-name",          // Required
  "metadata": {
    "version": "3.2.0",           // Required
    "description": "..."          // Required
  }
}
```

### 3. Installation Test

Checks plugin directory structure:
- `.claude-plugin/` exists
- `plugin.json` exists
- Directory is readable

## What Gets Updated

### marketplace.json

```json
{
  "plugins": [
    {
      "name": "mobile-ui-testing",
      "version": "3.1.0"  // ← Auto-updated
    }
  ]
}
```

### README.md

Only the version table is auto-updated:

```markdown
| Plugin | Description | Version |
|--------|-------------|---------|
| mobile-ui-testing | ... | 3.1.0 |  ← Auto-updated
```

Detailed plugin sections remain manual for custom content.

## Error Handling

### When Validation Fails

1. Workflow creates PR with failing checks
2. PR includes:
   - Error message
   - Workflow logs link
   - Troubleshooting guide
   - Manual override instructions

### Common Failures

**Version Mismatch**
```
❌ Error: Version mismatch
Git tag: v3.2.0
plugin.json: 3.1.9
```
Fix: Update plugin.json to match tag, create new tag

**Invalid JSON**
```
❌ Error: Invalid JSON in plugin.json
```
Fix: Validate JSON syntax, ensure required fields exist

**Installation Failed**
```
❌ Error: Missing .claude-plugin directory
```
Fix: Verify plugin directory structure

## Rollback Procedure

### Automated Rollback (Recommended)

```bash
# Find the bad commit
git log --grep="chore: bump" --oneline

# Revert it
git revert <commit-hash>
git push
```

### Manual Override

```bash
# Edit marketplace.json directly
jq '.plugins |= map(if .name == "plugin-name" then .version = "3.1.0" else . end)' marketplace.json

# Commit
git commit -am "revert: rollback plugin-name to v3.1.0"
git push
```

## Monitoring

### Check Sync Status

View recent syncs:
```bash
git log --grep="chore: bump" --oneline -10
```

### View Failed Syncs

Check PRs with "Failed to sync" in title:
```bash
gh pr list --label "automation-failure"
```

### Workflow Runs

- Plugin notification: `<plugin-repo>/actions/workflows/marketplace-notify.yml`
- Marketplace sync: `vladkarpman-plugins/actions/workflows/sync-plugin.yml`

## Security

### Token Scope

`MARKETPLACE_TOKEN` requires only:
- ✅ `repo` scope (trigger workflows)
- ❌ No admin access
- ❌ No write access to plugin repos

### Token Storage

- Stored in GitHub Secrets
- Never in code or logs
- Rotate periodically

### Validation Safety

- Multi-layer validation prevents bad releases
- Failed validations require manual review
- No direct push on failures (PR only)

## Maintenance

### Adding New Plugins

1. Add plugin to `marketplace.json` manually (first time)
2. Plugin maintainer adds notification workflow
3. Future versions sync automatically

### Updating Workflows

Workflow changes apply immediately to next trigger. No plugin repo updates needed unless webhook payload changes.

### Token Rotation

If rotating `MARKETPLACE_TOKEN`:
1. Generate new token
2. Update in all plugin repositories
3. Old token can be revoked after verification

## Troubleshooting

### Workflow Not Triggering

**Symptom:** Tag pushed but no marketplace sync

**Checks:**
1. Verify notification workflow exists in plugin repo
2. Check workflow file is on main branch
3. Confirm tag format is `v*.*.*`
4. Verify `MARKETPLACE_TOKEN` secret exists

### Validation Always Fails

**Symptom:** Every sync creates PR with error

**Checks:**
1. Verify plugin.json version matches tag exactly
2. Check JSON syntax with `jq empty plugin.json`
3. Verify required fields exist
4. Test clone: `git clone --depth 1 --branch v1.2.3 <repo>`

### Multiple Failed PRs

**Symptom:** Many open PRs for same plugin

**Solution:**
1. Close old PRs (they're stale)
2. Fix issue in plugin repo
3. Create new tag
4. New PR will be created if still failing

## Future Enhancements

- [ ] Full installation test with Claude Code CLI
- [ ] Breaking change detection
- [ ] Automated plugin testing in CI
- [ ] Download metrics tracking
- [ ] Multi-marketplace support
```

**Step 2: Commit automation guide**

```bash
git add docs/AUTOMATION.md
git commit -m "docs: add comprehensive automation guide

Complete guide covering architecture, validation, error handling,
rollback procedures, monitoring, and troubleshooting."
```

---

## Task 14: Final Verification and Cleanup

**Files:**
- Test only, verify all components

**Step 1: Verify all workflows are in place**

```bash
# Marketplace workflows
ls -la .github/workflows/sync-plugin.yml

# Template workflows
ls -la .github/plugin-workflows/

# Documentation
ls -la docs/AUTOMATION.md docs/plans/
```

Expected: All files exist

**Step 2: Verify plugin repos have notification workflows**

Check:
- https://github.com/vladkarpman/mobile-ui-testing/.github/workflows/marketplace-notify.yml
- https://github.com/vladkarpman/compose-designer-plugin/.github/workflows/marketplace-notify.yml

Expected: Both files exist on main branch

**Step 3: Verify secrets are configured**

Check:
- mobile-ui-testing repo secrets for `MARKETPLACE_TOKEN`
- compose-designer-plugin repo secrets for `MARKETPLACE_TOKEN`

Expected: Both have the secret configured

**Step 4: Run manual sync test**

Go to: Actions → Sync Plugin Version → Run workflow manually
Test with: mobile-ui-testing, v3.1.0, https://github.com/vladkarpman/mobile-ui-testing.git

Expected: Workflow completes successfully

**Step 5: Review commit history**

```bash
git log --oneline -20
```

Expected: See all commits from this implementation

**Step 6: Final commit**

```bash
git commit --allow-empty -m "chore: marketplace automation implementation complete

All components implemented and tested:
- ✅ Marketplace sync workflow with validation
- ✅ PR creation on failure
- ✅ Plugin notification workflows in both repos
- ✅ Comprehensive documentation
- ✅ End-to-end testing complete

Ready for production use."
```

---

## Completion Checklist

- [ ] Marketplace sync workflow created and tested
- [ ] Validation checks implemented (tag match, schema, installation)
- [ ] File update logic working (marketplace.json, README.md)
- [ ] PR creation on failure configured
- [ ] Plugin notification workflow template created
- [ ] mobile-ui-testing has notification workflow
- [ ] compose-designer has notification workflow
- [ ] Both plugins have MARKETPLACE_TOKEN secret
- [ ] End-to-end testing completed
- [ ] Documentation updated (README.md, AUTOMATION.md)
- [ ] All commits pushed to main

## Post-Implementation

### Immediate Next Steps

1. Monitor first real release (wait for actual plugin update)
2. Verify automation works without manual trigger
3. Check timing (should complete within 5 minutes)

### Future Improvements

1. Add Claude Code CLI to CI for full installation testing
2. Implement breaking change detection
3. Add Slack/email notifications on successful sync
4. Create dashboard showing plugin version history
5. Add rate limiting for high-frequency updates
