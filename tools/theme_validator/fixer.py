#!/usr/bin/env python3
"""
Theme Validator Fixer — Apply automated fixes to YAML theme files.

Provides functions to add missing tokens, purge unused tokens, or deprecate them
based on validation results from the comparator.
"""
from pathlib import Path
from typing import Dict, Set, Any, Optional, List
import shutil
import yaml
import datetime
import sys

# Try to use ruamel.yaml for better YAML preservation
try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap
    RUAMEL_AVAILABLE = True
except ImportError:
    RUAMEL_AVAILABLE = False


# ============================================================================
# Placeholder generation based on token type
# ============================================================================

def _generate_placeholder(token: str) -> Any:
    """Generate a sensible placeholder value for a missing token.

    Args:
        token: Token path (e.g., 'colors.bg.modal', 'typography.scale.xs')

    Returns:
        Placeholder value appropriate for the token type
    """
    parts = token.split('.')

    if len(parts) < 2:
        return "# TODO: define"

    category = parts[0]
    subpath = parts[1:]

    # Color-related tokens
    if category == 'colors':
        if subpath[0] == 'bg':
            return {'ref': 'palette.neutral-3'}
        elif subpath[0] == 'text':
            return {'ref': 'palette.neutral-14'}
        elif subpath[0] == 'accent':
            return {'ref': 'palette.cyan'}
        elif subpath[0] == 'border':
            return {'ref': 'palette.neutral-7'}
        elif subpath[0] == 'state':
            if 'hover' in subpath[1:]:
                return {'ref': 'palette.overlay-light'}
            elif 'pressed' in subpath[1:]:
                return {'ref': 'palette.overlay-medium'}
            else:
                return {'ref': 'palette.green'}
        elif subpath[0] == 'preset':
            # Preset arrays: return a list with one placeholder
            return [{'ref': 'palette.preset-red'}]
        else:
            return {'ref': 'palette.neutral-3'}

    elif category == 'palette':
        # New raw color - suggest a hex placeholder
        return "#XXXXXX"

    elif category == 'typography':
        if subpath[0] == 'scale':
            return 11
        elif subpath[0] == 'weights':
            return 400
        elif subpath[0] == 'families':
            return "mono"
        elif subpath[0] == 'presets':
            # Return a preset template
            return {
                'family': {'ref': 'typography.families.mono'},
                'size': {'ref': 'typography.scale.base'},
                'weight': {'ref': 'typography.weights.normal'}
            }
        else:
            return "# TODO: define"

    elif category == 'spacing':
        return 10

    elif category == 'borders':
        if subpath[0] == 'radius':
            return 4
        else:
            return 1

    elif category == 'components':
        # Component tokens vary widely; return a basic structure
        # For color array properties: ["colors.bg.input"]
        if 'color' in token or 'bg' in subpath or 'text' in subpath or 'border' in subpath:
            return ["colors.bg.input"]
        elif 'font' in token or 'family' in subpath:
            return {'ref': 'typography.presets.body'}
        elif 'radius' in token:
            return {'ref': 'borders.radius.md'}
        else:
            return 0

    else:
        return "# TODO: define"


# ============================================================================
# YAML path navigation and manipulation
# ============================================================================

def _get_nested_value(data: Dict, path_parts: List[str]) -> Any:
    """Navigate nested dict by path parts and return the value."""
    current = data
    for part in path_parts:
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"Path {'->'.join(path_parts)} not found")
        current = current[part]
    return current


def _set_nested_value(data: Dict, path_parts: List[str], value: Any) -> None:
    """Set a value in nested dict by path parts."""
    current = data
    for part in path_parts[:-1]:
        if part not in current:
            if RUAMEL_AVAILABLE and isinstance(current, CommentedMap):
                current[part] = CommentedMap()
            else:
                current[part] = {}
        current = current[part]
    current[path_parts[-1]] = value

def _delete_nested_value(data: Dict, path_parts: List[str]) -> bool:
    """Delete a value from nested dict. Returns True if deleted."""
    try:
        parent = _get_nested_value(data, path_parts[:-1])
        if path_parts[-1] in parent:
            del parent[path_parts[-1]]
            return True
    except KeyError:
        return False
    return False


# ============================================================================
# Component array updates (when tokens are removed from palette/colors)
# ============================================================================

def _find_references_to_token(components_data: Dict, token: str) -> List[List[str]]:
    """Find all paths in components that reference a given token.

    Args:
        components_data: components section dict
        token: Token to search for (e.g., 'palette.neutral-4')

    Returns:
        List of paths (as list of parts) where token appears in arrays
    """
    references = []

    def search_in_data(data: Any, path: List[str]) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                search_in_data(value, path + [key])
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                search_in_data(item, path + [str(idx)])
        elif isinstance(data, str):
            # Check if this string references the token
            if data == token or data.startswith(token + '.'):
                # Record the parent path (the list itself)
                if len(path) >= 2:
                    references.append(path[:-1])

    search_in_data(components_data, [])
    return references


def _remove_token_from_arrays(components_data: Dict, token: str) -> int:
    """Remove token from all component color/font arrays.

    Returns:
        Number of items removed across all arrays
    """
    removed_count = 0

    def process_list(lst: List) -> int:
        removed = 0
        i = 0
        while i < len(lst):
            item = lst[i]
            if isinstance(item, str):
                if item == token:
                    del lst[i]
                    removed += 1
                    continue  # Don't increment i, we removed current
            i += 1
        return removed

    def search_and_remove(data: Any) -> int:
        removed = 0
        if isinstance(data, dict):
            for value in data.values():
                removed += search_and_remove(value)
        elif isinstance(data, list):
            removed += process_list(data)
            # Also recurse into list items (in case nested lists/dicts)
            for item in data:
                removed += search_and_remove(item)
        return removed

    removed_count = search_and_remove(components_data)
    return removed_count


# ============================================================================
# Backup and I/O
# ============================================================================

def _create_backup(yaml_path: str) -> str:
    """Create a backup of the YAML file.

    Args:
        yaml_path: Path to original file

    Returns:
        Backup file path
    """
    backup_path = f"{yaml_path}.bak"
    shutil.copy2(yaml_path, backup_path)
    return backup_path


def _load_yaml_ruamel(yaml_path: str):
    """Load YAML using ruamel.yaml preserving structure and comments."""
    yaml_ruamel = YAML()
    yaml_ruamel.preserve_quotes = True
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml_ruamel.load(f)


def _write_yaml_ruamel(data: Any, yaml_path: str) -> None:
    """Write YAML using ruamel.yaml preserving formatting."""
    yaml_ruamel = YAML()
    yaml_ruamel.indent(mapping=2, sequence=4, offset=2)
    yaml_ruamel.width = 4096  # Prevent line wrapping
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml_ruamel.dump(data, f)


def _load_yaml_safe(yaml_path: str) -> Dict:
    """Load YAML using safe_load."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _validate_yaml(yaml_path: str) -> bool:
    """Validate that YAML file is parseable."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError:
        return False


# ============================================================================
# Fix operations
# ============================================================================

def _add_missing_token(yaml_data: Any, token: str, dry_run: bool = False) -> Dict:
    """Add a missing token to the YAML data structure.

    Args:
        yaml_data: Loaded YAML data (ruamel CommentedMap or regular dict)
        token: Token path to add
        dry_run: If True, don't modify, just return what would be done

    Returns:
        Dict with 'added' (bool), 'path' (where added), 'value' (what was set)
    """
    parts = token.split('.')
    if len(parts) < 2:
        return {'added': False, 'path': None, 'value': None}

    # Check if token already exists (shouldn't happen but be safe)
    try:
        existing = _get_nested_value(yaml_data, parts)
        return {'added': False, 'path': token, 'value': existing, 'reason': 'already exists'}
    except KeyError:
        pass

    # Generate placeholder
    placeholder = _generate_placeholder(token)

    # Insert into structure
    if not dry_run:
        _set_nested_value(yaml_data, parts, placeholder)
        # Add AUTO-ADDED comment if using ruamel.yaml
        if RUAMEL_AVAILABLE:
            try:
                parent = yaml_data
                for part in parts[:-1]:
                    parent = parent[part]
                if isinstance(parent, CommentedMap):
                    parent.yaml_add_comment_before_after_key(key=parts[-1], before='# AUTO-ADDED: verify this value')
            except Exception:
                pass  # comment may not be supported

    return {
        'added': True,
        'path': token,
        'value': placeholder,
        'section': parts[0]
    }

def _purge_unused_tokens(yaml_data: Any, unused_set: Set[str], dry_run: bool = False) -> Dict:
    """Remove unused tokens from YAML data.

    Also updates component arrays to remove references to removed palette/colors tokens.

    Args:
        yaml_data: Loaded YAML data
        unused_set: Set of token paths to remove
        dry_run: If True, don't modify

    Returns:
        Dict with 'removed' (list of paths), 'array_updates' (count)
    """
    removed = []
    array_updates = 0

    # Track tokens we remove from palette/colors so we can update components
    removed_palette_colors = set()

    # Sort tokens by depth (deepest first) to avoid parent deletion issues
    sorted_tokens = sorted(unused_set, key=lambda t: len(t.split('.')), reverse=True)

    for token in sorted_tokens:
        parts = token.split('.')
        try:
            # Check if token actually exists (might have been manually removed)
            _get_nested_value(yaml_data, parts)

            # Track palette/colors tokens for array cleanup
            if parts[0] in ('palette', 'colors'):
                removed_palette_colors.add(token)

            if not dry_run:
                deleted = _delete_nested_value(yaml_data, parts)
                if deleted:
                    removed.append(token)
            else:
                removed.append(token)

        except KeyError:
            # Token doesn't exist in current YAML, skip
            continue

    # Update component arrays if any palette/colors tokens were removed
    if not dry_run and removed_palette_colors:
        if 'components' in yaml_data and isinstance(yaml_data['components'], dict):
            for token in removed_palette_colors:
                array_updates += _remove_token_from_arrays(yaml_data['components'], token)

    return {
        'removed': removed,
        'array_updates': array_updates,
        'removed_palette_colors': list(removed_palette_colors)
    }


def _deprecate_unused_tokens(yaml_path: str, unused_set: Set[str],
                             dry_run: bool = False) -> Dict:
    """Comment out unused tokens in YAML file (text-based approach).

    Uses full path matching to avoid incorrectly commenting similar keys.

    Args:
        yaml_path: Path to YAML file (for reading lines)
        unused_set: Set of token paths to deprecate
        dry_run: If True, don't write

    Returns:
        Dict with 'deprecated' (list), 'lines_written'
    """
    import datetime

    # Read file as lines
    with open(yaml_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    deprecated = []
    new_lines = []
    date_str = datetime.date.today().isoformat()

    # Build mapping: full token path -> (line index, indent, parent path)
    token_meta = {}
    indent_stack = [(-1, [])]  # (indent, path_components)

    for line_num, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if ':' in stripped:
            indent = len(line) - len(line.lstrip())
            key = stripped.split(':', 1)[0].strip()
            # Update path stack based on indentation
            while indent <= indent_stack[-1][0]:
                indent_stack.pop()
            parent_path = indent_stack[-1][1]
            full_path = '.'.join(parent_path + [key])
            token_meta[full_path] = (line_num, indent, parent_path.copy())
            indent_stack.append((indent, parent_path + [key]))

    # Determine which lines are part of each token's block (its line + indent descendants)
    tokens_with_blocks = {}
    for token in unused_set:
        if token not in token_meta:
            continue
        start_line, base_indent, parent = token_meta[token]
        block = {start_line}
        # Include subsequent lines that are indented more than this token
        for i in range(start_line + 1, len(lines)):
            l = lines[i]
            s = l.strip()
            if not s or s.startswith('#'):
                block.add(i)
                continue
            indent_i = len(l) - len(l.lstrip())
            if indent_i <= base_indent:
                break
            block.add(i)
        tokens_with_blocks[token] = block

    # Combine all lines that belong to any deprecated block
    all_deprecated_lines = set()
    for block in tokens_with_blocks.values():
        all_deprecated_lines.update(block)

    # Generate output
    for line_num, line in enumerate(lines):
        stripped = line.strip()
        if line_num in all_deprecated_lines:
            # Find the root token line to prefix with DEPRECATED marker
            is_root = any(
                line_num in tokens_with_blocks.get(t, set()) and token_meta[t][0] == line_num
                for t in tokens_with_blocks
            )
            if is_root:
                token = next(t for t in tokens_with_blocks if token_meta[t][0] == line_num)
                new_lines.append(f"# DEPRECATED: unused since {date_str} - {stripped}\n")
                deprecated.append(token)
            else:
                if stripped and not stripped.startswith('#'):
                    new_lines.append(f"# {line}")
                else:
                    new_lines.append(line)
        else:
            new_lines.append(line)

    if not dry_run:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return {
        'deprecated': deprecated,
        'lines_written': len(new_lines)
    }


def apply_fixes(
    yaml_path: str,
    result,
    add_missing: bool = False,
    purge_unused: bool = False,
    deprecate: bool = False,
    dry_run: bool = True,
    backup: bool = True
) -> Dict:
    """Apply automated fixes to a YAML theme file.

    Args:
        yaml_path: Path to the YAML file to modify
        result: ValidationResult from comparator with missing/unused sets
        add_missing: If True, add tokens from result.missing
        purge_unused: If True, remove tokens from result.unused
        deprecate: If True, comment out tokens from result.unused (alternative to purge)
        dry_run: If True, show what would change but don't write
        backup: If True (and not dry_run), create .bak backup before modifying

    Returns:
        Dict with summary:
        {
            'changes_made': bool,
            'dry_run': bool,
            'backup_path': str or None,
            'errors': List[str],
            'added': List[Dict],
            'removed': List[str],
            'deprecated': List[str],
            'array_updates': int,
            'output_valid': bool
        }
    """
    summary = {
        'changes_made': False,
        'dry_run': dry_run,
        'backup_path': None,
        'errors': [],
        'added': [],
        'removed': [],
        'deprecated': [],
        'array_updates': 0,
        'output_valid': False
    }

    # Validate inputs
    if not Path(yaml_path).exists():
        summary['errors'].append(f"YAML file not found: {yaml_path}")
        return summary

    # Only one of purge_unused or deprecate should be active
    if purge_unused and deprecate:
        summary['errors'].append("Cannot specify both purge_unused and deprecate")
        return summary

    # If no action specified, return early
    if not (add_missing or purge_unused or deprecate):
        summary['errors'].append("No fix action specified (add_missing, purge_unused, or deprecate required)")
        return summary

    # Load YAML data
    try:
        if RUAMEL_AVAILABLE:
            yaml_data = _load_yaml_ruamel(yaml_path)
        else:
            yaml_data = _load_yaml_safe(yaml_path)
    except Exception as e:
        summary['errors'].append(f"Failed to load YAML: {e}")
        return summary

    if yaml_data is None:
        yaml_data = {}

    # Perform backup before any changes
    if not dry_run and backup:
        try:
            backup_path = _create_backup(yaml_path)
            summary['backup_path'] = backup_path
        except Exception as e:
            summary['errors'].append(f"Failed to create backup: {e}")
            return summary

    # --- ADD MISSING TOKENS ---
    if add_missing and result.missing:
        for token in sorted(result.missing):
            try:
                result_dict = _add_missing_token(yaml_data, token, dry_run)
                if result_dict['added']:
                    summary['added'].append(result_dict)
            except Exception as e:
                summary['errors'].append(f"Failed to add {token}: {e}")

    # --- PURGE UNUSED TOKENS ---
    if purge_unused and result.unused:
        try:
            purge_result = _purge_unused_tokens(yaml_data, result.unused, dry_run)
            summary['removed'] = purge_result['removed']
            summary['array_updates'] = purge_result['array_updates']
        except Exception as e:
            summary['errors'].append(f"Failed to purge unused tokens: {e}")

    # --- DEPRECATE UNUSED TOKENS ---
    if deprecate and result.unused:
        try:
            deprecate_result = _deprecate_unused_tokens(yaml_path, result.unused, dry_run)
            summary['deprecated'] = deprecate_result['deprecated']
        except Exception as e:
            summary['errors'].append(f"Failed to deprecate tokens: {e}")

    # Write changes if not dry_run
    if not dry_run and (summary['added'] or summary['removed']):
        try:
            if RUAMEL_AVAILABLE:
                _write_yaml_ruamel(yaml_data, yaml_path)
            else:
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

            summary['changes_made'] = True
        except Exception as e:
            summary['errors'].append(f"Failed to write YAML: {e}")
            return summary

        # Validate output
        if _validate_yaml(yaml_path):
            summary['output_valid'] = True
        else:
            summary['errors'].append("Output YAML failed validation (syntax error)")

    return summary


# ============================================================================
# Command-line interface
# ============================================================================

if __name__ == "__main__":
    import argparse
    from comparator import compare_tokens, parse_yaml as parse_yaml_original
    from scanner import scan_directory

    parser = argparse.ArgumentParser(description="Apply automated fixes to theme YAML files")
    parser.add_argument('yaml_file', help='Path to theme YAML file')
    parser.add_argument('--add-missing', action='store_true', help='Add missing tokens')
    parser.add_argument('--purge-unused', action='store_true', help='Remove unused tokens')
    parser.add_argument('--deprecate', action='store_true', help='Comment out unused tokens')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Show changes without writing')
    parser.add_argument('--no-dry-run', action='store_false', dest='dry_run', help='Actually write changes')
    parser.add_argument('--no-backup', action='store_false', dest='backup', help='Skip backup creation')
    parser.add_argument('--code-dir', help='Directory to scan for token usage')
    args = parser.parse_args()

    # Build ValidationResult
    defined = parse_yaml_original(args.yaml_file)
    used = {'all': set()}
    if args.code_dir:
        try:
            used = scan_directory(args.code_dir)
        except Exception as e:
            print(f"Warning: Could not scan code directory: {e}")

    result = compare_tokens(used, defined)

    print(f"Validation summary: {len(result.missing)} missing, {len(result.unused)} unused")
    print(f"Dry run: {args.dry_run}")
    print()

    summary = apply_fixes(
        args.yaml_file,
        result,
        add_missing=args.add_missing,
        purge_unused=args.purge_unused,
        deprecate=args.deprecate,
        dry_run=args.dry_run,
        backup=args.backup
    )

    # Print summary
    if summary['errors']:
        print("ERRORS:")
        for err in summary['errors']:
            print(f"  - {err}")
        print()

    if summary['added']:
        print(f"Would add {len(summary['added'])} missing tokens:")
        for item in summary['added'][:20]:
            print(f"  - {item['path']} -> {item['value']}")
        if len(summary['added']) > 20:
            print(f"  ... and {len(summary['added']) - 20} more")
        print()

    if summary['removed']:
        print(f"Would remove {len(summary['removed'])} unused tokens:")
        for token in summary['removed'][:20]:
            print(f"  - {token}")
        if len(summary['removed']) > 20:
            print(f"  ... and {len(summary['removed']) - 20} more")
        if summary['array_updates']:
            print(f"  (updated {summary['array_updates']} component array references)")
        print()

    if summary['deprecated']:
        print(f"Would deprecate {len(summary['deprecated'])} tokens")
        print()

    if summary['changes_made']:
        print("Changes applied successfully!")
        if summary['backup_path']:
            print(f"Backup saved: {summary['backup_path']}")
        if summary['output_valid']:
            print("Output YAML is valid.")
    elif args.dry_run:
        print("Dry run complete. No files modified.")
