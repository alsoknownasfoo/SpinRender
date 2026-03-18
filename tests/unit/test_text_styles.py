#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Tests for TextStyle class and semantic font system."""
import pytest
from unittest.mock import MagicMock
import sys

# Mock wx before SpinRender imports
wx_mock = MagicMock()
wx_mock.FONTWEIGHT_NORMAL = 400
wx_mock.FONTWEIGHT_SEMIBOLD = 600
wx_mock.FONTWEIGHT_BOLD = 700
wx_mock.FONTSTYLE_NORMAL = 0
wx_mock.FONTSTYLE_ITALIC = 1
wx_mock.FONTFAMILY_DEFAULT = 0
sys.modules['wx'] = wx_mock

from SpinRender.core.theme import Theme
_theme = Theme.current()

from SpinRender.ui.text_styles import TextStyle, TextStyles


class TestTextStyle:
    """Test the TextStyle frozen dataclass."""

    def test_textstyle_creation(self):
        """Test TextStyle can be created with all fields."""
        color = _theme.color("colors.text.primary")
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
        color = _theme.color("colors.text.primary")
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=400,
            color=color
        )
        with pytest.raises((AttributeError, TypeError)):
            style.size = 12

    def test_textstyle_create_font_returns_wx_font(self):
        """Test .create_font() calls wx.Font with correct args."""
        wx_mock.Font.reset_mock()
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=600
        )
        font = style.create_font()
        assert isinstance(font, MagicMock)
        wx_mock.Font.assert_called_once_with(11, wx_mock.FONTFAMILY_DEFAULT, wx_mock.FONTSTYLE_NORMAL, 600, faceName="JetBrains Mono")

    def test_textstyle_create_font_with_italic(self):
        """Test .create_font() respects italic formatting."""
        wx_mock.Font.reset_mock()
        style = TextStyle(
            family="JetBrains Mono",
            size=11,
            weight=400,
            formatting="italic"
        )
        font = style.create_font()
        wx_mock.Font.assert_called_once_with(11, wx_mock.FONTFAMILY_DEFAULT, wx_mock.FONTSTYLE_ITALIC, 400, faceName="JetBrains Mono")

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
        color = _theme.color("colors.accent.cyan")
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
        assert wx_mock.Font.called


class TestTextStyles:
    """Test semantic token definitions in TextStyles class/namespace."""

    def test_body_token_exists(self):
        """Test body token is defined."""
        assert hasattr(TextStyles, 'body')
        style = TextStyles.body
        assert isinstance(style, TextStyle)
        assert style.family == _theme.font_family("mono")
        assert style.size == 11
        assert style.weight == 400

    def test_body_strong_token(self):
        """Test body-strong uses semibold weight."""
        style = TextStyles.body_strong
        assert style.weight == 600
        assert style.size == 11
        assert style.family == _theme.font_family("mono")

    def test_label_sm_token(self):
        """Test label-sm uses small size and semibold."""
        style = TextStyles.label_sm
        assert style.size == 9
        assert style.weight == 600
        assert style.family == _theme.font_family("mono")

    def test_label_xs_token(self):
        """Test label-xs uses extra small size and bold."""
        style = TextStyles.label_xs
        assert style.size == 8
        assert style.weight == 700
        assert style.family == _theme.font_family("mono")

    def test_numeric_value_token(self):
        """Test numeric-value uses medium size and semibold."""
        style = TextStyles.numeric_value
        assert style.size == 13
        assert style.weight == 600
        assert style.family == _theme.font_family("mono")

    def test_numeric_unit_token(self):
        """Test numeric-unit uses base size."""
        style = TextStyles.numeric_unit
        assert style.size == 11
        assert style.weight == 400
        assert style.family == _theme.font_family("mono")

    def test_section_heading_token(self):
        """Test section-heading uses Oswald, medium size, semibold, uppercase."""
        style = TextStyles.section_heading
        assert style.family == _theme.font_family("display")
        assert style.size == 13
        assert style.weight == 600
        assert style.formatting == "uppercase"

    def test_panel_title_token(self):
        """Test panel-title uses Oswald, large, bold, uppercase."""
        style = TextStyles.panel_title
        assert style.family == _theme.font_family("display")
        assert style.size == 18
        assert style.weight == 700
        assert style.formatting == "uppercase"

    def test_icon_token(self):
        """Test icon uses MDI font at 14px."""
        style = TextStyles.icon
        assert style.family == _theme.font_family("icon")
        assert style.size == 14

    def test_icon_lg_token(self):
        """Test icon-lg uses 20px size."""
        style = TextStyles.icon_lg
        assert style.size == 20
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
