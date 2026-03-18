"""
Typography system for SpinRender.

Defines TextStyle dataclass and semantic text style tokens.
Uses Theme singleton for font families. Supports hot-reloading.
"""
import wx
from dataclasses import dataclass
from typing import Optional

from SpinRender.core.theme import Theme


# ---------------------------------------------------------------------------
# TextStyle Class
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TextStyle:
    """Immutable text style specification."""
    family: str
    size: int
    weight: int = 400
    color: Optional[object] = None
    formatting: Optional[str] = None

    def create_font(self) -> wx.Font:
        """Create a wx.Font object with these specifications."""
        style = wx.FONTSTYLE_ITALIC if self.formatting == "italic" else wx.FONTSTYLE_NORMAL
        return wx.Font(
            self.size,
            wx.FONTFAMILY_DEFAULT,
            style,
            self.weight,
            faceName=self.family
        )

    def format_text(self, text: str) -> str:
        """Apply text formatting transformations."""
        if self.formatting == "uppercase":
            return text.upper()
        elif self.formatting == "lowercase":
            return text.lower()
        elif self.formatting == "capitalize":
            return text.capitalize()
        else:
            return text


# ---------------------------------------------------------------------------
# Semantic Text Style Tokens (Dynamic via Properties)
# ---------------------------------------------------------------------------

class TextStyles:
    """Container for predefined semantic text styles.

    These styles reference theme font families and are used throughout the UI.
    Values are fetched dynamically from the Theme singleton to support hot-reloading.
    """
    
    @property
    def theme(self):
        return Theme.current()

    @property
    def body(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("mono"),
            size=self.theme.font_size("base"),
            weight=self.theme.font_weight("normal")
        )

    @property
    def body_strong(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("mono"),
            size=self.theme.font_size("base"),
            weight=self.theme.font_weight("semibold")
        )

    @property
    def label_sm(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("mono"),
            size=self.theme.font_size("sm"),
            weight=self.theme.font_weight("semibold")
        )

    @property
    def label_xs(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("mono"),
            size=self.theme.font_size("xs"),
            weight=self.theme.font_weight("bold")
        )

    @property
    def numeric_value(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("mono"),
            size=self.theme.font_size("md"),
            weight=self.theme.font_weight("semibold")
        )

    @property
    def numeric_unit(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("mono"),
            size=self.theme.font_size("base"),
            weight=self.theme.font_weight("normal")
        )

    @property
    def section_heading(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("display"),
            size=self.theme.font_size("md"),
            weight=self.theme.font_weight("semibold"),
            formatting="uppercase"
        )

    @property
    def panel_title(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("display"),
            size=self.theme.font_size("xl"),
            weight=self.theme.font_weight("bold"),
            formatting="uppercase"
        )

    @property
    def icon(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("icon"),
            size=self.theme.font_size("icon")
        )

    @property
    def icon_lg(self) -> TextStyle:
        return TextStyle(
            family=self.theme.font_family("icon"),
            size=self.theme.font_size("icon-lg")
        )

# Singleton access
TextStyles = TextStyles()
