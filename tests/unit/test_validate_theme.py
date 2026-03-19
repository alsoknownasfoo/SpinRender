#!/usr/bin/env python3
"""Comprehensive unit tests for theme validator modules (scanner, yaml_parser, comparator, fixer)."""

import sys
import ast
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add tools directory to path
sys.path.insert(0, '/Users/foo/Code/SpinRender_claude/tools')

import pytest

from theme_validator.scanner import (
    ThemeMethodVisitor, 
    extract_tokens_from_ast,
    _categorize_tokens,
    scan_directory
)
from theme_validator.yaml_parser import (
    collect_tokens,
    categorize_tokens,
    parse_yaml
)
from theme_validator.comparator import (
    compare_tokens,
    generate_report,
    get_exit_code,
    ValidationResult,
    _categorize_by_prefix
)
from theme_validator.fixer import (
    _generate_placeholder,
    _get_nested_value,
    _set_nested_value,
    _delete_nested_value,
    _add_missing_token,
    _purge_unused_tokens,
    _deprecate_unused_tokens,
    _create_backup,
    apply_fixes
)


# ============================================================================
# Scanner Tests
# ============================================================================

class TestScanner:
    """Tests for scanner module."""

    def test_extract_tokens_from_ast_simple(self):
        """Test extracting tokens from a simple Python snippet."""
        code = '''
from core.theme import theme
color = theme.color("colors.bg.page")
size = theme.size("spacing.md")
'''
        tree = ast.parse(code)
        tokens = extract_tokens_from_ast(tree)
        assert 'colors.bg.page' in tokens
        assert 'spacing.md' in tokens
        assert len(tokens) == 2

    def test_extract_tokens_multiple_patterns(self):
        """Test extracting tokens with different theme call patterns."""
        code = '''
from core.theme import Theme, theme, _theme

# Pattern 1: theme.token()
a = theme.color("colors.primary")
b = theme.size("spacing.lg")

# Pattern 2: _theme.token()
c = _theme.font("fonts.body")

# Pattern 3: Theme.current().token()
d = Theme.current().color("palette.neutral-1")
'''
        tree = ast.parse(code)
        tokens = extract_tokens_from_ast(tree)
        assert 'colors.primary' in tokens
        assert 'spacing.lg' in tokens
        assert 'fonts.body' in tokens
        assert 'palette.neutral-1' in tokens

    def test_extract_tokens_different_types(self):
        """Test extracting different token types (color, size, font)."""
        code = '''
theme.color("colors.bg.page")
theme.color_states("colors.state.hover")
theme.size("spacing.sm")
theme.font_size("typography.scale.h1")
theme.font("fonts.mono")
theme.font_family("typography.presets.body")
'''
        tree = ast.parse(code)
        tokens = extract_tokens_from_ast(tree)
        assert 'colors.bg.page' in tokens
        assert 'colors.state.hover' in tokens
        assert 'spacing.sm' in tokens
        assert 'typography.scale.h1' in tokens
        assert 'fonts.mono' in tokens
        assert 'typography.presets.body' in tokens

    def test_extract_tokens_ignores_non_string_args(self):
        """Test that non-string arguments are ignored."""
        code = '''
theme.color(variable_name)
theme.color(123)
theme.color(None)
theme.color("valid.token")
'''
        tree = ast.parse(code)
        tokens = extract_tokens_from_ast(tree)
        # Only the valid string literal should be extracted
        assert 'valid.token' in tokens
        assert len(tokens) == 1

    def test_extract_tokens_ignores_non_theme_calls(self):
        """Test that calls not matching theme patterns are ignored."""
        code = '''
other.color("colors.bg.page")
theme.other_method("some.token")
some_object.theme.color("ignore.me")
'''
        tree = ast.parse(code)
        tokens = extract_tokens_from_ast(tree)
        assert len(tokens) == 0

    def test_categorization(self):
        """Test token categorization by type."""
        tokens = {
            'colors.bg.page',
            'colors.primary',
            'palette.neutral-3',
            'palette.cyan',
            'spacing.md',
            'typography.scale.h1',
            'components.button.bg',
            'fonts.mono'
        }
        categorized = _categorize_tokens(tokens)
        
        # Colors (colors.* and palette.*)
        assert 'colors.bg.page' in categorized['colors']
        assert 'colors.primary' in categorized['colors']
        assert 'palette.neutral-3' in categorized['colors']
        assert 'palette.cyan' in categorized['colors']
        
        # Sizes (spacing.* and typography.scale.*)
        assert 'spacing.md' in categorized['sizes']
        assert 'typography.scale.h1' in categorized['sizes']
        
        # Components
        assert 'components.button.bg' in categorized['components']
        
        # Fonts (everything else used with font methods)
        assert 'fonts.mono' in categorized['fonts']
        
        # All should be present
        assert categorized['all'] == tokens

    def test_scan_directory_skips_syntax_errors(self, tmp_path):
        """Test that scan_directory gracefully handles files with syntax errors."""
        # Create a valid Python file
        valid_file = tmp_path / "valid.py"
        valid_file.write_text('theme.color("colors.test")')
        
        # Create a file with syntax error
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text('def broken(:\n    pass')
        
        # Create another valid file
        valid_file2 = tmp_path / "valid2.py"
        valid_file2.write_text('theme.size("spacing.lg")')
        
        result = scan_directory(str(tmp_path))
        
        # Should have tokens from valid files only
        assert 'colors.test' in result['all']
        assert 'spacing.lg' in result['all']
        # Invalid file should be skipped (not crash)

    def test_scan_directory_empty_dir(self, tmp_path):
        """Test scanning an empty directory."""
        result = scan_directory(str(tmp_path))
        assert result['all'] == set()
        assert result['colors'] == set()
        assert result['sizes'] == set()
        assert result['fonts'] == set()
        assert result['components'] == set()


# ============================================================================
# YAML Parser Tests
# ============================================================================

class TestYAMLParser:
    """Tests for yaml_parser module."""

    def test_parse_yaml_basic(self, tmp_path):
        """Test parsing a minimal YAML structure."""
        yaml_content = '''
palette:
  neutral-1: "#000000"
colors:
  bg:
    page: {ref: 'palette.neutral-1'}
'''
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        result = parse_yaml(str(yaml_file))
        
        assert 'palette.neutral-1' in result['all']
        assert 'colors.bg.page' in result['all']
        assert 'palette' in result
        assert 'colors' in result

    def test_collect_tokens_nested(self):
        """Test that nested paths are correctly collected."""
        data = {
            'colors': {
                'bg': {
                    'page': {'ref': 'palette.neutral-1'},
                    'panel': {'ref': 'palette.neutral-2'}
                },
                'text': {
                    'primary': {'ref': 'palette.neutral-14'}
                }
            },
            'typography': {
                'scale': {
                    'h1': {'size': 24}
                }
            }
        }
        tokens = collect_tokens(data)
        
        expected = {
            'colors.bg.page',
            'colors.bg.panel',
            'colors.text.primary',
            'typography.scale.h1'
        }
        assert tokens == expected

    def test_list_handling(self):
        """Test that lists don't create indexed tokens."""
        data = {
            'colors': {
                'preset': [
                    {'ref': 'palette.red'},
                    {'ref': 'palette.blue'}
                ]
            }
        }
        tokens = collect_tokens(data)
        
        # Should have 'colors.preset' but NOT 'colors.preset.0' or 'colors.preset.1'
        assert 'colors.preset' in tokens
        assert 'colors.preset.0' not in tokens
        assert 'colors.preset.1' not in tokens

    def test_categorization(self):
        """Test that tokens are properly categorized."""
        data = {
            'palette': {'red': '#FF0000'},
            'colors': {'bg': {'page': {'ref': 'palette.red'}}},
            'typography': {'scale': {'body': 14}},
            'spacing': {'sm': 8, 'md': 16},
            'borders': {'radius': {'md': 4}},
            'components': {'button': {'bg': {'ref': 'colors.bg.page'}}}
        }
        result = categorize_tokens(collect_tokens(data))
        
        assert 'palette.neutral-1' not in result['palette']  # our test key is 'red'
        assert 'palette.red' in result['palette']
        assert 'colors.bg.page' in result['colors']
        assert 'typography.scale.body' in result['typography']
        assert 'spacing.sm' in result['spacing']
        assert 'spacing.md' in result['spacing']
        assert 'borders.radius.md' in result['borders']
        assert 'components.button.bg' in result['components']

    def test_missing_section_returns_empty(self, tmp_path):
        """Test that missing top-level sections yield empty category sets."""
        yaml_content = '''
palette:
  red: "#FF0000"
'''
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        result = parse_yaml(str(yaml_file))
        
        assert 'palette' in result
        assert result['palette'] == {'palette.red'}
        assert result['colors'] == set()
        assert result['typography'] == set()
        assert result['spacing'] == set()
        assert result['borders'] == set()
        assert result['components'] == set()

    def test_parse_yaml_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            parse_yaml('/nonexistent/path.yaml')

    def test_parse_yaml_empty_file(self, tmp_path):
        """Test parsing an empty YAML file."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text('')
        
        result = parse_yaml(str(yaml_file))
        
        # All categories should be empty
        for cat in ['palette', 'colors', 'typography', 'spacing', 'borders', 'components', 'all']:
            assert result[cat] == set()


# ============================================================================
# Comparator Tests
# ============================================================================

class TestComparator:
    """Tests for comparator module."""

    def test_compare_tokens_basic(self):
        """Test basic comparison logic."""
        used = {
            'all': {'colors.bg.page', 'colors.bg.panel', 'colors.primary'}
        }
        defined = {
            'all': {
                'colors.bg.page',
                'colors.bg.panel',
                'colors.bg.surface',
                'colors.primary',
                'colors.text.primary'
            }
        }
        
        result = compare_tokens(used, defined)
        
        assert 'colors.bg.page' in result.used
        assert 'colors.bg.page' in result.defined
        assert 'colors.bg.surface' in result.unused
        assert 'colors.text.primary' in result.unused
        assert result.missing == set()
        assert abs(result.coverage - 100.0) < 0.01

    def test_compare_tokens_with_missing(self):
        """Test when there are missing tokens."""
        used = {'all': {'colors.bg.page', 'colors.bg.panel', 'colors.accent.missing'}}
        defined = {'all': {'colors.bg.page', 'colors.bg.panel', 'colors.primary'}}
        
        result = compare_tokens(used, defined)
        
        assert 'colors.accent.missing' in result.missing
        assert abs(result.coverage - 66.67) < 0.1

    def test_coverage_calculation(self):
        """Verify coverage percentage calculation."""
        used = {'all': {'a', 'b', 'c', 'd'}}
        defined = {'all': {'a', 'b', 'c', 'e', 'f'}}
        
        result = compare_tokens(used, defined)
        # intersection = {a, b, c} = 3 out of 4 used
        assert abs(result.coverage - 75.0) < 0.01

    def test_compare_tokens_with_baseline(self):
        """Test baseline comparison."""
        used = {'all': {'token.a', 'token.b', 'token.c'}}
        defined = {'all': {'token.a', 'token.b', 'token.d', 'token.e'}}
        
        baseline = {
            'tokens': {
                'used': ['token.x', 'token.y'],
                'missing': ['token.z'],
                'unused': ['token.old']
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            baseline_path = f.name
            json.dump(baseline, f)
        
        try:
            result = compare_tokens(used, defined, baseline_path=baseline_path)
            
            assert 'token.c' in result.newly_missing
            assert result.used_diff == {'token.a', 'token.b', 'token.c'}
            assert result.deprecated == set()
        finally:
            os.unlink(baseline_path)

    def test_baseline_deprecated_detection(self):
        """Test that deprecated tokens (used in baseline, now unused) are detected."""
        used = {'all': {'token.a', 'token.b'}}
        defined = {'all': {'token.a', 'token.b', 'token.c', 'token.d'}}
        
        baseline = {
            'tokens': {
                'used': ['token.a', 'token.b', 'token.c'],
                'missing': [],
                'unused': []
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            baseline_path = f.name
            json.dump(baseline, f)
        
        try:
            result = compare_tokens(used, defined, baseline_path=baseline_path)
            
            # token.c was used before but is now unused => deprecated
            assert 'token.c' in result.deprecated
            assert "token.c" in result.newly_unused
        finally:
            os.unlink(baseline_path)

    def test_generate_report_text(self):
        """Test text report generation."""
        result = ValidationResult(
            used={'colors.bg', 'colors.accent', 'spacing.md'},
            defined={'colors.bg', 'colors.accent', 'colors.text', 'spacing.md', 'spacing.lg'},
            missing=set(),
            unused={'colors.text', 'spacing.lg'},
            coverage=100.0,
            baseline=None
        )
        
        report = generate_report(result, 'text')
        assert 'Coverage: 100.0%' in report
        assert 'Used tokens: 3' in report
        assert 'Defined tokens: 5' in report
        assert 'Missing: 0' in report
        assert 'Unused: 2' in report
        assert 'colors.text' in report
        assert 'spacing.lg' in report

    def test_generate_report_json(self):
        """Test JSON report generation."""
        result = ValidationResult(
            used={'a', 'b'},
            defined={'a', 'c'},
            missing=set(),
            unused={'c'},
            coverage=50.0,
            baseline=None
        )
        
        report = generate_report(result, 'json')
        parsed = json.loads(report)
        
        assert parsed['coverage'] == 50.0
        assert parsed['used_count'] == 2
        assert parsed['defined_count'] == 2
        assert parsed['missing']['count'] == 0
        assert parsed['unused']['count'] == 1
        assert 'c' in parsed['unused']['tokens']

    def test_generate_report_markdown(self):
        """Test Markdown report generation."""
        result = ValidationResult(
            used={'a.b', 'c.d'},
            defined={'a.b', 'e.f'},
            missing=set(),
            unused={'e.f'},
            coverage=50.0,
            baseline=None
        )
        
        report = generate_report(result, 'markdown')
        assert '# Theme Validation Report' in report
        assert '50.0%' in report
        assert '## Unused Definitions' in report
        assert '`e.f`' in report

    def test_generate_report_with_missing_markdown(self):
        """Test markdown includes missing tokens section."""
        result = ValidationResult(
            used={'colors.bg'},
            defined={'colors.text'},
            missing={'colors.bg'},
            unused=set(),
            coverage=0.0,
            baseline=None
        )
        
        report = generate_report(result, 'markdown')
        assert '## Missing Tokens' in report
        assert '`colors.bg`' in report

    def test_get_exit_code(self):
        """Test exit code determination."""
        result = ValidationResult(set(), set(), set(), set(), 0.0)
        assert get_exit_code(result) == 0
        
        result = ValidationResult(set(), set(), {'a'}, set(), 0.0)
        assert get_exit_code(result) == 1
        
        result = ValidationResult(set(), set(), set(), {'a'}, 0.0)
        assert get_exit_code(result) == 2
        
        result = ValidationResult(set(), set(), set(), set(), 0.0)
        result.deprecated = {'a'}
        assert get_exit_code(result) == 3
        
        # When both missing and unused, missing (code 1) takes precedence
        result = ValidationResult(set(), set(), {'a'}, {'b'}, 0.0)
        assert get_exit_code(result) == 1

    def test_categorize_by_prefix(self):
        """Test token categorization by prefix."""
        tokens = {
            'colors.bg.page',
            'colors.text.primary',
            'typography.scale.h1',
            'spacing.md',
            'components.button.bg',
            'borders.radius.sm'
        }
        categorized = _categorize_by_prefix(tokens)
        
        assert 'colors' in categorized
        assert 'typography' in categorized
        assert 'spacing' in categorized
        assert 'components' in categorized
        assert 'borders' in categorized
        
        assert 'colors.bg.page' in categorized['colors']
        assert 'typography.scale.h1' in categorized['typography']

    def test_empty_sets(self):
        """Test comparison with empty sets."""
        used = {'all': set()}
        defined = {'all': {'a', 'b'}}
        
        result = compare_tokens(used, defined)
        assert result.missing == set()
        assert result.unused == {'a', 'b'}
        assert result.coverage == 0.0
        
        used = {'all': {'a', 'b'}}
        defined = {'all': set()}
        
        result = compare_tokens(used, defined)
        assert result.missing == {'a', 'b'}
        assert result.unused == set()
        assert result.coverage == 0.0
        
        used = {'all': set()}
        defined = {'all': set()}
        
        result = compare_tokens(used, defined)
        assert result.missing == set()
        assert result.unused == set()
        assert result.coverage == 0.0


# ============================================================================
# Fixer Tests
# ============================================================================

class TestFixer:
    """Tests for fixer module."""

    def test_generate_placeholder_colors(self):
        """Test placeholder generation for color tokens."""
        # Test different color subcategories
        assert _generate_placeholder('colors.bg.page') == {'ref': 'palette.neutral-3'}
        assert _generate_placeholder('colors.bg.modal') == {'ref': 'palette.neutral-3'}
        assert _generate_placeholder('colors.text.primary') == {'ref': 'palette.neutral-14'}
        assert _generate_placeholder('colors.primary') == {'ref': 'palette.cyan'}
        assert _generate_placeholder('colors.border.default') == {'ref': 'palette.neutral-7'}
        assert _generate_placeholder('colors.state.hover') == {'ref': 'palette.overlay-light'}
        assert _generate_placeholder('colors.state.pressed') == {'ref': 'palette.overlay-medium'}

    def test_generate_placeholder_palette(self):
        """Test placeholder for palette tokens."""
        placeholder = _generate_placeholder('palette.neutral-1')
        assert placeholder == "#XXXXXX"

    def test_generate_placeholder_typography(self):
        """Test placeholder for typography tokens."""
        assert _generate_placeholder('typography.scale.h1') == 11
        assert _generate_placeholder('typography.weights.bold') == 400
        assert _generate_placeholder('typography.families.mono') == "mono"
        
        preset = _generate_placeholder('typography.presets.body')
        assert isinstance(preset, dict)
        assert 'family' in preset
        assert 'size' in preset
        assert 'weight' in preset

    def test_generate_placeholder_spacing(self):
        """Test placeholder for spacing tokens."""
        assert _generate_placeholder('spacing.md') == 10
        assert _generate_placeholder('spacing.lg') == 10

    def test_generate_placeholder_borders(self):
        """Test placeholder for border tokens."""
        assert _generate_placeholder('borders.radius.md') == 4
        assert _generate_placeholder('borders.width.default') == 1

    def test_generate_placeholder_components(self):
        """Test placeholder for component tokens."""
        # Color-related component
        placeholder = _generate_placeholder('components.button.bg')
        assert isinstance(placeholder, list)
        assert 'colors.bg.input' in placeholder
        
        # Font-related component
        placeholder = _generate_placeholder('components.card.font')
        assert isinstance(placeholder, dict)
        assert 'ref' in placeholder
        
        # Radius-related component
        placeholder = _generate_placeholder('components.dialog.radius')
        assert isinstance(placeholder, dict)
        assert placeholder['ref'] == 'borders.radius.md'

    def test_nested_value_operations(self):
        """Test nested dict get/set/delete operations."""
        data = {
            'colors': {
                'bg': {
                    'page': {'ref': 'palette.neutral-3'}
                }
            }
        }
        
        # Get existing
        assert _get_nested_value(data, ['colors', 'bg', 'page']) == {'ref': 'palette.neutral-3'}
        
        # Get non-existing raises KeyError
        with pytest.raises(KeyError):
            _get_nested_value(data, ['colors', 'text', 'primary'])
        
        # Set nested value
        _set_nested_value(data, ['colors', 'text', 'primary'], {'ref': 'palette.neutral-14'})
        assert _get_nested_value(data, ['colors', 'text', 'primary']) == {'ref': 'palette.neutral-14'}
        
        # Delete nested value
        assert _delete_nested_value(data, ['colors', 'text', 'primary']) == True
        with pytest.raises(KeyError):
            _get_nested_value(data, ['colors', 'text', 'primary'])
        
        # Delete non-existing returns False
        assert _delete_nested_value(data, ['colors', 'nonexistent']) == False

    def test_add_missing_token(self, tmp_path):
        """Test adding a missing token to YAML data."""
        yaml_content = '''
palette:
  neutral-1: "#000000"
colors:
  bg:
    page: {ref: 'palette.neutral-1'}
'''
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        yaml_data = parse_yaml(str(yaml_file))
        # Manually construct a proper dict structure (parse_yaml returns categorized sets, not raw data)
        # Let's use yaml.safe_load directly
        import yaml
        with open(yaml_file, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        result = _add_missing_token(yaml_data, 'colors.text.primary', dry_run=False)
        
        assert result['added'] == True
        assert result['path'] == 'colors.text.primary'
        assert result['section'] == 'colors'
        # Check that placeholder value is set
        assert _get_nested_value(yaml_data, ['colors', 'text', 'primary']) == {'ref': 'palette.neutral-14'}

    def test_add_missing_token_dry_run(self):
        """Test dry-run doesn't modify data."""
        yaml_data = {'colors': {}}
        result = _add_missing_token(yaml_data, 'colors.bg.page', dry_run=True)
        
        assert result['added'] == True
        assert "bg" not in yaml_data.get("colors", {})  # No modification

    def test_purge_unused_tokens(self):
        """Test removing unused tokens from YAML data."""
        yaml_data = {
            'palette': {
                'neutral-1': '#000000',
                'neutral-2': '#111111',
                'neutral-3': '#222222'
            },
            'colors': {
                'bg': {
                    'page': {'ref': 'palette.neutral-1'},
                    'panel': {'ref': 'palette.neutral-2'}
                },
                'text': {
                    'primary': {'ref': 'palette.neutral-3'}
                }
            }
        }
        
        # Remove two tokens
        removed = _purge_unused_tokens(yaml_data, {'palette.neutral-2', 'colors.text.primary'}, dry_run=False)
        
        assert set(removed['removed']) == {'palette.neutral-2', 'colors.text.primary'}
        assert 'palette.neutral-2' not in yaml_data['palette']
        # The 'text' container remains but its child 'primary' is gone
        assert 'primary' not in yaml_data['colors'].get('text', {})
        assert yaml_data['colors'].get('text') == {}

    def test_purge_unused_tokens_sorted_by_depth(self):
        """Test that tokens are removed in depth order (deepest first)."""
        yaml_data = {
            'colors': {
                'bg': {
                    'page': {'ref': 'palette.1'},
                    'panel': {'ref': 'palette.2'}
                }
            }
        }
        
        # Both should be removed successfully
        removed = _purge_unused_tokens(yaml_data, {
            'colors.bg.page',
            'colors.bg.panel'
        }, dry_run=False)
        
        # The 'bg' container remains but children are gone
        assert 'bg' in yaml_data['colors']
        assert 'page' not in yaml_data['colors']['bg']
        assert 'panel' not in yaml_data['colors']['bg']

    def test_deprecate_unused(self, tmp_path):
        """Test commenting out unused tokens."""
        yaml_content = '''palette:
  neutral-1: "#000000"
  neutral-2: "#111111"
colors:
  bg:
    page: {ref: 'palette.neutral-1'}
'''
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        result = _deprecate_unused_tokens(
            str(yaml_file),
            {'palette.neutral-2'},
            dry_run=False
        )
        
        assert 'palette.neutral-2' in result['deprecated']
        
        # Check file content
        content = yaml_file.read_text()
        assert '# DEPRECATED:' in content
        assert 'neutral-2' in content

    def test_backup_created(self, tmp_path):
        """Test that backup file is created before modifications."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text('palette:\n  red: "#FF0000"')
        
        backup_path = _create_backup(str(yaml_file))
        
        assert backup_path == str(yaml_file) + ".bak"
        assert Path(backup_path).exists()
        assert Path(backup_path).read_text() == yaml_file.read_text()

    def test_dry_run_no_changes(self, tmp_path):
        """Test that dry-run doesn't create backups or modify files."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text('palette:\n  red: "#FF0000"')
        
        yaml_data = {'palette': {'red': '#FF0000'}}
        result = _purge_unused_tokens(yaml_data, {'palette.red'}, dry_run=True)
        
        assert result['removed'] == ['palette.red']
        assert 'palette' in yaml_data  # Unchanged
        assert not yaml_file.with_suffix('.yaml.bak').exists()


# ============================================================================
# Integration Test
# ============================================================================

class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_validation_flow(self, tmp_path):
        """Test complete validation: scan -> parse -> compare -> report."""
        # Create a small codebase
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "module.py").write_text('''
from core.theme import theme
def render():
    theme.color("colors.bg.page")
    theme.size("spacing.md")
''')
        
        # Create a YAML theme
        yaml_file = tmp_path / "theme.yaml"
        yaml_file.write_text('''
colors:
  bg:
    page: {ref: 'palette.neutral-3'}
spacing:
  md: 16
palette:
  neutral-3: "#121212"
''')
        
        # Run the workflow
        used = scan_directory(str(src_dir))
        defined = parse_yaml(str(yaml_file))
        result = compare_tokens(used, defined)
        
        # Verify
        assert result.coverage == 100.0
        assert result.missing == set()
        # There may be unused tokens if palette has more than neutral-3
        # That's okay

    def test_apply_fixes_add_missing(self, tmp_path):
        """Test the fix workflow: add missing tokens."""
        yaml_file = tmp_path / "theme.yaml"
        yaml_file.write_text('''
palette:
  neutral-1: "#000000"
''')
        
        # Simulate a validation result with missing token
        result = ValidationResult(
            used={'colors.bg.page'},
            defined={'palette.neutral-1'},
            missing={'colors.bg.page'},
            unused=set(),
            coverage=0.0
        )
        
        summary = apply_fixes(
            str(yaml_file),
            result,
            add_missing=True,
            purge_unused=False,
            deprecate=False,
            dry_run=False,
            backup=False
        )
        
        assert summary['changes_made'] == True
        assert len(summary['added']) == 1
        assert summary['added'][0]['path'] == 'colors.bg.page'
        
        # Verify YAML was updated
        import yaml
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        assert 'colors' in data
        assert 'bg' in data['colors']
        assert 'page' in data['colors']['bg']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
