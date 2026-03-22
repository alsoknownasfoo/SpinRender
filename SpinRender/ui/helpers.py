"""
Shared helper functions for unified component construction.
"""
import weakref
import wx
from SpinRender.core.theme import Theme
_theme = Theme.current()
from .text_styles import TextStyle, TextStyles


# Valid theme token paths for validation (Theme Schema)
VALID_BG_TOKENS = {
    'layout.main.frame.bg', 'layout.main.leftpanel.bg',
    'layout.main.header.bg', 'layout.main.rightpanel.bg',
    'colors.gray-dark', 'colors.gray-black', 'colors.transparent'
}
VALID_BORDER_TOKENS = {
    'borders.default.color', 'borders.subtle.color', 'borders.focus.color',
    'layout.main.divider.bg'
}
VALID_ACCENT_TOKENS = {
    'colors.primary', 'colors.secondary', 'colors.tertiary',
    'colors.ok', 'colors.warning', 'colors.error'
}
VALID_TEXT_TOKENS = {
    'text.body.color', 'text.subtitle.color', 'text.metadata.color',
    'text.subheader.color', 'text.button.color', 'text.label.color',
    'text.title.color'
}
ALL_VALID_TOKENS = (
    VALID_BG_TOKENS | VALID_BORDER_TOKENS | VALID_ACCENT_TOKENS | VALID_TEXT_TOKENS
)


# ---------------------------------------------------------------------------
# Global text registry for hot-reload
# ---------------------------------------------------------------------------

# Each entry: (weakref_to_widget, style_name, original_label)
_text_registry: list = []


def reapply_text_styles() -> None:
    """Re-apply font, color, and formatting to all live text widgets.

    Call this from any panel's reapply_theme() to hot-reload styled text.
    Dead widget references are pruned automatically.
    """
    live = []
    for ref, style_name, original_label in _text_registry:
        widget = ref()
        if widget:
            style = getattr(TextStyles, style_name)
            widget.SetFont(style.create_font())
            widget.SetForegroundColour(style.color)
            widget.SetLabel(style.format_text(original_label))
            live.append((ref, style_name, original_label))
    _text_registry[:] = live


# ---------------------------------------------------------------------------
# Text creation
# ---------------------------------------------------------------------------

def create_text(parent: wx.Window, label: str, style_name: str,
                color_token: str = None, **kwargs) -> wx.StaticText:
    """Create a themed, formatted wx.StaticText and register it for hot-reload.

    Args:
        parent:      Parent wx.Window.
        label:       Raw (un-formatted) label string. Formatting (e.g. uppercase)
                     is applied automatically from the style definition.
        style_name:  TextStyles alias (e.g. "header", "metadata", "subheader").
                     Must map to a layout.* or components.* YAML path.
        color_token: Optional theme token to override the style's default color
                     (e.g. "colors.primary" or an axis-specific token).
        **kwargs:    Additional wx.StaticText constructor args.

    Returns:
        wx.StaticText with font, color, and formatting applied.
    """
    style = getattr(TextStyles, style_name)
    formatted = style.format_text(label)
    txt = wx.StaticText(parent, label=formatted, **kwargs)
    txt.SetFont(style.create_font())
    color = _theme.color(color_token) if color_token else style.color
    txt.SetForegroundColour(color)

    # Pass through mouse clicks to parent (essential for labels inside
    # clickable containers like PresetCard, CustomButton)
    txt.Bind(wx.EVT_LEFT_DOWN, lambda e: e.Skip())

    _text_registry.append((weakref.ref(txt), style_name, label))
    return txt


# ---------------------------------------------------------------------------
# Frame / panel helpers
# ---------------------------------------------------------------------------

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


def create_section_label(parent, text, id="default"):
    """Create a section label with divider line."""
    from .custom_controls import SectionLabel
    return SectionLabel(parent, label=text, id=id)


def create_numeric_input(parent, value, unit, editable=True, min_val=None, max_val=None, id="slider", size=(100, 32), section=None):
    """Create a numeric input or display widget using consolidated CustomInput."""
    from .custom_controls import CustomInput
    v = float(value) if isinstance(value, str) else value

    inp = CustomInput(parent, value=v, unit=unit, min_val=min_val, max_val=max_val, id=id, size=size, section=section)
    if not editable:
        inp.Enable(False)
    return inp
