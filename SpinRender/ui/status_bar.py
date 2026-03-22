"""
StatusBar component - displays status message, progress bar, and color-coded states.

Encapsulates the status bar UI at the bottom of SpinRenderPanel.
"""
import wx
from .text_styles import TextStyle, TextStyles
from SpinRender.core.theme import Theme
_theme = Theme.current()


class StatusBar(wx.Panel):
    """Custom status bar with progress indicator and color-coded messages."""

    def __init__(self, parent):
        super().__init__(parent, size=(-1, 25))
        self.SetBackgroundColour(_theme.color("layout.main.status.default.bg"))
        self.SetMinSize((-1, 25))
        self.SetMaxSize((-1, 25))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        # State - import Locale for status messages
        from SpinRender.core.locale import Locale
        _locale = Locale.current()
        self._msg = TextStyles.status.format_text(_locale.get("component.status.ready", "Ready"))
        self._fg_override = None
        self._prog = 0.0
        self._bar_color_override = None

        # Bind paint handler
        self.Bind(wx.EVT_PAINT, self._on_paint)

    def _on_paint(self, event):
        """Paint the status bar with message and progress bar."""
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return

        w, h = self.GetSize()
        
        # Dynamic theme lookups from component section
        bg_color = _theme.color("layout.main.status.default.bg")
        success_color = _theme.color("layout.main.status.default.label.color")
        primary_color = _theme.color("layout.main.status.progress.bg")

        # Background
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)

        # Progress bar fill (from left) — drawn before text, no clip
        bar_color = self._bar_color_override or primary_color
        fill_w = int(w * self._prog)
        if fill_w > 0:
            gc.SetBrush(wx.Brush(bar_color))
            gc.DrawRectangle(0, 0, fill_w, h)

        # Layer 1: base text (unclipped) — readable against the unfilled background
        fg_color = self._fg_override or success_color
        font_obj = TextStyles.status.create_font()
        gc.SetFont(gc.CreateFont(font_obj, fg_color))
        tw, th = gc.GetTextExtent(self._msg)
        tx, ty = 10, (h - th) / 2
        gc.DrawText(self._msg, tx, ty)

        # Layer 2: accent text clipped to fill region — readable against the fill colour
        if fill_w > 0:
            accent_color = _theme.color("layout.main.status.progress.label.color")
            gc.SetFont(gc.CreateFont(font_obj, accent_color))
            gc.Clip(0, 0, fill_w, h)
            gc.DrawText(self._msg, tx, ty)
            gc.ResetClip()

    def set_status(self, msg: str, fg_color=None, progress: float = 0.0, bar_color=None):
        """Update status bar display."""
        self._msg = TextStyles.status.format_text(msg)
        self._fg_override = fg_color
        self._prog = progress
        self._bar_color_override = bar_color
        self.Refresh()
        self.Update()

    def reset(self):
        """Reset to ready state."""
        from SpinRender.core.locale import Locale
        self.set_status(msg=Locale.current().get("component.status.ready", "Ready"), progress=0.0)

    def set_error(self, msg: str):
        """Set error state."""
        error_color = _theme.color("layout.main.status.error.label.color")
        self.set_status(msg, fg_color=error_color, progress=0.0, bar_color=error_color)

    def set_complete(self):
        """Set complete state."""
        from SpinRender.core.locale import Locale
        _locale = Locale.current()
        done_color = _theme.color("layout.main.status.complete.label.color")
        self.set_status(_locale.get("component.status.complete", "RENDER COMPLETE"), fg_color=done_color, progress=1.0, bar_color=done_color)
