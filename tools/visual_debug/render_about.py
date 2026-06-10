"""Render the About dialog DPI-aware and screenshot it to about_render.png.

Reproduces exactly what KiCad shows on this display (per-monitor DPI aware,
so FromDIP scaling matches) without relaunching KiCad. Read the saved PNG to
verify dialog changes pixel-by-pixel. Run with KiCad's bundled python:

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\visual_debug\\render_about.py
"""
import sys
import ctypes
from pathlib import Path

if sys.platform.startswith("win"):
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor DPI aware, like KiCad

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import wx
app = wx.App(False)

from SpinRender.ui import dialogs

OUT = Path(__file__).resolve().parent / "about_render.png"

frame = wx.Frame(None)
d = dialogs.AboutSpinRenderDialog(frame)
print("dpi scale:", d.GetDPIScaleFactor(), "dialog size:", d.GetSize(), "logical:", d.logical_size)
d.Show()


def grab():
    d.Refresh(); d.Update()
    w, h = d.GetSize()
    x, y = d.GetPosition()
    sdc = wx.ScreenDC()
    bmp = wx.Bitmap(w, h)
    mdc = wx.MemoryDC(bmp)
    mdc.Blit(0, 0, w, h, sdc, x, y)
    mdc.SelectObject(wx.NullBitmap)
    bmp.SaveFile(str(OUT), wx.BITMAP_TYPE_PNG)
    print("saved", OUT, (w, h))
    d.Destroy()
    app.ExitMainLoop()


wx.CallLater(600, grab)
app.MainLoop()
