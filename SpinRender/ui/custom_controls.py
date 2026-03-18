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


# Font Families - sourced from Theme singleton
_JETBRAINS_MONO = _theme.font_family("mono")
_MDI_FONT_FAMILY = _theme.font_family("icon")
_OSWALD = _theme.font_family("display")

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
        _JETBRAINS_MONO: ["JetBrainsMono-VariableFont_wght.ttf"],
        _MDI_FONT_FAMILY: ["MaterialDesignIconsDesktop.ttf"],
        _OSWALD: ["Oswald-VariableFont_wght.ttf"]
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
    TRACK_COLOR = _theme.color("colors.bg.surface")  # migrated from wx.Colour(51, 51, 51)
    TRACK_HEIGHT = 8
    THUMB_WIDTH = 7
    THUMB_HEIGHT = 18

    def __init__(self, parent, value=50, min_val=0, max_val=100, size=(240, 18), color=None):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.dragging = False

        if color:
            self.fill_color = color
            self.thumb_color = color
        else:
            self.fill_color = _theme.color("colors.accent.primary")
            self.thumb_color = _theme.color("colors.accent.primary")

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
            self.Refresh()

    def _on_leave(self, event):
        """Mouse left slider control."""
        self._hovered = False
        self.Refresh()

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        track_y = (height - self.TRACK_HEIGHT) / 2
        thumb_y = (height - self.THUMB_HEIGHT) / 2

        # Apply disabled state to colors
        track_color = _theme.disabled(self.TRACK_COLOR) if not enabled else self.TRACK_COLOR
        fill_color = _theme.disabled(self.fill_color) if not enabled else self.fill_color
        thumb_color = _theme.disabled(self.thumb_color) if not enabled else self.thumb_color

        gc.SetBrush(wx.Brush(track_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, track_y, width, self.TRACK_HEIGHT, 4)

        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_width = ratio * width

        if fill_width > 0:
            gc.SetBrush(wx.Brush(fill_color))
            gc.DrawRoundedRectangle(0, track_y, fill_width, self.TRACK_HEIGHT, 4)

        thumb_x = fill_width - self.THUMB_WIDTH / 2
        thumb_x = max(0, min(thumb_x, width - self.THUMB_WIDTH))

        gc.SetBrush(wx.Brush(thumb_color))
        gc.DrawRoundedRectangle(thumb_x, thumb_y, self.THUMB_WIDTH, self.THUMB_HEIGHT, 2)

    def on_mouse_down(self, event):
        if not self.IsEnabled(): return
        self.dragging = True
        self.update_value_from_mouse(event.GetX())
        self.CaptureMouse()

    def on_mouse_up(self, event):
        if self.dragging:
            self.dragging = False
            if self.HasCapture():
                self.ReleaseMouse()

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

    def AcceptsFocus(self):
        return False

    def AcceptsFocusFromKeyboard(self):
        return False


class CustomToggleButton(wx.Panel):
    """
    Multi-state toggle matching Component/Toggle from Pencil
    Supports 2 or more states.
    """
    BG_COLOR = _theme.color("colors.bg.surface")
    TEXT_PRIMARY = _theme.color("colors.text.primary")
    DEFAULT_ACTIVE_BG = _theme.color("colors.accent.primary")
    # Note: BORDER_DEFAULT and TEXT_SECONDARY are used inline via theme.*

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
        """
        options: list of dicts like [{'label': 'ON', 'icon': 'mdi-check'}, ...]
        """
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.active_bg = active_color if active_color else self.DEFAULT_ACTIVE_BG
        
        if options is None:
            self.options = [
                {'label': 'OFF', 'icon': None},
                {'label': 'ON', 'icon': None}
            ]
        else:
            self.options = options
            
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

        # Border logic - apply disabled state
        bg_color = _theme.disabled(self.BG_COLOR) if not enabled else self.BG_COLOR
        border_color = _theme.disabled(_theme.color("colors.border.default")) if not enabled else _theme.color("colors.border.default")
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.Pen(border_color, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        # Draw Active Indicator - apply disabled state
        active_color = _theme.disabled(self.active_bg) if not enabled else self.active_bg
        gc.SetBrush(wx.Brush(active_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        active_x = self.selection * state_width
        gc.DrawRoundedRectangle(active_x + 1, 1, state_width - 2, height - 2, 4)

        # Draw each state
        for i, opt in enumerate(self.options):
            is_active = (i == self.selection)
            base_color = _theme.color("colors.text.primary") if is_active else _theme.color("colors.text.secondary")
            color = _theme.disabled(base_color) if not enabled else base_color
            self._draw_side(gc, opt.get('label'), opt.get('icon'), i * state_width, state_width, height, color)

    def _draw_side(self, gc, label, icon_name, x_offset, width, height, color):
        font = TextStyles.body_strong.create_font()
        icon_char = self.ICONS.get(icon_name, icon_name) if icon_name else None
        
        tw, th = 0, 0
        if label:
            gc.SetFont(font, color)
            tw, th = gc.GetTextExtent(label)
            
        iw, ih = 0, 0
        icon_font = None
        if icon_char:
            if icon_name and icon_name.startswith("mdi-"):
                icon_font = TextStyles.icon.create_font()
            else:
                icon_font = TextStyles.icon.create_font()
            gc.SetFont(icon_font, color)
            iw, ih = gc.GetTextExtent(icon_char)
            
        gap = 6 if (icon_char and label) else 0
        total_w = iw + gap + tw
        start_x = x_offset + (width - total_w) / 2
        
        if icon_char:
            gc.SetFont(icon_font, color)
            gc.DrawText(icon_char, start_x, (height - ih) / 2)
            
        if label:
            gc.SetFont(font, color)
            gc.DrawText(label, start_x + iw + gap, (height - th) / 2)

    def on_click(self, event):
        if not self.IsEnabled(): return
        
        # Calculate which option was clicked based on X position
        width = self.GetSize().x
        num_options = len(self.options)
        state_width = width / num_options
        
        click_x = event.GetX()
        new_selection = int(click_x // state_width)
        
        # Clip just in case of rounding at the very edge
        new_selection = max(0, min(new_selection, num_options - 1))
        
        if self.selection != new_selection:
            self.selection = new_selection
            self.Refresh()
            
            evt = wx.PyCommandEvent(wx.EVT_TOGGLEBUTTON.typeId, self.GetId())
            evt.SetInt(self.selection)
            self.GetEventHandler().ProcessEvent(evt)

    def GetSelection(self): return self.selection
    def SetSelection(self, index):
        if 0 <= index < len(self.options):
            self.selection = index
            self.Refresh()

    def GetStringSelection(self):
        return self.options[self.selection].get('label')

    def GetValue(self): 
        # Legacy support: return True if last state
        return self.selection == (len(self.options) - 1)
        
    def SetValue(self, value):
        # Legacy support: set to 1 if True, 0 if False
        self.selection = 1 if value else 0
        self.Refresh()

    def AcceptsFocus(self):
        return False

    def AcceptsFocusFromKeyboard(self):
        return False


class DropdownPopup(wx.PopupTransientWindow):
    """
    Transient popup window for the dropdown list
    """
    def __init__(self, parent, choices, current_selection, callback):
        super().__init__(parent, wx.BORDER_NONE)
        self.choices = choices
        self.selection = current_selection
        self.callback = callback
        self.hover_index = -1
        
        self.bg_color = _theme.color("colors.bg.surface")
        self.accent_color = _theme.color("colors.accent.primary")
        self.text_primary = _theme.color("colors.text.primary")
        self.text_muted = _theme.color("colors.text.muted")
        self.border_color = _theme.color("colors.border.default")
        
        self.item_height = 32
        self.SetBackgroundColour(self.bg_color)
        
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        gc.SetBrush(wx.Brush(self.bg_color))
        gc.SetPen(wx.Pen(self.border_color, 1))
        gc.DrawRoundedRectangle(0, 0, width, height, 4)

        font = TextStyles.body.create_font()
        selected_font = TextStyles.body_strong.create_font()

        for i, choice in enumerate(self.choices):
            rect = wx.Rect(4, 4 + (i * self.item_height), width - 8, self.item_height)
            
            is_selected = (i == self.selection)
            is_hovered = (i == self.hover_index)
            
            if is_selected:
                gc.SetBrush(wx.Brush(self.accent_color))
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, 2)
                gc.SetFont(selected_font, _theme.color("colors.bg.input"))
            elif is_hovered:
                gc.SetBrush(wx.Brush(_theme.color("colors.bg.panel")))  # hover background
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, 2)
                gc.SetFont(font, self.text_primary)
            else:
                gc.SetFont(font, self.text_primary)
                
            tw, th = gc.GetTextExtent(choice)
            gc.DrawText(choice, rect.x + 8, rect.y + (rect.height - th) / 2)

    def on_mouse_move(self, event):
        y = event.GetY() - 4
        idx = y // self.item_height
        if 0 <= idx < len(self.choices):
            if self.hover_index != idx:
                self.hover_index = idx
                self.Refresh()
        else:
            if self.hover_index != -1:
                self.hover_index = -1
                self.Refresh()

    def on_click(self, event):
        y = event.GetY() - 4
        idx = y // self.item_height
        if 0 <= idx < len(self.choices):
            self.callback(idx)
            self.Dismiss()

    def on_leave(self, event):
        self.hover_index = -1
        self.Refresh()


class CustomDropdown(wx.Panel):
    """
    Custom dropdown matching Component/Dropdown from Pencil
    """
    BG_COLOR = _theme.color("colors.bg.input")
    BORDER_COLOR = _theme.color("colors.border.default")
    TEXT_PRIMARY = _theme.color("colors.text.primary")
    # Note: TEXT_SECONDARY and ACCENT_CYAN are used inline via theme.*

    def __init__(self, parent, choices=None, size=(160, 32)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.choices = choices or []
        self.selection = 0
        self.hovered = False
        self.is_open = False
        
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(
            self,
            hover_handler=self.on_enter,
            leave_handler=self.on_leave,
            click_handler=self.on_click
        )

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        # Background (apply disabled state inline)
        bg_color = _theme.disabled(self.BG_COLOR) if not enabled else self.BG_COLOR
        gc.SetBrush(wx.Brush(bg_color))

        # Border (Accent Cyan if hovered or open)
        bc = _theme.color("colors.accent.primary") if (self.hovered or self.is_open) else _theme.color("colors.border.default")
        border_color = _theme.disabled(bc) if not enabled else bc
        gc.SetPen(wx.Pen(border_color, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        # Label
        label = self.choices[self.selection] if self.choices else "SELECT OPTION"
        font = TextStyles.body_strong.create_font()
        text_color = _theme.disabled(_theme.color("colors.text.primary")) if not enabled else _theme.color("colors.text.primary")
        gc.SetFont(font, text_color)
        tw, th = gc.GetTextExtent(label)
        gc.DrawText(label, 12, (height - th) / 2)

        # Chevron
        icon_char = CustomToggleButton.ICONS.get('mdi-chevron-up' if self.is_open else 'mdi-chevron-down')
        icon_font = TextStyles.icon.create_font()
        icon_color = _theme.color("colors.accent.primary") if self.is_open else _theme.color("colors.text.secondary")
        icon_color_disabled = _theme.disabled(icon_color) if not enabled else icon_color
        gc.SetFont(icon_font, icon_color_disabled)
        iw, ih = gc.GetTextExtent(icon_char)
        gc.DrawText(icon_char, width - iw - 12, (height - ih) / 2)

    def on_click(self, event):
        if not self.IsEnabled(): return
        self.show_popup()

    def on_enter(self, event):
        self.hovered = True
        self.Refresh()

    def on_leave(self, event):
        self.hovered = False
        self.Refresh()

    def show_popup(self):
        if not self.choices: return
        
        width, height = self.GetSize()
        popup_height = (len(self.choices) * 32) + 8
        
        popup = DropdownPopup(self, self.choices, self.selection, self.on_select)
        popup.SetSize((width, popup_height))
        
        # Calculate position
        pos = self.ClientToScreen(wx.Point(0, height))
        
        # Check if it fits below
        display_rect = wx.Display().GetClientArea()
        if pos.y + popup_height > display_rect.height:
            # Render above instead
            pos.y = pos.y - height - popup_height
            
        popup.Position(pos, wx.Size(0, 0))
        
        self.is_open = True
        self.Refresh()
        popup.Popup()
        self.is_open = False
        self.Refresh()

    def on_select(self, index):
        if self.selection != index:
            self.selection = index
            self.Refresh()
            evt = wx.PyCommandEvent(wx.EVT_CHOICE.typeId, self.GetId())
            evt.SetInt(index)
            evt.SetString(self.choices[index])
            self.GetEventHandler().ProcessEvent(evt)

    def GetSelection(self): return self.selection
    def SetSelection(self, index):
        if 0 <= index < len(self.choices):
            self.selection = index
            self.Refresh()

    def GetStringSelection(self):
        return self.choices[self.selection] if self.choices else ""

    def SetChoices(self, choices):
        self.choices = choices
        self.selection = 0
        self.Refresh()

    def AcceptsFocus(self):
        return False

    def AcceptsFocusFromKeyboard(self):
        return False


class CustomButton(wx.Panel):
    """
    Custom action button matching Component/ActionButton and SecondaryButton
    Supports custom icon fonts like Material Design Icons.
    """
    ICONS = {
        'play': '▶',
        'eye': '👁',
        'save': '💾',
        'settings': '⚙',
        'check': '✓',
        'alert': '⚠',
        'download': '⬇',
        'folder': '📁',
        'close': '✕',
        # MDI hex codes (v7.x Desktop)
        'mdi-download': '\U000F01DA',
        'mdi-close': '\U000F0156',
        'mdi-cog': '\U000F0493',
        'mdi-play': '\U000F040D',
        'mdi-stop': '\U000F04DB',
        'mdi-video-vintage': '\U000F0A1C',
        'mdi-folder': '\U000F024B',
        'mdi-check': '\U000F012C',
        'mdi-alert': '\U000F0026',
        'mdi-information-outline': '\U000F02FD',
        'mdi-trash-can-outline': '\U000F0A7A',
        'mdi-alert-octagram': '\U000F0767',
        'mdi-exit-to-app': '\U000F0206',
        'mdi-palette': '\U000F03E8'
    }

    def __init__(self, parent, label="BUTTON", icon=None, icon_font_family=None, primary=True, ghost=False, danger=False, icon_color=None, icon_color_hover=None, icon_color_pressed=None, bg_color=None, bg_color_hover=None, bg_color_pressed=None, size=(-1, 36)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        self.label = str(label)
        self.icon = icon
        self.icon_font_family = icon_font_family
        self.primary = primary
        self.ghost = ghost
        self.danger = danger
        self.icon_color_override = icon_color
        self.icon_color_hover = icon_color_hover
        self.icon_color_pressed = icon_color_pressed
        self.bg_color_override = bg_color
        self.bg_color_hover = bg_color_hover
        self.bg_color_pressed = bg_color_pressed
        self.hovered = False
        self.pressed = False

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        bind_mouse_events(
            self,
            hover_handler=self.on_enter,
            leave_handler=self.on_leave,
            click_handler=self.on_mouse_down
        )

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        # Style colors - migrated to theme
        if self.primary:
            if self.danger:
                bg_base, text_base, border_base = _theme.color("colors.accent.warning"), _theme.color("colors.text.primary"), None
            else:
                bg_base, text_base, border_base = _theme.color("colors.accent.primary"), _theme.color("colors.bg.input"), None
        elif self.ghost:
            bg_base, text_base, border_base = _theme.TRANSPARENT, _theme.color("colors.text.primary"), None
        else:
            bg_base, text_base, border_base = _theme.color("colors.bg.input"), _theme.color("colors.text.primary"), _theme.color("colors.border.default")

        # Apply interaction feedback to base colors
        bg = bg_base
        text_color = text_base

        # Allow explicit state colors to override automatic state handling
        if self.bg_color_override:
            if self.pressed and self.bg_color_pressed:
                bg = self.bg_color_pressed
            elif self.hovered and self.bg_color_hover:
                bg = self.bg_color_hover
            elif self.bg_color_override:
                bg = self.bg_color_override
        else:
            if self.danger and self.primary:
                if self.pressed: bg = _theme.DANGER_DARK
                elif self.hovered: bg = _theme.DANGER_HOVER
            elif self.danger:
                if self.pressed:
                    bg = _theme.DANGER_MEDIUM
                    text_color = _theme.WHITE
                elif self.hovered:
                    bg = _theme.DANGER_HOVER
                    text_color = _theme.WHITE
            elif not self.ghost:
                if self.pressed:
                    bg = wx.Colour(max(0, bg.Red()-30), max(0, bg.Green()-30), max(0, bg.Blue()-30))
                elif self.hovered:
                    inc = 20 if self.primary else 30
                    bg = wx.Colour(min(255, bg.Red()+inc), min(255, bg.Green()+inc), min(255, bg.Blue()+inc))
            else:
                if self.pressed:
                    bg = _theme.WHITE_ALPHA_40
                    text_color = _theme.WHITE
                elif self.hovered:
                    bg = _theme.WHITE_ALPHA_20
                    text_color = _theme.WHITE

        # Apply disabled state directly (no _get_paint_color helper)
        final_bg = _theme.disabled(bg) if not enabled else bg
        final_text = _theme.disabled(text_color) if not enabled else text_color

        # Determine final icon color (priority to override with state-aware colors)
        final_icon_color = final_text
        if self.icon_color_override:
            if self.pressed and self.icon_color_pressed:
                final_icon_color = self.icon_color_pressed if enabled else _theme.disabled(self.icon_color_pressed)
            elif self.hovered and self.icon_color_hover:
                final_icon_color = self.icon_color_hover if enabled else _theme.disabled(self.icon_color_hover)
            else:
                final_icon_color = self.icon_color_override if enabled else _theme.disabled(self.icon_color_override)

        if not self.ghost or (self.hovered or self.pressed):
            gc.SetBrush(wx.Brush(final_bg))
            if border_base:
                border_color = _theme.disabled(border_base) if not enabled else border_base
                gc.SetPen(wx.Pen(border_color, 1))
            else:
                gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        # Prepare fonts and measure content
        icon_char = self.ICONS.get(self.icon, self.icon) if self.icon else None
        label_font = TextStyles.body_strong.create_font()

        tw, th = 0, 0
        if self.label:
            gc.SetFont(label_font, final_text)
            tw, th = gc.GetTextExtent(self.label)

        iw, ih = 0, 0
        icon_font = None
        if icon_char:
            if self.icon_font_family:
                icon_font = TextStyle(family=self.icon_font_family, size=14, weight=400).create_font()
            elif isinstance(self.icon, str) and self.icon.startswith("mdi-"):
                icon_font = TextStyles.icon.create_font()
            else:
                icon_font = TextStyles.icon.create_font()
            gc.SetFont(icon_font, final_icon_color)
            iw, ih = gc.GetTextExtent(icon_char)

        # Calculate total group width for horizontal centering
        gap = 10 if (icon_char and self.label) else 0
        total_w = iw + gap + tw
        start_x = (width - total_w) / 2

        # Draw icon centered vertically
        if icon_char:
            gc.SetFont(icon_font, final_icon_color)
            gc.DrawText(icon_char, start_x, (height - ih) / 2)

        # Draw label centered vertically
        if self.label:
            gc.SetFont(label_font, final_text)
            gc.DrawText(self.label, start_x + iw + gap, (height - th) / 2)

    def on_mouse_down(self, event):
        if not self.IsEnabled(): return
        self.pressed = True
        self.Refresh()

    def on_mouse_up(self, event):
        if self.pressed:
            self.pressed = False
            self.Refresh()
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)

    def on_enter(self, event):
        if not self.IsEnabled(): return
        self.hovered = True
        self.Refresh()

    def on_leave(self, event):
        self.hovered = False
        self.pressed = False
        self.Refresh()

    def SetLabel(self, label):
        self.label = str(label)
        self.Refresh()

    def SetIcon(self, icon):
        self.icon = icon
        self.Refresh()

    def SetPrimary(self, primary):
        self.primary = primary
        self.Refresh()

    def SetDanger(self, danger):
        self.danger = danger
        self.Refresh()

    def AcceptsFocus(self):
        return False

    def AcceptsFocusFromKeyboard(self):
        return False


class PresetCard(wx.Panel):
    """
    Preset card matching Component/PresetCard
    """
    BG_COLOR = _theme.color("colors.bg.surface")
    # Other colors inlined in methods per test expectations
    ICONS = {
        'rotate-cw': '↻',
        'rotate-ccw': '↺',
        'arrow-down': '↓',
        'arrow-up': '↑',
        'circle': '○',
        'star': '⭐',
        'mdi-rotate-cw': '\U000F0465',
        'mdi-arrow-down': '\U000F0045',
        'mdi-arrow-up': '\U000F005D',
        'mdi-circle': '\U000F012F',
        'mdi-star-settings-outline': '\U000F166B',
        'mdi-rotate-360': '\U000F1999',
        'mdi-rotate-orbit': '\U000F0D98',
        'mdi-horizontal-rotate-counterclockwise': '\U000F10F4'
    }

    def __init__(self, parent, label="PRESET", icon_name="rotate-cw", size=(90, 64)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.label = label
        self.icon_name = icon_name
        self.selected = False
        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, click_handler=self.on_click)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        bg = _theme.color("colors.bg.panel") if self.selected else _theme.color("colors.bg.surface")
        border = _theme.color("colors.accent.primary") if self.selected else _theme.color("colors.border.default")
        txt_color = _theme.color("colors.accent.primary") if self.selected else _theme.color("colors.text.secondary")

        # Apply disabled state directly
        bg_color = _theme.disabled(bg) if not enabled else bg
        border_color = _theme.disabled(border) if not enabled else border
        text_color = _theme.disabled(txt_color) if not enabled else txt_color

        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.Pen(border_color, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        icon_char = self.ICONS.get(self.icon_name, self.icon_name)
        icon_font = TextStyles.icon_lg.create_font() if str(self.icon_name).startswith("mdi-") else TextStyles.icon_lg.create_font()

        gc.SetFont(icon_font, text_color)
        iw, ih = gc.GetTextExtent(icon_char)
        gc.DrawText(icon_char, (width - iw) / 2, 14)

        font = TextStyles.label_sm.create_font()
        gc.SetFont(font, text_color)
        tw, th = gc.GetTextExtent(self.label)
        gc.DrawText(self.label, (width - tw) / 2, height - th - 8)

    def on_click(self, event):
        if not self.IsEnabled(): return
        self.selected = True
        self.Refresh()
        evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)

    def SetSelected(self, selected):
        self.selected = selected
        self.Refresh()

    def SetLabel(self, label):
        self.label = str(label).upper()
        self.Refresh()

    def IsSelected(self): return self.selected

    def AcceptsFocus(self):
        return False

    def AcceptsFocusFromKeyboard(self):
        return False


class SectionLabel(wx.Panel):
    """
    Section label matching Component/SectionLabel
    """
    TEXT_COLOR = _theme.color("colors.text.secondary")
    LINE_COLOR = _theme.color("colors.border.default")

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
        font = TextStyles.section_heading.create_font()
        gc.SetFont(font, self.TEXT_COLOR)
        tw, th = gc.GetTextExtent(self.label)
        gc.DrawText(self.label, 0, (height - th) / 2)

        line_x = tw + 8
        line_y = height / 2
        if width - line_x > 0:
            gc.SetPen(wx.Pen(self.LINE_COLOR, 1))
            gc.StrokeLine(line_x, line_y, width, line_y)


class NumericDisplay(wx.Panel):
    """
    Numeric value display matching Component/NumericInput
    """
    BG_COLOR = _theme.color("colors.bg.input")
    # Other colors inlined via theme.* in on_paint

    def __init__(self, parent, value=0.0, unit="", size=(100, 32)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.value = value
        self.unit = unit
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        # Apply disabled state to colors
        bg = _theme.disabled(_theme.color("colors.bg.input")) if not enabled else _theme.color("colors.bg.input")
        border = _theme.disabled(_theme.color("colors.border.default")) if not enabled else _theme.color("colors.border.default")
        accent = _theme.disabled(_theme.color("colors.accent.secondary")) if not enabled else _theme.color("colors.accent.secondary")
        secondary = _theme.disabled(_theme.color("colors.text.secondary")) if not enabled else _theme.color("colors.text.secondary")

        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(wx.Pen(border, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        v_str = f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
        v_font = TextStyles.numeric_value.create_font()
        gc.SetFont(v_font, accent)
        vw, vh = gc.GetTextExtent(v_str)

        u_font = TextStyles.body.create_font()
        gc.SetFont(u_font, secondary)
        uw, uh = gc.GetTextExtent(self.unit)

        total_w = vw + 4 + uw
        start_x = width - total_w - 8
        gc.DrawText(v_str, start_x, (height - vh) / 2)
        gc.DrawText(self.unit, start_x + vw + 4, (height - uh) / 2)

    def SetValue(self, value):
        self.value = value
        self.Refresh()
    def GetValue(self): return self.value


class NumericInput(wx.Panel):
    """
    Editable numeric input matching Component/NumericInput
    """
    BG_COLOR = _theme.color("colors.bg.input")
    BORDER_FOCUS = _theme.color("colors.accent.primary")
    VALUE_EDIT = _theme.color("colors.text.primary")
    # Border default, VALUE_COLOR (ACCENT_YELLOW), UNIT_COLOR (TEXT_SECONDARY) inlined

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

        # Background
        bg = _theme.disabled(_theme.color("colors.bg.input")) if not enabled else _theme.color("colors.bg.input")
        gc.SetBrush(wx.Brush(bg))

        # Border
        bc = _theme.color("colors.accent.primary") if self.editing else _theme.color("colors.border.default")
        border = _theme.disabled(bc) if not enabled else bc
        gc.SetPen(wx.Pen(border, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        if self.editing:
            v_str, v_color = self.edit_text, _theme.color("colors.text.primary")
        else:
            v_str = f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
            v_color = _theme.color("colors.accent.secondary")

        v_font = TextStyles.numeric_value.create_font()
        v_color_disabled = _theme.disabled(v_color) if not enabled else v_color
        gc.SetFont(v_font, v_color_disabled)
        vw, vh = gc.GetTextExtent(v_str)

        u_font = TextStyles.body.create_font()
        unit_color = _theme.disabled(_theme.color("colors.text.secondary")) if not enabled else _theme.color("colors.text.secondary")
        gc.SetFont(u_font, unit_color)
        uw, uh = gc.GetTextExtent(self.unit)

        total_w = vw + 4 + uw
        start_x = width - total_w - 8
        gc.DrawText(v_str, start_x, (height - vh) / 2)
        gc.DrawText(self.unit, start_x + vw + 4, (height - uh) / 2)

        if self.editing:
            cx = start_x + vw + 2
            cy1 = (height - vh) / 2
            edit_color = _theme.disabled(self.VALUE_EDIT) if not enabled else self.VALUE_EDIT
            gc.SetPen(wx.Pen(edit_color, 1))
            gc.StrokeLine(cx, cy1, cx, cy1 + vh)

    def on_click(self, event):
        if not self.IsEnabled(): return
        if not self.editing:
            self.editing, self.original_value, self.text_selected = True, self.value, True
            self.edit_text = f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
            self.SetFocus(); self.Refresh()

    def on_focus_gained(self, event):
        if not self.IsEnabled(): return
        if not self.editing:
            self.editing, self.original_value, self.text_selected = True, self.value, True
            self.edit_text = f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
            self.Refresh()
        event.Skip()

    def on_char(self, event):
        if not self.IsEnabled(): return
        key = event.GetKeyCode()
        if not self.editing:
            # Allow arrow keys to adjust value even when not editing
            if key in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_NUMPAD_UP, wx.WXK_NUMPAD_DOWN):
                self._handle_arrow(key, event.ShiftDown())
            event.Skip()
            return

        if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self.confirm_edit()
        elif key == wx.WXK_ESCAPE:
            self.cancel_edit()
        elif key == wx.WXK_TAB:
            self.confirm_edit()
            event.Skip()
        elif key in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_NUMPAD_UP, wx.WXK_NUMPAD_DOWN):
            self._handle_arrow(key, event.ShiftDown())
        elif key == wx.WXK_BACK:
            if self.text_selected:
                self.edit_text, self.text_selected = "", False
            else:
                self.edit_text = self.edit_text[:-1]
            self.Refresh()
        else:
            char = chr(key) if key < 256 else None
            if char and (char.isdigit() or char in '.-'):
                if self.text_selected:
                    self.edit_text, self.text_selected = char, False
                else:
                    self.edit_text += char
                self.Refresh()

    def _handle_arrow(self, key, shift_pressed):
        """Handle Up/Down arrow keys to increment/decrement value."""
        # Determine step size: 0.1 for normal, 1.0 for Shift
        step = 1.0 if shift_pressed else 0.1

        # Get current value from edit_text if editing, else from value
        try:
            current = float(self.edit_text) if self.editing and self.edit_text else self.value
        except (ValueError, TypeError):
            current = self.value

        # Apply increment/decrement
        if key in (wx.WXK_UP, wx.WXK_NUMPAD_UP):
            new_val = current + step
        else:  # Down
            new_val = current - step

        # Clamp to min/max
        if self.min_val is not None:
            new_val = max(self.min_val, new_val)
        if self.max_val is not None:
            new_val = min(self.max_val, new_val)

        # Round to 1 decimal place to avoid floating point precision issues
        new_val = round(new_val, 1)

        # Update value and edit_text
        self.value = new_val
        if self.editing:
            self.edit_text = f"{new_val:.2f}" if isinstance(new_val, float) else str(new_val)
            self.text_selected = True  # Select all on next paint? We'll just refresh
        self.Refresh()

        # Emit change event
        evt = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId, self.GetId())
        evt.SetString(str(new_val))
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
            self.Refresh()
            evt = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId, self.GetId())
            evt.SetString(str(val))
            self.GetEventHandler().ProcessEvent(evt)
        except ValueError: self.cancel_edit()

    def cancel_edit(self):
        self.value, self.editing = self.original_value, False
        self.Refresh()

    def SetValue(self, value):
        self.value = value
        if not self.editing: self.Refresh()
    def GetValue(self): return self.value

    def AcceptsFocus(self):
        return self.IsEnabled()

    def AcceptsFocusFromKeyboard(self):
        return self.IsEnabled()


class CustomTextInput(wx.Panel):
    """
    Custom text input using wx.Panel to avoid native OS focus highlights.
    Supports multiline and placeholder text.
    """
    BG_COLOR = _theme.color("colors.bg.input")
    TEXT_COLOR = _theme.color("colors.text.primary")
    PLACEHOLDER_COLOR = _theme.color("colors.text.muted")
    # BORDER_DEFAULT and ACCENT_CYAN inlined in on_paint

    def __init__(self, parent, value="", placeholder="", multiline=False, size=(-1, 36)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.value = str(value).upper()
        self.placeholder = str(placeholder)
        self.multiline = multiline
        self.is_placeholder_active = not self.value and self.placeholder

        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(self, click_handler=self.on_click)
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_focus_lost)
        self.Bind(wx.EVT_SET_FOCUS, self.on_focus_gained)
        self.SetCanFocus(True)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()

        # Background
        bg = _theme.disabled(_theme.color("colors.bg.input")) if not enabled else _theme.color("colors.bg.input")
        gc.SetBrush(wx.Brush(bg))

        # Border
        bc = _theme.color("colors.accent.primary") if self.HasFocus() else _theme.color("colors.border.default")
        border = _theme.disabled(bc) if not enabled else bc
        gc.SetPen(wx.Pen(border, 1))
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        # Text
        font = TextStyles.body.create_font()

        if self.is_placeholder_active and not self.HasFocus():
            display_text = self.placeholder
            text_color = self.PLACEHOLDER_COLOR
        else:
            display_text = self.value
            text_color = self.TEXT_COLOR

        text_color_disabled = _theme.disabled(text_color) if not enabled else text_color
        gc.SetFont(font, text_color_disabled)

        if self.HasFocus():
            display_text += "|"

        if self.multiline:
            # Simple wrapping/multiline support
            gc.DrawText(display_text, 12, 10)
        else:
            tw, th = gc.GetTextExtent(display_text)
            gc.DrawText(display_text, 12, (height - th) / 2)

    def on_click(self, event):
        if not self.IsEnabled(): return
        self.SetFocus()
        self.Refresh()

    def on_char(self, event):
        if not self.IsEnabled(): return
        key = event.GetKeyCode()
        
        if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            if self.multiline:
                self.value += "\n"
                self.Refresh()
            else:
                # Trigger enter event for single line
                evt = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId, self.GetId())
                self.GetEventHandler().ProcessEvent(evt)
        elif key == wx.WXK_BACK:
            if len(self.value) > 0:
                self.value = self.value[:-1]
                self.Refresh()
        elif key == wx.WXK_TAB:
            event.Skip()
        else:
            char = chr(key) if key < 256 else None
            if char and char.isprintable():
                self.value += char.upper()
                self.Refresh()
                
        # Update placeholder state
        self.is_placeholder_active = not self.value and self.placeholder
                
        # Trigger generic text event
        evt = wx.PyCommandEvent(wx.EVT_TEXT.typeId, self.GetId())
        evt.SetString(self.value)
        self.GetEventHandler().ProcessEvent(evt)

    def on_focus_gained(self, event):
        self.Refresh()
        event.Skip()

    def on_focus_lost(self, event):
        self.Refresh()
        event.Skip()

    def GetValue(self): return self.value.strip()
    def SetValue(self, val):
        self.value = str(val).upper()
        self.is_placeholder_active = not self.value and self.placeholder
        self.Refresh()

    def AcceptsFocus(self):
        return self.IsEnabled()

    def AcceptsFocusFromKeyboard(self):
        return self.IsEnabled()


class ProjectFolderChip(wx.Panel):
    """
    Small orange chip for "PROJECT FOLDER" prefix
    """
    def __init__(self, parent):
        # Measure text to get width
        font = TextStyles.label_xs.create_font()
        temp_dc = wx.ScreenDC()
        temp_dc.SetFont(font)
        tw, th = temp_dc.GetTextExtent("PROJECT FOLDER")
        
        super().__init__(parent, size=(tw + 12, 18))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        w, h = self.GetSize()
        gc.SetBrush(wx.Brush(_theme.color("colors.accent.warning")))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, w, h, 4)

        gc.SetFont(TextStyles.label_xs.create_font(), _theme.color("colors.bg.page"))
        tw, th = gc.GetTextExtent("PROJECT FOLDER")
        gc.DrawText("PROJECT FOLDER", (w - tw) / 2, (h - th) / 2)

    def AcceptsFocus(self):
        return False

    def AcceptsFocusFromKeyboard(self):
        return False


class CustomColorPicker(wx.Panel):
    """
    Custom color picker matching Component/ColorPicker from Pencil design.
    Features swatches for presets and an editable hex color input.
    """
    BORDER_COLOR = _theme.color("colors.border.default")
    BG_INPUT = _theme.color("colors.bg.input")
    # BG_PANEL, ACCENT_CYAN, TEXT_MUTED, ACCENT_YELLOW inlined in on_paint

    PRESETS = [
        ("#000000", "BLACK"),
        ("#1A1F23", "SLATE"),
        ("#F5F0E8", "CREAM"),
        ("#FFFFFF", "WHITE")
    ]

    def __init__(self, parent, current_color="#000000"):
        super().__init__(parent)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.current_color = current_color.upper()

        self.hover_idx = -1 # 0-3 for presets, 4 for custom
        self.selection = -1 # -1 if custom, 0-3 if preset
        self.editing = False
        self._update_selection()

        # Hex color text input
        self.hex_input = CustomTextInput(
            self,
            value=self.current_color,
            placeholder="#000000",
            multiline=False,
            size=(-1, 28)
        )
        self.hex_input.Bind(wx.EVT_TEXT_ENTER, self.on_hex_enter)
        self.hex_input.Bind(wx.EVT_KILL_FOCUS, self.on_hex_focus_lost)
        self.hex_input.Bind(wx.EVT_TEXT, self.on_hex_change)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        bind_mouse_events(
            self,
            hover_handler=self.on_mouse_move,  # motion serves as hover update
            click_handler=self.on_click,
            leave_handler=self.on_leave
        )

        # Fixed size based on design
        self.SetMinSize((340, 64))

        # Initial layout
        self._layout_input()

        # Keep hex input positioned on resize
        self.Bind(wx.EVT_SIZE, self._on_size)

    def _on_size(self, event):
        """Reposition hex input when parent resizes."""
        self._layout_input()
        event.Skip()

    def _update_selection(self):
        self.selection = -1
        for i, (hex_val, _) in enumerate(self.PRESETS):
            if hex_val.upper() == self.current_color:
                self.selection = i
                break

    def SetColor(self, hex_color):
        self.current_color = hex_color.upper()
        self._update_selection()
        if hasattr(self, 'hex_input'):
            self.hex_input.SetValue(self.current_color)
        self.Refresh()

    def _layout_input(self):
        """Position the hex input widget."""
        if not hasattr(self, 'hex_input'):
            return
        rects = self._get_rects()
        r_hex = rects['hex']
        self.hex_input.SetSize(r_hex.width, r_hex.height)
        self.hex_input.SetPosition((r_hex.x, r_hex.y))

    def on_hex_enter(self, event):
        """User pressed Enter in hex input."""
        self._apply_hex_color()

    def on_hex_change(self, event):
        """Hex input text changed - optionally validate format."""
        # Could add live validation here
        pass

    def _apply_hex_color(self):
        """Apply the current hex input value as the color."""
        hex_val = self.hex_input.GetValue().strip()
        if not hex_val.startswith('#'):
            hex_val = f"#{hex_val}"
        # Validate hex format
        if len(hex_val) == 7 and all(c in '0123456789ABCDEFabcdef' for c in hex_val[1:]):
            hex_val = hex_val.upper()
            if hex_val != self.current_color:
                self.current_color = hex_val
                self._update_selection()
                self.Refresh()
                # Emit change event
                evt = wx.PyCommandEvent(wx.EVT_COLOURPICKER_CHANGED.typeId, self.GetId())
                evt.SetString(hex_val)
                self.GetEventHandler().ProcessEvent(evt)
        else:
            # Reset to current valid color on invalid input
            self.hex_input.SetValue(self.current_color)

    def on_hex_focus_lost(self, event):
        """Apply color when hex input loses focus."""
        self._apply_hex_color()
        event.Skip()

    def _get_rects(self):
        """Pre-calculate rectangles for hit detection and painting"""
        w, h = self.GetSize()
        rects = {}
        
        x_cursor = 12
        swatch_size = 28
        gap = 10 # Increased gap
        
        # Presets
        for i in range(len(self.PRESETS)):
            rects[f'preset_{i}'] = wx.Rect(x_cursor, 10, swatch_size, swatch_size)
            x_cursor += swatch_size + gap
            
        # Divider position
        rects['divider'] = x_cursor
        x_cursor += gap
        
        # Custom Swatch
        rects['custom'] = wx.Rect(x_cursor, 10, swatch_size, swatch_size)
        x_cursor += swatch_size + gap + 4
        
        # Hex Input
        input_w = 100
        input_h = 28
        rects['hex'] = wx.Rect(x_cursor, (h - input_h) // 2, input_w, input_h)
        
        return rects

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        w, h = self.GetSize()
        enabled = self.IsEnabled()
        rects = self._get_rects()

        # 1. Background (No Border)
        bg = _theme.disabled(_theme.color("colors.bg.panel")) if not enabled else _theme.color("colors.bg.panel")
        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, w, h, 4)

        # 2. Draw Presets
        for i, (hex_val, label) in enumerate(self.PRESETS):
            r = rects[f'preset_{i}']
            self._draw_swatch(gc, r.x, r.y, hex_val, label, i == self.selection, i == self.hover_idx, enabled)

        # 3. Divider
        border = _theme.disabled(self.BORDER_COLOR) if not enabled else self.BORDER_COLOR
        gc.SetPen(wx.Pen(border, 1))
        div_x = rects['divider']
        gc.StrokeLine(div_x, 10, div_x, h - 10)

        # 4. Custom Swatch
        is_custom = self.selection == -1
        r_cust = rects['custom']
        self._draw_swatch(gc, r_cust.x, r_cust.y, self.current_color, "CUSTOM", is_custom, self.hover_idx == 4, enabled)

        # 5. Hex Input Background (the CustomTextInput draws the actual text)
        r_hex = rects['hex']
        hex_bg = _theme.disabled(self.BG_INPUT) if not enabled else self.BG_INPUT
        gc.SetBrush(wx.Brush(hex_bg))
        hex_border = _theme.disabled(self.BORDER_COLOR) if not enabled else self.BORDER_COLOR
        gc.SetPen(wx.Pen(hex_border, 1))
        gc.DrawRoundedRectangle(r_hex.x, r_hex.y, r_hex.width, r_hex.height, 4)

    def _draw_swatch(self, gc, x, y, color_hex, label, is_selected, is_hovered, enabled):
        swatch_size = 28

        # Color Box - apply disabled to actual color
        swatch_color = wx.Colour(color_hex)
        swatch_color_disabled = _theme.disabled(swatch_color) if not enabled else swatch_color
        gc.SetBrush(wx.Brush(swatch_color_disabled))

        stroke_color = _theme.color("colors.border.default")
        thickness = 1
        if is_selected:
            stroke_color = _theme.color("colors.accent.primary")
            thickness = 2
        elif is_hovered:
            stroke_color = _theme.HOVER_HIGHLIGHT
        stroke_color_disabled = _theme.disabled(stroke_color) if not enabled else stroke_color
        gc.SetPen(wx.Pen(stroke_color_disabled, thickness))
        gc.DrawRoundedRectangle(x, y, swatch_size, swatch_size, 4)

        # Label
        label_font = TextStyles.label_xs.create_font()
        text_color = _theme.disabled(_theme.color("colors.text.muted")) if not enabled else _theme.color("colors.text.muted")
        gc.SetFont(label_font, text_color)
        tw, th = gc.GetTextExtent(label)
        gc.DrawText(label, x + (swatch_size - tw) / 2, y + swatch_size + 4)

    def on_mouse_move(self, event):
        if not self.IsEnabled(): return
        pos = event.GetPosition()
        rects = self._get_rects()
        
        new_hover = -1
        for i in range(len(self.PRESETS)):
            if rects[f'preset_{i}'].Contains(pos):
                new_hover = i
                break
        
        if new_hover == -1 and rects['custom'].Contains(pos):
            new_hover = 4
            
        if self.hover_idx != new_hover:
            self.hover_idx = new_hover
            self.Refresh()

    def on_click(self, event):
        if not self.IsEnabled(): return
        pos = event.GetPosition()
        rects = self._get_rects()
        
        clicked_idx = -1
        for i in range(len(self.PRESETS)):
            if rects[f'preset_{i}'].Contains(pos):
                clicked_idx = i
                break
        
        if clicked_idx == -1 and rects['custom'].Contains(pos):
            clicked_idx = 4

        if clicked_idx == -1: return
        
        if clicked_idx < 4:
            # Preset selected
            new_color = self.PRESETS[clicked_idx][0]
            if new_color != self.current_color:
                self.current_color = new_color
                self.selection = clicked_idx
                self.Refresh()
                # Emit color picker changed event
                evt = wx.PyCommandEvent(wx.EVT_COLOURPICKER_CHANGED.typeId, self.GetId())
                evt.SetString(new_color)
                self.GetEventHandler().ProcessEvent(evt)
        else:
            # Custom clicked - show dialog
            curr_color = wx.Colour(self.current_color)
            data = wx.ColorData()
            data.SetColor(curr_color)
            dlg = wx.ColorDialog(self, data)
            if dlg.ShowModal() == wx.ID_OK:
                new_color_obj = dlg.GetColorData().GetColor()
                new_hex = "#%02X%02X%02X" % (new_color_obj.Red(), new_color_obj.Green(), new_color_obj.Blue())
                self.current_color = new_hex
                self._update_selection()
                self.Refresh()
                # Emit color picker changed event
                evt = wx.PyCommandEvent(wx.EVT_COLOURPICKER_CHANGED.typeId, self.GetId())
                evt.SetString(new_hex)
                self.GetEventHandler().ProcessEvent(evt)
            dlg.Destroy()

    def on_leave(self, event):
        self.hover_idx = -1
        self.Refresh()


class PathInputControl(wx.Panel):
    """
    Styled path display with folder icon and project chip support
    """
    BG_COLOR = _theme.color("colors.bg.input")
    TEXT_COLOR = _theme.color("colors.text.secondary")
    # BORDER_DEFAULT inlined in on_paint

    def __init__(self, parent, size=(-1, 36)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.path_text = ""
        self.show_chip = False
        
        self.chip = ProjectFolderChip(self)
        self.chip.Hide()
        
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        self.update_chip_pos()
        event.Skip()

    def update_chip_pos(self):
        # Position chip after the icon
        self.chip.Move(wx.Point(36, (self.GetSize().y - 18) / 2))

    def SetPath(self, path, in_project=False):
        self.path_text = path
        self.show_chip = in_project
        if self.show_chip: self.chip.Show()
        else: self.chip.Hide()
        self.Refresh()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        w, h = self.GetSize()
        enabled = self.IsEnabled()

        # Background
        bg = _theme.disabled(_theme.color("colors.bg.input")) if not enabled else _theme.color("colors.bg.input")
        gc.SetBrush(wx.Brush(bg))
        border = _theme.disabled(_theme.color("colors.border.default")) if not enabled else _theme.color("colors.border.default")
        gc.SetPen(wx.Pen(border, 1))
        gc.DrawRoundedRectangle(1, 1, w - 2, h - 2, 4)

        # Folder Icon
        icon_font = TextStyles.icon.create_font()
        text_color = _theme.disabled(self.TEXT_COLOR) if not enabled else self.TEXT_COLOR
        gc.SetFont(icon_font, text_color)
        # mdi-folder: F024B
        itw, ih = gc.GetTextExtent('\U000F024B')
        gc.DrawText('\U000F024B', 12, (h - ih) / 2)

        # Path Text
        font = TextStyles.body.create_font()
        gc.SetFont(font, text_color)

        text_x = 36
        if self.show_chip:
            text_x += self.chip.GetSize().x + 6

        # Truncate text if too long
        tw, th = gc.GetTextExtent(self.path_text)
        display_text = self.path_text
        if text_x + tw > w - 12:
            # Simple truncation for now
            display_text = "..." + self.path_text[-25:]

        gc.DrawText(display_text, text_x, (h - th) / 2)

    def AcceptsFocus(self):
        return False

    def AcceptsFocusFromKeyboard(self):
        return False
