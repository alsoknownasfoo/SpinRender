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


class FontMock:
    """Mock for wx.Font that returns configured faceName."""
    def __init__(self, size, family=None, style=None, weight=None, faceName=None, **kwargs):
        self._size = size
        self._family = family
        self._style = style
        self._weight = weight
        self._faceName = faceName

    def GetFaceName(self):
        return self._faceName

    def GetPointSize(self):
        return self._size


class DummyWindow:
    """Simple window mock that accepts arbitrary kwargs like wx.Window."""
    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return MagicMock()


class Mockwx:
    """Mock wxPython module for headless testing."""

    def __init__(self):
        self._objects = {}
        # Pre-create submodule mocks
        self._svg = self._make_module('wx.svg')
        self._lib = self._make_module('wx.lib')
        self._glcanvas = self._make_module('wx.glcanvas')
        self._scrolledpanel = self._make_module('wx.lib.scrolledpanel')
        # Link scrolledpanel to lib
        self._lib.scrolledpanel = self._scrolledpanel

    def _make_module(self, name):
        m = MagicMock()
        m.__name__ = name
        m.__file__ = f'{name}.py'
        m.__path__ = [] if '.' in name else None
        return m

    def __getattr__(self, name):
        """Return mocked wx classes/functions based on name."""
        # Colour/Color - return the ColourMock class itself (not a factory)
        if name in ['Colour', 'Color']:
            return ColourMock

        # Font - return FontMock class
        if name == 'Font':
            return FontMock

        # Constants
        font_weights = {
            'FONTWEIGHT_NORMAL': 400,
            'FONTWEIGHT_LIGHT': 300,
            'FONTWEIGHT_BOLD': 700,
            'FONTWEIGHT_SEMIBOLD': 600,
        }
        if name in font_weights:
            return font_weights[name]

        font_constants = {
            'FONTSTYLE_NORMAL': 0,
            'FONTSTYLE_ITALIC': 1,
            'FONTFAMILY_DEFAULT': 80,
        }
        if name in font_constants:
            return font_constants[name]

        # Submodules
        if name == 'svg':
            return self._svg
        if name == 'lib':
            return self._lib
        if name == 'glcanvas':
            return self._glcanvas

        # Window classes - return DummyWindow class (callable, subclassable)
        window_classes = [
            'Panel', 'Dialog', 'Frame', 'Window',
            'Slider', 'Button', 'StaticText', 'TextCtrl',
            'PopupTransientWindow'
        ]
        if name in window_classes:
            return DummyWindow

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

        # Generic mock for anything else - create and cache a MagicMock instance
        mock = MagicMock()
        self._objects[name] = mock
        return mock

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

# Register wx submodule mocks in sys.modules
sys.modules['wx.svg'] = mock_wx_module._svg
sys.modules['wx.lib'] = mock_wx_module._lib
sys.modules['wx.glcanvas'] = mock_wx_module._glcanvas
sys.modules['wx.lib.scrolledpanel'] = mock_wx_module._scrolledpanel


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
