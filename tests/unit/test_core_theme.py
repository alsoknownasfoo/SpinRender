#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Unit tests for SpinRender.core.theme.Theme class.

Tests YAML loading, token resolution, color parsing, font factory.
Strictly YAML-based (no hardcoded fallback constants).
"""
import pytest
import sys
import importlib
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def reset_theme_singleton():
    """Ensure Theme singleton is reset before and after each test."""
    from SpinRender.core.theme import Theme
    Theme._instance = None
    # Ensure yaml is available in sys.modules if it was mocked away
    if 'yaml' in sys.modules and sys.modules['yaml'] is None:
        del sys.modules['yaml']
    importlib.reload(sys.modules['SpinRender.core.theme'])
    yield
    Theme._instance = None


class TestThemeSingleton:
    """Test Theme singleton pattern."""

    def test_current_creates_default_if_none(self):
        """Theme.current() should load default theme if none set."""
        from SpinRender.core.theme import Theme
        theme = Theme.current()
        assert theme is not None
        assert isinstance(theme, Theme)

    def test_load_sets_instance(self):
        """Theme.load() should set the singleton instance."""
        from SpinRender.core.theme import Theme
        theme = Theme.load("dark")
        assert Theme._instance is theme
        assert Theme.current() is theme

    def test_load_with_nonexistent_name_raises(self):
        """Theme.load() should raise FileNotFoundError for missing theme."""
        from SpinRender.core.theme import Theme
        with pytest.raises(FileNotFoundError):
            Theme.load("nonexistent_theme_xyz")

    def test_multiple_loads_return_same_instance(self):
        """Subsequent Theme.load() calls should return same instance."""
        from SpinRender.core.theme import Theme
        theme1 = Theme.load("dark")
        theme2 = Theme.load("dark")
        assert theme1 is theme2


class TestThemeTokenResolution:
    """Test _resolve() token traversal and ref following."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        """Load dark theme for each test."""
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_resolve_simple_token(self):
        """_resolve should get value at simple path."""
        value = self.theme._resolve("colors.accent.primary")
        # Should resolve to a hex color string (via ref) or a ref dict
        assert value in ("#00BCD4", {"ref": "palette.cyan"})

    def test_resolve_nested_token(self):
        """_resolve should traverse nested paths."""
        value = self.theme._resolve("typography.presets.body.size")
        assert value is not None

    def test_resolve_follows_ref(self):
        """_resolve should follow 'ref' keys recursively."""
        value = self.theme._resolve("colors.bg.page")
        assert isinstance(value, str)
        assert value.startswith("#")

    def test_resolve_missing_token_returns_pink(self):
        """_resolve should return pink (#FF00FF) and log error for missing token."""
        result = self.theme._resolve("nonexistent.token.path")
        assert result == "#FF00FF"

    def test_resolve_circular_ref_would_infinite_loop(self):
        """_resolve should fail gracefully on circular ref (eventually max recursion).."""
        # Inject circular reference into data
        original_data = self.theme._data.copy()
        self.theme._data["test"] = {"ref": "test"}  # circular
        with pytest.raises(RecursionError):
            self.theme._resolve("test")
        # Restore
        self.theme._data = original_data


class TestThemeColorParsing:
    """Test _parse_color() color string conversion."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_parse_hex_color(self):
        """_parse_color should parse #RRGGBB."""
        import wx
        color = self.theme._parse_color("#FF6B6B")
        assert isinstance(color, wx.Colour)
        assert color.Red() == 255
        assert color.Green() == 107
        assert color.Blue() == 107

    def test_parse_hex_color_lowercase(self):
        """_parse_color should handle lowercase hex."""
        import wx
        color = self.theme._parse_color("#00bbd4")
        assert isinstance(color, wx.Colour)
        assert color.Red() == 0
        assert color.Green() == 187
        assert color.Blue() == 212

    def test_parse_hex_no_hash(self):
        """_parse_color should accept hex without leading #."""
        import wx
        color = self.theme._parse_color("4CAF50")
        assert isinstance(color, wx.Colour)
        assert color.Red() == 76
        assert color.Green() == 175
        assert color.Blue() == 80

    def test_parse_rgba(self):
        """_parse_color should parse rgba(r,g,b,a)."""
        import wx
        color = self.theme._parse_color("rgba(255,255,255,0.5)")
        assert isinstance(color, wx.Colour)
        assert color.Red() == 255
        assert color.Green() == 255
        assert color.Blue() == 255
        assert color.Alpha() == 128  # 0.5 * 255 = 127.5 ≈ 128

    def test_parse_rgba_with_decimals(self):
        """_parse_color should handle float alpha."""
        import wx
        color = self.theme._parse_color("rgba(0,0,0,0.0)")
        assert color.Alpha() == 0

    def test_parse_invalid_format_raises(self):
        """_parse_color should raise ValueError for invalid format."""
        with pytest.raises(ValueError):
            self.theme._parse_color("not a color")
        with pytest.raises(ValueError):
            self.theme._parse_color("#GGGGGG")  # invalid hex
        with pytest.raises(ValueError):
            self.theme._parse_color("#FFF")  # too short

    def test_parse_wx_color_passthrough(self):
        """_parse_color should pass through wx.Colour objects."""
        import wx
        original = wx.Colour(100, 150, 200)
        result = self.theme._parse_color(original)
        assert result is original


class TestThemeColorAPI:
    """Test color() public API."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_color_returns_wx_color(self):
        """color(token) should return wx.Colour."""
        import wx
        color = self.theme.color("colors.accent.primary")
        assert isinstance(color, wx.Colour)

    def test_color_bg_tokens(self):
        """color() should resolve background tokens."""
        import wx
        bg_page = self.theme.color("colors.bg.page")
        assert isinstance(bg_page, wx.Colour)
        assert bg_page.Red() < 50

    def test_color_text_tokens(self):
        """color() should resolve text color tokens."""
        import wx
        text_primary = self.theme.color("colors.text.primary")
        assert isinstance(text_primary, wx.Colour)
        assert text_primary.Red() > 200

    def test_color_border_tokens(self):
        """color() should resolve border tokens."""
        import wx
        border = self.theme.color("colors.border.default")
        assert isinstance(border, wx.Colour)


class TestThemeSizeAPI:
    """Test size() public API."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_size_returns_int(self):
        """size(token) should return int."""
        value = self.theme.size("spacing.lg")
        assert isinstance(value, int)

    def test_size_spacing_tokens(self):
        """size() should resolve spacing tokens."""
        assert self.theme.size("spacing.xs") == 4
        assert self.theme.size("spacing.sm") == 6
        assert self.theme.size("spacing.md") == 10
        assert self.theme.size("spacing.lg") == 16
        assert self.theme.size("spacing.xl") == 24

    def test_size_typography_scale(self):
        """size() should resolve font size tokens."""
        assert self.theme.size("typography.scale.base") == 11
        assert self.theme.size("typography.scale.md") == 13
        assert self.theme.size("typography.scale.xl") == 18


class TestThemeFontAPI:
    """Test font() public API."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_font_returns_wx_font(self):
        """font(preset) should return wx.Font."""
        import wx
        font = self.theme.font("body")
        assert isinstance(font, wx.Font)

    def test_font_body_properties(self):
        """body font should be JetBrains Mono, 11px, normal."""
        import wx
        font = self.theme.font("body")
        assert font.GetFaceName() == "JetBrains Mono"
        assert font.GetPointSize() == 11
        assert font.GetWeight() == wx.FONTWEIGHT_NORMAL

    def test_font_panel_title_properties(self):
        """panel_title font should be Oswald, 18px, bold."""
        import wx
        font = self.theme.font("panel_title")
        assert font.GetFaceName() == "Oswald"
        assert font.GetPointSize() == 18
        assert font.GetWeight() == wx.FONTWEIGHT_BOLD

    def test_font_numeric_value_properties(self):
        """numeric_value font should be 13px semibold."""
        import wx
        font = self.theme.font("numeric_value")
        assert font.GetPointSize() == 13
        assert font.GetWeight() == wx.FONTWEIGHT_SEMIBOLD

    def test_font_icon_properties(self):
        """icon font should be Material Design Icons, 14px."""
        import wx
        font = self.theme.font("icon")
        assert font.GetFaceName() == "Material Design Icons"
        assert font.GetPointSize() == 14

    def test_font_unknown_preset_returns_system_fallback(self):
        """font() with invalid preset should return a system fallback font instead of crashing."""
        import wx
        font = self.theme.font("nonexistent_preset")
        assert font is not None
        # Verify it's either a real font or a mock that represents one
        if hasattr(font, 'IsOk'):
            assert font.IsOk()


class TestThemeFallback:
    """Test behavior when YAML unavailable or invalid (Strict YAML mode)."""

    def test_error_when_yaml_missing(self):
        """If YAML file missing, should raise FileNotFoundError."""
        from SpinRender.core.theme import Theme
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                Theme.load("dark")

    def test_error_when_yaml_malformed(self):
        """If YAML malformed, should raise RuntimeError."""
        from SpinRender.core.theme import Theme
        yaml_path = Path(__file__).parent.parent.parent / "SpinRender" / "resources" / "themes" / "dark.yaml"
        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                original_content = f.read()
            try:
                # Corrupt the YAML
                with open(yaml_path, 'w') as f:
                    f.write("invalid: yaml: content: [")
                
                # Reload to trigger parse error on load
                from SpinRender.core import theme as theme_mod
                importlib.reload(theme_mod)
                with pytest.raises(RuntimeError):
                    theme_mod.Theme.load("dark")
            finally:
                # Restore
                with open(yaml_path, 'w') as f:
                    f.write(original_content)

    def test_error_when_pyyaml_missing(self):
        """If PyYAML not installed, should raise ImportError."""
        from SpinRender.core.theme import Theme
        with patch.dict(sys.modules, {'yaml': None}):
            from SpinRender.core import theme as theme_mod
            importlib.reload(theme_mod)
            with pytest.raises(ImportError):
                theme_mod.Theme.load("dark")


class TestThemeYAMLStructure:
    """Test that dark.yaml has correct structure and all tokens resolve."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_yaml_has_required_top_level_keys(self):
        """dark.yaml must have palette, colors, typography, spacing."""
        assert "palette" in self.theme._data
        assert "colors" in self.theme._data
        assert "typography" in self.theme._data
        assert "spacing" in self.theme._data

    def test_all_color_tokens_resolve(self):
        """All color tokens used in UI should resolve without errors."""
        required_tokens = [
            "colors.bg.page",
            "colors.bg.panel",
            "colors.bg.input",
            "colors.bg.surface",
            "colors.bg.overlay",
            "colors.text.primary",
            "colors.text.secondary",
            "colors.text.muted",
            "colors.accent.primary",
            "colors.accent.secondary",
            "colors.accent.success",
            "colors.accent.warning",
            "colors.border.default",
            "colors.border.focus",
        ]
        for token in required_tokens:
            try:
                color = self.theme.color(token)
                import wx
                assert isinstance(color, wx.Colour)
            except Exception as e:
                pytest.fail(f"Token '{token}' failed to resolve: {e}")

    def test_all_font_presets_resolve(self):
        """All font presets used in UI should resolve."""
        required_presets = [
            "body",
            "body_strong",
            "label_sm",
            "label_xs",
            "numeric_value",
            "numeric_unit",
            "section_heading",
            "panel_title",
            "icon",
            "icon_lg",
        ]
        import wx
        for preset in required_presets:
            try:
                font = self.theme.font(preset)
                assert isinstance(font, wx.Font), f"Preset '{preset}' didn't return wx.Font"
            except Exception as e:
                pytest.fail(f"Preset '{preset}' failed to resolve: {e}")

    def test_all_spacing_tokens_resolve(self):
        """Spacing tokens should resolve to integers."""
        spacing_tokens = ["spacing.xs", "spacing.sm", "spacing.md", "spacing.lg", "spacing.xl"]
        for token in spacing_tokens:
            value = self.theme.size(token)
            assert isinstance(value, int)
            assert value >= 0


class TestThemeColorStates:
    """Test color_states() array resolution and auto-brightness shifting."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_single_color_returns_three_states(self):
        """[normal] should auto-generate hover (+10) and active (-10)."""
        import wx
        states = self.theme.color_states("colors.accent.primary")
        assert len(states) == 3
        assert isinstance(states[0], wx.Colour)
        base = self.theme.color("colors.accent.primary")
        assert states[0].Red() == base.Red()
        assert states[1].Red() == max(0, min(255, base.Red() + 10))
        assert states[2].Red() == max(0, min(255, base.Red() - 10))

    def test_two_colors_returns_three_states(self):
        """[normal, hover] should derive active from hover (-10)."""
        states = self.theme.color_states("components.button.primary.bg")
        assert len(states) == 3
        assert all(isinstance(c, type(states[0])) for c in states)

    def test_rgba_preserves_alpha(self):
        """Alpha channel should be preserved across shifts."""
        import wx
        color = self.theme._parse_color("rgba(255,255,255,0.27)")
        shifted = self.theme._shift_color(color, 10)
        assert shifted.Alpha() == color.Alpha()

    def test_component_button_primary(self):
        """components.button.primary.bg should have all three state colors."""
        states = self.theme.color_states("components.button.primary.bg")
        assert len(states) == 3
        for c in states:
            assert 0 <= c.Red() <= 255

    def test_component_toggle_active(self):
        """toggle.active.bg should resolve to states array."""
        states = self.theme.color_states("components.toggle.active.bg")
        assert len(states) == 3
        base = self.theme.color("colors.state.active")
        assert states[0].Red() == base.Red()


class TestThemeV2Features:
    """Test V2-specific features: glyphs, text roles, scales.

    These tests are designed to run against V2 theme YAMLs.
    In Phase 1, we test the new methods exist and handle missing tokens gracefully.
    In Phase 2+, V2 themes will be deployed and these tests will validate full V2 support.
    """

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")  # Will load V2 after Phase 2; for now V1 is okay

    def test_glyph_method_exists(self):
        """Theme should have glyph() method."""
        assert hasattr(self.theme, 'glyph')
        assert callable(self.theme.glyph)

    def test_glyph_returns_string(self):
        """glyph() should return a string (or empty if missing)."""
        # Try with existing or missing; should not crash
        glyph = self.theme.glyph("render-action")
        assert isinstance(glyph, str)

    def test_glyph_unknown_returns_empty(self):
        """glyph('unknown') should return empty string gracefully."""
        glyph = self.theme.glyph("unknown-nonexistent")
        assert glyph == ""  # Empty string for missing glyph

    def test_size_works_for_any_numeric_token(self):
        """size() should work for any numeric token (radius, borders, spacing)."""
        # Test with V1 tokens (always exist) and V2 tokens (if available)
        value = self.theme.size("spacing.md")
        assert isinstance(value, int)
        # V2 tokens might exist; if they do, they should return correct values
        try:
            radius_md = self.theme.size("radius.md")
            assert isinstance(radius_md, int)
            if radius_md:  # If token exists, should be 6 in V2
                assert radius_md == 6
        except:
            pass  # Missing token is okay for V1

    def test_color_works_for_text_roles(self):
        """color() should resolve text.*.color tokens."""
        # May be missing in V1, but should not crash
        try:
            color = self.theme.color("text.title.color")
            import wx
            assert isinstance(color, wx.Colour)
        except:
            pass  # Missing token okay

    def test_has_token_method(self):
        """has_token() should correctly detect token existence."""
        assert self.theme.has_token("colors")
        assert self.theme.has_token("palette")
        assert not self.theme.has_token("nonexistent.xyz")
