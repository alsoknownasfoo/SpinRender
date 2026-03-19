#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Shared helper functions for unified component construction.
"""
import wx
from SpinRender.core.theme import Theme
_theme = Theme.current()
from .text_styles import TextStyle


# Valid theme token paths for validation (V2 Mastering Schema)
VALID_BG_TOKENS = {
    'colors.bg.page', 'colors.bg.panel', 'colors.bg.surface', 
    'components.main.frame.bg', 'components.main.leftpanel.bg'
}
VALID_BORDER_TOKENS = {
    'borders.default.color', 'borders.subtle.color', 'borders.focus.color',
    'components.main.divider.bg'
}
VALID_ACCENT_TOKENS = {
    'colors.primary', 'colors.secondary', 'colors.success',
    'colors.red', 'colors.orange', 'colors.cyan', 'colors.purple'
}
VALID_TEXT_TOKENS = {
    'text.body.color', 'text.subtitle.color', 'text.metadata.color',
    'text.subheader.color', 'text.button.color', 'text.label.color'
}
ALL_VALID_TOKENS = (
    VALID_BG_TOKENS | VALID_BORDER_TOKENS | VALID_ACCENT_TOKENS | VALID_TEXT_TOKENS
)


def _resolve_token(token: str):
    """Resolve theme token path to actual color value."""
    return _theme.color(token)


def create_frame(parent: wx.Panel, style_token: str, **kwargs) -> wx.Panel:
    """
    Create a themed panel frame.

    Args:
        parent: Parent wx.Window
        style_token: Theme token path (e.g., 'colors.bg.input', 'colors.bg.surface')
        **kwargs: Additional wx.Panel constructor args

    Returns:
        wx.Panel with background color from theme token

    Raises:
        ValueError: If token is not recognized
    """
    if style_token not in ALL_VALID_TOKENS:
        raise ValueError(f"Unknown theme token: {style_token}")

    frame = wx.Panel(parent, **kwargs)
    color = _resolve_token(style_token)
    frame.SetBackgroundColour(color)
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
        wx.StaticText with font and foreground color set, and mouse pass-through
        for click events (EVT_LEFT_DOWN calls event.Skip()).
    """
    text = wx.StaticText(parent, label=label, **kwargs)

    # Apply font from TextStyle
    if text_style:
        font = text_style.create_font()
        text.SetFont(font)

        # Apply foreground color if specified
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

    Uses _theme.disabled() to apply 50% opacity to the current background color.

    Args:
        widget: wx.Window to modify
        is_enabled: True for normal state, False for disabled
    """
    if not is_enabled:
        current_color = widget.GetBackgroundColor()
        disabled_color = _theme.disabled(current_color)
        widget.SetBackgroundColour(disabled_color)


def create_section_label(parent, text):
    """Create a section label with divider line."""
    panel = wx.Panel(parent)
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(panel, label=text)
    label.SetForegroundColour(_theme.color("colors.primary"))
    label.SetFont(TextStyle(family=_theme.font_family("display"), size=13, weight=600).create_font())
    sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
    line = wx.Panel(panel, size=(60, 1))
    line.SetBackgroundColour(_theme.color("colors.border.default"))
    sizer.Add(line, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
    panel.SetSizerAndFit(sizer)
    return panel


def create_numeric_input(parent, value, unit, editable=True, min_val=None, max_val=None):
    """Create a numeric input or display widget."""
    from .custom_controls import NumericInput, NumericDisplay
    v = float(value) if isinstance(value, str) else value
    if editable:
        return NumericInput(parent, value=v, unit=unit, min_val=min_val, max_val=max_val, size=(100, 32))
    else:
        return NumericDisplay(parent, value=v, unit=unit, size=(100, 32))
