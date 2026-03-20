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
    """Container for semantic text styles.

    Resolves styles dynamically from the Theme singleton via __getattr__.
    This ensures any new style added to the YAML theme is automatically available.
    """
    
    # Map code style names to their definitive theme paths
    _ALIASES = {
        "title": "layout.main.header.title",
        "version": "layout.main.header.subtitle",
        "header": "layout.main.leftpanel.headers",
        "subheader": "layout.main.leftpanel.subheaders",
        "metadata": "layout.main.leftpanel.body",
        "icon": "icon",
        "label": "label",

        # Right Panel styles
        "info": "layout.main.rightpanel.info",
        "shader": "layout.main.rightpanel.shader",

        # Legacy/helper aliases
        "label_sm": "layout.main.leftpanel.headers",
        "label_xs": "layout.main.leftpanel.body",
        "numeric_unit": "layout.main.leftpanel.body",
        "section_heading": "layout.main.leftpanel.headers",
        "panel_title": "layout.main.header.title"
    }

    @property
    def theme(self):
        return Theme.current()

    def _get_style(self, role: str) -> TextStyle:
        """Helper to create TextStyle from theme role."""
        font = self.theme.font(role)
        color = self.theme.color(role) # Engine handles extracting .color from dict or sibling
        
        # Resolve extra metadata like formatting from the theme spec
        spec = self.theme.text_style(role)
        if not isinstance(spec, dict) or spec == "#FF00FF":
            spec = self.theme._resolve(role)
            
        formatting = None
        if isinstance(spec, dict):
            formatting = spec.get("formatting")
            
        return TextStyle(
            family=font.GetFaceName(),
            size=font.GetPointSize(),
            weight=font.GetWeight(),
            color=color,
            formatting=formatting
        )

    def __getattr__(self, name: str) -> TextStyle:
        """Dynamically resolve style properties."""
        role = self._ALIASES.get(name, name)
        try:
            return self._get_style(role)
        except Exception:
            # Fallback to body if resolution fails completely
            return self._get_style("body")

# Singleton access
TextStyles = TextStyles()
