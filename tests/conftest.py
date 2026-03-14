#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Pytest configuration and fixtures for SpinRender tests.

This module provides mocking for wxPython to enable headless testing.
"""
import sys
from unittest.mock import MagicMock
import pytest


class ColourMock:
    """Mock for wx.Colour that behaves like a simple data object."""

    def __init__(self, r=0, g=0, b=0, a=255):
        self._r = r
        self._g = g
        self._b = b
        self._a = a

    def Red(self):
        return self._r

    def Green(self):
        return self._g

    def Blue(self):
        return self._b

    def Alpha(self):
        return self._a


class Mockwx:
    """Mock wxPython module for headless testing."""

    def __init__(self):
        self._objects = {}

    def __getattr__(self, name):
        """Return mocked wx classes/functions based on name."""
        # Colour/Color - return the ColourMock class itself (not a factory)
        if name in ['Colour', 'Color']:
            return ColourMock

        # Constants
        font_weights = {
            'FONTWEIGHT_NORMAL': 400,
            'FONTWEIGHT_LIGHT': 300,
            'FONTWEIGHT_BOLD': 700,
            'FONTWEIGHT_SEMIBOLD': 600,
        }
        if name in font_weights:
            return font_weights[name]

        # Window classes - return MagicMock class (callable, subclassable)
        window_classes = [
            'Panel', 'Dialog', 'Frame', 'Window',
            'Slider', 'Button', 'StaticText', 'TextCtrl'
        ]
        if name in window_classes:
            # Return the MagicMock class itself so it can be subclassed
            # and instantiated. Instances will have MagicMock behavior.
            return MagicMock

        # Other classes
        if name == 'GraphicsContext':
            return self._create_gc_mock
        if name == 'AutoBufferedPaintDC':
            return self._create_dc_mock
        if name == 'App':
            return self._create_app_mock
        if name in ['Pen', 'Brush', 'GraphicsPenInfo', 'GraphicsBrushInfo']:
            return MagicMock()
        if name in ['EVT_PAINT', 'EVT_SIZE', 'BG_STYLE_PAINT',
                    'ALIGN_CENTER', 'ALIGN_LEFT', 'ALIGN_RIGHT',
                    'VERTICAL', 'HORIZONTAL']:
            return MagicMock()

        # Generic mock for anything else
        mock = MagicMock()
        self._objects[name] = mock
        return mock

    def _create_colour_mock(self, *args, **kwargs):
        """Create a mock wx.Colour instance."""
        if len(args) == 1 and isinstance(args[0], str):
            hex_str = args[0].lstrip('#')
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            a = kwargs.get('alpha', 255)
        elif len(args) == 3:
            r, g, b = args
            a = kwargs.get('alpha', 255)
        elif len(args) == 4:
            r, g, b, a = args
        else:
            r = g = b = a = 0

        colour = MagicMock()
        colour.Red.return_value = r
        colour.Green.return_value = g
        colour.Blue.return_value = b
        colour.Alpha.return_value = a

        return colour

    def _create_window_mock(self, *args, **kwargs):
        """Create a mock wx.Window-derived instance."""
        window = MagicMock()
        window.GetSize.return_value = (100, 100)
        window.GetClientSize.return_value = (100, 100)
        window.GetPosition.return_value = (0, 0)
        window.GetBackgroundColour.return_value = MagicMock()
        window.SetBackgroundColour.return_value = None
        window.SetMinSize.return_value = None
        window.Bind.return_value = None
        window.GetParent.return_value = None
        window.GetChildren.return_value = []
        window.GetSizer.return_value = None
        window.SetSizer.return_value = None
        window.Layout.return_value = None
        window.Refresh.return_value = None
        return window

    def _create_gc_mock(self, dc):
        """Create a mock wx.GraphicsContext."""
        gc = MagicMock()
        gc.CreateBrush.return_value = MagicMock()
        gc.CreatePen.return_value = MagicMock()
        gc.SetBrush.return_value = None
        gc.SetPen.return_value = None
        gc.DrawRectangle.return_value = None
        gc.DrawText.return_value = None
        gc.GetTextExtent.return_value = (50, 20)
        gc.StrokeLine.return_value = None
        return gc

    def _create_dc_mock(self, window):
        """Create a mock wx.AutoBufferedPaintDC."""
        return MagicMock()

    def _create_app_mock(self):
        """Create a mock wx.App."""
        app = MagicMock()
        app.MainLoop.return_value = None
        return app


# Install the mock IMMEDIATELY upon module import, before any test modules
# or SpinRender modules can import wx
mock_wx_module = Mockwx()
mock_pcbnew = MagicMock()
mock_pcbnew.GetBoard.return_value = MagicMock()
mock_pcbnew.__version__ = "6.0"
sys.modules['wx'] = mock_wx_module
sys.modules['pcbnew'] = mock_pcbnew

# Mock wx submodules that are imported in the codebase
sys.modules['wx.svg'] = MagicMock()
sys.modules['wx.lib'] = MagicMock()
sys.modules['wx.lib.scrolledpanel'] = MagicMock()
sys.modules['wx.glcanvas'] = MagicMock()


@pytest.fixture(scope='session', autouse=True)
def mock_wx():
    """
    Mock wxPython module for all tests.

    The mock is already installed at conftest import time (above),
    so this fixture simply provides access to it for tests that
    request it explicitly.
    """
    yield sys.modules['wx']


@pytest.fixture
def wx_mock():
    """
    Provide access to the wx mock for explicit testing.

    Usage in tests:
        def test_something(wx_mock):
            colour = wx.Colour(255, 0, 0)
            assert colour.Red() == 255
    """
    return sys.modules['wx']


@pytest.fixture(scope='function', autouse=True)
def reset_mocks():
    """Reset all mock calls before each test."""
    yield
