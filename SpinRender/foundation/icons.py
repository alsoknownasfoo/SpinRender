"""
Icon glyph mappings for UI.

These map semantic icon names to their Unicode/character representation.
The actual rendering uses the appropriate font (MDI) to display these.
"""
from SpinRender.core.theme import Theme

# Status icons used in dependency dialogs and other UI
# These are Material Design Icons (MDI) hex code values
STATUS_ICONS = {
    "mdi-check-circle": "\U000F05E0",
    "mdi-close-circle": "\U000F05E8",
    "mdi-close": "\U000F0156",  # Plain X for missing dependencies
}

# Commonly used UI icons (subset from CustomButton.ICONS)
UI_ICONS = {
    # Simple glyphs
    "play": "▶",
    "pause": "⏸",
    "stop": "⏹",
    "eye": "👁",
    "save": "💾",
    "settings": "⚙",
    "check": "✓",
    "alert": "⚠",
    "download": "⬇",
    "folder": "📁",
    "close": "✕",

    # MDI hex codes (v7.x Desktop)
    "mdi-play": "\U000F040D",
    "mdi-stop": "\U000F04DB",
    "mdi-folder": "\U000F024B",
    "mdi-check": "\U000F012C",
    "mdi-alert": "\U000F0026",
    "mdi-trash-can-outline": "\U000F0A7A",
    "mdi-close": "\U000F0156",
    "mdi-cog": "\U000F0493",
    "mdi-download": "\U000F01DA",
    "mdi-video-vintage": "\U000F0A1C",
    "mdi-information-outline": "\U000F02FD",
    "mdi-exit-to-app": "\U000F0206",
    "mdi-palette": "\U000F03E8",
}

def get_glyph(name: str) -> str:
    """
    Get a glyph by name.
    Prioritizes Theme resolution, falls back to legacy UI_ICONS/STATUS_ICONS.
    """
    # 1. Try theme
    try:
        t = Theme.current()
        # Clean 'mdi-' if present for theme lookup
        clean_name = name.replace('mdi-', '')
        val = t.glyph(clean_name)
        if val:
            return val
    except Exception:
        pass

    # 2. Try legacy mappings
    if name in UI_ICONS:
        return UI_ICONS[name]
    if name in STATUS_ICONS:
        return STATUS_ICONS[name]
        
    return name

__all__ = ["STATUS_ICONS", "UI_ICONS", "get_glyph"]
