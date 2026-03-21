#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Test suite for main_panel.py theme migration.
TDD: Verify SpinRenderPanel uses centralized theme instead of class-level color constants.
"""
import sys
from unittest.mock import MagicMock

# Mock OpenGL module to avoid dependency in tests
sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()
sys.modules['OpenGL.GLU'] = MagicMock()
sys.modules['OpenGL.GLUT'] = MagicMock()

import pytest

from SpinRender.core.theme import Theme
_theme = Theme.current()


def test_no_class_level_colors():
    """SpinRenderPanel should have NO class-level color constants."""
    import inspect
    from SpinRender.ui import main_panel

    forbidden_attrs = [
        'BG_PAGE', 'BG_PANEL', 'BG_INPUT', 'BG_SURFACE',
        'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_MUTED',
        'ACCENT_CYAN', 'ACCENT_YELLOW', 'ACCENT_GREEN', 'ACCENT_ORANGE',
        'BORDER_DEFAULT'
    ]

    panel_class = getattr(main_panel, 'SpinRenderPanel', None)
    assert panel_class is not None, "SpinRenderPanel class not found in main_panel module"

    class_vars = panel_class.__dict__
    found_attrs = [attr for attr in forbidden_attrs if attr in class_vars]

    assert not found_attrs, (
        f"SpinRenderPanel has class-level color constants: {found_attrs}. "
        f"All colors must use theme singleton instead."
    )


def test_uses_theme_module():
    """main_panel.py must import the Theme class."""
    from SpinRender.ui import main_panel
    # Check that Theme class is imported (not old theme module)
    assert hasattr(main_panel, 'Theme'), "main_panel.py must import Theme class from core.theme"
    assert hasattr(main_panel, '_theme'), "main_panel.py should have _theme = Theme.current()"
