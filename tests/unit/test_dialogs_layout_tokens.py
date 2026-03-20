#!/usr/bin/env python3
"""
Tests for dialog layout token integration.

Verify that dialogs use layout.dialogs tokens instead of hardcoded values.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from SpinRender.core.theme import Theme
from SpinRender.ui.dialogs import BaseStyledDialog, AdvancedOptionsDialog, SavePresetDialog, RecallPresetDialog


@pytest.fixture(scope="function", autouse=True)
def reset_theme():
    """Reset theme singleton before each test."""
    Theme._instance = None
    yield
    Theme._instance = None


class TestBaseStyledDialogLayoutTokens:
    """BaseStyledDialog must use layout.dialogs tokens."""

    def test_shadow_size_from_layout(self):
        """SHADOW_SIZE should come from layout.dialogs.default.frame.shadow.size."""
        # Get expected shadow size from theme
        theme = Theme.current()
        expected_shadow = theme._resolve("layout.dialogs.default.frame.shadow.size")
        if expected_shadow is None or expected_shadow == "#FF00FF":
            expected_shadow = 16  # fallback

        # We can't instantiate a real dialog without wx, but we can check the code
        # by inspecting the class or mocking
        from SpinRender.ui import dialogs
        import inspect

        source = inspect.getsource(dialogs.BaseStyledDialog.__init__)
        # Should reference layout.dialogs, not hardcoded 16
        assert "layout.dialogs.default.frame.shadow.size" in source or "self.shadow_size" in source

    def test_header_height_from_layout(self):
        """Header height should use layout.dialogs.default.header.height."""
        from SpinRender.ui import dialogs
        import inspect

        source = inspect.getsource(dialogs.BaseStyledDialog.create_header)
        # Should reference layout.dialogs.default.header.height
        assert "layout.dialogs.default.header.height" in source or "header_height" in source

    def test_no_hardcoded_shadow_in_init(self):
        """BaseStyledDialog.__init__ should not have hardcoded SHADOW_SIZE = 16 at class level."""
        from SpinRender.ui.dialogs import BaseStyledDialog
        # Check that SHADOW_SIZE is not a class constant
        assert not hasattr(BaseStyledDialog, 'SHADOW_SIZE') or BaseStyledDialog.SHADOW_SIZE is None

    def test_no_hardcoded_header_height(self):
        """create_header should not hardcode height=48."""
        from SpinRender.ui.dialogs import BaseStyledDialog
        import inspect

        source = inspect.getsource(BaseStyledDialog.create_header)
        # Should not have hardcoded size=(-1, 48) or height=48
        assert "size=(-1, 48)" not in source
        assert "height: 48" not in source


class TestDialogSubclassesUseLayout:
    """Dialog subclasses should use layout.dialogs variants."""

    def test_advancedoptions_uses_layout_dialogs_options(self):
        """AdvancedOptionsDialog should derive size from layout.dialogs.options."""
        from SpinRender.ui.dialogs import AdvancedOptionsDialog
        import inspect

        source = inspect.getsource(AdvancedOptionsDialog.__init__)
        # Should reference layout.dialogs.options
        assert "layout.dialogs.options" in source

    def test_savepreset_uses_layout_dialogs_addpreset(self):
        """SavePresetDialog should derive size from layout.dialogs.addpreset."""
        from SpinRender.ui.dialogs import SavePresetDialog
        import inspect

        source = inspect.getsource(SavePresetDialog.__init__)
        assert "layout.dialogs.addpreset" in source

    def test_recallpreset_uses_layout_dialogs_presets(self):
        """RecallPresetDialog should derive size from layout.dialogs.presets."""
        from SpinRender.ui.dialogs import RecallPresetDialog
        import inspect

        source = inspect.getsource(RecallPresetDialog.__init__)
        assert "layout.dialogs.presets" in source

    def test_recallpreset_uses_customlistview(self):
        """RecallPresetDialog must use CustomListView with id='custompresets'."""
        from SpinRender.ui.dialogs import RecallPresetDialog
        from SpinRender.ui.custom_controls import CustomListView
        import inspect

        source = inspect.getsource(RecallPresetDialog.build_ui)
        assert "CustomListView" in source
        assert "id=\"custompresets\"" in source or "id='custompresets'" in source


class TestNoManualTextStylesInDialogs:
    """Dialogs should not use manual TextStyle or hardcoded paddings."""

    def test_no_textstyle_usage(self):
        """Dialogs should not create TextStyle instances directly."""
        from SpinRender.ui import dialogs
        import inspect

        source = inspect.getsource(dialogs)
        # Should not contain TextStyle(
        assert "TextStyle(" not in source
        # Should not contain TextStyles(
        assert "TextStyles(" not in source

    def test_no_hardcoded_padding_values(self):
        """Dialog layouts should use theme tokens, not hardcoded wx.ALL, 24 etc."""
        from SpinRender.ui import dialogs
        import inspect

        source = inspect.getsource(dialogs)
        # Hardcoded padding patterns to avoid
        hardcoded_patterns = [
            "wx.ALL, 24",
            "wx.ALL, 16",
            "wx.ALL, 12",
            "wx.LEFT, 24",
            "wx.RIGHT, 24",
            "wx.TOP, 24",
            "wx.BOTTOM, 24"
        ]
        for pattern in hardcoded_patterns:
            assert pattern not in source, f"Found hardcoded padding: {pattern}"
