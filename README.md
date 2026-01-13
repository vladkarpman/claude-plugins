# Vladkarpman Plugins

Claude Code plugins by Vladislav Karpman.

## Installation

```bash
# Add this marketplace (one time)
claude plugin marketplace add vladkarpman/vladkarpman-plugins

# Install any plugin
claude plugin install <plugin-name>
```

## Available Plugins

| Plugin | Description | Version |
|--------|-------------|---------|
| [mobile-ui-testing](#mobile-ui-testing) | YAML-based mobile UI testing framework with mobile-mcp | 3.3.1 |
| [compose-designer](#compose-designer) | Transform design mockups into production-ready Jetpack Compose code | 0.2.0 |

## Plugins

### mobile-ui-testing

YAML-based mobile UI testing framework for Claude Code using [mobile-mcp](https://github.com/anthropics/mobile-mcp).

**Features:**
- Declarative YAML test syntax - no programming required
- Record tests by interacting with your device
- Auto-approved mobile-mcp tools - no manual confirmations
- Cross-device percentage-based coordinates
- AI-powered screen verification

**Commands:**
- `/run-test <file>` - Execute a YAML test
- `/create-test <name>` - Create test from template
- `/generate-test <description>` - Generate test from natural language
- `/record-test <name>` - Record user actions
- `/stop-recording` - Stop and generate YAML

**Quick Start:**
```bash
claude plugin install mobile-ui-testing

# Then in Claude Code:
/create-test login
/run-test tests/login/test.yaml
```

See [full documentation](./plugins/mobile-ui-testing) for details.

### compose-designer

Transform design mockups (screenshots, Figma designs) into production-ready Jetpack Compose code through automated three-phase workflow with visual validation and device testing.

**Features:**
- Multi-input support (screenshots, Figma, clipboard, batch processing)
- Ralph-wiggum visual validation loop (92%+ similarity)
- Mobile-mcp device testing integration
- Theme extraction from existing code
- Production-ready idiomatic Compose code

**Commands:**
- `/compose-design config` - Interactive configuration wizard
- `/compose-design create` - Generate Compose code from design

**Quick Start:**
```bash
claude plugin install compose-designer

# Then in Claude Code:
/compose-design config
/compose-design create --input design.png --name MyComponent --type component
```

See [full documentation](./plugins/compose-designer-plugin) for details.

## Quick Start

```bash
# Add marketplace
claude plugin marketplace add vladkarpman/vladkarpman-plugins

# Install any plugin
claude plugin install mobile-ui-testing
claude plugin install compose-designer

# Restart Claude Code to activate
```
