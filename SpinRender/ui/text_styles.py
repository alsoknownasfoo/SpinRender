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

    def _get_style(self, role: str) -> TextStyle:
        """Helper to create TextStyle from theme role."""
        font = self.theme.font(role)
        color = self.theme.color(f"text.{role}.color")
        return TextStyle(
            family=font.GetFaceName(),
            size=font.GetPointSize(),
            weight=font.GetWeight(),
            color=color
        )

    @property
    def body(self) -> TextStyle: return self._get_style("body")
    @property
    def body_strong(self) -> TextStyle: return self._get_style("body_strong")
    @property
    def label_sm(self) -> TextStyle: return self._get_style("label") # Maps to label role
    @property
    def label_xs(self) -> TextStyle: return self._get_style("metadata") # Maps to metadata role
    @property
    def numeric_value(self) -> TextStyle: return self._get_style("numeric_value")
    @property
    def numeric_unit(self) -> TextStyle: return self._get_style("body")
    
    @property
    def section_heading(self) -> TextStyle:
        style = self._get_style("header")
        return TextStyle(
            family=style.family,
            size=style.size,
            weight=style.weight,
            color=style.color,
            formatting="uppercase"
        )

    @property
    def panel_title(self) -> TextStyle:
        style = self._get_style("title")
        return TextStyle(
            family=style.family,
            size=style.size,
            weight=style.weight,
            color=style.color,
            formatting="uppercase"
        )

    @property
    def icon(self) -> TextStyle: return self._get_style("icon")
    @property
    def icon_lg(self) -> TextStyle: return self._get_style("icon_lg")

# Singleton access
TextStyles = TextStyles()
