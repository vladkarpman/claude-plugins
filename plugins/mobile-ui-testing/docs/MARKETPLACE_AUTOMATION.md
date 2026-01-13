# Marketplace Automation Setup

This document explains how to set up automatic marketplace updates when releasing new versions.

## Overview

When you create a new release tag (e.g., `v3.3.2`), the GitHub Actions workflow will:

1. Create a GitHub release
2. Automatically create a PR to update the marketplace repository
3. Update both `marketplace.json` and `README.md` with the new version

## Setup Instructions

### 1. Create a Personal Access Token (PAT)

1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
   - Direct link: https://github.com/settings/tokens

2. Click **"Generate new token"** → **"Generate new token (classic)"**

3. Configure the token:
   - **Note:** `mobile-ui-testing marketplace automation`
   - **Expiration:** Choose your preference (90 days, 1 year, or no expiration)
   - **Scopes:** Check `repo` (Full control of private repositories)
     - This grants access to read/write to your marketplace repository

4. Click **"Generate token"**

5. **Copy the token immediately** (you won't be able to see it again!)

### 2. Add Token as Repository Secret

1. Go to your **mobile-ui-testing** repository on GitHub
   - https://github.com/vladkarpman/mobile-ui-testing

2. Navigate to **Settings** → **Secrets and variables** → **Actions**

3. Click **"New repository secret"**

4. Configure the secret:
   - **Name:** `MARKETPLACE_TOKEN`
   - **Secret:** Paste the PAT you created in step 1

5. Click **"Add secret"**

### 3. Test the Automation

The workflow will run automatically on the next release. To test it:

```bash
# Bump version in plugin.json
# ... make your changes ...

# Commit and tag
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 3.3.2"
git tag v3.3.2
git push origin main --tags
```

The workflow will:
1. Create a GitHub release at https://github.com/vladkarpman/mobile-ui-testing/releases/tag/v3.3.2
2. Create a PR at https://github.com/vladkarpman/vladkarpman-plugins/pulls

### 4. Review and Merge

Once the PR is created automatically:
1. Review the changes in the marketplace PR
2. Merge the PR
3. Users can now update via:
   ```bash
   /plugin marketplace update vladkarpman-plugins
   /plugin install mobile-ui-testing
   ```

## How It Works

The workflow step:

```yaml
- name: Update Marketplace
  if: ${{ secrets.MARKETPLACE_TOKEN != '' }}
  run: |
    # Clone marketplace repo
    # Update version in marketplace.json and README.md
    # Create PR with the changes
```

**Key features:**
- Only runs if `MARKETPLACE_TOKEN` secret exists
- Uses bot identity for commits: `github-actions[bot]`
- Creates descriptive PR with link to release
- Fails gracefully if secret is missing (workflow still succeeds)

## Security Notes

- The PAT has `repo` scope, granting full access to your repositories
- Keep the token secure - never commit it to code
- Consider setting an expiration date (90 days or 1 year)
- Rotate the token periodically
- If compromised, immediately revoke the token at https://github.com/settings/tokens

## Troubleshooting

### Workflow skips marketplace update
- Check that `MARKETPLACE_TOKEN` secret exists in repository settings
- Verify the token hasn't expired

### Authentication failed
- Verify the PAT has `repo` scope
- Check the token is still valid at https://github.com/settings/tokens
- Regenerate the token if needed

### PR creation failed
- Check the marketplace repository exists: https://github.com/vladkarpman/vladkarpman-plugins
- Verify the token has write access to the marketplace repo
- Check GitHub Actions logs for detailed error message

## Manual Fallback

If automation fails, you can always update the marketplace manually:

```bash
cd /path/to/vladkarpman-plugins
git checkout -b update-mobile-ui-testing-X.Y.Z

# Edit .claude-plugin/marketplace.json
# Edit README.md

git add .
git commit -m "chore: update mobile-ui-testing to vX.Y.Z"
git push origin update-mobile-ui-testing-X.Y.Z

# Create PR on GitHub
```
