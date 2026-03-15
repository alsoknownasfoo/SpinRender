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
    """Test that font constants use theme.FONT_* instead of local definitions."""

    def test_no_local_font_constants(self):
        """Local constants _JETBRAINS_MONO, _MDI_FONT_FAMILY, _OSWALD must be removed."""
        from SpinRender.ui import custom_controls

        # These should NOT exist as independent local font string constants
        # They should either be removed or aliased to theme values
        # We check that they are not defined as string literals in the module
        if hasattr(custom_controls, '_JETBRAINS_MONO'):
            val = getattr(custom_controls, '_JETBRAINS_MONO')
            # If it exists, it must be equal to theme.FONT_MONO (aliased)
            from SpinRender.ui.theme import FONT_MONO
            assert val == FONT_MONO, f"_JETBRAINS_MONO should be aliased to theme.FONT_MONO"

        if hasattr(custom_controls, '_MDI_FONT_FAMILY'):
            val = getattr(custom_controls, '_MDI_FONT_FAMILY')
            from SpinRender.ui.theme import FONT_ICONS
            assert val == FONT_ICONS, f"_MDI_FONT_FAMILY should be aliased to theme.FONT_ICONS"

        if hasattr(custom_controls, '_OSWALD'):
            val = getattr(custom_controls, '_OSWALD')
            from SpinRender.ui.theme import FONT_DISPLAY
            assert val == FONT_DISPLAY, f"_OSWALD should be aliased to theme.FONT_DISPLAY"

    def test_get_custom_font_uses_theme_fonts(self):
        """get_custom_font() must use theme.FONT_* constants, not local strings."""
        from SpinRender.ui import custom_controls
        from SpinRender.ui.theme import FONT_MONO, FONT_ICONS, FONT_DISPLAY

        # Call get_custom_font with default mono font
        font_default = custom_controls.get_custom_font(size=12)
        assert font_default.GetFaceName() == FONT_MONO

        # Call with MDI font
        font_mdi = custom_controls.get_custom_font(size=14, family_name=FONT_ICONS)
        assert font_mdi.GetFaceName() == FONT_ICONS

        # Call with display font
        font_display = custom_controls.get_custom_font(size=16, family_name=FONT_DISPLAY)
        assert font_display.GetFaceName() == FONT_DISPLAY

    def test_get_mdi_font_uses_theme_icons(self):
        """get_mdi_font() must use theme.FONT_ICONS."""
        from SpinRender.ui import custom_controls
        from SpinRender.ui.theme import FONT_ICONS

        font = custom_controls.get_mdi_font(size=14)
        assert font.GetFaceName() == FONT_ICONS


class TestGetPaintColorReplacement:
    """Test that _get_paint_color() is replaced with theme.disabled()."""

    def test_paint_color_helper_removed_or_aliased(self):
        """_get_paint_color should be removed or wrapped to use theme.disabled()."""
        from SpinRender.ui import custom_controls
        from SpinRender.ui.theme import disabled as theme_disabled

        if hasattr(custom_controls, '_get_paint_color'):
            func = getattr(custom_controls, '_get_paint_color')
            # If it exists, it must internally call theme.disabled()
            # We can't easily test internal implementation, but we can test behavior
            color = wx.Colour(255, 128, 0, 255)
            result = func(color, enabled=False)
            expected = theme_disabled(color)
            assert result.Red() == expected.Red()
            assert result.Green() == expected.Green()
            assert result.Blue() == expected.Blue()
            assert result.Alpha() == expected.Alpha()


class TestNoHardcodedColors:
    """Test that custom_controls.py contains NO hardcoded wx.Colour() calls."""

    def test_custom_slider_uses_theme_colors(self):
        """CustomSlider must use theme.BG_SURFACE for track and theme.ACCENT_CYAN for handle."""
        from SpinRender.ui.custom_controls import CustomSlider
        from SpinRender.ui.theme import BG_SURFACE, ACCENT_CYAN

        slider = CustomSlider(None, value=50)
        # The hardcoded colors should be replaced by theme constants.
        # We can't directly inspect the Class-level constants after migration,
        # but we can check that the class no longer defines its own wx.Colour constants
        # except potentially as aliases to theme.
        # Check: the TRACK_COLOR and any color constants should equal theme values

        # After migration, CustomSlider should NOT have wx.Colour in its class attrs
        for attr_name in dir(CustomSlider):
            attr_val = getattr(CustomSlider, attr_name)
            if isinstance(attr_val, wx.Colour):
                # If a wx.Colour constant exists, it must be from theme (same reference or equal value)
                # We can verify it matches a known theme color
                theme_match = False
                for theme_name, theme_color in [('BG_SURFACE', BG_SURFACE), ('ACCENT_CYAN', ACCENT_CYAN)]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"CustomSlider.{attr_name} is a wx.Colour not matching any theme color"

    def test_custom_toggle_button_uses_theme_colors(self):
        """CustomToggleButton must use theme colors."""
        from SpinRender.ui.custom_controls import CustomToggleButton
        from SpinRender.ui.theme import BG_SURFACE, ACCENT_CYAN, TEXT_PRIMARY, TEXT_SECONDARY

        # Check that any wx.Colour class attributes match theme colors
        for attr_name in dir(CustomToggleButton):
            attr_val = getattr(CustomToggleButton, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [BG_SURFACE, ACCENT_CYAN, TEXT_PRIMARY, TEXT_SECONDARY]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"CustomToggleButton.{attr_name} is a wx.Colour not matching any theme color"

    def test_custom_dropdown_uses_theme_colors(self):
        """CustomDropdown must use theme.BG_INPUT, theme.BORDER_DEFAULT, theme.TEXT_PRIMARY."""
        from SpinRender.ui.custom_controls import CustomDropdown
        from SpinRender.ui.theme import BG_INPUT, BORDER_DEFAULT, TEXT_PRIMARY

        for attr_name in dir(CustomDropdown):
            attr_val = getattr(CustomDropdown, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [BG_INPUT, BORDER_DEFAULT, TEXT_PRIMARY]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"CustomDropdown.{attr_name} is a wx.Colour not matching any theme color"

    def test_dropdown_popup_uses_theme_colors(self):
        """DropdownPopup must use theme.BG_INPUT, theme.BORDER_DEFAULT, theme.TEXT_PRIMARY, theme.TEXT_MUTED."""
        from SpinRender.ui.custom_controls import DropdownPopup
        from SpinRender.ui.theme import BG_INPUT, BORDER_DEFAULT, TEXT_PRIMARY, TEXT_MUTED

        for attr_name in dir(DropdownPopup):
            attr_val = getattr(DropdownPopup, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [BG_INPUT, BORDER_DEFAULT, TEXT_PRIMARY, TEXT_MUTED]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"DropdownPopup.{attr_name} is a wx.Colour not matching any theme color"

    def test_custom_button_uses_theme_colors(self):
        """CustomButton must use theme.ACCENT_CYAN, theme.BORDER_DEFAULT, theme.ACCENT_ORANGE."""
        from SpinRender.ui.custom_controls import CustomButton
        from SpinRender.ui.theme import ACCENT_CYAN, BORDER_DEFAULT, ACCENT_ORANGE

        for attr_name in dir(CustomButton):
            attr_val = getattr(CustomButton, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [ACCENT_CYAN, BORDER_DEFAULT, ACCENT_ORANGE]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"CustomButton.{attr_name} is a wx.Colour not matching any theme color"

    def test_preset_card_uses_theme_colors(self):
        """PresetCard must use theme.BG_SURFACE, theme.ACCENT_CYAN, theme.TEXT_PRIMARY."""
        from SpinRender.ui.custom_controls import PresetCard
        from SpinRender.ui.theme import BG_SURFACE, ACCENT_CYAN, TEXT_PRIMARY

        for attr_name in dir(PresetCard):
            attr_val = getattr(PresetCard, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [BG_SURFACE, ACCENT_CYAN, TEXT_PRIMARY]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"PresetCard.{attr_name} is a wx.Colour not matching any theme color"

    def test_section_label_uses_theme_colors(self):
        """SectionLabel must use theme.TEXT_SECONDARY and theme.BORDER_DEFAULT."""
        from SpinRender.ui.custom_controls import SectionLabel
        from SpinRender.ui.theme import TEXT_SECONDARY, BORDER_DEFAULT

        for attr_name in dir(SectionLabel):
            attr_val = getattr(SectionLabel, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [TEXT_SECONDARY, BORDER_DEFAULT]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"SectionLabel.{attr_name} is a wx.Colour not matching any theme color"

    def test_numeric_display_uses_theme_colors(self):
        """NumericDisplay must use theme.BG_INPUT and theme.TEXT_PRIMARY."""
        from SpinRender.ui.custom_controls import NumericDisplay
        from SpinRender.ui.theme import BG_INPUT, TEXT_PRIMARY

        for attr_name in dir(NumericDisplay):
            attr_val = getattr(NumericDisplay, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [BG_INPUT, TEXT_PRIMARY]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"Numer icDisplay.{attr_name} is a wx.Colour not matching any theme color"

    def test_numeric_input_uses_theme_colors(self):
        """NumericInput must use theme.BG_INPUT, theme.ACCENT_CYAN, theme.TEXT_PRIMARY."""
        from SpinRender.ui.custom_controls import NumericInput
        from SpinRender.ui.theme import BG_INPUT, ACCENT_CYAN, TEXT_PRIMARY

        for attr_name in dir(NumericInput):
            attr_val = getattr(NumericInput, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [BG_INPUT, ACCENT_CYAN, TEXT_PRIMARY]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"NumericInput.{attr_name} is a wx.Colour not matching any theme color"

    def test_custom_text_input_uses_theme_colors(self):
        """CustomTextInput must use theme.BG_INPUT, theme.TEXT_MUTED, theme.TEXT_PRIMARY."""
        from SpinRender.ui.custom_controls import CustomTextInput
        from SpinRender.ui.theme import BG_INPUT, TEXT_MUTED, TEXT_PRIMARY

        for attr_name in dir(CustomTextInput):
            attr_val = getattr(CustomTextInput, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [BG_INPUT, TEXT_MUTED, TEXT_PRIMARY]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"CustomTextInput.{attr_name} is a wx.Colour not matching any theme color"

    def test_project_folder_chip_uses_theme_colors(self):
        """ProjectFolderChip must use theme.ACCENT_ORANGE and theme.BG_PAGE."""
        from SpinRender.ui.custom_controls import ProjectFolderChip
        from SpinRender.ui.theme import ACCENT_ORANGE, BG_PAGE

        for attr_name in dir(ProjectFolderChip):
            attr_val = getattr(ProjectFolderChip, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [ACCENT_ORANGE, BG_PAGE]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"ProjectFolderChip.{attr_name} is a wx.Colour not matching any theme color"

    def test_custom_color_picker_uses_theme_colors(self):
        """CustomColorPicker must use theme.BORDER_DEFAULT and theme.BG_INPUT."""
        from SpinRender.ui.custom_controls import CustomColorPicker
        from SpinRender.ui.theme import BORDER_DEFAULT, BG_INPUT

        for attr_name in dir(CustomColorPicker):
            attr_val = getattr(CustomColorPicker, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [BORDER_DEFAULT, BG_INPUT]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"CustomColorPicker.{attr_name} is a wx.Colour not matching any theme color"

    def test_path_input_control_uses_theme_colors(self):
        """PathInputControl must use theme.BG_INPUT and theme.TEXT_SECONDARY."""
        from SpinRender.ui.custom_controls import PathInputControl
        from SpinRender.ui.theme import BG_INPUT, TEXT_SECONDARY

        for attr_name in dir(PathInputControl):
            attr_val = getattr(PathInputControl, attr_name)
            if isinstance(attr_val, wx.Colour):
                theme_match = False
                for theme_color in [BG_INPUT, TEXT_SECONDARY]:
                    if attr_val.Red() == theme_color.Red() and attr_val.Green() == theme_color.Green() and attr_val.Blue() == theme_color.Blue():
                        theme_match = True
                        break
                assert theme_match, f"PathInputControl.{attr_name} is a wx.Colour not matching any theme color"
