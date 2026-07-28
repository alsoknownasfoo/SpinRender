"""Copyable error dialog.

Render/board-prep errors can carry crash diagnostics (kicad-cli exit code,
binary info, arch checks - see core/renderer.py's _crash_diagnostics) that
are exactly what we need from a user filing a bug report. A plain
wx.MessageBox gives no way to copy that text, so users end up screenshotting
the dialog instead (as happened with issue #5) - error-prone and easy to
crop out the useful part. This gives them one button that copies the full
message verbatim.
"""
import wx

BG_DARK = wx.Colour(18, 18, 18)
BG_BLACK = wx.Colour(13, 13, 13)
TEXT_PRIMARY = wx.Colour(224, 224, 224)
COLOR_ERROR = wx.Colour(255, 59, 48)
COLOR_BORDER = wx.Colour(31, 31, 31)
FONT_MONO = "JetBrains Mono"
FONT_BODY = "Inter"


def show_copyable_error(parent, message, title="Error"):
    """Show `message` in a dialog with a button to copy it verbatim."""
    dlg = wx.Dialog(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
    dlg.SetBackgroundColour(BG_DARK)
    dlg.SetMinSize((480, 280))

    sizer = wx.BoxSizer(wx.VERTICAL)

    heading = wx.StaticText(dlg, label=title)
    heading.SetForegroundColour(COLOR_ERROR)
    heading.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName=FONT_MONO))
    sizer.Add(heading, 0, wx.EXPAND | wx.ALL, 16)

    text_ctrl = wx.TextCtrl(dlg, value=message, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.BORDER_SIMPLE)
    text_ctrl.SetBackgroundColour(BG_BLACK)
    text_ctrl.SetForegroundColour(TEXT_PRIMARY)
    text_ctrl.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=FONT_MONO))
    sizer.Add(text_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)

    button_sizer = wx.BoxSizer(wx.HORIZONTAL)
    copy_btn = wx.Button(dlg, label="Copy Details")
    ok_btn = wx.Button(dlg, id=wx.ID_OK, label="OK")

    def on_copy(event):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(message))
            wx.TheClipboard.Close()
            copy_btn.SetLabel("Copied!")

    copy_btn.Bind(wx.EVT_BUTTON, on_copy)

    button_sizer.AddStretchSpacer()
    button_sizer.Add(copy_btn, 0, wx.RIGHT, 8)
    button_sizer.Add(ok_btn, 0)
    sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 16)

    dlg.SetSizer(sizer)
    dlg.SetSize((520, 340))
    dlg.CentreOnParent()

    dlg.ShowModal()
    dlg.Destroy()
