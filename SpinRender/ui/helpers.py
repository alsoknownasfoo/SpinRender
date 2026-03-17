#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Shared helper functions for unified component construction.
"""
import wx
from . import theme


# Valid theme token names for validation
VALID_BG_TOKENS = {
    'BG_PAGE', 'BG_PANEL', 'BG_INPUT', 'BG_SURFACE', 'BG_MODAL'
}
VALID_BORDER_TOKENS = {
    'BORDER_DEFAULT', 'BORDER_MODAL', 'BORDER_FOCUS'
}
VALID_ACCENT_TOKENS = {
    'ACCENT_CYAN', 'ACCENT_YELLOW', 'ACCENT_GREEN', 'ACCENT_ORANGE',
    'ACCENT_RED', 'ACCENT_AMBER', 'ACCENT_BLUE', 'ACCENT_PURPLE'
}
VALID_TEXT_TOKENS = {
    'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_MUTED'
}
ALL_VALID_TOKENS = (
    VALID_BG_TOKENS | VALID_BORDER_TOKENS | VALID_ACCENT_TOKENS | VALID_TEXT_TOKENS
)


def _resolve_token(token: str):
    """Resolve theme token string to actual colour value."""
    return getattr(theme, token)


def create_frame(parent: wx.Panel, style_token: str, **kwargs) -> wx.Panel:
    """
    Create a themed panel frame.

    Args:
        parent: Parent wx.Window
        style_token: Theme token name (e.g., 'BG_INPUT', 'BG_SURFACE')
        **kwargs: Additional wx.Panel constructor args

    Returns:
        wx.Panel with background colour from theme token

    Raises:
        ValueError: If token is not recognized
    """
    if style_token not in ALL_VALID_TOKENS:
        raise ValueError(f"Unknown theme token: {style_token}")

    frame = wx.Panel(parent, **kwargs)
    colour = _resolve_token(style_token)
    frame.SetBackgroundColour(colour)
    return frame


def create_text(parent: wx.Window, label: str, text_style, **kwargs) -> wx.StaticText:
    """
    Create StaticText with TextStyle applied.

    Args:
        parent: Parent wx.Window
        label: Text to display
        text_style: TextStyle object with font/color specifications
        **kwargs: Additional wx.StaticText constructor args

    Returns:
        wx.StaticText with font and foreground colour set, and mouse pass-through
        for click events (EVT_LEFT_DOWN calls event.Skip()).
    """
    text = wx.StaticText(parent, label=label, **kwargs)

    # Apply font from TextStyle
    if text_style:
        font = text_style.create_font()
        text.SetFont(font)

        # Apply foreground colour if specified
        if text_style.color:
            text.SetForegroundColour(text_style.color)

    # Enable mouse pass-through: clicks on the label propagate to parent
    # This is essential for non-interactive labels inside clickable containers
    # (e.g., PresetCard, CustomButton). The label will not consume the event.
    text.Bind(wx.EVT_LEFT_DOWN, lambda e: e.Skip())

    return text


def bind_mouse_events(widget: wx.Window,
                      hover_handler=None,
                      leave_handler=None,
                      click_handler=None) -> None:
    """
    Bind standard mouse event handlers to a widget.

    Args:
        widget: wx.Window to bind events to
        hover_handler: Callable for EVT_ENTER_WINDOW (mouse enter)
        leave_handler: Callable for EVT_LEAVE_WINDOW (mouse leave)
        click_handler: Callable for EVT_LEFT_DOWN (mouse click)
    """
    if hover_handler:
        widget.Bind(wx.EVT_ENTER_WINDOW, hover_handler)
    if leave_handler:
        widget.Bind(wx.EVT_LEAVE_WINDOW, leave_handler)
    if click_handler:
        widget.Bind(wx.EVT_LEFT_DOWN, click_handler)


def apply_disabled_state(widget: wx.Window, is_enabled: bool) -> None:
    """
    Apply disabled state visual effect to widget background.

    Uses theme.disabled() to apply 50% opacity to the current background colour.

    Args:
        widget: wx.Window to modify
        is_enabled: True for normal state, False for disabled
    """
    if not is_enabled:
        current_colour = widget.GetBackgroundColour()
        disabled_colour = theme.disabled(current_colour)
        widget.SetBackgroundColour(disabled_colour)
