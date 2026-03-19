#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for V2 theme migration — validates that V2 themes load and key tokens resolve.
"""
import pytest


class TestV2ThemeLoading:
    """Test that V2 themes load successfully."""

    @pytest.fixture(autouse=True)
    def reset_theme(self):
        from SpinRender.core.theme import Theme
        Theme._instance = None
        yield
        Theme._instance = None

    def test_dark_theme_loads(self):
        """V2 dark theme should load without errors."""
        from SpinRender.core.theme import Theme
        theme = Theme.load("dark")
        assert theme is not None
        assert Theme._instance is theme

    def test_light_theme_loads(self):
        """V2 light theme should load without errors."""
        from SpinRender.core.theme import Theme
        theme = Theme.load("light")
        assert theme is not None

    def test_theme_switching(self):
        """Loading dark then light should update singleton data."""
        from SpinRender.core.theme import Theme
        dark = Theme.load("dark")
        dark_primary = dark.color("colors.primary")
        # Force-load light theme
        light = Theme.load("light")
        light_primary = light.color("colors.primary")
        # Same instance
        assert dark is light
        # But colors should differ (dark primary is cyan, light primary likely something else)
        assert dark_primary.Red() != light_primary.Red() or dark_primary.Blue() != light_primary.Blue()

    def test_v2_color_tokens(self):
        """V2 theme should have colors.primary and colors.secondary."""
        from SpinRender.core.theme import Theme
        theme = Theme.load("dark")
        assert theme.has_token("colors")
        assert theme.has_token("colors.primary")
        assert theme.has_token("colors.secondary")
        primary = theme.color("colors.primary")
        import wx
        assert isinstance(primary, wx.Colour)

    def test_v2_radius_tokens(self):
        """V2 theme should have radius scale."""
        from SpinRender.core.theme import Theme
        theme = Theme.load("dark")
        assert theme.has_token("radius")
        md = theme.size("radius.md")
        assert md == 6

    def test_v2_glyphs_exist(self):
        """V2 theme should have glyphs section."""
        from SpinRender.core.theme import Theme
        theme = Theme.load("dark")
        assert theme.has_token("glyphs")
        assert theme.has_token("glyphs.render-action")
        glyph = theme.glyph("render-action")
        assert isinstance(glyph, str) and len(glyph) > 0

    def test_v2_text_roles(self):
        """V2 theme should have text.* roles."""
        from SpinRender.core.theme import Theme
        theme = Theme.load("dark")
        assert theme.has_token("text")
        assert theme.has_token("text.title")
        title_color = theme.color("text.title.color")
        import wx
        assert isinstance(title_color, wx.Colour)

    def test_v2_components(self):
        """V2 theme should have components. definitions."""
        from SpinRender.core.theme import Theme
        theme = Theme.load("dark")
        assert theme.has_token("components")
        assert theme.has_token("components.button.default")
        btn_bg = theme.color("components.button.default.bg")
        import wx
        assert isinstance(btn_bg, wx.Colour)

    def test_glyph_method_works(self):
        """Theme.glyph() should return a proper unicode glyph."""
        from SpinRender.core.theme import Theme
        theme = Theme.load("dark")
        # Test render-action is a Material Design Icon codepoint
        glyph = theme.glyph("render-action")
        # Should be a single Unicode char (or surrogate pair) but definitely non-empty
        assert len(glyph) >= 1
        # Could check that it's in the Private Use Area (PUA) range: 0xE000-0xF8FF
        # But at least ensure it's not the fallback empty string
        assert glyph != ""
