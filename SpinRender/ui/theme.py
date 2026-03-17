#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
SpinRender Design System — single source of truth for colors and typography.
All UI files import from here. Never define wx.Colour values elsewhere.
"""
import wx


# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------

# Backgrounds
BG_PAGE    = wx.Colour(18,  18,  18)   # outermost page/window bg
BG_PANEL   = wx.Colour(26,  26,  26)   # side panel, scrolled areas
BG_INPUT   = wx.Colour(13,  13,  13)   # text inputs, numeric inputs
BG_SURFACE = wx.Colour(34,  34,  34)   # raised surfaces, cards
BG_MODAL   = wx.Colour(18,  18,  18)   # modal dialog background (unified)

# Text
TEXT_PRIMARY   = wx.Colour(224, 224, 224)
TEXT_SECONDARY = wx.Colour(119, 119, 119)
TEXT_MUTED     = wx.Colour(85,  85,  85)

# Accents
ACCENT_CYAN   = wx.Colour(0,   188, 212)  # primary accent / interactive
ACCENT_YELLOW = wx.Colour(255, 214, 0)    # secondary / highlights
ACCENT_GREEN  = wx.Colour(76,  175, 80)   # success / info
ACCENT_ORANGE = wx.Colour(255, 107, 53)   # warnings / badges

# Structure
BORDER_DEFAULT = wx.Colour(31, 31, 31)   # dividers, control borders
BORDER_MODAL   = wx.Colour(51, 51, 51)   # dialog chrome borders
BORDER_FOCUS   = wx.Colour(0, 188, 212)   # focused input border (cyan)

# State
DISABLED_ALPHA = 128   # 50% opacity for disabled widgets

# Preset card accent colors
PRESET_RED    = wx.Colour(255, 107, 107)
PRESET_AMBER  = wx.Colour(255, 180, 107)
PRESET_BLUE   = wx.Colour(77, 150, 255)
PRESET_PURPLE = wx.Colour(170, 107, 255)

# Danger button states (for CustomButton)
DANGER_DARK   = wx.Colour(140, 0, 0)      # pressed
DANGER_HOVER  = wx.Colour(220, 20, 20)    # hover
DANGER_MEDIUM = wx.Colour(180, 0, 0)      # normal danger bg

# White with alpha overlays (for hover/pressed effects)
WHITE        = wx.Colour(255, 255, 255)
WHITE_ALPHA_20 = wx.Colour(255, 255, 255, 51)   # 0.2 alpha
WHITE_ALPHA_30 = wx.Colour(255, 255, 255, 77)   # 0.3 alpha
WHITE_ALPHA_40 = wx.Colour(255, 255, 255, 102)  # 0.4 alpha
WHITE_ALPHA_68 = wx.Colour(255, 255, 255, 173)  # 0.68 alpha

# Basic black
BLACK = wx.Colour(0, 0, 0)
TRANSPARENT = wx.Colour(0, 0, 0, 0)

# Hover highlight for color swatches
HOVER_HIGHLIGHT = wx.Colour(120, 120, 120)

# Scrollbar / minor UI
SCROLLBAR_GREY = wx.Colour(50, 50, 50)

# Output preview background (very dark)
BG_OUTPUT_PREVIEW = wx.Colour(10, 10, 10)

# Inactive button / disabled text
GREY_100 = wx.Colour(100, 100, 100)


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

FONT_MONO   = "JetBrains Mono"
FONT_ICONS  = "Material Design Icons"
FONT_DISPLAY = "Oswald"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def disabled(color: wx.Colour) -> wx.Colour:
    """Return a copy of *color* at disabled opacity."""
    return wx.Colour(color.Red(), color.Green(), color.Blue(), DISABLED_ALPHA)
