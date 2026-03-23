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
        value = self.theme._resolve("colors.primary")
        # Should resolve to a hex color string (via ref) or a ref dict
        # colors.primary is "@colors.cyan" which resolves to palette.cyan
        assert isinstance(value, (str, dict))

    def test_resolve_nested_token(self):
        """_resolve should traverse nested paths."""
        value = self.theme._resolve("typography.presets.body.size")
        assert value is not None

    def test_resolve_follows_ref(self):
        """_resolve should follow 'ref' keys recursively."""
        # text.body.color is "@colors.gray-white" which resolves to hex
        value = self.theme._resolve("text.body.color")
        assert isinstance(value, str)
        assert value.startswith("#") or value.startswith("rgba")

    def test_resolve_missing_token_returns_pink(self):
        """_resolve should return pink (#FF00FF) and log error for missing token."""
        result = self.theme._resolve("nonexistent.token.path")
        assert result == "#FF00FF"

    def test_resolve_circular_ref_would_infinite_loop(self):
        """_resolve should fail gracefully on circular ref (eventually max recursion).."""
        # Inject circular reference into data using string reference
        original_data = self.theme._data.copy()
        self.theme._data["test"] = "@test"  # circular reference via @ syntax
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
        # ColorMock is duck-typed; check for color methods
        assert hasattr(color, 'Red') and hasattr(color, 'Green') and hasattr(color, 'Blue')
        assert color.Red() == 255
        assert color.Green() == 107
        assert color.Blue() == 107

    def test_parse_hex_color_lowercase(self):
        """_parse_color should handle lowercase hex."""
        import wx
        color = self.theme._parse_color("#00bbd4")
        assert hasattr(color, 'Red') and hasattr(color, 'Green') and hasattr(color, 'Blue')
        assert color.Red() == 0
        assert color.Green() == 187
        assert color.Blue() == 212

    def test_parse_hex_no_hash(self):
        """_parse_color should accept hex without leading #."""
        import wx
        color = self.theme._parse_color("4CAF50")
        assert hasattr(color, 'Red') and hasattr(color, 'Green') and hasattr(color, 'Blue')
        assert color.Red() == 76
        assert color.Green() == 175
        assert color.Blue() == 80

    def test_parse_rgba(self):
        """_parse_color should parse rgba(r,g,b,a)."""
        import wx
        color = self.theme._parse_color("rgba(255,255,255,0.5)")
        assert hasattr(color, 'Red') and hasattr(color, 'Green') and hasattr(color, 'Blue') and hasattr(color, 'Alpha')
        assert color.Red() == 255
        assert color.Green() == 255
        assert color.Blue() == 255
        assert color.Alpha() == 128  # 0.5 * 255 = 127.5 ≈ 128

    def test_parse_rgba_with_decimals(self):
        """_parse_color should handle float alpha."""
        import wx
        color = self.theme._parse_color("rgba(0,0,0,0.0)")
        assert hasattr(color, 'Alpha')
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
        # Duck-typed check: result should have same RGB values
        assert result.Red() == original.Red()
        assert result.Green() == original.Green()
        assert result.Blue() == original.Blue()


class TestThemeColorAPI:
    """Test color() public API."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_color_returns_wx_color(self):
        """color(token) should return wx.Colour."""
        import wx
        color = self.theme.color("colors.primary")
        assert hasattr(color, 'Red') and hasattr(color, 'Green') and hasattr(color, 'Blue')

    def test_color_bg_tokens(self):
        """color() should resolve background tokens."""
        import wx
        # layout.main.frame.bg -> @colors.gray-black -> very low RGB
        bg_page = self.theme.color("layout.main.frame.bg")
        assert isinstance(bg_page, wx.Colour)
        # Dark theme: gray-black is #0D0D0D, very low RGB
        assert bg_page.Red() < 15
        assert bg_page.Green() < 15
        assert bg_page.Blue() < 15

    def test_color_text_tokens(self):
        """color() should resolve text color tokens."""
        import wx
        # text.body.color -> @colors.gray-white -> near white
        text_primary = self.theme.color("text.body.color")
        assert isinstance(text_primary, wx.Colour)
        # Dark theme: gray-white is #E0E0E0, very high RGB
        assert text_primary.Red() > 200
        assert text_primary.Green() > 200
        assert text_primary.Blue() > 200

    def test_color_border_tokens(self):
        """color() should resolve border tokens."""
        import wx
        border = self.theme.color("borders.default.color")
        assert isinstance(border, wx.Colour)


class TestThemeSizeAPI:
    """Test size() public API."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_size_returns_int(self):
        """size(token) should return int."""
        value = self.theme.size("typography.spacing.lg")
        assert isinstance(value, int)

    def test_size_spacing_tokens(self):
        """size() should resolve spacing tokens."""
        assert self.theme.size("typography.spacing.sm") == 6
        assert self.theme.size("typography.spacing.base") == 10
        assert self.theme.size("typography.spacing.md") == 16
        assert self.theme.size("typography.spacing.lg") == 24

    def test_size_typography_scale(self):
        """size() should resolve font size tokens."""
        assert self.theme.size("typography.scale.xs") == 7
        assert self.theme.size("typography.scale.base") == 11
        assert self.theme.size("typography.scale.md") == 14
        assert self.theme.size("typography.scale.xl") == 24


class TestThemeFontAPI:
    """Test font() public API."""

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")

    def test_font_returns_wx_font(self):
        """font(preset) should return wx.Font (or compatible mock)."""
        font = self.theme.font("body")
        # Should have methods to be font-like
        assert hasattr(font, 'GetFaceName') and hasattr(font, 'GetPointSize') and hasattr(font, 'GetWeight')

    def test_font_body_properties(self):
        """body font should be JetBrains Mono, 9px, normal (from text.body.font)."""
        font = self.theme.font("body")
        assert font.GetFaceName() == "JetBrains Mono"
        assert font.GetPointSize() == 9  # YAML: typography.scale.sm
        # text.body.font.weight = 400 maps to FONTWEIGHT_NORMAL
        assert font.GetWeight() == 400

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
        """dark.yaml must have colors, typography, radius, borders, components, viewport."""
        assert "colors" in self.theme._data
        assert "typography" in self.theme._data
        assert "radius" in self.theme._data
        assert "borders" in self.theme._data
        assert "components" in self.theme._data
        assert "viewport" in self.theme._data
        # theme does not have root-level 'palette' (uses colors.{name} instead)

    def test_all_color_tokens_resolve(self):
        """All color tokens used in UI should resolve without errors."""
        required_tokens = [
            "colors.cyan",
            "colors.yellow",
            "colors.green",
            "colors.orange",
            "colors.red",
            "colors.primary",
            "colors.secondary",
            "colors.ok",
            "colors.warning",
            "colors.error",
            "colors.gray-dark",
            "colors.gray-black",
            "colors.gray-border",
            "colors.gray-medium",
            "colors.gray-light",
            "colors.gray-text",
            "colors.gray-white",
            "colors.white",
            "colors.transparent",
        ]
        for token in required_tokens:
            try:
                color = self.theme.color(token)
                assert hasattr(color, 'Red') and hasattr(color, 'Green') and hasattr(color, 'Blue')
            except Exception as e:
                pytest.fail(f"Token '{token}' failed to resolve: {e}")

    def test_all_font_presets_resolve(self):
        """All font presets used in UI should resolve.

        theme uses global text.* roles, not individual named presets.
        TextStyles class builds fonts dynamically from font_family/font_size.
        """
        # font presets are defined in typography.presets
        # But the actual UI uses TextStyle that constructs fonts from families+scales
        # Test that the constituent parts exist:
        assert self.theme.font_family("mono") in ("JetBrains Mono", "mono")
        assert self.theme.font_family("display") == "Oswald"
        assert self.theme.font_family("icon") == "Material Design Icons"
        assert self.theme.font_size("base") == 11
        assert self.theme.font_size("md") == 14
        assert self.theme.font_size("xl") == 24
        assert self.theme.font_size("icon") == 16
        assert self.theme.font_size("icon-lg") == 20

    def test_all_spacing_tokens_resolve(self):
        """Spacing tokens should resolve to integers."""
        spacing_tokens = [
            "typography.spacing.none",
            "typography.spacing.sm",
            "typography.spacing.base",
            "typography.spacing.md",
            "typography.spacing.lg"
        ]
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

    def test_single_color_returns_four_states(self):
        """[normal] should auto-generate hover (+10), active (-10), and disabled (alpha)."""
        states = self.theme.color_states("colors.primary")
        assert len(states) == 4
        assert hasattr(states[0], 'Red') and hasattr(states[0], 'Green') and hasattr(states[0], 'Blue')
        base = self.theme.color("colors.primary")
        assert states[0].Red() == base.Red()
        # Generation depends on auto_states deltas in dark.yaml
        
    def test_rgba_preserves_alpha(self):
        """Alpha channel should be preserved across shifts."""
        import wx
        # gray-white is #E0E0E0
        color = self.theme._parse_color("#E0E0E0")
        shifted = self.theme._shift_color(color, 10)
        assert shifted.Alpha() == color.Alpha()

    def test_component_button_render(self):
        """components.button.render.frame.bg should have all four state colors."""
        states = self.theme.color_states("components.button.render.frame.bg")
        assert len(states) == 4
        for c in states:
            assert 0 <= c.Red() <= 255


class TestThemeV2Features:
    """Test theme-specific features: glyphs, text roles, scales.

    These tests are designed to run against theme YAMLs.
    In Phase 1, we test the new methods exist and handle missing tokens gracefully.
    In Phase 2+, full support for all theme features will be validated.
    """

    @pytest.fixture(autouse=True)
    def setup_theme(self):
        from SpinRender.core.theme import Theme
        self.theme = Theme.load("dark")  # Load the current theme

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
        # theme tokens
        assert self.theme.size("radius.sm") == 4
        assert self.theme.size("radius.md") == 6
        assert self.theme.size("borders.width.thin") == 1
        assert self.theme.size("borders.width.medium") == 2
        assert self.theme.size("typography.spacing.base") == 10
        assert self.theme.size("typography.scale.md") == 14

    def test_color_works_for_text_roles(self):
        """color() should resolve text.*.color tokens."""
        # text.title.color should resolve
        color = self.theme.color("text.title.color")
        assert hasattr(color, 'Red') and hasattr(color, 'Green') and hasattr(color, 'Blue')

    def test_has_token_method(self):
        """has_token() should correctly detect token existence."""
        assert self.theme.has_token("colors")
        assert self.theme.has_token("typography")
        assert not self.theme.has_token("nonexistent.xyz")
