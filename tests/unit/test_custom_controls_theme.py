#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for custom_controls.py theme migration.

Tests that all custom controls use theme constants instead of local definitions
and hardcoded wx.Colour values.

TDD Phases:
- RED: Tests fail because custom_controls.py still uses local fonts and hardcoded colors
- GREEN: Modify custom_controls.py to use theme.* constants
- REFACTOR: Clean up and ensure consistency
"""
import pytest
import wx


class TestFontMigration:
    def test_no_local_font_constants(self):
        from SpinRender.ui import custom_controls
        from SpinRender.ui.theme import FONT_MONO, FONT_ICONS, FONT_DISPLAY

        # Font family constants should still exist for backward compatibility
        if hasattr(custom_controls, '_JETBRAINS_MONO'):
            assert getattr(custom_controls, '_JETBRAINS_MONO') == FONT_MONO
        if hasattr(custom_controls, '_MDI_FONT_FAMILY'):
            assert getattr(custom_controls, '_MDI_FONT_FAMILY') == FONT_ICONS
        if hasattr(custom_controls, '_OSWALD'):
            assert getattr(custom_controls, '_OSWALD') == FONT_DISPLAY

    def test_deprecated_font_functions_removed(self):
        """After migration, get_custom_font and get_mdi_font should no longer exist."""
        from SpinRender.ui import custom_controls
        assert not hasattr(custom_controls, 'get_custom_font'), "get_custom_font should be removed after migration"
        assert not hasattr(custom_controls, 'get_mdi_font'), "get_mdi_font should be removed after migration"


class TestGetPaintColorReplacement:
    def test_paint_helper_uses_theme_disabled(self):
        from SpinRender.ui import custom_controls
        from SpinRender.ui.theme import disabled as theme_disabled

        if hasattr(custom_controls, '_get_paint_color'):
            fn = getattr(custom_controls, '_get_paint_color')
            c = wx.Colour(255, 128, 0, 255)
            result = fn(c, enabled=False)
            expected = theme_disabled(c)
            assert result.Red() == expected.Red()
            assert result.Green() == expected.Green()
            assert result.Blue() == expected.Blue()
            assert result.Alpha() == expected.Alpha()


class TestNoHardcodedColors:
    """Verify class-level colour constants are only theme aliases and match exactly."""

    def _check(self, cls, expected):
        """
        expected: dict mapping attribute name to expected theme colour.
        Ensures the class has exactly these colour attributes and they match.
        """
        class_vars = cls.__dict__
        # Get all attribute names that look like colours (have Red/Green/Blue methods)
        found = []
        for name, val in class_vars.items():
            if hasattr(val, 'Red') and hasattr(val, 'Green') and hasattr(val, 'Blue'):
                found.append(name)
        expected_set = set(expected.keys())
        if set(found) != expected_set:
            pytest.fail(f"{cls.__name__}: expected colour attrs {expected_set}, found {set(found)}")
        for name, exp in expected.items():
            val = class_vars[name]
            if not (val.Red() == exp.Red() and val.Green() == exp.Green() and val.Blue() == exp.Blue()):
                pytest.fail(f"{cls.__name__}.{name} does not match theme colour")

    def test_custom_slider(self):
        from SpinRender.ui.custom_controls import CustomSlider
        from SpinRender.ui.theme import BG_SURFACE
        self._check(CustomSlider, {'TRACK_COLOR': BG_SURFACE})

    def test_custom_toggle_button(self):
        from SpinRender.ui.custom_controls import CustomToggleButton
        from SpinRender.ui.theme import BG_SURFACE, ACCENT_CYAN, TEXT_PRIMARY
        self._check(CustomToggleButton, {
            'BG_COLOR': BG_SURFACE,
            'TEXT_PRIMARY': TEXT_PRIMARY,
            'DEFAULT_ACTIVE_BG': ACCENT_CYAN,
        })

    def test_custom_dropdown(self):
        from SpinRender.ui.custom_controls import CustomDropdown
        from SpinRender.ui.theme import BG_INPUT, BORDER_DEFAULT, TEXT_PRIMARY
        self._check(CustomDropdown, {
            'BG_COLOR': BG_INPUT,
            'BORDER_COLOR': BORDER_DEFAULT,
            'TEXT_PRIMARY': TEXT_PRIMARY,
        })

    def test_dropdown_popup_has_no_colour_attrs(self):
        from SpinRender.ui.custom_controls import DropdownPopup
        class_vars = DropdownPopup.__dict__
        colour_attrs = [n for n, v in class_vars.items()
                       if hasattr(v, 'Red') and hasattr(v, 'Green') and hasattr(v, 'Blue')]
        assert not colour_attrs, f"DropdownPopup should have no class-level colours: {colour_attrs}"

    def test_custom_button_has_no_colour_attrs(self):
        from SpinRender.ui.custom_controls import CustomButton
        class_vars = CustomButton.__dict__
        colour_attrs = [n for n, v in class_vars.items()
                       if hasattr(v, 'Red') and hasattr(v, 'Green') and hasattr(v, 'Blue')]
        assert not colour_attrs, f"CustomButton should have no class-level colours: {colour_attrs}"

    def test_preset_card(self):
        from SpinRender.ui.custom_controls import PresetCard
        from SpinRender.ui.theme import BG_SURFACE
        self._check(PresetCard, {'BG_COLOR': BG_SURFACE})

    def test_section_label(self):
        from SpinRender.ui.custom_controls import SectionLabel
        from SpinRender.ui.theme import TEXT_SECONDARY, BORDER_DEFAULT
        self._check(SectionLabel, {
            'TEXT_COLOR': TEXT_SECONDARY,
            'LINE_COLOR': BORDER_DEFAULT,
        })

    def test_numeric_display(self):
        from SpinRender.ui.custom_controls import NumericDisplay
        from SpinRender.ui.theme import BG_INPUT
        self._check(NumericDisplay, {'BG_COLOR': BG_INPUT})

    def test_numeric_input(self):
        from SpinRender.ui.custom_controls import NumericInput
        from SpinRender.ui.theme import BG_INPUT, ACCENT_CYAN, TEXT_PRIMARY
        self._check(NumericInput, {
            'BG_COLOR': BG_INPUT,
            'BORDER_FOCUS': ACCENT_CYAN,
            'VALUE_EDIT': TEXT_PRIMARY,
        })

    def test_custom_text_input(self):
        from SpinRender.ui.custom_controls import CustomTextInput
        from SpinRender.ui.theme import BG_INPUT, TEXT_MUTED, TEXT_PRIMARY
        self._check(CustomTextInput, {
            'BG_COLOR': BG_INPUT,
            'TEXT_COLOR': TEXT_PRIMARY,
            'PLACEHOLDER_COLOR': TEXT_MUTED,
        })

    def test_project_folder_chip_has_no_colour_attrs(self):
        from SpinRender.ui.custom_controls import ProjectFolderChip
        class_vars = ProjectFolderChip.__dict__
        colour_attrs = [n for n, v in class_vars.items()
                       if hasattr(v, 'Red') and hasattr(v, 'Green') and hasattr(v, 'Blue')]
        assert not colour_attrs, f"ProjectFolderChip should have no class-level colours: {colour_attrs}"

    def test_custom_color_picker(self):
        from SpinRender.ui.custom_controls import CustomColorPicker
        from SpinRender.ui.theme import BORDER_DEFAULT, BG_INPUT
        self._check(CustomColorPicker, {
            'BORDER_COLOR': BORDER_DEFAULT,
            'BG_INPUT': BG_INPUT,
        })

    def test_path_input_control(self):
        from SpinRender.ui.custom_controls import PathInputControl
        from SpinRender.ui.theme import BG_INPUT, TEXT_SECONDARY
        self._check(PathInputControl, {
            'BG_COLOR': BG_INPUT,
            'TEXT_COLOR': TEXT_SECONDARY,
        })
