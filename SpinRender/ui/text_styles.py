#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Typography system for SpinRender.

Defines TextStyle dataclass and semantic text style tokens.
Imports font constants from theme module.
"""
import wx
from dataclasses import dataclass
from typing import Optional
from .theme import (
    FONT_MONO,
    FONT_ICONS,
    FONT_DISPLAY,
    FONT_SIZE_XS,
    FONT_SIZE_SM,
    FONT_SIZE_BASE,
    FONT_SIZE_MD,
    FONT_SIZE_LG,
    FONT_SIZE_XL,
    FONT_SIZE_ICON,
    FONT_SIZE_ICON_LG,
    FONT_WEIGHT_NORMAL,
    FONT_WEIGHT_SEMIBOLD,
    FONT_WEIGHT_BOLD,
)


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
# Semantic Text Style Tokens
# ---------------------------------------------------------------------------

class TextStyles:
    """Container for predefined semantic text styles.

    These styles reference theme font families and are used throughout the UI.
    Import and use like: TextStyles.body, TextStyles.section_heading, etc.
    """
    # Base body text - JetBrains Mono, 11px, normal
    body = TextStyle(
        family=FONT_MONO,
        size=FONT_SIZE_BASE,
        weight=FONT_WEIGHT_NORMAL
    )

    # Strong body text - JetBrains Mono, 11px, semibold
    body_strong = TextStyle(
        family=FONT_MONO,
        size=FONT_SIZE_BASE,
        weight=FONT_WEIGHT_SEMIBOLD
    )

    # Small labels - 9px, semibold
    label_sm = TextStyle(
        family=FONT_MONO,
        size=FONT_SIZE_SM,
        weight=FONT_WEIGHT_SEMIBOLD
    )

    # Extra small labels (badges, captions) - 8px, bold
    label_xs = TextStyle(
        family=FONT_MONO,
        size=FONT_SIZE_XS,
        weight=FONT_WEIGHT_BOLD
    )

    # Numeric display values - 13px, semibold (for tilt angles, etc.)
    numeric_value = TextStyle(
        family=FONT_MONO,
        size=FONT_SIZE_MD,
        weight=FONT_WEIGHT_SEMIBOLD
    )

    # Numeric units (°, %, etc.) - 11px, normal
    numeric_unit = TextStyle(
        family=FONT_MONO,
        size=FONT_SIZE_BASE,
        weight=FONT_WEIGHT_NORMAL
    )

    # Section headings - Oswald, 13px, semibold, uppercase
    section_heading = TextStyle(
        family=FONT_DISPLAY,
        size=FONT_SIZE_MD,
        weight=FONT_WEIGHT_SEMIBOLD,
        formatting="uppercase"
    )

    # Panel titles - Oswald, 18px, bold, uppercase
    panel_title = TextStyle(
        family=FONT_DISPLAY,
        size=FONT_SIZE_XL,
        weight=FONT_WEIGHT_BOLD,
        formatting="uppercase"
    )

    # MDI icons - Material Design Icons, 14px
    icon = TextStyle(
        family=FONT_ICONS,
        size=FONT_SIZE_ICON
    )

    # Large icons (button icons) - 20px
    icon_lg = TextStyle(
        family=FONT_ICONS,
        size=FONT_SIZE_ICON_LG
    )
