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
        Theme.current().color("colors.primary")  # → wx.Colour
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
                # Fallback to ref if key not found locally
                if isinstance(current, dict) and "ref" in current:
                    try:
                        resolved = self._resolve(current["ref"])
                        if isinstance(resolved, dict) and key in resolved:
                            current = resolved[key]
                            continue
                    except:
                        pass
                return False
            current = current[key]
        return True

    def _resolve(self, path: str) -> Any:
        """
        Resolve a dot-path token, following 'ref' references.
        Supports both dict-style ref: {ref: "token"} and V2 string-style @token.
        Recursive: follows references until a terminal value is reached.
        Deep Inheritance: If a sub-key is missing in a local override, attempts
        to find it in the referenced base.
        """
        if not isinstance(path, str):
            return path

        if path.startswith("@"):
            path = path[1:]

        # If it's a simple hex/rgba or literal, return as-is
        if '.' not in path and path not in self._data:
            if path.startswith("#") or path.startswith("rgba(") or path.isalpha():
                return path

        node = self._data
        parts = path.split(".")
        
        for i, key in enumerate(parts):
            if not isinstance(node, dict):
                logger.error(f"Theme: Cannot traverse into {type(node)} at '{key}' in '{path}' (node: {node})")
                return "#FF00FF"

            if key in node:
                # 1. Found locally - enter it
                node = node[key]
            elif "ref" in node:
                # 2. Not found locally, but this LEVEL has a reference base.
                # Use the base to resolve the rest of the path.
                base_ref = node["ref"]
                remaining_path = ".".join(parts[i:])
                
                # Recursively resolve from the base reference
                return self._resolve(f"{base_ref}.{remaining_path}")
            else:
                # 3. Not found locally and no reference here to fall back to.
                logger.error(f"Theme: Undefined token: '{path}' (missing '{key}')")
                # DEBUG: Log keys in current node to help diagnose
                logger.error(f"Theme: Available keys in current node: {list(node.keys())}")
                return "#FF00FF"

            # If we are NOT at the leaf, and the current node is a reference,
            # we MUST resolve it now so we can traverse into it in the next loop.
            if i < len(parts) - 1:
                while (isinstance(node, dict) and "ref" in node) or (isinstance(node, str) and str(node).startswith("@")):
                    if isinstance(node, dict):
                        node = self._resolve(node["ref"])
                    else:
                        node = self._resolve(node)

        # Final Leaf Resolution: follow ref if present
        while (isinstance(node, dict) and "ref" in node) or (isinstance(node, str) and str(node).startswith("@")):
            if isinstance(node, dict):
                node = self._resolve(node["ref"])
            else:
                node = self._resolve(node)

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
        """Parse color string to wx.Colour. Supports hex, rgba, and @references."""
        import wx
        import re

        if not isinstance(value, str):
            raise ValueError(f"Theme: Invalid color value type: {type(value)}")

        # V2: Resolve string-based references before parsing
        if value.startswith("@"):
            resolved = self._resolve(value)
            if isinstance(resolved, str) and not resolved.startswith("@"):
                return self._parse_color(resolved)
            return resolved 

        # 1. Try wx.ColourDatabase for named colors
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
        """Resolve a color token to a wx.Colour. e.g. 'colors.primary'."""
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
        """Resolve a color token to a list of wx.Colour objects for [normal, hover, active] states.
        
        V2: Supports explicit 'hover' and 'pressed' sibling properties if token is a path
        to a value in a dictionary (e.g. components.button.close.frame.bg).
        """
        # 1. Resolve the main token
        raw = self._resolve(token)

        # 2. Case: Explicit list [normal, hover, active]
        if isinstance(raw, list):
            resolved_values = []
            for v in raw:
                resolved_values.append(self._resolve(v) if isinstance(v, str) and v.startswith("@") else v)
            colors = [self._parse_color(rv) for rv in resolved_values]
        
        # 3. Case: Explicit dictionary with hover/pressed keys
        elif isinstance(raw, dict) and ("hover" in raw or "pressed" in raw):
            normal = raw.get("bg") or raw.get("color") or raw.get("value")
            hover = raw.get("hover")
            pressed = raw.get("pressed")
            
            colors = [self._parse_color(normal)]
            if hover: colors.append(self._parse_color(hover))
            if pressed: colors.append(self._parse_color(pressed))
        
        # 4. Case: Dot-path fallback for siblings (e.g. token='...frame.bg' -> look for '...frame.hover')
        elif '.' in token:
            parent_path = ".".join(token.split(".")[:-1])
            leaf_key = token.split(".")[-1]
            
            try:
                parent_node = self._resolve(parent_path)
                if isinstance(parent_node, dict):
                    # If looking for 'bg', also check for 'hover' and 'pressed' in the same dict
                    colors = [self._parse_color(raw)]
                    
                    # Try to find stateful siblings
                    for state_key in ["hover", "pressed", "active"]:
                        if state_key in parent_node:
                            colors.append(self._parse_color(parent_node[state_key]))
                else:
                    colors = [self._parse_color(raw)]
            except Exception:
                colors = [self._parse_color(raw)]
        else:
            colors = [self._parse_color(raw)]

        # 5. Pad with shifted colors if not enough states provided
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
        """Resolve a font preset to a wx.Font.

        Supports V1 (typography.presets.{preset}) and V2 (text.{preset}.font) formats.
        """
        logger.debug(f"Theme usage: resolve font preset '{preset}'")
        import wx

        # Try V2 format first: text.{preset}.font
        v2_path = f"text.{preset}.font"
        spec = self._resolve(v2_path)

        # If resolution failed (pink hex), try V1 format
        if isinstance(spec, str) and spec.startswith("#"):
            logger.debug(f"V2 font path '{v2_path}' not found, trying V1 format")
            spec = self._resolve(f"typography.presets.{preset}")

        if isinstance(spec, str) and spec.startswith("#"):
             # Failed resolution returned pink hex
             logger.error(f"Theme: Cannot create font for invalid preset '{preset}'")
             # Fallback to system font if resolution failed
             return wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

        # Resolve family (V2 uses 'typeface', V1 uses 'family')
        family_spec = spec.get("typeface") or spec.get("family", "wx.FONTFAMILY_DEFAULT")
        if isinstance(family_spec, dict) and "ref" in family_spec:
            family = self._resolve(family_spec["ref"])
        elif isinstance(family_spec, str) and family_spec.startswith("@"):
            family = self._resolve(family_spec[1:])  # strip '@'
        else:
            family = family_spec

        # Resolve size
        size_spec = spec.get("size", 11)
        if isinstance(size_spec, dict) and "ref" in size_spec:
            size = int(self._resolve(size_spec["ref"]))
        elif isinstance(size_spec, str) and size_spec.startswith("@"):
            size = int(size_spec[1:])
        else:
            size = int(size_spec) if not isinstance(size_spec, (int, float)) else int(size_spec)

        # Resolve weight
        weight_spec = spec.get("weight", 400)
        if isinstance(weight_spec, dict) and "ref" in weight_spec:
            weight = int(self._resolve(weight_spec["ref"]))
        elif isinstance(weight_spec, str) and weight_spec.startswith("@"):
            weight = int(weight_spec[1:])
        else:
            weight = int(weight_spec) if not isinstance(weight_spec, (int, float)) else int(weight_spec)

        weight_map = {
            100: wx.FONTWEIGHT_THIN,
            200: wx.FONTWEIGHT_LIGHT,
            300: wx.FONTWEIGHT_LIGHT,
            400: wx.FONTWEIGHT_NORMAL,
            500: wx.FONTWEIGHT_NORMAL,
            600: wx.FONTWEIGHT_SEMIBOLD,
            700: wx.FONTWEIGHT_BOLD,
            800: wx.FONTWEIGHT_BOLD,
            900: wx.FONTWEIGHT_BOLD,
        }
        wx_weight = weight_map.get(weight, wx.FONTWEIGHT_NORMAL)

        return wx.Font(
            size,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx_weight,
            faceName=family
        )

    def frame(self, path: str) -> dict[str, Any]:
        """Resolve a full frame object (bg, radius, border, etc.)."""
        return self._resolve(f"components.{path}.frame")

    def border(self, role: str = "default") -> dict[str, Any]:
        """Resolve a semantic border role."""
        return self._resolve(f"borders.{role}")

    def text_style(self, role: str) -> dict[str, Any]:
        """Resolve a global text style role (font + color)."""
        return self._resolve(f"text.{role}")

    def glyph(self, name: str) -> str:
        """Get a glyph Unicode string by name from the glyphs section.

        Example:
            theme.glyph("render-action") → "\U000F0A1C"
            theme.glyph("glyphs.render-action") → "\U000F0A1C"

        Returns:
            Unicode string representing the glyph, or empty string if not found or "None".
        """
        if not name or name.lower() == "none":
            return ""

        # Strip 'glyphs.' prefix if provided (allows direct use of locale icon_ref)
        token_name = name.replace("glyphs.", "")
        token = f"glyphs.{token_name}"
        value = self._resolve(token)

        # Handle 'None' as a value in YAML
        if isinstance(value, str) and value.lower() == "none":
            return ""

        # If resolution failed, _resolve returns pink hex; detect that
        if isinstance(value, str) and (value == "#FF00FF" or value == "#FF00FFFF"):
            # Only warn if it's not a known null-ish value
            logger.warning(f"Theme: Glyph '{token_name}' not found")
            return ""

        # Return string value directly
        if isinstance(value, str):
            return value

        logger.warning(f"Theme: Glyph '{token_name}' has unexpected type {type(value)}")
        return ""
