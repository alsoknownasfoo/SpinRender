#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Unit tests for UI helper functions in helpers.py."""
import pytest
from unittest.mock import MagicMock
import importlib

# Test doubles that track state
class FakePanel:
    """Fake wx.Panel that tracks background color and common methods."""
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        self._bg_color = None
        self._size = (100, 100)
        self._sizer = None

    def SetBackgroundColour(self, color):
        self._bg_color = color

    def GetBackgroundColor(self):
        return self._bg_color

    def GetSize(self):
        return self._size

    def SetMinSize(self, size):
        pass

    def SetSizer(self, sizer):
        self._sizer = sizer

    def SetSizerAndFit(self, sizer):
        self.SetSizer(sizer)
        min_size = sizer.CalcMin() if hasattr(sizer, 'CalcMin') else (100, 100)
        self.SetMinSize(min_size)

    def GetSizer(self):
        return self._sizer


class FakeStaticText:
    """Fake wx.StaticText that tracks font, color, and event bindings."""
    def __init__(self, parent, label, **kwargs):
        self.parent = parent
        self.label = label
        self.markup_label = None
        self.screen_rect = FakeRect(0, 0, 0, 0)
        self._font = None
        self._fg_color = None
        self._bindings = {}

    def SetFont(self, font):
        self._font = font

    def GetFont(self):
        return self._font

    def SetForegroundColour(self, color):
        self._fg_color = color

    def GetForegroundColor(self):
        return self._fg_color

    def GetLabel(self):
        return self.label

    def SetLabel(self, label):
        self.label = label
        self.markup_label = None

    def SetLabelMarkup(self, markup):
        self.markup_label = markup
        return True

    def Bind(self, event_type, handler):
        if event_type not in self._bindings:
            self._bindings[event_type] = []
        self._bindings[event_type].append(handler)

    def GetBindings(self):
        return self._bindings

    def GetParent(self):
        return self.parent

    def Refresh(self):
        pass

    def GetScreenRect(self):
        return self.screen_rect


class FakeRect:
    """Minimal rectangle double for hover hit-testing."""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def Contains(self, point):
        px, py = point
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height


# Event constants
EVT_ENTER_WINDOW = 1001
EVT_LEAVE_WINDOW = 1002
EVT_LEFT_DOWN = 1003


@pytest.fixture(autouse=True)
def patch_wx():
    """Patch wx.Panel and wx.StaticText before each test."""
    import wx

    # Save originals if not already saved (check __dict__ directly to avoid Mockwx __getattr__)
    if '_original_Panel' not in wx.__dict__:
        wx._original_Panel = wx.Panel
    if '_original_StaticText' not in wx.__dict__:
        wx._original_StaticText = wx.StaticText
    if '_original_GetMousePosition' not in wx.__dict__:
        wx._original_GetMousePosition = getattr(wx, "GetMousePosition", None)

    # Apply patches
    wx.Panel = FakePanel
    wx.StaticText = FakeStaticText
    wx.EVT_ENTER_WINDOW = EVT_ENTER_WINDOW
    wx.EVT_LEAVE_WINDOW = EVT_LEAVE_WINDOW
    wx.EVT_LEFT_DOWN = EVT_LEFT_DOWN
    wx.GetMousePosition = lambda: (-1, -1)

    yield

    # Restore originals from __dict__ directly
    if '_original_Panel' in wx.__dict__:
        wx.Panel = wx.__dict__['_original_Panel']
    if '_original_StaticText' in wx.__dict__:
        wx.StaticText = wx.__dict__['_original_StaticText']
    if '_original_GetMousePosition' in wx.__dict__:
        original_get_mouse_position = wx.__dict__['_original_GetMousePosition']
        if original_get_mouse_position is None:
            delattr(wx, "GetMousePosition")
        else:
            wx.GetMousePosition = original_get_mouse_position


@pytest.fixture
def helpers_module(patch_wx):
    """Import and reload helpers module after wx is patched."""
    from SpinRender.core.theme import Theme
    from SpinRender.ui.text_styles import TextStyle
    # Reload to ensure fresh module state
    import SpinRender.ui.helpers as helpers
    importlib.reload(helpers)
    return helpers, Theme.current()


class TestCreateFrame:
    """Test create_frame helper."""

    def test_creates_panel_with_parent(self, helpers_module):
        """Creates wx.Panel (FakePanel) with given parent."""
        helpers, _ = helpers_module
        parent = MagicMock()
        frame = helpers.create_frame(parent, 'layout.main.frame.bg')
        assert isinstance(frame, FakePanel)
        assert frame.parent is parent

    def test_applies_background_from_token(self, helpers_module):
        """Background color set from theme token."""
        helpers, theme = helpers_module
        parent = MagicMock()
        frame = helpers.create_frame(parent, 'layout.main.frame.bg')
        bg = frame.GetBackgroundColor()
        expected = theme.color("layout.main.frame.bg")
        assert bg.Red() == expected.Red() and bg.Green() == expected.Green() and bg.Blue() == expected.Blue()

    def test_token_validation_raises_for_unknown(self):
        """Unknown token raises ValueError."""
        import SpinRender.ui.helpers as helpers
        parent = MagicMock()
        with pytest.raises(ValueError, match="Unknown theme token"):
            helpers.create_frame(parent, 'UNKNOWN_TOKEN')


class TestCreateText:
    """Test create_text helper."""

    def test_creates_statictext_with_parent(self, helpers_module):
        """Creates wx.StaticText (FakeStaticText) with given parent."""
        helpers, theme = helpers_module
        parent = MagicMock()
        style = helpers.TextStyle(family="Test", size=11, weight=400, color=theme.color("colors.text.primary"))
        text = helpers.create_text(parent, "Label", style)
        assert isinstance(text, FakeStaticText)
        assert text.parent is parent
        assert text.label == "Label"

    def test_applies_font_from_style(self, helpers_module):
        """Font set from TextStyle.create_font()."""
        helpers, _ = helpers_module
        parent = MagicMock()
        style = helpers.TextStyle(family="Test", size=11, weight=600)
        text = helpers.create_text(parent, "Label", style)
        font = text.GetFont()
        assert font is not None
        assert hasattr(font, 'GetFaceName')
        assert hasattr(font, 'GetPointSize')
        assert hasattr(font, 'GetWeight')

    def test_applies_foreground_from_style_color(self, helpers_module):
        """Foreground color set from style.color when provided."""
        helpers, theme = helpers_module
        parent = MagicMock()
        style = helpers.TextStyle(family="Test", size=11, weight=400, color=theme.color("colors.cyan"))
        text = helpers.create_text(parent, "Label", style)
        fg = text.GetForegroundColor()
        expected = theme.color("colors.cyan")
        assert fg.Red() == expected.Red() and fg.Green() == expected.Green() and fg.Blue() == expected.Blue()

    def test_no_foreground_when_color_none(self, helpers_module):
        """Does not set foreground if color is None."""
        helpers, _ = helpers_module
        parent = MagicMock()
        style = helpers.TextStyle(family="Test", size=11, weight=400)
        text = helpers.create_text(parent, "Label", style)
        fg = text.GetForegroundColor()
        assert fg is None

    def test_enables_mouse_pass_through(self, helpers_module):
        """Binds EVT_LEFT_DOWN to enable click propagation to parent."""
        helpers, _ = helpers_module
        parent = MagicMock()
        style = helpers.TextStyle(family="Test", size=11, weight=400)
        text = helpers.create_text(parent, "Label", style)
        bindings = text.GetBindings()
        assert EVT_LEFT_DOWN in bindings
        assert len(bindings[EVT_LEFT_DOWN]) == 1


class TestBindMouseEvents:
    """Test bind_mouse_events helper."""

    def test_binds_enter_window_when_handler_provided(self):
        """Binds EVT_ENTER_WINDOW if hover_handler not None."""
        parent = MagicMock()
        handler = MagicMock()
        import SpinRender.ui.helpers as helpers
        helpers.bind_mouse_events(parent, hover_handler=handler)
        parent.Bind.assert_any_call(EVT_ENTER_WINDOW, handler)

    def test_binds_leave_window_when_handler_provided(self):
        """Binds EVT_LEAVE_WINDOW if leave_handler not None."""
        parent = MagicMock()
        handler = MagicMock()
        import SpinRender.ui.helpers as helpers
        helpers.bind_mouse_events(parent, leave_handler=handler)
        parent.Bind.assert_any_call(EVT_LEAVE_WINDOW, handler)

    def test_binds_left_down_when_handler_provided(self):
        """Binds EVT_LEFT_DOWN if click_handler not None."""
        parent = MagicMock()
        handler = MagicMock()
        import SpinRender.ui.helpers as helpers
        helpers.bind_mouse_events(parent, click_handler=handler)
        parent.Bind.assert_any_call(EVT_LEFT_DOWN, handler)

    def test_does_not_bind_when_handler_none(self):
        """Does not bind event if corresponding handler is None."""
        parent = MagicMock()
        import SpinRender.ui.helpers as helpers
        helpers.bind_mouse_events(parent)
        parent.Bind.assert_not_called()

    def test_binds_only_specified_handlers(self):
        """Binds exactly the handlers that are provided."""
        parent = MagicMock()
        hover = MagicMock()
        click = MagicMock()
        import SpinRender.ui.helpers as helpers
        helpers.bind_mouse_events(parent, hover_handler=hover, click_handler=click)
        # Should bind exactly two events
        assert parent.Bind.call_count == 2


class TestTextHoverState:
    """Test state-aware hover helpers for styled text."""

    def test_set_text_widget_state_uses_registered_style_token(self, helpers_module):
        """Hover state should resolve through the widget's registered text style."""
        helpers, theme = helpers_module
        parent = MagicMock()
        text = helpers.create_text(parent, "Open logs folder", "dialog_link")

        helpers.set_text_widget_state(text, hovered=True)

        fg = text.GetForegroundColor()
        expected = theme.color("layout.dialogs.options.body.links", hovered=True)
        assert fg.Red() == expected.Red()
        assert fg.Green() == expected.Green()
        assert fg.Blue() == expected.Blue()

    def test_set_text_widget_state_updates_link_suffix_markup(self, helpers_module):
        """Hovering a suffix-arrow link should re-render the arrow with the hovered suffix color."""
        helpers, theme = helpers_module
        parent = MagicMock()
        text = helpers.create_text(parent, "Open logs folder", "dialog_link", link_suffix_arrow=True)

        helpers.set_text_widget_state(text, hovered=True)

        suffix_color = theme.color("colors.primary", hovered=True).GetAsString()
        assert text.markup_label is not None
        assert suffix_color in text.markup_label
        assert "\u2197" in text.markup_label

    def test_bind_hover_text_group_applies_override_color_token(self, helpers_module):
        """Hover group bindings should update text using the provided override token."""
        helpers, theme = helpers_module
        parent = MagicMock()
        text = helpers.create_text(parent, "kicad-cli render options", "dialog_description")
        event = MagicMock()

        helpers.bind_hover_text_group(
            [
                {
                    "widget": text,
                    "style_name": "dialog_description",
                    "label": "kicad-cli render options",
                    "color_token": "layout.dialogs.options.body.links",
                }
            ],
            click_handler=MagicMock(),
        )

        bindings = text.GetBindings()
        bindings[EVT_ENTER_WINDOW][0](event)

        fg = text.GetForegroundColor()
        expected = theme.color("layout.dialogs.options.body.links", hovered=True)
        assert fg.Red() == expected.Red()
        assert fg.Green() == expected.Green()
        assert fg.Blue() == expected.Blue()
        event.Skip.assert_called_once_with()

    def test_bind_hover_text_group_keeps_hover_while_pointer_stays_in_group(self, helpers_module):
        """Leaving one widget should not clear hover if the pointer is still over a sibling."""
        helpers, theme = helpers_module
        parent = MagicMock()
        first = helpers.create_text(parent, "Open logs folder", "dialog_link")
        second = helpers.create_text(parent, "More details", "dialog_link")
        first.screen_rect = FakeRect(0, 0, 10, 10)
        second.screen_rect = FakeRect(20, 0, 10, 10)
        enter_event = MagicMock()
        leave_event = MagicMock()

        import wx
        wx.GetMousePosition = lambda: (25, 5)

        helpers.bind_hover_text_group(
            [{"widget": first}, {"widget": second}],
            click_handler=MagicMock(),
        )

        bindings = first.GetBindings()
        bindings[EVT_ENTER_WINDOW][0](enter_event)
        hovered = theme.color("layout.dialogs.options.body.links", hovered=True)
        assert first.GetForegroundColor().GetAsString() == hovered.GetAsString()

        bindings[EVT_LEAVE_WINDOW][0](leave_event)
        assert first.GetForegroundColor().GetAsString() == hovered.GetAsString()
        leave_event.Skip.assert_called_once_with()


class TestApplyDisabledState:
    """Test apply_disabled_state helper."""

    def test_applies_disabled_alpha_to_widget(self):
        """Sets widget to 50% opacity when disabled."""
        widget = FakePanel(None)
        import SpinRender.core.theme as theme_mod
        theme = theme_mod.Theme.current()
        original = theme.color("colors.cyan")
        widget.SetBackgroundColour(original)

        import SpinRender.ui.helpers as helpers
        helpers.apply_disabled_state(widget, is_enabled=False)

        new_bg = widget.GetBackgroundColor()
        # Should be a ColorMock with alpha=128
        assert new_bg.Alpha() == 128
        # RGB should be unchanged
        assert new_bg.Red() == original.Red()
        assert new_bg.Green() == original.Green()
        assert new_bg.Blue() == original.Blue()

    def test_restores_enabled_state(self):
        """Does not change color when is_enabled=True."""
        widget = FakePanel(None)
        import SpinRender.core.theme as theme_mod
        theme = theme_mod.Theme.current()
        original = theme.color("colors.cyan")
        widget.SetBackgroundColour(original)

        import SpinRender.ui.helpers as helpers
        helpers.apply_disabled_state(widget, is_enabled=True)

        # Should not have changed background
        new_bg = widget.GetBackgroundColor()
        assert new_bg is original
