# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.3.1] - 2026-01-13

### Changed

- **Distribution Model** - Switched to GitHub-only distribution:
  - Removed npm publishing (not needed for Claude Code plugins)
  - Use tag-based releases with direct GitHub installation
  - Updated CI workflow to auto-create releases from tags
  - Removed `package.json`, use `.claude-plugin/plugin.json` instead
  - Updated README with GitHub installation instructions: `/plugin install github:vladkarpman/mobile-ui-testing#v3.3.1`

## [3.3.0] - 2026-01-13

### Changed

- **BREAKING: Recording Artifacts Reorganization** - All recording artifacts now stored in `recording/` subfolder:
  - `test.yaml` remains at top level (it's the actual test, not a recording artifact)
  - All other files moved to `tests/{name}/recording/`:
    - `touch_events.json`
    - `typing_sequences.json`
    - `verifications.json`
    - `checkpoints.json`
    - `recording.mp4`
    - `screenshots/`
  - Updated all Python scripts to use new paths
  - Updated all command workflows (`/record-test`, `/stop-recording`)
  - Non-recording commands (`/create-test`, `/generate-test`) no longer create `screenshots/` directory
  - Integration tests updated and passing

### Added

- **Keyboard Typing Detection** - Automatic detection and conversion of keyboard taps:
  - `scripts/analyze-typing.py` - Detects typing sequences from touch events
  - Interactive typing interview during `/stop-recording`
  - Collects actual typed text from user (not guessed)
  - Converts 8+ keyboard taps into single `type` command
  - Supports submit action (Enter/Search key)
  - Generated YAML includes:
    ```yaml
    - type: {text: "search query", submit: true}
    # Replaced touches 5-12 (8 keyboard taps)
    ```
  - Documentation: `docs/testing/typing-detection-test-guide.md`

### Migration

- No migration needed - `tests/` folder is gitignored
- New recordings automatically use new structure
- Old test artifacts (if any) continue to work if manually created with flat structure

## [3.2.0] - 2026-01-13

### Added

- **Conditional Logic Operators** - Runtime branching without separate test files:
  - `if_exists` - Execute steps if element exists
  - `if_not_exists` - Execute steps if element doesn't exist
  - `if_all_exist` - Execute if ALL elements exist (AND logic)
  - `if_any_exist` - Execute if ANY element exists (OR logic)
  - `if_screen` - Execute based on AI vision screen matching
  - Full nesting support (unlimited depth)
  - Then/else branch execution
  - Decimal step numbering for branch steps (3.1, 3.2)

- **Verification Interview Feature** (Experimental) - AI-guided verification insertion:
  - Automatic checkpoint detection (screen changes, waits, navigation)
  - AI-powered verification suggestions via Claude API
  - Interactive verification selection workflow
  - Enhanced test generation with verifications at checkpoints
  - `scripts/analyze-checkpoints.py` for checkpoint detection
  - `scripts/suggest-verification.py` for AI suggestions
  - `scripts/generate-test.py` supports verification insertion

- **Integration Test Suite** - Comprehensive testing with Android Calculator:
  - `tests/integration/calculator/` test files
  - `tests/integration/run-integration-tests.sh` test runner
  - All commands and conditional operators validated

- **Example Tests** - Reference implementations:
  - `tests/integration/examples/conditional-basic.test.yaml`
  - `tests/integration/examples/conditional-nested.test.yaml`
  - `tests/integration/examples/conditional-screen.test.yaml`

- **Reference Documentation**:
  - `skills/yaml-test-schema/references/conditionals.md` - Complete conditional syntax
  - Updated `skills/yaml-test-schema/SKILL.md` with conditional operators

- **Python Dependencies** - Added to `scripts/requirements.txt`:
  - `anthropic>=0.39.0` for AI verification suggestions
  - `Pillow>=10.0.0` for image processing
  - `imagehash>=4.3.0` for perceptual hashing

### Changed

- **Deprecated `if_present` operator** - Use `if_exists` instead:
  - Better error handling
  - Full nesting support
  - Consistent with new conditional operators
  - `if_present` still works for backwards compatibility

- **Updated README.md** - Comprehensive documentation updates:
  - Flow Control section with all conditional operators
  - Conditional Logic section with examples
  - Verification Interview feature documentation
  - Updated templates to use `if_exists`

- **Updated CLAUDE.md** - Architecture documentation:
  - Conditional logic architecture
  - Verification interview pipeline
  - Design document references

### Fixed

- **Recording pipeline** - Improved frame extraction timing (100ms before touch)
- **Step numbering** - Proper decimal notation for nested steps

### Security

- No security updates in this release

## [3.1.0] - [Previous Release Date]

### Added
- Initial recording features
- Basic test execution
- YAML test schema

[Continue with previous version history if available]

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backwards compatible
- **Patch** (0.0.X): Bug fixes, backwards compatible
