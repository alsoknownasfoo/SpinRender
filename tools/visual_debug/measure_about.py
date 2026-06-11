"""Print the About dialog's layout tree (positions, sizes, best sizes, bgs).

Useful for diagnosing clipping/squeeze issues: compare each panel's actual
size against its best size and check where backgrounds change colour.
Run with KiCad's bundled python:

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\visual_debug\\measure_about.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import wx
app = wx.App(False)

from SpinRender.ui import dialogs

frame = wx.Frame(None)
d = dialogs.AboutSpinRenderDialog(frame)
d.main_container.Layout()

mc = d.main_container
print("dialog size:", d.GetSize(), "logical:", d.logical_size, "shadow:", d.shadow_size)
print("main_container size:", mc.GetSize(), "best:", mc.GetBestSize())

def walk(win, depth=0):
    name = type(win).__name__
    bg = win.GetBackgroundColour()
    print("  " * depth + f"{name:18s} pos={tuple(win.GetPosition())} size={tuple(win.GetSize())} best={tuple(win.GetBestSize())} bg={bg.GetAsString(wx.C2S_HTML_SYNTAX)}")
    if depth < 2:
        for c in win.GetChildren():
            walk(c, depth + 1)

walk(mc)
d.Destroy()
