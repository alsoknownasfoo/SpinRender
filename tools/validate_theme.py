#!/usr/bin/env python3
"""
Theme Validator CLI - Validates theme YAML against code usage.

This tool scans Python source code to extract theme token references,
compares them against defined tokens in a YAML theme file, and can
automatically fix discrepancies.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to support running from tools/
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import theme validator modules
from tools.theme_validator import scanner, yaml_parser, comparator, fixer
from tools.theme_validator.yaml_parser import ThemeValidatorError


VERSION = "1.0.0"


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate theme YAML files against code usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Validate with defaults
  %(prog)s --yaml custom.yaml --src ui/      # Validate specific paths
  %(prog)s --add-missing --dry-run           # Preview missing token additions
  %(prog)s --baseline-mode                   # Generate baseline inventory
  %(prog)s --strict                          # Fail on any issue (CI mode)
        """
    )

    # Path arguments
    parser.add_argument(
        '-y', '--yaml',
        default='SpinRender/resources/themes/dark.yaml',
        help='Path to theme YAML file (default: SpinRender/resources/themes/dark.yaml)'
    )
    parser.add_argument(
        '-s', '--src',
        default='SpinRender/',
        help='Path to source code directory to scan (default: SpinRender/)'
    )
    parser.add_argument(
        '-b', '--baseline',
        default='tests/theme_token_inventory.json',
        help='Path to baseline JSON file (default: tests/theme_token_inventory.json)'
    )

    # Auto-fix flags
    fix_group = parser.add_argument_group('automated fixes')
    fix_group.add_argument(
        '--add-missing',
        action='store_true',
        help='Auto-add missing tokens to YAML (with placeholders)'
    )
    fix_group.add_argument(
        '--purge-unused',
        action='store_true',
        help='Remove unused tokens from YAML'
    )
    fix_group.add_argument(
        '--deprecate',
        action='store_true',
        help='Comment out unused tokens (alternative to purge)'
    )

    # Execution control
    exec_group = parser.add_argument_group('execution control')
    exec_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would change without modifying files'
    )
    exec_group.add_argument(
        '--no-backup',
        action='store_true',
        help='Disable .bak backup creation (use with caution)'
    )

    # Output formatting
    out_group = parser.add_argument_group('output formatting')
    out_group.add_argument(
        '-o', '--output',
        choices=['text', 'json', 'markdown'],
        default='text',
        help='Output format (default: text)'
    )

    # Exit code controls
    fail_group = parser.add_argument_group('exit code control (CI mode)')
    fail_group.add_argument(
        '--fail-on-missing',
        action='store_true',
        help='Exit with code 1 if missing tokens found'
    )
    fail_group.add_argument(
        '--fail-on-unused',
        action='store_true',
        help='Exit with code 2 if unused tokens found'
    )
    fail_group.add_argument(
        '--fail-on-deprecated',
        action='store_true',
        help='Exit with code 3 if deprecated tokens found'
    )
    fail_group.add_argument(
        '--strict',
        action='store_true',
        help='Equivalent to --fail-on-missing --fail-on-unused --fail-on-deprecated'
    )

    # Special modes
    parser.add_argument(
        '--baseline-mode',
        action='store_true',
        help='Generate/update baseline JSON (no validation)'
    )
    parser.add_argument(
        '--compare-baseline',
        action='store_true',
        help='Show changes since baseline (implies fail-on-* flags)'
    )

    # Verbosity
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Increase output verbosity (debug logging)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}'
    )

    return parser.parse_args()


def validate_paths(yaml_path: str, src_path: str, baseline_path: str):
    """Validate that required paths exist."""
    yaml_file = Path(yaml_path)
    src_dir = Path(src_path)
    baseline_file = Path(baseline_path)

    errors = []

    if not yaml_file.exists():
        errors.append(f"YAML file not found: {yaml_path}")
    if not src_dir.exists():
        errors.append(f"Source directory not found: {src_path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)


def generate_baseline(yaml_path: str, src_path: str, baseline_path: str, dry_run: bool = False):
    """Generate baseline JSON from current state."""
    print(f"Generating baseline...", file=sys.stderr)

    # Scan source code
    used = scanner.scan_directory(src_path)

    # Parse YAML
    defined = yaml_parser.parse_yaml(yaml_path)

    # Compare to get all sets
    result = comparator.compare_tokens(used, defined)

    # Build baseline data
    yaml_file = Path(yaml_path)
    yaml_bytes = yaml_file.read_bytes()
    baseline_data = {
        "theme_file": yaml_file.name,
        "yaml_hash": hashlib.sha256(yaml_bytes).hexdigest(),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "tokens": {
            "used": sorted(list(used['all'])),
            "defined": sorted(list(defined['all'])),
            "missing": sorted(list(result.missing)),
            "unused": sorted(list(result.unused))
        },
        "history": []
    }

    # Show what would be written
    if dry_run:
        print(f"[DRY RUN] Would write baseline to: {baseline_path}", file=sys.stderr)
        print(f"  Used tokens: {len(used['all'])}", file=sys.stderr)
        print(f"  Defined tokens: {len(defined['all'])}", file=sys.stderr)
        print(f"  Missing: {len(result.missing)}", file=sys.stderr)
        print(f"  Unused: {len(result.unused)}", file=sys.stderr)
        return

    # Write baseline
    baseline_file = Path(baseline_path)
    baseline_file.parent.mkdir(parents=True, exist_ok=True)

    if baseline_file.exists():
        print(f"Overwriting existing baseline: {baseline_path}", file=sys.stderr)
    else:
        print(f"Creating new baseline: {baseline_path}", file=sys.stderr)

    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f, indent=2)

    print(f"Baseline saved successfully.", file=sys.stderr)


def main():
    """Main entry point."""
    args = parse_args()

    # Check if fix operations are requested but PyYAML is unavailable
    if (args.add_missing or args.purge_unused or args.deprecate) and not yaml_parser._YAML_AVAILABLE:
        print("ERROR: Fix operations (--add-missing, --purge-unused, --deprecate) require PyYAML.", file=sys.stderr)
        print("       Install PyYAML: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    # Validate paths early
    validate_paths(args.yaml, args.src, args.baseline)

    # Handle baseline generation mode
    if args.baseline_mode:
        generate_baseline(args.yaml, args.src, args.baseline, args.dry_run)
        sys.exit(0)

    # Step 1: Scan source code
    if not args.quiet:
        print(f"Scanning source code: {args.src}", file=sys.stderr)
    used = scanner.scan_directory(args.src)

    # Step 2: Parse YAML
    if not args.quiet:
        print(f"Parsing theme file: {args.yaml}", file=sys.stderr)
    try:
        defined = yaml_parser.parse_yaml(args.yaml)
    except (ThemeValidatorError, ImportError) as e:
        # Error message already printed by yaml_parser or fixer; just exit
        sys.exit(1)

    # Step 3: Compare tokens
    baseline_path = args.baseline if not args.dry_run else None
    result = comparator.compare_tokens(used, defined, baseline_path=baseline_path)

    # Step 4: Apply fixes if requested
    if args.add_missing or args.purge_unused or args.deprecate:
        if not args.quiet:
            print("\nApplying fixes...", file=sys.stderr)
        fix_result = fixer.apply_fixes(
            yaml_path=args.yaml,
            result=result,
            add_missing=args.add_missing,
            purge_unused=args.purge_unused,
            deprecate=args.deprecate,
            dry_run=args.dry_run,
            backup=not args.no_backup
        )

        # Show fix summary
        # Always show errors
        if fix_result.get("errors"):
            print("\nFixer Errors:", file=sys.stderr)
            for error in fix_result["errors"]:
                print(f"  - {error}", file=sys.stderr)

        if not args.quiet:
            print("\nFix Summary:", file=sys.stderr)
            if fix_result['changes_made']:
                if fix_result['added']:
                    print(f"  Added: {len(fix_result['added'])} tokens", file=sys.stderr)
                if fix_result['removed']:
                    print(f"  Removed: {len(fix_result['removed'])} tokens", file=sys.stderr)
                if fix_result['deprecated']:
                    print(f"  Deprecated: {len(fix_result['deprecated'])} tokens", file=sys.stderr)
                if fix_result['array_updates']:
                    print(f"  Array updates: {fix_result['array_updates']} occurrences", file=sys.stderr)
                if fix_result['backup_path']:
                    print(f"  Backup: {fix_result['backup_path']}", file=sys.stderr)
            else:
                print("  No changes made.", file=sys.stderr)

        # If fixes were applied, re-validate to show updated state
        if fix_result['changes_made'] and not args.dry_run:
            if not args.quiet:
                print("\nRe-validating after fixes...", file=sys.stderr)
            # Re-parse updated YAML
            defined = yaml_parser.parse_yaml(args.yaml)
            result = comparator.compare_tokens(used, defined)

    # Step 5: Generate and display report (stdout)
    report = comparator.generate_report(result, output_format=args.output)
    print(report)

    # Step 6: Verbose output (stderr)
    if args.verbose:
        print("\n--- Verbose Info ---", file=sys.stderr)
        print(f"Used tokens: {len(used['all'])}", file=sys.stderr)
        print(f"Defined tokens: {len(defined['all'])}", file=sys.stderr)
        print(f"Missing: {len(result.missing)}", file=sys.stderr)
        print(f"Unused: {len(result.unused)}", file=sys.stderr)
        print(f"Deprecated: {len(result.deprecated)}", file=sys.stderr)
        if result.baseline:
            print(f"Baseline: {result.baseline.get('theme_file', 'N/A')}", file=sys.stderr)

    # Step 7: Determine exit code
    exit_code = comparator.get_exit_code(result, strict=args.strict)

    # Override with explicit flags
    if args.fail_on_missing and result.missing:
        exit_code = 1
    if args.fail_on_unused and result.unused:
        exit_code = 2
    if args.fail_on_deprecated and result.deprecated:
        exit_code = 3

    if not args.quiet and exit_code != 0:
        print(f"\nExiting with code {exit_code} due to validation issues.", file=sys.stderr)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
