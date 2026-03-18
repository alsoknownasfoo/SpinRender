#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Test that verifies NO hardcoded wx.Colour() calls remain in UI modules.

This test enforces that all colors come from the theme module.
"""
import pytest
import ast


def extract_wx_color_calls_from_source(file_path, module_name):
    """Parse Python file and find all wx.Colour(...) calls with hardcoded RGB literals."""
    with open(file_path, 'r') as f:
        content = f.read()

    tree = ast.parse(content)
    color_calls = []

    class CallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            # Check if this is wx.Colour(...)
            if isinstance(node.func, ast.Attribute):
                if (isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'wx' and
                    node.func.attr == 'Color'):
                    # Check if ALL positional arguments are literal integers (hardcoded)
                    # We only flag as "hardcoded" if all args are integer constants
                    is_hardcoded = True
                    for arg in node.args:
                        if not isinstance(arg, ast.Constant) or not isinstance(arg.value, int):
                            is_hardcoded = False
                            break
                    # Also check keyword args if any
                    if is_hardcoded:
                        for kw in node.keywords:
                            # Skip 'alpha' keyword if it's not an int constant
                            if not (isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int)):
                                is_hardcoded = False
                                break

                    if is_hardcoded:
                        line_num = node.lineno
                        end_line = node.end_lineno if hasattr(node, 'end_lineno') else line_num
                        color_calls.append({
                            'line': line_num,
                            'end_line': end_line,
                            'module': module_name
                        })
            # Continue visiting
            self.generic_visit(node)

    visitor = CallVisitor()
    visitor.visit(tree)
    return color_calls


class TestNoHardcodedColors:
    """Ensure UI modules have zero inline wx.Colour() calls."""

    def test_custom_controls_no_inline_colors(self):
        """custom_controls.py must not contain any wx.Colour() calls (all must use theme)."""
        calls = extract_wx_color_calls_from_source(
            'SpinRender/ui/custom_controls.py',
            'custom_controls'
        )
        if calls:
            details = ', '.join([f"line {c['line']}" for c in calls])
            pytest.fail(f"custom_controls.py has {len(calls)} wx.Colour calls: {details}")

    def test_dialogs_no_inline_colors(self):
        """dialogs.py must not contain any wx.Colour() calls."""
        calls = extract_wx_color_calls_from_source(
            'SpinRender/ui/dialogs.py',
            'dialogs'
        )
        if calls:
            details = ', '.join([f"line {c['line']}" for c in calls])
            pytest.fail(f"dialogs.py has {len(calls)} wx.Colour calls: {details}")

    def test_main_panel_no_inline_colors(self):
        """main_panel.py must not contain any wx.Colour() calls."""
        calls = extract_wx_color_calls_from_source(
            'SpinRender/ui/main_panel.py',
            'main_panel'
        )
        if calls:
            details = ', '.join([f"line {c['line']}" for c in calls])
            pytest.fail(f"main_panel.py has {len(calls)} wx.Colour calls: {details}")
