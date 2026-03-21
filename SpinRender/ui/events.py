"""
Custom wx events for SpinRender UI.
"""
import wx.lib.newevent

# Fired by any parameter control when the user interacts with it while enabled.
# Bubbles up the wx command event chain — bind once on controls_side_panel.
ParameterInteractionEvent, EVT_PARAMETER_INTERACTION = wx.lib.newevent.NewCommandEvent()
