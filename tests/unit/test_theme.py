#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for SpinRender.ui.theme module.

Tests all color constants, typography constants, and helper functions
using TDD methodology.
"""
import pytest


class TestThemeConstants:
    """Test that all required theme constants exist and have correct values."""

    def test_theme_module_exists(self):
        """Test that theme module can be imported."""
        from SpinRender.ui import theme
        assert theme is not None

    # ─────────────────────────────────────────────────────
    # Background Colors
    # ─────────────────────────────────────────────────────

    def test_bg_page_exists(self):
        """BG_PAGE constant must exist."""
        from SpinRender.ui.theme import BG_PAGE
        assert BG_PAGE is not None

    def test_bg_page_value(self):
        """BG_PAGE must be wx.Colour(18, 18, 18)."""
        import wx
        from SpinRender.ui.theme import BG_PAGE
        assert isinstance(BG_PAGE, wx.Colour)
        assert BG_PAGE.Red() == 18
        assert BG_PAGE.Green() == 18
        assert BG_PAGE.Blue() == 18
        assert BG_PAGE.Alpha() == 255

    def test_bg_panel_exists(self):
        """BG_PANEL constant must exist."""
        from SpinRender.ui.theme import BG_PANEL
        assert BG_PANEL is not None

    def test_bg_panel_value(self):
        """BG_PANEL must be wx.Colour(26, 26, 26)."""
        import wx
        from SpinRender.ui.theme import BG_PANEL
        assert isinstance(BG_PANEL, wx.Colour)
        assert BG_PANEL.Red() == 26
        assert BG_PANEL.Green() == 26
        assert BG_PANEL.Blue() == 26

    def test_bg_input_exists(self):
        """BG_INPUT constant must exist."""
        from SpinRender.ui.theme import BG_INPUT
        assert BG_INPUT is not None

    def test_bg_input_value(self):
        """BG_INPUT must be wx.Colour(13, 13, 13)."""
        import wx
        from SpinRender.ui.theme import BG_INPUT
        assert isinstance(BG_INPUT, wx.Colour)
        assert BG_INPUT.Red() == 13
        assert BG_INPUT.Green() == 13
        assert BG_INPUT.Blue() == 13

    def test_bg_surface_exists(self):
        """BG_SURFACE constant must exist."""
        from SpinRender.ui.theme import BG_SURFACE
        assert BG_SURFACE is not None

    def test_bg_surface_value(self):
        """BG_SURFACE must be wx.Colour(34, 34, 34)."""
        import wx
        from SpinRender.ui.theme import BG_SURFACE
        assert isinstance(BG_SURFACE, wx.Colour)
        assert BG_SURFACE.Red() == 34
        assert BG_SURFACE.Green() == 34
        assert BG_SURFACE.Blue() == 34

    def test_bg_modal_exists(self):
        """BG_MODAL constant must exist."""
        from SpinRender.ui.theme import BG_MODAL
        assert BG_MODAL is not None

    def test_bg_modal_value(self):
        """BG_MODAL must be wx.Colour(18, 18, 18) to unify with BG_PAGE."""
        import wx
        from SpinRender.ui.theme import BG_MODAL
        assert isinstance(BG_MODAL, wx.Colour)
        assert BG_MODAL.Red() == 18
        assert BG_MODAL.Green() == 18
        assert BG_MODAL.Blue() == 18

    # ─────────────────────────────────────────────────────
    # Text Colors
    # ─────────────────────────────────────────────────────

    def test_text_primary_exists(self):
        """TEXT_PRIMARY constant must exist."""
        from SpinRender.ui.theme import TEXT_PRIMARY
        assert TEXT_PRIMARY is not None

    def test_text_primary_value(self):
        """TEXT_PRIMARY must be wx.Colour(224, 224, 224)."""
        import wx
        from SpinRender.ui.theme import TEXT_PRIMARY
        assert isinstance(TEXT_PRIMARY, wx.Colour)
        assert TEXT_PRIMARY.Red() == 224
        assert TEXT_PRIMARY.Green() == 224
        assert TEXT_PRIMARY.Blue() == 224

    def test_text_secondary_exists(self):
        """TEXT_SECONDARY constant must exist."""
        from SpinRender.ui.theme import TEXT_SECONDARY
        assert TEXT_SECONDARY is not None

    def test_text_secondary_value(self):
        """TEXT_SECONDARY must be wx.Colour(119, 119, 119)."""
        import wx
        from SpinRender.ui.theme import TEXT_SECONDARY
        assert isinstance(TEXT_SECONDARY, wx.Colour)
        assert TEXT_SECONDARY.Red() == 119
        assert TEXT_SECONDARY.Green() == 119
        assert TEXT_SECONDARY.Blue() == 119

    def test_text_muted_exists(self):
        """TEXT_MUTED constant must exist."""
        from SpinRender.ui.theme import TEXT_MUTED
        assert TEXT_MUTED is not None

    def test_text_muted_value(self):
        """TEXT_MUTED must be wx.Colour(85, 85, 85)."""
        import wx
        from SpinRender.ui.theme import TEXT_MUTED
        assert isinstance(TEXT_MUTED, wx.Colour)
        assert TEXT_MUTED.Red() == 85
        assert TEXT_MUTED.Green() == 85
        assert TEXT_MUTED.Blue() == 85

    # ─────────────────────────────────────────────────────
    # Accent Colors
    # ─────────────────────────────────────────────────────

    def test_accent_cyan_exists(self):
        """ACCENT_CYAN constant must exist."""
        from SpinRender.ui.theme import ACCENT_CYAN
        assert ACCENT_CYAN is not None

    def test_accent_cyan_value(self):
        """ACCENT_CYAN must be wx.Colour(0, 188, 212)."""
        import wx
        from SpinRender.ui.theme import ACCENT_CYAN
        assert isinstance(ACCENT_CYAN, wx.Colour)
        assert ACCENT_CYAN.Red() == 0
        assert ACCENT_CYAN.Green() == 188
        assert ACCENT_CYAN.Blue() == 212

    def test_accent_yellow_exists(self):
        """ACCENT_YELLOW constant must exist."""
        from SpinRender.ui.theme import ACCENT_YELLOW
        assert ACCENT_YELLOW is not None

    def test_accent_yellow_value(self):
        """ACCENT_YELLOW must be wx.Colour(255, 214, 0)."""
        import wx
        from SpinRender.ui.theme import ACCENT_YELLOW
        assert isinstance(ACCENT_YELLOW, wx.Colour)
        assert ACCENT_YELLOW.Red() == 255
        assert ACCENT_YELLOW.Green() == 214
        assert ACCENT_YELLOW.Blue() == 0

    def test_accent_green_exists(self):
        """ACCENT_GREEN constant must exist."""
        from SpinRender.ui.theme import ACCENT_GREEN
        assert ACCENT_GREEN is not None

    def test_accent_green_value(self):
        """ACCENT_GREEN must be wx.Colour(76, 175, 80)."""
        import wx
        from SpinRender.ui.theme import ACCENT_GREEN
        assert isinstance(ACCENT_GREEN, wx.Colour)
        assert ACCENT_GREEN.Red() == 76
        assert ACCENT_GREEN.Green() == 175
        assert ACCENT_GREEN.Blue() == 80

    def test_accent_orange_exists(self):
        """ACCENT_ORANGE constant must exist."""
        from SpinRender.ui.theme import ACCENT_ORANGE
        assert ACCENT_ORANGE is not None

    def test_accent_orange_value(self):
        """ACCENT_ORANGE must be wx.Colour(255, 107, 53)."""
        import wx
        from SpinRender.ui.theme import ACCENT_ORANGE
        assert isinstance(ACCENT_ORANGE, wx.Colour)
        assert ACCENT_ORANGE.Red() == 255
        assert ACCENT_ORANGE.Green() == 107
        assert ACCENT_ORANGE.Blue() == 53

    # ─────────────────────────────────────────────────────
    # Border Colors
    # ─────────────────────────────────────────────────────

    def test_border_default_exists(self):
        """BORDER_DEFAULT constant must exist."""
        from SpinRender.ui.theme import BORDER_DEFAULT
        assert BORDER_DEFAULT is not None

    def test_border_default_value(self):
        """BORDER_DEFAULT must be wx.Colour(31, 31, 31)."""
        import wx
        from SpinRender.ui.theme import BORDER_DEFAULT
        assert isinstance(BORDER_DEFAULT, wx.Colour)
        assert BORDER_DEFAULT.Red() == 31
        assert BORDER_DEFAULT.Green() == 31
        assert BORDER_DEFAULT.Blue() == 31

    def test_border_modal_exists(self):
        """BORDER_MODAL constant must exist."""
        from SpinRender.ui.theme import BORDER_MODAL
        assert BORDER_MODAL is not None

    def test_border_modal_value(self):
        """BORDER_MODAL must be wx.Colour(51, 51, 51)."""
        import wx
        from SpinRender.ui.theme import BORDER_MODAL
        assert isinstance(BORDER_MODAL, wx.Colour)
        assert BORDER_MODAL.Red() == 51
        assert BORDER_MODAL.Green() == 51
        assert BORDER_MODAL.Blue() == 51

    # ─────────────────────────────────────────────────────
    # Disabled State
    # ─────────────────────────────────────────────────────

    def test_disabled_alpha_exists(self):
        """DISABLED_ALPHA constant must exist and equal 128."""
        from SpinRender.ui.theme import DISABLED_ALPHA
        assert DISABLED_ALPHA == 128

    # ─────────────────────────────────────────────────────
    # Typography
    # ─────────────────────────────────────────────────────

    def test_font_mono_exists(self):
        """FONT_MONO constant must exist."""
        from SpinRender.ui.theme import FONT_MONO
        assert FONT_MONO is not None

    def test_font_mono_value(self):
        """FONT_MONO must equal 'JetBrains Mono'."""
        from SpinRender.ui.theme import FONT_MONO
        assert FONT_MONO == "JetBrains Mono"

    def test_font_icons_exists(self):
        """FONT_ICONS constant must exist."""
        from SpinRender.ui.theme import FONT_ICONS
        assert FONT_ICONS is not None

    def test_font_icons_value(self):
        """FONT_ICONS must equal 'Material Design Icons'."""
        from SpinRender.ui.theme import FONT_ICONS
        assert FONT_ICONS == "Material Design Icons"

    def test_font_display_exists(self):
        """FONT_DISPLAY constant must exist."""
        from SpinRender.ui.theme import FONT_DISPLAY
        assert FONT_DISPLAY is not None

    def test_font_display_value(self):
        """FONT_DISPLAY must equal 'Oswald'."""
        from SpinRender.ui.theme import FONT_DISPLAY
        assert FONT_DISPLAY == "Oswald"

    # ─────────────────────────────────────────────────────
    # Helper Functions
    # ─────────────────────────────────────────────────────

    def test_disabled_function_exists(self):
        """disabled() helper function must exist."""
        from SpinRender.ui.theme import disabled
        assert callable(disabled)

    def test_disabled_returns_colour_with_alpha(self):
        """disabled(color) must return a wx.Colour with alpha=128."""
        import wx
        from SpinRender.ui.theme import disabled, DISABLED_ALPHA

        original = wx.Colour(255, 128, 0, 255)
        result = disabled(original)

        assert isinstance(result, wx.Colour)
        assert result.Red() == 255
        assert result.Green() == 128
        assert result.Blue() == 0
        assert result.Alpha() == DISABLED_ALPHA

    def test_disabled_does_not_mutate_original(self):
        """disabled() must not modify the input colour."""
        import wx
        from SpinRender.ui.theme import disabled

        original = wx.Colour(255, 128, 0, 255)
        original_alpha = original.Alpha()

        disabled(original)

        # Verify original alpha unchanged
        assert original.Alpha() == original_alpha

    def test_disabled_handles_various_colors(self):
        """disabled() must work with any RGB value."""
        import wx
        from SpinRender.ui.theme import disabled, DISABLED_ALPHA

        test_colors = [
            wx.Colour(255, 255, 255),
            wx.Colour(0, 0, 0),
            wx.Colour(128, 64, 192),
            wx.Colour(18, 18, 18),
        ]

        for color in test_colors:
            result = disabled(color)
            assert result.Red() == color.Red()
            assert result.Green() == color.Green()
            assert result.Blue() == color.Blue()
            assert result.Alpha() == DISABLED_ALPHA


class TestThemeUniqueness:
    """Test that all color constants have unique RGB values."""

    def test_all_colors_are_unique(self):
        """All color constants must have distinct RGB combinations, with one intentional exception: BG_MODAL == BG_PAGE (unification)."""
        import wx
        from SpinRender.ui.theme import (
            BG_PAGE, BG_PANEL, BG_INPUT, BG_SURFACE, BG_MODAL,
            TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
            ACCENT_CYAN, ACCENT_YELLOW, ACCENT_GREEN, ACCENT_ORANGE,
            BORDER_DEFAULT, BORDER_MODAL,
        )

        all_colors = [
            ('BG_PAGE', BG_PAGE),
            ('BG_PANEL', BG_PANEL),
            ('BG_INPUT', BG_INPUT),
            ('BG_SURFACE', BG_SURFACE),
            ('BG_MODAL', BG_MODAL),
            ('TEXT_PRIMARY', TEXT_PRIMARY),
            ('TEXT_SECONDARY', TEXT_SECONDARY),
            ('TEXT_MUTED', TEXT_MUTED),
            ('ACCENT_CYAN', ACCENT_CYAN),
            ('ACCENT_YELLOW', ACCENT_YELLOW),
            ('ACCENT_GREEN', ACCENT_GREEN),
            ('ACCENT_ORANGE', ACCENT_ORANGE),
            ('BORDER_DEFAULT', BORDER_DEFAULT),
            ('BORDER_MODAL', BORDER_MODAL),
        ]

        # Build a set of RGB tuples
        rgb_values = []
        for name, color in all_colors:
            rgb = (color.Red(), color.Green(), color.Blue(), color.Alpha())
            rgb_values.append((name, rgb))

        # Check for duplicates, but allow BG_MODAL == BG_PAGE as intentional unification
        seen = {}
        duplicates = []
        for name, rgb in rgb_values:
            if rgb in seen:
                # Allow BG_MODAL and BG_PAGE to be the same (unification per migration strategy)
                pair = (seen[rgb], name)
                if pair != ('BG_MODAL', 'BG_PAGE') and pair != ('BG_PAGE', 'BG_MODAL'):
                    duplicates.append(f"'{name}' and '{seen[rgb]}' both have RGB{rgb}")
            else:
                seen[rgb] = name

        if duplicates:
            pytest.fail(f"Duplicate color values found (excluding intentional BG_MODAL==BG_PAGE):\n  " + "\n  ".join(duplicates))


class TestThemeModuleStructure:
    """Test the theme module's structure and documentation."""

    def test_theme_has_docstring(self):
        """theme module must have a docstring."""
        import SpinRender.ui.theme as theme
        assert theme.__doc__ is not None
        assert len(theme.__doc__.strip()) > 0

    def test_theme_imports_wx(self):
        """theme module must import wx."""
        import SpinRender.ui.theme as theme
        # Verify wx is imported in the module
        assert hasattr(theme, 'wx') or 'wx' in theme.__dict__
