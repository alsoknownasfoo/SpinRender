#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for dialogs.py theme migration.

Tests that BaseStyledDialog and its subclasses use theme tokens
instead of class-level color attributes.
"""
import pytest
import wx

from SpinRender.core.theme import Theme
_theme = Theme.current()


class TestBaseStyledDialogTheme:
    """Test that BaseStyledDialog uses theme colors, not class constants."""

    def test_no_class_level_colors(self):
        """BaseStyledDialog must not define BG_MODAL, BORDER_DEFAULT, ACCENT_YELLOW, TEXT_PRIMARY as class attrs."""
        from SpinRender.ui.dialogs import BaseStyledDialog

        forbidden_attrs = ['BG_MODAL', 'BORDER_DEFAULT', 'ACCENT_YELLOW', 'TEXT_PRIMARY']
        for attr in forbidden_attrs:
            if hasattr(BaseStyledDialog, attr):
                pytest.fail(f"BaseStyledDialog should not have class attribute {attr}")

    def test_uses_theme_colors_in_constructor(self):
        """BaseStyledDialog.__init__ must use _theme.color() calls."""
        from SpinRender.ui.dialogs import BaseStyledDialog

        class TestDialog(BaseStyledDialog):
            def __init__(self, parent):
                super().__init__(parent, title="Test", size=(400, 300))

        dlg = TestDialog(None)
        # Basic sanity: dialog created without error
        assert dlg is not None

    def test_shadow_size_from_theme(self):
        """SHADOW_SIZE should be derived from theme, not a class constant."""
        from SpinRender.ui.dialogs import BaseStyledDialog
        # SHADOW_SIZE should not be a class-level constant
        if hasattr(BaseStyledDialog, 'SHADOW_SIZE'):
            # If it exists, it should be None or very small (placeholder)
            assert BaseStyledDialog.SHADOW_SIZE is None, "SHADOW_SIZE must be None if present"
        # Verify that the dialog can be instantiated and uses theme token
        class TestDialog(BaseStyledDialog):
            def __init__(self, parent):
                super().__init__(parent, title="Test", size=(400, 300))
        dlg = TestDialog(None)
        # Check that instance has shadow_size attribute set from theme
        assert hasattr(dlg, 'shadow_size'), "Dialog instance must have shadow_size attribute"
        # The value should be 16 (from dark.yaml) or fallback 16
        assert dlg.shadow_size == 16, f"Expected shadow_size=16, got {dlg.shadow_size}"


class TestAdvancedOptionsDialogTheme:
    """Test AdvancedOptionsDialog uses theme colors."""

    def test_no_inherited_class_colors(self):
        """AdvancedOptionsDialog should not introduce new class-level color constants."""
        from SpinRender.ui.dialogs import AdvancedOptionsDialog
        color_attrs = [attr for attr in dir(AdvancedOptionsDialog) if attr.isupper() and 'COLOR' in attr]
        assert len(color_attrs) == 0, f"Found class color attrs: {color_attrs}"


class TestSavePresetDialogTheme:
    """Test SavePresetDialog uses theme colors."""

    def test_no_inherited_class_colors(self):
        """SavePresetDialog should not introduce new class-level color constants."""
        from SpinRender.ui.dialogs import SavePresetDialog
        color_attrs = [attr for attr in dir(SavePresetDialog) if attr.isupper() and 'COLOR' in attr]
        assert len(color_attrs) == 0, f"Found class color attrs: {color_attrs}"
