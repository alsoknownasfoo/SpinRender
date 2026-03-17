"""
Icon glyph mappings for UI.

These map semantic icon names to their Unicode/character representation.
The actual rendering uses the appropriate font (MDI) to display these.
"""

# Status icons used in dependency dialogs and other UI
# These are Material Design Icons (MDI) hex code values
STATUS_ICONS = {
    "mdi-check-circle": "\U000F05E0",
    "mdi-close-circle": "\U000F05E8",
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

__all__ = ["STATUS_ICONS", "UI_ICONS"]
