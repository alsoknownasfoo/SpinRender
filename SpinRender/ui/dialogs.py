"""
SpinRender UI Dialogs
Implements modal dialogs from Pencil design
"""
import wx
import os
import webbrowser
import threading
from .custom_controls import CustomButton, CustomTextInput
from .text_styles import TextStyle, TextStyles
from . import theme
from foundation.fonts import JETBRAINS_MONO, MDI_FONT_FAMILY, INTER
from foundation.icons import STATUS_ICONS


ID_RESET = 10001

class BaseStyledDialog(wx.Dialog):
    """
    Base class for chromeless, styled dialogs with dragging support and drop shadow
    """
    SHADOW_SIZE = 16
    # Colors sourced from theme module

    def __init__(self, parent, title, size):
        # Expand size to account for shadow padding
        actual_size = wx.Size(size[0] + self.SHADOW_SIZE * 2, size[1] + self.SHADOW_SIZE * 2)
        
        super().__init__(
            parent,
            title=title,
            size=actual_size,
            style=wx.FRAME_NO_TASKBAR | wx.BORDER_NONE | wx.STAY_ON_TOP
        )
        
        # Transparent background for shadow bleed
        if wx.Platform == '__WXMSW__':
            self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        else:
            self.SetBackgroundColour(theme.TRANSPARENT)
            self.SetCanFocus(True)
            
        self.logical_size = size
        self.drag_pos = None
        
        # Layout container for the actual content (offset by shadow)
        self.main_container = wx.Panel(self, pos=(self.SHADOW_SIZE, self.SHADOW_SIZE), size=size)
        self.main_container.SetBackgroundColour(theme.BG_MODAL)
        
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char_hook)
        self.Bind(wx.EVT_PAINT, self.on_paint_window)

    def on_paint_window(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        
        w, h = self.GetSize()
        s = self.SHADOW_SIZE
        
        # 1. Draw Shadow (Fading black)
        for i in range(s):
            # Doubled base alpha (from 80 to 160) for much darker shadow
            alpha = int(160 * (1.0 - (i / s)**0.5))
            gc.SetBrush(wx.Brush(wx.Colour(theme.BLACK.Red(), theme.BLACK.Green(), theme.BLACK.Blue(), alpha)))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRoundedRectangle(i, i, w - 2*i, h - 2*i, 12)
            
        # 2. Draw actual modal background (no border)
        gc.SetBrush(wx.Brush(theme.BG_MODAL))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(s, s, self.logical_size[0], self.logical_size[1], 4)

    def on_char_hook(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    def create_header(self, title_text):
        header = wx.Panel(self.main_container, size=(-1, 48))
        header.SetBackgroundColour(theme.BG_MODAL)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.header_title = wx.StaticText(header, label=title_text)
        self.header_title.SetForegroundColour(theme.ACCENT_YELLOW if "SETUP" in title_text else theme.TEXT_PRIMARY)
        self.header_title.SetFont(TextStyle(family=theme.FONT_MONO, size=13, weight=600).create_font())
        
        header_sizer.Add(self.header_title, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)
        
        # Add standard close button to all headers
        header_sizer.AddStretchSpacer()
        close_btn = CustomButton(header, label="", icon="mdi-close", primary=False, ghost=True, icon_color=theme.TEXT_MUTED, size=(32, 32))
        close_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        header_sizer.Add(close_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        header.SetSizer(header_sizer)

        # Dragging support (needs to move the dialog, not just the header)
        header.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        header.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        header.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.header_title.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.header_title.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.header_title.Bind(wx.EVT_MOTION, self.on_mouse_motion)

        return header

    def on_left_down(self, event):
        win = event.GetEventObject()
        win.CaptureMouse()
        x, y = win.ClientToScreen(event.GetPosition())
        origin_x, origin_y = self.GetPosition()
        self.drag_pos = wx.Point(x - origin_x, y - origin_y)

    def on_left_up(self, event):
        win = event.GetEventObject()
        if win.HasCapture():
            win.ReleaseMouse()

    def on_mouse_motion(self, event):
        if event.Dragging() and event.LeftIsDown() and self.drag_pos:
            win = event.GetEventObject()
            x, y = win.ClientToScreen(event.GetPosition())
            new_pos = wx.Point(x - self.drag_pos.x, y - self.drag_pos.y)
            self.Move(new_pos)


class AdvancedOptionsDialog(BaseStyledDialog):
    """
    Advanced Options modal dialog
    Follows Pencil design: Modal/AdvancedOptions
    """
    PLACEHOLDER_TEXT = ".e.g. --color-theme=theme"
    # All colors use theme.*

    def __init__(self, parent, settings, board_path):
        super().__init__(parent, "Advanced Options", (480, 560))
        self.settings = settings
        self.board_path = board_path
        self.board_dir = os.path.dirname(board_path)
        self.build_ui()
        self.Centre()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        main_sizer.Add(self.create_header("ADVANCED OPTIONS"), 0, wx.EXPAND)

        # Border separator
        line = wx.Panel(self.main_container, size=(-1, 1))
        line.SetBackgroundColour(theme.BORDER_MODAL)
        main_sizer.Add(line, 0, wx.EXPAND)

        # Content
        content = wx.Panel(self.main_container)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 1. OUTPUT PATH section
        content_sizer.Add(self.create_section_label(content, "OUTPUT PATH"), 0, wx.EXPAND | wx.BOTTOM, 12)

        # Auto Row
        auto_row = wx.Panel(content)
        auto_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        auto_desc = wx.StaticText(auto_row, label="Automatically save to time-stamped directories.")
        auto_desc.SetForegroundColour(theme.TEXT_MUTED)
        auto_desc.SetFont(TextStyle(family=theme.FONT_MONO, size=9, weight=400).create_font())
        auto_sizer.Add(auto_desc, 1, wx.ALIGN_CENTER_VERTICAL)
        
        from .custom_controls import CustomToggleButton
        self.auto_toggle = CustomToggleButton(auto_row, size=(100, 28))
        self.auto_toggle.SetValue(self.settings.output_auto)
        self.auto_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_auto_toggle)
        auto_sizer.Add(self.auto_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        
        auto_row.SetSizer(auto_sizer)
        content_sizer.Add(auto_row, 0, wx.EXPAND | wx.BOTTOM, 16)

        # Path Input Row
        path_input_row = wx.Panel(content)
        path_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        from .custom_controls import PathInputControl
        self.path_display = PathInputControl(path_input_row, size=(-1, 36))
        path_input_sizer.Add(self.path_display, 1, wx.RIGHT, 8)
        
        self.browse_btn = CustomButton(path_input_row, label="BROWSE", icon="mdi-folder", primary=False, size=(110, 36))
        self.browse_btn.Bind(wx.EVT_BUTTON, self.on_browse)
        path_input_sizer.Add(self.browse_btn, 0)
        
        path_input_row.SetSizer(path_input_sizer)
        content_sizer.Add(path_input_row, 0, wx.EXPAND | wx.BOTTOM, 20)

        # 2. PARAMETER OVERRIDES section
        content_sizer.Add(self.create_section_label(content, "PARAMETER OVERRIDES"), 0, wx.EXPAND | wx.BOTTOM, 12)
        
        self.override_input = CustomTextInput(
            content,
            value=getattr(self.settings, 'cli_overrides', ''),
            placeholder=self.PLACEHOLDER_TEXT,
            multiline=True,
            size=(-1, 80)
        )
        content_sizer.Add(self.override_input, 0, wx.EXPAND | wx.BOTTOM, 8)
        
        # Helper link simulation
        link_row = wx.Panel(content)
        link_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        info_icon = wx.StaticText(link_row, label='\U000F02FD') # mdi-information-outline
        info_icon.SetForegroundColour(theme.TEXT_MUTED)
        info_icon.SetFont(TextStyles.icon.create_font())
        info_icon.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        link_sizer.Add(info_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        see_txt = wx.StaticText(link_row, label="See ")
        see_txt.SetForegroundColour(theme.TEXT_MUTED); see_txt.SetFont(TextStyle(family=theme.FONT_MONO, size=9, weight=400).create_font())
        link_sizer.Add(see_txt, 0, wx.ALIGN_CENTER_VERTICAL)
        
        link_txt = wx.StaticText(link_row, label="kicad-cli render options")
        link_txt.SetForegroundColour(theme.ACCENT_CYAN); link_txt.SetFont(TextStyle(family=theme.FONT_MONO, size=9, weight=400).create_font())
        link_txt.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        link_sizer.Add(link_txt, 0, wx.ALIGN_CENTER_VERTICAL)
        
        url = "https://docs.kicad.org/master/en/cli/cli.html#pcb_render"
        info_icon.Bind(wx.EVT_LEFT_DOWN, lambda e: webbrowser.open(url))
        link_txt.Bind(wx.EVT_LEFT_DOWN, lambda e: webbrowser.open(url))
        
        link_row.SetSizer(link_sizer)
        content_sizer.Add(link_row, 0, wx.EXPAND | wx.BOTTOM, 24)

        # 3. LOGGING section
        content_sizer.Add(self.create_section_label(content, "SYSTEM LOGGING"), 0, wx.EXPAND | wx.BOTTOM, 12)
        
        log_row = wx.Panel(content)
        log_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.log_opts = [
            {'id': 'off', 'label': 'OFF'},
            {'id': 'simple', 'label': 'SIMPLE'},
            {'id': 'verbose', 'label': 'VERBOSE'}
        ]
        self.log_toggle = CustomToggleButton(log_row, options=self.log_opts, size=(240, 28))
        curr_lvl = getattr(self.settings, 'logging_level', 'simple')
        lvl_idx = next((i for i, o in enumerate(self.log_opts) if o['id'] == curr_lvl), 1)
        self.log_toggle.SetSelection(lvl_idx)
        log_hsizer.Add(self.log_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        
        log_row.SetSizer(log_hsizer)
        content_sizer.Add(log_row, 0, wx.EXPAND | wx.BOTTOM, 12)
        
        log_info = wx.StaticText(content, label="Logs are kept for 30 days. Useful for troubleshooting render failures.")
        log_info.SetForegroundColour(theme.TEXT_MUTED)
        log_info.SetFont(TextStyle(family=theme.FONT_MONO, size=8, weight=400).create_font())
        content_sizer.Add(log_info, 0, wx.EXPAND | wx.BOTTOM, 8)

        from utils.logger import SpinLogger
        open_logs_txt = wx.StaticText(content, label="OPEN LOGS FOLDER")
        open_logs_txt.SetForegroundColour(theme.ACCENT_CYAN)
        open_logs_txt.SetFont(TextStyle(family=theme.FONT_MONO, size=9, weight=700).create_font())
        open_logs_txt.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        open_logs_txt.Bind(wx.EVT_LEFT_DOWN, lambda e: SpinLogger.open_logs_folder())
        content_sizer.Add(open_logs_txt, 0, wx.BOTTOM, 12)

        content.SetSizer(content_sizer)
        main_sizer.Add(content, 1, wx.EXPAND | wx.ALL, 24)

        # Footer
        footer = wx.Panel(self.main_container, size=(-1, 60))
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)

        cancel_btn = CustomButton(footer, label="CANCEL", icon="mdi-close", primary=False, size=(120, 36))
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)

        ok_btn = CustomButton(footer, label="OK", icon="mdi-check", primary=True, size=(120, 36))
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        footer_sizer.AddStretchSpacer()
        footer_sizer.Add(cancel_btn, 0, wx.RIGHT, 12)
        footer_sizer.Add(ok_btn, 0, wx.RIGHT, 16)

        footer.SetSizer(footer_sizer)
        main_sizer.Add(footer, 0, wx.EXPAND | wx.BOTTOM, 16)

        self.main_container.SetSizer(main_sizer)
        self.update_path_display()

    def create_section_label(self, parent, text):
        lbl = wx.StaticText(parent, label=text)
        lbl.SetForegroundColour(theme.TEXT_PRIMARY)
        lbl.SetFont(TextStyle(family=theme.FONT_MONO, size=10, weight=600).create_font())
        return lbl

    def update_path_display(self):
        auto = self.auto_toggle.GetValue()
        self.browse_btn.Enable(not auto)
        
        if auto:
            self.path_display.SetPath("/Renders/[YYMMDD_HHMMSS]..", in_project=True)
            self.path_display.Enable(False)
        else:
            self.path_display.Enable(True)
            path = getattr(self.settings, 'output_path', '')
            if not path:
                ext = getattr(self.settings, 'format', 'mp4')
                self.path_display.SetPath(f"/Renders/Untitled.{ext}", in_project=True)
            else:
                try:
                    rel = os.path.relpath(path, self.board_dir)
                    if not rel.startswith('..'):
                        self.path_display.SetPath(f"/{rel}", in_project=True)
                    else:
                        self.path_display.SetPath(path, in_project=False)
                except ValueError:
                    self.path_display.SetPath(path, in_project=False)

    def on_auto_toggle(self, event):
        self.update_path_display()

    def on_browse(self, event):
        start_dir = os.path.join(self.board_dir, "Renders")
        if not os.path.exists(start_dir): os.makedirs(start_dir, exist_ok=True)
        dlg = wx.DirDialog(self, "Select Output Directory", defaultPath=start_dir)
        if dlg.ShowModal() == wx.ID_OK:
            self.settings.output_path = dlg.GetPath()
            self.update_path_display()
        dlg.Destroy()

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_ok(self, event):
        self.settings.cli_overrides = self.override_input.GetValue()
        self.settings.output_auto = self.auto_toggle.GetValue()
        self.settings.logging_level = self.log_opts[self.log_toggle.GetSelection()]['id']
        self.EndModal(wx.ID_OK)


class SavePresetDialog(BaseStyledDialog):
    """
    Save Preset dialog
    Follows Pencil design: Modal/SavePreset
    """
    # All colors use theme module - no class-level color constants

    def __init__(self, parent, board_path):
        super().__init__(parent, "Save Preset", (400, 260))
        self.board_path = board_path
        self.preset_name = ""
        self.build_ui()
        self.Centre()

    def build_ui(self):
        from core.presets import PresetManager
        self.manager = PresetManager(self.board_path)
        self.existing_names = [n.upper() for s, n in self.manager.list_presets()]

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.create_header("SAVE PRESET"), 0, wx.EXPAND)
        line = wx.Panel(self.main_container, size=(-1, 1)); line.SetBackgroundColour(theme.BORDER_MODAL)
        main_sizer.Add(line, 0, wx.EXPAND)

        content = wx.Panel(self.main_container)
        content_sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(content, label="PRESET NAME")
        label.SetForegroundColour(theme.TEXT_SECONDARY)
        label.SetFont(TextStyle(family=theme.FONT_MONO, size=10, weight=700).create_font())
        content_sizer.Add(label, 0, wx.LEFT | wx.TOP, 24)

        self.name_input = CustomTextInput(content, size=(-1, 36))
        self.name_input.Bind(wx.EVT_TEXT_ENTER, self.on_save)
        self.name_input.Bind(wx.EVT_TEXT, self.on_text_change)
        content_sizer.Add(self.name_input, 0, wx.EXPAND | wx.ALL, 24)

        content.SetSizer(content_sizer)
        main_sizer.Add(content, 1, wx.EXPAND)

        footer = wx.Panel(self.main_container, size=(-1, 60))
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cancel_btn = CustomButton(footer, label="CANCEL", icon="mdi-close", primary=False, size=(110, 36))
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.save_btn = CustomButton(footer, label="SAVE", icon="mdi-check", primary=True, size=(110, 36))
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        footer_sizer.AddStretchSpacer(); footer_sizer.Add(cancel_btn, 0, wx.RIGHT, 12); footer_sizer.Add(self.save_btn, 0, wx.RIGHT, 16)
        footer.SetSizer(footer_sizer)
        main_sizer.Add(footer, 0, wx.EXPAND | wx.BOTTOM, 16)

        self.main_container.SetSizer(main_sizer)

    def on_cancel(self, event): self.EndModal(wx.ID_CANCEL)
    def on_save(self, event): self.EndModal(wx.ID_OK)
    def on_text_change(self, event):
        val = self.name_input.GetValue().upper(); is_overwrite = val in self.existing_names
        if is_overwrite:
            self.save_btn.SetLabel("OVERWRITE"); self.save_btn.SetIcon("mdi-alert-octagram"); self.save_btn.SetDanger(True)
        else:
            self.save_btn.SetLabel("SAVE"); self.save_btn.SetIcon("mdi-check"); self.save_btn.SetDanger(False)
    def GetPresetName(self): return self.name_input.GetValue()


class RecallPresetDialog(BaseStyledDialog):
    """
    Recall Preset dialog
    Follows Pencil design: Modal/PresetList
    """
    # All colors use theme module

    def __init__(self, parent, board_path):
        super().__init__(parent, "SELECT CUSTOM PRESET", (400, 400))
        self.board_path = board_path
        self.selected_preset = self.selected_name = None
        self.build_ui()
        self.Centre()

    def build_ui(self):
        from core.presets import PresetManager
        self.manager = PresetManager(self.board_path); presets = self.manager.list_presets()
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        header = self.create_header("SELECT CUSTOM PRESET")
        main_sizer.Add(header, 0, wx.EXPAND)
        line = wx.Panel(self.main_container, size=(-1, 1)); line.SetBackgroundColour(theme.BORDER_MODAL)
        main_sizer.Add(line, 0, wx.EXPAND)

        import wx.lib.scrolledpanel as scrolled
        list_panel = scrolled.ScrolledPanel(self.main_container)
        list_panel.SetBackgroundColour(theme.BG_MODAL); list_panel.SetupScrolling(scroll_x=False, scroll_y=True)
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        if not presets:
            empty_text = wx.StaticText(list_panel, label="No saved presets found."); empty_text.SetForegroundColour(theme.TEXT_MUTED)
            empty_text.SetFont(TextStyle(family=theme.FONT_MONO, size=11, weight=400, formatting="italic").create_font()); list_sizer.Add(empty_text, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 40)
        else:
            for scope, name in presets:
                item = self.create_preset_item(list_panel, scope, name)
                list_sizer.Add(item, 0, wx.EXPAND | wx.BOTTOM, 8)
        list_panel.SetSizer(list_sizer); main_sizer.Add(list_panel, 1, wx.EXPAND | wx.ALL, 16)
        self.main_container.SetSizer(main_sizer)

    def create_preset_item(self, parent, scope, name):
        panel = wx.Panel(parent, size=(-1, 40)); panel.SetBackgroundColour(theme.BG_SURFACE); panel.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        sizer = wx.BoxSizer(wx.HORIZONTAL); label = wx.StaticText(panel, label=name.upper()); label.SetForegroundColour(theme.TEXT_PRIMARY)
        label.SetFont(TextStyles.body.create_font()); sizer.Add(label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)
        action_area = wx.Panel(panel); action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        trash_btn = wx.StaticText(action_area, label='\U000F0A7A'); trash_btn.SetForegroundColour(theme.ACCENT_ORANGE)
        trash_btn.SetFont(TextStyles.icon.create_font()); trash_btn.SetCursor(wx.Cursor(wx.CURSOR_HAND)); action_sizer.Add(trash_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        cancel_icon = wx.StaticText(action_area, label='\U000F0156'); cancel_icon.SetForegroundColour(theme.ACCENT_ORANGE)
        cancel_icon.SetFont(TextStyles.icon.create_font()); cancel_icon.Hide(); confirm_icon = wx.StaticText(action_area, label='\U000F012C')
        confirm_icon.SetForegroundColour(theme.ACCENT_GREEN); confirm_icon.SetFont(TextStyles.icon.create_font()); confirm_icon.Hide()
        action_area.SetSizer(action_sizer); sizer.Add(action_area, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12); panel.SetSizer(sizer)
        def show_confirm(e):
            trash_btn.Hide(); action_sizer.Clear(); action_sizer.Add(cancel_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
            action_sizer.Add(confirm_icon, 0, wx.ALIGN_CENTER_VERTICAL); cancel_icon.Show(); confirm_icon.Show(); action_area.Layout(); panel.Layout()
        def hide_confirm(e):
            cancel_icon.Hide(); confirm_icon.Hide(); action_sizer.Clear(); action_sizer.Add(trash_btn, 0, wx.ALIGN_CENTER_VERTICAL)
            trash_btn.Show(); action_area.Layout(); panel.Layout()
        panel.Bind(wx.EVT_LEFT_DOWN, lambda e: self.on_select(name, scope)); label.Bind(wx.EVT_LEFT_DOWN, lambda e: self.on_select(name, scope))
        trash_btn.Bind(wx.EVT_LEFT_DOWN, show_confirm); cancel_icon.Bind(wx.EVT_LEFT_DOWN, hide_confirm)
        confirm_icon.Bind(wx.EVT_LEFT_DOWN, lambda e: self.perform_delete(name, scope)); return panel

    def perform_delete(self, name, scope):
        if self.manager.delete_preset(name, is_global=(scope=='global')): self.EndModal(ID_RESET)
    def on_select(self, name, scope):
        self.selected_preset = self.manager.load_preset(name, is_global=(scope=='global'))
        if self.selected_preset: self.selected_name = name; self.EndModal(wx.ID_OK)
    def on_cancel(self, event): self.EndModal(wx.ID_CANCEL)
    def GetSelectedSettings(self): return self.selected_preset
    def GetSelectedName(self): return self.selected_name
class RoundedPanel(wx.Panel):
    """Panel with rounded corners"""
    def __init__(self, parent, radius=4, bg_color=None):
        super().__init__(parent)
        self.radius = radius
        self.bg_color = bg_color or theme.BG_INPUT
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return
        w, h = self.GetSize()
        gc.SetBrush(wx.Brush(self.bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, w, h, self.radius)


class DependencyCheckDialog(wx.Dialog):
    """
    Dialog for dependency checking and installation
    Follows High-Density aesthetic from Res/SpinRender.pen
    """

    def __init__(self, parent, dep_status, checker):
        super().__init__(
            parent,
            title="SpinRender - Setup Required",
            size=(500, 650),
            style=wx.FRAME_NO_TASKBAR | wx.BORDER_NONE | wx.STAY_ON_TOP
        )

        self.dep_status = dep_status
        self.checker = checker

        # Design system colors - migrated to theme module
        self.bg_color = theme.BG_MODAL  # Dark gray modal background
        self.bg_input = theme.BG_INPUT
        self.text_primary = theme.TEXT_PRIMARY
        self.text_secondary = theme.TEXT_SECONDARY
        self.accent_yellow = theme.ACCENT_YELLOW
        self.accent_green = theme.ACCENT_GREEN
        self.accent_orange = theme.ACCENT_ORANGE
        self.accent_cyan = theme.ACCENT_CYAN
        self.border_default = theme.BORDER_DEFAULT

        self.SetBackgroundColour(self.bg_color)
        
        # UI state
        self.current_dep_index = 0
        self.num_deps = 0
        
        # simulated progress timer
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

        self.build_ui()
        self.Centre()

        # Dragging support - Bind specifically to header components
        self.header.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.header.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.header.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        
        self.header_title.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.header_title.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.header_title.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        
        self.drag_pos = None

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header (Drag handle)
        self.header = wx.Panel(self, size=(-1, 48))
        self.header.SetBackgroundColour(self.bg_color)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.header_title = wx.StaticText(self.header, label="SETUP REQUIRED")
        self.header_title.SetForegroundColour(theme.TEXT_PRIMARY)  # White title
        self.header_title.SetFont(TextStyles.section_heading.create_font())
        
        header_sizer.Add(self.header_title, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)
        self.header.SetSizer(header_sizer)
        main_sizer.Add(self.header, 0, wx.EXPAND)

        # Border separator
        line = wx.Panel(self, size=(-1, 1))
        line.SetBackgroundColour(self.border_default)
        main_sizer.Add(line, 0, wx.EXPAND)

        # Content Panel
        content = wx.Panel(self)
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        
        msg = wx.StaticText(content, label="SpinRender requires the following dependencies to function:")
        msg.SetForegroundColour(self.text_secondary)
        msg.SetFont(TextStyles.body.create_font())
        self.content_sizer.Add(msg, 0, wx.ALL, 16)

        # List existing dependencies
        for dep_name, is_found in self.dep_status.items():
            dep_panel = RoundedPanel(content, radius=4, bg_color=self.bg_input)
            dep_sizer = wx.BoxSizer(wx.VERTICAL)
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)

            dep_label = wx.StaticText(dep_panel, label=dep_name)
            dep_label.SetForegroundColour(self.text_primary)
            dep_label.SetFont(TextStyle(family=theme.FONT_MONO, size=10, weight=400).create_font())

            # Use bundled MDI symbols (required)
            status_symbol = "mdi-check-circle" if is_found else "mdi-close"  # Red X for missing
            status_color = self.accent_green if is_found else theme.ACCENT_RED
            
            # Get icon from foundation icons
            icon_char = STATUS_ICONS.get(status_symbol, "")
            
            status_label = wx.StaticText(dep_panel, label=icon_char)
            status_label.SetForegroundColour(status_color)
            status_label.SetFont(TextStyles.icon_lg.create_font())

            row_sizer.Add(dep_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)
            row_sizer.Add(status_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
            # Increase vertical height/whitespace
            dep_sizer.Add(row_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 12)

            dep_panel.SetSizer(dep_sizer)
            # Horizontal padding matching list items
            self.content_sizer.Add(dep_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)

        # Spacing between list and progress panel - double the item spacing
        self.content_sizer.AddSpacer(16)

        # Integrated Progress Area
        self.progress_panel = wx.Panel(content)
        self.progress_panel.Hide()
        progress_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.progress_gauge = wx.Gauge(self.progress_panel, range=100, size=(-1, 4))
        self.progress_gauge.SetBackgroundColour(self.bg_input)
        self.progress_gauge.SetForegroundColour(self.accent_cyan)
        progress_sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.BOTTOM, 8)
        
        self.progress_status = wx.StaticText(self.progress_panel, label="Initializing...")
        self.progress_status.SetForegroundColour(self.text_primary)
        self.progress_status.SetFont(TextStyle(family=theme.FONT_INTER, size=10, weight=700).create_font())
        progress_sizer.Add(self.progress_status, 0, wx.EXPAND | wx.BOTTOM, 8)
        
        self.progress_log = wx.TextCtrl(
            self.progress_panel, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.NO_BORDER | wx.TE_RICH
        )
        self.progress_log.SetBackgroundColour(self.bg_input)
        self.progress_log.SetForegroundColour(self.text_secondary)
        self.progress_log.SetFont(TextStyles.label_xs.create_font())
        progress_sizer.Add(self.progress_log, 1, wx.EXPAND)
        
        self.progress_panel.SetSizer(progress_sizer)
        # Match list item padding: 24px horizontal, 8px bottom spacing
        self.content_sizer.Add(self.progress_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)

        content.SetSizer(self.content_sizer)
        main_sizer.Add(content, 1, wx.EXPAND)

        # Footer with custom buttons
        footer = wx.Panel(self)
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Secondary Button (Close)
        self.close_btn = CustomButton(footer, label="EXIT", primary=False, danger=True, size=(90, 36))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        
        # Action Button (Install)
        self.install_btn = CustomButton(footer, label="INSTALL", primary=True, size=(150, 36))
        self.install_btn.Bind(wx.EVT_BUTTON, self.on_install)

        footer_sizer.AddStretchSpacer()
        footer_sizer.Add(self.close_btn, 0, wx.RIGHT, 12)
        footer_sizer.Add(self.install_btn, 0, wx.RIGHT, 16)

        footer.SetSizer(footer_sizer)
        main_sizer.Add(footer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 16)

        self.SetSizer(main_sizer)

    # Window Dragging Logic
    def on_left_down(self, event):
        win = event.GetEventObject()
        win.CaptureMouse()
        x, y = win.ClientToScreen(event.GetPosition())
        origin_x, origin_y = self.GetPosition()
        self.drag_pos = wx.Point(x - origin_x, y - origin_y)

    def on_left_up(self, event):
        win = event.GetEventObject()
        if win.HasCapture():
            win.ReleaseMouse()

    def on_mouse_motion(self, event):
        if event.Dragging() and event.LeftIsDown() and self.drag_pos:
            win = event.GetEventObject()
            x, y = win.ClientToScreen(event.GetPosition())
            new_pos = wx.Point(x - self.drag_pos.x, y - self.drag_pos.y)
            self.Move(new_pos)

    def on_timer(self, event):
        val = self.progress_gauge.GetValue()
        limit = (self.current_dep_index * 100) + 95
        if val < limit:
            self.progress_gauge.SetValue(val + 1)

    def on_close(self, event):
        """Close dialog"""
        self.EndModal(wx.ID_CANCEL)

    def on_install(self, event):
        if not self.checker.missing_deps:
            self.EndModal(wx.ID_OK)
            return

        # UI State: Disable buttons
        self.install_btn.Enable(False)
        self.close_btn.Enable(False)
        
        self.progress_panel.Show()
        self.progress_log.Clear()
        self.Layout()

        self.num_deps = len(self.checker.missing_deps)
        self.progress_gauge.SetRange(self.num_deps * 100)
        self.progress_gauge.SetValue(0)
        
        self.timer.Start(100)

        thread = threading.Thread(target=self._run_install_thread)
        thread.daemon = True
        thread.start()

    def _run_install_thread(self):
        num_deps = len(self.checker.missing_deps)
        for i, dep_name in enumerate(self.checker.missing_deps):
            self.current_dep_index = i
            is_last = (i == num_deps - 1)
            wx.CallAfter(self.progress_status.SetLabel, f"Installing {dep_name}...")
            
            def log_callback(message):
                wx.CallAfter(self._append_log, message)
                if is_last and "Successfully installed" in message:
                    wx.CallAfter(self.progress_gauge.SetValue, num_deps * 100)
                    wx.CallAfter(self.progress_status.SetLabel, "Installation complete.")

            self.checker.install_dependency(dep_name, callback=log_callback)
            wx.CallAfter(self.progress_gauge.SetValue, (i + 1) * 100)

        wx.CallAfter(self._on_install_finished)

    def _append_log(self, message):
        self.progress_log.AppendText(message + "\n")
        self.progress_log.ShowPosition(self.progress_log.GetLastPosition())

    def _on_install_finished(self):
        self.timer.Stop()
        self.progress_gauge.SetValue(self.num_deps * 100)
        
        self.dep_status = self.checker.check_all()
        if not self.checker.missing_deps:
            self.EndModal(wx.ID_OK)
        else:
            self.install_btn.Enable(True)
            self.close_btn.Enable(True)
            self.progress_status.SetLabel("Some installations failed.")
            self.Layout()
