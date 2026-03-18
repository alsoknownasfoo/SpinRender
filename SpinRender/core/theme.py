#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
SpinRender Theme Loader — YAML-based design tokens with fallback support.

This module provides the Theme singleton that loads color, font, and spacing
tokens from YAML configuration. If YAML loading fails or PyYAML is unavailable,
falls back to hardcoded defaults from ui.theme (backward compatibility).
"""
import sys
from pathlib import Path
from typing import Any

# Try to import PyYAML, but allow fallback if not available
_yaml_available = False
try:
    import yaml
    _yaml_available = True
except ImportError:
    yaml = None


class Theme:
    """Singleton theme manager with token resolution.

    Usage:
        Theme.load("dark")           # Load theme by name, sets singleton
        Theme.current()              # Get loaded singleton
        Theme.current().color("colors.accent.primary")  # → wx.Colour
        Theme.current().font("body")  # → wx.Font
        Theme.current().size("typography.scale.base")  # → int
    """
    _instance: "Theme | None" = None
    _data: dict[str, Any] = {}

    def __init__(self, data: dict):
        self._data = data

    @classmethod
    def load(cls, name: str = "dark") -> "Theme":
        """Load theme from YAML file. Sets singleton instance."""
        # Idempotent: if already loaded, return existing instance
        if cls._instance is not None:
            return cls._instance

        path = Path(__file__).parent.parent / "resources" / "themes" / f"{name}.yaml"

        if not path.exists():
            raise FileNotFoundError(f"Theme file not found: {path}")

        if not _yaml_available:
            # Fall back to hardcoded defaults (self-contained, no ui.theme dependency)
            cls._instance = cls(cls._build_fallback_data())
            return cls._instance

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            cls._instance = cls(data)
        except Exception:
            # Fall back to hardcoded on any YAML error (self-contained)
            cls._instance = cls(cls._build_fallback_data())

        return cls._instance

    @classmethod
    def current(cls) -> "Theme":
        """Get the current theme singleton, loading default if not set."""
        if cls._instance is None:
            cls.load()
        return cls._instance

    def has_token(self, path: str) -> bool:
        """Check if a token path exists in the theme data."""
        keys = path.split('.')
        current = self._data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        return True

    @classmethod
    def _build_palette(cls, hardcoded: Any) -> dict:
        """Build raw palette from hardcoded constants."""
        return {
            "neutral-1":  "#0A0A0A",
            "neutral-2":  "#0D0D0D",
            "neutral-3":  "#121212",
            "neutral-4":  "#1A1A1A",
            "neutral-5":  "#1A1A1A",
            "neutral-6":  "#222222",
            "neutral-7":  "#1F1F1F",
            "neutral-8":  "#222222",
            "neutral-9":  "#2A2A2A",
            "neutral-10": "#323232",
            "neutral-11": "#777777",
            "neutral-12": "#999999",
            "neutral-13": "#CCCCCC",
            "neutral-14": "#E0E0E0",
            "cyan":       "#00BCD4",   # 0,188,212 matches ACCENT_CYAN
            "yellow":     "#FFD600",
            "green":      "#4CAF50",
            "orange":     "#FF6B35",
            "preset-red":    "#FF6B6B",
            "preset-amber":  "#FFB46B",
            "preset-blue":   "#4D96FF",
            "preset-purple": "#AA6BFF",
            "danger-dark":   "#8C0000",
            "danger-hover":  "#DC1414",
            "danger-medium": "#B40000",
        }

    @classmethod
    def _build_fallback_data(cls) -> dict:
        """Build complete fallback data (self-contained, no dependencies)."""
        palette = cls._build_palette(None)
        return {
            "palette": palette,
            "colors": {
                "bg": {
                    "page": {"ref": "palette.neutral-3"},
                    "panel": {"ref": "palette.neutral-5"},
                    "surface": {"ref": "palette.neutral-8"},
                    "input": {"ref": "palette.neutral-2"},
                    "inner": {"ref": "palette.neutral-6"},
                    "overlay": {"ref": "palette.neutral-4"},
                    "track": {"ref": "palette.neutral-10"},
                    "hover": {"ref": "palette.neutral-9"},
                    "output": {"ref": "palette.neutral-1"},
                },
                "text": {
                    "primary": {"ref": "palette.neutral-14"},
                    "secondary": {"ref": "palette.neutral-11"},
                    "muted": {"ref": "palette.neutral-10"},
                },
                "accent": {
                    "primary": {"ref": "palette.cyan"},
                    "secondary": {"ref": "palette.yellow"},
                    "success": {"ref": "palette.green"},
                    "warning": {"ref": "palette.orange"},
                },
                "border": {
                    "default": {"ref": "palette.neutral-7"},
                    "subtle": {"ref": "palette.neutral-10"},
                    "focus": {"ref": "palette.cyan"},
                    "strong": {"ref": "palette.neutral-10"},
                },
                "preset": [
                    {"ref": "palette.preset-red"},
                    {"ref": "palette.preset-amber"},
                    {"ref": "palette.preset-blue"},
                    {"ref": "palette.preset-purple"},
                ],
                "state": {
                    "hover-overlay": {"ref": "palette.overlay-light"},
                    "pressed-overlay": {"ref": "palette.overlay-medium"},
                    "ghost-overlay": {"ref": "palette.overlay-faint"},
                    "active": {"ref": "palette.green"},
                    "danger": {"ref": "palette.danger-medium"},
                    "danger-hover": {"ref": "palette.danger-hover"},
                    "danger-pressed": {"ref": "palette.danger-dark"},
                },
            },
            "typography": cls._build_fallback_typography(),
            "spacing": cls._build_fallback_spacing(),
            "components": cls._build_fallback_components(),
        }

    @classmethod
    def _build_fallback_typography(cls) -> dict:
        """Build typography dict with hardcoded fallback values."""
        # Font families (same as from foundation.fonts)
        FONT_MONO = "JetBrains Mono"
        FONT_DISPLAY = "Oswald"
        FONT_ICONS = "Material Design Icons"
        FONT_INTER = "Inter"
        # Font sizes (points)
        FONT_SIZE_XS = 8
        FONT_SIZE_SM = 9
        FONT_SIZE_BASE = 11
        FONT_SIZE_MD = 13
        FONT_SIZE_LG = 14
        FONT_SIZE_XL = 18
        FONT_SIZE_ICON = 14
        FONT_SIZE_ICON_LG = 20
        # Font weights
        FONT_WEIGHT_NORMAL = 400
        FONT_WEIGHT_SEMIBOLD = 600
        FONT_WEIGHT_BOLD = 700

        return {
            "families": {
                "mono": FONT_MONO,
                "display": FONT_DISPLAY,
                "icon": FONT_ICONS,
                "inter": FONT_INTER,
            },
            "scale": {
                "xs": FONT_SIZE_XS,
                "sm": FONT_SIZE_SM,
                "base": FONT_SIZE_BASE,
                "md": FONT_SIZE_MD,
                "lg": FONT_SIZE_LG,
                "xl": FONT_SIZE_XL,
                "icon": FONT_SIZE_ICON,
                "icon-lg": FONT_SIZE_ICON_LG,
            },
            "weights": {
                "normal": FONT_WEIGHT_NORMAL,
                "semibold": FONT_WEIGHT_SEMIBOLD,
                "bold": FONT_WEIGHT_BOLD,
            },
            "presets": {
                "body": {
                    "family": {"ref": "typography.families.mono"},
                    "size": {"ref": "typography.scale.base"},
                    "weight": {"ref": "typography.weights.normal"},
                },
                "body_strong": {
                    "family": {"ref": "typography.families.mono"},
                    "size": {"ref": "typography.scale.base"},
                    "weight": {"ref": "typography.weights.semibold"},
                },
                "label_sm": {
                    "family": {"ref": "typography.families.mono"},
                    "size": {"ref": "typography.scale.sm"},
                    "weight": {"ref": "typography.weights.semibold"},
                },
                "label_xs": {
                    "family": {"ref": "typography.families.mono"},
                    "size": {"ref": "typography.scale.xs"},
                    "weight": {"ref": "typography.weights.bold"},
                },
                "numeric_value": {
                    "family": {"ref": "typography.families.mono"},
                    "size": {"ref": "typography.scale.md"},
                    "weight": {"ref": "typography.weights.semibold"},
                },
                "numeric_unit": {
                    "family": {"ref": "typography.families.mono"},
                    "size": {"ref": "typography.scale.base"},
                    "weight": {"ref": "typography.weights.normal"},
                },
                "section_heading": {
                    "family": {"ref": "typography.families.display"},
                    "size": {"ref": "typography.scale.md"},
                    "weight": {"ref": "typography.weights.semibold"},
                },
                "panel_title": {
                    "family": {"ref": "typography.families.display"},
                    "size": {"ref": "typography.scale.xl"},
                    "weight": {"ref": "typography.weights.bold"},
                },
                "icon": {
                    "family": {"ref": "typography.families.icon"},
                    "size": {"ref": "typography.scale.icon"},
                    "weight": {"ref": "typography.weights.normal"},
                },
                "icon_lg": {
                    "family": {"ref": "typography.families.icon"},
                    "size": {"ref": "typography.scale.icon-lg"},
                    "weight": {"ref": "typography.weights.normal"},
                },
            },
        }

    @classmethod
    def _build_fallback_spacing(cls) -> dict:
        """Build spacing dict."""
        return {
            "0": 0,
            "xs": 4,
            "sm": 6,
            "md": 10,
            "lg": 16,
            "xl": 24,
        }

    @classmethod
    def _build_fallback_components(cls) -> dict:
        """Build minimal component tokens for fallback, using array state format."""
        return {
            "numeric_display": {
                "bg": ["colors.bg.input"],
                "border": ["colors.border.default"],
                "text-value": ["colors.text.primary"],
                "text-unit": ["colors.text.secondary"],
                "font-value": {"ref": "typography.presets.numeric-value"},
                "font-unit": {"ref": "typography.presets.numeric-unit"},
            },
            "numeric_input": {
                "bg": ["colors.bg.input"],
                "border": ["colors.border.default"],
                "border-focus": ["colors.border.focus"],
                "text": ["colors.text.primary"],
                "placeholder": ["colors.text.muted"],
                "font": {"ref": "typography.presets.body"},
            },
            "color_picker": {
                "bg": ["colors.bg.overlay"],
                "border": ["colors.border.default"],
                "swatch-border": ["colors.border.subtle"],
                "overlay-fg": ["palette.overlay-medium"],
                "radius": {"ref": "borders.radius.md"},
            },
            "panel": {
                "bg": ["colors.bg.page"],
                "header-bg": ["colors.bg.panel"],
                "header-border": ["colors.border.default"],
                "close-icon": ["colors.text.muted"],
                "padding": {"ref": "spacing.lg"},
                "section-gap": {"ref": "spacing.lg"},
            },
            "slider": {
                "height": 18,
                "track": {
                    "color": ["colors.bg.track"],
                    "height": 4,
                    "radius": {"ref": "borders.radius.sm"},
                },
                "fill": {
                    "color": ["colors.accent.primary"],
                    "radius": {"ref": "borders.radius.sm"},
                },
            },
            "toggle": {
                "bg": ["colors.bg.input"],
                "border": ["colors.border.subtle"],
                "radius": {"ref": "borders.radius.md"},
                "option": {
                    "text": ["colors.text.secondary"],
                    "font": {"ref": "typography.presets.body-strong"},
                    "icon_gap": {"ref": "spacing.sm"},
                },
                "active": {
                    "bg": ["colors.state.active"],
                    "text": ["colors.text.on-accent"],
                    "font": {"ref": "typography.presets.body-strong"},
                },
            },
            "dropdown": {
                "height": 32,
                "bg": ["colors.bg.input"],
                "border": ["colors.border.default"],
                "border-focus": ["colors.border.focus"],
                "radius": {"ref": "borders.radius.md"},
                "text": ["colors.text.primary"],
                "text-muted": ["colors.text.muted"],
                "font": {"ref": "typography.presets.body-strong"},
                "popup": {
                    "bg": ["colors.bg.inner"],
                    "hover": ["colors.bg.hover"],
                },
            },
            "button": {
                "height": 36,
                "radius": {"ref": "borders.radius.md"},
                "font": {"ref": "typography.presets.body-strong"},
                "icon_gap": {"ref": "spacing.md"},
                "primary": {
                    "bg": ["colors.accent.primary"],
                    "text": ["colors.text.on-accent"],
                    "hover": ["colors.state.hover-overlay"],
                    "pressed": ["colors.state.pressed-overlay"],
                },
                "secondary": {
                    "bg": ["colors.bg.surface"],
                    "text": ["colors.text.primary"],
                    "border": ["colors.border.default"],
                    "hover": ["colors.state.hover-overlay"],
                },
                "ghost": {
                    "bg": ["palette.transparent"],
                    "text": ["colors.text.primary"],
                    "hover": ["colors.state.ghost-overlay"],
                },
                "danger": {
                    "bg": ["colors.state.danger"],
                    "text": ["colors.text.on-danger"],
                    "hover-bg": ["colors.state.danger-hover"],
                    "pressed-bg": ["colors.state.danger-pressed"],
                },
            },
            "preset_card": {
                "bg": ["colors.bg.surface"],
                "border": ["colors.border.default"],
                "accent": ["colors.accent.primary"],
            },
            "badge": {
                "bg": ["colors.accent.warning"],
                "text": ["colors.text.on-accent"],
            },
        }

    def _resolve(self, path: str) -> Any:
        """Resolve a dot-path token, following 'ref' references. Returns pink if undefined."""
        import logging
        logger = logging.getLogger("SpinRender")
        node = self._data
        for key in path.split("."):
            if isinstance(node, dict):
                if key not in node:
                    logger.error(f"Undefined theme token: '{path}' (missing '{key}')")
                    # Return pink as visible default for missing tokens
                    return "#FF00FF"  # Magenta/pink for visibility
                node = node[key]
            else:
                logger.error(f"Cannot traverse into {type(node)} at '{key}' in '{path}'")
                return "#FF00FF"

        # Follow ref if present
        if isinstance(node, dict) and "ref" in node:
            return self._resolve(node["ref"])
        return node

    def disabled(self, color) -> 'wx.Colour':
        """Return a copy of color with disabled opacity (alpha=128)."""
        import wx
        if isinstance(color, wx.Colour):
            return wx.Colour(color.Red(), color.Green(), color.Blue(), 128)
        raise ValueError(f"Expected wx.Colour, got {type(color)}")

    def font_family(self, name: str) -> str:
        """Get font family by name: 'mono', 'display', 'icon', 'inter'."""
        try:
            return self._resolve(f"typography.families.{name}")
        except KeyError:
            fallbacks = {
                "mono": "JetBrains Mono",
                "display": "Oswald",
                "icon": "Material Design Icons",
                "inter": "Inter",
            }
            return fallbacks.get(name, "")

    def font_size(self, name: str) -> int:
        """Get font size by name: 'xs', 'sm', 'base', 'md', 'lg', 'xl', 'icon', 'icon-lg'."""
        value = self._resolve(f"typography.scale.{name}")
        return int(value)

    def font_weight(self, name: str) -> int:
        """Get font weight by name: 'normal' (400), 'semibold' (600), 'bold' (700)."""
        value = self._resolve(f"typography.weights.{name}")
        return int(value)

    def get_palette_color(self, name: str) -> 'wx.Colour':
        """Get a raw palette color by name (e.g., 'cyan', 'yellow', 'neutral-3')."""
        return self.color(f"palette.{name}")

    # Special colors via properties for cleaner access
    @property
    def BLACK(self) -> 'wx.Colour':
        """Solid black."""
        return self.color("palette.black-solid")

    @property
    def TRANSPARENT(self) -> 'wx.Colour':
        """Fully transparent."""
        return self.parse_color("rgba(0,0,0,0)") if hasattr(self, '_parse_color') else self.color("palette.transparent")

    @property
    def HOVER_HIGHLIGHT(self) -> 'wx.Colour':
        """Hover highlight color (used for scrollbars etc)."""
        return self.color("colors.bg.hover")

    @property
    def SCROLLBAR_GREY(self) -> 'wx.Colour':
        """Scrollbar track color."""
        return self.get_palette_color("neutral-10")

    @property
    def GREY_100(self) -> 'wx.Colour':
        """Secondary text subtler color."""
        return self.get_palette_color("neutral-11")  # Note: comment said neutral-11 but was 100

    @property
    def DANGER_DARK(self) -> 'wx.Colour':
        """Danger state (pressed)."""
        return self.color("palette.danger-dark")

    @property
    def DANGER_HOVER(self) -> 'wx.Colour':
        """Danger state (hover)."""
        return self.color("palette.danger-hover")

    @property
    def DANGER_MEDIUM(self) -> 'wx.Colour':
        """Danger state (default)."""
        return self.color("palette.danger-medium")

    @property
    def WHITE(self) -> 'wx.Colour':
        """Solid white."""
        return self.color("palette.neutral-15")

    @property
    def WHITE_ALPHA_20(self) -> 'wx.Colour':
        """White with 20% opacity (0.08 alpha ≈ 20)."""
        return self.parse_color("rgba(255,255,255,0.08)")

    @property
    def WHITE_ALPHA_30(self) -> 'wx.Colour':
        """White with 30% opacity (0.16)."""
        return self.parse_color("rgba(255,255,255,0.16)")

    @property
    def WHITE_ALPHA_40(self) -> 'wx.Colour':
        """White with 40% opacity (0.27)."""
        return self.parse_color("rgba(255,255,255,0.27)")

    @property
    def WHITE_ALPHA_68(self) -> 'wx.Colour':
        """White with 68% opacity (0.68)."""
        return self.parse_color("rgba(255,255,255,0.68)")

    @property
    def BG_MODAL(self) -> 'wx.Colour':
        """Modal background (same as BG_PAGE)."""
        return self.color("colors.bg.page")

    def _parse_color(self, value: str):
        """Parse color string to wx.Colour. Supports hex (#RRGGBB) and rgba(r,g,b,a)."""
        import wx
        import re

        if isinstance(value, wx.Colour):
            return value

        if not isinstance(value, str):
            raise ValueError(f"Invalid color value: {value}")

        # Parse rgba(r, g, b, a)
        if value.startswith("rgba("):
            parts = re.findall(r"[\d.]+", value)
            if len(parts) != 4:
                raise ValueError(f"Invalid rgba format: {value}")
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = max(0, min(255, int(round(float(parts[3]) * 255))))
            return wx.Colour(r, g, b, a)

        # Parse hex #RRGGBB (case-insensitive)
        clean = value.lstrip("#")
        if len(clean) != 6:
            raise ValueError(f"Invalid hex color: {value}")
        r = int(clean[0:2], 16)
        g = int(clean[2:4], 16)
        b = int(clean[4:6], 16)
        return wx.Colour(r, g, b)

    def parse_color(self, value: str):
        """
        Public wrapper for _parse_color. Use this from compatibility layers
        instead of accessing the private method.
        """
        return self._parse_color(value)

    def _shift_color(self, color: 'wx.Colour', delta: int) -> 'wx.Colour':
        """
        Shift RGB channels by delta (±10), clamped 0-255, preserving alpha.
        Used to generate hover/active states from base colors.
        """
        import wx
        r = max(0, min(255, color.Red() + delta))
        g = max(0, min(255, color.Green() + delta))
        b = max(0, min(255, color.Blue() + delta))
        a = color.Alpha()
        return wx.Colour(r, g, b, a)

    def color(self, token: str, state: int = 0) -> list:
        """Resolve a color token to a wx.Colour. e.g. 'colors.accent.primary'.
        by default return the normal state color and it's color in a state. By default, return the normal color state. States: 0=normal, 1=hover, 2=active."""
        value = self.color_states(token)[state]
        return self._parse_color(value)

    def get_preset_colors(self) -> list:
        """
        Get list of preset colors from the theme.
        Returns list of wx.Colour objects for red, amber, blue, purple.
        Falls back to hardcoded values if not defined in theme.
        """
        try:
            # Try to get preset color strings from palette section
            raw_presets = self._resolve("colors.preset")
            if isinstance(raw_presets, list) and len(raw_presets) >= 4:
                colors = []
                for ref_dict in raw_presets[:4]:
                    if isinstance(ref_dict, dict) and 'ref' in ref_dict:
                        color_str = self._resolve(ref_dict['ref'])
                    elif isinstance(ref_dict, str):
                        color_str = self._resolve(ref_dict) if not ref_dict.startswith('#') and not ref_dict.startswith('rgba(') else ref_dict
                    else:
                        color_str = ref_dict
                    colors.append(self._parse_color(color_str))
                return colors
        except (KeyError, AttributeError):
            pass

        # Fallback: use hardcoded preset colors from palette
        fallback = [
            ("palette.red", wx.Colour(255, 107, 107)),
            ("palette.amber", wx.Colour(255, 180, 107)),
            ("palette.blue", wx.Colour(77, 150, 255)),
            ("palette.purple", wx.Colour(170, 107, 255)),
        ]
        colors = []
        for token, default in fallback:
            try:
                colors.append(self.color(token))
            except KeyError:
                colors.append(default)
        return colors

    def has_palette_color(self, token: str) -> bool:
        """Check if a palette color token exists."""
        try:
            palette = self._data.get("palette", {})
            return token in palette
        except AttributeError:
            return False

    def color_states(self, token: str, states: int = 3) -> list:
        """
        Resolve a color token that may be a single value or an array.
        Returns list of wx.Colour objects for [normal, hover, active] states.

        Array format in YAML:
          - [normal]                     → auto [+10, -10]
          - [normal, hover]              → auto active [hover, -10]
          - [normal, hover, active]      → explicit

        Elements in arrays can be:
          - Hex/RGBA strings: "#RRGGBB" or "rgba(r,g,b,a)"
          - Token references: {ref: "colors.xxx"} or "colors.xxx" (resolved via _resolve)
        """
        import wx

        raw = self._resolve(token)

        # Normalize to list and resolve each element to a color string
        if isinstance(raw, list):
            color_strings = []
            for v in raw:
                if isinstance(v, dict) and 'ref' in v:
                    # Resolve ref dict: {ref: "colors.xxx"}
                    resolved = self._resolve(v['ref'])
                    color_strings.append(resolved)
                elif isinstance(v, str):
                    # Could be a token path like "colors.accent.primary" or a direct color
                    # Try to resolve as token; if it fails, treat as direct color
                    try:
                        resolved = self._resolve(v)
                        color_strings.append(resolved)
                    except KeyError:
                        # Not a token, direct color string
                        color_strings.append(v)
                else:
                    raise ValueError(f"Invalid array element in token '{token}': {v}")
            # Parse all color strings
            colors = [self._parse_color(cs) for cs in color_strings]
        else:
            # Single value (string, ref dict)
            if isinstance(raw, dict) and 'ref' in raw:
                raw = self._resolve(raw['ref'])
            colors = [self._parse_color(raw)]

        # Pad to required length with shifted colors
        while len(colors) < states:
            if len(colors) == 0:
                raise ValueError(f"No color found for token '{token}'")
            # Shift from the last color in the list
            base = colors[-1]
            if len(colors) == 1:
                # Need hover (+10) and active (-10)
                colors.append(self._shift_color(base, 10))
                colors.append(self._shift_color(base, -10))
            elif len(colors) == 2:
                # Need active (-10 from hover)
                colors.append(self._shift_color(colors[1], -10))
            else:
                # Shouldn't get here, but duplicate last
                colors.append(base)

        return colors[:states]

    def size(self, token: str) -> int:
        """Resolve a spacing/size token to an int. e.g. 'spacing.lg'."""
        value = self._resolve(token)
        return int(value)

    def font(self, preset: str):
        """Resolve a font preset to a wx.Font.

        Args:
            preset: e.g. 'body', 'section_heading', 'icon'

        Returns:
            wx.Font configured with family, size, weight from theme.
        """
        import wx
        spec = self._resolve(f"typography.presets.{preset}")

        # Resolve family (can be string or ref dict)
        family_spec = spec.get("family", "wx.FONTFAMILY_DEFAULT")
        if isinstance(family_spec, dict) and "ref" in family_spec:
            family = self._resolve(family_spec["ref"])
        else:
            family = family_spec

        # Resolve size (can be int or ref)
        size_spec = spec.get("size", 11)
        if isinstance(size_spec, dict) and "ref" in size_spec:
            size = self._resolve(size_spec["ref"])
        else:
            size = int(size_spec)

        # Resolve weight (can be int or ref)
        weight_spec = spec.get("weight", 400)
        if isinstance(weight_spec, dict) and "ref" in weight_spec:
            weight = self._resolve(weight_spec["ref"])
        else:
            weight = int(weight_spec)

        # Map weight to wx constants
        weight_map = {
            400: wx.FONTWEIGHT_NORMAL,
            600: wx.FONTWEIGHT_SEMIBOLD,
            700: wx.FONTWEIGHT_BOLD,
        }
        wx_weight = weight_map.get(weight, wx.FONTWEIGHT_NORMAL)

        # Create wx.Font directly; private fonts are pre-registered at app startup
        return wx.Font(
            size,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx_weight,
            faceName=family
        )
