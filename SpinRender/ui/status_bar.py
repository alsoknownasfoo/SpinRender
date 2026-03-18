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
        self._fg = _theme.color("colors.accent.success")
        self._prog = 0.0
        self._bar_color = _theme.color("colors.accent.primary")

        # Bind paint handler
        self.Bind(wx.EVT_PAINT, self._on_paint)

    def _on_paint(self, event):
        """Paint the status bar with message and progress bar."""
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return

        w, h = self.GetSize()

        # Background
        gc.SetBrush(wx.Brush(_theme.color("colors.bg.panel")))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)

        # Progress bar fill (from left)
        fill_w = int(w * self._prog)
        if fill_w > 0:
            gc.SetBrush(wx.Brush(self._bar_color))
            gc.DrawRectangle(0, 0, fill_w, h)
            gc.Clip(0, 0, fill_w, h)

        # Text
        font = TextStyle(family=_theme.font_family("mono"), size=8, weight=400).create_font()
        gc.SetFont(font, self._fg)
        tw, th = gc.GetTextExtent(self._msg)
        tx, ty = 10, (h - th) / 2
        gc.DrawText(self._msg, tx, ty)

        if fill_w > 0:
            gc.ResetClip()
            # Draw text again in background color for the filled portion (inverted)
            gc.SetFont(font, _theme.color("colors.bg.input"))
            gc.DrawText(self._msg, tx, ty)

    def set_status(self, msg: str, fg_color=None, progress: float = 0.0, bar_color=None):
        """Update status bar display.

        Args:
            msg: Status message text
            fg_color: Foreground color (text color)
            progress: Progress fraction (0.0 to 1.0)
            bar_color: Progress bar fill color
        """
        self._msg = msg
        if fg_color is not None:
            self._fg = fg_color
        self._prog = progress
        if bar_color is not None:
            self._bar_color = bar_color
        self.Refresh()

    def reset(self):
        """Reset to ready state."""
        self.set_status(
            msg="READY",
            fg_color=_theme.color("colors.accent.success"),
            progress=0.0,
            bar_color=_theme.color("colors.accent.primary")
        )

    def set_error(self, msg: str):
        """Set error state."""
        self.set_status(msg, fg_color=_theme.color("colors.accent.warning"), progress=0.0, bar_color=_theme.color("colors.accent.warning"))

    def set_complete(self):
        """Set complete state."""
        self.set_status("RENDER COMPLETE", fg_color=_theme.color("colors.accent.success"), progress=1.0, bar_color=_theme.color("colors.accent.success"))
