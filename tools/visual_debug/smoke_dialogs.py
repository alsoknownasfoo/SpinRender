"""Construct every styled dialog outside KiCad.

Catches constructor errors, sizer assertions, and layout exceptions in one
pass without relaunching KiCad. Run with KiCad's bundled python:

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\visual_debug\\smoke_dialogs.py
"""
import sys
import traceback
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import wx
app = wx.App(False)

from SpinRender.ui import dialogs

frame = wx.Frame(None)
ok = True

def try_dialog(name, fn):
    global ok
    try:
        d = fn()
        d.Layout()
        d.Destroy()
        print(f"OK   {name}")
    except Exception:
        ok = False
        print(f"FAIL {name}")
        traceback.print_exc()

settings = types.SimpleNamespace(
    theme_mode="system", output_auto=True, output_path="",
    cli_overrides="", logging_level="info", format="gif",
)

board = str(Path(__file__).resolve().parent / "fake_board.kicad_pcb")

try_dialog("AboutSpinRenderDialog", lambda: dialogs.AboutSpinRenderDialog(frame))
try_dialog("RecallPresetDialog", lambda: dialogs.RecallPresetDialog(frame, board))
try_dialog("AdvancedOptionsDialog", lambda: dialogs.AdvancedOptionsDialog(frame, settings, board))
try_dialog("MessageDialog", lambda: dialogs.MessageDialog(frame, "Test", "Hello world"))

print("ALL OK" if ok else "FAILURES PRESENT")
