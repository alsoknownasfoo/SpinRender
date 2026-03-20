"""
SpinRender Theme Loader — YAML-based design tokens.

This module provides the Theme singleton that loads color, font, and spacing
tokens from YAML configuration. YAML loading is strictly required.
"""
import logging
import re
from pathlib import Path
from typing import Any, Optional

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
        path = (Path(__file__).parent.parent / "resources" / "themes" / f"{name}.yaml").resolve()
        
        if not path.exists():
            error_msg = f"Theme file not found: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        mtime = path.stat().st_mtime
        is_stale = mtime > cls._loaded_mtime or name != cls._loaded_name
        
        if cls._instance is not None and not force and not is_stale:
            return cls._instance

        if not _yaml_available:
            raise ImportError("PyYAML is not available. Theme system requires PyYAML.")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if cls._instance:
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
        return cls.load(name=cls._loaded_name if cls._loaded_name else "dark", force=True)

    @classmethod
    def current(cls) -> "Theme":
        if cls._instance is None:
            cls.load()
        return cls._instance

    def has_token(self, path: str) -> bool:
        """Check if a token path exists, following refs and merging inheritance."""
        try:
            res = self._resolve(path)
            return res is not None and res != "#FF00FF"
        except:
            return False

    def _get_raw(self, path: str) -> Any:
        """Internal direct lookup in data dict without ref following."""
        curr = self._data
        for k in path.split('.'):
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return None
        return curr

    def _resolve(self, path: str, visited: set = None) -> Any:
        """
        Resolve a dot-path token with robust Parent-Ref Recursive Lookup.
        
        Strategy:
        1. Start at data root.
        2. Traverse keys. If a node is a pointer (@ or {ref:}), follow it 
           to its target before continuing traversal.
        3. If a key is missing, probe parents for a 'ref' and retry from base.
        """
        if visited is None: visited = set()
        if not isinstance(path, str): return path
        if path.startswith("@"): path = path[1:]
        
        if path in visited: raise RecursionError(f"Circular reference detected at '{path}'")
        visited.add(path)

        # Fast path for literals
        if '.' not in path and path not in self._data:
            if path.startswith("#") or path.startswith("rgba(") or path.isalpha():
                return path

        parts = path.split(".")
        node = self._data
        
        for i, key in enumerate(parts):
            # 1. Follow any string pointers (@refs) mid-path
            while isinstance(node, str) and node.startswith("@"):
                node = self._resolve(node[1:], visited.copy())

            # 2. Look for key in current node (Dictionary lookup)
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                # 3. Inheritance: Climb parents of the ORIGINAL path to find a 'ref'
                for j in range(i, 0, -1):
                    parent_path = ".".join(parts[:j])
                    parent = self._get_raw(parent_path)
                    if isinstance(parent, dict) and "ref" in parent:
                        base_ref = parent["ref"]
                        remaining = ".".join(parts[j:])
                        return self._resolve(f"{base_ref}.{remaining}", visited.copy())
                
                return "#FF00FF"

        # 4. Final Leaf Follow (if result is a pointer)
        while isinstance(node, str) and node.startswith("@"):
            node = self._resolve(node[1:], visited.copy())

        return node

    # --- COLOR ENGINE ---

    def color(self, token: str, hovered: bool = False, pressed: bool = False, enabled: bool = True) -> 'wx.Colour':
        """Resolve a color token to a wx.Colour, considering component state.
        
        Priority: Disabled > Pressed > Hovered > Normal.
        """
        import wx
        states = self.color_states(token)
        
        final_color = states[0]
        state_name = "normal"

        if not enabled:
            final_color = states[3] if len(states) > 3 else self.disabled(states[0])
            state_name = "disabled"
        elif pressed:
            final_color = states[2] if len(states) > 2 else states[0]
            state_name = "pressed"
        elif hovered:
            final_color = states[1] if len(states) > 1 else states[0]
            state_name = "hovered"
            
        try:
            hex_val = final_color.GetAsString(wx.C2S_HTML_SYNTAX)
            logger.debug(f"Theme: color('{token}') -> state '{state_name}' -> {hex_val}")
        except:
            pass
            
        return final_color

    def color_states(self, token: str, states: int = 4) -> list['wx.Colour']:
        """Resolve a color token to [normal, hover, active, disabled] states."""
        import wx
        raw = self._resolve(token)
        
        # Fallback for style roles (e.g. "icon", "label") that aren't at root
        if raw is None or raw == "#FF00FF":
            style_raw = self._resolve(f"text.{token}")
            if isinstance(style_raw, dict):
                raw = style_raw

        if raw is None or raw == "#FF00FF":
            logger.error(f"Theme: Color token '{token}' not found.")
            pink = self._parse_color("#FF00FF")
            return [pink] * states

        # Extract defined states
        colors, source = self._extract_defined_states(raw, token)
        
        # Fill missing states
        final_colors, gen_count = self._fill_missing_states(colors)
        
        try:
            hex_list = [c.GetAsString(wx.C2S_HTML_SYNTAX) for c in final_colors[:states]]
            logger.debug(f"Theme: color_states('{token}') -> src={source} gen={gen_count} -> {hex_list}")
        except:
            pass

        return final_colors[:states]

    def _extract_defined_states(self, raw: Any, token: str) -> tuple[list[Optional['wx.Colour']], str]:
        res = [None, None, None, None] # [normal, hover, active, disabled]
        
        if isinstance(raw, list):
            for i, v in enumerate(raw[:4]):
                res[i] = self._parse_color(v)
            return res, "list"
        
        if isinstance(raw, dict):
            # Resolve .color explicitly if it's a component dict
            if "color" in raw:
                # If .color is itself a dict (stateful), recurse
                if isinstance(raw["color"], (dict, list)):
                    return self._extract_defined_states(raw["color"], f"{token}.color")
                res[0] = self._parse_color(raw["color"])
                return res, "dict.color"
                
            # Direct property mapping
            m = {"default": 0, "bg": 0, "value": 0, "hover": 1, "active": 2, "pressed": 2, "disabled": 3}
            found = False
            for k, idx in m.items():
                val = raw.get(k)
                if val:
                    res[idx] = self._parse_color(val)
                    found = True
            if found: return res, "dict"

        # Fallback: Treat as direct color value
        try:
            res[0] = self._parse_color(raw)
            return res, "direct"
        except ValueError:
            # If the raw value isn't a color string (e.g. it's a nested dict we missed), return Pink
            logger.error(f"Theme: Token '{token}' resolved to non-color value: {raw}")
            pink = self._parse_color("#FF00FF")
            return [pink] * 4, "error"

    def _fill_missing_states(self, colors: list[Optional['wx.Colour']]) -> tuple[list['wx.Colour'], int]:
        if not colors[0]:
            pink = self._parse_color("#FF00FF")
            return [pink] * 4, 0
            
        base = colors[0]
        gen_count = 0
        # 1. Fill Hover (Index 1)
        if not colors[1]:
            colors[1] = self._apply_auto_shift(base, "hover")
            gen_count += 1
        # 2. Fill Active (Index 2)
        if not colors[2]:
            colors[2] = self._apply_auto_shift(base, "active")
            gen_count += 1
        # 3. Fill Disabled (Index 3)
        if not colors[3]:
            colors[3] = self._apply_auto_shift(base, "disabled")
            gen_count += 1
            
        return colors, gen_count

    def _apply_auto_shift(self, base_color: 'wx.Colour', state: str) -> 'wx.Colour':
        import wx
        delta_raw = self._resolve(f"colors.auto_states.{state}")
        
        if not isinstance(delta_raw, str) or delta_raw == "#FF00FF":
            if state == "hover": return self._shift_color(base_color, 10)
            if state == "active": return self._shift_color(base_color, -10)
            return self.disabled(base_color)

        try:
            parts = [float(p) for p in re.findall(r"[-?\d.]+", delta_raw)]
            if state == "disabled" and len(parts) >= 4:
                alpha = int(parts[3] * 255) if parts[3] <= 1.0 else int(parts[3])
                return wx.Colour(base_color.Red(), base_color.Green(), base_color.Blue(), alpha)

            r = max(0, min(255, int(base_color.Red() + (parts[0] if len(parts) > 0 else 0))))
            g = max(0, min(255, int(base_color.Green() + (parts[1] if len(parts) > 1 else 0))))
            b = max(0, min(255, int(base_color.Blue() + (parts[2] if len(parts) > 2 else 0))))
            a = int(parts[3] * 255) if len(parts) >= 4 else base_color.Alpha()
            return wx.Colour(r, g, b, a)
        except:
            return base_color

    def disabled(self, color) -> 'wx.Colour':
        import wx
        if isinstance(color, wx.Colour):
            return wx.Colour(color.Red(), color.Green(), color.Blue(), 128)
        return self._parse_color("#FF00FF")

    def _parse_color(self, value: str) -> 'wx.Colour':
        """Parse color string to wx.Colour. Raises ValueError for invalid format."""
        import wx
        
        # 0. wx.Colour Passthrough (Critical for tests)
        if isinstance(value, wx.Colour):
            return value

        if not isinstance(value, str): 
            raise ValueError(f"Theme: Invalid color value type: {type(value)}")
        
        # 1. Handle @references
        if value.startswith("@"):
            resolved = self._resolve(value)
            if resolved == "#FF00FF": return wx.Colour(255, 0, 255)
            return self._parse_color(resolved)

        # 2. Parse rgba(r, g, b, a)
        if value.startswith("rgba("):
            parts = [float(p) for p in re.findall(r"[\d.]+", value)]
            if len(parts) == 4:
                return wx.Colour(int(parts[0]), int(parts[1]), int(parts[2]), int(round(parts[3] * 255)))
            raise ValueError(f"Theme: Invalid rgba format: {value}")

        # 3. Parse hex
        clean = value.lstrip("#")
        try:
            if len(clean) == 6:
                return wx.Colour(int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))
            if len(clean) == 8:
                return wx.Colour(int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16), int(clean[6:8], 16))
        except: pass

        # 4. Try direct construction (named colors)
        try:
            c = wx.Colour(value)
            if c.IsOk(): return c
        except: pass

        raise ValueError(f"Theme: Invalid color format or unknown color name: '{value}'")

    def _shift_color(self, color: 'wx.Colour', delta: int) -> 'wx.Colour':
        import wx
        return wx.Colour(
            max(0, min(255, color.Red() + delta)),
            max(0, min(255, color.Green() + delta)),
            max(0, min(255, color.Blue() + delta)),
            color.Alpha()
        )

    # --- PROPERTY ACCESSORS (Aliases to common literal tokens) ---

    @property
    def BLACK(self) -> 'wx.Colour': return self._parse_color("black")
    @property
    def WHITE(self) -> 'wx.Colour': return self._parse_color("white")
    @property
    def TRANSPARENT(self) -> 'wx.Colour': return self._parse_color("rgba(0,0,0,0)")

    # --- OTHER HELPERS ---

    def font_family(self, name: str) -> str:
        res = self._resolve(f"typography.families.{name}")
        return res if res != "#FF00FF" else "Arial"

    def font_size(self, name: str) -> int:
        res = self._resolve(f"typography.scale.{name}")
        try: return int(res)
        except: return 11

    def font_weight(self, name: str) -> int:
        res = self._resolve(f"typography.weights.{name}")
        try: return int(res)
        except: return 400

    def size(self, token: str) -> int: 
        val = self._resolve(token)
        try: return int(val)
        except: return 0
    
    def glyph(self, name: str) -> str:
        if not name or name.lower() == "none": return ""
        token = f"glyphs.{name.replace('glyphs.', '')}"
        val = self._resolve(token)
        return str(val) if isinstance(val, str) and not val.startswith("#") else ""

    def get_palette_color(self, name: str) -> 'wx.Colour': return self.color(f"colors.{name}")
    def get_preset_colors(self) -> list['wx.Colour']:
        raw = self._resolve("colors.preset")
        return [self._parse_color(v) for v in raw] if isinstance(raw, list) else []

    def font(self, token: str) -> 'wx.Font':
        """Resolve a font preset. Returns a bold 'Webdings' font if resolution fails."""
        import wx
        # 1. Resolve spec (Check for direct .font, then text.{token}.font, then legacy presets)
        spec = self._resolve(f"{token}.font")
        if not isinstance(spec, dict):
            spec = self._resolve(f"text.{token}.font")
        if not isinstance(spec, dict):
            spec = self._resolve(f"typography.presets.{token}")
        
        # 2. If resolution failed, return "Pink" equivalent for fonts: Webdings Symbols
        if not isinstance(spec, dict):
            logger.debug(f"Theme: Font preset '{token}' not found. Returning symbol fallback.")
            return wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName="Webdings")

        # 3. Resolve components
        family_raw = spec.get("typeface") or spec.get("family")
        family = self._resolve(family_raw) if family_raw else "#FF00FF"
        
        size_raw = spec.get("size")
        size_val = self._resolve(size_raw) if size_raw else "#FF00FF"
        
        weight_raw = spec.get("weight")
        weight_val = self._resolve(weight_raw) if weight_raw else "#FF00FF"

        # 4. Handle internal component resolution failure
        if "#FF00FF" in (family, size_val, weight_val):
            if logger.isEnabledFor(logging.DEBUG):
                missing = []
                if family == "#FF00FF": missing.append(f"typeface/family ({family_raw})")
                if size_val == "#FF00FF": missing.append(f"size ({size_raw})")
                if weight_val == "#FF00FF": missing.append(f"weight ({weight_raw})")
                logger.debug(f"Theme: Font preset '{preset}' has missing components: {', '.join(missing)}. Raw Spec: {spec}. Returning symbol fallback.")
            return wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName="Webdings")

        try:
            size = int(size_val)
            weight = int(weight_val)
            w_map = {100:wx.FONTWEIGHT_THIN, 200:wx.FONTWEIGHT_LIGHT, 300:wx.FONTWEIGHT_LIGHT, 400:wx.FONTWEIGHT_NORMAL, 
                     500:wx.FONTWEIGHT_NORMAL, 600:wx.FONTWEIGHT_SEMIBOLD, 700:wx.FONTWEIGHT_BOLD, 800:wx.FONTWEIGHT_BOLD, 900:wx.FONTWEIGHT_BOLD}
            
            return wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, w_map.get(weight, wx.FONTWEIGHT_NORMAL), faceName=family)
        except Exception as e:
            logger.debug(f"Theme: Failed to create font for '{preset}': {e}. (Family: {family}, Size: {size_val}, Weight: {weight_val})")
            return wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName="Webdings")

    def frame(self, path: str) -> dict[str, Any]: return self._resolve(f"components.{path}.frame")
    def border(self, role: str = "default") -> dict[str, Any]: return self._resolve(f"borders.{role}")
    def text_style(self, role: str) -> dict[str, Any]: return self._resolve(f"text.{role}")
