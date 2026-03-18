#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
SpinRender Design System — single source of truth for colors and typography.

Backward compatibility layer: All constants now sourced from YAML theme via
core.theme.Theme singleton. This module maintains 100% API compatibility while
enabling dynamic theme loading.

Do NOT import from this module directly in new code. Instead, use:
    from core.theme import Theme
    Theme.current().colour("token")
"""
import logging
import wx

logger = logging.getLogger("SpinRender")

# ---------------------------------------------------------------------------
# Font Families (from foundation.fonts) - keep as constants (not theme-driven)
# ---------------------------------------------------------------------------
from SpinRender.foundation.fonts import JETBRAINS_MONO, MDI_FONT_FAMILY, OSWALD, INTER

FONT_MONO     = JETBRAINS_MONO
FONT_ICONS    = MDI_FONT_FAMILY
FONT_DISPLAY  = OSWALD
FONT_INTER    = INTER

# Font size scale (point sizes) - keep constants for backward compatibility
FONT_SIZE_XS     = 8
FONT_SIZE_SM     = 9
FONT_SIZE_BASE   = 11
FONT_SIZE_MD     = 13
FONT_SIZE_LG     = 14
FONT_SIZE_XL     = 18
FONT_SIZE_ICON   = 14
FONT_SIZE_ICON_LG = 20

# Font weight constants
FONT_WEIGHT_NORMAL   = 400
FONT_WEIGHT_SEMIBOLD = 600
FONT_WEIGHT_BOLD     = 700


# ---------------------------------------------------------------------------
# Color Constants - sourced from YAML theme via Theme singleton
# ---------------------------------------------------------------------------
# Initialize Theme to get actual values. Fallback to hardcoded if YAML unavailable.
try:
    from SpinRender.core.theme import Theme
    _theme = Theme.load("dark")
except (ImportError, FileNotFoundError, ValueError, KeyError) as e:
    # Theme loading failed - using fallback constants
    logger.warning(f"Theme loading failed, using fallback: {e}")
    BG_PAGE    = wx.Colour(18,  18,  18)
    BG_PANEL   = wx.Colour(26,  26,  26)
    BG_INPUT   = wx.Colour(13,  13,  13)
    BG_SURFACE = wx.Colour(34,  34,  34)
    BG_MODAL   = wx.Colour(18,  18,  18)
    TEXT_PRIMARY   = wx.Colour(224, 224, 224)
    TEXT_SECONDARY = wx.Colour(119, 119, 119)
    TEXT_MUTED     = wx.Colour(85,  85,  85)
    ACCENT_CYAN   = wx.Colour(0,   188, 212)
    ACCENT_YELLOW = wx.Colour(255, 214, 0)
    ACCENT_GREEN  = wx.Colour(76,  175, 80)
    ACCENT_ORANGE = wx.Colour(255, 107, 53)
    ACCENT_RED    = wx.Colour(255,  59,  48)  # Error/danger red
    ACCENT_RED    = wx.Colour(255,  59,  48)  # Error/danger red
    BORDER_DEFAULT = wx.Colour(31, 31, 31)
    BORDER_MODAL   = wx.Colour(51, 51, 51)
    BORDER_FOCUS   = wx.Colour(0, 188, 212)
    DISABLED_ALPHA = 128
    PRESET_RED    = wx.Colour(255, 107, 107)
    PRESET_AMBER  = wx.Colour(255, 180, 107)
    PRESET_BLUE   = wx.Colour(77, 150, 255)
    PRESET_PURPLE = wx.Colour(170, 107, 255)
    DANGER_DARK   = wx.Colour(140, 0, 0)
    DANGER_HOVER  = wx.Colour(220, 20, 20)
    DANGER_MEDIUM = wx.Colour(180, 0, 0)
    WHITE        = wx.Colour(255, 255, 255)
    WHITE_ALPHA_20 = wx.Colour(255, 255, 255, 51)
    WHITE_ALPHA_30 = wx.Colour(255, 255, 255, 77)
    WHITE_ALPHA_40 = wx.Colour(255, 255, 255, 102)
    WHITE_ALPHA_68 = wx.Colour(255, 255, 255, 173)
    BLACK = wx.Colour(0, 0, 0)
    TRANSPARENT = wx.Colour(0, 0, 0, 0)
    HOVER_HIGHLIGHT = wx.Colour(120, 120, 120)
    SCROLLBAR_GREY = wx.Colour(50, 50, 50)
    BG_OUTPUT_PREVIEW = wx.Colour(10, 10, 10)
    GREY_100 = wx.Colour(100, 100, 100)
else:
    t = _theme  # shorthand

    # --- Backgrounds ---
    BG_PAGE    = t.colour("colors.bg.page")
    BG_PANEL   = t.colour("colors.bg.panel")
    BG_INPUT   = t.colour("colors.bg.input")
    BG_SURFACE = t.colour("colors.bg.surface")
    BG_MODAL   = t.colour("colors.bg.page")  # unify with BG_PAGE

    # --- Text ---
    TEXT_PRIMARY   = t.colour("colors.text.primary")
    TEXT_SECONDARY = t.colour("colors.text.secondary")
    TEXT_MUTED     = t.colour("colors.text.muted")

    # --- Accents ---
    ACCENT_CYAN   = t.colour("colors.accent.primary")
    ACCENT_YELLOW = t.colour("colors.accent.secondary")
    ACCENT_GREEN  = t.colour("colors.accent.success")
    ACCENT_ORANGE = t.colour("colors.accent.warning")
    ACCENT_RED    = t.colour("colors.accent.danger") if t.has_token("colors.accent.danger") else wx.Colour(255, 59, 48)

    # --- Borders ---
    BORDER_DEFAULT = t.colour("colors.border.default")
    BORDER_MODAL   = BORDER_DEFAULT  # reuse
    BORDER_FOCUS   = t.colour("colors.border.focus")

    # --- Preset colors ---
    # Get preset colors using new public API
    try:
        preset_list = t.get_preset_colors()
        if len(preset_list) >= 4:
            PRESET_RED, PRESET_AMBER, PRESET_BLUE, PRESET_PURPLE = preset_list[:4]
        else:
            raise ValueError("Not enough preset colors")
    except (KeyError, AttributeError, ValueError):
        # Fallback if theme doesn't have preset colors
        PRESET_RED = wx.Colour(255, 107, 107)
        PRESET_AMBER = wx.Colour(255, 180, 107)
        PRESET_BLUE = wx.Colour(77, 150, 255)
        PRESET_PURPLE = wx.Colour(170, 107, 255)

    # --- Danger colors (hardcoded for now, not in YAML) ---
    DANGER_DARK   = wx.Colour(140, 0, 0)
    DANGER_HOVER  = wx.Colour(220, 20, 20)
    DANGER_MEDIUM = wx.Colour(180, 0, 0)

    # --- Overlay colors with alpha (rgba) ---
    WHITE = wx.Colour(255, 255, 255)
    # Use theme's parse_colour public method
    try:
        WHITE_ALPHA_20 = t.parse_colour("rgba(255,255,255,0.08)")  # overlay-faint
        WHITE_ALPHA_30 = t.parse_colour("rgba(255,255,255,0.16)")  # overlay-light
        WHITE_ALPHA_40 = t.parse_colour("rgba(255,255,255,0.27)")  # overlay-medium
        WHITE_ALPHA_68 = t.parse_colour("rgba(255,255,255,0.68)")  # scaled from original
    except (AttributeError, ValueError):
        WHITE_ALPHA_20 = wx.Colour(255, 255, 255, 51)
        WHITE_ALPHA_30 = wx.Colour(255, 255, 255, 77)
        WHITE_ALPHA_40 = wx.Colour(255, 255, 255, 102)
        WHITE_ALPHA_68 = wx.Colour(255, 255, 255, 173)

    # --- Basic colors ---
    try:
        BLACK = t.colour("palette.black-solid")
    except KeyError:
        BLACK = wx.Colour(0, 0, 0)
    try:
        TRANSPARENT = t.parse_colour("rgba(0,0,0,0)")
    except (AttributeError, ValueError):
        TRANSPARENT = wx.Colour(0, 0, 0, 0)

    # --- Misc UI colors ---
    HOVER_HIGHLIGHT = t.colour("colors.bg.hover")  # Use hover background
    try:
        SCROLLBAR_GREY = t.colour("palette.neutral-10")
    except KeyError:
        SCROLLBAR_GREY = wx.Colour(50, 50, 50)
    try:
        BG_OUTPUT_PREVIEW = t.colour("colors.bg.output")
    except KeyError:
        BG_OUTPUT_PREVIEW = wx.Colour(10, 10, 10)
    try:
        GREY_100 = t.colour("palette.neutral-11")  # secondary text
    except KeyError:
        GREY_100 = wx.Colour(100, 100, 100)

    # --- Font sizes and weights (already defined as constants above) ---
    DISABLED_ALPHA = 128  # opacity for disabled widgets


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def disabled(color: wx.Colour) -> wx.Colour:
    """Return a copy of *color* at disabled opacity."""
    return wx.Colour(color.Red(), color.Green(), color.Blue(), DISABLED_ALPHA)
