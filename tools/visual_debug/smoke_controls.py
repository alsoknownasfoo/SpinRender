"""Construct and paint every custom control outside KiCad.

Catches constructor/attribute-order bugs and paint-handler exceptions in
one pass without relaunching KiCad. Run with KiCad's bundled python:

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\visual_debug\\smoke_controls.py
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import wx
app = wx.App(False)

from SpinRender.ui.custom_controls import (
    CustomSlider, CustomToggleButton, CustomCheckbox, CustomDropdown,
    CustomButton, PresetCard, SectionLabel, SectionToggle, CustomInput,
    CustomColorPicker, CustomListView,
)
from SpinRender.core.theme import Theme

frame = wx.Frame(None)
panel = wx.Panel(frame)
panel.SetBackgroundColour(Theme.current().color("layout.main.frame.bg"))

ok = True
ctors = [
    ("CustomSlider",       lambda: CustomSlider(panel, value=10, min_val=0, max_val=100, id="primary")),
    ("CustomToggleButton", lambda: CustomToggleButton(panel, id="direction")),
    ("CustomCheckbox",     lambda: CustomCheckbox(panel, id="hide_vias")),
    ("CustomDropdown",     lambda: CustomDropdown(panel, choices=["A", "B"], id="format")),
    ("CustomButton",       lambda: CustomButton(panel, id="render")),
    ("PresetCard",         lambda: PresetCard(panel, id="card1")),
    ("SectionLabel",       lambda: SectionLabel(panel, label="TEST")),
    ("SectionToggle",      lambda: SectionToggle(panel, size=12)),
    ("CustomInput num",    lambda: CustomInput(panel, value="1.0", id="axis", unit="deg")),
    ("CustomInput hex",    lambda: CustomInput(panel, value="#000000", id="hex")),
    ("CustomColorPicker",  lambda: CustomColorPicker(panel)),
    ("CustomListView",     lambda: CustomListView(panel)),
]
for name, fn in ctors:
    try:
        w = fn()
        w.Refresh()
        print(f"OK   {name}")
    except Exception:
        ok = False
        print(f"FAIL {name}")
        traceback.print_exc()

# exercise paint handlers off-screen
frame.Show()
wx.CallLater(300, frame.Close)
wx.CallLater(400, app.ExitMainLoop)
app.MainLoop()
print("ALL OK" if ok else "FAILURES PRESENT")
