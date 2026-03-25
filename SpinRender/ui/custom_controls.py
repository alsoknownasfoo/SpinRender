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
from .helpers import bind_mouse_events, create_text, prepare_styled_text, draw_styled_text
from .events import ParameterInteractionEvent

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


def disable_mac_focus_ring(window):
    """
    Suppresses the OS-level blue focus ring on macOS native controls.
    Targets both the NSView and its NSCell (if it exists) for maximum suppression.
    Requires pyobjc (pyobjc-core and pyobjc-framework-Cocoa).
    """
    if wx.Platform != '__WXMAC__':
        return
    
    handle = window.GetHandle()
    if not handle:
        return

    try:
        import objc
        # Convert the raw pointer handle to an objc object
        v = objc.objc_object(c_void_p=handle)
        
        # NSFocusRingTypeNone = 1
        # Set on view
        if hasattr(v, 'setFocusRingType_'):
            v.setFocusRingType_(1)
        
        # Set on cell if it's an NSControl (like NSTextField)
        if hasattr(v, 'cell'):
            try:
                c = v.cell()
                if c and hasattr(c, 'setFocusRingType_'):
                    c.setFocusRingType_(1)
            except Exception:
                pass
    except ImportError:
        logger.error("pyobjc (pyobjc-core, pyobjc-framework-Cocoa) is required for macOS focus ring suppression but is not installed.")
    except Exception as e:
        logger.debug(f"Failed to disable macOS focus ring: {e}")


class CustomSlider(wx.Panel):
    """
    Custom slider matching Component/Slider from Pencil design
    """
    def __init__(self, parent, value=50, min_val=0, max_val=100, size=(240, 18), id=wx.ID_ANY, section=None):
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

        _p = self.GetParent()
        while _p is not None:
            if hasattr(_p, '_registry'):
                _p._registry.add(self, section=section)
                break
            _p = _p.GetParent()

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

        # Theme token mappings
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
        wx.PostEvent(self, ParameterInteractionEvent(self.GetId()))
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
    def __init__(self, parent, options=None, size=(120, 32), id=wx.ID_ANY, section=None):
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = None
            real_id = id

        super().__init__(parent, id=real_id, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        if options is None:
            off_label = _locale.get("system.controls.toggle_off", "OFF")
            on_label = _locale.get("system.controls.toggle_on", "ON")
            options = [{'label': off_label, 'icon': None}, {'label': on_label, 'icon': None}]
        self.options = options
        self.selection = 0
        self.hover_index = -1

        _p = self.GetParent()
        while _p is not None:
            if hasattr(_p, '_registry'):
                _p._registry.add(self, section=section)
                break
            _p = _p.GetParent()

        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, click_handler=self.on_click, hover_handler=self.on_mouse_move, leave_handler=self.on_leave)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)

    def on_leave(self, event):
        self.hover_index = -1
        self.Refresh(); self.Update()

    def on_mouse_move(self, event):
        if not self.IsEnabled(): return
        w = self.GetSize().width
        num_options = len(self.options)
        new_hover = int(event.GetX() // (w / num_options))
        if new_hover != self.hover_index:
            self.hover_index = new_hover
            self.Refresh(); self.Update()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        num_options = len(self.options)
        state_width = width / num_options
        enabled = self.IsEnabled()

        # Fetch colors dynamically from component section
        token = f"components.toggle.{self.style_id}" if self.style_id else "components.toggle.default"
        if not _theme.has_token(token): token = "components.toggle.default"

        # 1. Main Frame
        is_any_hovered = self.hover_index != -1
        bg_color = _theme.color(f"{token}.frame.bg", is_any_hovered, False, enabled)
        border_color = _theme.color(f"{token}.frame.border.color", is_any_hovered, False, enabled)
        
        radius = _theme.size(f"{token}.frame.radius") or 6
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.Pen(border_color, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, radius)

        # 2. Draw each segment
        for i, opt in enumerate(self.options):
            is_active = (i == self.selection)
            is_hovered = (i == self.hover_index)
            
            x_offset = i * state_width
            
            # Resolve Segment Background
            # When disabled, resolve the intended visual-state colour first (enabled=True),
            # then desaturate — avoids the auto-generated disabled state being based on
            # the transparent default rather than the coloured active state.
            if not enabled:
                seg_bg = _theme.disabled(_theme.color(f"{token}.items.frame.bg", False, is_active, True))
            else:
                seg_bg = _theme.color(f"{token}.items.frame.bg", is_hovered, is_active, enabled)
            if seg_bg.Alpha() > 0:
                gc.SetBrush(wx.Brush(seg_bg))
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.DrawRoundedRectangle(x_offset + 1, 1, state_width - 2, height - 2, radius)

            # Resolve Content Colors
            label_token = f"{token}.items.label"
            icon_token = f"{token}.items.icon"

            if not enabled:
                l_color = _theme.disabled(_theme.color(f"{label_token}.color", False, is_active, True))
                i_color = _theme.disabled(_theme.color(f"{icon_token}.color", False, is_active, True))
            else:
                l_color = _theme.color(f"{label_token}.color", is_hovered, is_active, enabled)
                i_color = _theme.color(f"{icon_token}.color", is_hovered, is_active, enabled)
            
            self._draw_side(gc, opt.get('label'), opt.get('icon'), x_offset, state_width, height, l_color, i_color, label_token, icon_token)

    def _draw_side(self, gc, label, icon_name, x_offset, width, height, l_color, i_color, label_token, icon_token):
        # Resolve icon from glyphs
        icon_char = ""
        if icon_name and str(icon_name).lower() != "none":
            stripped = str(icon_name).replace('mdi-', '')
            icon_char = _theme.glyph(stripped) or str(icon_name)

        formatted, tw, th = None, 0, 0
        if label:
            formatted, tw, th = prepare_styled_text(gc, label, label_token, l_color)

        iw, ih = 0, 0
        if icon_char:
            _, iw, ih = prepare_styled_text(gc, icon_char, icon_token, i_color)

        gap = 6 if (icon_char and label) else 0
        total_w = iw + gap + tw
        start_x = x_offset + (width - total_w) / 2

        if icon_char:
            draw_styled_text(gc, icon_char, icon_token, start_x, (height - ih) / 2, i_color)

        if formatted:
            draw_styled_text(gc, label, label_token, start_x + iw + gap, (height - th) / 2, l_color)

    def on_click(self, event):
        if not self.IsEnabled(): return
        wx.PostEvent(self, ParameterInteractionEvent(self.GetId()))
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
        
        # Theme token mapping
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
        
        # Theme token mappings
        token = f"components.dropdown.{self.style_id}" if self.style_id else "components.dropdown.default"
        if not _theme.has_token(token): token = "components.dropdown.default"

        # 1. Menu Container
        bg_color = _theme.color(f"{token}.menu.frame.bg")
        border_color = _theme.color(f"{token}.menu.frame.border.color")
        radius = _theme.size(f"{token}.menu.frame.radius") or 4
        
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.Pen(border_color, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, radius)

        # 2. Menu Items
        item_radius = _theme.size(f"{token}.menu.items.radius") or 2
        for i, choice in enumerate(self.choices):
            rect = wx.Rect(4, 4 + (i * self.item_height), width - 8, self.item_height)
            is_selected = (i == self.selection)
            is_hovered = (i == self.hover_index)
            
            # Resolve Item Background
            item_bg = _theme.color(f"{token}.menu.items.bg", is_hovered, is_selected, True)
            if item_bg.Alpha() > 0:
                gc.SetBrush(wx.Brush(item_bg))
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.DrawRoundedRectangle(rect.x + 1, rect.y + 1, rect.width - 2, rect.height - 2, item_radius)
            
            # Resolve Item Border (usually for hover)
            item_bc = _theme.color(f"{token}.menu.items.border.color", is_hovered, is_selected, True)
            if item_bc.Alpha() > 0:
                gc.SetPen(wx.Pen(item_bc, 1))
                gc.SetBrush(wx.TRANSPARENT_BRUSH)
                gc.DrawRoundedRectangle(rect.x + 1, rect.y + 1, rect.width - 2, rect.height - 2, item_radius)
            
            # Resolve Item Label (Font & Color)
            label_token = f"{token}.menu.items.label"
            text_color = _theme.color(f"{label_token}.color", is_hovered, is_selected, True)

            _, _, th = prepare_styled_text(gc, choice, label_token, text_color)
            draw_styled_text(gc, choice, label_token, rect.x + 8, rect.y + (rect.height - th) / 2, text_color)

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
    def __init__(self, parent, choices=None, size=(160, 32), id=wx.ID_ANY, section=None):
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = None
            real_id = id

        super().__init__(parent, id=real_id, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.choices, self.selection, self.hovered, self.is_open = choices or [], 0, False, False
        self._default_label = _locale.get("components.dropdown.default.label", "SELECT OPTION")

        _p = self.GetParent()
        while _p is not None:
            if hasattr(_p, '_registry'):
                _p._registry.add(self, section=section)
                break
            _p = _p.GetParent()

        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, hover_handler=self.on_enter, leave_handler=self.on_leave, click_handler=self.on_click)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        # Theme token mappings
        token = f"components.dropdown.{self.style_id}" if self.style_id else "components.dropdown.default"
        if not _theme.has_token(token): token = "components.dropdown.default"

        base_bg_color = _theme.color(f"{token}.frame.bg", self.hovered or self.is_open, False, enabled)
        gc.SetBrush(wx.Brush(base_bg_color))

        # 1. Resolve Frame Border (Hover/Open state)
        bc_token = f"{token}.frame.border.color"
        # If open or hovered, the engine can handle stateful lookup if provided in YAML, 
        # or we pass the flags here.
        bc = _theme.color(bc_token, self.hovered or self.is_open, False, enabled)
        gc.SetPen(wx.Pen(bc, 1))
        
        radius = _theme.size(f"{token}.frame.radius") or 4
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, radius)

        # 2. Resolve Label (Font & Color)
        label = self.choices[self.selection] if self.choices else getattr(self, '_default_label', _locale.get("components.dropdown.default.label", "SELECT OPTION"))
        label_token = f"{token}.label"
        
        # Color resolution from label.color.default/hover
        text_color = _theme.color(f"{label_token}.color", self.hovered or self.is_open, False, enabled)

        _, _, th = prepare_styled_text(gc, label, label_token, text_color)
        draw_styled_text(gc, label, label_token, 12, (height - th) / 2, text_color)

        # 3. Resolve Chevron Icon
        icon_char = _theme.glyph("chevron-up" if self.is_open else "chevron-down")
        icon_color = _theme.color(f"{token}.icon.color", self.hovered or self.is_open, False, enabled)
            
        _, iw, ih = prepare_styled_text(gc, icon_char, f"{token}.icon", icon_color)
        draw_styled_text(gc, icon_char, f"{token}.icon", width - iw - 12, (height - ih) / 2, icon_color)

    def on_click(self, event):
        if self.IsEnabled():
            wx.PostEvent(self, ParameterInteractionEvent(self.GetId()))
            self.show_popup()
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
    def __init__(self, parent, label=None, icon=None, icon_font_family=None, size=(-1, 36), id=wx.ID_ANY, section=None):
        # Extract style_id if passed as string (e.g. id="render")
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = None
            real_id = id

        super().__init__(parent, id=real_id, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        # Auto-derive label/icon from style_id via locale
        if self.style_id:
            if label is None:
                label = _locale.get(f"component.button.{self.style_id}.label", self.style_id)
            if icon is None:
                icon_ref = _locale.get(f"component.button.{self.style_id}.icon_ref")
                if icon_ref:
                    icon = icon_ref

        if label is None:
            label = _locale.get("components.button.default.label", "BUTTON")

        self.label, self.icon, self.icon_font_family = str(label), icon, icon_font_family
        self.icon_rotation_degrees = 0
        self.hovered, self.pressed = False, False

        _p = self.GetParent()
        while _p is not None:
            if hasattr(_p, '_registry'):
                _p._registry.add(self, section=section)
                break
            _p = _p.GetParent()

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

        # Theme token mapping
        token = f"components.button.{self.style_id}" if self.style_id else "components.button.default"
        if not _theme.has_token(token):
            token = "components.button.default"

        # Resolve stateful colors from hierarchical token
        bg = _theme.color(f"{token}.frame.bg", self.hovered, self.pressed, enabled)

        # Label colors
        final_text = _theme.color(f"{token}.label.color", self.hovered, self.pressed, enabled)

        # Border
        border_token = f"{token}.frame.border.color"
        final_border = _theme.color(border_token, self.hovered, self.pressed, enabled) if _theme.has_token(border_token) else None

        final_icon_color = final_text

        gc.SetBrush(wx.Brush(bg))
        if final_border: gc.SetPen(wx.Pen(final_border, 1))
        else: gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 6)

        # Resolve icon from theme glyphs
        icon_char = ""
        if self.icon and str(self.icon).lower() != "none":
            stripped = str(self.icon).replace('mdi-', '')
            icon_char = _theme.glyph(stripped) or str(self.icon)

        text_lines = []
        text_line_sizes = []
        text_w, text_h = 0, 0
        line_gap = 0
        if self.label and len(self.label) > 0:
            font_obj = _theme.font("button")
            gfx_font = gc.CreateFont(font_obj, final_text)
            gc.SetFont(gfx_font)
            text_lines = str(self.label).split("\n")
            if len(text_lines) == 0:
                text_lines = [""]
            for line in text_lines:
                lw, lh = gc.GetTextExtent(line)
                text_line_sizes.append((lw, lh))
                text_w = max(text_w, lw)
                text_h += lh
            if len(text_lines) > 1:
                line_gap = 1
                text_h += line_gap * (len(text_lines) - 1)

        iw, ih = 0, 0
        if icon_char:
            icon_font_obj = _theme.font("icon")
            if self.icon_font_family:
                icon_font_obj.SetFaceName(self.icon_font_family)
            icon_gfx_font = gc.CreateFont(icon_font_obj, final_icon_color)
            gc.SetFont(icon_gfx_font)
            iw, ih = gc.GetTextExtent(icon_char)

        has_text = len(text_lines) > 0
        gap = 10 if (icon_char and has_text) else 0
        total_w = iw + gap + text_w
        start_x = (width - total_w) / 2

        if icon_char:
            gc.SetFont(icon_gfx_font)
            icon_x = start_x
            icon_y = (height - ih) / 2
            if self.icon_rotation_degrees:
                gc.PushState()
                gc.Translate(icon_x + (iw / 2), icon_y + (ih / 2))
                gc.Rotate(math.radians(self.icon_rotation_degrees))
                gc.DrawText(icon_char, -(iw / 2), -(ih / 2))
                gc.PopState()
            else:
                gc.DrawText(icon_char, icon_x, icon_y)

        if has_text:
            gc.SetFont(gc.CreateFont(_theme.font("button"), final_text))
            text_x = start_x + iw + gap
            text_y = (height - text_h) / 2
            for idx, line in enumerate(text_lines):
                _, lh = text_line_sizes[idx]
                gc.DrawText(line, text_x, text_y)
                text_y += lh + line_gap

    def on_mouse_down(self, event):
        if self.IsEnabled():
            wx.PostEvent(self, ParameterInteractionEvent(self.GetId()))
            self.pressed = True; self.Refresh(); self.Update()
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
    def SetIconRotation(self, degrees): self.icon_rotation_degrees = degrees % 360; self.Refresh(); self.Update()
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
    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class PresetCard(wx.Panel):
    """
    Preset card matching Component/PresetCard
    """
    def __init__(self, parent, label=None, icon_name=None, size=(90, 64), id=wx.ID_ANY, section=None):
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
                label = _locale.get(f"component.preset_card.{self.style_id}.label", self.style_id)
            if icon_name is None:
                icon_name = _locale.get(f"component.preset_card.{self.style_id}.icon_ref")

        if label is None:
            label = _locale.get("components.preset_card.default.label", "PRESET")

        self.label, self.icon_name, self.selected = label, icon_name, False
        self.hovered = False

        _p = self.GetParent()
        while _p is not None:
            if hasattr(_p, '_registry'):
                _p._registry.add(self, section=section)
                break
            _p = _p.GetParent()

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
        
        # Theme token mapping
        token = f"components.preset_card.{self.style_id}" if self.style_id else "components.preset_card.default"
        if not _theme.has_token(token):
            token = "components.preset_card.default"
            
        bg = _theme.color(f"{token}.frame.bg", self.hovered, self.selected, enabled)
        border = _theme.color(f"{token}.frame.border.color", self.hovered, self.selected, enabled) if _theme.has_token(f"{token}.frame.border.color") else None
        
        txt_color = _theme.color(f"{token}.label.color", self.hovered, self.selected, enabled)

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

        _, iw, ih = prepare_styled_text(gc, icon_char, f"{token}.icon", icon_color)
        
        _, tw, th = prepare_styled_text(gc, self.label, f"{token}.label", txt_color)

        gap, total_h = 8, ih + 8 + th
        start_y = (height - total_h) / 2

        draw_styled_text(gc, icon_char, f"{token}.icon", (width - iw) / 2, start_y, icon_color)
        draw_styled_text(gc, self.label, f"{token}.label", (width - tw) / 2, start_y + ih + gap, txt_color)

    def on_click(self, event):
        if self.IsEnabled():
            wx.PostEvent(self, ParameterInteractionEvent(self.GetId()))
            self.selected = True; self.Refresh(); self.Update()
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)

    def SetSelected(self, selected): self.selected = selected; self.Refresh(); self.Update()
    def SetLabel(self, label): self.label = str(label); self.Refresh(); self.Update()
    def IsSelected(self): return self.selected
    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class SectionLabel(wx.Panel):
    """
    Section label matching Component/SectionLabel.
    Uses create_text() so formatting (e.g. uppercase) is driven by YAML.
    Rule: style names passed to create_text() should use TextStyles alias keys.
    Paint-time helpers may use direct component theme paths.
    """
    def __init__(self, parent, label=None, size=(-1, 20), id="default"):
        if label is None:
            label = _locale.get("components.section.default.label", "Section")
        super().__init__(parent, size=size)
        self.style_id = id
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._txt = create_text(self, label, "header")
        sizer.Add(self._txt, 0, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(sizer)


class CustomInput(wx.Panel):
    """
    HUD-style input using a visible native wx.TextCtrl for rich editing.
    The parent panel draws the HUD frame (border/bg) and non-editable elements (units/icons).
    """
    def __init__(self, parent, value="", placeholder="", size=(-1, 32), id=wx.ID_ANY, section=None, allow_empty=False, **kwargs):
        if isinstance(id, str):
            self.style_id = id
            real_id = wx.ID_ANY
        else:
            self.style_id = "default"
            real_id = id

        # Enforce minimum width
        actual_size = list(size)
        if actual_size[0] == -1: actual_size[0] = 100

        super().__init__(parent, id=real_id, size=tuple(actual_size))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        # Resolve DNA
        self.token = f"components.input.{self.style_id}"
        if not _theme.has_token(self.token): self.token = "components.input.default"

        self.type = _theme._resolve(f"{self.token}.type") or "text"
        self.case = _theme._resolve(f"{self.token}.case") or "none"
        self.unit = kwargs.get('unit') or _theme._resolve(f"{self.token}.unit") or ""
        self.prefix = kwargs.get('prefix') or _theme._resolve(f"{self.token}.prefix")
        if not isinstance(self.prefix, str) or self.prefix == "#FF00FF": self.prefix = ""

        # Allow empty values (don't revert on blur)
        self.allow_empty = allow_empty
        
        # 1. Native Control
        style = wx.TE_PROCESS_ENTER | wx.BORDER_NONE
        self.multiline = kwargs.get('multiline', False)
        if self.multiline:
            style |= wx.TE_MULTILINE | wx.TE_NO_VSCROLL | wx.TE_RICH
        
        # Determine native alignment
        align_token = _theme._resolve(f"{self.token}.alignment")
        if align_token == "right" or self.type == "numeric":
            style |= wx.TE_RIGHT
        elif align_token == "center":
            style |= wx.TE_CENTRE
            
        self.text_ctrl = wx.TextCtrl(self, value=str(value), style=style)
        self.text_ctrl.SetBackgroundColour("TRANSPARENT")
        
        if hasattr(self.text_ctrl, 'SetFocusAppearance'):
            self.text_ctrl.SetFocusAppearance(False)
        if hasattr(self.text_ctrl, 'OSXSetFocusRingStyle'):
            self.text_ctrl.OSXSetFocusRingStyle(wx.USER_FOCUS_RING_NONE)
        
        # Aggressive Mac suppression
        disable_mac_focus_ring(self.text_ctrl)
        
        # 2. State
        self.placeholder = str(placeholder)
        self._placeholder_active = False
        self.hovered = False
        self.original_value = str(value)
        self.icon_ref = _theme._resolve(f"{self.token}.icon")
        self.show_chip = False
        
        self.chip = None
        if self.type == "rich":
            self.chip = ProjectFolderChip(self)
            self.chip.Hide()

        # 3. Bindings
        self.text_ctrl.Bind(wx.EVT_TEXT, self._on_text)
        self.text_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_enter)
        self.text_ctrl.Bind(wx.EVT_SET_FOCUS, self._on_focus)
        self.text_ctrl.Bind(wx.EVT_KILL_FOCUS, self._on_blur)
        self.text_ctrl.Bind(wx.EVT_ENTER_WINDOW, self._on_mouse_enter)
        self.text_ctrl.Bind(wx.EVT_LEAVE_WINDOW, self._on_mouse_leave)
        
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_SET_FOCUS, lambda e: self.text_ctrl.SetFocus())
        self.Bind(wx.EVT_ENTER_WINDOW, self._on_mouse_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_mouse_leave)
        self.Bind(wx.EVT_LEFT_DOWN, lambda e: self.text_ctrl.SetFocus())

        _p = self.GetParent()
        while _p is not None:
            if hasattr(_p, '_registry'):
                _p._registry.add(self, section=section)
                break
            _p = _p.GetParent()

        # Show placeholder for multiline fields when initially empty
        if self.multiline and self.placeholder and not value:
            wx.CallAfter(self._show_placeholder)

    def _show_placeholder(self):
        """Display placeholder as muted styled text inside the text control."""
        if not self.placeholder or self._placeholder_active:
            return
        self._placeholder_active = True
        self.text_ctrl.ChangeValue(self.placeholder)
        self.text_ctrl.SetStyle(0, len(self.placeholder), wx.TextAttr(_theme.color(f"{self.token}.placeholder.color")))

    def _hide_placeholder(self):
        """Clear placeholder text so the user can type."""
        if not self._placeholder_active:
            return
        self._placeholder_active = False
        self.text_ctrl.ChangeValue("")

    def _on_text(self, e):
        val = self.text_ctrl.GetValue()
        
        # Auto-convert em-dash (—) to double hyphen (--) for CLI compatibility
        if "—" in val:
            pos = self.text_ctrl.GetInsertionPoint()
            new_val = val.replace("—", "--")
            self.text_ctrl.ChangeValue(new_val)
            # Adjust insertion point if we replaced a single char with two
            self.text_ctrl.SetInsertionPoint(pos + (len(new_val) - len(val)))
            val = new_val

        if self.case == "upper": self.text_ctrl.ChangeValue(val.upper())
        self._fire_event(wx.EVT_TEXT)
        e.Skip()

    def _on_enter(self, e): self._confirm(); self._fire_event(wx.EVT_TEXT_ENTER)
    def _on_focus(self, e):
        if self.IsEnabled():
            wx.PostEvent(self, ParameterInteractionEvent(self.GetId()))
        self._hide_placeholder()
        self.original_value = self.text_ctrl.GetValue()
        wx.CallAfter(self.text_ctrl.SelectAll)
        self.Refresh(); e.Skip()
    def _on_blur(self, e):
        self._confirm()
        if self.multiline and self.placeholder and not self.text_ctrl.GetValue().strip():
            self._show_placeholder()
        self.Refresh(); e.Skip()
    
    def _on_mouse_enter(self, e): self.hovered = True; self.Refresh(); e.Skip()
    def _on_mouse_leave(self, e): self.hovered = False; self.Refresh(); e.Skip()

    def _confirm(self):
        if self._placeholder_active:
            return
        val = self.text_ctrl.GetValue().strip()
        if not val and not self.allow_empty and not self.multiline:
            self.text_ctrl.ChangeValue(self.original_value)
        elif self.type == "numeric":
            try:
                v = float(val)
                self.text_ctrl.ChangeValue(f"{v:.2f}")
            except: pass

    def _fire_event(self, evt_type):
        evt = wx.PyCommandEvent(evt_type.typeId, self.GetId())
        evt.SetString(self.text_ctrl.GetValue())
        self.GetEventHandler().ProcessEvent(evt)

    def on_click(self, event): self.text_ctrl.SetFocus()
    def on_enter(self, event): self.hovered = True; self.Refresh(); self.Update()
    def on_leave(self, event): self.hovered = False; self.Refresh(); self.Update()

    def on_size(self, event):
        w, h = self.GetSize()
        # Area calculation
        px = 12
        if self.type == "rich": px = 36
        if self.type == "rich" and self.show_chip and self.chip:
            self.chip.Move(wx.Point(36, (h - self.chip.GetSize().y) / 2))
            px += self.chip.GetSize().x + 6
            
        pw = w - px - 12
        if self.type == "numeric":
            # Probe font size for unit width
            font = _theme.font(self.token)
            temp_dc = wx.ScreenDC(); temp_dc.SetFont(font)
            utw, _ = temp_dc.GetTextExtent(self.unit)
            pw -= (utw + 8)
            
        # Position native control
        if self.multiline:
            # Multiline fills available height with 8px padding
            # Increase width by reducing right padding to 4px
            pw = w - px - 4
            ph = h - 16
            self.text_ctrl.SetSize(pw, ph)
            self.text_ctrl.SetPosition((px, 8))
        else:
            ph = self.text_ctrl.GetBestSize().y - 4 # Add vertical padding
            self.text_ctrl.SetSize(pw, ph)
            self.text_ctrl.SetPosition((px, (h - ph) / 2))
        self.Refresh(); event.Skip()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self); gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = self.GetSize(); enabled = self.IsEnabled(); focused = self.text_ctrl.HasFocus()

        # 1. Sync Native Visuals
        tc = _theme.color(f"{self.token}.color", self.hovered, focused, enabled)
        bg = _theme.color(f"{self.token}.frame.bg", self.hovered, False, enabled)
        font = _theme.font(self.token)
        
        self.text_ctrl.SetBackgroundColour("TRANSPARENT")
        self.text_ctrl.SetForegroundColour(tc)
        self.text_ctrl.SetFont(font)
        
        if self.multiline:
            # Hack to darken bg for multiline since wx.TextCtrl doesn't support transparent bg in multiline mode
            shiftby = -10 if self.hovered else -1
            bgcolor = _theme._shift_color(bg, shiftby)
            self.text_ctrl.SetBackgroundColour(bgcolor)
            self.text_ctrl.SetDefaultStyle(wx.TextAttr(tc, bgcolor))
            # Re-apply per-character style so SetForegroundColour/SetDefaultStyle take effect
            # on existing text (SetDefaultStyle only affects future typed text in TE_RICH)
            if self._placeholder_active and self.placeholder:
                self.text_ctrl.SetStyle(0, len(self.placeholder), wx.TextAttr(_theme.color(f"{self.token}.placeholder.color"), bgcolor))
            else:
                real_text = self.text_ctrl.GetValue()
                if real_text:
                    self.text_ctrl.SetStyle(0, len(real_text), wx.TextAttr(tc, bgcolor))

        # 2. Draw HUD Frame
        bc_tok, bs_tok = f"{self.token}.frame.border.color", f"{self.token}.frame.border.size"
        if focused and _theme.has_token(f"{bc_tok}.active"):
            bc, bs = _theme.color(bc_tok, self.hovered, True, enabled), _theme.size(bs_tok) or 1
        elif focused:
            bc, bs = _theme.color("borders.focus.color"), _theme.size("borders.focus.size") or 1
        else:
            bc, bs = _theme.color(bc_tok, self.hovered, False, enabled), _theme.size(bs_tok) or 1

        gc.SetBrush(wx.Brush(bg)); gc.SetPen(wx.Pen(bc, bs))
        gc.DrawRoundedRectangle(1, 1, w - 2, h - 2, _theme.size(f"{self.token}.frame.radius") or 6)

        # 3. Draw Non-editable content
        if self.type == "rich" and self.icon_ref:
            icon_char = _theme.glyph(self.icon_ref)
            icon_color = _theme.color(f"{self.token}.icon.color", self.hovered, False, enabled) if _theme.has_token(f"{self.token}.icon.color") else tc
            _, _, ith = prepare_styled_text(gc, icon_char, f"{self.token}.icon_style", icon_color)
            draw_styled_text(gc, icon_char, f"{self.token}.icon_style", 12, (h - ith) / 2, icon_color)

        if self.type == "numeric" and self.unit:
            unit_color = _theme.color(f"{self.token}.color", self.hovered, False, enabled)
            _, utw, uth = prepare_styled_text(gc, self.unit, f"{self.token}.label", unit_color)
            draw_styled_text(gc, self.unit, f"{self.token}.label", w - utw - 12, (h - uth) / 2, unit_color)

    def GetValue(self):
        if self._placeholder_active:
            return ""
        return self.text_ctrl.GetValue().strip()
    
    # TODO - Do better hex value handling in input field
    def SetValue(self, val):
        if self.type == "numeric" and val is not None:
            try:
                v = float(val)
                self.text_ctrl.ChangeValue(f"{v:.2f}")
                self.Refresh()
                return
            except:
                pass    

        v = str(val)
        if self.prefix and v.startswith(self.prefix): v = v[len(self.prefix):]
        self._placeholder_active = False
        if self.multiline and self.placeholder and not v.strip():
            self._show_placeholder()
        else:
            self.text_ctrl.ChangeValue(v)
        self.Refresh()
    def SetEditable(self, e): self.text_ctrl.SetEditable(e); self.Enable(e); self.Refresh()
    def SetPath(self, p, in_project=False):
        self.text_ctrl.ChangeValue(p); self.show_chip = in_project
        if self.chip: self.chip.Show() if in_project else self.chip.Hide()
        self.Refresh()

    def AcceptsFocus(self): return self.IsEnabled()
    def AcceptsFocusFromKeyboard(self): return self.IsEnabled()


class ProjectFolderChip(wx.Panel):
    """
    Small orange chip for "PROJECT FOLDER" prefix
    """
    def __init__(self, parent):
        font = _theme.font("components.badge.label")
        height = _theme.size("components.badge.frame.height")
        pad_h = _theme.size("components.badge.frame.padding.horizontal")
        temp_dc = wx.ScreenDC(); temp_dc.SetFont(font)
        tw, th = temp_dc.GetTextExtent("PROJECT FOLDER")
        super().__init__(parent, size=(tw + pad_h * 2, height))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT); self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = self.GetSize()
        radius = _theme.size("components.badge.frame.radius")
        gc.SetBrush(wx.Brush(_theme.color("components.badge.frame.bg")))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, w, h, radius)
        label_text = _locale.get("component.badge.label", "PROJECT FOLDER")
        badge_color = _theme.color("components.badge.label.color")
        _, tw, th = prepare_styled_text(gc, label_text, "components.badge.label", badge_color)
        draw_styled_text(gc, label_text, "components.badge.label", (w - tw) / 2, (h - th) / 2, badge_color)

    def AcceptsFocus(self): return False
    def AcceptsFocusFromKeyboard(self): return False


class CustomColorPicker(wx.Panel):
    """
    Custom color picker matching Component/ColorPicker from Pencil design.
    """
    PRESETS = [("#000000", "BLACK"), ("#1A1F23", "SLATE"), ("#F5F0E8", "CREAM"), ("#FFFFFF", "WHITE")]

    def __init__(self, parent, current_color="#000000", section=None):
        super().__init__(parent)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.current_color, self.hover_idx, self.selection, self.editing = current_color.upper(), -1, -1, False
        self._update_selection()

        _p = self.GetParent()
        while _p is not None:
            if hasattr(_p, '_registry'):
                _p._registry.add(self, section=section)
                break
            _p = _p.GetParent()
        
        # Use consolidated CustomInput
        self.hex_input = CustomInput(self, value=self.current_color, placeholder="#000000", size=(100, 32), id="hex")
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
                evt = wx.PyCommandEvent(EVT_COLOURPICKER_CHANGED.typeId, self.GetId()); evt.SetString(h); self.GetEventHandler().ProcessEvent(evt)
        else: self.hex_input.SetValue(self.current_color)

    def _get_rects(self):
        w, h = self.GetSize()
        rects, x = {}, 12
        for i in range(len(self.PRESETS)): rects[f'preset_{i}'] = wx.Rect(x, 10, 28, 28); x += 38
        rects['divider'], x = x, x + 10
        # Expand custom hit area to include text below (28x40 total)
        rects['custom'], x = wx.Rect(x, 10, 28, 40), x + 42
        # Top-align to match swatches (y=10)
        rects['hex'] = wx.Rect(x, 10, 100, 28)
        return rects

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self); gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = self.GetSize(); enabled, rects = self.IsEnabled(), self._get_rects()
        
        # Theme token mappings
        bg = _theme.color("components.colorpicker.default.bg")
        gc.SetBrush(wx.Brush(_theme.disabled(bg) if not enabled else bg))
        gc.SetPen(wx.TRANSPARENT_PEN); gc.DrawRoundedRectangle(0, 0, w, h, 4)
        for i, (hv, lbl) in enumerate(self.PRESETS):
            r = rects[f'preset_{i}']; self._draw_swatch(gc, r.x, r.y, hv, lbl, i == self.selection, i == self.hover_idx, enabled)
        
        border = _theme.color("borders.subtle.color")
        gc.SetPen(wx.Pen(_theme.disabled(border) if not enabled else border, 1))
        dx = rects['divider']; gc.StrokeLine(dx, 10, dx, h - 10)
        # Only pass the 28x28 box for drawing, but use larger rect for hit detection
        rc = rects['custom']; self._draw_swatch(gc, rc.x, rc.y, self.current_color, "CUSTOM", self.selection == -1, self.hover_idx == 4, enabled)
        
        # Hex input frame is handled by CustomInput itself

    def _draw_swatch(self, gc, x, y, ch, lbl, sel, hov, enabled):
        sc = wx.Colour(ch); 
        
        # Swatch border role
        token = "components.colorpicker.default"
        bc_token = f"{token}.items.border.color"
        ibs_token = f"{token}.items.innerborder.size"
        ibc_token = f"{token}.items.innerborder.color"
        
        # 1. Background
        gc.SetBrush(wx.Brush(_theme.disabled(sc) if not enabled else sc))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(x, y, 28, 28, 4)
        
        # 2. Inner Border (Optional)
        if _theme.has_token(ibc_token):
            ibc = _theme.color(ibc_token, hov, sel, enabled)
            ibs = _theme.size(ibs_token) or 1
            gc.SetPen(wx.Pen(ibc, ibs))
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            # Inset by 1px to show inside outer border
            gc.DrawRoundedRectangle(x + 1, y + 1, 25, 25, 3)

        # 3. Outer Border
        stc = _theme.color(bc_token, hov, sel, enabled)
        thk = _theme.size(f"{token}.items.border.size") or 1
        gc.SetPen(wx.Pen(stc, thk))
        gc.SetBrush(wx.TRANSPARENT_BRUSH)
        gc.DrawRoundedRectangle(x, y, 28, 28, 4)
        
        _, tw, _ = prepare_styled_text(gc, lbl, f"{token}.label")
        draw_styled_text(gc, lbl, f"{token}.label",     x + (28 - tw) / 2, y + 32, _theme.color(f"{token}.label.color", hov, sel, enabled))

    def on_mouse_move(self, event):
        if not self.IsEnabled(): return
        p, r = event.GetPosition(), self._get_rects(); nh = -1
        for i in range(len(self.PRESETS)):
            if r[f'preset_{i}'].Contains(p): nh = i; break
        if nh == -1 and r['custom'].Contains(p): nh = 4
        if self.hover_idx != nh: self.hover_idx = nh; self.Refresh(); self.Update()

    def on_click(self, event):
        if not self.IsEnabled(): return
        wx.PostEvent(self, ParameterInteractionEvent(self.GetId()))
        p, r = event.GetPosition(), self._get_rects(); ci = -1
        for i in range(len(self.PRESETS)):
            if r[f'preset_{i}'].Contains(p): ci = i; break
        if ci == -1 and r['custom'].Contains(p): ci = 4
        if ci == -1: return
        if ci < 4:
            nc = self.PRESETS[ci][0]
            if nc != self.current_color:
                self.SetColor(nc)
                evt = wx.PyCommandEvent(EVT_COLOURPICKER_CHANGED.typeId, self.GetId()); evt.SetString(nc); self.GetEventHandler().ProcessEvent(evt)
        else:
            # Use ColourDialog and explicit parent
            data = wx.ColourData()
            data.SetColour(wx.Colour(self.current_color))
            dlg = wx.ColourDialog(wx.GetTopLevelParent(self), data)
            if dlg.ShowModal() == wx.ID_OK:
                no = dlg.GetColourData().GetColour()
                nh = "#%02X%02X%02X" % (no.Red(), no.Green(), no.Blue())
                self.SetColor(nh)
                evt = wx.PyCommandEvent(EVT_COLOURPICKER_CHANGED.typeId, self.GetId()); evt.SetString(nh); self.GetEventHandler().ProcessEvent(evt)
            dlg.Destroy()

    def on_leave(self, event): self.hover_idx = -1; self.Refresh(); self.Update()


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
            self._fire_event(EVT_LIST_ITEM_SELECTED)

    def handle_action_click(self, local_x):
        if self.confirm_mode:
            if local_x < 40: # Cancel
                self.confirm_mode = False
            else: # Confirm
                self._fire_event(EVT_LIST_ITEM_DELETED)
                return # Stop here as item is destroyed
        else:
            self.confirm_mode = True
        
        if self:
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
        
        # 2. Resolve Frame Border
        bc_token = f"{self.token}.frame.border.color"
        bc = _theme.color(bc_token, self.hovered, False, enabled)
        gc.SetPen(wx.Pen(bc, 1))
        
        radius = _theme.size(f"{self.token}.frame.radius") or 4
        gc.DrawRoundedRectangle(1, 1, w - 2, h - 2, radius)

        # 3. Icon & Label
        tc = _theme.color(f"{self.token}.label.color", self.hovered, False, enabled)

        text_x = 12
        if self.icon_ref:
            icon_char = _theme.glyph(self.icon_ref)
            _, _, ith = prepare_styled_text(gc, icon_char, f"{self.token}.icon", tc)
            draw_styled_text(gc, icon_char, f"{self.token}.icon", 12, (h - ith) / 2, tc)
            text_x = 36

        _, _, th = prepare_styled_text(gc, self.label, f"{self.token}.label", tc)
        draw_styled_text(gc, self.label, f"{self.token}.label", text_x, (h - th) / 2, tc)

        # 4. Actions
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
            
            draw_styled_text(gc, c_icon, f"{self.token}.icon", w - 70, (h - 16) / 2, c_color)
            draw_styled_text(gc, s_icon, f"{self.token}.icon", w - 30, (h - 16) / 2, s_color)
        else:
            # Draw Delete
            d_icon = _theme.glyph(_theme._resolve(f"{actions_token}.delete.icon"))
            d_color = _theme.color(f"{actions_token}.delete.color")
            draw_styled_text(gc, d_icon, f"{self.token}.icon", w - 30, (h - 16) / 2, d_color)


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
EVT_LIST_ITEM_SELECTED = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_LIST_ITEM_DELETED = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_COLOURPICKER_CHANGED = wx.PyEventBinder(wx.NewEventType(), 1)
