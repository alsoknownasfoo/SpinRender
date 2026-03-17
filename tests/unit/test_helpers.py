#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Unit tests for UI helper functions in helpers.py."""
import pytest
from unittest.mock import MagicMock
import sys

# Use conftest's wx mock. Define test doubles that track state.
class FakePanel:
    """Fake wx.Panel that tracks background colour."""
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        self._bg_colour = None

    def SetBackgroundColour(self, colour):
        self._bg_colour = colour

    def GetBackgroundColour(self):
        return self._bg_colour


class FakeStaticText:
    """Fake wx.StaticText that tracks font, colour, and event bindings."""
    def __init__(self, parent, label, **kwargs):
        self.parent = parent
        self.label = label
        self._font = None
        self._fg_colour = None
        self._bindings = {}  # event_type -> handler

    def SetFont(self, font):
        self._font = font

    def GetFont(self):
        return self._font

    def SetForegroundColour(self, colour):
        self._fg_colour = colour

    def GetForegroundColour(self):
        return self._fg_colour

    def GetLabel(self):
        return self.label

    def Bind(self, event_type, handler):
        """Track event bindings for testing."""
        if event_type not in self._bindings:
            self._bindings[event_type] = []
        self._bindings[event_type].append(handler)

    def GetBindings(self):
        """Return the bindings dict for test inspection."""
        return self._bindings


# wx is already mocked by conftest. Replace Panel and StaticText with our fakes.
import wx
original_Panel = wx.Panel
original_StaticText = wx.StaticText
wx.Panel = FakePanel
wx.StaticText = FakeStaticText

# Event constants for bind_mouse_events tests
wx.EVT_ENTER_WINDOW = 1001
wx.EVT_LEAVE_WINDOW = 1002
wx.EVT_LEFT_DOWN = 1003

from SpinRender.ui import theme
from SpinRender.ui.text_styles import TextStyle
from SpinRender.ui import helpers


class TestCreateFrame:
    """Test create_frame helper."""

    def test_creates_panel_with_parent(self):
        """Creates wx.Panel (FakePanel) with given parent."""
        parent = MagicMock()
        frame = helpers.create_frame(parent, 'BG_INPUT')
        assert isinstance(frame, FakePanel)
        assert frame.parent is parent

    def test_applies_background_from_token(self):
        """Background colour set from theme token."""
        parent = MagicMock()
        frame = helpers.create_frame(parent, 'BG_SURFACE')
        bg = frame.GetBackgroundColour()
        assert bg is theme.BG_SURFACE

    def test_token_validation_raises_for_unknown(self):
        """Unknown token raises ValueError."""
        parent = MagicMock()
        with pytest.raises(ValueError, match="Unknown theme token"):
            helpers.create_frame(parent, 'UNKNOWN_TOKEN')


class TestCreateText:
    """Test create_text helper."""

    def test_creates_statictext_with_parent(self):
        """Creates wx.StaticText (FakeStaticText) with given parent."""
        parent = MagicMock()
        style = TextStyle(family="Test", size=11, weight=400, color=theme.TEXT_PRIMARY)
        text = helpers.create_text(parent, "Label", style)
        assert isinstance(text, FakeStaticText)
        assert text.parent is parent
        assert text.label == "Label"

    def test_applies_font_from_style(self):
        """Font set from TextStyle.create_font()."""
        parent = MagicMock()
        style = TextStyle(family="Test", size=11, weight=600)
        text = helpers.create_text(parent, "Label", style)
        font = text.GetFont()
        assert font is not None
        # TextStyle.create_font returns a MagicMock in test environment
        assert isinstance(font, MagicMock)

    def test_applies_foreground_from_style_color(self):
        """Foreground colour set from style.color when provided."""
        parent = MagicMock()
        style = TextStyle(family="Test", size=11, weight=400, color=theme.ACCENT_CYAN)
        text = helpers.create_text(parent, "Label", style)
        fg = text.GetForegroundColour()
        assert fg is theme.ACCENT_CYAN

    def test_no_foreground_when_color_none(self):
        """Does not set foreground if color is None."""
        parent = MagicMock()
        style = TextStyle(family="Test", size=11, weight=400)
        text = helpers.create_text(parent, "Label", style)
        fg = text.GetForegroundColour()
        assert fg is None

    def test_enables_mouse_pass_through(self):
        """Binds EVT_LEFT_DOWN to enable click propagation to parent."""
        parent = MagicMock()
        style = TextStyle(family="Test", size=11, weight=400)
        text = helpers.create_text(parent, "Label", style)
        bindings = text.GetBindings()
        assert wx.EVT_LEFT_DOWN in bindings
        assert len(bindings[wx.EVT_LEFT_DOWN]) == 1


class TestBindMouseEvents:
    """Test bind_mouse_events helper."""

    def test_binds_enter_window_when_handler_provided(self):
        """Binds EVT_ENTER_WINDOW if hover_handler not None."""
        parent = MagicMock()
        handler = MagicMock()
        helpers.bind_mouse_events(parent, hover_handler=handler)
        parent.Bind.assert_any_call(wx.EVT_ENTER_WINDOW, handler)

    def test_binds_leave_window_when_handler_provided(self):
        """Binds EVT_LEAVE_WINDOW if leave_handler not None."""
        parent = MagicMock()
        handler = MagicMock()
        helpers.bind_mouse_events(parent, leave_handler=handler)
        parent.Bind.assert_any_call(wx.EVT_LEAVE_WINDOW, handler)

    def test_binds_left_down_when_handler_provided(self):
        """Binds EVT_LEFT_DOWN if click_handler not None."""
        parent = MagicMock()
        handler = MagicMock()
        helpers.bind_mouse_events(parent, click_handler=handler)
        parent.Bind.assert_any_call(wx.EVT_LEFT_DOWN, handler)

    def test_does_not_bind_when_handler_none(self):
        """Does not bind event if corresponding handler is None."""
        parent = MagicMock()
        helpers.bind_mouse_events(parent)
        parent.Bind.assert_not_called()

    def test_binds_only_specified_handlers(self):
        """Binds exactly the handlers that are provided."""
        parent = MagicMock()
        hover = MagicMock()
        click = MagicMock()
        helpers.bind_mouse_events(parent, hover_handler=hover, click_handler=click)
        # Should bind exactly two events
        assert parent.Bind.call_count == 2


class TestApplyDisabledState:
    """Test apply_disabled_state helper."""

    def test_applies_disabled_alpha_to_widget(self):
        """Sets widget to 50% opacity when disabled."""
        widget = FakePanel(None)
        original = theme.ACCENT_CYAN
        widget.SetBackgroundColour(original)

        helpers.apply_disabled_state(widget, is_enabled=False)

        new_bg = widget.GetBackgroundColour()
        # Should be a ColourMock with alpha=128
        assert new_bg.Alpha() == 128
        # RGB should be unchanged
        assert new_bg.Red() == original.Red()
        assert new_bg.Green() == original.Green()
        assert new_bg.Blue() == original.Blue()

    def test_restores_enabled_state(self):
        """Does not change colour when is_enabled=True."""
        widget = FakePanel(None)
        original = theme.ACCENT_CYAN
        widget.SetBackgroundColour(original)

        helpers.apply_disabled_state(widget, is_enabled=True)

        # Should not have changed background
        new_bg = widget.GetBackgroundColour()
        assert new_bg is original
