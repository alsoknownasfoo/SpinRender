#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Typography system for SpinRender.

Defines TextStyle dataclass and semantic text style tokens.
Uses Theme singleton for font families.
"""
import wx
from dataclasses import dataclass
from typing import Optional

from SpinRender.core.theme import Theme
_theme = Theme.current()


# ---------------------------------------------------------------------------
# TextStyle Class
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TextStyle:
    """Immutable text style specification.

    Attributes:
        family: Font family name (e.g., "JetBrains Mono", "Oswald")
        size: Font size in points
        weight: Font weight (400=normal, 600=semibold, 700=bold)
        color: Optional wx.Colour for text (if None, uses default)
        formatting: Optional text formatting like "uppercase", "lowercase", "italic"
    """
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
# Semantic Text Style Tokens (reference theme values)
# ---------------------------------------------------------------------------

# Resolve theme values once at module load
_FONT_MONO = _theme.font_family("mono")
_FONT_ICONS = _theme.font_family("icon")
_FONT_DISPLAY = _theme.font_family("display")
_FONT_SIZE_XS = _theme.font_size("xs")
_FONT_SIZE_SM = _theme.font_size("sm")
_FONT_SIZE_BASE = _theme.font_size("base")
_FONT_SIZE_MD = _theme.font_size("md")
_FONT_SIZE_LG = _theme.font_size("lg")
_FONT_SIZE_XL = _theme.font_size("xl")
_FONT_SIZE_ICON = _theme.font_size("icon")
_FONT_SIZE_ICON_LG = _theme.font_size("icon-lg")  # Note: hyphen, not underscore
_FONT_WEIGHT_NORMAL = _theme.font_weight("normal")
_FONT_WEIGHT_SEMIBOLD = _theme.font_weight("semibold")
_FONT_WEIGHT_BOLD = _theme.font_weight("bold")


class TextStyles:
    """Container for predefined semantic text styles.

    These styles reference theme font families and are used throughout the UI.
    Import and use like: TextStyles.body, TextStyles.section_heading, etc.
    """
    # Base body text - JetBrains Mono, 11px, normal
    body = TextStyle(
        family=_FONT_MONO,
        size=_FONT_SIZE_BASE,
        weight=_FONT_WEIGHT_NORMAL
    )

    # Strong body text - JetBrains Mono, 11px, semibold
    body_strong = TextStyle(
        family=_FONT_MONO,
        size=_FONT_SIZE_BASE,
        weight=_FONT_WEIGHT_SEMIBOLD
    )

    # Small labels - 9px, semibold
    label_sm = TextStyle(
        family=_FONT_MONO,
        size=_FONT_SIZE_SM,
        weight=_FONT_WEIGHT_SEMIBOLD
    )

    # Extra small labels (badges, captions) - 8px, bold
    label_xs = TextStyle(
        family=_FONT_MONO,
        size=_FONT_SIZE_XS,
        weight=_FONT_WEIGHT_BOLD
    )

    # Numeric display values - 13px, semibold (for tilt angles, etc.)
    numeric_value = TextStyle(
        family=_FONT_MONO,
        size=_FONT_SIZE_MD,
        weight=_FONT_WEIGHT_SEMIBOLD
    )

    # Numeric units (°, %, etc.) - 11px, normal
    numeric_unit = TextStyle(
        family=_FONT_MONO,
        size=_FONT_SIZE_BASE,
        weight=_FONT_WEIGHT_NORMAL
    )

    # Section headings - Oswald, 13px, semibold, uppercase
    section_heading = TextStyle(
        family=_FONT_DISPLAY,
        size=_FONT_SIZE_MD,
        weight=_FONT_WEIGHT_SEMIBOLD,
        formatting="uppercase"
    )

    # Panel titles - Oswald, 18px, bold, uppercase
    panel_title = TextStyle(
        family=_FONT_DISPLAY,
        size=_FONT_SIZE_XL,
        weight=_FONT_WEIGHT_BOLD,
        formatting="uppercase"
    )

    # MDI icons - Material Design Icons, 14px
    icon = TextStyle(
        family=_FONT_ICONS,
        size=_FONT_SIZE_ICON
    )

    # Large icons (button icons) - 20px
    icon_lg = TextStyle(
        family=_FONT_ICONS,
        size=_FONT_SIZE_ICON_LG
    )
