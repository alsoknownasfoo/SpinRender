"""
SpinRender UI Dialogs
Implements modal dialogs from Pencil design
"""
import wx
import os
from .custom_controls import CustomButton, get_custom_font


class BaseStyledDialog(wx.Dialog):
    """
    Base class for chromeless, styled dialogs with dragging support
    """
    BG_MODAL = wx.Colour(17, 17, 17)
    BORDER_DEFAULT = wx.Colour(51, 51, 51)
    ACCENT_YELLOW = wx.Colour(255, 214, 0)
    TEXT_PRIMARY = wx.Colour(224, 224, 224)

    def __init__(self, parent, title, size):
        super().__init__(
            parent,
            title=title,
            size=size,
            style=wx.FRAME_NO_TASKBAR | wx.BORDER_NONE | wx.STAY_ON_TOP
        )
        self.SetBackgroundColour(self.BG_MODAL)
        self.drag_pos = None

    def create_header(self, title_text):
        header = wx.Panel(self, size=(-1, 48))
        header.SetBackgroundColour(self.BG_MODAL)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.header_title = wx.StaticText(header, label=title_text)
        self.header_title.SetForegroundColour(self.ACCENT_YELLOW if "SETUP" in title_text else self.TEXT_PRIMARY)
        self.header_title.SetFont(get_custom_font(13, weight=wx.FONTWEIGHT_SEMIBOLD))
        
        header_sizer.Add(self.header_title, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)
        header.SetSizer(header_sizer)

        # Dragging support
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
    BG_INPUT = wx.Colour(13, 13, 13)
    TEXT_SECONDARY = wx.Colour(119, 119, 119)
    TEXT_MUTED = wx.Colour(85, 85, 85)
    ACCENT_CYAN = wx.Colour(0, 188, 212)

    def __init__(self, parent, settings):
        super().__init__(parent, "Advanced Options", (480, 420))
        self.settings = settings
        self.build_ui()
        self.Centre()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        main_sizer.Add(self.create_header("ADVANCED OPTIONS"), 0, wx.EXPAND)

        # Border separator
        line = wx.Panel(self, size=(-1, 1))
        line.SetBackgroundColour(self.BORDER_DEFAULT)
        main_sizer.Add(line, 0, wx.EXPAND)

        # Content
        content = wx.Panel(self)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # Output Path section
        path_section = self.create_output_path_section(content)
        content_sizer.Add(path_section, 0, wx.EXPAND | wx.ALL, 24)

        # Parameter Overrides section
        override_section = self.create_parameter_overrides_section(content)
        content_sizer.Add(override_section, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 24)

        content.SetSizer(content_sizer)
        main_sizer.Add(content, 1, wx.EXPAND)

        # Footer
        footer = wx.Panel(self, size=(-1, 60))
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

        self.SetSizer(main_sizer)

    def create_output_path_section(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(panel, label="OUTPUT PATH")
        label.SetForegroundColour(self.TEXT_PRIMARY)
        label.SetFont(get_custom_font(10, weight=wx.FONTWEIGHT_BOLD))
        sizer.Add(label, 0, wx.BOTTOM, 16)

        auto_row = wx.Panel(panel)
        auto_sizer = wx.BoxSizer(wx.HORIZONTAL)

        auto_desc = wx.StaticText(auto_row, label="Automatically save to time-stamped directories.")
        auto_desc.SetForegroundColour(self.TEXT_MUTED)
        auto_desc.SetFont(get_custom_font(9))
        auto_sizer.Add(auto_desc, 1, wx.ALIGN_CENTER_VERTICAL)

        # Use standard toggle but style it
        self.auto_toggle = wx.ToggleButton(auto_row, label="ON / OFF", size=(100, 28))
        self.auto_toggle.SetValue(self.settings.get('output_auto', True))
        self.auto_toggle.SetBackgroundColour(self.BG_INPUT)
        self.auto_toggle.SetForegroundColour(self.TEXT_PRIMARY)
        self.auto_toggle.SetFont(get_custom_font(10, weight=wx.FONTWEIGHT_BOLD))
        self.auto_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_auto_toggle)
        auto_sizer.Add(self.auto_toggle, 0, wx.ALIGN_CENTER_VERTICAL)

        auto_row.SetSizer(auto_sizer)
        sizer.Add(auto_row, 0, wx.EXPAND | wx.BOTTOM, 12)

        path_row = wx.Panel(panel)
        path_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.path_input = wx.TextCtrl(path_row, value=self.settings.get('output_path', ''), size=(-1, 36), style=wx.NO_BORDER)
        self.path_input.SetBackgroundColour(self.BG_INPUT)
        self.path_input.SetForegroundColour(self.TEXT_PRIMARY)
        self.path_input.SetFont(get_custom_font(11))
        self.path_input.Enable(not self.settings.get('output_auto', True))
        path_sizer.Add(self.path_input, 1, wx.RIGHT, 8)

        browse_btn = CustomButton(path_row, label="BROWSE", icon="mdi-folder", primary=False, size=(110, 36))
        browse_btn.Bind(wx.EVT_BUTTON, self.on_browse)
        browse_btn.Enable(not self.settings.get('output_auto', True))
        self.browse_btn = browse_btn
        path_sizer.Add(browse_btn, 0)

        path_row.SetSizer(path_sizer)
        sizer.Add(path_row, 0, wx.EXPAND)

        panel.SetSizer(sizer)
        return panel

    def create_parameter_overrides_section(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(panel, label="PARAMETER OVERRIDES")
        label.SetForegroundColour(self.TEXT_PRIMARY)
        label.SetFont(get_custom_font(10, weight=wx.FONTWEIGHT_BOLD))
        sizer.Add(label, 0, wx.BOTTOM, 12)

        self.override_input = wx.TextCtrl(
            panel,
            value=self.settings.get('cli_overrides', ''),
            size=(-1, 80),
            style=wx.TE_MULTILINE | wx.NO_BORDER
        )
        self.override_input.SetBackgroundColour(self.BG_INPUT)
        self.override_input.SetForegroundColour(self.TEXT_PRIMARY)
        self.override_input.SetFont(get_custom_font(11))
        sizer.Add(self.override_input, 0, wx.EXPAND | wx.BOTTOM, 8)

        panel.SetSizer(sizer)
        return panel

    def on_auto_toggle(self, event):
        auto = self.auto_toggle.GetValue()
        self.path_input.Enable(not auto)
        self.browse_btn.Enable(not auto)

    def on_browse(self, event):
        dlg = wx.DirDialog(self, "Select Output Directory")
        if dlg.ShowModal() == wx.ID_OK:
            self.path_input.SetValue(dlg.GetPath())
        dlg.Destroy()

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_ok(self, event):
        self.EndModal(wx.ID_OK)

    def ShowModal(self):
        result = super().ShowModal()
        if result == wx.ID_OK:
            self.settings['output_auto'] = self.auto_toggle.GetValue()
            self.settings['output_path'] = self.path_input.GetValue()
            self.settings['cli_overrides'] = self.override_input.GetValue()
        return result


class SavePresetDialog(BaseStyledDialog):
    """
    Save Preset dialog
    Follows Pencil design: Modal/SavePreset
    """
    BG_INPUT = wx.Colour(13, 13, 13)
    TEXT_SECONDARY = wx.Colour(119, 119, 119)

    def __init__(self, parent):
        super().__init__(parent, "Save Preset", (400, 260))
        self.preset_name = ""
        self.build_ui()
        self.Centre()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        main_sizer.Add(self.create_header("SAVE PRESET"), 0, wx.EXPAND)

        # Border separator
        line = wx.Panel(self, size=(-1, 1))
        line.SetBackgroundColour(self.BORDER_DEFAULT)
        main_sizer.Add(line, 0, wx.EXPAND)

        # Content
        content = wx.Panel(self)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(content, label="PRESET NAME")
        label.SetForegroundColour(self.TEXT_SECONDARY)
        label.SetFont(get_custom_font(10, weight=wx.FONTWEIGHT_BOLD))
        content_sizer.Add(label, 0, wx.LEFT | wx.TOP, 24)

        self.name_input = wx.TextCtrl(content, size=(-1, 36), style=wx.NO_BORDER)
        self.name_input.SetBackgroundColour(self.BG_INPUT)
        self.name_input.SetForegroundColour(self.TEXT_PRIMARY)
        self.name_input.SetFont(get_custom_font(12))
        content_sizer.Add(self.name_input, 0, wx.EXPAND | wx.ALL, 24)

        content.SetSizer(content_sizer)
        main_sizer.Add(content, 1, wx.EXPAND)

        # Footer
        footer = wx.Panel(self, size=(-1, 60))
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)

        cancel_btn = CustomButton(footer, label="CANCEL", icon="mdi-close", primary=False, size=(110, 36))
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)

        save_btn = CustomButton(footer, label="SAVE", icon="mdi-check", primary=True, size=(110, 36))
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)

        footer_sizer.AddStretchSpacer()
        footer_sizer.Add(cancel_btn, 0, wx.RIGHT, 12)
        footer_sizer.Add(save_btn, 0, wx.RIGHT, 16)

        footer.SetSizer(footer_sizer)
        main_sizer.Add(footer, 0, wx.EXPAND | wx.BOTTOM, 16)

        self.SetSizer(main_sizer)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_save(self, event):
        self.EndModal(wx.ID_OK)

    def GetPresetName(self):
        return self.name_input.GetValue().strip()
