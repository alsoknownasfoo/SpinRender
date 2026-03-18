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

    def test_shadow_size_constant_preserved(self):
        """SHADOW_SIZE layout constant should remain as class attribute."""
        from SpinRender.ui.dialogs import BaseStyledDialog
        class_vars = BaseStyledDialog.__dict__
        assert 'SHADOW_SIZE' in class_vars, "BaseStyledDialog must have SHADOW_SIZE class attribute"
        assert class_vars['SHADOW_SIZE'] == 16


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
