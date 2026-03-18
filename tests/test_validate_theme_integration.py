#!/usr/bin/env python3
"""
Test script for theme_validator.comparator

This demonstrates the comparator using real data from the codebase.
"""
import sys
sys.path.insert(0, '/Users/foo/Code/SpinRender_claude/tools/theme_validator')
sys.path.insert(0, '/Users/foo/Code/SpinRender_claude')

from scanner import scan_directory
from yaml_parser import parse_yaml
from comparator import compare_tokens, generate_report, get_exit_code

def main():
    print("=" * 70)
    print("THEME VALIDATOR COMPARATOR TEST")
    print("=" * 70)
    print()

    # 1. Scan the codebase for used tokens
    print("1. Scanning codebase for theme token usage...")
    root = '/Users/foo/Code/SpinRender_claude'
    used = scan_directory(root)
    print(f"   Found {len(used['all'])} used tokens")
    print()

    # 2. Parse the YAML theme file
    print("2. Parsing YAML theme definition...")
    yaml_path = '/Users/foo/Code/SpinRender_claude/SpinRender/resources/themes/dark.yaml'
    defined = parse_yaml(yaml_path)
    print(f"   Found {len(defined['all'])} defined tokens")
    print()

    # 3. Compare tokens
    print("3. Comparing used vs defined tokens...")
    result = compare_tokens(used, defined)
    print(f"   Coverage: {result.coverage:.1f}%")
    print(f"   Missing: {len(result.missing)}")
    print(f"   Unused: {len(result.unused)}")
    print()

    # 4. Generate report in different formats
    print("4. Generating TEXT report:")
    print("-" * 70)
    print(generate_report(result, output_format='text'))
    print()

    print("5. Generating JSON report sample (first 2000 chars):")
    print("-" * 70)
    json_report = generate_report(result, output_format='json')
    print(json_report[:2000] + ("..." if len(json_report) > 2000 else ""))
    print()

    print("6. Generating MARKDOWN report sample (first 1500 chars):")
    print("-" * 70)
    md_report = generate_report(result, output_format='markdown')
    print(md_report[:1500] + ("..." if len(md_report) > 1500 else ""))
    print()

    # 5. Exit code
    exit_code = get_exit_code(result)
    print(f"7. Exit code: {exit_code}")
    print()

    # 6. Show actual missing tokens
    print("8. MISSING TOKENS (need to be added to YAML):")
    for token in sorted(result.missing):
        print(f"   - {token}")
    print()

    print("9. UNUSED TOKENS (defined but not referenced):")
    for token in sorted(result.unused)[:30]:
        print(f"   - {token}")
    if len(result.unused) > 30:
        print(f"   ... and {len(result.unused) - 30} more")
    print()

    return exit_code

if __name__ == '__main__':
    sys.exit(main())
