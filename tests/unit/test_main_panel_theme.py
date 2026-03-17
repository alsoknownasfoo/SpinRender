"""
Test suite for main_panel.py theme migration
TDD: Verify SpinRenderPanel uses centralized theme instead of class-level color constants
"""
import pytest


class MockSpinRenderPanel:
    """
    Test double for SpinRenderPanel that checks for class-level color constants.
    We cannot instantiate the real class due to KiCad dependencies, but we can
    inspect its class attributes.
    """
    pass


def test_no_class_level_colors():
    """SpinRenderPanel should have NO class-level color constants."""
    import inspect
    from SpinRender.ui import main_panel

    # Class-level color constants that MUST be removed
    forbidden_attrs = [
        'BG_PAGE', 'BG_PANEL', 'BG_INPUT', 'BG_SURFACE',
        'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_MUTED',
        'ACCENT_CYAN', 'ACCENT_YELLOW', 'ACCENT_GREEN', 'ACCENT_ORANGE',
        'BORDER_DEFAULT'
    ]

    # Get the class without instantiating it
    panel_class = getattr(main_panel, 'SpinRenderPanel', None)
    assert panel_class is not None, "SpinRenderPanel class not found in main_panel module"

    # Check class __dict__ directly to avoid inherited attributes
    class_vars = panel_class.__dict__
    found_attrs = [attr for attr in forbidden_attrs if attr in class_vars]

    assert not found_attrs, (
        f"SpinRenderPanel has class-level color constants: {found_attrs}. "
        f"All colors must use theme module instead."
    )


def test_uses_theme_module():
    """main_panel.py must import the theme module."""
    from SpinRender.ui import main_panel

    # Check theme module is imported
    assert hasattr(main_panel, 'theme'), (
        "main_panel.py must import the theme module"
    )


def test_theme_module_accessible():
    """Theme constants should be accessible from main_panel.theme."""
    from SpinRender.ui import main_panel
    from SpinRender.ui import theme

    # Verify key theme attributes exist
    required_attrs = [
        'BG_PAGE', 'BG_PANEL', 'BG_INPUT', 'BG_SURFACE',
        'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_MUTED',
        'ACCENT_CYAN', 'ACCENT_YELLOW', 'ACCENT_GREEN', 'ACCENT_ORANGE',
        'BORDER_DEFAULT'
    ]

    for attr in required_attrs:
        assert hasattr(theme, attr), f"Theme module missing: {attr}"
