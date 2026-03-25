"""
Validation utilities for the SpinRender theme system.

Provides:
- Token resolution validation
- WCAG contrast ratio checking
- Theme schema verification (when using YAML configs)
"""
import wx
from SpinRender.core.theme import Theme
_theme = Theme.current()
from typing import List, Tuple, Optional


# ---------------------------------------------------------------------------
# Token Resolution Validation
# ---------------------------------------------------------------------------

def validate_all_tokens() -> List[str]:
    """
    Validate that all required theme tokens are defined and resolve to valid colors.

    Returns:
        List of error messages. Empty list indicates success.

    Checks:
        - All tokens listed in helpers.VALID_BG_TOKENS, etc. resolve via Theme.color()
        - Each token is a wx.Colour instance
        - Color values are within valid RGB(A) ranges
    """
    from .helpers import ALL_VALID_TOKENS

    errors = []

    for token in ALL_VALID_TOKENS:
        try:
            color = _theme.color(token)
        except Exception as e:
            errors.append(f"Token {token} failed to resolve: {e}")
            continue

        # Check type
        if not isinstance(color, wx.Colour):
            errors.append(f"Token {token} is not a wx.Colour (type: {type(color).__name__})")
            continue

        # Check RGB range
        for channel, name in [(color.Red(), "Red"), (color.Green(), "Green"), (color.Blue(), "Blue")]:
            if not (0 <= channel <= 255):
                errors.append(f"Token {token} has {name} value {channel} outside 0-255 range")

        # Check alpha (if set) is 0-255
        alpha = color.Alpha()
        if alpha is not None and not (0 <= alpha <= 255):
            errors.append(f"Token {token} has alpha value {alpha} outside 0-255 range")

    return errors


# ---------------------------------------------------------------------------
# WCAG Contrast Ratio Checking
# ---------------------------------------------------------------------------

class ContrastChecker:
    """
    Utility for checking color contrast according to WCAG 2.1 guidelines.

    Computes contrast ratio between foreground and background colors.
    AA standards:
      - Normal text: 4.5:1 minimum
      - Large text: 3:1 minimum
    """

    @staticmethod
    def _srgb_to_linear(c: float) -> float:
        """Convert sRGB color channel (0-255) to linear RGB (0-1)."""
        c = c / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    @staticmethod
    def relative_luminance(color: wx.Colour) -> float:
        """
        Calculate relative luminance of a color per WCAG 2.1.

        Args:
            color: wx.Colour object

        Returns:
            Luminance value between 0.0 (dark) and 1.0 (light)
        """
        r = ContrastChecker._srgb_to_linear(color.Red())
        g = ContrastChecker._srgb_to_linear(color.Green())
        b = ContrastChecker._srgb_to_linear(color.Blue())
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @staticmethod
    def contrast_ratio(fg: wx.Colour, bg: wx.Colour) -> float:
        """
        Calculate WCAG contrast ratio between two colors.

        Formula: (L1 + 0.05) / (L2 + 0.05) where L1 is lighter.

        Args:
            fg: Foreground color (text)
            bg: Background color

        Returns:
            Contrast ratio as a float (e.g., 4.5, 7.2, 21.0)
        """
        L1 = ContrastChecker.relative_luminance(fg)
        L2 = ContrastChecker.relative_luminance(bg)

        # Ensure L1 is the lighter color
        if L1 < L2:
            L1, L2 = L2, L1

        return (L1 + 0.05) / (L2 + 0.05)

    @staticmethod
    def meets_aa(ratio: float, large_text: bool = False) -> bool:
        """
        Check if contrast ratio meets WCAG AA standard.

        Args:
            ratio: Contrast ratio (from contrast_ratio())
            large_text: True if text is considered "large" (≥18pt or 14pt bold)

        Returns:
            True if ratio meets or exceeds AA threshold
        """
        threshold = 3.0 if large_text else 4.5
        return ratio >= threshold

    @staticmethod
    def check_contrast(fg: wx.Colour, bg: wx.Colour, large_text: bool = False) -> Tuple[bool, float, str]:
        """
        Full contrast check with diagnostic message.

        Args:
            fg: Foreground text color
            bg: Background color
            large_text: Whether text is large

        Returns:
            Tuple of (passes_aa, ratio, message)
        """
        ratio = ContrastChecker.contrast_ratio(fg, bg)
        passes = ContrastChecker.meets_aa(ratio, large_text)
        threshold = 3.0 if large_text else 4.5

        status = "PASS" if passes else "FAIL"
        message = f"{status}: contrast ratio {ratio:.2f}:1 (AA requires ≥{threshold}:1 for {'large text' if large_text else 'normal text'})"
        return passes, ratio, message


# ---------------------------------------------------------------------------
# Theme Configuration Validation (for YAML-based themes - future)
# ---------------------------------------------------------------------------

def validate_theme_schema(theme_data: dict) -> List[str]:
    """
    Validate a YAML theme configuration dict for required structure.

    Args:
        theme_data: Parsed YAML dict (from theme.load())

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Top-level keys
    required_keys = {'meta', 'palette', 'colors', 'typography', 'spacing', 'borders'}
    for key in required_keys:
        if key not in theme_data:
            errors.append(f"Missing required top-level key: {key}")

    # Palette entries should be hex colors or rgba()
    if 'palette' in theme_data:
        for name, value in theme_data['palette'].items():
            if not isinstance(value, str):
                errors.append(f"Palette entry '{name}' must be a string (got {type(value).__name__})")
            elif not (value.startswith('#') or value.startswith('rgba(')):
                errors.append(f"Palette entry '{name}' is not a valid hex or rgba() format: {value}")

    # Semantic colors should use {ref: ...} pattern exclusively
    if 'colors' in theme_data:
        def check_colors_subtree(path: str, value):
            """Recursively validate the colors tree. All leaf values must be {ref: 'palette.xxx'}."""
            if isinstance(value, dict):
                if 'ref' in value:
                    # Leaf node with ref - validate it
                    ref_val = value['ref']
                    if not isinstance(ref_val, str) or not ref_val.startswith('palette.'):
                        errors.append(f"Invalid ref at {path}: {ref_val}")
                else:
                    # Intermediate node: recurse into children
                    for k, v in value.items():
                        child_path = f"{path}.{k}" if path else k
                        check_colors_subtree(child_path, v)
            elif isinstance(value, list):
                # Lists contain items that should be {ref: ...}
                for i, item in enumerate(value):
                    child_path = f"{path}[{i}]"
                    check_colors_subtree(child_path, item)
            else:
                # Plain value (string, number, etc.) - invalid in colors tree
                errors.append(f"At {path}: expected {{ref: 'palette.xxx'}} but got {type(value).__name__}")

        check_colors_subtree('colors', theme_data['colors'])

    # Typography presets should have family, size, weight
    if 'typography' in theme_data and 'presets' in theme_data['typography']:
        for preset_name, preset_def in theme_data['typography']['presets'].items():
            if not isinstance(preset_def, dict):
                errors.append(f"Typography preset '{preset_name}' must be a dict")
                continue
            for field in ('family', 'size', 'weight'):
                if field not in preset_def:
                    errors.append(f"Typography preset '{preset_name}' missing '{field}' field")

    return errors

