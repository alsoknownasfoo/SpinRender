"""
SpinRender UI Dialogs
Implements modal dialogs from Pencil design
"""
import wx
import os
import glob as _glob
import webbrowser
import threading
from .custom_controls import (
    CustomButton, CustomInput, CustomListView, 
    EVT_LIST_ITEM_SELECTED, EVT_LIST_ITEM_DELETED
)
from .helpers import create_text
from SpinRender.core.theme import Theme
from SpinRender.core.locale import Locale
from SpinRender.foundation.fonts import JETBRAINS_MONO, MDI_FONT_FAMILY, INTER
from SpinRender.foundation.icons import STATUS_ICONS

_theme = Theme.current()
_locale = Locale.current()


ID_RESET = 10001

class BaseStyledDialog(wx.Dialog):
    """
    Base class for chromeless, styled dialogs with dragging support and drop shadow
    """
    # Colors sourced from theme module

    def __init__(self, parent, title, size):
        # Get shadow size from theme
        self.shadow_size = _theme._resolve("layout.dialogs.default.frame.shadow.size")
        if self.shadow_size is None:
            self.shadow_size = 16  # fallback
        # Ensure it's an integer (coerce from string if needed)
        if isinstance(self.shadow_size, str):
            try:
                self.shadow_size = int(self.shadow_size)
            except (ValueError, TypeError):
                self.shadow_size = 16

        # Expand size to account for shadow padding
        actual_size = wx.Size(size[0] + self.shadow_size * 2, size[1] + self.shadow_size * 2)
        
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
            self.SetBackgroundColour(_theme.TRANSPARENT)
            self.SetCanFocus(True)
            
        self.logical_size = size
        self.drag_pos = None
        
        # Layout container for the actual content (offset by shadow)
        self.main_container = wx.Panel(self, pos=(self.shadow_size, self.shadow_size), size=size)
        self.main_container.SetBackgroundColour(_theme.color("colors.gray-dark"))
        
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char_hook)
        self.Bind(wx.EVT_PAINT, self.on_paint_window)

    def on_paint_window(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        w, h = self.GetSize()
        s = self.shadow_size
        
        # 1. Draw Shadow (Fading black)
        for i in range(s):
            # Doubled base alpha (from 80 to 160) for much darker shadow
            alpha = int(160 * (1.0 - (i / s)**0.5))
            gc.SetBrush(wx.Brush(wx.Colour(_theme.BLACK.Red(), _theme.BLACK.Green(), _theme.BLACK.Blue(), alpha)))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRoundedRectangle(i, i, w - 2*i, h - 2*i, 12)
            
        # 2. Draw actual modal background (no border)
        gc.SetBrush(wx.Brush(_theme.color("colors.gray-dark")))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(s, s, self.logical_size[0], self.logical_size[1], 4)

    def on_char_hook(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    def create_header(self, title_text, show_close=True):
        header_height = _theme._resolve("layout.dialogs.default.header.height")
        if header_height is None:
            header_height = 48
        header = wx.Panel(self.main_container, size=(-1, header_height))
        header.SetBackgroundColour(_theme.color("colors.gray-dark"))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        _color_token = "colors.secondary" if "SETUP" in title_text else "colors.primary"
        self.header_title = create_text(header, title_text, "header", color_token=_color_token)
        
        header_sizer.Add(self.header_title, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)
        
        # Add standard close button if requested
        header_sizer.AddStretchSpacer()
        if show_close:
            close_btn = CustomButton(header, id="close", label="", size=(32, 32))
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


class FilenameEntryDialog(BaseStyledDialog):
    """
    Filename entry dialog for PNG sequence base name.
    Mirrors SavePresetDialog: text input with smart SAVE→OVERWRITE switching on keystroke.
    """

    def __init__(self, parent, chosen_dir, default_name):
        self.dialog_w = _theme._resolve("layout.dialogs.filename.frame.width") or 300
        h = _theme._resolve("layout.dialogs.filename.frame.height") or 220
        super().__init__(parent, "Enter base filename", (self.dialog_w, h))
        self.chosen_dir = chosen_dir
        self.build_ui()
        self.Centre()

        self.name_input.SetValue(default_name)
        wx.CallAfter(self.name_input.text_ctrl.SetFocus)
        wx.CallAfter(self.name_input.text_ctrl.SetSelection, 0, -1)

        self.on_text_change(None)

    def build_ui(self):
        padding_raw = _theme._resolve("layout.dialogs.filename.controls.padding") or 16
        padding = _theme._parse_padding(padding_raw)
        gap = _theme._resolve("layout.dialogs.filename.controls.gap") or 8

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.create_header("Enter base filename", show_close=False), 0, wx.EXPAND)

        line = wx.Panel(self.main_container, size=(-1, 1))
        line.SetBackgroundColour(_theme.color("borders.default.color"))
        main_sizer.Add(line, 0, wx.EXPAND)

        content = wx.Panel(self.main_container)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        self.name_input = CustomInput(content, size=(-1, 36), id="default")
        self.name_input.Bind(wx.EVT_TEXT_ENTER, self.on_save)
        self.name_input.Bind(wx.EVT_TEXT, self.on_text_change)
        content_sizer.Add(self.name_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding['left'])

        helper = create_text(
            content,
            _locale.get("dialog.filename.helper", "Frames are saved as name_00001.png, name_00002.png, \u2026"),
            "dialog_description",
            style=wx.ALIGN_CENTRE_HORIZONTAL
        )
        helper.Wrap(self.dialog_w - 2 * padding['left'])
        content_sizer.Add((0, gap))
        content_sizer.Add(helper, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding['left'])

        content.SetSizer(content_sizer)
        main_sizer.Add((0, 0), 1)  # stretch above
        main_sizer.Add(content, 0, wx.EXPAND)
        main_sizer.Add((0, 0), 1)  # stretch below

        footer = wx.Panel(self.main_container)
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.cancel_btn = CustomButton(footer, id="cancel", size=(-1, 36))
        self.cancel_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))

        self.save_btn = CustomButton(footer, id="save", size=(-1, 36))
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)

        footer_sizer.Add((padding['left'], 0))
        footer_sizer.Add(self.cancel_btn, 1)
        footer_sizer.Add((gap, 0))
        footer_sizer.Add(self.save_btn, 1)
        footer_sizer.Add((padding['right'], 0))
        footer.SetSizer(footer_sizer)

        main_sizer.Add((0, padding['top']))
        main_sizer.Add(footer, 0, wx.EXPAND | wx.BOTTOM, padding['bottom'])

        self.main_container.SetSizer(main_sizer)

    def on_save(self, event):
        if self.save_btn.IsEnabled():
            self.EndModal(wx.ID_OK)

    def on_text_change(self, event):
        val = self.name_input.GetValue().strip()
        self.save_btn.Enable(bool(val))
        if val:
            existing = _glob.glob(os.path.join(self.chosen_dir, f"{val}_*.png"))
            if existing:
                self.save_btn.SetStyle("exit", update_content=False)
                self.save_btn.SetLabel(_locale.get("component.button.overwrite.label", "OVERWRITE"))
                self.save_btn.SetIcon(_locale.get("component.button.overwrite.icon_ref", "alert"))
            else:
                self.save_btn.SetStyle("save")

    def GetFilename(self):
        return self.name_input.GetValue().strip()


class AdvancedOptionsDialog(BaseStyledDialog):
    """
    Advanced Options modal dialog
    Follows Pencil design: Modal/AdvancedOptions
    """
    # All colors use theme.*

    def __init__(self, parent, settings, board_path):
        # Get dimensions from theme
        dialog_width = _theme._resolve("layout.dialogs.options.frame.width")
        dialog_height = _theme._resolve("layout.dialogs.options.frame.height")
        if dialog_width is None:
            dialog_width = 480
        if dialog_height is None:
            dialog_height = 560
        super().__init__(parent, "Advanced Options", (dialog_width, dialog_height))
        self.settings = settings
        self.board_path = board_path
        self.board_dir = os.path.dirname(board_path)
        self.build_ui()
        self.Centre()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        main_sizer.Add(self.create_header("Advanced options"), 0, wx.EXPAND)

        # Border separator
        line = wx.Panel(self.main_container, size=(-1, 1))
        line.SetBackgroundColour(_theme.color("borders.default.color"))
        main_sizer.Add(line, 0, wx.EXPAND)

        # Content
        content = wx.Panel(self.main_container)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 1. OUTPUT PATH section
        content_sizer.Add(self.create_section_label(content, _locale.get("parameters.output_path.label", "OUTPUT PATH")), 0, wx.EXPAND | wx.BOTTOM, 12)

        # Auto Row
        auto_row = wx.Panel(content)
        auto_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        auto_desc = create_text(auto_row, _locale.get("output.auto_desc", "Automatically save to time-stamped directories."), "dialog_description", color_token="colors.gray-light")
        auto_sizer.Add(auto_desc, 1, wx.ALIGN_CENTER_VERTICAL)
        
        from .custom_controls import CustomToggleButton
        self.auto_toggle = CustomToggleButton(auto_row, id="direction", size=(100, 28)) # Reuse toggle style
        self.auto_toggle.SetValue(self.settings.output_auto)
        self.auto_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_auto_toggle)
        auto_sizer.Add(self.auto_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        
        auto_row.SetSizer(auto_sizer)
        content_sizer.Add(auto_row, 0, wx.EXPAND | wx.BOTTOM, 16)

        # Path Input Row
        path_input_row = wx.Panel(content)
        path_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.path_display = CustomInput(path_input_row, size=(-1, 36), id="path")
        path_input_sizer.Add(self.path_display, 1, wx.RIGHT, 8)
        
        self.browse_btn = CustomButton(path_input_row, id="browse", size=(110, 36))
        self.browse_btn.Bind(wx.EVT_BUTTON, self.on_browse)
        path_input_sizer.Add(self.browse_btn, 0)
        
        path_input_row.SetSizer(path_input_sizer)
        content_sizer.Add(path_input_row, 0, wx.EXPAND | wx.BOTTOM, 20)

        # 2. PARAMETER OVERRIDES section
        content_sizer.Add(self.create_section_label(content, "PARAMETER OVERRIDES"), 0, wx.EXPAND | wx.BOTTOM, 12)
        
        self.override_input = CustomInput(
            content,
            value=getattr(self.settings, 'cli_overrides', ''),
            placeholder=_locale.get("dialog.advanced.overrides_placeholder", ""),
            multiline=True,
            size=(-1, 80),
            id="parameters",
            allow_empty=True
        )
        content_sizer.Add(self.override_input, 1, wx.EXPAND | wx.BOTTOM, 8)
        
        # Helper link simulation
        link_row = wx.Panel(content)
        link_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        info_icon = create_text(link_row, _theme.glyph("info"), "icon", color_token="colors.gray-light")
        info_icon.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        link_sizer.Add(info_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        see_txt = create_text(link_row, _locale.get("dialog.advanced.see", "See "), "dialog_description", color_token="colors.gray-light")
        link_sizer.Add(see_txt, 0, wx.ALIGN_CENTER_VERTICAL)

        link_txt = create_text(link_row, _locale.get("dialog.advanced.docs_link", "kicad-cli render options"), "dialog_description", color_token="colors.primary")
        link_txt.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        link_sizer.Add(link_txt, 0, wx.ALIGN_CENTER_VERTICAL)
        
        url = "https://docs.kicad.org/master/en/cli/cli.html#pcb_render"
        info_icon.Bind(wx.EVT_LEFT_DOWN, lambda e: webbrowser.open(url))
        link_txt.Bind(wx.EVT_LEFT_DOWN, lambda e: webbrowser.open(url))
        
        link_row.SetSizer(link_sizer)
        padding_lg = _theme._resolve("typography.spacing.lg") or 24
        content_sizer.Add(link_row, 0, wx.EXPAND | wx.BOTTOM, padding_lg)

        # 3. LOGGING section
        content_sizer.Add(self.create_section_label(content, "SYSTEM LOGGING"), 0, wx.EXPAND | wx.BOTTOM, 12)
        
        log_row = wx.Panel(content)
        log_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.log_opts = [
            {'id': 'off', 'label': 'OFF'},
            {'id': 'info', 'label': 'INFO'},
            {'id': 'debug', 'label': 'DEBUG'}
        ]
        self.log_toggle = CustomToggleButton(log_row, options=self.log_opts, size=(240, 28), id="direction")
        curr_lvl = getattr(self.settings, 'logging_level', 'info')
        lvl_idx = next((i for i, o in enumerate(self.log_opts) if o['id'] == curr_lvl), 1)
        self.log_toggle.SetSelection(lvl_idx)
        log_hsizer.Add(self.log_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        
        log_row.SetSizer(log_hsizer)
        content_sizer.Add(log_row, 0, wx.EXPAND | wx.BOTTOM, 12)
        
        log_info = create_text(content, _locale.get("parameters.log_info", "Logs are kept for 30 days. Useful for troubleshooting render failures."), "dialog_description", color_token="colors.gray-light")
        content_sizer.Add(log_info, 0, wx.EXPAND | wx.BOTTOM, 8)

        from SpinRender.utils.logger import SpinLogger
        open_logs_txt = create_text(content, _locale.get("parameters.open_logs", "Open logs folder"), "label", color_token="colors.primary")
        open_logs_txt.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        open_logs_txt.Bind(wx.EVT_LEFT_DOWN, lambda e: SpinLogger.open_logs_folder())
        content_sizer.Add(open_logs_txt, 0, wx.BOTTOM, 12)

        content.SetSizer(content_sizer)
        padding_lg = _theme._resolve("typography.spacing.lg") or 24
        main_sizer.Add(content, 1, wx.EXPAND | wx.ALL, padding_lg)

        # Footer
        footer = wx.Panel(self.main_container, size=(-1, 60))
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)

        cancel_btn = CustomButton(footer, id="cancel", size=(120, 36))
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)

        ok_btn = CustomButton(footer, id="ok", size=(120, 36))
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        footer_sizer.AddStretchSpacer()
        footer_sizer.Add(cancel_btn, 0, wx.RIGHT, 12)
        footer_sizer.Add(ok_btn, 0, wx.RIGHT, 16)

        footer.SetSizer(footer_sizer)
        main_sizer.Add(footer, 0, wx.EXPAND | wx.BOTTOM, 16)

        self.main_container.SetSizer(main_sizer)
        self.update_path_display()

    def create_section_label(self, parent, text):
        return create_text(parent, text, "dialog_section_label")

    def update_path_display(self):
        auto = self.auto_toggle.GetValue()
        self.browse_btn.Enable(not auto)
        fmt = getattr(self.settings, 'format', 'mp4')

        if auto:
            self.path_display.SetPath("/Renders/[YYMMDD_HHMMSS]/..", in_project=True)
            self.path_display.Enable(False)
        else:
            self.path_display.Enable(True)
            path = getattr(self.settings, 'output_path', '')
            if not path:
                if fmt == 'png_sequence':
                    self.path_display.SetPath("/Renders/Untitled_#####.png", in_project=True)
                else:
                    ext = 'mp4' if fmt == 'mp4' else 'gif'
                    self.path_display.SetPath(f"/Renders/Untitled.{ext}", in_project=True)
            else:
                display = f"{path}_#####.png" if fmt == 'png_sequence' else path
                try:
                    rel = os.path.relpath(display, self.board_dir)
                    if not rel.startswith('..'):
                        self.path_display.SetPath(f"/{rel}", in_project=True)
                    else:
                        self.path_display.SetPath(display, in_project=False)
                except ValueError:
                    self.path_display.SetPath(display, in_project=False)

    def on_auto_toggle(self, event):
        self.update_path_display()

    def on_browse(self, event):
        start_dir = os.path.join(self.board_dir, "Renders")
        os.makedirs(start_dir, exist_ok=True)
        fmt = getattr(self.settings, 'format', 'mp4')

        if fmt == 'png_sequence':
            # Step 1: pick folder
            board_name = os.path.splitext(os.path.basename(self.board_path))[0]
            existing = getattr(self.settings, 'output_path', '')
            default_name = os.path.basename(existing) if existing else board_name
            default_dir = os.path.dirname(existing) if existing else start_dir
            dir_dlg = wx.DirDialog(self, "Select output folder", defaultPath=default_dir)
            if dir_dlg.ShowModal() != wx.ID_OK:
                dir_dlg.Destroy()
                return
            chosen_dir = dir_dlg.GetPath()
            dir_dlg.Destroy()

            # Step 2: pick base name with inline overwrite detection
            name_dlg = FilenameEntryDialog(self, chosen_dir, default_name)
            if name_dlg.ShowModal() != wx.ID_OK:
                name_dlg.Destroy()
                return
            base_name = os.path.splitext(name_dlg.GetFilename())[0]
            name_dlg.Destroy()
            if not base_name:
                return

            self.settings.output_path = os.path.join(chosen_dir, base_name)
            self.update_path_display()
        else:
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
    PLACEHOLDER_COPY = "PRESET_NAME"

    def __init__(self, parent, board_path):
        # Get dimensions from theme
        dialog_width = _theme._resolve("layout.dialogs.addpreset.frame.width")
        dialog_height = _theme._resolve("layout.dialogs.addpreset.frame.height")
        if dialog_width is None:
            dialog_width = 400
        if dialog_height is None:
            dialog_height = 200 # Reduced height since we removed label
        super().__init__(parent, "Save preset", (dialog_width, dialog_height))
        self.board_path = board_path
        self.preset_name = ""
        self.build_ui()
        self.Centre()
        
        # Prefill and highlight placeholder
        self.name_input.SetValue(self.PLACEHOLDER_COPY)
        wx.CallAfter(self.name_input.text_ctrl.SetFocus)
        wx.CallAfter(self.name_input.text_ctrl.SetSelection, 0, -1)
        
        self.on_text_change(None) # Initial state check

    def build_ui(self):
        from SpinRender.core.presets import PresetManager
        self.manager = PresetManager(self.board_path)
        self.existing_names = [n.upper() for s, n in self.manager.list_presets()]

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        # Header without close button as requested
        main_sizer.Add(self.create_header("Save preset", show_close=False), 0, wx.EXPAND)
        line = wx.Panel(self.main_container, size=(-1, 1)); line.SetBackgroundColour(_theme.color("borders.default.color"))
        main_sizer.Add(line, 0, wx.EXPAND)

        content = wx.Panel(self.main_container)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        self.name_input = CustomInput(content, size=(-1, 36), id="default")
        self.name_input.Bind(wx.EVT_TEXT_ENTER, self.on_save)
        self.name_input.Bind(wx.EVT_TEXT, self.on_text_change)
        
        padding_lg = _theme._resolve("typography.spacing.lg") or 24
        content_sizer.Add(self.name_input, 0, wx.EXPAND | wx.ALL, padding_lg)

        content.SetSizer(content_sizer)
        main_sizer.Add(content, 1, wx.EXPAND)

        footer = wx.Panel(self.main_container, size=(-1, 60))
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        cancel_btn = CustomButton(footer, id="cancel", size=(110, 36))
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        
        self.save_btn = CustomButton(footer, id="save", size=(110, 36))
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        
        footer_sizer.AddStretchSpacer(); footer_sizer.Add(cancel_btn, 0, wx.RIGHT, 12); footer_sizer.Add(self.save_btn, 0, wx.RIGHT, 16)
        footer.SetSizer(footer_sizer)
        main_sizer.Add(footer, 0, wx.EXPAND | wx.BOTTOM, 16)

        self.main_container.SetSizer(main_sizer)

    def on_cancel(self, event): self.EndModal(wx.ID_CANCEL)
    def on_save(self, event): 
        if self.save_btn.IsEnabled():
            self.EndModal(wx.ID_OK)
            
    def on_text_change(self, event):
        val = self.name_input.GetValue().strip()
        is_empty = not val
        is_placeholder = val.upper() == self.PLACEHOLDER_COPY
        
        # Enable save only if not empty and not placeholder
        self.save_btn.Enable(not is_empty and not is_placeholder)
        
        val_upper = val.upper()
        is_overwrite = val_upper in self.existing_names and not is_placeholder
        if is_overwrite:
            self.save_btn.SetStyle("exit", update_content=False)
            self.save_btn.SetLabel(_locale.get("component.button.overwrite.label", "OVERWRITE"))
            self.save_btn.SetIcon(_locale.get("component.button.overwrite.icon_ref", "alert"))
        else:
            self.save_btn.SetStyle("save")
            
    def GetPresetName(self): return self.name_input.GetValue()


class RecallPresetDialog(BaseStyledDialog):
    """
    Recall Preset dialog
    Follows Pencil design: Modal/PresetList
    """
    # All colors use theme module

    def __init__(self, parent, board_path, current_name=None):
        # Get dimensions from theme
        dialog_width = _theme._resolve("layout.dialogs.presets.frame.width")
        dialog_height = _theme._resolve("layout.dialogs.presets.frame.height")
        if dialog_width is None:
            dialog_width = 400
        if dialog_height is None:
            dialog_height = 400
        super().__init__(parent, "Select custom preset", (dialog_width, dialog_height))
        self.board_path = board_path
        self.current_active_name = current_name
        self.selected_preset = self.selected_name = None
        self.build_ui()
        self.Centre()

    def build_ui(self):
        from SpinRender.core.presets import PresetManager
        self.manager = PresetManager(self.board_path); presets = self.manager.list_presets()
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        header = self.create_header("Select custom preset")
        main_sizer.Add(header, 0, wx.EXPAND)
        line = wx.Panel(self.main_container, size=(-1, 1)); line.SetBackgroundColour(_theme.color("borders.default.color"))
        main_sizer.Add(line, 0, wx.EXPAND)

        self.list_view = CustomListView(self.main_container, id="custompresets")
        self.list_view.Bind(EVT_LIST_ITEM_SELECTED, self.on_list_select)
        self.list_view.Bind(EVT_LIST_ITEM_DELETED, self.on_list_delete)
        
        if not presets:
            # Fallback for empty state
            empty_item = self.list_view.AddItem(_locale.get("component.status.no_presets", "No saved presets found."))
            empty_item.Enable(False)
        else:
            for scope, name in presets:
                self.list_view.AddItem(name.upper(), data={"name": name, "scope": scope})
                
        padding_md = _theme._resolve("typography.spacing.md") or 16
        main_sizer.Add(self.list_view, 1, wx.EXPAND | wx.ALL, padding_md)
        self.main_container.SetSizer(main_sizer)

    def on_list_select(self, event):
        data = event.GetClientData()
        name, scope = data["name"], data["scope"]
        self.selected_preset = self.manager.load_preset(name, is_global=(scope=='global'))
        if self.selected_preset:
            self.selected_name = name
            self.EndModal(wx.ID_OK)

    def on_list_delete(self, event):
        data = event.GetClientData()
        name, scope = data["name"], data["scope"]
        if self.manager.delete_preset(name, is_global=(scope=='global')):
            # Refresh list instead of closing dialog to prevent flash and ensure persistence
            self.list_view.ClearItems()
            presets = self.manager.list_presets()
            if not presets:
                empty_item = self.list_view.AddItem(_locale.get("component.status.no_presets", "No saved presets found."))
                empty_item.Enable(False)
            else:
                for scope, name in presets:
                    self.list_view.AddItem(name.upper(), data={"name": name, "scope": scope})
            self.list_view.Layout()
            self.list_view.SetupScrolling(scroll_x=False, scroll_y=True)

    def on_cancel(self, event): self.EndModal(wx.ID_CANCEL)
    def GetSelectedSettings(self): return self.selected_preset
    def GetSelectedName(self): return self.selected_name
