"""Focused tests for KiCad board path resolution in the plugin entrypoint."""

import importlib
import sys
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