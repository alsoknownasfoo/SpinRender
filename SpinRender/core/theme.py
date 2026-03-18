"""
SpinRender Theme Loader — YAML-based design tokens.

This module provides the Theme singleton that loads color, font, and spacing
tokens from YAML configuration. YAML loading is strictly required.
"""
import logging
from pathlib import Path
from typing import Any

# Try to import PyYAML
_yaml_available = False
try:
    import yaml
    _yaml_available = True
except ImportError:
    yaml = None

logger = logging.getLogger("SpinRender")


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
    _loaded_mtime: float = 0
    _loaded_name: str = ""

    def __init__(self, data: dict):
        self._data = data

    @classmethod
    def load(cls, name: str = "dark", force: bool = False) -> "Theme":
        """Load theme from YAML file. Sets singleton instance."""
        # Use resolve() to follow symlinks and get the absolute path
        path = (Path(__file__).parent.parent / "resources" / "themes" / f"{name}.yaml").resolve()
        
        if not path.exists():
            error_msg = f"Theme file not found: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Check mtime to auto-detect disk changes
        mtime = path.stat().st_mtime
        is_stale = mtime > cls._loaded_mtime or name != cls._loaded_name
        
        # Idempotent: if already loaded and not forcing/stale, return existing instance
        if cls._instance is not None and not force and not is_stale:
            return cls._instance

        logger.info(f"Theme: {'Reloading' if (force or is_stale) else 'Initializing'} '{name}' theme loading.")

        if not _yaml_available:
            error_msg = "PyYAML is not available. Theme system requires PyYAML."
            logger.error(error_msg)
            raise ImportError(error_msg)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            # Print full loaded theme data at INFO level
            debug_data = yaml.dump(data, sort_keys=False, default_flow_style=False)
            logger.info(f"Theme Data (Loaded from {path.name}):\n{debug_data}")

            if cls._instance:
                # CRITICAL: Update the existing instance's data dictionary in-place.
                # This ensures all modules that hold a reference to this instance 
                # (via _theme = Theme.current()) see the new data immediately.
                cls._instance._data = data
            else:
                cls._instance = cls(data)
            
            cls._loaded_mtime = mtime
            cls._loaded_name = name
            logger.info(f"Theme: '{name}' theme loaded successfully.")
        except Exception as e:
            error_msg = f"Failed to parse theme '{name}' from {path}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return cls._instance

    @classmethod
    def reload(cls) -> "Theme":
        """Force a reload of the current theme from disk."""
        # Use the name of the currently loaded theme, or default to dark
        name = cls._loaded_name if cls._loaded_name else "dark"
        instance = cls.load(name=name, force=True)
        
        if _yaml_available:
            try:
                # Print the full data as YAML for easy debugging
                debug_data = yaml.dump(instance._data, sort_keys=False, default_flow_style=False)
                logger.info(f"Theme Data (Reloaded):\n{debug_data}")
            except Exception as e:
                logger.info(f"Theme Data (Reloaded - Raw): {instance._data}")
                logger.error(f"Failed to dump theme debug data: {e}")
        else:
            logger.info(f"Theme Data (Reloaded - Raw): {instance._data}")
            
        return instance


    @classmethod
    def _build_fallback_data(cls) -> dict:
        """Return hardcoded fallback theme data for the default dark theme.

        This is used by the theme validator when PyYAML is not available.
        The structure matches the YAML format exactly.
        """
        return {
            "meta": {
                "name": "Dark",
                "version": "1.0.0",
                "description": "Default dark theme matching the SpinRender design system"
            },
            "palette": {
                # Neutrals (darkest -> lightest)
                "neutral-1": "#0A0A0A",
                "neutral-2": "#0D0D0D",
                "neutral-3": "#121212",
                "neutral-4": "#1A1A1A",
                "neutral-5": "#1A1A1A",
                "neutral-6": "#222222",
                "neutral-7": "#1F1F1F",
                "neutral-8": "#222222",
                "neutral-9": "#2A2A2A",
                "neutral-10": "#323232",
                "neutral-11": "#777777",
                "neutral-12": "#555555",
                "neutral-13": "#CCCCCC",
                "neutral-14": "#E0E0E0",
                "neutral-15": "#FFFFFF",
                "neutral-16": "#333333",
                "neutral-17": "#787878",
                "neutral-18": "#646464",
                # Accent colors
                "cyan": "#00BCD4",
                "yellow": "#FFD600",
                "green": "#4CAF50",
                "orange": "#FF6B35",
                "red": "#FF3B30",
                "purple": "#AA6BFF",
                "pink": "#FF4081",
                # Preset card colors
                "preset-red": "#FF6B6B",
                "preset-amber": "#FFB46B",
                "preset-blue": "#4D96FF",
                "preset-purple": "#AA6BFF",
                # Danger button states
                "danger-dark": "#8C0000",
                "danger-hover": "#DC1414",
                "danger-medium": "#B40000",
                # Overlays (RGBA with alpha)
                "overlay-faint": "rgba(255,255,255,0.08)",
                "overlay-light": "rgba(255,255,255,0.16)",
                "overlay-medium": "rgba(255,255,255,0.27)",
                "transparent": "rgba(0,0,0,0)",
                "black-solid": "#000000"
            },
            "colors": {
                # Backgrounds
                "bg": {
                    "page": {"ref": "palette.neutral-3"},
                    "panel": {"ref": "palette.neutral-5"},
                    "surface": {"ref": "palette.neutral-8"},
                    "input": {"ref": "palette.neutral-2"},
                    "inner": {"ref": "palette.neutral-6"},
                    "overlay": {"ref": "palette.neutral-4"},
                    "track": {"ref": "palette.neutral-10"},
                    "hover": {"ref": "palette.neutral-9"},
                    "output": {"ref": "palette.neutral-1"}
                },
                # Text
                "text": {
                    "primary": {"ref": "palette.neutral-14"},
                    "secondary": {"ref": "palette.neutral-11"},
                    "muted": {"ref": "palette.neutral-12"},
                    "on-accent": {"ref": "palette.neutral-2"},
                    "on-danger": {"ref": "palette.neutral-15"}
                },
                # Accent
                "accent": {
                    "primary": {"ref": "palette.cyan"},
                    "secondary": {"ref": "palette.yellow"},
                    "success": {"ref": "palette.green"},
                    "warning": {"ref": "palette.orange"}
                },
                # Borders
                "border": {
                    "default": {"ref": "palette.neutral-7"},
                    "subtle": {"ref": "palette.neutral-10"},
                    "focus": {"ref": "palette.cyan"},
                    "strong": {"ref": "palette.neutral-10"}
                },
                # Presets
                "preset": [
                    {"ref": "palette.preset-red"},
                    {"ref": "palette.preset-amber"},
                    {"ref": "palette.preset-blue"},
                    {"ref": "palette.preset-purple"}
                ],
                # State overlays
                "state": {
                    "hover-overlay": {"ref": "palette.overlay-light"},
                    "pressed-overlay": {"ref": "palette.overlay-medium"},
                    "ghost-overlay": {"ref": "palette.overlay-faint"},
                    "active": {"ref": "palette.green"},
                    "danger": {"ref": "palette.danger-medium"},
                    "danger-hover": {"ref": "palette.danger-hover"},
                    "danger-pressed": {"ref": "palette.danger-dark"}
                }
            },
            "typography": {
                "families": {
                    "mono": "JetBrains Mono",
                    "display": "Oswald",
                    "icon": "Material Design Icons",
                    "inter": "Inter"
                },
                "scale": {
                    "xs": 8,
                    "sm": 9,
                    "base": 11,
                    "md": 13,
                    "lg": 14,
                    "xl": 18,
                    "icon": 14,
                    "icon-lg": 20
                },
                "weights": {
                    "normal": 400,
                    "semibold": 600,
                    "bold": 700
                },
                "presets": {
                    "body": {
                        "family": {"ref": "typography.families.mono"},
                        "size": {"ref": "typography.scale.base"},
                        "weight": {"ref": "typography.weights.normal"}
                    },
                    "body_strong": {
                        "family": {"ref": "typography.families.mono"},
                        "size": {"ref": "typography.scale.base"},
                        "weight": {"ref": "typography.weights.semibold"}
                    },
                    "label_sm": {
                        "family": {"ref": "typography.families.mono"},
                        "size": {"ref": "typography.scale.sm"},
                        "weight": {"ref": "typography.weights.semibold"}
                    },
                    "label_xs": {
                        "family": {"ref": "typography.families.mono"},
                        "size": {"ref": "typography.scale.xs"},
                        "weight": {"ref": "typography.weights.bold"}
                    },
                    "numeric_value": {
                        "family": {"ref": "typography.families.mono"},
                        "size": {"ref": "typography.scale.md"},
                        "weight": {"ref": "typography.weights.semibold"}
                    },
                    "numeric_unit": {
                        "family": {"ref": "typography.families.mono"},
                        "size": {"ref": "typography.scale.base"},
                        "weight": {"ref": "typography.weights.normal"}
                    },
                    "section_heading": {
                        "family": {"ref": "typography.families.display"},
                        "size": {"ref": "typography.scale.md"},
                        "weight": {"ref": "typography.weights.semibold"}
                    },
                    "panel_title": {
                        "family": {"ref": "typography.families.display"},
                        "size": {"ref": "typography.scale.xl"},
                        "weight": {"ref": "typography.weights.bold"}
                    },
                    "icon": {
                        "family": {"ref": "typography.families.icon"},
                        "size": {"ref": "typography.scale.icon"},
                        "weight": {"ref": "typography.weights.normal"}
                    },
                    "icon_lg": {
                        "family": {"ref": "typography.families.icon"},
                        "size": {"ref": "typography.scale.icon-lg"},
                        "weight": {"ref": "typography.weights.normal"}
                    }
                }
            },
            "spacing": {
                "0": 0,
                "xs": 4,
                "sm": 6,
                "md": 10,
                "lg": 16,
                "xl": 24
            },
            "borders": {
                "radius": {
                    "sm": 4,
                    "md": 6,
                    "lg": 8,
                    "full": 9999
                }
            },
            "components": {
                "numeric_display": {
                    "bg": ["colors.bg.input"],
                    "border": ["colors.border.default"],
                    "text-value": ["colors.text.primary"],
                    "text-unit": ["colors.text.secondary"],
                    "font-value": {"ref": "typography.presets.numeric-value"},
                    "font-unit": {"ref": "typography.presets.numeric-unit"}
                },
                "numeric_input": {
                    "bg": ["colors.bg.input"],
                    "border": ["colors.border.default"],
                    "border-focus": ["colors.border.focus"],
                    "text": ["colors.text.primary"],
                    "placeholder": ["colors.text.muted"],
                    "font": {"ref": "typography.presets.body"}
                },
                "color_picker": {
                    "bg": ["colors.bg.overlay"],
                    "border": ["colors.border.default"],
                    "swatch-border": ["colors.border.subtle"],
                    "overlay-fg": ["palette.overlay-medium"],
                    "radius": {"ref": "borders.radius.md"}
                },
                "panel": {
                    "bg": ["colors.bg.page"],
                    "header-bg": ["colors.bg.panel"],
                    "header-border": ["colors.border.default"],
                    "padding": {"ref": "spacing.lg"},
                    "section-gap": {"ref": "spacing.lg"}
                },
                "slider": {
                    "height": 18,
                    "track": {
                        "color": ["colors.bg.track"],
                        "height": 4,
                        "radius": {"ref": "borders.radius.sm"}
                    },
                    "fill": {
                        "color": ["colors.accent.primary"],
                        "radius": {"ref": "borders.radius.sm"}
                    }
                },
                "toggle": {
                    "bg": ["colors.bg.input"],
                    "border": ["colors.border.subtle"],
                    "radius": {"ref": "borders.radius.md"},
                    "option": {
                        "text": ["colors.text.secondary"],
                        "font": {"ref": "typography.presets.body-strong"},
                        "icon_gap": {"ref": "spacing.sm"}
                    },
                    "active": {
                        "bg": ["colors.state.active"],
                        "text": ["colors.text.on-accent"],
                        "font": {"ref": "typography.presets.body-strong"}
                    }
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
                        "hover": ["colors.bg.hover"]
                    }
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
                        "pressed": ["colors.state.pressed-overlay"]
                    },
                    "secondary": {
                        "bg": ["colors.bg.surface"],
                        "text": ["colors.text.primary"],
                        "border": ["colors.border.default"],
                        "hover": ["colors.state.hover-overlay"]
                    },
                    "ghost": {
                        "bg": ["palette.transparent"],
                        "text": ["colors.text.primary"],
                        "hover": ["colors.state.ghost-overlay"],
                        "border": ["palette.transparent"],
                        "radius": {"ref": "borders.radius.md"}
                    },
                    "danger": {
                        "bg": ["colors.state.danger"],
                        "text": ["colors.text.on-danger"],
                        "hover-bg": ["colors.state.danger-hover"],
                        "pressed-bg": ["colors.state.danger-pressed"]
                    },
                    "close": {"ref": "components.button.ghost"}
                },
                "preset_card": {
                    "bg": ["colors.bg.surface"],
                    "border": ["colors.border.default"],
                    "accent": ["colors.accent.primary"]
                },
                "badge": {
                    "bg": ["colors.accent.warning"],
                    "text": ["colors.text.on-accent"]
                }
            }
        }

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

    def _resolve(self, path: str) -> Any:
        """
        Resolve a dot-path token, following 'ref' references. 
        If path is not a valid token but looks like a color name, returns it as-is.
        Returns pink if undefined.
        """
        node = self._data
        is_token_path = '.' in path or path in node
        
        if not is_token_path:
            # Not a token path (no dots, not in root). 
            # Could be a direct color name (e.g. "red") or hex.
            if path.startswith("#") or path.startswith("rgba(") or len(path) == 6:
                return path
            # If it's a simple word, let _parse_color try wx.ColourDatabase
            if path.isalpha():
                return path

        for key in path.split("."):
            # If we encounter a ref during traversal, resolve it and continue from there
            while isinstance(node, dict) and "ref" in node:
                node = self._resolve(node["ref"])

            if isinstance(node, dict):
                if key not in node:
                    logger.error(f"Theme: Undefined token: '{path}' (missing '{key}')")
                    return "#FF00FF"  # Magenta/pink for visibility
                node = node[key]
            else:
                logger.error(f"Theme: Cannot traverse into {type(node)} at '{key}' in '{path}'")
                return "#FF00FF"

        # Follow ref if present at the leaf
        while isinstance(node, dict) and "ref" in node:
            node = self._resolve(node["ref"])
        return node

    def disabled(self, color) -> 'wx.Colour':
        """Return a copy of color with disabled opacity (alpha=128)."""
        import wx
        if isinstance(color, wx.Colour):
            return wx.Colour(color.Red(), color.Green(), color.Blue(), 128)
        raise ValueError(f"Expected wx.Colour, got {type(color)}")

    def font_family(self, name: str) -> str:
        """Get font family by name: 'mono', 'display', 'icon', 'inter'."""
        return self._resolve(f"typography.families.{name}")

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
        return self.color("palette.transparent")

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
        # Use neutral-18 which exists in dark.yaml
        return self.get_palette_color("neutral-18")

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
        """White with 20% opacity."""
        return self.parse_color("rgba(255,255,255,0.08)")

    @property
    def WHITE_ALPHA_30(self) -> 'wx.Colour':
        """White with 30% opacity."""
        return self.parse_color("rgba(255,255,255,0.16)")

    @property
    def WHITE_ALPHA_40(self) -> 'wx.Colour':
        """White with 40% opacity."""
        return self.parse_color("rgba(255,255,255,0.27)")

    @property
    def WHITE_ALPHA_68(self) -> 'wx.Colour':
        """White with 68% opacity."""
        return self.parse_color("rgba(255,255,255,0.68)")

    @property
    def BG_MODAL(self) -> 'wx.Colour':
        """Modal background (same as BG_PAGE)."""
        return self.color("colors.bg.page")

    def _parse_color(self, value: str):
        """Parse color string to wx.Colour. Supports hex (#RRGGBB, RRGGBB, #RRGGBBAA), rgba(r,g,b,a), and basic color names."""
        import wx
        import re

        if isinstance(value, wx.Colour):
            return value

        if not isinstance(value, str):
            raise ValueError(f"Theme: Invalid color value type: {type(value)}")

        # 1. Try wx.ColourDatabase for named colors (e.g. 'red', 'blue', 'LIGHT GREY')
        named_color = wx.Colour(value)
        if named_color.IsOk():
            return named_color

        # 2. Parse rgba(r, g, b, a)
        if value.startswith("rgba("):
            parts = re.findall(r"[\d.]+", value)
            if len(parts) != 4:
                raise ValueError(f"Theme: Invalid rgba format: {value}")
            try:
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                a = max(0, min(255, int(round(float(parts[3]) * 255))))
                return wx.Colour(r, g, b, a)
            except (ValueError, IndexError):
                raise ValueError(f"Theme: Invalid rgba format: {value}")

        # 3. Parse hex #RRGGBB or RRGGBB or #RRGGBBAA
        clean = value.lstrip("#")
        try:
            if len(clean) == 6:
                r = int(clean[0:2], 16)
                g = int(clean[2:4], 16)
                b = int(clean[4:6], 16)
                return wx.Colour(r, g, b)
            elif len(clean) == 8:
                r = int(clean[0:2], 16)
                g = int(clean[2:4], 16)
                b = int(clean[4:6], 16)
                a = int(clean[6:8], 16)
                return wx.Colour(r, g, b, a)
        except ValueError:
            pass

        # 4. Final attempt at direct wx.Colour constructor
        try:
            direct = wx.Colour(value)
            if direct.IsOk():
                return direct
        except Exception:
            pass

        raise ValueError(f"Theme: Invalid color format or unknown color name: '{value}'")

    def parse_color(self, value: str):
        """Public wrapper for _parse_color."""
        return self._parse_color(value)

    def _shift_color(self, color: 'wx.Colour', delta: int) -> 'wx.Colour':
        """Shift RGB channels by delta (±10), clamped 0-255, preserving alpha."""
        import wx
        r = max(0, min(255, color.Red() + delta))
        g = max(0, min(255, color.Green() + delta))
        b = max(0, min(255, color.Blue() + delta))
        a = color.Alpha()
        return wx.Colour(r, g, b, a)

    def color(self, token: str, state: int = 0) -> 'wx.Colour':
        """Resolve a color token to a wx.Colour. e.g. 'colors.accent.primary'."""
        logger.debug(f"Theme usage: resolve color '{token}' (state={state})")
        states = self.color_states(token)
        if state >= len(states):
            logger.warning(f"Theme: Requested state {state} for token '{token}' exceeds available states ({len(states)}).")
            return states[0]
        return states[state]

    def get_preset_colors(self) -> list['wx.Colour']:
        """Get list of preset colors from the theme."""
        raw_presets = self._resolve("colors.preset")
        if isinstance(raw_presets, list):
            colors = []
            for item in raw_presets:
                if isinstance(item, dict) and 'ref' in item:
                    color_str = self._resolve(item['ref'])
                elif isinstance(item, str):
                    color_str = self._resolve(item) if not item.startswith('#') and not item.startswith('rgba(') else item
                else:
                    color_str = item
                colors.append(self._parse_color(color_str))
            return colors
        
        logger.error("Theme: 'colors.preset' not found or invalid in theme data.")
        raise KeyError("colors.preset missing")

    def has_palette_color(self, token: str) -> bool:
        """Check if a palette color token exists."""
        palette = self._data.get("palette", {})
        return token in palette

    def color_states(self, token: str, states: int = 3) -> list['wx.Colour']:
        """Resolve a color token to a list of wx.Colour objects for [normal, hover, active] states."""
        raw = self._resolve(token)

        # Normalize to list and resolve each element
        if isinstance(raw, list):
            resolved_values = []
            for v in raw:
                if isinstance(v, dict) and 'ref' in v:
                    resolved_values.append(self._resolve(v['ref']))
                elif isinstance(v, str):
                    try:
                        resolved_values.append(self._resolve(v))
                    except KeyError:
                        resolved_values.append(v)
                else:
                    resolved_values.append(v)
            colors = [self._parse_color(rv) for rv in resolved_values]
        else:
            if isinstance(raw, dict) and 'ref' in raw:
                raw = self._resolve(raw['ref'])
            colors = [self._parse_color(raw)]

        # Pad with shifted colors
        while len(colors) < states:
            base = colors[-1]
            if len(colors) == 1:
                colors.append(self._shift_color(base, 10))  # hover
                colors.append(self._shift_color(base, -10)) # active
            elif len(colors) == 2:
                colors.append(self._shift_color(colors[1], -10))
            else:
                colors.append(base)

        return colors[:states]

    def size(self, token: str) -> int:
        """Resolve a spacing/size token to an int. e.g. 'spacing.lg'."""
        logger.debug(f"Theme usage: resolve size '{token}'")
        value = self._resolve(token)
        return int(value)

    def font(self, preset: str) -> 'wx.Font':
        """Resolve a font preset to a wx.Font."""
        logger.debug(f"Theme usage: resolve font preset '{preset}'")
        import wx
        spec = self._resolve(f"typography.presets.{preset}")

        if isinstance(spec, str) and spec.startswith("#"):
             # Failed resolution returned pink hex
             logger.error(f"Theme: Cannot create font for invalid preset '{preset}'")
             # Fallback to system font if resolution failed
             return wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

        # Resolve family
        family_spec = spec.get("family", "wx.FONTFAMILY_DEFAULT")
        family = self._resolve(family_spec["ref"]) if isinstance(family_spec, dict) else family_spec

        # Resolve size
        size_spec = spec.get("size", 11)
        size = int(self._resolve(size_spec["ref"]) if isinstance(size_spec, dict) else size_spec)

        # Resolve weight
        weight_spec = spec.get("weight", 400)
        weight = int(self._resolve(weight_spec["ref"]) if isinstance(weight_spec, dict) else weight_spec)

        weight_map = {
            400: wx.FONTWEIGHT_NORMAL,
            600: wx.FONTWEIGHT_SEMIBOLD,
            700: wx.FONTWEIGHT_BOLD,
        }
        wx_weight = weight_map.get(weight, wx.FONTWEIGHT_NORMAL)

        return wx.Font(
            size,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx_weight,
            faceName=family
        )
