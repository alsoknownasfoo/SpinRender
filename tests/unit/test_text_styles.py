#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Tests for TextStyle class and semantic font system."""
import pytest
import wx
from SpinRender.core.theme import Theme
_theme = Theme.current()

from SpinRender.ui.text_styles import TextStyle, TextStyles


@pytest.fixture
def wx_mock():
    """Provide access to the wx mock."""
    import sys
    return sys.modules['wx']


class TestTextStyle:
    """Test the TextStyle frozen dataclass."""

    def test_textstyle_creation(self):
        """Test TextStyle can be created with all fields."""
        color = _theme.color("text.body.color")  # primary text color
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=400,
            color=color,
            formatting=None
        )
        assert style.family == "JetBrains Mono"
        assert style.size == 11
        assert style.weight == 400
        assert style.color.Red() == color.Red() and style.color.Green() == color.Green() and style.color.Blue() == color.Blue()
        assert style.formatting is None

    def test_textstyle_minimal_creation(self):
        """Test TextStyle with only required fields (family, size, weight)."""
        style = TextStyle(
            family="Oswald",
            size=18,
            weight=700
        )
        assert style.family == "Oswald"
        assert style.size == 18
        assert style.weight == 700
        assert style.color is None
        assert style.formatting is None

    def test_textstyle_is_frozen(self):
        """Test that TextStyle instances are immutable."""
        color = _theme.color("text.body.color")  # primary text color
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=400,
            color=color
        )
        with pytest.raises((AttributeError, TypeError)):
            style.size = 12

    def test_textstyle_create_font_returns_wx_font(self):
        """Test .create_font() returns a wx.Font-compatible object."""
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=600
        )
        font = style.create_font()
        # Font should be an object with expected attributes
        assert hasattr(font, 'GetFaceName') and hasattr(font, 'GetPointSize')
        # The returned font is a FontMock; check its properties
        assert font.GetFaceName() == "JetBrains Mono"
        assert font.GetPointSize() == 11
        assert font.GetWeight() == 600

    def test_textstyle_create_font_with_italic(self):
        """Test .create_font() respects italic formatting."""
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=400,
            formatting="italic"
        )
        font = style.create_font()
        # FontMock stores the style; we can check it
        assert font._style == wx.FONTSTYLE_ITALIC
        assert font.GetFaceName() == "JetBrains Mono"

    def test_textstyle_format_text_uppercase(self):
        """Test .format_text() applies uppercase."""
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=400,
            formatting="uppercase"
        )
        result = style.format_text("Hello World")
        assert result == "HELLO WORLD"

    def test_textstyle_format_text_lowercase(self):
        """Test .format_text() applies lowercase."""
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=400,
            formatting="lowercase"
        )
        result = style.format_text("Hello World")
        assert result == "hello world"

    def test_textstyle_format_text_none(self):
        """Test .format_text() with no formatting returns unchanged."""
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=400,
            formatting=None
        )
        result = style.format_text("Hello World")
        assert result == "Hello World"

    def test_textstyle_format_text_unknown_passthrough(self):
        """Test .format_text() with unknown formatting returns unchanged."""
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=400,
            formatting="unknown"
        )
        result = style.format_text("Hello World")
        assert result == "Hello World"

    def test_textstyle_full_workflow(self):
        """Test complete TextStyle workflow: format text, create font."""
        color = _theme.color("colors.cyan")
        style = TextStyle(
            family="Oswald",
            size=18,
            weight=700,
            color=color,
            formatting="uppercase"
        )
        text = style.format_text("panel title")
        assert text == "PANEL TITLE"

        font = style.create_font()
        # Font should be created successfully
        assert font is not None


class TestTextStyles:
    """Test semantic token definitions in TextStyles class/namespace."""

    def test_body_token_exists(self):
        """Test body token is defined."""
        assert hasattr(TextStyles, 'body')
        style = TextStyles.body
        assert isinstance(style, TextStyle)
        assert style.family == _theme.font_family("mono")
        assert style.size == 9  # typography.scale.sm
        assert style.weight == 400

    def test_body_strong_token(self):
        """Test body-strong uses semibold weight."""
        style = TextStyles.body_strong
        assert style.weight == 600
        assert style.size == 9  # inherits body size (sm=9)
        assert style.family == _theme.font_family("mono")

    def test_label_sm_token(self):
        """Test label-sm uses header style (md=14, semibold)."""
        style = TextStyles.label_sm
        assert style.size == 14  # Maps to header: typography.scale.md
        assert style.weight == 600
        assert style.family == _theme.font_family("mono")

    def test_label_xs_token(self):
        """Test label-xs uses body style (sm=9, regular)."""
        style = TextStyles.label_xs
        assert style.size == 9  # Maps to body: typography.scale.sm
        assert style.weight == 400  # body weight
        assert style.family == _theme.font_family("mono")

    def test_numeric_value_token(self):
        """Test numeric-value uses numeric style (base=11, semibold)."""
        style = TextStyles.numeric_value
        # Note: numeric_value is not a defined alias, this test likely fails
        # Since there's no alias, _get_style falls back to body
        # We should either add alias or test the actual numeric token
        # For now, check what it actually resolves to
        assert style.size == 11  # numeric: typography.scale.base
        assert style.weight == 600
        assert style.family == _theme.font_family("mono")

    def test_numeric_unit_token(self):
        """Test numeric-unit uses body style (sm=9, regular)."""
        style = TextStyles.numeric_unit
        # Maps to body: typography.scale.sm
        assert style.size == 9
        assert style.weight == 400
        assert style.family == _theme.font_family("mono")

    def test_section_heading_token(self):
        """Test section-heading uses header style (mono, md=14, semibold, uppercase)."""
        style = TextStyles.section_heading
        # Maps to header: mono, size md=14, weight 600, uppercase
        assert style.family == _theme.font_family("mono")
        assert style.size == 14
        assert style.weight == 600
        assert style.formatting == "uppercase"

    def test_panel_title_token(self):
        """Test panel-title uses title style (display, lg=18, bold, uppercase)."""
        style = TextStyles.panel_title
        # Maps to title: display, size lg=18, weight 700, uppercase
        assert style.family == _theme.font_family("display")
        assert style.size == 18  # title uses lg, not xl
        assert style.weight == 700
        assert style.formatting == "uppercase"

    def test_icon_token(self):
        """Test icon uses MDI font at 14px (text.icon: typography.scale.md)."""
        style = TextStyles.icon
        assert style.family == _theme.font_family("icon")
        assert style.size == 14  # YAML: text.icon size = typography.scale.md

    def test_icon_lg_token(self):
        """Test icon-lg uses 18px size (typography.scale.lg)."""
        style = TextStyles.icon_lg
        assert style.size == 18  # YAML: text.icon_lg size = typography.scale.lg
        assert style.family == _theme.font_family("icon")

    def test_all_tokens_have_valid_sizes(self):
        """Test all semantic tokens have reasonable font sizes."""
        for name in dir(TextStyles):
            if not name.startswith('_'):
                attr = getattr(TextStyles, name)
                if isinstance(attr, TextStyle):
                    assert 6 <= attr.size <= 30, f"{name} has unreasonable size {attr.size}"
                    assert attr.weight in (400, 600, 700), f"{name} has invalid weight {attr.weight}"

    def test_all_tokens_have_valid_families(self):
        """Test all tokens use known font families."""
        mono = _theme.font_family("mono")
        icons = _theme.font_family("icon")
        display = _theme.font_family("display")
        valid_families = (mono, icons, display)
        for name in dir(TextStyles):
            if not name.startswith('_'):
                attr = getattr(TextStyles, name)
                if isinstance(attr, TextStyle):
                    assert attr.family in valid_families, f"{name} uses unknown family {attr.family}"
