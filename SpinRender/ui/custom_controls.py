"""
Custom UI Controls for SpinRender
Implements designs from SpinRender.pen exactly
"""
import wx
import wx.lib.scrolledpanel as scrolled
import wx.svg
import math
import re
from pathlib import Path
from SpinRender.core.theme import Theme
from SpinRender.core.locale import Locale
from .text_styles import TextStyle, TextStyles
from .helpers import bind_mouse_events

_theme = Theme.current()
_locale = Locale.current()


# Tracking state
_LOAD_ATTEMPTED = False


def ensure_fonts_loaded():
    """Load bundled fonts (JetBrains Mono, MDI, Oswald). Required for UI."""
    global _LOAD_ATTEMPTED
    if _LOAD_ATTEMPTED:
        return

    _LOAD_ATTEMPTED = True

    if wx.Platform == '__WXMAC__':
        return

    if not hasattr(wx.Font, "AddPrivateFont"):
        return

    # Load from resources folder
    fonts_dir = Path(__file__).resolve().parent.parent / "resources" / "fonts"
    font_files = {
        _theme.font_family("mono"): ["JetBrainsMono-VariableFont_wght.ttf"],
        _theme.font_family("icon"): ["MaterialDesignIconsDesktop.ttf"],
        _theme.font_family("display"): ["Oswald-VariableFont_wght.ttf"]
    }

    for family, files in font_files.items():
        for filename in files:
            font_path = fonts_dir / filename
            if font_path.exists():
                try:
                    wx.Font.AddPrivateFont(str(font_path))
                except Exception:
                    pass


def _get_paint_color(color, enabled=True):
    """Helper to apply alpha if component is disabled."""
    return _theme.disabled(color) if not enabled else color


class CustomSlider(wx.Panel):
    """
    Custom slider matching Component/Slider from Pencil design
    """
    def __init__(self, parent, value=50, min_val=0, max_val=100, size=(240, 18), id=wx.ID_ANY):
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = None
            real_id = id

        super().__init__(parent, id=real_id, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.dragging = False
        self._hovered = False

        # Standard mouse bindings for hover/click interactions
        bind_mouse_events(
            self,
            hover_handler=self._on_hover,
            leave_handler=self._on_leave,
            click_handler=self.on_mouse_down
        )

        # Custom paint and other events bound directly
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def _on_hover(self, event):
        """Mouse entered slider control."""
        if self.IsEnabled():
            self._hovered = True
            self.Refresh(); self.Update()

    def _on_leave(self, event):
        """Mouse left slider control."""
        self._hovered = False
        self.Refresh(); self.Update()

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        # V2 Mappings
        token = f"components.slider.{self.style_id}" if self.style_id else "components.slider.default"
        if not _theme.has_token(token): token = "components.slider.default"

        track_h = _theme._resolve(f"{token}.track.frame.height") or 4
        track_y = (height - track_h) / 2
        
        thumb_w = _theme._resolve(f"{token}.nub.width") or 7
        thumb_h = _theme._resolve(f"{token}.nub.height") or 18
        thumb_y = (height - thumb_h) / 2

        # Fetch colors dynamically from component section
        track_color = _theme.color(f"{token}.track.color", self._hovered, False, enabled)
        fill_color = _theme.color(f"{token}.nub.color", self._hovered, False, enabled)
        thumb_color = fill_color
        
        gc.SetBrush(wx.Brush(track_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, track_y, width, track_h, 2)

        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_width = ratio * width

        if fill_width > 0:
            gc.SetBrush(wx.Brush(fill_color))
            gc.DrawRoundedRectangle(0, track_y, fill_width, track_h, 2)

        thumb_x = fill_width - thumb_w / 2
        thumb_x = max(0, min(thumb_x, width - thumb_w))

        gc.SetBrush(wx.Brush(thumb_color))
        gc.DrawRoundedRectangle(thumb_x, thumb_y, thumb_w, thumb_h, 2)

    def on_mouse_down(self, event):
        if not self.IsEnabled(): return
        self.dragging = True
        self.update_value_from_mouse(event.GetX())
        self.CaptureMouse()
        self.Update()

    def on_mouse_up(self, event):
        if self.dragging:
            self.dragging = False
            if self.HasCapture(): self.ReleaseMouse()
            self.Update()

    def on_mouse_move(self, event):
        if self.dragging:
            self.update_value_from_mouse(event.GetX())

    def update_value_from_mouse(self, x):
        width = self.GetSize()[0]
        ratio = max(0, min(1, x / width))
        new_value = self.min_val + ratio * (self.max_val - self.min_val)
        if new_value != self.value:
            self.value = new_value
            self.Refresh()
            event = wx.PyCommandEvent(wx.EVT_SLIDER.typeId, self.GetId())
            event.SetInt(int(self.value))
            self.GetEventHandler().ProcessEvent(event)

    def GetValue(self): return self.value
    def SetValue(self, value):
        self.value = max(self.min_val, min(self.max_val, value))
        self.Refresh()

    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class CustomToggleButton(wx.Panel):
    """
    Multi-state toggle matching Component/Toggle from Pencil
    Supports 2 or more states.
    """
    def __init__(self, parent, options=None, size=(120, 32), id=wx.ID_ANY):
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = None
            real_id = id

        super().__init__(parent, id=real_id, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.options = options or [{'label': 'OFF', 'icon': None}, {'label': 'ON', 'icon': None}]
        self.selection = 0
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, click_handler=self.on_click)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        num_options = len(self.options)
        state_width = width / num_options
        enabled = self.IsEnabled()

        # Fetch colors dynamically from component section (V2)
        token = f"components.toggle.{self.style_id}" if self.style_id else "components.toggle.default"
        if not _theme.has_token(token): token = "components.toggle.default"

        bg_color = _theme.color(f"{token}.frame.bg", False, False, enabled)
        border_color = _theme.color(f"{token}.frame.border.color", False, False, enabled)
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.Pen(border_color, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 6)

        # Draw Active Indicator
        active_token = f"{token}.selected.frame.bg"
        active_bg = _theme.color(active_token, False, False, enabled) if _theme.has_token(active_token) else _theme.color("colors.primary", False, False, enabled)
        
        gc.SetBrush(wx.Brush(active_bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        active_x = self.selection * state_width
        gc.DrawRoundedRectangle(active_x + 1, 1, state_width - 2, height - 2, 6)

        # Draw each state
        for i, opt in enumerate(self.options):
            is_active = (i == self.selection)
            
            # Resolve text color from theme
            if is_active:
                text_token = f"{token}.selected.label.color"
                if not _theme.has_token(text_token): text_token = "colors.gray-black"
            else:
                text_token = f"{token}.default.label.color"
                if not _theme.has_token(text_token): text_token = "colors.gray-text"
                
            color = _theme.color(text_token, False, False, enabled)
            self._draw_side(gc, opt.get('label'), opt.get('icon'), i * state_width, state_width, height, color)

    def _draw_side(self, gc, label, icon_name, x_offset, width, height, color):
        # Resolve icon from glyphs
        icon_char = ""
        if icon_name and str(icon_name).lower() != "none":
            stripped = str(icon_name).replace('mdi-', '')
            icon_char = _theme.glyph(stripped) or str(icon_name)

        tw, th = 0, 0
        if label:
            font_obj = _theme.font("label")
            gc.SetFont(gc.CreateFont(font_obj, color))
            tw, th = gc.GetTextExtent(label)
            
        iw, ih = 0, 0
        icon_gfx_font = None
        if icon_char:
            icon_font_obj = _theme.font("icon")
            icon_gfx_font = gc.CreateFont(icon_font_obj, color)
            gc.SetFont(icon_gfx_font)
            iw, ih = gc.GetTextExtent(icon_char)
            
        gap = 6 if (icon_char and label) else 0
        total_w = iw + gap + tw
        start_x = x_offset + (width - total_w) / 2
        
        if icon_char:
            gc.SetFont(icon_gfx_font)
            gc.DrawText(icon_char, start_x, (height - ih) / 2)
            
        if label:
            font_obj = _theme.font("label")
            gc.SetFont(gc.CreateFont(font_obj, color))
            gc.DrawText(label, start_x + iw + gap, (height - th) / 2)

    def on_click(self, event):
        if not self.IsEnabled(): return
        width, num_options = self.GetSize().x, len(self.options)
        state_width = width / num_options
        new_selection = max(0, min(int(event.GetX() // state_width), num_options - 1))
        
        if self.selection != new_selection:
            self.selection = new_selection
            self.Refresh(); self.Update()
            evt = wx.PyCommandEvent(wx.EVT_TOGGLEBUTTON.typeId, self.GetId())
            evt.SetInt(self.selection)
            self.GetEventHandler().ProcessEvent(evt)

    def GetSelection(self): return self.selection
    def SetSelection(self, index):
        if 0 <= index < len(self.options):
            self.selection = index
            self.Refresh(); self.Update()

    def GetStringSelection(self): return self.options[self.selection].get('label')
    def GetValue(self): return self.selection == (len(self.options) - 1)
    def SetValue(self, value):
        self.selection = 1 if value else 0
        self.Refresh(); self.Update()

    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class DropdownPopup(wx.PopupTransientWindow):
    """
    Transient popup window for the dropdown list
    """
    def __init__(self, parent, choices, current_selection, callback, style_id="default"):
        super().__init__(parent, wx.BORDER_NONE)
        self.choices, self.selection, self.callback, self.hover_index = choices, current_selection, callback, -1
        self.style_id = style_id
        self.item_height = 32
        
        # V2 Mapping
        token = f"components.dropdown.{style_id}" if style_id else "components.dropdown.default"
        if not _theme.has_token(token): token = "components.dropdown.default"
        
        menu_bg = _theme.color(f"{token}.menu.frame.bg")
        self.SetBackgroundColour(menu_bg)
        
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        
        # V2 Mappings
        token = f"components.dropdown.{self.style_id}" if self.style_id else "components.dropdown.default"
        if not _theme.has_token(token): token = "components.dropdown.default"

        bg_color = _theme.color(f"{token}.menu.frame.bg")
        border_color = _theme.color(f"{token}.menu.frame.border.color") if _theme.has_token(f"{token}.menu.frame.border.color") else _theme.color("borders.subtle.color")
        
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.Pen(border_color, 1))
        gc.DrawRoundedRectangle(0, 0, width, height, 4)

        for i, choice in enumerate(self.choices):
            rect = wx.Rect(4, 4 + (i * self.item_height), width - 8, self.item_height)
            is_selected = (i == self.selection)
            is_hovered = (i == self.hover_index)
            
            if is_selected:
                accent_color = _theme.color(f"{token}.menu.selected.bg") if _theme.has_token(f"{token}.menu.selected.bg") else _theme.color("colors.primary")
                gc.SetBrush(wx.Brush(accent_color))
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, 2)
                
                text_color = _theme.color(f"{token}.menu.selected.label.color") if _theme.has_token(f"{token}.menu.selected.label.color") else _theme.color("colors.gray-black")
                gc.SetFont(gc.CreateFont(_theme.font("body"), text_color))
            elif is_hovered:
                gc.SetBrush(wx.Brush(_theme.color("colors.gray-medium")))
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, 2)
                gc.SetFont(gc.CreateFont(_theme.font("body"), _theme.color("text.body.color")))
            else:
                gc.SetFont(gc.CreateFont(_theme.font("body"), _theme.color("text.body.color")))
                
            tw, th = gc.GetTextExtent(choice)
            gc.DrawText(choice, rect.x + 8, rect.y + (rect.height - th) / 2)

    def on_mouse_move(self, event):
        idx = (event.GetY() - 4) // self.item_height
        if 0 <= idx < len(self.choices):
            if self.hover_index != idx: self.hover_index = idx; self.Refresh(); self.Update()
        elif self.hover_index != -1: self.hover_index = -1; self.Refresh(); self.Update()

    def on_click(self, event):
        idx = (event.GetY() - 4) // self.item_height
        if 0 <= idx < len(self.choices): self.callback(idx); self.Dismiss()

    def on_leave(self, event): self.hover_index = -1; self.Refresh(); self.Update()


class CustomDropdown(wx.Panel):
    """
    Custom dropdown matching Component/Dropdown from Pencil
    """
    def __init__(self, parent, choices=None, size=(160, 32), id=wx.ID_ANY):
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = None
            real_id = id

        super().__init__(parent, id=real_id, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.choices, self.selection, self.hovered, self.is_open = choices or [], 0, False, False
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, hover_handler=self.on_enter, leave_handler=self.on_leave, click_handler=self.on_click)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        # V2 Mappings
        token = f"components.dropdown.{self.style_id}" if self.style_id else "components.dropdown.default"
        if not _theme.has_token(token): token = "components.dropdown.default"

        base_bg_color = _theme.color(f"{token}.frame.bg", False, False, enabled)
        gc.SetBrush(wx.Brush(base_bg_color))

        # Border
        bc = _theme.color(f"{token}.open.border.color") if (self.hovered or self.is_open) else _theme.color(f"{token}.frame.border.color")
        gc.SetPen(wx.Pen(bc, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        # Label
        label = self.choices[self.selection] if self.choices else "SELECT OPTION"
        text_color = _theme.color("text.body.color", False, False, enabled)
        gc.SetFont(gc.CreateFont(_theme.font("body"), text_color))
        tw, th = gc.GetTextExtent(label)
        gc.DrawText(label, 12, (height - th) / 2)

        # Chevron
        icon_char = _theme.glyph("chevron-up" if self.is_open else "chevron-down")
        icon_token = f"{token}.open.icon.color" if self.is_open else f"{token}.icon.color"
        if not _theme.has_token(icon_token):
            icon_color = _theme.color("colors.primary") if self.is_open else _theme.color("colors.gray-text")
        else:
            icon_color = _theme.color(icon_token, False, False, enabled)
            
        icon_gfx_font = gc.CreateFont(_theme.font("icon"), icon_color)
        gc.SetFont(icon_gfx_font)
        iw, ih = gc.GetTextExtent(icon_char)
        gc.DrawText(icon_char, width - iw - 12, (height - ih) / 2)

    def on_click(self, event):
        if self.IsEnabled(): self.show_popup()
    def on_enter(self, event): self.hovered = True; self.Refresh(); self.Update()
    def on_leave(self, event): self.hovered = False; self.Refresh(); self.Update()

    def show_popup(self):
        if not self.choices: return
        popup = DropdownPopup(self, self.choices, self.selection, self.on_select, style_id=self.style_id or "default")
        width, height = self.GetSize()
        popup_height = (len(self.choices) * 32) + 8
        popup.SetSize((width, popup_height))
        pos = self.ClientToScreen(wx.Point(0, height))
        display_rect = wx.Display().GetClientArea()
        if pos.y + popup_height > display_rect.height: pos.y -= (height + popup_height)
        popup.Position(pos, wx.Size(0, 0))
        self.is_open = True; self.Refresh(); self.Update()
        popup.Popup()
        self.is_open = False; self.Refresh(); self.Update()

    def on_select(self, index):
        if self.selection != index:
            self.selection = index; self.Refresh(); self.Update()
            evt = wx.PyCommandEvent(wx.EVT_CHOICE.typeId, self.GetId())
            evt.SetInt(index); evt.SetString(self.choices[index])
            self.GetEventHandler().ProcessEvent(evt)

    def GetSelection(self): return self.selection
    def SetSelection(self, index):
        if 0 <= index < len(self.choices): self.selection = index; self.Refresh(); self.Update()
    def GetStringSelection(self): return self.choices[self.selection] if self.choices else ""
    def SetChoices(self, choices): self.choices, self.selection = choices, 0; self.Refresh(); self.Update()
    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class CustomButton(wx.Panel):
    """
    Custom action button matching Component/ActionButton and SecondaryButton
    """
    def __init__(self, parent, label=None, icon=None, icon_font_family=None, primary=True, ghost=False, danger=False, icon_color=None, icon_color_hover=None, icon_color_pressed=None, bg_color=None, bg_color_hover=None, bg_color_pressed=None, size=(-1, 36), id=wx.ID_ANY):
        # Extract style_id if passed as string (e.g. id="render")
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = None
            real_id = id

        super().__init__(parent, id=real_id, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        # Auto-derive from style_id if provided
        if self.style_id:
            if label is None:
                label = _locale.get(f"component.button.{self.style_id}.label", self.style_id.upper())
            if icon is None:
                icon_ref = _locale.get(f"component.button.{self.style_id}.icon_ref")
                if icon_ref:
                    # Store icon_ref; on_paint resolves it to glyph via theme
                    icon = icon_ref

        # Fallbacks for manual usage
        if label is None: label = "BUTTON"

        self.label, self.icon, self.icon_font_family, self.primary, self.ghost, self.danger = str(label), icon, icon_font_family, primary, ghost, danger
        self.icon_color_override, self.icon_color_hover, self.icon_color_pressed = icon_color, icon_color_hover, icon_color_pressed
        self.bg_color_override, self.bg_color_hover, self.bg_color_pressed = bg_color, bg_color_hover, bg_color_pressed
        self.border_color_override, self.border_color_hover, self.border_color_pressed = None, None, None
        self.hovered, self.pressed = False, False
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        bind_mouse_events(self, hover_handler=self.on_enter, leave_handler=self.on_leave, click_handler=self.on_mouse_down)

    def on_size(self, event): self.Refresh(); event.Skip()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        # V2 Mapping Logic
        if hasattr(self, 'style_id') and self.style_id:
            token = f"components.button.{self.style_id}"
            if not _theme.has_token(token):
                token = "components.button.default"
        else:
            if self.primary:
                token = "components.button.exit" if self.danger else "components.button.ok"
            elif self.ghost:
                token = "components.button.close"
            else:
                token = "components.button.cancel"

        # Resolve stateful colors from hierarchical token
        bg = _theme.color(f"{token}.frame.bg", self.hovered, self.pressed, enabled)
        
        # Label colors
        label_token = f"{token}.label.color"
        if not _theme.has_token(label_token):
            label_token = "text.button.color"
        text_color = _theme.color(label_token, self.hovered, self.pressed, enabled)
        
        # Border defaults
        border_token = f"{token}.frame.border.color"
        border_color = _theme.color(border_token, self.hovered, self.pressed, enabled) if _theme.has_token(border_token) else None

        # Overrides (if any)
        if self.bg_color_override:
            if not enabled: bg = _theme.disabled(self.bg_color_override)
            elif self.pressed and self.bg_color_pressed: bg = self.bg_color_pressed
            elif self.hovered and self.bg_color_hover: bg = self.bg_color_hover
            else: bg = self.bg_color_override

        if self.border_color_override:
            if not enabled: border_color = _theme.disabled(self.border_color_override)
            elif self.pressed and self.border_color_pressed: border_color = self.border_color_pressed
            elif self.hovered and self.border_color_hover: border_color = self.hovered
            else: border_color = self.border_color_override

        final_bg = bg
        final_text = text_color
        final_border = border_color

        final_icon_color = final_text
        if self.icon_color_override:
            if not enabled: final_icon_color = _theme.disabled(self.icon_color_override)
            elif self.pressed and self.icon_color_pressed: final_icon_color = self.icon_color_pressed
            elif self.hovered and self.icon_color_hover: final_icon_color = self.icon_color_hover
            else: final_icon_color = self.icon_color_override

        if not self.ghost or (self.hovered or self.pressed):
            gc.SetBrush(wx.Brush(final_bg))
            if final_border: gc.SetPen(wx.Pen(final_border, 1))
            else: gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 6)

        # Resolve icon from theme glyphs (V2 logic)
        icon_char = ""
        if self.icon and str(self.icon).lower() != "none":
            stripped = str(self.icon).replace('mdi-', '')
            icon_char = _theme.glyph(stripped) or str(self.icon)

        tw, th = 0, 0
        if self.label and len(self.label) > 0:
            font_obj = _theme.font("button")
            gfx_font = gc.CreateFont(font_obj, final_text)
            gc.SetFont(gfx_font)
            tw, th = gc.GetTextExtent(self.label)

        iw, ih = 0, 0
        icon_gfx_font = None
        if icon_char:
            icon_font_obj = _theme.font("icon")
            icon_gfx_font = gc.CreateFont(icon_font_obj, final_icon_color)
            gc.SetFont(icon_gfx_font)
            iw, ih = gc.GetTextExtent(icon_char)

        gap = 10 if (icon_char and self.label and len(self.label) > 0) else 0
        total_w = iw + gap + tw
        start_x = (width - total_w) / 2

        if icon_char:
            gc.SetFont(icon_gfx_font)
            gc.DrawText(icon_char, start_x, (height - ih) / 2)

        if self.label and len(self.label) > 0:
            gc.SetFont(gc.CreateFont(_theme.font("button"), final_text))
            gc.DrawText(self.label, start_x + iw + gap, (height - th) / 2)

    def on_mouse_down(self, event):
        if self.IsEnabled(): self.pressed = True; self.Refresh(); self.Update()
    def on_mouse_up(self, event):
        if self.pressed:
            self.pressed = False; self.Refresh(); self.Update()
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)
    def on_enter(self, event):
        if self.IsEnabled(): self.hovered = True; self.Refresh(); self.Update()
    def on_leave(self, event): self.hovered = False; self.pressed = False; self.Refresh(); self.Update()
    def SetLabel(self, label): self.label = str(label); self.Refresh(); self.Update()
    def SetIcon(self, icon): self.icon = icon; self.Refresh(); self.Update()
    def SetStyle(self, style_id, update_content=True):
        """Update style_id and optionally refresh label/icon from locale."""
        self.style_id = style_id
        if update_content and style_id:
            label = _locale.get(f"component.button.{style_id}.label")
            if label is not None:
                self.label = str(label)
            icon_ref = _locale.get(f"component.button.{style_id}.icon_ref")
            if icon_ref:
                self.icon = icon_ref
        self.Refresh(); self.Update()
    def SetPrimary(self, primary): self.primary = primary; self.Refresh(); self.Update()
    def SetDanger(self, danger): self.danger = danger; self.Refresh(); self.Update()
    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class PresetCard(wx.Panel):
    """
    Preset card matching Component/PresetCard
    """
    def __init__(self, parent, label=None, icon_name=None, size=(90, 64), id=wx.ID_ANY):
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = None
            real_id = id
            
        super().__init__(parent, id=real_id, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        if self.style_id:
            if label is None:
                label = _locale.get(f"component.preset_card.{self.style_id}.label", self.style_id.upper())
            if icon_name is None:
                icon_name = _locale.get(f"component.preset_card.{self.style_id}.icon_ref")
                
        if label is None: label = "PRESET"
        
        self.label, self.icon_name, self.selected = label, icon_name, False
        self.hovered = False
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, hover_handler=self.on_enter, leave_handler=self.on_leave, click_handler=self.on_click)

    def on_enter(self, event): self.hovered = True; self.Refresh(); self.Update()
    def on_leave(self, event): self.hovered = False; self.Refresh(); self.Update()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()
        
        # V2 Mapping
        token = f"components.preset_card.{self.style_id}" if self.style_id else "components.preset_card.default"
        if not _theme.has_token(token):
            token = "components.preset_card.default"
            
        bg = _theme.color(f"{token}.frame.bg", self.hovered, self.selected, enabled)
        border = _theme.color(f"{token}.frame.border.color", self.hovered, self.selected, enabled) if _theme.has_token(f"{token}.frame.border.color") else None
        
        label_token = f"{token}.label.color"
        if not _theme.has_token(label_token): label_token = "text.label.color"
        txt_color = _theme.color(label_token, self.hovered, self.selected, enabled)

        gc.SetBrush(wx.Brush(bg))
        if border: gc.SetPen(wx.Pen(border, 1))
        else: gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 8)

        # Resolve icon
        icon_char = ""
        if self.icon_name and str(self.icon_name).lower() != "none":
            stripped = str(self.icon_name).replace('mdi-', '')
            icon_char = _theme.glyph(stripped) or str(self.icon_name)
        
        icon_token = f"{token}.icon.color"
        if not _theme.has_token(icon_token): icon_token = txt_color # fallback to text color
        icon_color = _theme.color(icon_token, self.hovered, self.selected, enabled) if isinstance(icon_token, str) else icon_token

        icon_gfx_font = gc.CreateFont(_theme.font("icon_lg"), icon_color)
        gc.SetFont(icon_gfx_font)
        iw, ih = gc.GetTextExtent(icon_char)
        
        label_gfx_font = gc.CreateFont(_theme.font("label"), txt_color)
        gc.SetFont(label_gfx_font)
        tw, th = gc.GetTextExtent(self.label)

        gap, total_h = 8, ih + 8 + th
        start_y = (height - total_h) / 2

        gc.SetFont(icon_gfx_font)
        gc.DrawText(icon_char, (width - iw) / 2, start_y)
        gc.SetFont(label_gfx_font)
        gc.DrawText(self.label, (width - tw) / 2, start_y + ih + gap)

    def on_click(self, event):
        if self.IsEnabled():
            self.selected = True; self.Refresh(); self.Update()
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)

    def SetSelected(self, selected): self.selected = selected; self.Refresh(); self.Update()
    def SetLabel(self, label): self.label = str(label).upper(); self.Refresh(); self.Update()
    def IsSelected(self): return self.selected
    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class SectionLabel(wx.Panel):
    """
    Section label matching Component/SectionLabel
    """
    def __init__(self, parent, label="SECTION", size=(-1, 20), id="default"):
        super().__init__(parent, size=size)
        self.style_id = id
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.label = label
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        
        # V2 Mapping
        text_color = _theme.color("components.main.leftpanel.headers.color")
        line_color = _theme.color("components.main.divider.bg")
        line_size = _theme.size("components.main.divider.size") or 1
        
        gfx_font = gc.CreateFont(_theme.font("header"), text_color)
        gc.SetFont(gfx_font)
        tw, th = gc.GetTextExtent(self.label)
        gc.DrawText(self.label, 0, (height - th) / 2)


class CustomInput(wx.Panel):
    """
    Consolidated HUD-style input control for text, numeric, and rich path displays.
    Drives behavior and aesthetics from YAML components.input.{id}.
    """
    def __init__(self, parent, value="", placeholder="", size=(-1, 32), id=wx.ID_ANY, **kwargs):
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = "default"
            real_id = id

        # Enforce minimum width if size is default (-1, 32)
        actual_size = list(size)
        if actual_size[0] == -1: actual_size[0] = 100
        
        super().__init__(parent, id=real_id, size=tuple(actual_size))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetCanFocus(True)

        # Resolve DNA from theme
        self.token = f"components.input.{self.style_id}"
        if not _theme.has_token(self.token): self.token = "components.input.default"
        
        self.type = _theme._resolve(f"{self.token}.type") or "text"
        self.case = _theme._resolve(f"{self.token}.case") or "none"
        self.multiline = kwargs.get('multiline', False)
        self.unit = kwargs.get('unit') or _theme._resolve(f"{self.token}.unit") or ""
        
        self.prefix = kwargs.get('prefix') or _theme._resolve(f"{self.token}.prefix")
        if not isinstance(self.prefix, str) or self.prefix == "#FF00FF": self.prefix = ""
        
        step_val = kwargs.get('step') or _theme._resolve(f"{self.token}.step")
        try: self.step = float(step_val)
        except: self.step = 0.1
        
        self.min_val = kwargs.get('min_val')
        self.max_val = kwargs.get('max_val')
        
        # Initial editable state from theme or kwarg
        theme_editable = _theme._resolve(f"{self.token}.editable")
        self.Enable(kwargs.get('editable', True if theme_editable is None else theme_editable))
        
        # Rich state
        self.icon_ref = _theme._resolve(f"{self.token}.icon")
        self.show_chip = False # Toggled via method
        
        # Interaction state
        self.value = str(value)
        self.placeholder = str(placeholder)
        self.editing = False
        self.text_selected = False
        self.hovered = False
        
        # Layout components
        self.chip = None
        if self.type == "rich":
            self.chip = ProjectFolderChip(self)
            self.chip.Hide()

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_focus_lost)
        self.Bind(wx.EVT_SET_FOCUS, self.on_focus_gained)
        bind_mouse_events(self, hover_handler=self.on_enter, leave_handler=self.on_leave, click_handler=self.on_click)

    def on_size(self, event):
        if self.chip:
            h = self.GetSize().y
            self.chip.Move(wx.Point(36, (h - 18) / 2))
        self.Refresh(); event.Skip()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        w, h = self.GetSize()
        enabled = self.IsEnabled()
        focused = self.HasFocus() or self.editing

        # 1. Draw Frame
        bg = _theme.color(f"{self.token}.frame.bg", self.hovered, False, enabled)
        bc = _theme.color("borders.focus.color") if focused else _theme.color(f"{self.token}.frame.border.color")
        
        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(wx.Pen(bc, 1))
        gc.DrawRoundedRectangle(1, 1, w - 2, h - 2, 6)

        # 2. Resolve Text to draw
        display_text = self.value
        is_placeholder = not self.value and self.placeholder
        
        if is_placeholder and not focused:
            display_text = self.placeholder
            tc = _theme.color("colors.gray-text", False, False, enabled)
        else:
            tc_token = f"{self.token}.color.active" if focused else f"{self.token}.color.default"
            tc = _theme.color(tc_token, False, False, enabled)

        # 3. Draw Icon (Rich type)
        text_x = 12
        if self.type == "rich" and self.icon_ref:
            icon_char = _theme.glyph(self.icon_ref)
            gc.SetFont(gc.CreateFont(_theme.font("icon"), tc))
            itw, ith = gc.GetTextExtent(icon_char)
            gc.DrawText(icon_char, 12, (h - ith) / 2)
            text_x = 36
            if self.show_chip and self.chip:
                text_x += self.chip.GetSize().x + 6

        # 4. Draw Content
        gc.SetFont(gc.CreateFont(_theme.font("body"), tc))
        
        # Add cursor if editing
        if focused and not is_placeholder:
            # Simple cursor simulation
            if not self.text_selected: display_text += "|"

        if self.multiline:
            gc.DrawText(display_text, text_x, 10)
        else:
            # Handle Prefix/Suffix/Units
            full_display = f"{self.prefix}{display_text}"
            tw, th = gc.GetTextExtent(full_display)
            
            # Numeric right-align logic (V1 style)
            if self.type == "numeric":
                utw, uth = gc.GetTextExtent(self.unit)
                start_x = w - tw - 8 - (utw + 4 if self.unit else 0)
                gc.DrawText(full_display, start_x, (h - th) / 2)
                if self.unit:
                    uc = _theme.color("colors.gray-text", False, False, enabled)
                    gc.SetFont(gc.CreateFont(_theme.font("body"), uc))
                    gc.DrawText(self.unit, start_x + tw + 4, (h - th) / 2)
            else:
                # Path truncation
                if text_x + tw > w - 12:
                    full_display = "..." + full_display[-25:]
                gc.DrawText(full_display, text_x, (h - th) / 2)

    def on_click(self, event):
        if self.IsEnabled(): self.SetFocus(); self.Refresh(); self.Update()
    def on_enter(self, event): self.hovered = True; self.Refresh(); self.Update()
    def on_leave(self, event): self.hovered = False; self.Refresh(); self.Update()

    def on_focus_gained(self, event):
        if self.IsEnabled():
            self.editing = True
            self.text_selected = True
            self.Refresh(); self.Update()
        event.Skip()

    def on_focus_lost(self, event):
        self.editing = False
        self.text_selected = False
        self.confirm_value()
        self.Refresh(); self.Update()
        event.Skip()

    def on_char(self, event):
        if not self.IsEnabled(): return
        key = event.GetKeyCode()
        
        # Handle Enter/Escape/Tab
        if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            if self.multiline: self.value += "\n"; self.Refresh(); self.Update()
            else: self.confirm_value()
            return
        elif key == wx.WXK_ESCAPE:
            self.editing = False; self.Refresh(); self.Update(); return
        elif key == wx.WXK_TAB:
            self.confirm_value(); event.Skip(); return
            
        # Handle Arrows (Numeric stepping)
        if key in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_NUMPAD_UP, wx.WXK_NUMPAD_DOWN):
            if self.type == "numeric":
                delta = self.step * (10.0 if event.ShiftDown() else 1.0)
                try: val = float(self.value)
                except: val = 0.0
                new_val = (val + delta) if key in (wx.WXK_UP, wx.WXK_NUMPAD_UP) else (val - delta)
                if self.min_val is not None: new_val = max(self.min_val, new_val)
                if self.max_val is not None: new_val = min(self.max_val, new_val)
                self.SetValue(round(new_val, 2))
                self._fire_event(wx.EVT_TEXT_ENTER)
            return

        # Handle Backspace
        if key == wx.WXK_BACK:
            if self.text_selected: self.value = ""
            elif len(self.value) > 0: self.value = self.value[:-1]
            self.text_selected = False
            self.Refresh(); self.Update()
            self._fire_event(wx.EVT_TEXT)
            return

        # Input filtering
        char = chr(key) if key < 256 else None
        if char and char.isprintable():
            if self.type == "numeric" and not (char.isdigit() or char in '.-'): return
            
            if self.text_selected: self.value = ""
            
            val = char
            if self.case == "upper": val = val.upper()
            elif self.case == "lower": val = val.lower()
            
            self.value += val
            self.text_selected = False
            self.Refresh(); self.Update()
            self._fire_event(wx.EVT_TEXT)

    def confirm_value(self):
        self.editing = False
        if self.type == "numeric":
            try:
                v = float(self.value)
                if self.min_val is not None: v = max(self.min_val, v)
                if self.max_val is not None: v = min(self.max_val, v)
                self.value = f"{v:.2f}"
            except: pass
        self._fire_event(wx.EVT_TEXT_ENTER)

    def _fire_event(self, evt_type):
        evt = wx.PyCommandEvent(evt_type.typeId, self.GetId())
        evt.SetString(self.value)
        self.GetEventHandler().ProcessEvent(evt)

    def GetValue(self): return self.value.strip()
    def SetValue(self, val):
        if self.type == "numeric":
            try: self.value = f"{float(val):.2f}"
            except: self.value = str(val)
        else:
            self.value = str(val)
            if self.case == "upper": self.value = self.value.upper()
        self.Refresh(); self.Update()

    def SetEditable(self, editable):
        """Toggle editable state. Read-only state is derived from IsEnabled()."""
        self.Enable(editable)
        self.Refresh(); self.Update()

    def SetPath(self, path, in_project=False):
        self.value = path
        self.show_chip = in_project
        if self.chip:
            if self.show_chip: self.chip.Show()
            else: self.chip.Hide()
        self.Refresh(); self.Update()

    def AcceptsFocus(self): return self.IsEnabled()
    def AcceptsFocusFromKeyboard(self): return self.IsEnabled()


class CustomListItem(wx.Panel):
    """
    A single interactive item in a CustomListView.
    Drives styling from components.list.{id}.item.
    """
    def __init__(self, parent, label="", icon=None, data=None, id="default"):
        super().__init__(parent)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.label = str(label)
        self.icon_ref = icon
        self.data = data
        self.style_id = id
        self.hovered = False
        self.confirm_mode = False
        
        # Resolve DNA
        self.token = f"components.list.{self.style_id}"
        if not _theme.has_token(self.token): self.token = "components.list.default"
        
        self.height = _theme._resolve(f"{self.token}.frame.height") or 40
        self.SetMinSize((-1, self.height))
        
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, hover_handler=self.on_enter, leave_handler=self.on_leave, click_handler=self.on_click)

    def on_enter(self, event): self.hovered = True; self.Refresh(); self.Update()
    def on_leave(self, event): self.hovered = False; self.Refresh(); self.Update()
    
    def on_click(self, event):
        # Determine if click was on action area or main body
        w, h = self.GetSize()
        x = event.GetX()
        
        action_width = 80 # Approx width of action area
        if x > w - action_width:
            self.handle_action_click(x - (w - action_width))
        else:
            self._fire_event(wx.EVT_LIST_ITEM_SELECTED)

    def handle_action_click(self, local_x):
        if self.confirm_mode:
            if local_x < 40: # Cancel
                self.confirm_mode = False
            else: # Confirm
                self._fire_event(wx.EVT_LIST_ITEM_DELETED)
        else:
            self.confirm_mode = True
        self.Refresh(); self.Update()

    def _fire_event(self, evt_type):
        evt = wx.PyCommandEvent(evt_type.typeId, self.GetId())
        evt.SetClientData(self.data)
        self.GetEventHandler().ProcessEvent(evt)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        w, h = self.GetSize()
        enabled = self.IsEnabled()
        
        # 1. Background
        bg = _theme.color(f"{self.token}.frame.bg", self.hovered, False, enabled)
        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)

        # 2. Icon & Label
        tc = _theme.color(f"{self.token}.label.color", self.hovered, False, enabled)
        gc.SetFont(gc.CreateFont(_theme.font("body"), tc))
        
        text_x = 12
        if self.icon_ref:
            icon_char = _theme.glyph(self.icon_ref)
            gc.SetFont(gc.CreateFont(_theme.font("icon"), tc))
            itw, ith = gc.GetTextExtent(icon_char)
            gc.DrawText(icon_char, 12, (h - ith) / 2)
            text_x = 36
            gc.SetFont(gc.CreateFont(_theme.font("body"), tc))

        gc.DrawText(self.label, text_x, (h - gc.GetTextExtent(self.label)[1]) / 2)

        # 3. Actions
        if self.hovered or self.confirm_mode:
            self.draw_actions(gc, w, h)

    def draw_actions(self, gc, w, h):
        # Action data from theme
        actions_token = f"{self.token}.actions"
        if not _theme.has_token(actions_token): return
        
        if self.confirm_mode:
            # Draw Cancel and Confirm
            c_icon = _theme.glyph(_theme._resolve(f"{actions_token}.cancel.icon"))
            c_color = _theme.color(f"{actions_token}.cancel.color")
            s_icon = _theme.glyph(_theme._resolve(f"{actions_token}.confirm.icon"))
            s_color = _theme.color(f"{actions_token}.confirm.color")
            
            gc.SetFont(gc.CreateFont(_theme.font("icon"), c_color))
            gc.DrawText(c_icon, w - 70, (h - 16) / 2)
            
            gc.SetFont(gc.CreateFont(_theme.font("icon"), s_color))
            gc.DrawText(s_icon, w - 30, (h - 16) / 2)
        else:
            # Draw Delete
            d_icon = _theme.glyph(_theme._resolve(f"{actions_token}.delete.icon"))
            d_color = _theme.color(f"{actions_token}.delete.color")
            gc.SetFont(gc.CreateFont(_theme.font("icon"), d_color))
            gc.DrawText(d_icon, w - 30, (h - 16) / 2)


class CustomListView(scrolled.ScrolledPanel):
    """
    HUD-style list container that manages CustomListItem instances.
    """
    def __init__(self, parent, size=(-1, -1), id="default"):
        super().__init__(parent, size=size)
        self.style_id = id
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetupScrolling(scroll_x=False, scroll_y=True)
        
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.main_sizer)
        
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        # Just clear background with theme color
        bg = _theme.color("colors.gray-dark")
        dc.SetBackground(wx.Brush(bg))
        dc.Clear()

    def AddItem(self, label, icon=None, data=None):
        item = CustomListItem(self, label=label, icon=icon, data=data, id=self.style_id)
        self.main_sizer.Add(item, 0, wx.EXPAND | wx.BOTTOM, 4)
        self.Layout()
        self.SetupScrolling(scroll_x=False, scroll_y=True)
        return item

    def ClearItems(self):
        self.main_sizer.Clear(True)
        self.Layout()


# Define custom event types for list interaction
wx.EVT_LIST_ITEM_SELECTED = wx.PyEventBinder(wx.NewEventType(), 1)
wx.EVT_LIST_ITEM_DELETED = wx.PyEventBinder(wx.NewEventType(), 1)


class ProjectFolderChip(wx.Panel):
    """
    Small orange chip for "PROJECT FOLDER" prefix
    """
    def __init__(self, parent):
        font = _theme.font("metadata")
        temp_dc = wx.ScreenDC(); temp_dc.SetFont(font)
        tw, th = temp_dc.GetTextExtent("PROJECT FOLDER")
        super().__init__(parent, size=(tw + 12, 18))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT); self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = self.GetSize()
        gc.SetBrush(wx.Brush(_theme.color("components.badge.frame.bg")))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, w, h, 4)
        gc.SetFont(gc.CreateFont(_theme.font("metadata"), _theme.color("components.badge.label.color")))
        tw, th = gc.GetTextExtent("PROJECT FOLDER")
        gc.DrawText("PROJECT FOLDER", (w - tw) / 2, (h - th) / 2)

    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class CustomColorPicker(wx.Panel):
    """
    Custom color picker matching Component/ColorPicker from Pencil design.
    """
    PRESETS = [("#000000", "BLACK"), ("#1A1F23", "SLATE"), ("#F5F0E8", "CREAM"), ("#FFFFFF", "WHITE")]

    def __init__(self, parent, current_color="#000000"):
        super().__init__(parent)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.current_color, self.hover_idx, self.selection, self.editing = current_color.upper(), -1, -1, False
        self._update_selection()
        
        # Use consolidated CustomInput
        self.hex_input = CustomInput(self, value=self.current_color, placeholder="#000000", size=(-1, 28), id="hex")
        self.hex_input.Bind(wx.EVT_TEXT_ENTER, self.on_hex_enter); self.hex_input.Bind(wx.EVT_KILL_FOCUS, self.on_hex_focus_lost)
        
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, hover_handler=self.on_mouse_move, click_handler=self.on_click, leave_handler=self.on_leave)
        self.SetMinSize((340, 64)); self._layout_input(); self.Bind(wx.EVT_SIZE, self._on_size)

    def _on_size(self, event): self._layout_input(); event.Skip()
    def _update_selection(self):
        self.selection = -1
        for i, (h, _) in enumerate(self.PRESETS):
            if h.upper() == self.current_color: self.selection = i; break

    def SetColor(self, hex_color):
        self.current_color = hex_color.upper(); self._update_selection()
        if hasattr(self, 'hex_input'): self.hex_input.SetValue(self.current_color)
        self.Refresh(); self.Update()

    def _layout_input(self):
        if not hasattr(self, 'hex_input'): return
        r = self._get_rects()['hex']
        self.hex_input.SetSize(r.width, r.height); self.hex_input.SetPosition((r.x, r.y))

    def on_hex_enter(self, event): self._apply_hex_color()
    def on_hex_focus_lost(self, event): self._apply_hex_color(); event.Skip()

    def _apply_hex_color(self):
        h = self.hex_input.GetValue().strip()
        if not h.startswith('#'): h = f"#{h}"
        if len(h) == 7 and all(c in '0123456789ABCDEFabcdef' for c in h[1:]):
            h = h.upper()
            if h != self.current_color:
                self.current_color = h; self._update_selection(); self.Refresh(); self.Update()
                evt = wx.PyCommandEvent(wx.EVT_COLOURPICKER_CHANGED.typeId, self.GetId()); evt.SetString(h); self.GetEventHandler().ProcessEvent(evt)
        else: self.hex_input.SetValue(self.current_color)

    def _get_rects(self):
        w, h = self.GetSize()
        rects, x = {}, 12
        for i in range(len(self.PRESETS)): rects[f'preset_{i}'] = wx.Rect(x, 10, 28, 28); x += 38
        rects['divider'], x = x, x + 10
        rects['custom'], x = wx.Rect(x, 10, 28, 28), x + 42
        # Top-align to match swatches (y=10)
        rects['hex'] = wx.Rect(x, 10, 100, 28)
        return rects

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self); gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = self.GetSize(); enabled, rects = self.IsEnabled(), self._get_rects()
        
        # V2 Mappings
        bg = _theme.color("components.colorpicker.default.bg")
        gc.SetBrush(wx.Brush(_theme.disabled(bg) if not enabled else bg))
        gc.SetPen(wx.TRANSPARENT_PEN); gc.DrawRoundedRectangle(0, 0, w, h, 4)
        for i, (hv, lbl) in enumerate(self.PRESETS):
            r = rects[f'preset_{i}']; self._draw_swatch(gc, r.x, r.y, hv, lbl, i == self.selection, i == self.hover_idx, enabled)
        
        border = _theme.color("borders.subtle.color")
        gc.SetPen(wx.Pen(_theme.disabled(border) if not enabled else border, 1))
        dx = rects['divider']; gc.StrokeLine(dx, 10, dx, h - 10)
        rc = rects['custom']; self._draw_swatch(gc, rc.x, rc.y, self.current_color, "CUSTOM", self.selection == -1, self.hover_idx == 4, enabled)
        
        # Hex input frame is handled by CustomInput itself

    def _draw_swatch(self, gc, x, y, ch, lbl, sel, hov, enabled):
        sc = wx.Colour(ch); gc.SetBrush(wx.Brush(_theme.disabled(sc) if not enabled else sc))
        
        # Swatch border role
        stc = _theme.color("borders.subtle.color")
        if sel: stc, thk = _theme.color("colors.primary"), 2
        elif hov: stc, thk = _theme.color("colors.gray-medium"), 1
        else: thk = 1
        
        gc.SetPen(wx.Pen(_theme.disabled(stc) if not enabled else stc, thk))
        gc.DrawRoundedRectangle(x, y, 28, 28, 4)
        
        text_muted = _theme.color("colors.gray-text")
        gfx_font = gc.CreateFont(_theme.font("metadata"), _theme.disabled(text_muted) if not enabled else text_muted)
        gc.SetFont(gfx_font); tw, th = gc.GetTextExtent(lbl); gc.DrawText(lbl, x + (28 - tw) / 2, y + 32)

    def on_mouse_move(self, event):
        if not self.IsEnabled(): return
        p, r = event.GetPosition(), self._get_rects(); nh = -1
        for i in range(len(self.PRESETS)):
            if r[f'preset_{i}'].Contains(p): nh = i; break
        if nh == -1 and r['custom'].Contains(p): nh = 4
        if self.hover_idx != nh: self.hover_idx = nh; self.Refresh(); self.Update()

    def on_click(self, event):
        if not self.IsEnabled(): return
        p, r = event.GetPosition(), self._get_rects(); ci = -1
        for i in range(len(self.PRESETS)):
            if r[f'preset_{i}'].Contains(p): ci = i; break
        if ci == -1 and r['custom'].Contains(p): ci = 4
        if ci == -1: return
        if ci < 4:
            nc = self.PRESETS[ci][0]
            if nc != self.current_color:
                self.current_color, self.selection = nc, ci; self.Refresh(); self.Update()
                evt = wx.PyCommandEvent(wx.EVT_COLOURPICKER_CHANGED.typeId, self.GetId()); evt.SetString(nc); self.GetEventHandler().ProcessEvent(evt)
        else:
            data = wx.ColorData(); data.SetColor(wx.Colour(self.current_color)); dlg = wx.ColorDialog(self, data)
            if dlg.ShowModal() == wx.ID_OK:
                no = dlg.GetColorData().GetColor(); nh = "#%02X%02X%02X" % (no.Red(), no.Green(), no.Blue())
                self.current_color = nh; self._update_selection(); self.Refresh(); self.Update()
                evt = wx.PyCommandEvent(wx.EVT_COLOURPICKER_CHANGED.typeId, self.GetId()); evt.SetString(nh); self.GetEventHandler().ProcessEvent(evt)
            dlg.Destroy()

    def on_leave(self, event): self.hover_idx = -1; self.Refresh(); self.Update()


class SVGLogoPanel(wx.Panel):
    """Panel that renders the SpinRender SVG logo."""
    def __init__(self, parent, size=(58, 58)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        plugin_dir = Path(__file__).parent.parent
        svg_path = plugin_dir / "resources" / "logo.svg"
        if not svg_path.exists():
            svg_path = plugin_dir.parent / "res" / "logo.svg"
        self.svg_image = None
        if svg_path.exists():
            try:
                self.svg_image = wx.svg.SVGimage.CreateFromFile(str(svg_path))
            except Exception as e:
                import logging
                logger = logging.getLogger("SpinRender")
                logger.error(f"Failed to load SVG: {e}", exc_info=True)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return
        width, height = self.GetSize()
        gc.SetBrush(wx.TRANSPARENT_BRUSH)
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, width, height)
        if self.svg_image:
            try:
                self.svg_image.RenderToGC(gc, 1.0)
            except Exception:
                gc.SetBrush(wx.Brush(_theme.color("colors.primary")))
                gc.DrawRectangle(0, 0, width, height)
