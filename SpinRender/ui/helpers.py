"""
Shared helper functions for unified component construction.
"""
import html
import logging
import re
import weakref
from pathlib import Path
from typing import Optional

import wx
import wx.svg

from SpinRender.core.theme import Theme

_logger = logging.getLogger("SpinRender")
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
    'dividers.default.color', 'layout.main.divider.bg'
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

# Each entry:
# (weakref_to_widget, style_name, original_label, color_token,
#  link_suffix_arrow, link_suffix_color_token)
_text_registry: list = []


def reapply_text_styles() -> None:
    """Re-apply font, color, and formatting to all live text widgets.

    Call this from any panel's reapply_theme() to hot-reload styled text.
    Dead widget references are pruned automatically.
    """
    live = []
    for ref, style_name, original_label, color_token, link_suffix_arrow, link_suffix_color_token in _text_registry:
        widget = ref()
        if widget:
            style = getattr(TextStyles, style_name)
            formatted = style.format_text(original_label)
            widget.SetFont(style.create_font())
            color = _resolve_text_foreground(style_name, color_token)
            widget.SetForegroundColour(color)
            _apply_link_suffix_label(
                widget,
                formatted,
                link_suffix_arrow,
                link_suffix_color_token,
            )
            live.append((
                ref,
                style_name,
                original_label,
                color_token,
                link_suffix_arrow,
                link_suffix_color_token,
            ))
    _text_registry[:] = live


# ---------------------------------------------------------------------------
# Text creation
# ---------------------------------------------------------------------------

def _resolve_text_style(text: str, style_name: str):
    """Resolve TextStyle and apply formatting.

    Shared by create_text() (widget context) and prepare_styled_text() (paint context).
    Note: create_text() callsites should use TextStyles alias keys.
    Paint-time helpers may pass direct theme paths for component-specific drawing.

    Returns:
        (formatted_text, style) tuple.
    """
    style = getattr(TextStyles, style_name)
    return style.format_text(text), style


def _resolve_text_foreground(
    style_name: str,
    color_token: Optional[str] = None,
    *,
    hovered: bool = False,
    pressed: bool = False,
    enabled: bool = True,
):
    """Resolve text color using state-aware theme tokens."""
    token = color_token or TextStyles._ALIASES.get(style_name, style_name)
    return _theme.color(token, hovered=hovered, pressed=pressed, enabled=enabled)


def _find_registered_text(widget: wx.StaticText):
    """Return registry metadata for a styled text widget, if available."""
    for entry in _text_registry:
        if entry[0]() == widget:
            return entry
    return None


def _apply_link_suffix_label(
    text_widget: wx.StaticText,
    formatted_text: str,
    link_suffix_arrow: bool,
    link_suffix_color_token: Optional[str],
    *,
    hovered: bool = False,
    pressed: bool = False,
    enabled: bool = True,
) -> None:
    """Apply text label and optional colored external-link arrow suffix."""
    if not link_suffix_arrow:
        text_widget.SetLabel(formatted_text)
        return

    suffix = "\u2197"
    if not link_suffix_color_token:
        text_widget.SetLabel(f"{formatted_text} {suffix}")
        return

    suffix_color = _theme.color(
        link_suffix_color_token,
        hovered=hovered,
        pressed=pressed,
        enabled=enabled,
    )
    color_hex = suffix_color.GetAsString(wx.C2S_HTML_SYNTAX)
    markup = (
        f"{html.escape(formatted_text)} "
        f"<span foreground=\"{color_hex}\">{suffix}</span>"
    )
    if not text_widget.SetLabelMarkup(markup):
        text_widget.SetLabel(f"{formatted_text} {suffix}")


def load_svg(svg_path: Path) -> Optional[object]:
    """Load an SVG file. Returns wx.svg.SVGimage or None on failure/missing."""
    if not svg_path.exists():
        return None
    try:
        return wx.svg.SVGimage.CreateFromFile(str(svg_path))
    except Exception as e:
        _logger.error("Failed to load SVG %s: %s", svg_path, e, exc_info=True)
        return None


def load_svg_markup(svg_markup: str) -> Optional[object]:
    """Load an SVG image from in-memory XML markup.

    wxPython documentation confirms SVG images can be created from an in-memory
    buffer, but the exact factory name differs across bindings. Probe the
    available APIs at runtime and return None if none are supported.
    """
    svg_bytes = svg_markup.encode("utf-8")
    candidates = (
        ("CreateFromBytes", lambda: wx.svg.SVGimage.CreateFromBytes(svg_bytes)),
        ("CreateFromBuffer", lambda: wx.svg.SVGimage.CreateFromBuffer(svg_bytes)),
        ("CreateFromData", lambda: wx.svg.SVGimage.CreateFromData(svg_bytes)),
    )

    for name, factory in candidates:
        if hasattr(wx.svg.SVGimage, name):
            try:
                return factory()
            except Exception as e:  # pragma: no cover
                _logger.debug("SVG markup loader %s failed: %s", name, e, exc_info=True)

    try:
        return wx.svg.SVGimage(svg_bytes)  # type: ignore[call-arg]
    except Exception as e:
        _logger.warning("Failed to load SVG markup from memory: %s", e, exc_info=True)
        return None


def replace_svg_fill(svg_markup: str, fill_color: str) -> str:
    """Replace non-`none` SVG fill attributes with the provided color.

    This keeps container-level `fill="none"` declarations intact while forcing
    visible paths to use a theme color.
    """
    return re.sub(
        r'fill="(?!none\b)[^"]+"',
        f'fill="{fill_color}"',
        svg_markup,
        flags=re.IGNORECASE,
    )


def create_text(parent: wx.Window, label: str, style_name: str,
                color_token: Optional[str] = None,
                link_suffix_arrow: bool = False,
                link_suffix_color_token: Optional[str] = "colors.primary",
                **kwargs) -> wx.StaticText:
    """Create a themed, formatted wx.StaticText and register it for hot-reload.

    Args:
        parent:      Parent wx.Window.
        label:       Raw (un-formatted) label string. Formatting (e.g. uppercase)
                     is applied automatically from the style definition.
        style_name:  TextStyles alias key (e.g. "header", "leftpanel_description", "dialog_link").
                 Alias keys should be defined in TextStyles._ALIASES and map
                 to layout.* or components.* YAML paths.
        color_token: Optional theme token to override the style's default color
                     (e.g. "colors.primary" or an axis-specific token).
        link_suffix_arrow: Append an external-link arrow suffix (\u2197).
        link_suffix_color_token: Theme token used for the suffix arrow color.
        **kwargs:    Additional wx.StaticText constructor args.

    Returns:
        wx.StaticText with font, color, and formatting applied.
    """
    formatted, style = _resolve_text_style(label, style_name)
    txt = wx.StaticText(parent, label=formatted, **kwargs)
    txt.SetFont(style.create_font())
    color = _resolve_text_foreground(style_name, color_token)
    txt.SetForegroundColour(color)
    _apply_link_suffix_label(
        txt,
        formatted,
        link_suffix_arrow,
        link_suffix_color_token,
    )

    # Pass through mouse clicks to parent (essential for labels inside
    # clickable containers like PresetCard, CustomButton)
    txt.Bind(wx.EVT_LEFT_DOWN, lambda e: e.Skip())

    _text_registry.append((
        weakref.ref(txt),
        style_name,
        label,
        color_token,
        link_suffix_arrow,
        link_suffix_color_token,
    ))
    return txt


def prepare_styled_text(gc, text: str, style_name: str, color=None):
    """Paint-context companion to create_text().

    Resolves font and formatting from TextStyles, sets the gc font,
    and returns layout metrics.  The caller positions and draws.

    Args:
        gc:          wx.GraphicsContext from an OnPaint handler.
        text:        Raw (un-formatted) label string.
        style_name:  TextStyles alias key (preferred), or a direct theme path
                 for component paint-time styles (e.g. "components.badge.label").
        color:       wx.Colour for the text. Usually state-dependent
                     (hover/pressed/enabled), so the caller computes it.

    Returns:
        (formatted_text, tw, th) — formatted string and its pixel extent.
    """
    formatted, style = _resolve_text_style(text, style_name)
    draw_color = color or style.color
    gc.SetFont(gc.CreateFont(style.create_font(), draw_color))
    tw, th = gc.GetTextExtent(formatted)
    return formatted, tw, th


def draw_styled_text(gc, text: str, style_name: str, x: float, y: float, color=None):
    """Draw text in a paint context using the same style pipeline as create_text().

    This helper centralizes prepare+draw to keep gc.DrawText usage consistent.
    """
    formatted, tw, th = prepare_styled_text(gc, text, style_name, color)
    gc.DrawText(formatted, x, y)
    return formatted, tw, th


def update_text(widget: wx.StaticText, label: str) -> None:
    """Update a registered text widget's label, respecting its style's formatting.
    
    This should be used instead of SetLabel() for widgets created via create_text()
    to ensure transformations like 'uppercase' are preserved during dynamic updates.
    """
    found = False
    for i, (
        ref,
        style_name,
        old_label,
        color_token,
        link_suffix_arrow,
        link_suffix_color_token,
    ) in enumerate(_text_registry):
        if ref() == widget:
            style = getattr(TextStyles, style_name)
            formatted = style.format_text(label)
            _apply_link_suffix_label(
                widget,
                formatted,
                link_suffix_arrow,
                link_suffix_color_token,
            )
            # Update the original label in the registry so hot-reload works with the new content
            _text_registry[i] = (
                ref,
                style_name,
                label,
                color_token,
                link_suffix_arrow,
                link_suffix_color_token,
            )
            found = True
            break
            
    if not found:
        # Fallback if widget not in registry (though it should be if created via create_text)
        widget.SetLabel(label)


def set_text_widget_state(
    widget: wx.StaticText,
    style_name: Optional[str] = None,
    label: Optional[str] = None,
    *,
    color_token: Optional[str] = None,
    hovered: bool = False,
    pressed: bool = False,
    enabled: bool = True,
    link_suffix_arrow: Optional[bool] = None,
    link_suffix_color_token: Optional[str] = None,
) -> None:
    """Apply a state-aware text color to a styled text widget."""
    registered = _find_registered_text(widget)
    if registered:
        _, reg_style_name, reg_label, reg_color_token, reg_link_suffix_arrow, reg_suffix_color_token = registered
        style_name = style_name or reg_style_name
        label = reg_label if label is None else label
        color_token = color_token or reg_color_token
        if link_suffix_arrow is None:
            link_suffix_arrow = reg_link_suffix_arrow
        if link_suffix_color_token is None:
            link_suffix_color_token = reg_suffix_color_token

    if style_name is None:
        raise ValueError("style_name is required for unregistered text widgets")

    if label is None:
        label = widget.GetLabel()

    formatted, _ = _resolve_text_style(label, style_name)
    widget.SetForegroundColour(
        _resolve_text_foreground(
            style_name,
            color_token,
            hovered=hovered,
            pressed=pressed,
            enabled=enabled,
        )
    )
    _apply_link_suffix_label(
        widget,
        formatted,
        bool(link_suffix_arrow),
        link_suffix_color_token,
        hovered=hovered,
        pressed=pressed,
        enabled=enabled,
    )
    if hasattr(widget, "Refresh"):
        widget.Refresh()


def bind_hover_text_group(
    bindings: list[dict],
    *,
    click_handler=None,
    click_event=wx.EVT_LEFT_DOWN,
) -> None:
    """Bind a shared hover state across one or more clickable text widgets."""

    def _pointer_inside_group() -> bool:
        get_mouse_position = getattr(wx, "GetMousePosition", None)
        if get_mouse_position is None:
            return False
        mouse_pos = get_mouse_position()
        for binding in bindings:
            widget = binding["widget"]
            rect_getter = getattr(widget, "GetScreenRect", None)
            if rect_getter is None:
                continue
            rect = rect_getter()
            if rect and hasattr(rect, "Contains") and rect.Contains(mouse_pos):
                return True
        return False

    def _apply_state(hovered: bool) -> None:
        for binding in bindings:
            widget = binding["widget"]
            style_name = binding.get("style_name")
            color_token = binding.get("color_token")
            if style_name is None and color_token is None and _find_registered_text(widget) is None:
                continue
            set_text_widget_state(
                widget,
                style_name,
                binding.get("label"),
                color_token=color_token,
                hovered=hovered,
                link_suffix_arrow=binding.get("link_suffix_arrow"),
                link_suffix_color_token=binding.get("link_suffix_color_token"),
            )

    def _on_enter(event):
        _apply_state(True)
        event.Skip()

    def _on_leave(event):
        if _pointer_inside_group():
            event.Skip()
            return
        _apply_state(False)
        event.Skip()

    for binding in bindings:
        widget = binding["widget"]
        widget.Bind(wx.EVT_ENTER_WINDOW, _on_enter)
        widget.Bind(wx.EVT_LEAVE_WINDOW, _on_leave)
        if click_handler:
            widget.Bind(click_event, click_handler)
            if hasattr(widget, "SetCursor"):
                widget.SetCursor(wx.Cursor(wx.CURSOR_HAND))


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
