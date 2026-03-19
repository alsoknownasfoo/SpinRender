"""
SpinRender Dependency Check Dialog (Bootstrap Version)
Uses only standard wxPython controls but implements custom drawing to match
the themed High-Density aesthetic exactly. 
No dependencies on core.theme or ui.custom_controls.
"""
import wx
import threading
import logging
from SpinRender.core.theme import Theme
from SpinRender.foundation.icons import get_glyph

logger = logging.getLogger("SpinRender")

# ─────────────────────────────────────────────────────────────────────────────
# BOOTSTRAP FALLBACKS (Used if Theme is not available)
# ─────────────────────────────────────────────────────────────────────────────
def _get_color(token, fallback):
    try:
        t = Theme.current()
        if t and t._data:
            return t.color(token)
    except Exception:
        pass
    return fallback

# Hardcoded theme & font constants (Legacy fallbacks)
BG_PAGE_FB = wx.Colour(18, 18, 18)      # palette.neutral-3
BG_INPUT_FB = wx.Colour(13, 13, 13)     # palette.neutral-2
TEXT_PRIMARY_FB = wx.Colour(224, 224, 224)  # palette.neutral-14
TEXT_SECONDARY_FB = wx.Colour(119, 119, 119) # palette.neutral-11
ACCENT_CYAN_FB = wx.Colour(0, 188, 212) # palette.cyan
ACCENT_GREEN_FB = wx.Colour(76, 175, 80) # palette.green
ACCENT_DANGER_FB = wx.Colour(180, 0, 0) # palette.danger-medium
BORDER_DEFAULT_FB = wx.Colour(31, 31, 31) # palette.neutral-7

JETBRAINS_MONO = "JetBrains Mono"
MDI_FONT_FAMILY = "Material Design Icons"
OSWALD = "Oswald"
INTER = "Inter"

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CONTROLS (BOOTSTRAP VERSIONS)
# ─────────────────────────────────────────────────────────────────────────────

class RoundedPanel(wx.Panel):
    """Panel with rounded corners and hardcoded background."""
    def __init__(self, parent, radius=4, bg_color=None):
        super().__init__(parent)
        self.radius = radius
        self.bg_color = bg_color or _get_color("components.main.frame.bg", BG_INPUT_FB)
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
        
        # Determine colors based on type and interaction state
        if self.primary:
            # Action Button: Cyan background, Dark text
            bg_base = _get_color("colors.primary", ACCENT_CYAN_FB)
            text_color = _get_color("colors.gray-black", BG_INPUT_FB)
            border_pen = wx.TRANSPARENT_PEN
            
            if self.pressed:
                bg = wx.Colour(max(0, bg_base.Red()-30), max(0, bg_base.Green()-30), max(0, bg_base.Blue()-30))
            elif self.hovered:
                bg = wx.Colour(min(255, bg_base.Red()+20), min(255, bg_base.Green()+20), min(255, bg_base.Blue()+20))
            else:
                bg = bg_base
        elif self.danger:
            # Exit Button
            if self.hovered or self.pressed:
                bg = _get_color("palette.danger-medium", ACCENT_DANGER_FB)
                text_color = _get_color("colors.bg.page", BG_PAGE_FB)
                border_pen = wx.TRANSPARENT_PEN
            else:
                bg = _get_color("colors.bg.page", BG_PAGE_FB)
                text_color = wx.Colour(255, 255, 255)
                border_pen = wx.Pen(_get_color("borders.default.color", BORDER_DEFAULT_FB), 1)
        else:
            # Secondary
            bg = _get_color("components.component.input.default.frame.bg", BG_INPUT_FB)
            text_color = _get_color("text.body.color", TEXT_PRIMARY_FB)
            border_pen = wx.Pen(_get_color("borders.default.color", BORDER_DEFAULT_FB), 1)

        # Draw Background
        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(border_pen)
        gc.DrawRoundedRectangle(1, 1, width - 2, height - 2, 4)

        # Draw Label
        font_obj = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName=JETBRAINS_MONO)
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
    Follows High-Density V2 aesthetic.
    """
    def __init__(self, parent, checker):
        super().__init__(parent, style=wx.FRAME_NO_TASKBAR | wx.BORDER_NONE | wx.STAY_ON_TOP)
        self.checker = checker
        self.dep_status = checker.get_status()
        self.drag_pos = None
        self.current_dep_index = 0
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)

        self.SetSize((480, 520))
        self.Centre()
        self.SetBackgroundColour(_get_color("colors.bg.page", BG_PAGE_FB))

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 1. Header
        header = wx.Panel(self, size=(-1, 60))
        header.SetBackgroundColour(_get_color("colors.bg.page", BG_PAGE_FB))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        title = wx.StaticText(header, label="DEPENDENCY CHECK")
        title.SetForegroundColour(_get_color("colors.secondary", ACCENT_CYAN_FB))
        title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName=JETBRAINS_MONO))
        header_sizer.Add(title, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 24)
        
        header.SetSizer(header_sizer)
        main_sizer.Add(header, 0, wx.EXPAND)

        # Dragging bindings
        header.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        header.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        header.Bind(wx.EVT_MOTION, self.on_mouse_motion)

        # 2. Content Area
        content = wx.Panel(self)
        content.SetBackgroundColour(_get_color("colors.bg.page", BG_PAGE_FB))
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)

        msg = wx.StaticText(content, label="SpinRender requires the following dependencies to be installed in the KiCad Python environment:")
        msg.SetForegroundColour(_get_color("text.body.color", TEXT_PRIMARY_FB))
        msg.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=INTER))
        msg.Wrap(430)
        self.content_sizer.Add(msg, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 24)

        # Dependency List
        for dep_name, is_found in self.dep_status.items():
            dep_panel = RoundedPanel(content, radius=6, bg_color=_get_color("components.component.input.default.frame.bg", BG_INPUT_FB))
            dep_sizer = wx.BoxSizer(wx.VERTICAL)
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)

            dep_label = wx.StaticText(dep_panel, label=dep_name.upper())
            dep_label.SetForegroundColour(_get_color("text.body.color", TEXT_PRIMARY_FB))
            dep_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=JETBRAINS_MONO))

            icon_name = "mdi-check-circle" if is_found else "mdi-close"
            icon_char = get_glyph(icon_name)
            status_color = _get_color("colors.success", ACCENT_GREEN_FB) if is_found else _get_color("palette.danger-medium", ACCENT_DANGER_FB)
            
            status_label = wx.StaticText(dep_panel, label=icon_char)
            status_label.SetForegroundColour(status_color)
            status_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=MDI_FONT_FAMILY))

            row_sizer.Add(dep_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 16)
            row_sizer.Add(status_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
            dep_sizer.Add(row_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 12)

            dep_panel.SetSizer(dep_sizer)
            self.content_sizer.Add(dep_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
            self.content_sizer.AddSpacer(8)

        self.content_sizer.AddSpacer(16)

        # 3. Progress Panel (hidden initially)
        self.progress_panel = wx.Panel(content)
        self.progress_panel.SetBackgroundColour(_get_color("colors.bg.page", BG_PAGE_FB))
        self.progress_panel.Hide()
        progress_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.progress_gauge = wx.Gauge(self.progress_panel, range=100, size=(-1, 4))
        self.progress_gauge.SetBackgroundColour(_get_color("components.component.input.default.frame.bg", BG_INPUT_FB))
        self.progress_gauge.SetForegroundColour(_get_color("colors.primary", ACCENT_CYAN_FB))
        progress_sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.BOTTOM, 8)
        
        self.progress_status = wx.StaticText(self.progress_panel, label="Initializing...")
        self.progress_status.SetForegroundColour(_get_color("text.body.color", TEXT_PRIMARY_FB))
        self.progress_status.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName=INTER))
        progress_sizer.Add(self.progress_status, 0, wx.EXPAND | wx.BOTTOM, 8)
        
        self.progress_log = wx.TextCtrl(
            self.progress_panel, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.NO_BORDER | wx.TE_RICH
        )
        self.progress_log.SetBackgroundColour(_get_color("components.component.input.default.frame.bg", BG_INPUT_FB))
        self.progress_log.SetForegroundColour(_get_color("colors.gray-text", TEXT_SECONDARY_FB))
        self.progress_log.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=JETBRAINS_MONO))
        progress_sizer.Add(self.progress_log, 1, wx.EXPAND)
        
        self.progress_panel.SetSizer(progress_sizer)
        self.content_sizer.Add(self.progress_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)

        content.SetSizer(self.content_sizer)
        main_sizer.Add(content, 1, wx.EXPAND)

        # 4. Footer
        footer = wx.Panel(self)
        footer.SetBackgroundColour(_get_color("colors.bg.page", BG_PAGE_FB))
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
        self.Layout()

    # Window Dragging Logic
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
