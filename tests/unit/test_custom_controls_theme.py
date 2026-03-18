#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for custom_controls.py theme migration.

Tests that all custom controls use theme tokens instead of local definitions
and hardcoded wx.Colour values.
"""
import pytest
import wx

from SpinRender.core.theme import Theme
_theme = Theme.current()


class TestFontMigration:
    """Test that module-level font constants use Theme.font_family()."""

    def test_jetbrains_mono_matches_theme_mono(self):
        """_JETBRAINS_MONO should equal theme's mono font family."""
        from SpinRender.ui.custom_controls import _JETBRAINS_MONO
        assert _JETBRAINS_MONO == _theme.font_family("mono")

    def test_mdi_font_family_matches_theme_icon(self):
        """_MDI_FONT_FAMILY should equal theme's icon font family."""
        from SpinRender.ui.custom_controls import _MDI_FONT_FAMILY
        assert _MDI_FONT_FAMILY == _theme.font_family("icon")

    def test_oswald_matches_theme_display(self):
        """_OSWALD should equal theme's display font family."""
        from SpinRender.ui.custom_controls import _OSWALD
        assert _OSWALD == _theme.font_family("display")


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


class TestNoHardcodedColors:
    """Verify class-level color constants are only theme aliases and match exactly."""

    def _check(self, cls, expected_attrs):
        """
        expected_attrs: dict mapping attribute name to expected color (from _theme.color()).
        Ensures the class has exactly these color attributes and they match.
        """
        class_vars = cls.__dict__
        found = []
        for name, val in class_vars.items():
            if hasattr(val, 'Red') and hasattr(val, 'Green') and hasattr(val, 'Blue'):
                found.append(name)
        expected_set = set(expected_attrs.keys())
        if set(found) != expected_set:
            pytest.fail(f"{cls.__name__}: expected color attrs {expected_set}, found {set(found)}")
        for name, exp in expected_attrs.items():
            val = class_vars[name]
            if not (val.Red() == exp.Red() and val.Green() == exp.Green() and val.Blue() == exp.Blue()):
                pytest.fail(f"{cls.__name__}.{name} does not match theme color")

    def test_custom_slider(self):
        from SpinRender.ui.custom_controls import CustomSlider
        self._check(CustomSlider, {'TRACK_COLOR': _theme.color("colors.bg.surface")})

    def test_custom_toggle_button(self):
        from SpinRender.ui.custom_controls import CustomToggleButton
        self._check(CustomToggleButton, {
            'BG_COLOR': _theme.color("colors.bg.surface"),
            'TEXT_PRIMARY': _theme.color("colors.text.primary"),
            'DEFAULT_ACTIVE_BG': _theme.color("colors.accent.primary"),
        })

    def test_custom_dropdown(self):
        from SpinRender.ui.custom_controls import CustomDropdown
        self._check(CustomDropdown, {
            'BG_COLOR': _theme.color("colors.bg.input"),
            'BORDER_COLOR': _theme.color("colors.border.default"),
            'TEXT_PRIMARY': _theme.color("colors.text.primary"),
        })

    def test_dropdown_popup_has_no_color_attrs(self):
        from SpinRender.ui.custom_controls import DropdownPopup
        class_vars = DropdownPopup.__dict__
        color_attrs = [n for n, v in class_vars.items()
                       if hasattr(v, 'Red') and hasattr(v, 'Green') and hasattr(v, 'Blue')]
        assert not color_attrs, f"DropdownPopup should have no class-level colors: {color_attrs}"

    def test_custom_button_has_no_color_attrs(self):
        from SpinRender.ui.custom_controls import CustomButton
        class_vars = CustomButton.__dict__
        color_attrs = [n for n, v in class_vars.items()
                       if hasattr(v, 'Red') and hasattr(v, 'Green') and hasattr(v, 'Blue')]
        assert not color_attrs, f"CustomButton should have no class-level colors: {color_attrs}"

    def test_preset_card(self):
        from SpinRender.ui.custom_controls import PresetCard
        self._check(PresetCard, {'BG_COLOR': _theme.color("colors.bg.surface")})

    def test_section_label(self):
        from SpinRender.ui.custom_controls import SectionLabel
        self._check(SectionLabel, {
            'TEXT_COLOR': _theme.color("colors.text.secondary"),
            'LINE_COLOR': _theme.color("colors.border.default"),
        })

    def test_numeric_display(self):
        from SpinRender.ui.custom_controls import NumericDisplay
        self._check(NumericDisplay, {'BG_COLOR': _theme.color("colors.bg.input")})

    def test_numeric_input(self):
        from SpinRender.ui.custom_controls import NumericInput
        self._check(NumericInput, {
            'BG_COLOR': _theme.color("colors.bg.input"),
            'BORDER_FOCUS': _theme.color("colors.accent.primary"),
            'VALUE_EDIT': _theme.color("colors.text.primary"),
        })

    def test_custom_text_input(self):
        from SpinRender.ui.custom_controls import CustomTextInput
        self._check(CustomTextInput, {
            'BG_COLOR': _theme.color("colors.bg.input"),
            'TEXT_COLOR': _theme.color("colors.text.primary"),
            'PLACEHOLDER_COLOR': _theme.color("colors.text.muted"),
        })

    def test_project_folder_chip_has_no_color_attrs(self):
        from SpinRender.ui.custom_controls import ProjectFolderChip
        class_vars = ProjectFolderChip.__dict__
        color_attrs = [n for n, v in class_vars.items()
                       if hasattr(v, 'Red') and hasattr(v, 'Green') and hasattr(v, 'Blue')]
        assert not color_attrs, f"ProjectFolderChip should have no class-level colors: {color_attrs}"

    def test_custom_color_picker(self):
        from SpinRender.ui.custom_controls import CustomColorPicker
        self._check(CustomColorPicker, {
            'BORDER_COLOR': _theme.color("colors.border.default"),
            'BG_INPUT': _theme.color("colors.bg.input"),
        })

    def test_path_input_control(self):
        from SpinRender.ui.custom_controls import PathInputControl
        self._check(PathInputControl, {
            'BG_COLOR': _theme.color("colors.bg.input"),
            'TEXT_COLOR': _theme.color("colors.text.secondary"),
        })
