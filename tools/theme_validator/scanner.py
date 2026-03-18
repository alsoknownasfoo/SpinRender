"""Theme token scanner using AST analysis.

Scans Python source files to extract theme token references.
"""

import ast
import os
from pathlib import Path
from typing import Dict, Set, Optional


class ThemeMethodVisitor(ast.NodeVisitor):
    """AST visitor to extract theme token references."""

    # All theme methods that accept token strings as first positional arg
    THEME_METHODS = {
        'color', 'color_states',
        'size', 'font_size',
        'font', 'font_family'
    }

    def __init__(self):
        self.tokens: Set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes to detect theme token usage."""
        token = self._extract_token_from_call(node)
        if token:
            self.tokens.add(token)
        # Continue visiting children
        self.generic_visit(node)

    def _extract_token_from_call(self, node: ast.Call) -> Optional[str]:
        """Check if a call matches theme.token() pattern and extract token string."""
        # Only interested in calls with at least one positional argument
        if not node.args or not isinstance(node.args[0], ast.Constant):
            return None

        # Extract the string argument
        if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            token = node.args[0].value
        else:
            return None

        # Check if this is a call on theme-like object or Theme.current()
        if self._is_theme_call(node.func):
            return token

        return None

    def _is_theme_call(self, func: ast.AST) -> bool:
        """Determine if func represents a theme method call."""
        if not isinstance(func, ast.Attribute):
            return False

        method_name = func.attr
        if method_name not in self.THEME_METHODS:
            return False

        # Check if the value is one of:
        # - Name with id='theme' or '_theme'
        # - Attribute access: Theme.current()
        value = func.value

        if isinstance(value, ast.Name):
            return value.id in ('theme', '_theme')
        elif isinstance(value, ast.Call):
            # Check if it's Theme.current()
            call = value
            if (isinstance(call.func, ast.Attribute) and
                call.func.attr == 'current' and
                isinstance(call.func.value, ast.Name) and
                call.func.value.id == 'Theme'):
                return True

        return False


def extract_tokens_from_ast(tree: ast.AST) -> Set[str]:
    """Extract token strings from an AST.

    Args:
        tree: Parsed AST

    Returns:
        Set of token strings found in the code
    """
    visitor = ThemeMethodVisitor()
    visitor.visit(tree)
    return visitor.tokens


def _categorize_tokens(tokens: Set[str]) -> Dict[str, Set[str]]:
    """Categorize tokens by type.

    Args:
        tokens: Set of all token strings

    Returns:
        Dictionary with keys 'colors', 'sizes', 'fonts', 'components', 'all'
    """
    colors = set()
    sizes = set()
    fonts = set()
    components = set()

    for token in tokens:
        if token.startswith('colors.') or token.startswith('palette.'):
            colors.add(token)
        elif token.startswith('spacing.') or token.startswith('typography.scale.'):
            sizes.add(token)
        elif token.startswith('components.'):
            components.add(token)
        else:
            # Could be a font preset or other; if used with theme.font-family(), it's a font
            fonts.add(token)

    return {
        'colors': colors,
        'sizes': sizes,
        'fonts': fonts,
        'components': components,
        'all': tokens,
    }


def scan_directory(path: str) -> dict:
    """Scan all .py files under path and return token categories.

    Args:
        path: Directory path to scan recursively

    Returns:
        Dictionary with categorized token sets:
        {
            'colors': set([...]),
            'sizes': set([...]),
            'fonts': set([...]),
            'components': set([...]),
            'all': set([...])
        }
    """
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    all_tokens: Set[str] = set()
    file_count = 0
    error_count = 0

    for py_file in root.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            tokens = extract_tokens_from_ast(tree)
            all_tokens.update(tokens)
            file_count += 1
        except SyntaxError as e:
            error_count += 1
            print(f"Warning: Syntax error in {py_file}: {e}")
        except Exception as e:
            error_count += 1
            print(f"Warning: Error processing {py_file}: {e}")

    result = _categorize_tokens(all_tokens)
    return result
