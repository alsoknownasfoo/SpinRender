"""
SpinRender UI Dialogs
Implements modal dialogs from Pencil design
"""
import logging
import wx
import os
import glob as _glob
import webbrowser
import math as _math
from pathlib import Path
from .custom_controls import (
    CustomButton, CustomInput, CustomListView, 
    EVT_LIST_ITEM_SELECTED, EVT_LIST_ITEM_DELETED
)
from .helpers import create_text, load_svg, load_svg_markup, replace_svg_fill
from SpinRender.core.theme import Theme
from SpinRender.core.locale import Locale
from SpinRender.foundation.fonts import JETBRAINS_MONO, MDI_FONT_FAMILY, INTER
from SpinRender.foundation.icons import STATUS_ICONS

_theme = Theme.current()
_locale = Locale.current()
_logger = logging.getLogger("SpinRender")


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

    def reapply_theme(self):
        """Repaint the dialog and all children with the current theme colors."""
        # Re-apply stored background colors that were set at construction time
        self.main_container.SetBackgroundColour(_theme.color("colors.gray-dark"))
        if hasattr(self, '_dialog_header'):
            self._dialog_header.SetBackgroundColour(_theme.color("colors.gray-dark"))
        # Refresh all children — custom controls query _theme in their on_paint handlers
        self._refresh_recursive(self)
        self.Refresh()
        self.Update()

    def _refresh_recursive(self, win):
        win.Refresh()
        for child in win.GetChildren():
            self._refresh_recursive(child)

    def autosize_dialog_height(self, max_height=None):
        """Resize the dialog to its content height while preserving its base width."""
        self.main_container.Layout()
        best = self.main_container.GetBestSize()
        width = max(self.logical_size[0], best.width) if best.width > 0 else self.logical_size[0]
        height = best.height if best.height > 0 else self.logical_size[1]
        if max_height is not None:
            height = min(height, max_height)
        self.main_container.SetSize(width, height)
        self.logical_size = (width, height)
        self.SetMinSize((-1, -1))
        self.SetSize(width + self.shadow_size * 2, height + self.shadow_size * 2)

    def center_over_parent(self):
        parent = self.GetParent()
        if parent:
            self.CentreOnParent(wx.BOTH)
        else:
            self.Centre()

    def create_header(self, title_text, show_close=True):
        header_height = _theme._resolve("layout.dialogs.default.header.height")
        if header_height is None:
            header_height = 48
        header = wx.Panel(self.main_container, size=(-1, header_height))
        self._dialog_header = header  # stored for reapply_theme
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

    def create_footer(self, btn1_id, btn2_id, padding=16, gap=8, btn1_prop=None, btn2_prop=None):
        """Create a footer panel with divider, vertical padding, and two buttons.

        Args:
            btn1_id: Button ID string for left button
            btn2_id: Button ID string for right button
            padding: int or dict with 'left'/'right'/'top'/'bottom' keys (defaults to 16)
            gap: int gap between buttons (defaults to 8, typically half of horizontal padding)
            btn1_prop: Optional int proportion for button1 (percentage 1-100 or arbitrary int).
                       If None, defaults to 1 (fill mode with equal width).
            btn2_prop: Optional int proportion for button2. If None, defaults to 1.

            Proportion logic:
            - If both props are provided and (btn1_prop + btn2_prop) < 100, a left stretch
              spacer with proportion = 100 - (btn1_prop + btn2_prop) is added (right-align).
            - If both props are provided and sum >= 100, no stretch is added (buttons fill).
            - If either prop is None, both default to 1 and no stretch is added (fill mode).

        Returns:
            tuple: (footer_panel, btn1, btn2)
        """
        if isinstance(padding, int):
            pad = {'left': padding, 'right': padding, 'top': padding, 'bottom': padding}
        else:
            pad = {'left': padding.get('left', 16), 'right': padding.get('right', 16),
                   'top': padding.get('top', 16), 'bottom': padding.get('bottom', 16)}

        footer = wx.Panel(self.main_container)
        outer_sizer = wx.BoxSizer(wx.VERTICAL)

        divider = wx.Panel(footer, size=(-1, 1))
        divider.SetBackgroundColour(_theme.color("borders.default.color"))
        outer_sizer.Add(divider, 0, wx.EXPAND)

        # Determine proportions and if we need a left stretch
        if btn1_prop is None or btn2_prop is None:
            prop1 = 1
            prop2 = 1
            left_stretch = 0
        else:
            prop1 = btn1_prop
            prop2 = btn2_prop
            total = prop1 + prop2
            left_stretch = 100 - total if total < 100 else 0

        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn1 = CustomButton(footer, id=btn1_id, size=(-1, 36))
        btn2 = CustomButton(footer, id=btn2_id, size=(-1, 36))

        footer_sizer.Add((pad['left'], 0))
        if left_stretch:
            footer_sizer.AddStretchSpacer(left_stretch)
        footer_sizer.Add(btn1, prop1)
        footer_sizer.Add((gap, 0))
        footer_sizer.Add(btn2, prop2)
        footer_sizer.Add((pad['right'], 0))

        outer_sizer.Add((0, pad['top']))
        outer_sizer.Add(footer_sizer, 0, wx.EXPAND)
        outer_sizer.Add((0, pad['bottom']))
        footer.SetSizer(outer_sizer)

        return footer, btn1, btn2

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
        super().__init__(parent, _locale.get("dialog.filename.title", "Enter base filename"), (self.dialog_w, h))
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
        main_sizer.Add(self.create_header(_locale.get("dialog.filename.header", "Enter base filename"), show_close=False), 0, wx.EXPAND)

        line = wx.Panel(self.main_container, size=(-1, 1))
        line.SetBackgroundColour(_theme.color("dividers.default.color"))
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

        # Resolve button proportions from theme
        btn1_width = _theme._resolve("layout.dialogs.filename.controls.button1.width")
        btn2_width = _theme._resolve("layout.dialogs.filename.controls.button2.width")
        prop1 = prop2 = None
        if isinstance(btn1_width, str) and btn1_width.endswith("%"):
            try:
                prop1 = int(btn1_width.rstrip("%").strip())
            except ValueError:
                prop1 = None
        if isinstance(btn2_width, str) and btn2_width.endswith("%"):
            try:
                prop2 = int(btn2_width.rstrip("%").strip())
            except ValueError:
                prop2 = None
        footer, self.cancel_btn, self.save_btn = self.create_footer("cancel", "save", padding=padding, gap=gap, btn1_prop=prop1, btn2_prop=prop2)
        self.cancel_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)

        main_sizer.Add(footer, 0, wx.EXPAND)

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

    def __init__(self, parent, settings, board_path, on_theme_change=None):
        # Get dimensions from theme
        dialog_width = _theme._resolve("layout.dialogs.options.frame.width")
        dialog_height = _theme._resolve("layout.dialogs.options.frame.height")
        if dialog_width is None:
            dialog_width = 480
        if dialog_height is None:
            dialog_height = 640
        super().__init__(parent, _locale.get("dialog.advanced.title", "Advanced Options"), (dialog_width, dialog_height))
        self.settings = settings
        self.board_path = board_path
        self.board_dir = os.path.dirname(board_path)
        self._on_theme_change = on_theme_change
        self._original_theme_mode = getattr(settings, 'theme_mode', 'system')
        self.build_ui()
        self.center_over_parent()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        main_sizer.Add(self.create_header(_locale.get("dialog.advanced.header", "Advanced options"), show_close=False), 0, wx.EXPAND)

        # Border separator
        line = wx.Panel(self.main_container, size=(-1, 1))
        line.SetBackgroundColour(_theme.color("dividers.default.color"))
        main_sizer.Add(line, 0, wx.EXPAND)

        # Content
        content = wx.Panel(self.main_container)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 0. APPEARANCE section
        content_sizer.Add(self.create_section_label(content, _locale.get("parameters.appearance.label", "APPEARANCE")), 0, wx.EXPAND | wx.BOTTOM, 12)

        theme_row = wx.Panel(content)
        theme_sizer = wx.BoxSizer(wx.HORIZONTAL)

        theme_desc = create_text(theme_row, _locale.get("dialog.advanced.theme_desc", "Interface theme."), "dialog_description", color_token="colors.gray-light")
        theme_sizer.Add(theme_desc, 1, wx.ALIGN_CENTER_VERTICAL)

        from .custom_controls import CustomToggleButton
        self.theme_opts = [
            {'id': 'dark',   'label': 'DARK',   'icon': 'moon'},
            {'id': 'light',  'label': 'LIGHT',  'icon': 'sun'},
            {'id': 'system', 'label': 'SYSTEM', 'icon': 'computer'},
        ]
        self.theme_toggle = CustomToggleButton(theme_row, options=self.theme_opts, size=(240, 28), id="direction")
        curr_mode = getattr(self.settings, 'theme_mode', 'system')
        mode_idx = next((i for i, o in enumerate(self.theme_opts) if o['id'] == curr_mode), 2)
        self.theme_toggle.SetSelection(mode_idx)
        self.theme_toggle.Bind(wx.EVT_TOGGLEBUTTON, self._on_theme_mode_change)
        theme_sizer.Add(self.theme_toggle, 0, wx.ALIGN_CENTER_VERTICAL)

        theme_row.SetSizer(theme_sizer)
        content_sizer.Add(theme_row, 0, wx.EXPAND | wx.BOTTOM, 20)

        # 1. OUTPUT PATH section
        content_sizer.Add(self.create_section_label(content, _locale.get("parameters.output_path.label", "OUTPUT PATH")), 0, wx.EXPAND | wx.BOTTOM, 12)

        # Auto Row
        auto_row = wx.Panel(content)
        auto_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        auto_desc = create_text(auto_row, _locale.get("output.auto_desc", "Automatically save to time-stamped directories."), "dialog_description")
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
        content_sizer.Add(self.create_section_label(content, _locale.get("dialog.advanced.parameter_overrides_label", "PARAMETER OVERRIDES")), 0, wx.EXPAND | wx.BOTTOM, 12)
        
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
        
        see_txt = create_text(link_row, _locale.get("dialog.advanced.see", "See "), "dialog_description")
        link_sizer.Add(see_txt, 0, wx.ALIGN_CENTER_VERTICAL)

        link_txt = create_text(link_row, _locale.get("dialog.advanced.docs_link", "kicad-cli render options"), "dialog_description")
        link_txt.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        link_sizer.Add(link_txt, 0, wx.ALIGN_CENTER_VERTICAL)
        
        url = "https://docs.kicad.org/master/en/cli/cli.html#pcb_render"
        info_icon.Bind(wx.EVT_LEFT_DOWN, lambda e: webbrowser.open(url))
        link_txt.Bind(wx.EVT_LEFT_DOWN, lambda e: webbrowser.open(url))
        
        link_row.SetSizer(link_sizer)
        padding_lg = _theme._resolve("typography.spacing.lg") or 24
        content_sizer.Add(link_row, 0, wx.EXPAND | wx.BOTTOM, padding_lg)

        # 3. LOGGING section
        content_sizer.Add(self.create_section_label(content, _locale.get("dialog.advanced.section_logging", "SYSTEM LOGGING")), 0, wx.EXPAND | wx.BOTTOM, 12)
        
        log_row = wx.Panel(content)
        log_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.log_opts = [
            {'id': 'off', 'label': _locale.get("system.controls.toggle_off", "OFF")},
            {'id': 'info', 'label': _locale.get("system.controls.toggle_info", "INFO")},
            {'id': 'debug', 'label': _locale.get("system.controls.toggle_debug", "DEBUG")}
        ]
        self.log_toggle = CustomToggleButton(log_row, options=self.log_opts, size=(240, 28), id="direction")
        curr_lvl = getattr(self.settings, 'logging_level', 'info')
        lvl_idx = next((i for i, o in enumerate(self.log_opts) if o['id'] == curr_lvl), 1)
        self.log_toggle.SetSelection(lvl_idx)
        log_hsizer.Add(self.log_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        
        log_row.SetSizer(log_hsizer)
        content_sizer.Add(log_row, 0, wx.EXPAND | wx.BOTTOM, 12)
        
        log_info = create_text(content, _locale.get("parameters.log_info", "Logs are kept for 30 days. Useful for troubleshooting render failures."), "dialog_description")
        content_sizer.Add(log_info, 0, wx.EXPAND | wx.BOTTOM, 8)

        from SpinRender.utils.logger import SpinLogger
        open_logs_txt = create_text(
            content,
            _locale.get("parameters.open_logs", "Open logs folder"),
            "dialog_link",
            link_suffix_arrow=True,
        )
        open_logs_txt.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        open_logs_txt.Bind(wx.EVT_LEFT_DOWN, lambda e: SpinLogger.open_logs_folder())
        content_sizer.Add(open_logs_txt, 0, wx.BOTTOM, 12)

        content.SetSizer(content_sizer)
        padding_lg = _theme._resolve("typography.spacing.lg") or 24
        main_sizer.Add(content, 1, wx.EXPAND | wx.ALL, padding_lg)

        # Footer
        # Resolve gap from theme
        footer_gap = _theme._resolve("layout.dialogs.options.controls.gap") or 8
        footer, cancel_btn, ok_btn = self.create_footer("cancel", "ok", btn1_prop=25, btn2_prop=25, gap=footer_gap)
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        main_sizer.Add(footer, 0, wx.EXPAND)

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
            dir_dlg = wx.DirDialog(self, _locale.get("dir_dialog.select_output_folder", "Select output folder"), defaultPath=default_dir)
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
            dlg = wx.DirDialog(self, _locale.get("dir_dialog.select_output_directory", "Select Output Directory"), defaultPath=start_dir)
            if dlg.ShowModal() == wx.ID_OK:
                self.settings.output_path = dlg.GetPath()
                self.update_path_display()
            dlg.Destroy()

    def _on_theme_mode_change(self, event):
        idx = self.theme_toggle.GetSelection()
        mode = self.theme_opts[idx]['id']
        self.settings.theme_mode = mode
        if self._on_theme_change:
            self._on_theme_change(mode)
        self.reapply_theme()

    def on_cancel(self, event):
        # Restore original theme if the user changed it
        if self.settings.theme_mode != self._original_theme_mode:
            self.settings.theme_mode = self._original_theme_mode
            if self._on_theme_change:
                self._on_theme_change(self._original_theme_mode)
            self.reapply_theme()
        self.EndModal(wx.ID_CANCEL)

    def on_ok(self, event):
        self.settings.cli_overrides = self.override_input.GetValue()
        self.settings.output_auto = self.auto_toggle.GetValue()
        self.settings.logging_level = self.log_opts[self.log_toggle.GetSelection()]['id']
        # theme_mode already set via _on_theme_mode_change
        self.EndModal(wx.ID_OK)


class SavePresetDialog(BaseStyledDialog):
    """
    Save Preset dialog
    Follows Pencil design: Modal/SavePreset
    """
    PLACEHOLDER_COPY = "PRESET_NAME"  # Will be localized in __init__

    def __init__(self, parent, board_path):
        # Get dimensions from theme
        dialog_width = _theme._resolve("layout.dialogs.addpreset.frame.width")
        dialog_height = _theme._resolve("layout.dialogs.addpreset.frame.height")
        if dialog_width is None:
            dialog_width = 400
        if dialog_height is None:
            dialog_height = 200 # Reduced height since we removed label
        super().__init__(parent, _locale.get("dialog.preset.save.title", "Save preset"), (dialog_width, dialog_height))
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
        main_sizer.Add(self.create_header(_locale.get("dialog.preset.save.header", "Save preset"), show_close=False), 0, wx.EXPAND)
        line = wx.Panel(self.main_container, size=(-1, 1)); line.SetBackgroundColour(_theme.color("dividers.default.color"))
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

        # Resolve button proportions from theme
        btn1_width = _theme._resolve("layout.dialogs.addpreset.controls.button1.width")
        btn2_width = _theme._resolve("layout.dialogs.addpreset.controls.button2.width")
        prop1 = prop2 = None
        if isinstance(btn1_width, str) and btn1_width.endswith("%"):
            try:
                prop1 = int(btn1_width.rstrip("%").strip())
            except ValueError:
                prop1 = None
        if isinstance(btn2_width, str) and btn2_width.endswith("%"):
            try:
                prop2 = int(btn2_width.rstrip("%").strip())
            except ValueError:
                prop2 = None
        # Resolve gap from theme
        footer_gap = _theme._resolve("layout.dialogs.addpreset.controls.gap") or 8
        footer, cancel_btn, self.save_btn = self.create_footer("cancel", "save", btn1_prop=prop1, btn2_prop=prop2, gap=footer_gap)
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        main_sizer.Add(footer, 0, wx.EXPAND)

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
        super().__init__(parent, _locale.get("dialog.preset.recall.title", "Select custom preset"), (dialog_width, dialog_height))
        self.board_path = board_path
        self.current_active_name = current_name
        self.selected_preset = self.selected_name = None
        self.build_ui()
        self.Centre()

    def build_ui(self):
        from SpinRender.core.presets import PresetManager
        self.manager = PresetManager(self.board_path); presets = self.manager.list_presets()
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        header = self.create_header(_locale.get("dialog.preset.recall.header", "Select custom preset"))
        main_sizer.Add(header, 0, wx.EXPAND)
        line = wx.Panel(self.main_container, size=(-1, 1)); line.SetBackgroundColour(_theme.color("dividers.default.color"))
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


# ─── About dialog helpers ─────────────────────────────────────────────────

class _AiLogoPanel(wx.Panel):
    """
    24×24 panel that paints a simplified AI brand icon.
    Loads SVG from resources/icons/<name>.svg if wx.svg is available,
    otherwise falls back to basic geometry. Click opens the AI provider URL.
    """
    _SIZE = 24
    _SHAPES = {
        "claude":  "asterisk",   # Anthropic starburst
        "gemini":  "diamond",    # Google Gemini 4-pointed star
        "chatgpt": "ring",       # OpenAI hollow ring
        "copilot":   "circle",     # GitHub Copilot/Codex
        "stepfun": "grid",       # StepFun 2×2 grid
    }
    _URLS = {
        "claude":  "https://claude.ai/",
        "gemini":  "https://gemini.google.com/",
        "chatgpt": "https://chatgpt.com/",
        "copilot":   "https://github.com/features/copilot",
        "stepfun": "https://stepfun.ai/chats/new",
    }
    _SVG_CACHE = {}  # class-level: name → wx.svg.SVGimage or None

    def __init__(self, parent, name):
        s = self._SIZE
        super().__init__(parent, size=(s, s))
        self.SetMinSize((s, s))
        self.SetMaxSize((s, s))
        self._name      = name.lower()
        self._shape     = self._SHAPES.get(self._name, "circle")
        fallback        = self._URLS.get(self._name)
        self._url       = _locale.get(f"dialog.about.ai.{self._name}_url") or fallback
        self._svg_image = self._load_svg(self._name)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self._on_paint)
        if self._url:
            self.Bind(wx.EVT_LEFT_UP, lambda e: webbrowser.open(self._url))
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))

    def _load_svg(self, name):
        """Try to load <resources>/icons/<name>.svg. Returns wx.svg.SVGimage or None."""
        if name not in self._SVG_CACHE:
            self._SVG_CACHE[name] = load_svg(
                Path(__file__).parent.parent / "resources" / "icons" / f"{name}.svg"
            )
        return self._SVG_CACHE[name]

    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return
        s  = float(self._SIZE)
        cx = cy = s / 2.0
        color_token = f"colors.brand.ai.{self._name}"
        c  = _theme.color(color_token if _theme.has_token(color_token) else "colors.brand.ai.unknown")
        bg = _theme.color("colors.gray-dark")

        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0.0, 0.0, s, s)

        if self._svg_image:
            try:
                self._svg_image.RenderToGC(gc, size=(s, s))
            except Exception as exc:
                _logger.debug("SVG render failed for %s: %s", self._name, exc)
            else:
                return

        # Fallback: draw with wx.GraphicsContext geometry
        gc.SetBrush(wx.Brush(c))
        gc.SetPen(wx.TRANSPARENT_PEN)

        if self._shape == "asterisk":
            # 6-armed starburst (Anthropic/Claude)
            gc.SetPen(wx.Pen(c, 2.5))
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            for i in range(6):
                a = _math.radians(i * 60 - 90)
                gc.StrokeLine(cx, cy, cx + 9.0 * _math.cos(a), cy + 9.0 * _math.sin(a))
            gc.SetBrush(wx.Brush(c))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawEllipse(cx - 2.0, cy - 2.0, 4.0, 4.0)

        elif self._shape == "diamond":
            # Narrow 4-pointed star (Google Gemini)
            path = gc.CreatePath()
            pts = [
                (cx,       cy - 11.0), (cx + 2.0,  cy - 2.0),
                (cx + 11.0, cy),       (cx + 2.0,  cy + 2.0),
                (cx,       cy + 11.0), (cx - 2.0,  cy + 2.0),
                (cx - 11.0, cy),       (cx - 2.0,  cy - 2.0),
            ]
            path.MoveToPoint(*pts[0])
            for pt in pts[1:]:
                path.AddLineToPoint(*pt)
            path.CloseSubpath()
            gc.FillPath(path)

        elif self._shape == "ring":
            # Filled ring / donut (OpenAI/ChatGPT)
            gc.DrawEllipse(cx - 9.0, cy - 9.0, 18.0, 18.0)
            gc.SetBrush(wx.Brush(bg))
            gc.DrawEllipse(cx - 4.5, cy - 4.5, 9.0, 9.0)

        elif self._shape == "circle":
            # Solid filled circle
            gc.DrawEllipse(cx - 9.0, cy - 9.0, 18.0, 18.0)

        elif self._shape == "grid":
            # 2×2 rounded-square grid (StepFun)
            sq  = 5.5
            gap = 2.5
            off = (sq * 2.0 + gap) / 2.0
            for row in range(2):
                for col in range(2):
                    gc.DrawRoundedRectangle(
                        cx - off + col * (sq + gap),
                        cy - off + row * (sq + gap),
                        sq, sq, 1.0,
                    )


class _AuthorLogoPanel(wx.Panel):
    """Renders FH.svg for the About author section with theme-aware SVG color."""
    _SVG_IMAGE = None
    _SVG_SOURCE = None
    _DARK_SVG_IMAGE = None
    _DARK_CACHE = {}

    def __init__(self, parent, size):
        super().__init__(parent, size=(size, size))
        self.SetMinSize((size, size))
        self.SetMaxSize((size, size))
        self._ensure_svg_assets()
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self._on_paint)

    @classmethod
    def _ensure_svg_assets(cls):
        svg_path = Path(__file__).parent.parent / "resources" / "icons" / "FH.svg"
        if cls._SVG_IMAGE is None:
            cls._SVG_IMAGE = load_svg(svg_path)
        if cls._SVG_SOURCE is None and svg_path.exists():
            cls._SVG_SOURCE = svg_path.read_text(encoding="utf-8")

    @staticmethod
    def _is_dark_mode():
        loaded_name = (getattr(Theme, "_loaded_name", "") or "dark").lower()
        return loaded_name == "dark"

    @classmethod
    def _dark_svg_image(cls):
        if cls._DARK_SVG_IMAGE is not None:
            return cls._DARK_SVG_IMAGE
        if not cls._SVG_SOURCE:
            return None
        tint = _theme.color("colors.gray-white")
        fill_hex = tint.GetAsString(wx.C2S_HTML_SYNTAX)
        if not fill_hex or not fill_hex.startswith("#"):
            _logger.warning("Unexpected color format from theme: %r", fill_hex)
            return None
        dark_markup = replace_svg_fill(cls._SVG_SOURCE, fill_hex)
        cls._DARK_SVG_IMAGE = load_svg_markup(dark_markup)
        return cls._DARK_SVG_IMAGE

    @staticmethod
    def _tint_bitmap(bitmap, color):
        if not bitmap or not bitmap.IsOk():
            return None
        image = bitmap.ConvertToImage()
        width, height = image.GetSize()
        if image.HasAlpha():
            for y in range(height):
                for x in range(width):
                    if image.GetAlpha(x, y) > 0:
                        image.SetRGB(x, y, color.Red(), color.Green(), color.Blue())
        else:
            for y in range(height):
                for x in range(width):
                    image.SetRGB(x, y, color.Red(), color.Green(), color.Blue())
        return wx.Bitmap(image)

    def _fallback_bitmap_for_size(self, size):
        if not self._SVG_IMAGE:
            return None
        if self._is_dark_mode():
            cached = self._DARK_CACHE.get(size)
            if cached:
                return cached
            base = self._SVG_IMAGE.ConvertToBitmap(scale=1.0)
            tint = _theme.color("colors.gray-white")
            tinted = self._tint_bitmap(base, tint)
            if not tinted or not tinted.IsOk():
                return None
            src_w, src_h = tinted.GetSize()
            if src_w <= 0 or src_h <= 0:
                return None
            scale = min(float(size) / float(src_w), float(size) / float(src_h))
            out_w = max(1, int(src_w * scale))
            out_h = max(1, int(src_h * scale))
            img = tinted.ConvertToImage()
            img.Rescale(out_w, out_h, wx.IMAGE_QUALITY_HIGH)
            fitted = wx.Bitmap(img)
            self._DARK_CACHE[size] = fitted
            return fitted

    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return
        w, h = self.GetClientSize()
        if self._is_dark_mode():
            svg_image = self._dark_svg_image() or self._SVG_IMAGE
        else:
            svg_image = self._SVG_IMAGE

        if svg_image:
            try:
                svg_image.RenderToGC(gc, size=(float(w), float(h)))
                return
            except Exception as exc:
                _logger.debug("FH SVG render failed: %s", exc)

        s = int(min(w, h))
        bmp = self._fallback_bitmap_for_size(s)
        if bmp and bmp.IsOk():
            bw, bh = bmp.GetSize()
            x = (float(w) - float(bw)) / 2.0
            y = (float(h) - float(bh)) / 2.0
            gc.DrawBitmap(bmp, x, y, float(bw), float(bh))

class AboutSpinRenderDialog(BaseStyledDialog):
    """
    About SpinRender dialog — mirrors Modal/About (Dark Theme) from SpinRender.pen.

    Sections (top to bottom):
      1. Version   — CHECK FOR UPDATES button + version badge + release notes link
      2. Author/AI — Author links (left) + AI tool logos (right)
      3. License   — Tagline + donation buttons (GitHub Sponsors + Ko-fi)
      4. Links     — Quick links (left) + License links (right)

    Check for Updates attempts the GitHub Releases API; falls back to a
    simulated animation when the repo is not yet public, communicating this.
    """

    _REPO_OWNER = "alsoknownasfoo"
    _REPO_NAME  = "SpinRender"

    def __init__(self, parent):
        w = _theme._resolve("layout.dialogs.about.frame.width")  or 480
        h = _theme._resolve("layout.dialogs.about.frame.height") or 416
        super().__init__(parent, "SPINRENDER", (w, h))
        self._update_timer = None
        self._update_rotation = 0
        self._closing = False
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)
        self.build_ui()
        self.autosize_dialog_height(max_height=h)
        self.center_over_parent()

    def on_paint_window(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return

        w, h = self.GetSize()
        s = self.shadow_size

        for i in range(s):
            alpha = int(160 * (1.0 - (i / s)**0.5))
            gc.SetBrush(wx.Brush(wx.Colour(_theme.BLACK.Red(), _theme.BLACK.Green(), _theme.BLACK.Blue(), alpha)))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRoundedRectangle(i, i, w - 2*i, h - 2*i, 12)

        gc.SetBrush(wx.Brush(_theme.color("colors.gray-dark")))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(s, s, self.logical_size[0], self.logical_size[1], 4)

        gc.SetPen(wx.Pen(_theme.color("colors.primary"), 1))
        gc.StrokeLine(s, s + self.logical_size[1] - 1, s + self.logical_size[0], s + self.logical_size[1] - 1)

    # ─── build ─────────────────────────────────────────────────────────────

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.create_header("SPINRENDER"), 0, wx.EXPAND)

        line = wx.Panel(self.main_container, size=(-1, 1))
        line.SetBackgroundColour(_theme.color("dividers.default.color"))
        main_sizer.Add(line, 0, wx.EXPAND)

        content = wx.Panel(self.main_container)
        content.SetBackgroundColour(_theme.color("colors.gray-dark"))
        cs = wx.BoxSizer(wx.VERTICAL)

        cs.Add(self._padded_section(content, self._build_version_section,  16, 16, 16, 16), 0, wx.EXPAND)
        cs.Add(self._padded_section(content, self._build_author_ai_section, 16, 16, 16, 16), 0, wx.EXPAND)
        cs.Add(self._padded_section(content, self._build_links_section,     16, 16, 16, 16), 0, wx.EXPAND)
        cs.Add(self._padded_section(content, self._build_license_section,   16, 16, 16, 16, outer_bg="colors.gray-black", show_divider=False), 0, wx.EXPAND)

        content.SetSizer(cs)
        main_sizer.Add(content, 0, wx.EXPAND)
        self.main_container.SetSizer(main_sizer)

    # ─── layout helpers ────────────────────────────────────────────────────

    def _padded_section(self, parent, build_fn, pt=12, pr=16, pb=16, pl=16, outer_bg=None, show_divider=True):
        """Wrap section content with padding and an optional 1 px bottom divider."""
        outer = wx.Panel(parent)
        outer.SetBackgroundColour(_theme.color(outer_bg or "colors.gray-dark"))
        inner = build_fn(outer)
        hs = wx.BoxSizer(wx.HORIZONTAL)
        hs.Add((pl, 0))
        hs.Add(inner, 1)
        hs.Add((pr, 0))
        vs = wx.BoxSizer(wx.VERTICAL)
        vs.Add((0, pt))
        vs.Add(hs, 0, wx.EXPAND)
        vs.Add((0, pb))
        if show_divider:
            div = wx.Panel(outer, size=(-1, 1))
            div.SetBackgroundColour(_theme.color("dividers.default.color"))
            vs.Add(div, 0, wx.EXPAND)
        outer.SetSizer(vs)
        return outer

    def _section_label(self, parent, text):
        """Cyan JetBrains Mono uppercase section header (AUTHOR, LINKS …)."""
        return create_text(parent, text, "about_section_label")

    def _mdi_icon(self, parent, glyph_name, size=12):
        """Small MDI glyph rendered as StaticText."""
        return create_text(parent, _theme.glyph(glyph_name) or "", "about_link_icon")

    def _link_row(self, parent, icon_glyph, label, url, show_arrow=True, icon_gap=12, row_min_height=None):
        """MDI icon + label (+ optional ↗ arrow); whole row opens URL on click."""
        row = wx.Panel(parent)
        row.SetBackgroundColour(_theme.color("colors.gray-dark"))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        icon = self._mdi_icon(row, icon_glyph)
        sizer.Add(icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, icon_gap)

        lbl = create_text(row, label, "about_link_label")
        sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)

        clickable = [row, icon, lbl]
        if show_arrow:
            arrow = create_text(row, "↗", "about_link_arrow")
            sizer.Add(arrow, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)
            clickable.append(arrow)

        if row_min_height is not None:
            row.SetMinSize((-1, row_min_height))
        row.SetSizer(sizer)
        for widget in clickable:
            widget.Bind(wx.EVT_LEFT_UP, lambda e, u=url: webbrowser.open(u))
            widget.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        return row

    # ─── section builders ──────────────────────────────────────────────────

    def _build_version_section(self, parent):
        """CHECK FOR UPDATES btn (left) + version badge + release-notes link (right)."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.color("colors.gray-dark"))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        right = wx.Panel(panel)
        right.SetMinSize((200, -1))
        right.SetBackgroundColour(_theme.color("colors.gray-dark"))
        rs = wx.BoxSizer(wx.VERTICAL)

        ver_raw = _locale.get("component.main.header.subtitle", "0.9 ALPHA")
        meta_wrap = wx.Panel(right)
        meta_wrap.SetBackgroundColour(_theme.color("colors.gray-dark"))
        meta_sizer = wx.BoxSizer(wx.HORIZONTAL)

        accent = wx.Panel(meta_wrap, size=(1, 28))
        accent.SetBackgroundColour(_theme.color("colors.primary"))
        meta_sizer.Add(accent, 0, wx.ALIGN_CENTER_VERTICAL)
        meta_sizer.Add((14, 0))

        meta_col = wx.BoxSizer(wx.VERTICAL)
        ver_lbl = create_text(meta_wrap, ver_raw, "about_link_label", color_token="colors.primary")
        meta_col.Add(ver_lbl, 0)
        meta_col.Add(
            self._link_row(
                meta_wrap,
                "release",
                _locale.get("dialog.about.release_notes_label", "RELEASE NOTES"),
                _locale.get("dialog.about.releases_url", "https://github.com/alsoknownasfoo/SpinRender/releases"),
            ),
            0,
            wx.TOP,
            6,
        )

        meta_sizer.Add(meta_col, 1)
        meta_wrap.SetSizer(meta_sizer)
        rs.Add((8, 0))
        rs.Add(meta_wrap, 0, wx.EXPAND)
        right.SetSizer(rs)
        sizer.Add(right, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddStretchSpacer()

        self.upd_btn = CustomButton(
            panel, id="check-updates",
            label=_locale.get("dialog.about.check_updates", "CHECK FOR UPDATES"),
            icon="cw", size=(170, 32),
        )
        self.upd_btn.SetIconRotation(0)
        self.upd_btn.Bind(wx.EVT_BUTTON, self.on_check_updates)
        sizer.Add(self.upd_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        panel.SetSizer(sizer)
        return panel

    def _build_author_ai_section(self, parent):
        """Author info (left column) + AI tool logos (right column)."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.color("colors.gray-dark"))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left — AUTHOR
        auth = wx.Panel(panel)
        auth.SetBackgroundColour(_theme.color("colors.gray-dark"))
        as_ = wx.BoxSizer(wx.VERTICAL)
        as_.Add(self._section_label(auth, _locale.get("dialog.about.section_author", "AUTHOR")), 0, wx.BOTTOM, 10)

        links_gap = 12
        logo_size = 42

        author_links = wx.Panel(auth)
        author_links.SetBackgroundColour(_theme.color("colors.gray-dark"))

        github_row = self._link_row(
            author_links,
            "github",
            _locale.get("dialog.about.author_github_label", "alsoknownasfoo"),
            _locale.get("dialog.about.author_github_url", "https://github.com/alsoknownasfoo"),
            show_arrow=False,
            icon_gap=6,
            row_min_height=16,
        )
        web_row = self._link_row(
            author_links,
            "web",
            _locale.get("dialog.about.author_website_label", "ALSOKNOWNASFOO.COM"),
            _locale.get("dialog.about.author_website_url", "https://alsoknownasfoo.com"),
            show_arrow=False,
            icon_gap=6,
            row_min_height=16,
        )

        author_links_sizer = wx.BoxSizer(wx.HORIZONTAL)
        author_links_sizer.Add(_AuthorLogoPanel(author_links, logo_size), 0, wx.RIGHT | wx.ALIGN_TOP, 16)

        links_col = wx.BoxSizer(wx.VERTICAL)
        links_col.Add(github_row, 0, wx.BOTTOM, links_gap)
        links_col.Add(web_row, 0)
        author_links_sizer.Add(links_col, 0, wx.ALIGN_TOP)
        author_links.SetSizer(author_links_sizer)

        as_.Add(author_links, 0, wx.ALIGN_TOP)
        auth.SetSizer(as_)
        sizer.Add(auth, 1)

        # Right — SUPPORTED BY
        ai_col = wx.Panel(panel)
        ai_col.SetMinSize((200, -1))
        ai_col.SetBackgroundColour(_theme.color("colors.gray-dark"))
        ais = wx.BoxSizer(wx.VERTICAL)
        ais.Add(self._section_label(ai_col, _locale.get("dialog.about.section_supported_by", "SUPPORTED BY")), 0, wx.BOTTOM, 10)
        ais.Add((0, 10))
        ai_row = wx.Panel(ai_col)
        ai_row.SetBackgroundColour(_theme.color("colors.gray-dark"))
        ars = wx.BoxSizer(wx.HORIZONTAL)
        for name in ("claude", "gemini", "chatgpt", "copilot", "stepfun"):
            ars.Add(_AiLogoPanel(ai_row, name), 0, wx.RIGHT, 16)
        ai_row.SetSizer(ars)
        ais.Add(ai_row, 0)
        ai_col.SetSizer(ais)
        sizer.Add(ai_col, 0, wx.ALIGN_TOP)

        panel.SetSizer(sizer)
        return panel

    def _build_license_section(self, parent):
        """Centered license tagline + donation buttons (GitHub Sponsors + Ko-fi)."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.color("colors.gray-black"))
        vs = wx.BoxSizer(wx.VERTICAL)

        card_w = panel.FromDIP(150)
        card_h = panel.FromDIP(42)

        def _donate_card(card_parent, style_id, icon_name, line1, line2, url):
            card = wx.Panel(card_parent, size=(card_w, card_h))
            card.SetMinSize((card_w, card_h))
            card.SetBackgroundStyle(wx.BG_STYLE_PAINT)
            card.SetCursor(wx.Cursor(wx.CURSOR_HAND))

            state = {"hovered": False}

            def _paint(_event):
                dc = wx.AutoBufferedPaintDC(card)
                gc = wx.GraphicsContext.Create(dc)
                if not gc:
                    _logger.debug("GraphicsContext unavailable for donate card: %s", style_id)
                    return

                card_pad_local = card.FromDIP(16)
                icon_gap_local = card.FromDIP(12)
                corner_radius = card.FromDIP(4)
                line_spacing = card.FromDIP(1)

                token = f"components.button.{style_id}"
                if not (
                    _theme.has_token(f"{token}.frame.bg")
                    and _theme.has_token(f"{token}.label.color")
                ):
                    token = "components.button.default"
                bg = _theme.color(f"{token}.frame.bg", state["hovered"], False, True)
                fg = _theme.color(f"{token}.label.color", state["hovered"], False, True)

                w, h = card.GetClientSize()
                gc.SetBrush(wx.Brush(bg))
                gc.SetPen(wx.TRANSPARENT_PEN)
                gc.DrawRoundedRectangle(0, 0, w, h, corner_radius)

                icon_char = _theme.glyph(icon_name) or ""
                icon_font = gc.CreateFont(_theme.font("icon"), fg)
                gc.SetFont(icon_font)
                iw, ih = gc.GetTextExtent(icon_char)
                icon_x = card_pad_local
                icon_y = (h - ih) / 2
                if icon_char:
                    gc.DrawText(icon_char, icon_x, icon_y)

                text_font = gc.CreateFont(_theme.font("button"), fg)
                gc.SetFont(text_font)
                t1w, t1h = gc.GetTextExtent(line1)
                t2w, t2h = gc.GetTextExtent(line2)
                text_x = icon_x + iw + icon_gap_local
                max_text_w = max(0, w - text_x - card_pad_local)

                def _fit_line(raw, measured_w):
                    if measured_w <= max_text_w:
                        return raw
                    suffix = "..."
                    suffix_w = gc.GetTextExtent(suffix)[0]
                    if suffix_w > max_text_w:
                        return ""
                    text = raw
                    while text and gc.GetTextExtent(text + suffix)[0] > max_text_w:
                        text = text[:-1]
                    return (text + suffix) if text else suffix

                line1_fit = _fit_line(line1, t1w)
                line2_fit = _fit_line(line2, t2w)
                text_block_h = t1h + line_spacing + t2h
                text_y = (h - text_block_h) / 2
                gc.DrawText(line1_fit, text_x, text_y)
                gc.DrawText(line2_fit, text_x, text_y + t1h + line_spacing)

            def _enter(_event):
                state["hovered"] = True
                card.Refresh()

            def _leave(_event):
                state["hovered"] = False
                card.Refresh()

            card.Bind(wx.EVT_PAINT, _paint)
            card.Bind(wx.EVT_ENTER_WINDOW, _enter)
            card.Bind(wx.EVT_LEAVE_WINDOW, _leave)
            card.Bind(wx.EVT_LEFT_UP, lambda _e, u=url: webbrowser.open(u))
            return card

        donate_row = wx.Panel(panel)
        donate_row.SetBackgroundColour(_theme.color("colors.gray-black"))
        dr = wx.BoxSizer(wx.HORIZONTAL)

        copy_wrap = wx.Panel(donate_row, size=(-1, card_h))
        copy_wrap.SetBackgroundColour(_theme.color("colors.gray-black"))
        copy_wrap.SetMinSize((-1, card_h))
        copy_sizer = wx.BoxSizer(wx.VERTICAL)
        copy_sizer.AddStretchSpacer()
        copy_lbl = create_text(
            copy_wrap,
            _locale.get("dialog.about.license_tagline", "Free for personal use\nTip if you love!"),
            "about_link_label",
            color_token="colors.gray-medium",
        )
        copy_sizer.Add(copy_lbl, 0, wx.ALIGN_CENTER_VERTICAL)
        copy_sizer.AddStretchSpacer()
        copy_wrap.SetSizer(copy_sizer)

        github_btn = _donate_card(
            donate_row,
            "donate",
            "heart",
            "SPONSOR ME ON",
            "GITHUB",
            _locale.get("dialog.about.github_sponsors_url", "https://github.com/sponsors/alsoknownasfoo"),
        )
        kofi_btn = _donate_card(
            donate_row,
            "kofi",
            "coffee",
            "SUPPORT ME ON",
            "KO-FI",
            _locale.get("dialog.about.kofi_url", "https://ko-fi.com/alsoknownasfoo"),
        )

        dr.Add(copy_wrap, 0, wx.ALIGN_CENTER_VERTICAL)
        dr.AddStretchSpacer()
        dr.Add(kofi_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        dr.Add(github_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, panel.FromDIP(16))

        donate_row.SetSizer(dr)
        vs.Add(donate_row, 0, wx.EXPAND)

        panel.SetSizer(vs)
        return panel

    def _build_links_section(self, parent):
        """LINKS column (left) + LICENSE column (right)."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(_theme.color("colors.gray-dark"))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        base  = _locale.get("dialog.about.repo_url", "https://github.com/alsoknownasfoo/SpinRender")

        # Left — LINKS
        links_panel = wx.Panel(panel)
        links_panel.SetBackgroundColour(_theme.color("colors.gray-dark"))
        ls = wx.BoxSizer(wx.VERTICAL)
        ls.Add(self._section_label(links_panel, _locale.get("dialog.about.section_links", "LINKS")), 0, wx.BOTTOM, 10)
        for icon_glyph, lkey, fallback, url in [
            ("discussions", "dialog.about.discussions_label",   "Ask a question",            f"{base}/discussions"),
            ("github",      "dialog.about.repo_label",          "/alsoknownasfoo/SpinRender", base),
            ("issues",      "dialog.about.issues_label",        "Report an issue",           f"{base}/issues/new"),
            ("readme",      "dialog.about.readme_label",        "Help + documentation",      f"{base}/blob/main/README.md"),
        ]:
            ls.Add(self._link_row(links_panel, icon_glyph, _locale.get(lkey, fallback), url),
                   0, wx.BOTTOM, 10)
        links_panel.SetSizer(ls)
        sizer.Add(links_panel, 1)

        # Right — LICENSE
        lic_panel = wx.Panel(panel)
        lic_panel.SetMinSize((200, -1))
        lic_panel.SetBackgroundColour(_theme.color("colors.gray-dark"))
        lic_s = wx.BoxSizer(wx.VERTICAL)
        lic_s.Add(self._section_label(lic_panel, _locale.get("dialog.about.section_license", "LICENSE")), 0, wx.BOTTOM, 10)
        lic_s.Add(self._link_row(lic_panel, "file",
                                 _locale.get("dialog.about.gpl_label", "GPLv3 License"),
                                 _locale.get("dialog.about.gpl_url", f"{base}/blob/main/LICENSE")),
                  0, wx.BOTTOM, 10)
        lic_s.Add(self._link_row(lic_panel, "file",
                                 _locale.get("dialog.about.cc_label", "CC BY-NC 4.0"),
                                 _locale.get("dialog.about.cc_url",
                                             "https://creativecommons.org/licenses/by-nc/4.0/")),
                  0, wx.BOTTOM, 10)
        lic_s.Add(self._link_row(lic_panel, "notices",
                                 _locale.get("dialog.about.notices_label", "Open source notices"),
                                 _locale.get("dialog.about.notices_url", f"{base}/blob/main/NOTICES.md")), 0)
        lic_panel.SetSizer(lic_s)
        sizer.Add(lic_panel, 0, wx.ALIGN_TOP)

        panel.SetSizer(sizer)
        return panel

    # ─── check for updates ─────────────────────────────────────────────────

    def on_check_updates(self, event):
        import threading, urllib.request, json

        self._closing = False
        self.upd_btn.SetLabel(self._update_progress_label())
        self.upd_btn.SetIcon("cw")
        self.upd_btn.SetIconRotation(0)
        self.upd_btn.Enable(False)
        self._update_rotation = 0

        self._update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_update_tick, self._update_timer)
        self._update_timer.Start(75)

        def _fetch():
            api_url = (
                f"https://api.github.com/repos/"
                f"{self._REPO_OWNER}/{self._REPO_NAME}/releases/latest"
            )
            try:
                req = urllib.request.Request(
                    api_url,
                    headers={"Accept": "application/vnd.github+json", "User-Agent": "SpinRender"},
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read())
                wx.CallAfter(self._finish_update_check, data.get("tag_name", ""), simulated=False)
            except Exception:
                # Repo not yet public or network failure — fall back to simulation
                import time
                time.sleep(2.2)
                wx.CallAfter(self._finish_update_check, None, simulated=True)

        threading.Thread(target=_fetch, daemon=True).start()

    def _update_progress_label(self):
        return _locale.get("dialog.about.check_updates_progress", "CHECKING").rstrip(". ")

    def _on_update_tick(self, event):
        if self._closing:
            return
        self._update_rotation = (self._update_rotation + 30) % 360
        self.upd_btn.SetIconRotation(self._update_rotation)

    def _stop_update_timer(self):
        if self._update_timer:
            self._update_timer.Stop()
            self._update_timer = None

    def _on_destroy(self, event):
        if event.GetEventObject() is self:
            self._closing = True
            self._stop_update_timer()
        event.Skip()

    def _finish_update_check(self, latest_tag, simulated):
        self._stop_update_timer()
        if self._closing:
            return

        current = _locale.get("component.main.header.subtitle", "0.9.0-alpha")

        if simulated:
            note  = _locale.get("dialog.about.check_updates_simulated",
                                 "(simulated — repo not yet public)")
            label = f"{_locale.get('dialog.about.check_updates_done', 'UP TO DATE')} {note}"
        elif latest_tag and latest_tag.lstrip("v") > current.lstrip("v"):
            label = (f"{_locale.get('dialog.about.check_updates_available', 'UPDATE AVAILABLE')}"
                     f": {latest_tag}")
        else:
            label = _locale.get("dialog.about.check_updates_done", "UP TO DATE")

        self.upd_btn.SetLabel(label)
        self.upd_btn.SetIcon("cw")
        self.upd_btn.SetIconRotation(0)
        self.upd_btn.Enable(True)

    def on_cancel(self, event):
        self._closing = True
        self._stop_update_timer()
        self.EndModal(wx.ID_CANCEL)
