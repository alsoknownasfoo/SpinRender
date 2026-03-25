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
    color_token: Optional[str] = None
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
        """Apply text formatting transformations.

        Uppercase/lowercase/capitalize preserve {placeholder} tokens so that
        format strings like "Rendering frame {current}/{total}" become
        "RENDERING FRAME {current}/{total}" with placeholders intact.
        """
        if self.formatting == "uppercase":
            # Upper-case every segment that is not a {placeholder} token.
            return self._transform_segments(text, lambda s: s.upper())
        elif self.formatting == "lowercase":
            return self._transform_segments(text, lambda s: s.lower())
        elif self.formatting == "capitalize":
            return self._transform_segments(text, lambda s: s[0].upper() + s[1:].lower() if s else s)
        else:
            return text

    def _transform_segments(self, text: str, fn) -> str:
        """Split text into {placeholder} and non-placeholder segments, apply fn to non-placeholders."""
        import re as _re
        def _repl(m):
            seg = m.group()
            return seg if seg.startswith('{') else fn(seg)
        return _re.sub(r'(\{[^}]*\}|[^{]+)', _repl, text)


# ---------------------------------------------------------------------------
# Semantic Text Style Tokens (Dynamic via Properties)
# ---------------------------------------------------------------------------

class TextStyles:
    """Container for semantic text styles.

    Resolves styles dynamically from the Theme singleton via __getattr__.
    Rule: create_text() callsites should use alias keys from _ALIASES.
    Raw theme path fallback remains supported for component paint helpers.
    """
    
    # Canonical alias map for text styles used by create_text().
    # Prefer adding aliases here for create_text() callsites.
    # Paint helpers may use direct component theme paths.
    _ALIASES = {
        "title": "layout.main.header.title",
        "version": "layout.main.header.subtitle",
        "header": "layout.main.leftpanel.headers",
        "subheader": "layout.main.leftpanel.subheaders",
        "metadata": "layout.main.leftpanel.body",
        "description": "layout.main.leftpanel.descriptions",

        "icon": "icon",
        "label": "label",

        # Right Panel styles
        "info": "layout.main.rightpanel.info",
        "shader": "layout.main.rightpanel.shader",

        "status": "status",

        # Component styles
        "button": "button",
        "dropdown": "dropdown",
        "nav": "nav",
        "link": "links",
        "input": "numeric",  # input fields use numeric style (no unit) or label style? Using numeric as placeholder
        "colorpicker": "label",  # color picker labels use label style

        # Button styles
        "closepreview": "components.button.closepreview.label",
        "save_preset": "components.button.save_preset.label",

        # Dialog styles
        "dialog_description": "layout.dialogs.default.body.description",
        "dialog_section_label": "layout.dialogs.default.body.section_label",
        "dialog_link": "layout.dialogs.options.body.links",

        # Component styles
        "section_label_component": "components.section_label.label",

        # Left panel styles
        "leftpanel_description": "layout.main.leftpanel.descriptions",

        # About dialog styles
        "about_section_label":   "layout.dialogs.about.body.section_label",
        "about_version_badge":   "layout.dialogs.about.body.version_badge",
        "about_license_tagline": "layout.dialogs.about.body.license_tagline",
        "about_link_label":      "layout.dialogs.about.body.link_label",
        "about_link_arrow":      "layout.dialogs.about.body.link_arrow",
        "about_link_icon":       "layout.dialogs.about.body.link_icon",

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
            if formatting is None and "ref" in spec:
                ref_spec = self.theme._resolve(spec["ref"].lstrip("@"))
                if isinstance(ref_spec, dict):
                    formatting = ref_spec.get("formatting")
            
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
