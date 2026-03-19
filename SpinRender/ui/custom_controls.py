"""
Custom UI Controls for SpinRender
Implements designs from SpinRender.pen exactly
"""
import wx
import math
from pathlib import Path
from SpinRender.core.theme import Theme
from .text_styles import TextStyle, TextStyles
from .helpers import bind_mouse_events

_theme = Theme.current()


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
    def __init__(self, parent, value=50, min_val=0, max_val=100, size=(240, 18), color=None):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.dragging = False
        self.color_override = color

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

        # Component constants
        track_h = _theme.size("components.slider.track.height")
        track_y = (height - track_h) / 2
        thumb_w, thumb_h = 7, 18
        thumb_y = (height - thumb_h) / 2

        # Fetch colors dynamically from component section
        base_track_color = _theme.color("components.slider.track.color")
        base_fill_color = self.color_override or _theme.color("components.slider.fill.color")
        
        # Apply disabled state to colors
        track_color = _theme.disabled(base_track_color) if not enabled else base_track_color
        fill_color = _theme.disabled(base_fill_color) if not enabled else base_fill_color
        thumb_color = fill_color

        gc.SetBrush(wx.Brush(track_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, track_y, width, track_h, 4)

        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_width = ratio * width

        if fill_width > 0:
            gc.SetBrush(wx.Brush(fill_color))
            gc.DrawRoundedRectangle(0, track_y, fill_width, track_h, 4)

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
    ICONS = {
        'mdi-reload': '\U000F0453',
        'mdi-restore': '\U000F099B',
        'mdi-check-circle': '\U000F05E0',
        'mdi-close-circle': '\U000F05E8',
        'mdi-weather-sunny': '\U000F0599',
        'mdi-lightning-bolt': '\U000F140B',
        'mdi-image-filter-drama-outline': '\U000F1BFF',
        'mdi-circle-off-outline': '\U000F10D3',
        'mdi-star-settings-outline': '\U000F166B',
        'mdi-chevron-down': '\U000F0140',
        'mdi-chevron-up': '\U000F0143',
        'mdi-video': '\U000F0592',
        'mdi-file-gif-box': '\U000F0D7E',
        'mdi-image-multiple': '\U000F02F0',
        'mdi-television-hd': '\U000F0704',
        'mdi-television': '\U000F0502',
        'mdi-monitor': '\U000F0379',
        'mdi-trash-can-outline': '\U000F0A7A',
        'mdi-axis-x-arrow': '\U000F0D4C',
        'mdi-axis-y-arrow': '\U000F0D51',
        'mdi-alert-octagram': '\U000F0767',
        'mdi-application-edit': '\U000F00AE'
    }

    def __init__(self, parent, options=None, size=(120, 32), active_color=None):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.active_bg_override = active_color
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

        # Fetch colors dynamically from component section
        base_bg_color = _theme.color("components.toggle.bg")
        base_border_color = _theme.color("components.toggle.border")
        
        bg_color = _theme.disabled(base_bg_color) if not enabled else base_bg_color
        border_color = _theme.disabled(base_border_color) if not enabled else base_border_color
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.Pen(border_color, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        # Draw Active Indicator
        base_active_bg = self.active_bg_override or _theme.color("components.toggle.active.bg")
        active_color = _theme.disabled(base_active_bg) if not enabled else base_active_bg
        gc.SetBrush(wx.Brush(active_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        active_x = self.selection * state_width
        gc.DrawRoundedRectangle(active_x + 1, 1, state_width - 2, height - 2, 4)

        # Draw each state
        for i, opt in enumerate(self.options):
            is_active = (i == self.selection)
            token = "components.toggle.active.text" if is_active else "components.toggle.option.text"
            base_color = _theme.color(token)
            color = _theme.disabled(base_color) if not enabled else base_color
            self._draw_side(gc, opt.get('label'), opt.get('icon'), i * state_width, state_width, height, color)

    def _draw_side(self, gc, label, icon_name, x_offset, width, height, color):
        icon_char = self.ICONS.get(icon_name, icon_name) if icon_name else None
        tw, th = 0, 0
        if label:
            font_obj = TextStyles.body_strong.create_font()
            gc.SetFont(gc.CreateFont(font_obj, color))
            tw, th = gc.GetTextExtent(label)
            
        iw, ih = 0, 0
        icon_gfx_font = None
        if icon_char:
            icon_font_obj = TextStyles.icon.create_font()
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
            font_obj = TextStyles.body_strong.create_font()
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
    def __init__(self, parent, choices, current_selection, callback):
        super().__init__(parent, wx.BORDER_NONE)
        self.choices, self.selection, self.callback, self.hover_index = choices, current_selection, callback, -1
        self.item_height = 32
        self.SetBackgroundColour(_theme.color("components.dropdown.popup.bg"))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        bg_color = _theme.color("components.dropdown.popup.bg")
        border_color = _theme.color("components.dropdown.border")
        accent_color = _theme.color("colors.primary")
        text_primary = _theme.color("components.dropdown.text")

        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.Pen(border_color, 1))
        gc.DrawRoundedRectangle(0, 0, width, height, 4)

        for i, choice in enumerate(self.choices):
            rect = wx.Rect(4, 4 + (i * self.item_height), width - 8, self.item_height)
            is_selected = (i == self.selection)
            is_hovered = (i == self.hover_index)
            
            if is_selected:
                gc.SetBrush(wx.Brush(accent_color))
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, 2)
                gc.SetFont(gc.CreateFont(TextStyles.body_strong.create_font(), _theme.color("colors.bg.input")))
            elif is_hovered:
                gc.SetBrush(wx.Brush(_theme.color("components.dropdown.popup.hover")))
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, 2)
                gc.SetFont(gc.CreateFont(TextStyles.body.create_font(), text_primary))
            else:
                gc.SetFont(gc.CreateFont(TextStyles.body.create_font(), text_primary))
                
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
    def __init__(self, parent, choices=None, size=(160, 32)):
        super().__init__(parent, size=size)
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

        # Background
        base_bg_color = _theme.color("components.dropdown.bg")
        gc.SetBrush(wx.Brush(_theme.disabled(base_bg_color) if not enabled else base_bg_color))

        # Border
        bc = _theme.color("components.dropdown.border-focus") if (self.hovered or self.is_open) else _theme.color("components.dropdown.border")
        gc.SetPen(wx.Pen(_theme.disabled(bc) if not enabled else bc, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        # Label
        label = self.choices[self.selection] if self.choices else "SELECT OPTION"
        text_color = _theme.color("components.dropdown.text")
        gc.SetFont(gc.CreateFont(TextStyles.body_strong.create_font(), _theme.disabled(text_color) if not enabled else text_color))
        tw, th = gc.GetTextExtent(label)
        gc.DrawText(label, 12, (height - th) / 2)

        # Chevron
        icon_char = CustomToggleButton.ICONS.get('mdi-chevron-up' if self.is_open else 'mdi-chevron-down')
        icon_color = _theme.color("colors.primary") if self.is_open else _theme.color("colors.text.secondary")
        icon_gfx_font = gc.CreateFont(TextStyles.icon.create_font(), _theme.disabled(icon_color) if not enabled else icon_color)
        gc.SetFont(icon_gfx_font)
        iw, ih = gc.GetTextExtent(icon_char)
        gc.DrawText(icon_char, width - iw - 12, (height - ih) / 2)

    def on_click(self, event):
        if self.IsEnabled(): self.show_popup()
    def on_enter(self, event): self.hovered = True; self.Refresh(); self.Update()
    def on_leave(self, event): self.hovered = False; self.Refresh(); self.Update()

    def show_popup(self):
        if not self.choices: return
        popup = DropdownPopup(self, self.choices, self.selection, self.on_select)
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
    ICONS = {
        'play': '▶', 'eye': '👁', 'save': '💾', 'settings': '⚙', 'check': '✓', 'alert': '⚠', 'download': '⬇', 'folder': '📁', 'close': '✕',
        'mdi-download': '\U000F01DA', 'mdi-close': '\U000F0156', 'mdi-cog': '\U000F0493', 'mdi-play': '\U000F040D', 'mdi-stop': '\U000F04DB',
        'mdi-video-vintage': '\U000F0A1C', 'mdi-folder': '\U000F024B', 'mdi-check': '\U000F012C', 'mdi-alert': '\U000F0026',
        'mdi-information-outline': '\U000F02FD', 'mdi-trash-can-outline': '\U000F0A7A', 'mdi-alert-octagram': '\U000F0767',
        'mdi-exit-to-app': '\U000F0206', 'mdi-palette': '\U000F03E8'
    }

    def __init__(self, parent, label="BUTTON", icon=None, icon_font_family=None, primary=True, ghost=False, danger=False, icon_color=None, icon_color_hover=None, icon_color_pressed=None, bg_color=None, bg_color_hover=None, bg_color_pressed=None, size=(-1, 36)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
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

        # Determine base colors
        if self.primary:
            token = "components.button.danger" if self.danger else "components.button.primary"
        elif self.ghost:
            token = "components.button.ghost"
        else:
            token = "components.button.secondary"

        colors = _theme.color_states(f"{token}.bg")
        bg_base = colors[0]
        text_colors = _theme.color_states(f"{token}.text")
        text_base = text_colors[0]
        
        # Border defaults
        border_base = None
        if not self.primary and not self.ghost: border_base = _theme.color("components.button.secondary.border")

        bg, text_color, border_color = bg_base, text_base, border_base

        if self.bg_color_override:
            if self.pressed and self.bg_color_pressed: bg = self.bg_color_pressed
            elif self.hovered and self.bg_color_hover: bg = self.bg_color_hover
            else: bg = self.bg_color_override
        else:
            # Automatic state handling from token arrays
            states = _theme.color_states(f"{token}.bg")
            if self.pressed and len(states) > 2: bg = states[2]
            elif self.hovered and len(states) > 1: bg = states[1]
            
            tstates = _theme.color_states(f"{token}.text")
            if self.pressed and len(tstates) > 2: text_color = tstates[2]
            elif self.hovered and len(tstates) > 1: text_color = tstates[1]

        if self.border_color_override:
            if self.pressed and self.border_color_pressed: border_color = self.border_color_pressed
            elif self.hovered and self.border_color_hover: border_color = self.border_color_hover
            else: border_color = self.border_color_override

        final_bg = _theme.disabled(bg) if not enabled else bg
        final_text = _theme.disabled(text_color) if not enabled else text_color
        final_border = _theme.disabled(border_color) if (not enabled and border_color) else border_color

        final_icon_color = final_text
        if self.icon_color_override:
            if self.pressed and self.icon_color_pressed: final_icon_color = self.icon_color_pressed if enabled else _theme.disabled(self.icon_color_pressed)
            elif self.hovered and self.icon_color_hover: final_icon_color = self.icon_color_hover if enabled else _theme.disabled(self.icon_color_hover)
            else: final_icon_color = self.icon_color_override if enabled else _theme.disabled(self.icon_color_override)

        if not self.ghost or (self.hovered or self.pressed):
            gc.SetBrush(wx.Brush(final_bg))
            if final_border: gc.SetPen(wx.Pen(final_border, 1))
            else: gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        icon_char = self.ICONS.get(self.icon, self.icon) if self.icon else None
        tw, th = 0, 0
        if self.label and len(self.label) > 0:
            font_obj = TextStyles.body_strong.create_font()
            gfx_font = gc.CreateFont(font_obj, final_text)
            gc.SetFont(gfx_font)
            tw, th = gc.GetTextExtent(self.label)

        iw, ih = 0, 0
        icon_gfx_font = None
        if icon_char:
            icon_font_obj = TextStyles.icon.create_font()
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
            gc.SetFont(gc.CreateFont(TextStyles.body_strong.create_font(), final_text))
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
    def SetPrimary(self, primary): self.primary = primary; self.Refresh(); self.Update()
    def SetDanger(self, danger): self.danger = danger; self.Refresh(); self.Update()
    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class PresetCard(wx.Panel):
    """
    Preset card matching Component/PresetCard
    """
    ICONS = {
        'rotate-cw': '↻', 'rotate-ccw': '↺', 'arrow-down': '↓', 'arrow-up': '↑', 'circle': '○', 'star': '⭐',
        'mdi-rotate-cw': '\U000F0465', 'mdi-arrow-down': '\U000F0045', 'mdi-arrow-up': '\U000F005D', 'mdi-circle': '\U000F012F',
        'mdi-star-settings-outline': '\U000F166B', 'mdi-rotate-360': '\U000F1999', 'mdi-rotate-orbit': '\U000F0D98',
        'mdi-horizontal-rotate-counterclockwise': '\U000F10F4'
    }

    def __init__(self, parent, label="PRESET", icon_name="rotate-cw", size=(90, 64)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.label, self.icon_name, self.selected = label, icon_name, False
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, click_handler=self.on_click)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()
        state = 1 if self.selected else 0

        bg = _theme.color("components.preset_card.bg", state)
        border = _theme.color("components.preset_card.border", state)
        txt_color = _theme.color("components.preset_card.text", state)

        gc.SetBrush(wx.Brush(_theme.disabled(bg) if not enabled else bg))
        gc.SetPen(wx.Pen(_theme.disabled(border) if not enabled else border, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        icon_char = self.ICONS.get(self.icon_name, self.icon_name)
        final_text = _theme.disabled(txt_color) if not enabled else txt_color
        
        icon_gfx_font = gc.CreateFont(TextStyles.icon_lg.create_font(), final_text)
        gc.SetFont(icon_gfx_font)
        iw, ih = gc.GetTextExtent(icon_char)
        
        label_gfx_font = gc.CreateFont(TextStyles.label_sm.create_font(), final_text)
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
    def __init__(self, parent, label="SECTION", size=(-1, 20)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.label = label
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        text_color, line_color = _theme.color("components.section_label.text"), _theme.color("components.section_label.line")
        
        gfx_font = gc.CreateFont(TextStyles.section_heading.create_font(), text_color)
        gc.SetFont(gfx_font)
        tw, th = gc.GetTextExtent(self.label)
        gc.DrawText(self.label, 0, (height - th) / 2)

        line_x = tw + 8
        line_y = height / 2
        if width - line_x > 0:
            gc.SetPen(wx.Pen(line_color, 1))
            gc.StrokeLine(line_x, line_y, width, line_y)


class NumericDisplay(wx.Panel):
    """
    Numeric value display matching Component/NumericInput
    """
    def __init__(self, parent, value=0.0, unit="", size=(100, 32)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.value, self.unit = value, unit
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        bg = _theme.color("components.numeric_display.bg")
        border = _theme.color("components.numeric_display.border")
        accent = _theme.color("components.numeric_display.text-value")
        secondary = _theme.color("components.numeric_display.text-unit")

        gc.SetBrush(wx.Brush(_theme.disabled(bg) if not enabled else bg))
        gc.SetPen(wx.Pen(_theme.disabled(border) if not enabled else border, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        v_str = f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
        v_gfx_font = gc.CreateFont(TextStyles.numeric_value.create_font(), _theme.disabled(accent) if not enabled else accent)
        gc.SetFont(v_gfx_font)
        vw, vh = gc.GetTextExtent(v_str)

        u_gfx_font = gc.CreateFont(TextStyles.body.create_font(), _theme.disabled(secondary) if not enabled else secondary)
        gc.SetFont(u_gfx_font)
        uw, uh = gc.GetTextExtent(self.unit)

        total_w = vw + 4 + uw
        start_x = width - total_w - 8
        gc.SetFont(v_gfx_font); gc.DrawText(v_str, start_x, (height - vh) / 2)
        gc.SetFont(u_gfx_font); gc.DrawText(self.unit, start_x + vw + 4, (height - uh) / 2)

    def SetValue(self, value): self.value = value; self.Refresh(); self.Update()
    def GetValue(self): return self.value


class NumericInput(wx.Panel):
    """
    Editable numeric input matching Component/NumericInput
    """
    def __init__(self, parent, value=0.0, unit="", min_val=None, max_val=None, size=(100, 32)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.value, self.unit, self.min_val, self.max_val, self.editing, self.edit_text, self.original_value, self.text_selected = \
            value, unit, min_val, max_val, False, "", value, False
        self.SetWindowStyle(self.GetWindowStyle() | wx.TAB_TRAVERSAL)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, click_handler=self.on_click)
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_focus_lost)
        self.Bind(wx.EVT_SET_FOCUS, self.on_focus_gained)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        bg = _theme.color("components.numeric_input.bg")
        gc.SetBrush(wx.Brush(_theme.disabled(bg) if not enabled else bg))

        bc = _theme.color("components.numeric_input.border-focus") if self.editing else _theme.color("components.numeric_input.border")
        gc.SetPen(wx.Pen(_theme.disabled(bc) if not enabled else bc, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        if self.editing:
            v_str, v_color = self.edit_text, _theme.color("components.numeric_input.text")
        else:
            v_str, v_color = (f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)), _theme.color("colors.secondary")

        v_gfx_font = gc.CreateFont(TextStyles.numeric_value.create_font(), _theme.disabled(v_color) if not enabled else v_color)
        gc.SetFont(v_gfx_font)
        vw, vh = gc.GetTextExtent(v_str)

        unit_color = _theme.color("colors.text.secondary")
        u_gfx_font = gc.CreateFont(TextStyles.body.create_font(), _theme.disabled(unit_color) if not enabled else unit_color)
        gc.SetFont(u_gfx_font)
        uw, uh = gc.GetTextExtent(self.unit)

        total_w = vw + 4 + uw
        start_x = width - total_w - 8
        gc.SetFont(v_gfx_font); gc.DrawText(v_str, start_x, (height - vh) / 2)
        gc.SetFont(u_gfx_font); gc.DrawText(self.unit, start_x + vw + 4, (height - uh) / 2)

        if self.editing:
            cx = start_x + vw + 2
            cy1, edit_color = (height - vh) / 2, _theme.color("components.numeric_input.text")
            gc.SetPen(wx.Pen(_theme.disabled(edit_color) if not enabled else edit_color, 1))
            gc.StrokeLine(cx, cy1, cx, cy1 + vh)

    def on_click(self, event):
        if self.IsEnabled() and not self.editing:
            self.editing, self.original_value, self.text_selected = True, self.value, True
            self.edit_text = f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
            self.SetFocus(); self.Refresh(); self.Update()

    def on_focus_gained(self, event):
        if self.IsEnabled() and not self.editing:
            self.editing, self.original_value, self.text_selected = True, self.value, True
            self.edit_text = f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
            self.Refresh(); self.Update()
        event.Skip()

    def on_char(self, event):
        if not self.IsEnabled(): return
        key = event.GetKeyCode()
        if not self.editing:
            if key in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_NUMPAD_UP, wx.WXK_NUMPAD_DOWN): self._handle_arrow(key, event.ShiftDown())
            event.Skip(); return

        if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER): self.confirm_edit()
        elif key == wx.WXK_ESCAPE: self.cancel_edit()
        elif key == wx.WXK_TAB: self.confirm_edit(); event.Skip()
        elif key in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_NUMPAD_UP, wx.WXK_NUMPAD_DOWN): self._handle_arrow(key, event.ShiftDown())
        elif key == wx.WXK_BACK:
            if self.text_selected: self.edit_text, self.text_selected = "", False
            else: self.edit_text = self.edit_text[:-1]
            self.Refresh(); self.Update()
        else:
            char = chr(key) if key < 256 else None
            if char and (char.isdigit() or char in '.-'):
                if self.text_selected: self.edit_text, self.text_selected = char, False
                else: self.edit_text += char
                self.Refresh(); self.Update()

    def _handle_arrow(self, key, shift_pressed):
        step = 1.0 if shift_pressed else 0.1
        try: current = float(self.edit_text) if self.editing and self.edit_text else self.value
        except: current = self.value
        new_val = (current + step) if key in (wx.WXK_UP, wx.WXK_NUMPAD_UP) else (current - step)
        if self.min_val is not None: new_val = max(self.min_val, new_val)
        if self.max_val is not None: new_val = min(self.max_val, new_val)
        self.value = round(new_val, 1)
        if self.editing: self.edit_text, self.text_selected = (f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)), True
        self.Refresh(); self.Update()
        evt = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId, self.GetId()); evt.SetString(str(self.value))
        self.GetEventHandler().ProcessEvent(evt)

    def on_focus_lost(self, event):
        if self.editing: self.confirm_edit()
        event.Skip()

    def confirm_edit(self):
        try:
            val = float(self.edit_text)
            if self.min_val is not None: val = max(self.min_val, val)
            if self.max_val is not None: val = min(self.max_val, val)
            self.value, self.editing = val, False
            self.Refresh(); self.Update()
            evt = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId, self.GetId()); evt.SetString(str(val))
            self.GetEventHandler().ProcessEvent(evt)
        except: self.cancel_edit()

    def cancel_edit(self): self.value, self.editing = self.original_value, False; self.Refresh(); self.Update()
    def SetValue(self, value):
        self.value = value
        if not self.editing: self.Refresh(); self.Update()
    def GetValue(self): return self.value
    def AcceptsFocus(self): return self.IsEnabled()
    def AcceptsFocusFromKeyboard(self): return self.IsEnabled()


class CustomTextInput(wx.Panel):
    """
    Custom text input matching Component/NumericInput (aliased)
    """
    def __init__(self, parent, value="", placeholder="", multiline=False, size=(-1, 36)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.value, self.placeholder, self.multiline = str(value).upper(), str(placeholder), multiline
        self.is_placeholder_active = not self.value and self.placeholder
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, click_handler=self.on_click)
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_focus_lost); self.Bind(wx.EVT_SET_FOCUS, self.on_focus_gained)
        self.SetCanFocus(True)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        bg = _theme.color("components.text_input.bg")
        gc.SetBrush(wx.Brush(_theme.disabled(bg) if not enabled else bg))
        bc = _theme.color("components.text_input.border-focus") if self.HasFocus() else _theme.color("components.text_input.border")
        gc.SetPen(wx.Pen(_theme.disabled(bc) if not enabled else bc, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        if self.is_placeholder_active and not self.HasFocus():
            display_text, text_color = self.placeholder, _theme.color("components.text_input.placeholder")
        else:
            display_text, text_color = self.value, _theme.color("components.text_input.text")

        gfx_font = gc.CreateFont(TextStyles.body.create_font(), _theme.disabled(text_color) if not enabled else text_color)
        gc.SetFont(gfx_font)
        if self.HasFocus(): display_text += "|"
        if self.multiline: gc.DrawText(display_text, 12, 10)
        else:
            tw, th = gc.GetTextExtent(display_text)
            gc.DrawText(display_text, 12, (height - th) / 2)

    def on_click(self, event):
        if self.IsEnabled(): self.SetFocus(); self.Refresh(); self.Update()
    def on_char(self, event):
        if not self.IsEnabled(): return
        key = event.GetKeyCode()
        if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            if self.multiline: self.value += "\n"; self.Refresh(); self.Update()
            else: self.GetEventHandler().ProcessEvent(wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId, self.GetId()))
        elif key == wx.WXK_BACK:
            if len(self.value) > 0: self.value = self.value[:-1]; self.Refresh(); self.Update()
        elif key == wx.WXK_TAB: event.Skip()
        else:
            char = chr(key) if key < 256 else None
            if char and char.isprintable(): self.value += char.upper(); self.Refresh(); self.Update()
        self.is_placeholder_active = not self.value and self.placeholder
        evt = wx.PyCommandEvent(wx.EVT_TEXT.typeId, self.GetId()); evt.SetString(self.value)
        self.GetEventHandler().ProcessEvent(evt)

    def on_focus_gained(self, event): self.Refresh(); self.Update(); event.Skip()
    def on_focus_lost(self, event): self.Refresh(); self.Update(); event.Skip()
    def GetValue(self): return self.value.strip()
    def SetValue(self, val):
        self.value = str(val).upper(); self.is_placeholder_active = not self.value and self.placeholder; self.Refresh(); self.Update()
    def AcceptsFocus(self): return self.IsEnabled()
    def AcceptsFocusFromKeyboard(self): return self.IsEnabled()


class ProjectFolderChip(wx.Panel):
    """
    Small orange chip for "PROJECT FOLDER" prefix
    """
    def __init__(self, parent):
        font = TextStyles.label_xs.create_font()
        temp_dc = wx.ScreenDC(); temp_dc.SetFont(font)
        tw, th = temp_dc.GetTextExtent("PROJECT FOLDER")
        super().__init__(parent, size=(tw + 12, 18))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT); self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = self.GetSize()
        gc.SetBrush(wx.Brush(_theme.color("components.badge.bg")))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, w, h, 4)
        gc.SetFont(gc.CreateFont(TextStyles.label_xs.create_font(), _theme.color("components.badge.text")))
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
        self.hex_input = CustomTextInput(self, value=self.current_color, placeholder="#000000", size=(-1, 28))
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
        bg = _theme.color("components.color_picker.bg")
        gc.SetBrush(wx.Brush(_theme.disabled(bg) if not enabled else bg))
        gc.SetPen(wx.TRANSPARENT_PEN); gc.DrawRoundedRectangle(0, 0, w, h, 4)
        for i, (hv, lbl) in enumerate(self.PRESETS):
            r = rects[f'preset_{i}']; self._draw_swatch(gc, r.x, r.y, hv, lbl, i == self.selection, i == self.hover_idx, enabled)
        border = _theme.color("components.color_picker.border")
        gc.SetPen(wx.Pen(_theme.disabled(border) if not enabled else border, 1))
        dx = rects['divider']; gc.StrokeLine(dx, 10, dx, h - 10)
        rc = rects['custom']; self._draw_swatch(gc, rc.x, rc.y, self.current_color, "CUSTOM", self.selection == -1, self.hover_idx == 4, enabled)
        rh = rects['hex']; hbg = _theme.color("components.text_input.bg")
        gc.SetBrush(wx.Brush(_theme.disabled(hbg) if not enabled else hbg))
        gc.SetPen(wx.Pen(_theme.disabled(border) if not enabled else border, 1))
        gc.DrawRoundedRectangle(rh.x, rh.y, rh.width, rh.height, 4)

    def _draw_swatch(self, gc, x, y, ch, lbl, sel, hov, enabled):
        sc = wx.Colour(ch); gc.SetBrush(wx.Brush(_theme.disabled(sc) if not enabled else sc))
        stc = _theme.color("components.color_picker.swatch-border")
        if sel: stc, thk = _theme.color("colors.primary"), 2
        elif hov: stc, thk = _theme.HOVER_HIGHLIGHT, 1
        else: thk = 1
        gc.SetPen(wx.Pen(_theme.disabled(stc) if not enabled else stc, thk))
        gc.DrawRoundedRectangle(x, y, 28, 28, 4)
        gfx_font = gc.CreateFont(TextStyles.label_xs.create_font(), _theme.disabled(_theme.color("colors.text.muted")) if not enabled else _theme.color("colors.text.muted"))
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


class PathInputControl(wx.Panel):
    """
    Styled path display with folder icon and project chip support
    """
    def __init__(self, parent, size=(-1, 36)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT); self.path_text, self.show_chip = "", False
        self.chip = ProjectFolderChip(self); self.chip.Hide(); self.Bind(wx.EVT_PAINT, self.on_paint); self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event): self.update_chip_pos(); event.Skip()
    def update_chip_pos(self): self.chip.Move(wx.Point(36, (self.GetSize().y - 18) / 2))
    def SetPath(self, path, in_project=False):
        self.path_text, self.show_chip = path, in_project
        if self.show_chip: self.chip.Show()
        else: self.chip.Hide()
        self.Refresh(); self.Update()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self); gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = self.GetSize(); enabled = self.IsEnabled()
        bg = _theme.color("components.path_input.bg")
        gc.SetBrush(wx.Brush(_theme.disabled(bg) if not enabled else bg))
        brd = _theme.color("components.path_input.border")
        gc.SetPen(wx.Pen(_theme.disabled(brd) if not enabled else brd, 1))
        gc.DrawRoundedRectangle(1, 1, w - 2, h - 2, 4)
        tc = _theme.color("components.path_input.text"); ic = _theme.color("components.path_input.icon")
        gf_i = gc.CreateFont(TextStyles.icon.create_font(), _theme.disabled(ic) if not enabled else ic)
        gc.SetFont(gf_i); itw, ih = gc.GetTextExtent('\U000F024B'); gc.DrawText('\U000F024B', 12, (h - ih) / 2)
        gf_t = gc.CreateFont(TextStyles.body.create_font(), _theme.disabled(tc) if not enabled else tc)
        gc.SetFont(gf_t); tx = 36 + (self.chip.GetSize().x + 6 if self.show_chip else 0)
        tw, th = gc.GetTextExtent(self.path_text); dt = self.path_text
        if tx + tw > w - 12: dt = "..." + self.path_text[-25:]
        gc.DrawText(dt, tx, (h - th) / 2)

    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False
