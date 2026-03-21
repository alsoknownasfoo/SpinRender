#!/usr/bin/env python3
"""
Theme Token Comparator — Compare used tokens against defined tokens.

Compares tokens extracted from code (scanner) with tokens defined in YAML (parser)
to identify missing, unused, and deprecated tokens.
"""
from dataclasses import dataclass, field
from typing import Dict, Set, Optional
import json


@dataclass
class ValidationResult:
    """Result of theme token validation."""
    used: Set[str]
    defined: Set[str]
    missing: Set[str]
    unused: Set[str]
    coverage: float
    baseline: Optional[dict] = None
    newly_missing: Set[str] = field(default_factory=set)
    newly_unused: Set[str] = field(default_factory=set)
    deprecated: Set[str] = field(default_factory=set)
    used_diff: Set[str] = field(default_factory=set)  # new tokens in code
    removed_usage: Set[str] = field(default_factory=set)  # removed from code


def _categorize_by_prefix(tokens: Set[str]) -> Dict[str, Set[str]]:
    """Categorize tokens by top-level prefix (colors, typography, etc.)."""
    categories: Dict[str, Set[str]] = {}

    for token in tokens:
        parts = token.split('.', 1)
        if len(parts) == 1:
            category = 'other'
        else:
            category = parts[0]

        if category not in categories:
            categories[category] = set()
        categories[category].add(token)

    return categories


def _load_baseline(baseline_path: str) -> Optional[dict]:
    """Load baseline JSON file."""
    try:
        with open(baseline_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load baseline: {e}")
        return None


def compare_tokens(
    used: dict,
    defined: dict,
    baseline_path: Optional[str] = None
) -> ValidationResult:
    """Compare used tokens against defined tokens.

    Args:
        used: Dict from scanner with keys: 'colors', 'sizes', 'fonts', 'components', 'all'
        defined: Dict from yaml_parser with keys: 'palette', 'colors', 'typography',
                'spacing', 'borders', 'components', 'all'
        baseline_path: Optional path to baseline JSON for change tracking

    Returns:
        ValidationResult with comprehensive comparison data
    """
    used_all: Set[str] = set(used.get('all', set()))
    defined_all: Set[str] = set(defined.get('all', set()))

    missing = used_all - defined_all
    unused = defined_all - used_all
    intersection = used_all & defined_all
    coverage = (len(intersection) / max(1, len(used_all))) * 100

    baseline_data = None
    if baseline_path:
        baseline_data = _load_baseline(baseline_path)

    newly_missing: Set[str] = set()
    newly_unused: Set[str] = set()
    deprecated: Set[str] = set()
    used_diff: Set[str] = set()
    removed_usage: Set[str] = set()

    if baseline_data:
        try:
            baseline_tokens = baseline_data.get('tokens', {})
            baseline_used: Set[str] = set(baseline_tokens.get('used', []))
            baseline_missing: Set[str] = set(baseline_tokens.get('missing', []))
            baseline_unused: Set[str] = set(baseline_tokens.get('unused', []))

            newly_missing = missing - baseline_missing
            newly_unused = unused & baseline_used
            deprecated = baseline_used & unused
            used_diff = used_all - baseline_used
            removed_usage = baseline_used - used_all

        except (KeyError, TypeError) as e:
            print(f"Warning: Invalid baseline format: {e}")

    result = ValidationResult(
        used=used_all,
        defined=defined_all,
        missing=missing,
        unused=unused,
        coverage=coverage,
        baseline=baseline_data,
        newly_missing=newly_missing,
        newly_unused=newly_unused,
        deprecated=deprecated,
        used_diff=used_diff,
        removed_usage=removed_usage
    )

    return result


def _get_suggestion(token: str) -> str:
    """Generate a helpful suggestion for fixing a missing token."""
    parts = token.split('.')

    if len(parts) < 2:
        return "Unknown token format"

    category = parts[0]
    subpath = '.'.join(parts[1:])

    suggestions = {
        'colors': f"ADD: Define in {category} section with semantic color value",
        'text': f"ADD: Define in text section (e.g. text.{subpath}.font)",
        'glyphs': f"ADD: Define glyph in glyphs section: {subpath}: \"\\UXXXXXXXX\"",
        'spacing': f"ADD: Define spacing.{subpath} as pixel value",
        'borders': f"ADD: Define borders.{subpath} as pixel value",
        'components': f"ADD: Define component token in components.{subpath}",
        'palette': f"ADD: Define raw color in palette section: {subpath}: '#XXXXXX'",
    }

    base_sugg = suggestions.get(category, f"ADD: Define token in YAML under {category}")

    if token.startswith('text.'):
        return f"ADD: Define in text section (font + color): {token}"
    elif token.startswith('glyphs.'):
        return f"ADD: Define Unicode glyph in glyphs section: {subpath}"
    elif token.startswith('palette.'):
        color_name = parts[1] if len(parts) > 1 else ''
        return f"ADD: Define raw hex color in palette: {color_name}: '#RRGGBB'"

    return base_sugg


def generate_report(result: ValidationResult, output_format: str = 'text') -> str:
    """Generate a formatted validation report.

    Args:
        result: ValidationResult from compare_tokens
        output_format: 'text', 'json', or 'markdown'

    Returns:
        Formatted report string

    Raises:
        ValueError: If output_format is not supported
    """
    if output_format == 'json':
        return _generate_json_report(result)
    elif output_format == 'markdown':
        return _generate_markdown_report(result)
    elif output_format == 'text':
        return _generate_text_report(result)
    else:
        raise ValueError(f"Unsupported format: {output_format}")


def _generate_text_report(result: ValidationResult) -> str:
    """Generate human-readable text report."""
    lines = []
    lines.append("Theme Validation Report")
    lines.append("=" * 60)
    lines.append("")

    defined_count = len(result.defined)
    used_count = len(result.used)
    intersection = len(result.used & result.defined)

    lines.append("📊 Summary")
    lines.append(f"  Coverage: {result.coverage:.1f}% ({intersection}/{used_count} used tokens defined)")
    lines.append(f"  Used tokens: {used_count}")
    lines.append(f"  Defined tokens: {defined_count}")
    lines.append(f"  ❌ Missing: {len(result.missing)}")
    lines.append(f"  ⚠️  Unused: {len(result.unused)}")

    if result.deprecated:
        lines.append(f"  🏴‍☠️  Deprecated: {len(result.deprecated)} (were used, now unused)")

    if result.baseline:
        lines.append("")
        lines.append("📈 Changes Since Baseline")
        lines.append(f"  Newly missing: {len(result.newly_missing)}")
        lines.append(f"  Newly unused: {len(result.newly_unused)}")
        lines.append(f"  Newly added to code: {len(result.used_diff)}")
        lines.append(f"  Removed from code: {len(result.removed_usage)}")

    if result.missing:
        lines.append("")
        lines.append(f"❌ Missing Tokens ({len(result.missing)})")
        missing_by_cat = _categorize_by_prefix(result.missing)
        for category in sorted(missing_by_cat.keys()):
            tokens = sorted(missing_by_cat[category])
            for token in tokens[:20]:
                lines.append(f"  {token}")
                suggestion = _get_suggestion(token)
                if suggestion:
                    lines.append(f"    → {suggestion}")
            if len(tokens) > 20:
                lines.append(f"  ... and {len(tokens) - 20} more")

    if result.unused:
        lines.append("")
        lines.append(f"⚠️  Unused Definitions ({len(result.unused)})")
        unused_by_cat = _categorize_by_prefix(result.unused)
        total_shown = 0
        MAX_UNUSED_SHOW = 50

        for category in sorted(unused_by_cat.keys()):
            tokens = sorted(unused_by_cat[category])
            for token in tokens[:10]:
                if total_shown < MAX_UNUSED_SHOW:
                    lines.append(f"  {token}")
                    total_shown += 1
                else:
                    break
            if total_shown >= MAX_UNUSED_SHOW and len(unused_by_cat) > 1:
                remaining = len(result.unused) - total_shown
                lines.append(f"  ... and {remaining} more (truncated)")
                break

    if result.deprecated:
        lines.append("")
        lines.append(f"🏴‍☠️  Deprecated Tokens ({len(result.deprecated)})")
        for token in sorted(result.deprecated)[:20]:
            lines.append(f"  {token}")
        if len(result.deprecated) > 20:
            lines.append(f"  ... and {len(result.deprecated) - 20} more")

    lines.append("")
    lines.append("Recommendations:")
    if result.missing:
        lines.append("  - Add missing tokens to theme YAML (see suggestions above)")
    if result.unused and len(result.unused) > 100:
        lines.append("  - Consider removing unused definitions to reduce file size")
    if result.deprecated:
        lines.append("  - Review deprecated tokens; remove if no longer needed")

    return "\n".join(lines)


def _generate_json_report(result: ValidationResult) -> str:
    """Generate machine-readable JSON report."""
    report = {
        "coverage": result.coverage,
        "used_count": len(result.used),
        "defined_count": len(result.defined),
        "missing": {
            "count": len(result.missing),
            "tokens": sorted(list(result.missing))
        },
        "unused": {
            "count": len(result.unused),
            "tokens": sorted(list(result.unused))
        },
        "deprecated": {
            "count": len(result.deprecated),
            "tokens": sorted(list(result.deprecated))
        },
        "changes": {
            "newly_missing": sorted(list(result.newly_missing)),
            "newly_unused": sorted(list(result.newly_unused)),
            "newly_added": sorted(list(result.used_diff)),
            "removed": sorted(list(result.removed_usage))
        } if result.baseline else None
    }
    return json.dumps(report, indent=2)


def _generate_markdown_report(result: ValidationResult) -> str:
    """Generate Markdown report suitable for documentation/CHANGELOG."""
    lines = []
    lines.append("# Theme Validation Report")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Coverage | {result.coverage:.1f}% |")
    lines.append(f"| Used tokens | {len(result.used)} |")
    lines.append(f"| Defined tokens | {len(result.defined)} |")
    lines.append(f"| Missing | {len(result.missing)} |")
    lines.append(f"| Unused | {len(result.unused)} |")
    if result.deprecated:
        lines.append(f"| Deprecated | {len(result.deprecated)} |")
    lines.append("")

    if result.missing:
        lines.append("## Missing Tokens")
        lines.append("")
        missing_by_cat = _categorize_by_prefix(result.missing)
        for category in sorted(missing_by_cat.keys()):
            tokens = sorted(missing_by_cat[category])
            if tokens:
                lines.append(f"### {category}")
                for token in tokens:
                    lines.append(f"- `{token}`")
                lines.append("")
        lines.append("### Suggestions")
        for token in sorted(result.missing)[:20]:
            suggestion = _get_suggestion(token)
            if suggestion:
                lines.append(f"- **{token}**: {suggestion}")
        if len(result.missing) > 20:
            lines.append(f"- ... and {len(result.missing) - 20} more")

    if result.unused:
        lines.append("")
        lines.append("## Unused Definitions")
        lines.append("")
        lines.append("Tokens defined in YAML but not referenced in code:")
        lines.append("")
        unused_by_cat = _categorize_by_prefix(result.unused)
        for category in sorted(unused_by_cat.keys()):
            tokens = sorted(unused_by_cat[category])
            if tokens:
                lines.append(f"### {category}")
                for token in tokens[:30]:
                    lines.append(f"- `{token}`")
                if len(tokens) > 30:
                    lines.append(f"- ... and {len(tokens) - 30} more")
                lines.append("")

    if result.deprecated:
        lines.append("")
        lines.append("## Deprecated Tokens")
        lines.append("")
        lines.append("These tokens were previously used but are now orphaned:")
        lines.append("")
        for token in sorted(result.deprecated)[:30]:
            lines.append(f"- `{token}`")
        if len(result.deprecated) > 30:
            lines.append(f"- ... and {len(result.deprecated) - 30} more")

    return "\n".join(lines)


def get_exit_code(result: ValidationResult, strict: bool = False) -> int:
    """Determine exit code based on validation result.

    Args:
        result: ValidationResult
        strict: If True, any issue causes non-zero exit (unused currently)

    Returns:
        Exit code (0-3)
    """
    if result.missing:
        return 1
    if result.unused:
        return 2
    if result.deprecated:
        return 3
    return 0
