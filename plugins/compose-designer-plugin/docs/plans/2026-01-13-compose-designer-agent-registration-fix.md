# Compose Designer Agent Registration Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix compose-designer plugin so agents register properly with Claude Code's Task tool after installation.

**Architecture:** Add explicit agent path configuration to plugin.json manifest, then update marketplace, reinstall plugin, and verify agents are discoverable.

**Tech Stack:** Claude Code plugin system, JSON manifest configuration, Git

---

## Problem Analysis

**Current State:**
- Plugin has 3 agents: `design-generator`, `visual-validator`, `device-tester`
- Agents are in `./agents/` directory with proper frontmatter
- Plugin installs successfully but agents not available in Task tool
- Error: `Agent type 'compose-designer:design-generator' not found`

**Root Cause:**
- `plugin.json` doesn't explicitly declare agent path
- Claude Code auto-discovery may require restart OR explicit path declaration
- Plugin follows convention but may need explicit configuration

**Solution:**
Add explicit agent path to plugin.json, update marketplace version, reinstall, and restart Claude Code to register agents.

---

## Task 1: Add Explicit Agent Path to plugin.json

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: Read current plugin.json**

Run: `cat .claude-plugin/plugin.json`
Expected: See current manifest without agents field

**Step 2: Add agents field**

Update plugin.json to include:

```json
{
  "name": "compose-designer",
  "version": "0.1.1",
  "description": "Transform design mockups (screenshots, Figma) into production-ready Jetpack Compose code with automated validation and device testing",
  "author": {
    "name": "Vladislav Karpman",
    "url": "https://github.com/vladkarpman/vladkarpman-plugins"
  },
  "homepage": "https://github.com/vladkarpman/vladkarpman-plugins/tree/main/compose-designer",
  "repository": "https://github.com/vladkarpman/vladkarpman-plugins",
  "license": "MIT",
  "keywords": ["compose", "android", "design", "figma", "ui-generation", "code-generation", "mobile"],
  "agents": "./agents"
}
```

**Changes:**
- Bumped version: `0.1.0` → `0.1.1`
- Added: `"agents": "./agents"` field

**Step 3: Verify JSON syntax**

Run: `cat .claude-plugin/plugin.json | python3 -m json.tool`
Expected: Valid JSON output with no errors

**Step 4: Commit changes**

```bash
git add .claude-plugin/plugin.json
git commit -m "fix: add explicit agent path to enable agent registration

- Added agents field pointing to ./agents directory
- Bumped version to 0.1.1
- Ensures Claude Code discovers agents after plugin installation"
```

---

## Task 2: Update Marketplace Entry

**Files:**
- Modify: `/Users/vladislavkarpman/projects/vladkarpman-plugins/.claude-plugin/marketplace.json:22-31`

**Step 1: Navigate to marketplace repo**

Run: `cd /Users/vladislavkarpman/projects/vladkarpman-plugins`
Expected: Changed directory

**Step 2: Read current marketplace entry**

Run: `jq '.plugins[] | select(.name == "compose-designer")' .claude-plugin/marketplace.json`
Expected: See compose-designer entry with version "0.1.0"

**Step 3: Update version in marketplace.json**

Update the compose-designer entry:

```json
{
  "name": "compose-designer",
  "source": {
    "source": "url",
    "url": "https://github.com/vladkarpman/compose-designer-plugin.git"
  },
  "description": "Transform design mockups into production-ready Jetpack Compose code through automated three-phase workflow with visual validation and device testing.",
  "version": "0.1.1",
  "strict": true
}
```

**Changes:**
- Updated version: `0.1.0` → `0.1.1`

**Step 4: Verify JSON syntax**

Run: `cat .claude-plugin/marketplace.json | python3 -m json.tool`
Expected: Valid JSON output

**Step 5: Commit marketplace changes**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore: bump compose-designer to v0.1.1

- Updated marketplace entry to reflect agent registration fix
- Version now includes explicit agent path configuration"
```

---

## Task 3: Push Plugin Changes to GitHub

**Files:**
- Push: compose-designer-plugin repository

**Step 1: Return to plugin repo**

Run: `cd /Users/vladislavkarpman/projects/compose-designer-plugin`
Expected: Changed directory

**Step 2: Verify commit is ready**

Run: `git status`
Expected: Branch clean or "Your branch is ahead"

**Step 3: Push plugin changes**

Run: `git push origin master`
Expected: Push successful, updates reflected on GitHub

---

## Task 4: Push Marketplace Changes to GitHub

**Files:**
- Push: vladkarpman-plugins repository

**Step 1: Navigate to marketplace repo**

Run: `cd /Users/vladislavkarpman/projects/vladkarpman-plugins`
Expected: Changed directory

**Step 2: Verify commit is ready**

Run: `git status`
Expected: Branch clean or "Your branch is ahead"

**Step 3: Push marketplace changes**

Run: `git push origin master`
Expected: Push successful, v0.1.1 available in marketplace

---

## Task 5: Update Local Marketplace Cache

**Files:**
- None (Claude Code command)

**Step 1: Update marketplace**

Run: `claude plugin marketplace update vladkarpman-plugins`
Expected: ✔ Successfully updated marketplace

**Step 2: Verify new version available**

Run: `claude plugin marketplace list | grep -A 3 vladkarpman-plugins`
Expected: See marketplace entry with updated timestamp

---

## Task 6: Reinstall Plugin with New Version

**Files:**
- None (Claude Code command)

**Step 1: Uninstall current version**

Run: `claude plugin uninstall compose-designer`
Expected: ✔ Successfully uninstalled plugin

**Step 2: Install new version**

Run: `claude plugin install compose-designer@vladkarpman-plugins`
Expected: ✔ Successfully installed plugin: compose-designer@vladkarpman-plugins (scope: user)

**Step 3: Verify installation**

Run: `ls -la ~/.claude/plugins/cache/vladkarpman-plugins/compose-designer/0.1.1/.claude-plugin/plugin.json`
Expected: File exists with version 0.1.1

---

## Task 7: Verify Agent Registration (After Claude Code Restart)

**Files:**
- None (verification step)

**Step 1: Document restart instruction**

Create verification note:

```
⚠️  RESTART REQUIRED

Before proceeding:
1. Exit this Claude Code session
2. Restart Claude Code CLI
3. Return to project directory
4. Verify agents are registered

Verification command:
  claude --help | grep -i agent

Expected: Should see agent-related help or no errors when using Task tool
```

**Step 2: Test agent availability (after restart)**

In NEW Claude Code session, test:

```kotlin
// This should work after restart
Task tool with subagent_type: "compose-designer:design-generator"
```

Expected: Agent launches successfully, no "not found" error

---

## Task 8: Test Complete Plugin Workflow

**Files:**
- Test: `/Users/vladislavkarpman/projects/compose-designer-test-project`

**Step 1: Navigate to test project**

Run: `cd /Users/vladislavkarpman/projects/compose-designer-test-project`
Expected: Changed directory

**Step 2: Run create command with test image**

Run via Skill tool:
```
/compose-design create --input test-images/jetchat.png --name ChatScreen --type screen
```

Expected workflow:
1. Phase 0: Config loaded, dependencies validated ✓
2. Phase 1: design-generator agent launches ✓
3. Phase 2: visual-validator agent launches ✓
4. Phase 3: device-tester agent launches ✓
5. Final report generated ✓

**Step 3: Verify generated output**

Run: `ls -la app/src/main/java/com/test/composedesigner/ui/screens/ChatScreenScreen.kt`
Expected: File exists with Compose code

**Step 4: Verify compilation**

Run: `./gradlew compileDebugKotlin`
Expected: BUILD SUCCESSFUL

---

## Verification Checklist

After completing all tasks:

- [ ] plugin.json has `"agents": "./agents"` field
- [ ] Plugin version bumped to 0.1.1
- [ ] Marketplace entry updated to 0.1.1
- [ ] Both repos pushed to GitHub
- [ ] Plugin reinstalled from marketplace
- [ ] Claude Code restarted
- [ ] `compose-designer:design-generator` agent available in Task tool
- [ ] `compose-designer:visual-validator` agent available in Task tool
- [ ] `compose-designer:device-tester` agent available in Task tool
- [ ] Full workflow runs without "agent not found" errors
- [ ] Generated Compose code compiles successfully

---

## Alternative Solutions (If Explicit Path Doesn't Work)

**Option A: Check Agent Frontmatter Format**

If agents still don't register after restart, verify frontmatter:

```yaml
---
description: Agent description here
capabilities:
  - Capability 1
  - Capability 2
model: sonnet
color: blue
tools:
  - Read
  - Write
---
```

Required fields:
- `description`: Third-person description for triggering
- `model`: sonnet, opus, or haiku
- `tools`: Array of allowed tools

**Option B: Use Different Agent Names**

If namespace collision, try:
- `compose-designer-design-generator`
- `compose-designer-visual-validator`
- `compose-designer-device-tester`

Update both agent filenames AND subagent_type references in commands.

**Option C: Add Agent Discovery Script**

Create `.claude-plugin/discover-agents.sh`:

```bash
#!/bin/bash
find ./agents -name "*.md" -type f
```

Then add to plugin.json:
```json
{
  "agents": {
    "path": "./agents",
    "discover": "./.claude-plugin/discover-agents.sh"
  }
}
```

---

## Success Criteria

**Primary Goal Achieved When:**
1. Plugin installs without errors
2. Claude Code restart completes
3. Task tool can invoke `compose-designer:design-generator`
4. Task tool can invoke `compose-designer:visual-validator`
5. Task tool can invoke `compose-designer:device-tester`
6. Full `/compose-design create` workflow executes end-to-end
7. Generated Compose code compiles and matches design baseline

**Quality Metrics:**
- Agent registration time: < 5 seconds after restart
- Agent invocation success rate: 100%
- Generated code compilation success rate: 100%
- Visual similarity score: ≥ 92% (from ralph-wiggum validation)

---

## Notes

**DRY Principle:**
- Single source of truth for agent paths (plugin.json)
- Reuse existing agent definitions (no duplication)
- Centralized version management

**YAGNI Principle:**
- Add only explicit path field (don't overconfigure)
- Avoid creating discovery scripts unless necessary
- Keep plugin.json minimal

**Testing Strategy:**
- Test each task immediately after completion
- Verify JSON syntax after each edit
- Commit frequently with descriptive messages
- Test full workflow only after all tasks complete
