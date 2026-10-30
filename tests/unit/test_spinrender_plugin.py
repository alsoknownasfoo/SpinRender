"""Focused tests for the plugin entrypoint: board path resolution and wx.App pinning."""

import importlib
import sys
import weakref
from types import SimpleNamespace


def _load_plugin_module(monkeypatch, fake_pcbnew):
    fake_wx = SimpleNamespace(
        OK=1,
        ICON_ERROR=2,
        Frame=type('Frame', (), {}),
        Timer=type('Timer', (), {}),
        EVT_TIMER=object(),
        EVT_CLOSE=object(),
        MessageBox=lambda *args, **kwargs: None,
    )
    fake_logger_module = SimpleNamespace(SpinLogger=SimpleNamespace(setup=lambda level='debug': None))
    fake_dependencies_module = SimpleNamespace(DependencyChecker=type('DependencyChecker', (), {}))

    monkeypatch.setitem(sys.modules, 'pcbnew', fake_pcbnew)
    monkeypatch.setitem(sys.modules, 'wx', fake_wx)
    monkeypatch.setitem(sys.modules, 'SpinRender.utils.logger', fake_logger_module)
    monkeypatch.setitem(sys.modules, 'utils.logger', fake_logger_module)
    monkeypatch.setitem(sys.modules, 'SpinRender.ui.dependencies', fake_dependencies_module)
    monkeypatch.setitem(sys.modules, 'ui.dependencies', fake_dependencies_module)
    monkeypatch.delitem(sys.modules, 'SpinRender.spinrender_plugin', raising=False)

    return importlib.import_module('SpinRender.spinrender_plugin')


def test_get_board_file_path_uses_board_method(monkeypatch):
    """The plugin should use GetFileName directly when the board exposes it."""
    fake_pcbnew = SimpleNamespace(ActionPlugin=type('ActionPlugin', (), {}))
    plugin = _load_plugin_module(monkeypatch, fake_pcbnew)

    board = SimpleNamespace(GetFileName=lambda: '/tmp/direct.kicad_pcb')

    assert plugin._get_board_file_path(board) == '/tmp/direct.kicad_pcb'


def test_get_board_file_path_casts_raw_board_when_needed(monkeypatch):
    """The plugin should cast raw SWIG board objects before reading the filename."""
    class RawBoard:
        pass

    class TypedBoard:
        def GetFileName(self):
            return '/tmp/cast.kicad_pcb'

    fake_pcbnew = SimpleNamespace(
        ActionPlugin=type('ActionPlugin', (), {}),
        Cast_to_BOARD=lambda board: TypedBoard(),
    )
    plugin = _load_plugin_module(monkeypatch, fake_pcbnew)

    assert plugin._get_board_file_path(RawBoard()) == '/tmp/cast.kicad_pcb'


class _AppWrapper:
    """Stand-in for the wxPython wrapper of KiCad's C++-owned wxApp."""


def _install_fake_app(plugin, monkeypatch):
    """Mimic KiCad: wx.GetApp() returns the live wrapper if something holds one,
    otherwise a fresh one (like sip's object map). wx.CallAfter() follows
    wxPython: it calls app.Connect() whenever the wrapper lacks _CallAfterId."""
    live = [None]
    connects = []

    def get_app():
        app = live[0]() if live[0] else None
        if app is None:
            app = _AppWrapper()
            live[0] = weakref.ref(app)
        return app

    def call_after(fn, *args, **kwargs):
        app = get_app()
        if not hasattr(app, '_CallAfterId'):
            app._CallAfterId = 1000 + len(connects)
            connects.append(app._CallAfterId)

    monkeypatch.setattr(plugin.wx, 'GetApp', get_app, raising=False)
    monkeypatch.setattr(plugin.wx, 'CallAfter', call_after, raising=False)
    return connects


def test_callafter_reconnects_every_call_with_transient_app_wrapper(monkeypatch):
    """Documents the KiCad behaviour behind the crash: without pinning, every
    CallAfter registers another handler on the app."""
    fake_pcbnew = SimpleNamespace(ActionPlugin=type('ActionPlugin', (), {}))
    plugin = _load_plugin_module(monkeypatch, fake_pcbnew)
    connects = _install_fake_app(plugin, monkeypatch)

    for _ in range(3):
        plugin.wx.CallAfter(lambda: None)

    assert len(connects) == 3


def test_pin_wx_app_registers_callafter_handler_once(monkeypatch):
    """After _pin_wx_app(), worker-thread CallAfter calls must only post events,
    never Connect() on the app."""
    fake_pcbnew = SimpleNamespace(ActionPlugin=type('ActionPlugin', (), {}))
    plugin = _load_plugin_module(monkeypatch, fake_pcbnew)
    connects = _install_fake_app(plugin, monkeypatch)

    plugin._pin_wx_app()
    connects_after_pin = len(connects)

    for _ in range(10):
        plugin.wx.CallAfter(lambda: None)
    plugin._pin_wx_app()  # idempotent

    assert plugin._wx_app_ref is plugin.wx.GetApp()
    assert len(connects) == connects_after_pin
