#!/usr/bin/env python3
"""
Load plugin configuration with priority: test > project > defaults.

Usage:
    python3 load-config.py [--project-config PATH] [--test-config PATH]

Outputs merged config as JSON.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


DEFAULTS = {
    "model": "opus",
    "generate_reports": True
}


def load_yaml_file(path: Path) -> Dict[str, Any]:
    """Load YAML file, return empty dict if not found."""
    if not path.exists():
        return {}

    if not HAS_YAML:
        print(f"Warning: PyYAML not installed, skipping {path}", file=sys.stderr)
        return {}

    with open(path) as f:
        data = yaml.safe_load(f)
        return data if data else {}


def load_project_config(project_config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load project-level config from .claude/mobile-ui-testing.yaml"""
    if project_config_path:
        return load_yaml_file(project_config_path)

    # Default location
    default_path = Path(".claude/mobile-ui-testing.yaml")
    return load_yaml_file(default_path)


def extract_test_config(test_yaml: Dict[str, Any]) -> Dict[str, Any]:
    """Extract config section from test YAML."""
    config = test_yaml.get("config", {})
    # Only return keys that are configuration, not test-specific like 'app'
    config_keys = [
        "model",
        "generate_reports"
    ]
    return {k: v for k, v in config.items() if k in config_keys}


def merge_configs(
    defaults: Dict[str, Any],
    project: Dict[str, Any],
    test: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge configs with priority: test > project > defaults."""
    result = defaults.copy()
    result.update(project)
    result.update(test)
    return result


def main():
    parser = argparse.ArgumentParser(description="Load merged configuration")
    parser.add_argument("--project-config", help="Project config path")
    parser.add_argument("--test-config", help="Test YAML path (extracts config section)")
    args = parser.parse_args()

    # Load project config
    project_path = Path(args.project_config) if args.project_config else None
    project_config = load_project_config(project_path)

    # Load test config
    test_config = {}
    if args.test_config:
        test_path = Path(args.test_config)
        if test_path.exists():
            test_yaml = load_yaml_file(test_path)
            test_config = extract_test_config(test_yaml)

    # Merge
    merged = merge_configs(DEFAULTS, project_config, test_config)

    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
