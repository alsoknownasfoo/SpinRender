"""
StatusBar component - displays status message, progress bar, and color-coded states.

Encapsulates the status bar UI at the bottom of SpinRenderPanel.
"""
import wx
from .text_styles import TextStyle
from SpinRender.core.theme import Theme
_theme = Theme.current()


class StatusBar(wx.Panel):
    """Custom status bar with progress indicator and color-coded messages."""

    def __init__(self, parent):
        super().__init__(parent, size=(-1, 25))
        self.SetBackgroundColour(_theme.color("colors.bg.panel"))
        self.SetMinSize((-1, 25))
        self.SetMaxSize((-1, 25))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        # State
        self._msg = "READY"
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
        
        # Dynamic theme lookups
        bg_color = _theme.color("colors.bg.panel")
        success_color = _theme.color("colors.accent.success")
        primary_color = _theme.color("colors.accent.primary")
        text_bg_color = _theme.color("colors.bg.input")

        # Background
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)

        # Progress bar fill (from left)
        bar_color = self._bar_color_override or primary_color
        fill_w = int(w * self._prog)
        if fill_w > 0:
            gc.SetBrush(wx.Brush(bar_color))
            gc.DrawRectangle(0, 0, fill_w, h)
            gc.Clip(0, 0, fill_w, h)

        # Text
        fg_color = self._fg_override or success_color
        font_obj = TextStyle(family=_theme.font_family("mono"), size=8, weight=400).create_font()
        
        gfx_font = gc.CreateFont(font_obj, fg_color)
        gc.SetFont(gfx_font)
        
        tw, th = gc.GetTextExtent(self._msg)
        tx, ty = 10, (h - th) / 2
        gc.DrawText(self._msg, tx, ty)

        if fill_w > 0:
            gc.ResetClip()
            # Draw text again in background color for the filled portion (inverted)
            gfx_font_inv = gc.CreateFont(font_obj, text_bg_color)
            gc.SetFont(gfx_font_inv)
            gc.Clip(0, 0, fill_w, h) # Clip to filled portion for inverted text
            gc.DrawText(self._msg, tx, ty)

    def set_status(self, msg: str, fg_color=None, progress: float = 0.0, bar_color=None):
        """Update status bar display."""
        self._msg = msg
        self._fg_override = fg_color
        self._prog = progress
        self._bar_color_override = bar_color
        self.Refresh()
        self.Update()

    def reset(self):
        """Reset to ready state."""
        self.set_status(msg="READY", progress=0.0)

    def set_error(self, msg: str):
        """Set error state."""
        self.set_status(msg, fg_color=_theme.color("colors.accent.warning"), progress=0.0, bar_color=_theme.color("colors.accent.warning"))

    def set_complete(self):
        """Set complete state."""
        self.set_status("RENDER COMPLETE", fg_color=_theme.color("colors.accent.success"), progress=1.0, bar_color=_theme.color("colors.accent.success"))
