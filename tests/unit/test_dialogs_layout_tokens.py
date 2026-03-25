#!/usr/bin/env python3
"""
Tests for dialog layout token integration.

Verify that dialogs use layout.dialogs tokens instead of hardcoded values.
"""
import inspect
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

        source = inspect.getsource(RecallPresetDialog.build_ui)
        assert "CustomListView" in source
        assert "id=\"custompresets\"" in source or "id='custompresets'" in source

    def test_about_dialog_uses_height_autosize_and_parent_centering(self):
        """AboutSpinRenderDialog should autosize height from content and center on its parent."""
        from SpinRender.ui.dialogs import AboutSpinRenderDialog

        source = inspect.getsource(AboutSpinRenderDialog.__init__)
        assert "layout.dialogs.about.frame.height" in source
        assert 'super().__init__(parent, "SPINRENDER", (w, h))' in source
        assert "self.autosize_dialog_height(max_height=h)" in source
        assert "self.center_over_parent()" in source

    def test_about_sections_match_version_vertical_padding(self):
        """Author, links, and license sections should reuse the version section top/bottom padding."""
        from SpinRender.ui.dialogs import AboutSpinRenderDialog

        source = inspect.getsource(AboutSpinRenderDialog.build_ui)
        assert 'self._padded_section(content, self._build_version_section,  16, 16, 16, 16)' in source
        assert 'self._padded_section(content, self._build_author_ai_section, 16, 16, 16, 16)' in source
        assert 'self._padded_section(content, self._build_links_section,     16, 16, 16, 16)' in source
        assert 'self._padded_section(content, self._build_license_section,   16, 16, 16, 16, outer_bg="colors.gray-black", show_divider=False)' in source

    def test_base_dialog_exposes_modal_layout_helpers(self):
        """BaseStyledDialog should expose shared helpers for modal sizing and centering."""
        source = inspect.getsource(BaseStyledDialog)
        assert "def autosize_dialog_height" in source
        assert "max_height=None" in source
        assert "def center_over_parent" in source

    def test_about_dialog_uses_icon_spinner_progress(self):
        """AboutSpinRenderDialog should animate update progress by rotating the resting icon."""
        from SpinRender.ui.dialogs import AboutSpinRenderDialog

        source = inspect.getsource(AboutSpinRenderDialog)
        assert "self._update_rotation = 0" in source
        assert "self._closing = False" in source
        assert "def _update_progress_label" in source
        assert 'self.upd_btn.SetIcon("cw")' in source
        assert "self.upd_btn.SetIconRotation(self._update_rotation)" in source
        assert "self._update_timer.Start(75)" in source
        assert 'self.upd_btn.SetLabel(f"CHECKING' not in source
        assert "def _stop_update_timer" in source
        assert "def _on_destroy" in source

    def test_about_license_copy_is_vertically_centered(self):
        """About license copy should be vertically centered against the donate button row."""
        from SpinRender.ui.dialogs import AboutSpinRenderDialog

        source = inspect.getsource(AboutSpinRenderDialog._build_license_section)
        assert "copy_wrap.SetMinSize((-1, card_h))" in source
        assert "copy_sizer.AddStretchSpacer()" in source

    def test_custom_button_supports_icon_rotation(self):
        """CustomButton should support rotating the same icon without changing glyph or size."""
        from SpinRender.ui.custom_controls import CustomButton

        source = inspect.getsource(CustomButton)
        assert "self.icon_rotation_degrees = 0" in source
        assert "gc.Rotate(_math.radians(self.icon_rotation_degrees))" in source
        assert "def SetIconRotation(self, degrees)" in source


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


class TestCreateFooterHelper:
    """BaseStyledDialog.create_footer must exist and dialogs must use it."""

    def test_create_footer_method_exists(self):
        """BaseStyledDialog must have a create_footer method."""
        from SpinRender.ui.dialogs import BaseStyledDialog
        assert hasattr(BaseStyledDialog, 'create_footer')
        assert callable(BaseStyledDialog.create_footer)

    def test_create_footer_uses_proportion_one(self):
        """When btn1_prop/btn2_prop are None, buttons use proportion=1."""
        from SpinRender.ui.dialogs import BaseStyledDialog
        import inspect

        source = inspect.getsource(BaseStyledDialog.create_footer)
        # None case defaults to prop1=prop2=1
        assert "prop1 = 1" in source and "prop2 = 1" in source
        # Buttons added with prop1, prop2
        assert "footer_sizer.Add(btn1, prop1)" in source
        assert "footer_sizer.Add(btn2, prop2)" in source

    def test_create_footer_has_divider_line(self):
        """create_footer must include a 1px divider panel at the top."""
        from SpinRender.ui.dialogs import BaseStyledDialog
        import inspect

        source = inspect.getsource(BaseStyledDialog.create_footer)
        assert 'size=(-1, 1)' in source
        assert 'borders.default.color' in source

    def test_create_footer_has_vertical_padding(self):
        """create_footer must add top and bottom spacers around the buttons."""
        from SpinRender.ui.dialogs import BaseStyledDialog
        import inspect

        source = inspect.getsource(BaseStyledDialog.create_footer)
        assert "pad['top']" in source
        assert "pad['bottom']" in source

    def test_create_footer_has_gap_and_proportions(self):
        """create_footer must accept gap, btn1_prop, btn2_prop parameters."""
        import inspect
        from SpinRender.ui.dialogs import BaseStyledDialog

        sig = inspect.signature(BaseStyledDialog.create_footer)
        params = list(sig.parameters.keys())
        assert 'padding' in params
        assert 'gap' in params
        assert 'btn1_prop' in params
        assert 'btn2_prop' in params

    def test_create_footer_proportions_add_stretch_when_sum_lt_100(self):
        """When btn1_prop + btn2_prop < 100, create_footer adds left stretch spacer."""
        from SpinRender.ui.dialogs import BaseStyledDialog
        import inspect

        source = inspect.getsource(BaseStyledDialog.create_footer)
        assert 'left_stretch' in source or 'AddStretchSpacer' in source
        assert '100 - total' in source

    def test_filename_dialog_uses_create_footer(self):
        """FilenameEntryDialog.build_ui must compute proportions from theme and pass to create_footer."""
        from SpinRender.ui.dialogs import FilenameEntryDialog
        import inspect

        source = inspect.getsource(FilenameEntryDialog.build_ui)
        assert "create_footer" in source
        assert "gap=gap" in source
        assert 'layout.dialogs.filename.controls.button1.width' in source
        assert 'layout.dialogs.filename.controls.button2.width' in source
        assert "btn1_prop=prop1" in source
        assert "btn2_prop=prop2" in source

    def test_advanced_options_dialog_uses_create_footer(self):
        """AdvancedOptionsDialog must pass btn1_prop=25, btn2_prop=25 and resolve gap."""
        from SpinRender.ui.dialogs import AdvancedOptionsDialog
        import inspect

        source = inspect.getsource(AdvancedOptionsDialog.build_ui)
        assert "create_footer" in source
        assert "btn1_prop=25" in source
        assert "btn2_prop=25" in source
        assert 'layout.dialogs.options.controls.gap' in source
        assert 'gap=footer_gap' in source

    def test_save_preset_dialog_uses_create_footer(self):
        """SavePresetDialog must compute proportions from theme, resolve gap, and pass to create_footer."""
        from SpinRender.ui.dialogs import SavePresetDialog
        import inspect

        source = inspect.getsource(SavePresetDialog.build_ui)
        assert "create_footer" in source
        assert 'layout.dialogs.addpreset.controls.button1.width' in source
        assert 'layout.dialogs.addpreset.controls.button2.width' in source
        assert "btn1_prop=prop1" in source
        assert "btn2_prop=prop2" in source
        assert 'layout.dialogs.addpreset.controls.gap' in source
        assert 'gap=footer_gap' in source


class TestDialogFocusRestorePatterns:
    """Modal callers should restore plugin focus after closing dialogs."""

    def test_main_panel_restores_focus_after_advanced_options(self):
        """SpinRenderPanel should restore focus after the advanced options modal closes."""
        source = Path("SpinRender/ui/main_panel.py").read_text()
        assert "def restore_plugin_focus(self):" in source
        assert "self.restore_plugin_focus()" in source
        assert "pf.Raise()" in source
        assert "self.SetFocus()" in source

    def test_about_dialog_reuses_main_panel_focus_restore(self):
        """ControlsSidePanel should open About with the main panel as parent and restore focus."""
        from SpinRender.ui.controls_side_panel import ControlsSidePanel

        dialog = MagicMock()
        with patch("SpinRender.ui.dialogs.AboutSpinRenderDialog", return_value=dialog) as dialog_cls:
            panel = ControlsSidePanel.__new__(ControlsSidePanel)
            panel.main_panel = MagicMock()

            ControlsSidePanel.on_about(panel, None)

        dialog_cls.assert_called_once_with(panel.main_panel)
        dialog.ShowModal.assert_called_once_with()
        dialog.Destroy.assert_called_once_with()
        panel.main_panel.restore_plugin_focus.assert_called_once_with()
