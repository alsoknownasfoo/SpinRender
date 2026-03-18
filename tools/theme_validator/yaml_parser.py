#!/usr/bin/env python3
"""
Theme YAML Parser — Extract token paths from theme configuration.

Parses a theme YAML file and returns categorized sets of token paths.
"""
from pathlib import Path
from typing import Any, Dict, Set
import yaml


# Top-level categories we care about
CATEGORIES = ['palette', 'colors', 'typography', 'spacing', 'borders', 'components']


def collect_tokens(data: dict, prefix: str = '') -> Set[str]:
    """Recursively collect token paths from YAML data.

    Only leaf tokens (actual defined tokens) are collected; container
    namespaces (dicts that group tokens) are not considered tokens themselves.

    A dict is considered a leaf if all its keys are known attribute keys
    (e.g., 'ref', 'family', 'size', 'weight'). Otherwise it's a container.
    """
    tokens = set()

    if not isinstance(data, dict):
        return tokens

    # Keys that indicate a dict is a leaf value (not a container)
    LEAF_VALUE_KEYS = {'ref', 'family', 'size', 'weight', 'fallback', 'transform', 'value'}

    for key, value in data.items():
        current_path = f"{prefix}.{key}" if prefix else key

        # Determine if this key's value is a container dict
        is_container = False
        if isinstance(value, dict):
            if value:
                # If all keys are leaf-value keys, it's a leaf; otherwise container
                all_leaf = all(k in LEAF_VALUE_KEYS for k in value.keys())
                is_container = not all_leaf
            else:
                # Empty dict, treat as container (unlikely)
                is_container = False
        # Non-dict values are leaves; containers are only dicts with non-leaf keys

        if not is_container:
            tokens.add(current_path)

        if is_container:
            tokens.update(collect_tokens(value, current_path))

    return tokens


def categorize_tokens(all_tokens: Set[str]) -> Dict[str, Set[str]]:
    """Categorize tokens by top-level section.

    Args:
        all_tokens: Set of all token paths

    Returns:
        Dict with keys for each category and 'all'
    """
    result = {cat: set() for cat in CATEGORIES}
    result['all'] = all_tokens.copy()

    for token in all_tokens:
        # Top-level category is first segment before dot
        top_level = token.split('.')[0]
        if top_level in result:
            result[top_level].add(token)

    return result


def parse_yaml(yaml_path: str) -> dict:
    """Parse theme YAML and return categorized token sets.

    Args:
        yaml_path: Path to the YAML theme file

    Returns:
        Dictionary with categorized token sets:
        {
            'palette': set([...]),
            'colors': set([...]),
            'typography': set([...]),
            'spacing': set([...]),
            'borders': set([...]),
            'components': set([...]),
            'all': set([...])
        }

    Raises:
        FileNotFoundError: If YAML file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    path = Path(yaml_path)

    if not path.exists():
        raise FileNotFoundError(f"Theme YAML not found: {yaml_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if data is None:
        # Empty YAML file
        return {cat: set() for cat in CATEGORIES + ['all']}

    # Ensure data is a dict
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a dictionary, got {type(data).__name__}")

    # Collect all tokens recursively
    all_tokens = collect_tokens(data)

    # Categorize by top-level section
    categorized = categorize_tokens(all_tokens)

    return categorized


# Enable command-line testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = parse_yaml(sys.argv[1])
        print("Token counts per category:")
        for category in CATEGORIES + ['all']:
            print(f"  {category}: {len(result[category])}")
    else:
        print("Usage: python yaml_parser.py <path-to-theme.yaml>")
