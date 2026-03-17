"""Tests for UI package __init__.py theme module exposure.

Task 1.8: Ensure theme module is properly exposed in SpinRender/ui/__init__.py
"""
import os
import ast
import pytest


def read_init_file():
    """Read and return the content of SpinRender/ui/__init__.py."""
    init_path = os.path.join(os.path.dirname(__file__), '..', '..', 'SpinRender', 'ui', '__init__.py')
    init_path = os.path.normpath(init_path)
    with open(init_path, 'r') as f:
        return f.read()


def extract_imports_from_init():
    """Extract import statements from __init__.py AST."""
    content = read_init_file()
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        pytest.fail(f"__init__.py has syntax error: {e}")

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'type': 'import',
                    'module': alias.name,
                    'alias': alias.asname
                })
        elif isinstance(node, ast.ImportFrom):
            imports.append({
                'type': 'from_import',
                'module': node.module,
                'names': [alias.name for alias in node.names],
                'level': node.level
            })
    return imports


class TestInitThemeExposure:
    """Test that __init__.py explicitly exposes the theme module."""

    def test_init_exists(self):
        """__init__.py file must exist."""
        init_path = os.path.join(os.path.dirname(__file__), '..', '..', 'SpinRender', 'ui', '__init__.py')
        init_path = os.path.normpath(init_path)
        assert os.path.exists(init_path), f"Missing file: {init_path}"

    def test_init_has_theme_import(self):
        """__init__.py should contain 'from . import theme' or similar."""
        imports = extract_imports_from_init()
        # Look for: from . import theme  (module=None, level=1, names=['theme'])
        # OR: from .theme import * (module='theme' or 'theme' in names, but simpler: any from_import with level=1 and 'theme' somewhere)
        has_theme_import = any(
            imp['type'] == 'from_import' and
            imp['level'] == 1 and
            ('theme' in imp['names'] or imp.get('module') == 'theme')
            for imp in imports
        )
        assert has_theme_import, "__init__.py should contain 'from . import theme' or 'from .theme import *'"

    def test_theme_constants_accessible_when_exposed(self):
        """After exposure, theme constants should be importable from ui package."""
        # This test assumes the import works. If __init__.py does from . import theme,
        # then SpinRender.ui.theme module object will be exposed.
        from SpinRender.ui import theme
        assert theme is not None
