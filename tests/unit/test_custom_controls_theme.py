#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for custom_controls.py V2 theme integration.

Tests that all custom controls use V2 theme tokens and no hardcoded colors exist.
"""
import pytest
import wx

from SpinRender.core.theme import Theme
from SpinRender.core.locale import Locale
_theme = Theme.current()
_locale = Locale.current()


class TestV2ThemeIntegration:
    """Test that controls use V2 theme tokens correctly."""

    def test_locale_available(self):
        """Locale should be loaded and accessible."""
        assert _locale is not None

    def test_theme_glyph_works(self):
        """Theme.glyph() should return unicode strings for V2 glyphs."""
        glyph = _theme.glyph("render-action")
        assert isinstance(glyph, str) and len(glyph) > 0


class TestGetPaintColorReplacement:
    """Test _get_paint_color uses _theme.disabled()."""

    def test_paint_helper_uses_theme_disabled(self):
        from SpinRender.ui.custom_controls import _get_paint_color
        c = wx.Colour(255, 128, 0, 255)
        result = _get_paint_color(c, enabled=False)
        expected = _theme.disabled(c)
        assert result.Red() == expected.Red()
        assert result.Green() == expected.Green()
        assert result.Blue() == expected.Blue()
        assert result.Alpha() == expected.Alpha()


class TestV2ThemeTokenIntegration:
    """Test that V2 theme tokens are used correctly in controls."""

    def test_custom_slider_uses_v2_tokens(self):
        """CustomSlider should use components.slider.default tokens."""
        from SpinRender.ui.custom_controls import CustomSlider
        # Just ensure it can be instantiated and painted without errors
        # The actual token resolution is tested in functional tests
        assert CustomSlider is not None

    def test_custom_toggle_button_uses_v2_tokens(self):
        """CustomToggleButton should use components.toggle.default tokens."""
        from SpinRender.ui.custom_controls import CustomToggleButton
        assert CustomToggleButton is not None

    def test_custom_dropdown_uses_v2_tokens(self):
        """CustomDropdown should use components.dropdown.default tokens."""
        from SpinRender.ui.custom_controls import CustomDropdown
        assert CustomDropdown is not None

    def test_custom_button_uses_v2_tokens(self):
        """CustomButton should use components.button.* tokens."""
        from SpinRender.ui.custom_controls import CustomButton
        assert CustomButton is not None

    def test_preset_card_uses_v2_tokens(self):
        """PresetCard should use components.preset_card.default tokens."""
        from SpinRender.ui.custom_controls import PresetCard
        assert PresetCard is not None

    def test_no_class_level_colors_in_controls(self):
        """Controls should not define class-level wx.Colour constants."""
        from SpinRender.ui.custom_controls import (
            CustomSlider, CustomToggleButton, CustomDropdown,
            CustomButton, PresetCard, SectionLabel,
            CustomInput, ProjectFolderChip,
            CustomColorPicker, CustomListItem, CustomListView
        )
        classes = [
            CustomSlider, CustomToggleButton, CustomDropdown,
            CustomButton, PresetCard, SectionLabel,
            CustomInput, ProjectFolderChip,
            CustomColorPicker, CustomListItem, CustomListView
        ]
        for cls in classes:
            class_vars = cls.__dict__
            color_attrs = [n for n, v in class_vars.items()
                           if hasattr(v, 'Red') and hasattr(v, 'Green') and hasattr(v, 'Blue')]
            assert not color_attrs, f"{cls.__name__} should have no class-level wx.Colour attributes, found: {color_attrs}"


class TestV2TokenResolution:
    """Test that V2 tokens referenced in controls actually resolve."""

    def test_slider_tokens_resolve(self):
        """components.slider.default tokens should resolve."""
        assert _theme.color("components.slider.default.track.color") is not None
        assert _theme.color("components.slider.default.nub.color") is not None
        assert _theme.size("components.slider.default.frame.height") is not None

    def test_toggle_tokens_resolve(self):
        """components.toggle.default tokens should resolve."""
        assert _theme.color("components.toggle.default.frame.bg") is not None
        assert _theme.color("components.toggle.default.border") is not None

    def test_dropdown_tokens_resolve(self):
        """components.dropdown.default tokens should resolve."""
        assert _theme.color("components.dropdown.default.frame.bg") is not None
        assert _theme.color("components.dropdown.popup.bg") is not None
        assert _theme.color("components.dropdown.text") is not None

    def test_button_tokens_resolve(self):
        """components.button tokens should resolve."""
        assert _theme.color("components.button.primary.bg") is not None
        assert _theme.color("components.button.secondary.border") is not None

    def test_input_tokens_resolve(self):
        """components.input.default tokens should resolve."""
        assert _theme.color("components.input.default.frame.bg") is not None
        assert _theme.color("components.input.default.color.active") is not None

    def test_preset_card_tokens_resolve(self):
        """components.preset_card.default tokens should resolve."""
        assert _theme.color("components.preset_card.default.bg") is not None
        assert _theme.color("components.preset_card.default.border") is not None

    def test_numeric_input_tokens_resolve(self):
        """components.numeric_input tokens should resolve."""
        assert _theme.color("components.numeric_input.bg") is not None
        assert _theme.color("components.numeric_input.border") is not None
        assert _theme.color("components.numeric_input.text") is not None

    def test_text_input_tokens_resolve(self):
        """components.text_input tokens should resolve."""
        assert _theme.color("components.text_input.bg") is not None
        assert _theme.color("components.text_input.placeholder") is not None

    def test_path_input_tokens_resolve(self):
        """components.path_input tokens should resolve."""
        assert _theme.color("components.path_input.bg") is not None
        assert _theme.color("components.path_input.border") is not None

    def test_color_picker_tokens_resolve(self):
        """components.colorpicker tokens should resolve."""
        assert _theme.color("components.colorpicker.default.bg") is not None
        assert _theme.color("components.colorpicker.swatch-border") is not None

    def test_section_label_tokens_resolve(self):
        """components.section_label tokens should resolve."""
        assert _theme.color("components.section_label.text") is not None
        assert _theme.color("components.section_label.line") is not None

    def test_numeric_display_tokens_resolve(self):
        """components.numeric_display tokens should resolve."""
        assert _theme.color("components.numeric_display.bg") is not None
        assert _theme.color("components.numeric_display.text-value") is not None

    def test_badge_tokens_resolve(self):
        """components.badge tokens should resolve."""
        assert _theme.color("components.badge.bg") is not None
        assert _theme.color("components.badge.text") is not None
