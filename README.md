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
| [mobile-ui-testing](https://github.com/vladkarpman/mobile-ui-testing) | YAML-based mobile UI testing framework with mobile-mcp | 3.1.0 |

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

See [full documentation](https://github.com/vladkarpman/mobile-ui-testing) for details.

## Quick Start

```bash
# Add marketplace
claude plugin marketplace add vladkarpman/vladkarpman-plugins

# Install mobile-ui-testing
claude plugin install mobile-ui-testing

# Restart Claude Code to activate
```
