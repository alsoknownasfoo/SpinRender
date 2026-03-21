"""
SpinRender Dependency Check Dialog (Bootstrap Version)
Uses only standard wxPython controls with hardcoded style values.
Derived from layouts.dialog.default in dark.yaml.
Strictly NO dependencies on core.theme, core.locale or ui.custom_controls.
"""
import wx
import threading
import logging

logger = logging.getLogger("SpinRender")

# ─────────────────────────────────────────────────────────────────────────────
# HARDCODED STYLE VALUES (Derived from dark.yaml)
# ─────────────────────────────────────────────────────────────────────────────
# layout.dialogs.default.frame.bg: @colors.gray-dark -> #121212
BG_DARK = wx.Colour(18, 18, 18)
# layout.dialogs.default.header.bg: @colors.gray-black -> #0D0D0D
BG_BLACK = wx.Colour(13, 13, 13)
# text.body.color: @colors.gray-medium -> #444444 (Wait, gray-medium is #444 but dialog text should be lighter)
# Using gray-white for primary text: #E0E0E0
TEXT_PRIMARY = wx.Colour(224, 224, 224)
# gray-text: #777777
TEXT_SECONDARY = wx.Colour(119, 119, 119)
# colors.primary: @colors.cyan -> #00BCD4
COLOR_PRIMARY = wx.Colour(0, 188, 212)
# colors.ok: @colors.green -> #4CAF50
COLOR_SUCCESS = wx.Colour(76, 175, 80)
# colors.error: @colors.red -> #FF3B30
COLOR_ERROR = wx.Colour(255, 59, 48)
# borders.default.color: @colors.gray-border -> #1F1F1F
COLOR_BORDER = wx.Colour(31, 31, 31)

# Font Names
FONT_MONO = "JetBrains Mono"
FONT_DISPLAY = "Oswald"
FONT_ICON = "Material Design Icons"
FONT_BODY = "Inter"

# Glyph Constants (Hardcoded unicode)
GLYPH_CHECK = "\U000F05E0"
GLYPH_CLOSE = "\U000F0156"

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CONTROLS (BOOTSTRAP VERSIONS)
# ─────────────────────────────────────────────────────────────────────────────

class RoundedPanel(wx.Panel):
    """Panel with rounded corners and hardcoded background."""
    def __init__(self, parent, radius=6, bg_color=None):
        super().__init__(parent)
        self.radius = radius
        self.bg_color = bg_color or BG_BLACK
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = self.GetSize()
        gc.SetBrush(wx.Brush(self.bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, w, h, self.radius)

class CustomButton(wx.Panel):
    """
    Bootstrap version of CustomButton.
    Supports default vs hover text and background colors.
    """
    def __init__(self, parent, label="BUTTON", primary=True, danger=False, size=(-1, 36)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.label = label
        self.primary = primary
        self.danger = danger
        self.hovered = False
        self.pressed = False

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return

        width, height = self.GetSize()
        enabled = self.IsEnabled()
        
        if not enabled:
            # Grayed out state
            bg = COLOR_BORDER
            text_color = TEXT_SECONDARY
            border_pen = wx.Pen(COLOR_BORDER, 1)
        elif self.primary:
            bg_base = COLOR_PRIMARY
            text_color = BG_BLACK
            border_pen = wx.TRANSPARENT_PEN
            if self.pressed:
                bg = wx.Colour(max(0, bg_base.Red()-30), max(0, bg_base.Green()-30), max(0, bg_base.Blue()-30))
            elif self.hovered:
                bg = wx.Colour(min(255, bg_base.Red()+20), min(255, bg_base.Green()+20), min(255, bg_base.Blue()+20))
            else:
                bg = bg_base
        elif self.danger:
            if self.hovered or self.pressed:
                bg = COLOR_ERROR
                text_color = BG_DARK
                border_pen = wx.TRANSPARENT_PEN
            else:
                bg = BG_DARK
                text_color = wx.Colour(255, 255, 255)
                border_pen = wx.Pen(COLOR_BORDER, 1)
        else:
            bg = BG_BLACK
            text_color = TEXT_PRIMARY
            border_pen = wx.Pen(COLOR_BORDER, 1)

        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(border_pen)
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        font_obj = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName=FONT_MONO)
        gfx_font = gc.CreateFont(font_obj, text_color)
        gc.SetFont(gfx_font)
        tw, th = gc.GetTextExtent(self.label)
        gc.DrawText(self.label, (width - tw) / 2, (height - th) / 2)

    def on_mouse_down(self, event):
        self.pressed = True
        self.Refresh()

    def on_mouse_up(self, event):
        if self.pressed:
            self.pressed = False
            self.Refresh()
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)

    def on_enter(self, event):
        self.hovered = True
        self.Refresh()

    def on_leave(self, event):
        self.hovered = False
        self.pressed = False
        self.Refresh()

class DependencyDialog(wx.Dialog):
    """
    Chromeless, styled dialog for dependency checking.
    Uses hardcoded bootstrap styles.
    """
    def __init__(self, parent, dep_status, checker):
        super().__init__(parent, style=wx.FRAME_NO_TASKBAR | wx.BORDER_NONE | wx.STAY_ON_TOP)
        self.checker = checker
        self.dep_status = dep_status
        self.drag_pos = None
        self.current_dep_index = 0
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)

        # Remove fixed size, use Fit later
        self.SetBackgroundColour(BG_DARK)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 1. Header
        header = wx.Panel(self, size=(-1, 60))
        header.SetBackgroundColour(BG_DARK)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        title = wx.StaticText(header, label="DEPENDENCY CHECK")
        title.SetForegroundColour(COLOR_PRIMARY)
        title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName=FONT_MONO))
        header_sizer.Add(title, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 24)
        
        header.SetSizer(header_sizer)
        main_sizer.Add(header, 0, wx.EXPAND)

        header.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        header.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        header.Bind(wx.EVT_MOTION, self.on_mouse_motion)

        # 2. Content Area
        content = wx.Panel(self)
        content.SetBackgroundColour(BG_DARK)
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)

        msg = wx.StaticText(content, label="SpinRender requires the following dependencies to be installed in the KiCad Python environment:")
        msg.SetForegroundColour(TEXT_PRIMARY)
        msg.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=FONT_BODY))
        msg.Wrap(430)
        self.content_sizer.Add(msg, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 24)

        for dep_name, is_found in self.dep_status.items():
            dep_panel = RoundedPanel(content, radius=6, bg_color=BG_BLACK)
            dep_sizer = wx.BoxSizer(wx.VERTICAL)
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)

            dep_label = wx.StaticText(dep_panel, label=dep_name.upper())
            dep_label.SetForegroundColour(TEXT_PRIMARY)
            dep_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=FONT_MONO))

            icon_char = GLYPH_CHECK if is_found else GLYPH_CLOSE
            status_color = COLOR_SUCCESS if is_found else COLOR_ERROR
            
            status_label = wx.StaticText(dep_panel, label=icon_char)
            status_label.SetForegroundColour(status_color)
            status_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=FONT_ICON))

            row_sizer.Add(dep_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)
            row_sizer.Add(status_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
            dep_sizer.Add(row_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 10)

            dep_panel.SetSizer(dep_sizer)
            self.content_sizer.Add(dep_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
            self.content_sizer.AddSpacer(4) # Reduced gap between items

        self.content_sizer.AddSpacer(12)

        # 3. Progress Panel
        self.progress_panel = wx.Panel(content)
        self.progress_panel.SetBackgroundColour(BG_DARK)
        self.progress_panel.Hide()
        progress_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.progress_gauge = wx.Gauge(self.progress_panel, range=100, size=(-1, 4))
        self.progress_gauge.SetBackgroundColour(BG_BLACK)
        self.progress_gauge.SetForegroundColour(COLOR_PRIMARY)
        progress_sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.BOTTOM, 8)
        
        self.progress_status = wx.StaticText(self.progress_panel, label="Initializing...")
        self.progress_status.SetForegroundColour(TEXT_PRIMARY)
        self.progress_status.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName=FONT_BODY))
        progress_sizer.Add(self.progress_status, 0, wx.EXPAND | wx.BOTTOM, 8)
        
        self.progress_log = wx.TextCtrl(self.progress_panel, size=(-1, 120), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.NO_BORDER | wx.TE_RICH)
        self.progress_log.SetBackgroundColour(BG_BLACK)
        self.progress_log.SetForegroundColour(TEXT_SECONDARY)
        self.progress_log.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=FONT_MONO))
        progress_sizer.Add(self.progress_log, 1, wx.EXPAND)
        
        self.progress_panel.SetSizer(progress_sizer)
        self.content_sizer.Add(self.progress_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)

        content.SetSizer(self.content_sizer)
        main_sizer.Add(content, 1, wx.EXPAND)

        # 4. Footer
        footer = wx.Panel(self)
        footer.SetBackgroundColour(BG_DARK)
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.close_btn = CustomButton(footer, label="EXIT", primary=False, danger=True, size=(90, 36))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        
        self.install_btn = CustomButton(footer, label="INSTALL", primary=True, size=(150, 36))
        self.install_btn.Bind(wx.EVT_BUTTON, self.on_install)

        footer_sizer.AddStretchSpacer()
        footer_sizer.Add(self.close_btn, 0, wx.RIGHT, 12)
        footer_sizer.Add(self.install_btn, 0, wx.RIGHT, 16)

        footer.SetSizer(footer_sizer)
        main_sizer.Add(footer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 16)

        self.SetSizer(main_sizer)
        self.SetMinSize((480, -1))
        self.Fit()
        self.Centre()

    def on_left_down(self, event):
        win = event.GetEventObject()
        win.CaptureMouse()
        x, y = win.ClientToScreen(event.GetPosition())
        origin_x, origin_y = self.GetPosition()
        self.drag_pos = wx.Point(x - origin_x, y - origin_y)

    def on_left_up(self, event):
        win = event.GetEventObject()
        if win.HasCapture(): win.ReleaseMouse()

    def on_mouse_motion(self, event):
        if event.Dragging() and event.LeftIsDown() and self.drag_pos:
            win = event.GetEventObject()
            x, y = win.ClientToScreen(event.GetPosition())
            new_pos = wx.Point(x - self.drag_pos.x, y - self.drag_pos.y)
            self.Move(new_pos)

    def on_timer(self, event):
        val = self.progress_gauge.GetValue()
        limit = (self.current_dep_index * 100) + 95
        if val < limit: self.progress_gauge.SetValue(val + 1)

    def on_close(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_install(self, event):
        if not self.checker.missing_deps:
            self.EndModal(wx.ID_OK)
            return

        self.install_btn.Enable(False)
        self.close_btn.Enable(False)
        self.progress_panel.Show()
        self.progress_log.Clear()
        
        # Ensure proper re-layout and re-fit
        self.Layout()
        self.Fit()
        self.Centre()

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
