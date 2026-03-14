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

# State
DISABLED_ALPHA = 128   # 50% opacity for disabled widgets


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
